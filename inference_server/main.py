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
    """서버 시작 시 모델 및 MCP 서버 초기화"""
    # 1. AI 모델 로딩
    await model_loader.load_models()

    # 2. MCP 서버 초기화
    logger.info("[Startup] Initializing MCP Server...")
    try:
        from inference_server.mcp import BelongMCPServer
        state.mcp_server = BelongMCPServer()
        logger.info("[Startup] MCP Server initialized successfully")

        # MCP Tool 목록 출력
        tools = state.mcp_server.get_available_tools()
        logger.info(f"[Startup] Available MCP Tools: {tools}")
    except Exception as e:
        logger.error(f"[Startup] Failed to initialize MCP Server: {e}", exc_info=True)
        logger.warning("[Startup] Server will run without MCP support")


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


@app.get("/adapters")
async def get_available_adapters():
    """
    사용 가능한 LoRA 어댑터 목록 조회 API
    
    Returns:
        {
            "ok": true,
            "adapters": [
                {
                    "name": "lora_best_r32_checkpoint-1000",
                    "path": "/app/belong/ml/fine_tune/lora_best_r32/checkpoint-1000",
                    "type": "checkpoint"
                },
                {
                    "name": "lora_light_r16_checkpoint-100",
                    "path": "/app/belong/ml/fine_tune/lora_light_r16/checkpoint-100",
                    "type": "checkpoint"
                }
            ],
            "base_model": {
                "name": "base",
                "display_name": "Llama-3-8B (Base)",
                "description": "Fine-tuning 없는 기본 모델"
            }
        }
    """
    # model_loader에서 탐색된 어댑터 리스트 가져오기
    from .services.model_loader import _discover_adapters
    
    try:
        discovered_adapters = _discover_adapters()
        
        # UI 친화적 형식으로 변환
        adapter_list = []
        for adapter in discovered_adapters:
            adapter_list.append({
                "name": adapter["name"],
                "path": adapter["path"],
                "type": adapter.get("type", "unknown"),
                "display_name": adapter["name"].replace("_checkpoint", " (ckpt)").replace("_", " ").title()
            })
        
        return {
            "ok": True,
            "adapters": adapter_list,
            "base_model": {
                "name": "base",
                "display_name": "Llama-3-8B (Base)",
                "description": "Fine-tuning 없는 기본 모델"
            },
            "count": len(adapter_list)
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to get adapters: {e}")
        return {
            "ok": False,
            "error": str(e),
            "adapters": [],
            "base_model": {
                "name": "base",
                "display_name": "Llama-3-8B (Base)",
                "description": "Fine-tuning 없는 기본 모델"
            }
        }

