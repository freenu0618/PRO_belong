# inference_server/schemas.py
"""Pydantic 요청/응답 스키마"""

from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    """텍스트 생성 요청"""
    prompt: str
    user_query: Optional[str] = None  # ✅ RAG 검색용 원본 질문 (없으면 prompt에서 추출)
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    model: str = "lora_best_r32"
    use_rag: bool = False


class TrainRequest(BaseModel):
    """파인튜닝 학습 요청 (model_name만 필수, 나머지는 Optional)"""
    model_name: str  # 필수: 저장될 모델명
    
    # Optional: 사용자가 안 보내면 기본값 사용
    max_steps: Optional[int] = 100
    warmup_steps: Optional[int] = 10
    learning_rate: Optional[float] = 2e-4
    eval_steps: Optional[int] = 20
    save_steps: Optional[int] = 20
    weight_decay: Optional[float] = 0.01
    optim: Optional[str] = "adamw_torch"
    evaluation_strategy: Optional[str] = "steps"
    save_strategy: Optional[str] = "steps"
    quantization: Optional[str] = "4bit"  # "4bit", "8bit", "none"
    use_double_quant: Optional[bool] = True
