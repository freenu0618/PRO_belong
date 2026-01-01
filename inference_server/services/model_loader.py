# inference_server/services/model_loader.py
"""모델 로딩 전담 서비스"""

import os
import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from inference_server import state

logger = logging.getLogger(__name__)


def _check_vectordb_dimension(persist_dir: str) -> int:
    """
    기존 VectorDB의 임베딩 차원 확인
    
    Args:
        persist_dir: ChromaDB 디렉토리 경로
        
    Returns:
        임베딩 차원 (int) 또는 None (데이터 없음/에러)
    """
    try:
        import chromadb
        
        if not os.path.exists(os.path.join(persist_dir, "chroma.sqlite3")):
            logger.debug(f"No existing VectorDB found at {persist_dir}")
            return None
        
        client = chromadb.PersistentClient(path=persist_dir)
        collection = client.get_collection("langchain")
        
        if collection.count() > 0:
            sample = collection.peek(1)
            if sample and sample.get("embeddings"):
                dimension = len(sample["embeddings"][0])
                logger.info(f"Existing VectorDB dimension: {dimension}")
                return dimension
    except Exception as e:
        logger.debug(f"Could not check VectorDB dimension: {e}")
    
    return None


def _reset_vectordb(persist_dir: str, embeddings, embedding_model: str):
    """
    VectorDB를 새 임베딩 모델로 리셋 (기존 데이터 백업)
    
    Args:
        persist_dir: ChromaDB 영구 저장 경로
        embeddings: HuggingFaceEmbeddings 인스턴스
        embedding_model: 새 임베딩 모델 ID
    
    Returns:
        초기화된 Chroma 인스턴스
    """
    import shutil
    from datetime import datetime
    from pathlib import Path
    
    logger.warning(f"🔄 Resetting VectorDB with embedding model: {embedding_model}")
    
    # 1. 기존 DB 백업
    persist_path = Path(persist_dir)
    if persist_path.exists():
        backup_name = f"chroma_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = persist_path.parent / backup_name
        shutil.copytree(persist_dir, backup_path)
        logger.info(f"📦 Backup created: {backup_path}")
        print(f"📦 Backup created: {backup_path}")
        
        # 2. 기존 DB 삭제
        shutil.rmtree(persist_dir)
        logger.info(f"🗑️ Removed old VectorDB at {persist_dir}")
        print(f"🗑️ Removed old VectorDB")
    
    # 3. 새 임베딩으로 초기화
    vectordb = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )
    
    logger.info(f"✅ VectorDB initialized with {embedding_model}")
    print(f"✅ VectorDB reset complete with {embedding_model}")
    return vectordb


def _discover_adapters() -> list:
    """
    사용 가능한 LoRA Adapter들을 자동 탐색
    
    탐색 경로:
    - /workspace/output/* (RunPod 영구 스토리지)
    - /app/belong/ml/fine_tune/* (Docker 이미지 번들)
    - ./belong/ml/fine_tune/* (로컬 개발)
    
    Returns:
        [{"name": "lora_r32", "path": "/path/to/adapter", "type": "checkpoint|direct"}, ...]
    """
    from pathlib import Path
    
    adapters = []
    seen_paths = set()  # ✅ 중복 경로 방지
    
    # 탐색할 기본 경로
    search_paths = [
        "/workspace/output",           # RunPod 영구 스토리지
        "/app/belong/ml/fine_tune",    # Docker 이미지 내
        os.path.join(os.getcwd(), "belong", "ml", "fine_tune"),  # 로컬
    ]
    
    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue
        
        # ✅ 경로 정규화로 중복 제거
        normalized_path = os.path.realpath(base_path)
        if normalized_path in seen_paths:
            logger.debug(f"Skipping duplicate path: {normalized_path}")
            continue
        seen_paths.add(normalized_path)
        logger.info(f"Scanning for adapters in: {normalized_path}")
        
        try:
            # base_path 내 모든 디렉토리 탐색
            for entry in os.listdir(normalized_path):
                entry_path = os.path.join(normalized_path, entry)
                
                if not os.path.isdir(entry_path):
                    continue
                
                # 1. adapter_config.json이 직접 있는 경우 (완성된 어댑터)
                if os.path.exists(os.path.join(entry_path, "adapter_config.json")):
                    adapters.append({
                        "name": entry,
                        "path": entry_path,
                        "type": "direct"
                    })
                else:
                    # 2. checkpoint-* 하위 폴더에 있는 경우
                    subdirs = [d for d in os.listdir(entry_path)
                              if os.path.isdir(os.path.join(entry_path, d)) and d.startswith("checkpoint-")]
                    
                    if subdirs:
                        # 가장 큰 번호의 checkpoint 사용 (최신)
                        subdirs.sort(key=lambda x: int(x.split('-')[-1]) if x.split('-')[-1].isdigit() else 0)
                        latest_checkpoint = subdirs[-1]
                        checkpoint_path = os.path.join(entry_path, latest_checkpoint)
                        
                        if os.path.exists(os.path.join(checkpoint_path, "adapter_config.json")):
                            adapters.append({
                                "name": f"{entry}_{latest_checkpoint}",
                                "path": checkpoint_path,
                                "type": "checkpoint"
                            })
        except Exception as e:
            logger.warning(f"Error scanning {normalized_path}: {e}")
            continue
    
    return adapters



