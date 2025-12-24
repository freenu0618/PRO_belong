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
from . import state
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
    }

    if torch.cuda.is_available():
        status_info["gpu_name"] = torch.cuda.get_device_name(0)
        status_info["gpu_memory_allocated"] = f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB"

    if state.model:
        status_info["device"] = str(state.model.device)

    return status_info
