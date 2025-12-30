# inference_server/main.py
"""
FastAPI 메인 진입점
- 각 서비스 모듈을 import하여 라우터 등록
- 단일 책임: HTTP 라우팅만 담당
"""

import os
import torch
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File

# 환경변수 로드
load_dotenv()

# 패키지 내부 import
from inference_server import state
from .schemas import GenerateRequest, TrainRequest
from .services import model_loader, generate, ingest, training

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Belong AI Inference Server")


# ============================================================
# Lifecycle Events
# ============================================================

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로딩"""
    await model_loader.load_models()


# ============================================================
# API Routes - Generation
# ============================================================

@app.post("/generate")
async def api_generate_text(request: GenerateRequest):
    """텍스트 생성 API"""
    return await generate.generate_text(request)


# ============================================================
# API Routes - Document Ingestion
# ============================================================

@app.post("/ingest")
async def api_ingest_document(file: UploadFile = File(...)):
    """문서 업로드 및 RAG 저장 API"""
    return await ingest.ingest_document(file)


# ============================================================
# API Routes - Fine-tuning
# ============================================================

@app.post("/train")
async def api_start_training(request: TrainRequest):
    """파인튜닝 학습 시작 API"""
    return await training.start_training(request)


@app.get("/train/status/{job_id}")
async def api_get_training_status(job_id: str):
    """학습 상태 조회 API"""
    return await training.get_training_status(job_id)


@app.get("/train/models")
async def api_list_trained_models():
    """학습된 모델 목록 API"""
    return await training.list_trained_models()


@app.delete("/train/models/{model_name}")
async def api_delete_trained_model(model_name: str):
    """학습된 모델 삭제 API"""
    return await training.delete_trained_model(model_name)


@app.post("/train/storage/cleanup")
async def api_cleanup_storage():
    """스토리지 정리 API - 고아 폴더 및 오래된 체크포인트 삭제"""
    return await training.cleanup_storage()


@app.get("/train/storage/info")
async def api_storage_info():
    """스토리지 사용량 정보 API"""
    return await training.get_storage_info()


# ============================================================
# API Routes - Health & Utility
# ============================================================

@app.get("/")
async def root():
    return {"message": "Belong AI Inference Server is Running!"}


@app.post("/")
async def root_post():
    return {"message": "POST request to root received. Use /generate for inference."}


@app.get("/health")
async def health_check():
    """AI 서버 상태 확인"""
    status_info = {
        "status": "ok" if state.model else "degraded",
        "model_loaded": state.model is not None,
        "tokenizer_loaded": state.tokenizer is not None,
        "vectordb_loaded": state.vectordb is not None,
        "hf_token_set": bool(os.environ.get("HF_TOKEN")),
        "gpu_available": torch.cuda.is_available(),
        "current_embedding_model": getattr(state, 'current_embedding_model', 'auto'),
    }

    if torch.cuda.is_available():
        status_info["gpu_name"] = torch.cuda.get_device_name(0)
        status_info["gpu_memory_allocated"] = f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB"

    if state.model:
        status_info["device"] = str(state.model.device)

    return status_info


# ============================================================
# API Routes - Embedding Model Selection
# ============================================================

# ✅ 지원되는 임베딩 모델 (Single Source of Truth)
EMBEDDING_MODELS = {
    "auto": {
        "id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "name": "다국어 (기본)",
        "dim": 384
    },
    "ko-sroberta": {
        "id": "jhgan/ko-sroberta-multitask",
        "name": "한글 특화 (ko-sRoBERTa)",
        "dim": 768
    }
}


@app.get("/embedding-models")
async def get_embedding_models():
    """지원되는 임베딩 모델 목록 조회 API"""
    return {
        "models": EMBEDDING_MODELS,
        "current": getattr(state, 'current_embedding_model', 'auto')
    }


@app.post("/set-embedding-model")
async def set_embedding_model(request_data: dict = None):
    """
    임베딩 모델 변경 및 VectorDB 재초기화
    
    Request Body:
        {"model_key": "ko-sroberta", "model_id": "jhgan/ko-sroberta-multitask"}
    """
    from pydantic import BaseModel
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    
    try:
        # Request body 파싱
        if request_data is None:
            from fastapi import Request
            # FastAPI에서 body 파싱
            import json
            body = await request.body()
            request_data = json.loads(body) if body else {}
        
        model_key = request_data.get("model_key", "auto")
        model_config = EMBEDDING_MODELS.get(model_key, EMBEDDING_MODELS["auto"])
        model_id = request_data.get("model_id") or model_config["id"]
        requested_dim = model_config.get("dim", 384)
        
        # ✅ 기존 데이터의 임베딩 차원 확인
        existing_dim = 384  # 기본값 (paraphrase-multilingual-MiniLM-L12-v2)
        try:
            import chromadb
            chroma_path = "/app/chroma_db"
            if not os.path.exists(os.path.join(chroma_path, "chroma.sqlite3")):
                chroma_path = "/workspace/chroma_db"
            client = chromadb.PersistentClient(path=chroma_path)
            collection = client.get_collection("langchain")
            if collection.count() > 0:
                sample = collection.peek(1)
                if sample and sample.get("embeddings"):
                    existing_dim = len(sample["embeddings"][0])
        except Exception as e:
            logger.warning(f"기존 임베딩 차원 확인 실패: {e}")
        
        # ✅ 차원 불일치 시 거부
        if requested_dim != existing_dim:
            return {
                "ok": False,
                "error": f"⚠️ 임베딩 차원 불일치! 기존 데이터: {existing_dim}차원, 요청된 모델: {requested_dim}차원. 데이터를 다시 인덱싱해야 합니다."
            }
        
        logger.info(f"🔄 Changing embedding model to: {model_key} ({model_id})")
        
        # 임베딩 모델 로드
        embeddings = HuggingFaceEmbeddings(
            model_name=model_id,
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # ✅ 기존 ChromaDB 경로 유지 (데이터가 있는 곳)
        state.vectordb = Chroma(
            persist_directory=chroma_path,
            embedding_function=embeddings
            # ✅ collection_name 제거 → 기본값 'langchain' 사용
        )
        
        # 현재 임베딩 모델 저장
        state.current_embedding_model = model_key
        
        logger.info(f"✅ Embedding model changed to: {model_key}")
        
        return {
            "ok": True,
            "model_key": model_key,
            "model_id": model_id,
            "chroma_path": chroma_path,
            "message": f"임베딩 모델이 '{model_key}'로 변경되었습니다."
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to change embedding model: {e}")
        return {
            "ok": False,
            "error": str(e)
        }
