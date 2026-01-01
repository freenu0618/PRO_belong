# belong/services/ai/training.py
"""
파인튜닝 학습 관리 서비스
- inference_server.py의 /train 엔드포인트 호출
- 학습 상태 조회
"""

import os
import requests
from flask import current_app
from belong.extensions import logger


class TrainingService:
    """
    파인튜닝 학습 관리 서비스
    
    역할:
    - inference_server.py의 /train 엔드포인트 호출
    - 학습 상태 조회
    - 사용 가능한 모델 목록 관리
    """
    
    def __init__(self):
        pass
    
    def _get_inference_url(self) -> str:
        """inference server URL 가져오기"""
        # RUNPOD_ENDPOINT_URL 환경변수에서 base URL 추출
        url = os.environ.get("RUNPOD_ENDPOINT_URL", "http://127.0.0.1:8000/generate")
        # /generate 제거하고 base URL만 사용
        return url.replace("/generate", "")
    
    def get_available_models(self) -> list:
        """
        사용 가능한 모델 리스트 반환 (inference server의 /adapters 호출)
        
        Returns:
            ["base", "lora_best_r32_checkpoint-1000", "lora_light_r16_checkpoint-100", ...]
        """
        try:
            # ✅ 새로운 /adapters API 호출
            url = f"{self._get_inference_url()}/adapters"
            logger.info(f"Fetching adapters from: {url}")
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    models = ["base"]  # Base 모델 항상 포함
                    
                    # LoRA adapter 추가
                    adapters = data.get("adapters", [])
                    for adapter in adapters:
                        models.append(adapter["name"])
                    
                    logger.info(f"✅ Found {len(models)} models: {models}")
                    return models
        except Exception as e:
            logger.warning(f"Failed to fetch adapters from inference server: {e}")
        
        # Fallback: Base 모델만 반환
        logger.info("Fallback: returning base model only")
        return ["base"]
    
    def start_training(self, model_name: str, params: dict) -> dict:
        """
        파인튜닝 작업 시작 (inference_server.py의 /train 호출)
        
        Args:
            model_name: 모델 이름
            params: 학습 파라미터 (UI에서 받은 값 그대로)
            
        Returns:
            {"ok": True, "job_id": "...", "status": "started", ...}
        """
        logger.info(f"Starting Fine-tuning: {model_name} with params={params}")
        
        try:
            url = f"{self._get_inference_url()}/train"
            
            payload = {
                "model_name": model_name,
                "max_steps": int(params.get("max_steps", 100)),
                "warmup_steps": int(params.get("warmup_steps", 10)),
                "learning_rate": float(params.get("learning_rate", 2e-4)),
                "eval_steps": int(params.get("eval_steps", 20)),
                "save_steps": int(params.get("save_steps", 20)),
                "weight_decay": float(params.get("weight_decay", 0.01)),
                "optim": params.get("optim", "adamw_torch"),
                "evaluation_strategy": params.get("evaluation_strategy", "steps"),
                "save_strategy": params.get("save_strategy", "steps"),
                "quantization": params.get("quantization", "4bit"),
                "use_double_quant": params.get("use_double_quant", True),
            }
            
            logger.info(f"Calling inference server: {url}")
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Training started: {data}")
                return data
            elif response.status_code == 409:
                return {"ok": False, "error": "이미 학습이 진행 중입니다."}
            else:
                error_msg = response.json().get("detail", "Unknown error")
                return {"ok": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to inference server: {e}")
            return {"ok": False, "error": f"AI 서버 연결 실패: {str(e)}"}
    
    def get_training_status(self, job_id: str) -> dict:
        """
        학습 상태 조회 (inference_server.py의 /train/status 호출)
        
        Args:
            job_id: 작업 ID
            
        Returns:
            {"ok": True, "status": "running/completed", "progress": 0-100, ...}
        """
        try:
            url = f"{self._get_inference_url()}/train/status/{job_id}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"ok": False, "message": "Job not found"}
            else:
                return {"ok": False, "message": "Status check failed"}
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to get training status: {e}")
            return {"ok": False, "message": f"AI 서버 연결 실패: {str(e)}"}

    def delete_model(self, model_name: str) -> dict:
        """
        파인튜닝된 모델 삭제
        
        Args:
            model_name: 삭제할 모델 이름
            
        Returns:
            {"ok": True, "message": "삭제 완료"}
        """
        try:
            url = f"{self._get_inference_url()}/train/models/{model_name}"
            logger.info(f"Deleting model: {url}")
            
            response = requests.delete(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"ok": False, "error": f"삭제 실패: {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to delete model: {e}")
            return {"ok": False, "error": f"AI 서버 연결 실패: {str(e)}"}


