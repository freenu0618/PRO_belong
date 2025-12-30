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
    
    # ✅ 어댑터 경로: /workspace/output (영구 스토리지) 우선, 없으면 /app (도커 이미지)
    workspace_adapter = "/workspace/output/max500"  # 학습된 모델 (adapter_config.json 최상위에 있음)
    bundled_adapter = os.path.join(os.getcwd(), "belong", "ml", "fine_tune", "lora_best_r32")
    
    if os.path.exists(os.path.join(workspace_adapter, "adapter_config.json")):
        adapter_path = workspace_adapter
        print(f"📁 Using workspace adapter: {adapter_path}")
    elif os.path.exists(bundled_adapter):
        adapter_path = bundled_adapter
        print(f"📁 Using bundled adapter: {adapter_path}")
    else:
        adapter_path = bundled_adapter  # 기본값
        print(f"⚠️ No adapter found, will try: {adapter_path}")

    try:
        import time
        start_time = time.time()

        # 2. Base Model 로드
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

        # 3. Multi-Adapter Loading (Local)
        print(f"🔧 Loading LoRA adapter from {adapter_path}...")

        if os.path.exists(adapter_path):
            # 🔍 Robust Checkpoint Search
            if not os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
                print(f"⚠️ adapter_config.json not found. Searching for checkpoints...")
                try:
                    subdirs = [d for d in os.listdir(adapter_path) 
                               if os.path.isdir(os.path.join(adapter_path, d)) and d.startswith("checkpoint-")]
                    if subdirs:
                        subdirs.sort(key=lambda x: int(x.split('-')[-1]) if x.split('-')[-1].isdigit() else 0)
                        best_checkpoint = subdirs[-1]
                        adapter_path = os.path.join(adapter_path, best_checkpoint)
                        print(f"   Found: {best_checkpoint}")
                except Exception as e:
                    print(f"⚠️ Checkpoint search error: {e}")

            state.model = PeftModel.from_pretrained(state.model, adapter_path, adapter_name="lora_best_r32")
            print(f"✅ LoRA adapter loaded from {adapter_path}")
        else:
            print(f"⚠️ Adapter not found at {adapter_path}. Using base model only.")

        # 4. Initialize RAG (ChromaDB)
        print("🧠 Initializing RAG VectorStore...")
        
        # ✅ 임베딩 모델 선택 (환경변수로 설정 가능)
        embedding_choice = os.environ.get("EMBEDDING_MODEL", "AUTO")
        
        EMBEDDING_MODELS = {
            "AUTO": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 다국어 (기본)
            "KOREAN": "BM-K/KoSimCSE-roberta-multitask",  # 한글 특화 (더 정확)
        }
        
        embedding_model = EMBEDDING_MODELS.get(embedding_choice.upper(), EMBEDDING_MODELS["AUTO"])
        print(f"📦 Embedding model: {embedding_choice} → {embedding_model}")
        
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
        
        state.vectordb = Chroma(persist_directory=chroma_path, embedding_function=embeddings)
        print(f"✅ RAG VectorStore ready at {chroma_path}")

        total_time = time.time() - start_time
        print("=" * 60)
        print(f"🎉 AI Server Startup Complete! ({total_time:.1f}s total)")
        print("✅ Available models: base, lora_best_r32")
        print(f"✅ RAG enabled with ChromaDB (Embedding: {embedding_choice})")
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
