# belong/services/ai/rag.py
"""
RAG (Retrieval-Augmented Generation) 서비스
- 질의응답 (QA)
- 문서 재순위 (Rerank)
- 문서 업로드/인덱싱
"""

import os
import requests
from belong.extensions import logger
from .model_loader import ModelLoaderService, UTILITY_MODELS
from .chat import AIChatService


class RAGService:
    """
    RAG 전용 서비스
    
    역할:
    - 질의응답 (context 기반 또는 RAG 기반)
    - 문서 재순위 (Reranker)
    - 문서 업로드 및 벡터 인덱싱
    """
    
    def __init__(self, loader: ModelLoaderService = None):
        self._loader = loader or ModelLoaderService()
        self._chat = AIChatService(self._loader)
    
    def answer_question(
        self, 
        question: str, 
        context: str = None, 
        model: str = None, 
        use_rag: bool = False
    ) -> dict:
        """
        질의응답
        
        Args:
            question: 질문
            context: 지문 (use_rag=False일 때 필수)
            model: 사용할 모델
            use_rag: RAG 사용 여부
            
        Returns:
            {"answer": "답변", "score": 0-100 (optional)}
        """
        if use_rag:
            res = self._chat._call_runpod(question, use_rag=True)
            return {"answer": res}
        
        if not context:
            return {"answer": "[QA 실패] context가 필요합니다."}
        
        model_id = UTILITY_MODELS["qa"]
        
        try:
            qa = self._loader.get_pipeline("question-answering", model_id)
            if qa is None:
                return {"answer": f"[QA 실패] 모델 로드 실패: {model_id}"}
            
            result = qa(question=question, context=context)
            
            if isinstance(result, dict) and "answer" in result:
                return {
                    "answer": result["answer"],
                    "score": round(result.get("score", 0.0) * 100, 1)
                }
            
            return {"answer": str(result)}
            
        except Exception as e:
            logger.error(f"QA error: {e}")
            return {"answer": f"[QA 실패] {str(e)}"}
    
    def rerank(self, query: str, documents: list, model: str = None) -> dict:
        """
        문서 재순위 (RAG 품질 향상용)
        
        Args:
            query: 검색 쿼리
            documents: 재순위할 문서 리스트 (최대 10개)
            
        Returns:
            {"ranked_documents": [{"text": "...", "score": 0.95}, ...]}
        """
        # NOTE: Reranker는 sentence-transformers 방식으로 로컬 실행이 복잡함
        # 현재는 fallback으로 원본 순서 반환
        logger.warning("Rerank: 로컬 모델 미지원 - 원본 순서 유지 fallback 사용")
        
        return {
            "ranked_documents": [
                {"text": doc, "score": 1.0 - (i * 0.05)} 
                for i, doc in enumerate(documents[:10])
            ],
            "message": "Reranker 로컬 미지원 - 원본 순서 유지"
        }
    
    def upload_document(self, file_storage) -> dict:
        """
        RunPod Inference Server로 문서 업로드 (RAG Ingestion)
        
        Args:
            file_storage: Flask FileStorage 객체
            
        Returns:
            {"ok": True, "message": "...", "chunks": N}
        """
        api_url = os.environ.get("RUNPOD_ENDPOINT_URL")
        
        # Mock Mode
        if not api_url or "mock" in api_url:
            return {
                "ok": True,
                "message": f"[Mock] File '{file_storage.filename}' uploaded successfully.",
                "chunks": 15
            }
        
        try:
            files = {
                'file': (file_storage.filename, file_storage.read(), file_storage.content_type)
            }
            base_url = api_url.replace("/generate", "")
            ingest_url = f"{base_url}/ingest"
            
            resp = requests.post(ingest_url, files=files, timeout=60)
            resp.raise_for_status()
            return resp.json()
            
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            return {
                "ok": False,
                "message": f"Upload failed: {str(e)}"
            }
