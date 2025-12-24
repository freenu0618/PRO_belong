# belong/services/ai/memory.py
"""
대화 메모리 서비스 (ChromaDB 기반)
- 사용자별 대화 기록 저장
- 관련 대화 검색 (RAG)
"""

import chromadb
from chromadb.config import Settings
from belong.extensions import logger

# ChromaDB 클라이언트 (영구 저장)
_chroma_client = None
_collection_cache = {}


def get_chroma_client():
    """ChromaDB 클라이언트 가져오기 (싱글톤)"""
    global _chroma_client
    if _chroma_client is None:
        # 영구 저장 경로 설정 (RunPod persistent volume)
        _chroma_client = chromadb.PersistentClient(path="/workspace/data/chromadb")
        logger.info("🧠 ChromaDB client initialized")
    return _chroma_client


def get_user_collection(user_id: int):
    """사용자별 컬렉션 가져오기 (없으면 생성)"""
    collection_name = f"user_{user_id}_memory"
    
    if collection_name in _collection_cache:
        return _collection_cache[collection_name]
    
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": f"User {user_id} conversation memory"}
    )
    _collection_cache[collection_name] = collection
    logger.info(f"📚 Collection created/loaded: {collection_name}")
    
    return collection


class MemoryService:
    """
    대화 메모리 서비스
    
    사용법:
        memory = MemoryService(user_id=1)
        memory.save("내 이름은 이영욱이야")
        results = memory.search("내 이름이 뭐야?")
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.collection = get_user_collection(user_id)
    
    def save(self, text: str, role: str = "user", metadata: dict = None) -> str:
        """
        대화 내용 저장
        
        Args:
            text: 저장할 텍스트
            role: "user" 또는 "assistant"
            metadata: 추가 메타데이터
            
        Returns:
            저장된 문서 ID
        """
        import uuid
        from datetime import datetime
        
        doc_id = str(uuid.uuid4())
        
        doc_metadata = {
            "role": role,
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            doc_metadata.update(metadata)
        
        self.collection.add(
            documents=[text],
            metadatas=[doc_metadata],
            ids=[doc_id]
        )
        
        logger.debug(f"💾 Memory saved: {text[:50]}... (id={doc_id})")
        return doc_id
    
    def search(self, query: str, n_results: int = 5) -> list:
        """
        관련 대화 검색
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            
        Returns:
            [{"text": "...", "role": "user", "score": 0.95}, ...]
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results or not results.get("documents"):
            return []
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
        distances = results["distances"][0] if results.get("distances") else [0] * len(documents)
        
        output = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            output.append({
                "text": doc,
                "role": meta.get("role", "user"),
                "score": max(0, 1 - dist),  # 거리를 유사도로 변환 (음수 방지)
                "timestamp": meta.get("timestamp", "")
            })
        
        return output
    
    def get_context(self, query: str, max_tokens: int = 500) -> str:
        """
        검색 결과를 LLM 컨텍스트 문자열로 변환
        
        Args:
            query: 검색 쿼리
            max_tokens: 최대 토큰 수 (대략적인 글자 수로 계산)
            
        Returns:
            컨텍스트 문자열
        """
        results = self.search(query, n_results=10)
        
        if not results:
            return ""
        
        context_parts = []
        total_len = 0
        
        for r in results:
            entry = f"[{r['role']}]: {r['text']}"
            if total_len + len(entry) > max_tokens * 2:  # 대략 2자 = 1토큰
                break
            context_parts.append(entry)
            total_len += len(entry)
        
        if context_parts:
            return "이전 대화 기록:\n" + "\n".join(context_parts)
        return ""
    
    def clear(self) -> int:
        """모든 메모리 삭제"""
        # 컬렉션의 모든 문서 삭제
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)
            logger.info(f"🗑️ Cleared {len(all_ids)} memories for user {self.user_id}")
            return len(all_ids)
        return 0
