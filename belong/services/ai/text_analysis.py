# belong/services/ai/text_analysis.py
"""
텍스트 분석 서비스
- 요약, 감정 분석, 개체명 인식 (NER)
- 로컬 GPU transformers pipeline 사용
"""

from belong.extensions import logger
from .model_loader import ModelLoaderService, UTILITY_MODELS


class TextAnalysisService:
    """
    텍스트 분석 전용 서비스
    
    지원:
    - summarize: 텍스트 요약
    - analyze_sentiment: 감정 분석
    - analyze_entities: 개체명 인식 (NER)
    """
    
    def __init__(self, loader: ModelLoaderService = None):
        self._loader = loader or ModelLoaderService()
    
    def summarize(self, text: str) -> dict:
        """
        텍스트 요약
        
        Args:
            text: 요약할 텍스트 (최대 1024자 처리)
            
        Returns:
            {"summary": "요약된 텍스트"}
        """
        model_id = UTILITY_MODELS["summarize"]
        max_chars = 1024
        truncated = text[:max_chars] if len(text) > max_chars else text
        
        try:
            summarizer = self._loader.get_pipeline("summarization", model_id)
            if summarizer is None:
                return {"summary": f"[요약 실패] 모델 로드 실패: {model_id}"}
            
            result = summarizer(truncated, max_length=130, min_length=30)
            
            if isinstance(result, list) and len(result) > 0:
                return {"summary": result[0].get("summary_text", "")}
            
            return {"summary": str(result)}
            
        except Exception as e:
            logger.error(f"Summarize error: {e}")
            return {"summary": f"[요약 실패] {str(e)}"}
    
    def analyze_sentiment(self, text: str) -> dict:
        """
        감정 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            {"label": "1 star" ~ "5 stars", "score": 0-100}
        """
        model_id = UTILITY_MODELS["sentiment"]
        
        try:
            classifier = self._loader.get_pipeline("text-classification", model_id)
            if classifier is None:
                return {"label": "ERROR", "score": 0.0, "message": f"모델 로드 실패: {model_id}"}
            
            result = classifier(text)
            
            if isinstance(result, list) and len(result) > 0:
                top = result[0]
                return {
                    "label": top.get("label", "UNKNOWN"),
                    "score": round(top.get("score", 0.0) * 100, 1)
                }
            
            return {"label": "UNKNOWN", "score": 0.0}
            
        except Exception as e:
            logger.error(f"Sentiment error: {e}")
            return {"label": "ERROR", "score": 0.0, "message": str(e)}
    
    def analyze_entities(self, text: str) -> dict:
        """
        개체명 인식 (NER)
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            {"entities": [{"word": "...", "entity": "PER/ORG/LOC", "score": 0-100}, ...]}
        """
        model_id = UTILITY_MODELS["ner"]
        
        try:
            ner = self._loader.get_pipeline("token-classification", model_id)
            if ner is None:
                return {"entities": [], "message": f"모델 로드 실패: {model_id}"}
            
            result = ner(text)
            
            if isinstance(result, list):
                entities = []
                for item in result:
                    if isinstance(item, dict):
                        entities.append({
                            "word": item.get("word", ""),
                            "text": item.get("word", ""),  # ChatService 호환용
                            "entity": item.get("entity_group", item.get("entity", "")),
                            "score": round(item.get("score", 0.0) * 100, 1)
                        })
                return {"entities": entities}
            
            return {"entities": []}
            
        except Exception as e:
            logger.error(f"NER error: {e}")
            return {"entities": [], "message": str(e)}
