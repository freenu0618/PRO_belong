# belong/services/ai/model_loader.py
"""
모델 로딩 및 캐시 관리 서비스
- Transformers pipeline lazy loading
- GPU/CPU 디바이스 관리
- 모델 프리로딩
"""

import torch
from belong.extensions import logger

# 디바이스 감지 (CUDA > CPU)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 유틸리티 도구 모델 ID
UTILITY_MODELS = {
    # 번역 - SMaLL-100 다국어 모델 (300M, 정확도 높음)
    "translate_ko_en": "alirezamsh/small100",  # 한→영
    "translate_en_ko": "alirezamsh/small100",  # 영→한
    
    # 요약
    "summarize": "facebook/bart-large-cnn",
    
    # 감정 분석
    "sentiment": "nlptown/bert-base-multilingual-uncased-sentiment",
    
    # 개체명 인식 (NER)
    "ner": "dslim/bert-base-NER",
    
    # Reranker
    "reranker": "BAAI/bge-reranker-v2-m3",
    
    # 텍스트 생성 - Qwen2.5 Instruct (한국어 지원, 지시 따르기 우수)
    "text_gen": "Qwen/Qwen2.5-0.5B-Instruct",
    
    # Q&A
    "qa": "deepset/roberta-base-squad2"
}

# 모델 캐시 (lazy loading)
_model_cache = {}


class ModelLoaderService:
    """
    모델 로딩 및 캐시 관리 서비스
    
    역할:
    - Transformers pipeline lazy loading
    - GPU/CPU 디바이스 자동 감지
    - 모델 캐싱으로 재로딩 방지
    """
    
    def __init__(self):
        logger.info(f"🔧 ModelLoaderService initialized (device: {DEVICE})")
    
    @staticmethod
    def get_device() -> str:
        """현재 사용 중인 디바이스 반환"""
        return DEVICE
    
    @staticmethod
    def get_model_id(key: str) -> str:
        """모델 키로 HuggingFace 모델 ID 조회"""
        return UTILITY_MODELS.get(key, key)
    
    @staticmethod
    def get_pipeline(task: str, model_id: str):
        """
        Transformers pipeline을 lazy loading으로 가져옴
        
        ⚠️ 유틸리티 모델은 CPU 강제 사용 (Llama-3가 GPU 점유)
        
        Args:
            task: pipeline task (예: "translation", "summarization")
            model_id: HuggingFace 모델 ID
            
        Returns:
            transformers.Pipeline 또는 None (실패 시)
        """
        from transformers import pipeline
        
        cache_key = f"{task}:{model_id}"
        
        if cache_key not in _model_cache:
            # ✅ 유틸리티 모델은 CPU 강제 (GPU는 Llama-3 전용)
            logger.info(f"📥 Loading model: {model_id} (task: {task}) on CPU...")
            try:
                _model_cache[cache_key] = pipeline(
                    task,
                    model=model_id,
                    device=-1  # -1 = CPU (GPU 메모리 충돌 방지)
                )
                logger.info(f"✅ Model loaded on CPU: {model_id}")
            except Exception as e:
                logger.error(f"❌ Failed to load model {model_id}: {e}")
                return None
        
        return _model_cache[cache_key]

    
    def preload_models(self) -> None:
        """서버 시작 시 주요 모델 미리 로드 (선택적)"""
        logger.info("🚀 Preloading utility models...")
        
        # 번역 모델만 미리 로드 (가장 많이 사용)
        try:
            self.get_pipeline("translation", UTILITY_MODELS["translate_ko_en"])
            self.get_pipeline("translation", UTILITY_MODELS["translate_en_ko"])
            logger.info("✅ Translation models preloaded")
        except Exception as e:
            logger.warning(f"⚠️ Preload warning: {e}")


# ============================================
# 모듈 레벨 함수 (기존 코드 호환용)
# ============================================
def get_pipeline(task: str, model_id: str):
    """모듈 레벨 get_pipeline (기존 호환)"""
    return ModelLoaderService.get_pipeline(task, model_id)


def preload_models():
    """모듈 레벨 preload_models (기존 호환)"""
    loader = ModelLoaderService()
    loader.preload_models()
