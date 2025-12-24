# belong/services/ai/__init__.py
"""
AI 서비스 패키지

하이브리드 AI 서비스:
- 유틸리티 도구: 로컬 GPU transformers
- 채팅/RAG: RunPod Llama 3
- 텍스트 생성: LFM2-350M + ChromaDB 메모리
"""

from belong.extensions import logger
from .model_loader import ModelLoaderService, UTILITY_MODELS
from .translation import TranslationService
from .text_analysis import TextAnalysisService
from .chat import AIChatService
from .rag import RAGService
from .text_gen import TextGenerationService
from .training import TrainingService


class AIService:
    """
    기존 API 100% 호환 Facade
    
    모든 AI 기능을 단일 인터페이스로 제공하며,
    내부적으로 전문화된 서비스에 위임합니다.
    """
    
    def __init__(self):
        self._loader = ModelLoaderService()
        self._translation = TranslationService(self._loader)
        self._analysis = TextAnalysisService(self._loader)
        self._chat = AIChatService(self._loader)
        self._rag = RAGService(self._loader)
        self._text_gen = TextGenerationService(self._loader)
        self._training = TrainingService()
        
        logger.info("🧠 AIService (Facade) initialized")
    
    # ========== Translation ==========
    def translate(self, text: str, direction: str = "ko-en", model: str = None) -> dict:
        return self._translation.translate(text, direction)
    
    # ========== Text Analysis ==========
    def summarize(self, text: str, model: str = None) -> dict:
        return self._analysis.summarize(text)
    
    def analyze_sentiment(self, text: str, model: str = None) -> dict:
        return self._analysis.analyze_sentiment(text)
    
    def analyze_entities(self, text: str, model: str = None) -> dict:
        return self._analysis.analyze_entities(text)
    
    # ========== Chat ==========
    def chat(self, text: str, model: str = None, options: dict = None) -> dict:
        return self._chat.chat(text, model, options)
    
    # ========== RAG ==========
    def answer_question(
        self, question: str, context: str = None, 
        model: str = None, use_rag: bool = False
    ) -> dict:
        return self._rag.answer_question(question, context, model, use_rag)
    
    def rerank(self, query: str, documents: list, model: str = None) -> dict:
        return self._rag.rerank(query, documents, model)
    
    def upload_document(self, file_storage) -> dict:
        return self._rag.upload_document(file_storage)
    
    # ========== Text Generation (with Memory) ==========
    def generate_text(
        self, prompt: str, user_id: int = None,
        use_memory: bool = True, save_to_memory: bool = True
    ) -> dict:
        """텍스트 생성 (메모리 기능 포함)"""
        return self._text_gen.generate(
            prompt, user_id=user_id, 
            use_memory=use_memory, 
            save_to_memory=save_to_memory
        )
    
    def clear_memory(self, user_id: int) -> dict:
        """사용자 메모리 초기화"""
        return self._text_gen.clear_memory(user_id)
    
    # ========== Training ==========
    def get_available_models(self) -> list:
        return self._training.get_available_models()
    
    def start_training(self, model_name: str, params: dict) -> dict:
        return self._training.start_training(model_name, params)
    
    def get_training_status(self, job_id: str) -> dict:
        return self._training.get_training_status(job_id)
    
    # ========== Utility ==========
    def get_utility_models(self) -> dict:
        """사용 가능한 유틸리티 모델 목록 반환"""
        return {
            name: {
                "model_id": model_id,
                "description": self._get_model_description(name)
            }
            for name, model_id in UTILITY_MODELS.items()
        }
    
    def _get_model_description(self, name: str) -> str:
        """모델별 설명 반환"""
        descriptions = {
            "translate_ko_en": "한국어 → 영어 번역",
            "translate_en_ko": "영어 → 한국어 번역",
            "summarize": "텍스트 요약 (영문)",
            "sentiment": "감정 분석 (다국어)",
            "ner": "개체명 인식 (영문)",
            "reranker": "RAG 문서 재순위 (다국어)",
            "text_gen": "AI 텍스트 생성 (한국어, 메모리 기능)",
            "qa": "질의응답 (영문)"
        }
        return descriptions.get(name, "유틸리티 도구")


# 기존 import 호환용
__all__ = ['AIService', 'ModelLoaderService', 'UTILITY_MODELS']

