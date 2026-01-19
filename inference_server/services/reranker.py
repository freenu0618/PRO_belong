"""
Reranker 서비스 - 검색된 문서의 관련성 재평가
BAAI/bge-reranker-v2-m3 모델 사용 (한글 성능 우수)
"""
import logging
from typing import List, Tuple
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class RerankerService:
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Reranker 모델 로드 (CPU에서 실행)"""
        if self._model is None:
            try:
                logger.info("🔄 Loading Reranker model (bge-reranker-v2-m3)...")
                # ✅ CPU에서 실행하여 GPU 메모리 충돌 방지
                self._model = CrossEncoder(
                    'BAAI/bge-reranker-v2-m3',
                    max_length=512,
                    device='cpu'
                )
                logger.info("✅ Reranker model loaded successfully!")
            except Exception as e:
                logger.error(f"❌ Failed to load Reranker model: {e}")
                self._model = None
        return self._model is not None
    
    def rerank(self, query: str, documents: list, top_k: int = 3) -> List[Tuple]:
        """
        문서를 질문과의 관련성으로 재정렬
        
        Args:
            query: 사용자 질문
            documents: 검색된 문서 리스트 (Document 객체)
            top_k: 반환할 상위 문서 개수
            
        Returns:
            [(doc, score), ...] 형태의 리스트
        """
        if not documents:
            return []
        
        if self._model is None:
            logger.warning("Reranker not loaded, returning original documents")
            return [(doc, 1.0) for doc in documents[:top_k]]
        
        try:
            # 쿼리-문서 쌍 생성
            pairs = [[query, doc.page_content] for doc in documents]
            
            # 점수 계산
            scores = self._model.predict(pairs)
            
            # 문서와 점수 결합 후 정렬
            doc_scores = list(zip(documents, scores))
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Top K 반환
            result = doc_scores[:top_k]
            
            logger.info(f"📊 Reranked {len(documents)} docs → Top {top_k} (scores: {[f'{s:.3f}' for _, s in result]})")
            return result
            
        except Exception as e:
            logger.error(f"Rerank failed: {e}")
            return [(doc, 1.0) for doc in documents[:top_k]]

# 싱글톤 인스턴스
reranker = RerankerService()