async def load_models():
    """
    AI 모델 로딩 (startup 시 호출)
    
    역할:
    - Llama 3 base model 로딩
    - LoRA adapter 로딩
    - ChromaDB VectorStore 초기화
    """
    print("🚀 Starting AI Server Startup Sequence...")
    print("=" * 60)

    # 0. Dependency & Token Check
    try:
        import transformers
        import peft
        print(f"📦 Library Versions: Transformers={transformers.__version__}, Torch={torch.__version__}")
        print(f"🔧 GPU Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"❌ CRITICAL: Missing Dependency - {e}")
        raise e

    # ✅ Enhanced HF_TOKEN validation
    hf_token = os.environ.get("HF_TOKEN")
    print(f"🔑 HF_TOKEN: {'✅ Set ({} chars)'.format(len(hf_token)) if hf_token else '❌ NOT SET'}")

    if not hf_token:
        print("")
        print("❌ CRITICAL: HF_TOKEN environment variable is missing!")
        print("💡 Llama 3 is a gated model. You MUST:")
        print("   1. Get token at: https://huggingface.co/settings/tokens")
        print("   2. Accept Llama 3 license: https://huggingface.co/meta-llama/Meta-Llama-3-8B")
        print("   3. Set HF_TOKEN in .env file or environment")
        print("")
        print("⚠️ Server will run in MOCK MODE (limited functionality)")
        print("=" * 60)
        return

    print("=" * 60)
    print("📥 Loading AI Models...")
    print("⏰ First time: ~10 minutes (downloading 8GB from HuggingFace)")
    print("⏰ Subsequent runs: ~60 seconds (loading from cache)")
    print("=" * 60)

    # 1. Base Model ID
    base_model_id = "meta-llama/Meta-Llama-3-8B"
    
    # ✅ Checkpoint 자동 탐색 로직 (사용자 요청)
    # - Base 모델만 기본 로드
    # - 파인튜닝 모델은 탐색하여 리스트업 (강제 로드 X)
    print("🔍 Searching for available LoRA checkpoints...")
    
    available_adapters = _discover_adapters()
    
    if available_adapters:
        print(f"📁 Found {len(available_adapters)} LoRA adapter(s):")
        for i, adapter_info in enumerate(available_adapters, 1):
            print(f"   {i}. {adapter_info['name']} (at {adapter_info['path']})")
    else:
        print("📁 No LoRA adapters found. Will use base model only.")

    try:
        import time
        start_time = time.time()

        # 2. Base Model 로드 (항상 기본값)
        torch_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
        print(f"📦 Loading Base Model: {base_model_id}")
        print(f"   Using dtype: {torch_dtype}")

        state.model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch_dtype,
            device_map="auto",
            token=hf_token
        )

        elapsed = time.time() - start_time
        print(f"✅ Base model loaded in {elapsed:.1f} seconds")

        state.tokenizer = AutoTokenizer.from_pretrained(base_model_id, token=hf_token)
        state.tokenizer.pad_token = state.tokenizer.eos_token
        state.tokenizer.padding_side = "right"

        # 3. Optional: 첫 번째 LoRA Adapter 로드 (환경변수로 제어)
        # ✅ 포트폴리오용: LoRA 어댑터 기본 로딩 (LOAD_DEFAULT_ADAPTER=true)
        load_default_adapter = os.environ.get("LOAD_DEFAULT_ADAPTER", "true").lower() == "true"
        default_adapter_name = os.environ.get("DEFAULT_ADAPTER_NAME", "")
        
        if load_default_adapter and available_adapters:
            # 환경변수로 지정된 어댑터 찾기
            target_adapter = None
            if default_adapter_name:
                for adapter in available_adapters:
                    if adapter['name'] == default_adapter_name:
                        target_adapter = adapter
                        break
            
            # 지정된 어댑터가 없으면 첫 번째 것 사용
            if not target_adapter and available_adapters:
                target_adapter = available_adapters[0]
            
            if target_adapter:
                print(f"🔧 Loading default LoRA adapter: {target_adapter['name']}...")
                try:
                    state.model = PeftModel.from_pretrained(
                        state.model,
                        target_adapter['path'],
                        adapter_name=target_adapter['name']
                    )
                    print(f"✅ LoRA adapter '{target_adapter['name']}' loaded")
                except Exception as e:
                    print(f"⚠️ Failed to load adapter '{target_adapter['name']}': {e}")
                    print(f"   Continuing with base model only.")
        else:
            print(f"💡 Base model ready. LoRA adapters can be loaded on-demand via API requests.")


        # 4. Initialize RAG (ChromaDB) with BAAI/bge-m3
        print("🧠 Initializing RAG VectorStore...")
        
        # ✅ BAAI/bge-m3 단일 모델 사용 (사용자 요청)
        # - 다국어 지원 (100+ languages)
        # - 1024 차원 (고성능)
        # - Hybrid retrieval (dense + sparse + multi-vector)
        embedding_model = "BAAI/bge-m3"
        print(f"📦 Embedding model: {embedding_model} (1024 dims, multilingual)")
        
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # ✅ ChromaDB 경로: 실제 데이터가 있는 경로 우선 선택
        possible_paths = [
            "/workspace/chroma_db",  # 사용자가 업로드한 영구 데이터
            "/app/chroma_db",        # Docker 이미지 내 기본 데이터
            "chroma_db"              # 로컬 개발 환경
        ]
        chroma_path = "chroma_db"  # 기본값
        for path in possible_paths:
            sqlite_file = os.path.join(path, "chroma.sqlite3")
            if os.path.exists(sqlite_file):
                chroma_path = path
                break
        
        # ✅ VectorDB 초기화 (기존 컬렉션 차원 불일치 자동 처리)
        force_reset = os.environ.get("RESET_VECTORDB", "false").lower() == "true"
        expected_dim = 1024  # BAAI/bge-m3
        
        if force_reset:
            # 수동 리셋 요청 시
            print(f"🔄 RESET_VECTORDB=true detected. Resetting VectorDB...")
            state.vectordb = _reset_vectordb(chroma_path, embeddings, embedding_model)
        else:
            # ✅ 사전 차원 확인
            existing_dim = _check_vectordb_dimension(chroma_path)
            
            if existing_dim and existing_dim != expected_dim:
                # 차원 불일치 감지 → 자동 리셋
                print(f"⚠️ 임베딩 차원 불일치 감지!")
                print(f"   기존 DB: {existing_dim}차원, 현재 모델: {expected_dim}차원")
                print(f"🔄 자동 VectorDB 리셋 중...")
                state.vectordb = _reset_vectordb(chroma_path, embeddings, embedding_model)
            else:
                # 차원 일치 또는 신규 DB → 정상 로드
                try:
                    state.vectordb = Chroma(
                        persist_directory=chroma_path,
                        embedding_function=embeddings
                    )
                    if existing_dim:
                        print(f"✅ RAG VectorStore ready at {chroma_path} ({existing_dim}D)")
                    else:
                        print(f"✅ RAG VectorStore initialized at {chroma_path} ({expected_dim}D)")
                except Exception as e:
                    error_msg = str(e).lower()
                    # 예상치 못한 차원 문제 발생 시 fallback
                    if "dimension" in error_msg or "embedding" in error_msg or "incompatible" in error_msg:
                        print(f"⚠️ VectorDB 로드 실패 (차원 문제): {e}")
                        print(f"🔄 자동 리셋 실행...")
                        state.vectordb = _reset_vectordb(chroma_path, embeddings, embedding_model)
                    else:
                        # 다른 에러는 그대로 raise
                        raise

        total_time = time.time() - start_time
        print("=" * 60)
        print(f"🎉 AI Server Startup Complete! ({total_time:.1f}s total)")
        print(f"✅ Base Model: {base_model_id}")
        
        # 로드된 어댑터 정보
        if hasattr(state.model, 'peft_config') and state.model.peft_config:
            loaded_adapters = list(state.model.peft_config.keys())
            print(f"✅ Loaded LoRA Adapters: {', '.join(loaded_adapters)}")
        else:
            print(f"✅ Using base model (no LoRA adapters loaded)")
        
        # 사용 가능한 어댑터 목록
        if available_adapters:
            print(f"📋 Available adapters for on-demand loading: {len(available_adapters)}")
        
        print(f"✅ RAG enabled with ChromaDB (Embedding: BAAI/bge-m3, 1024 dims)")
        print("=" * 60)

    except Exception as e:
        print("=" * 60)
        print(f"❌ Model Loading Error: {e}")
        print("")
        print("🔍 Possible causes:")
        print("   1. HF_TOKEN invalid or expired")
        print("   2. No internet connection to HuggingFace")
        print("   3. Insufficient GPU memory (need ~18GB)")
        print("   4. Llama 3 access not granted (check license)")
        print("")
        print("⚠️ Server continuing in MOCK MODE")
        print("=" * 60)

        # Graceful degradation - don't crash
        state.model = None
        state.tokenizer = None
        state.vectordb = None
