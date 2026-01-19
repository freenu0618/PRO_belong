# inference_server/mcp/tools/rag_tool.py
"""RagTool - ChromaDB 문서 검색 도구"""

import logging
from typing import Dict, Any

from .base import BaseTool

logger = logging.getLogger(__name__)


class RagTool(BaseTool):
    """
    ChromaDB에 업로드된 문서에서 관련 정보 검색

    기능:
    - 의미적 유사도 기반 문서 검색
    - state.vectordb (ChromaDB) 사용
    - 검색 결과 개수 조절 (top_k)
    """

    def get_schema(self) -> Dict[str, Any]:
        """
        Tool Schema (OpenAI Function Calling 표준 형식)

        Returns:
            {
                "type": "function",
                "function": {
                    "name": "rag_search",
                    "description": "...",
                    "parameters": {...}
                }
            }
        """
        return {
            "type": "function",
            "function": {
                "name": "rag_search",
                "description": (
                    "ChromaDB에 업로드된 문서(PDF, TXT)에서 관련 정보를 검색합니다. "
                    "의미적 유사도 기반으로 가장 관련성 높은 문서 조각을 반환합니다."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색 쿼리 (예: '독거노인 복지 정책', '고독사 예방 방안')",
                            "minLength": 2
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "반환할 문서 개수 (기본값: 3)",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        문서 검색 실행 (비동기)

        Args:
            arguments: {
                "query": "검색 쿼리" (필수),
                "top_k": 3 (선택)
            }

        Returns:
            {
                "success": True,
                "documents": [
                    {
                        "rank": 1,
                        "content": "문서 내용...",
                        "metadata": {
                            "source": "파일명.pdf",
                            "page": 12
                        },
                        "score": 0.85
                    },
                    ...
                ],
                "sources": ["파일명.pdf", ...],
                "count": 3
            }
            또는
            {
                "success": False,
                "error": "에러 메시지"
            }
        """
        from inference_server import state

        # VectorDB 확인
        if state.vectordb is None:
            logger.error("[RagTool] VectorDB not initialized")
            return {
                "success": False,
                "error": "VectorDB not initialized. Please upload documents first."
            }

        # 인자 추출
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 3)

        if not query:
            return {
                "success": False,
                "error": "Query parameter is required"
            }

        logger.info(f"[RagTool] Searching: query='{query}', top_k={top_k}")

        try:
            # ChromaDB similarity_search (동기 함수)
            # LangChain의 Chroma는 동기 API만 제공하므로 asyncio.to_thread 사용
            import asyncio
            results = await asyncio.to_thread(
                state.vectordb.similarity_search_with_score,
                query,
                k=top_k
            )

            # 결과 포맷팅
            documents = []
            sources = set()

            for rank, (doc, score) in enumerate(results, start=1):
                # 문서 정보
                doc_info = {
                    "rank": rank,
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": round(float(score), 3)
                }
                documents.append(doc_info)

                # 출처 추출
                if "source" in doc.metadata:
                    sources.add(doc.metadata["source"])

            logger.info(f"[RagTool] Found {len(documents)} documents")

            return {
                "success": True,
                "documents": documents,
                "sources": list(sources),
                "count": len(documents)
            }

        except Exception as e:
            logger.error(f"[RagTool] Search failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
