# belong/services/ai/chat.py
"""
채팅/대화 서비스
- RunPod Llama 3 파인튜닝 모델 호출
- 일반 챗봇 대화
"""

import os
import requests
from belong.extensions import logger
from .model_loader import ModelLoaderService


class AIChatService:
    """
    AI 채팅 전용 서비스 (기존 ChatService와 구분)
    
    역할:
    - RunPod Inference Server로 요청 전송
    - Llama 3 프롬프트 템플릿 적용
    """
    
    def __init__(self, loader: ModelLoaderService = None):
        self._loader = loader or ModelLoaderService()
    
    def _call_runpod(
        self, 
        prompt: str, 
        max_tokens: int = 512, 
        temperature: float = 0.7, 
        **kwargs
    ) -> str:
        """
        RunPod Custom Inference Server로 요청 전송
        
        Args:
            prompt: 프롬프트 텍스트
            max_tokens: 최대 생성 토큰 수
            temperature: 샘플링 온도
            
        Returns:
            생성된 텍스트
        """
        api_url = os.environ.get("RUNPOD_ENDPOINT_URL")
        
        # Mock Mode
        if not api_url or "mock" in api_url:
            logger.warning(f"[Mock] AI Call: {prompt[:50]}...")
            if "Translate" in prompt:
                return "이것은 테스트 번역 결과입니다. (Mock Translation)"
            if "Summarize" in prompt:
                return "이것은 테스트 요약 결과입니다. (Mock Summary)"
            return "안녕하세요! 저는 AI (Mock Mode) 입니다."
        
        headers = {"Content-Type": "application/json"}
        
        # URL Auto-Correction
        if api_url and not api_url.endswith("/generate"):
            api_url = f"{api_url.rstrip('/')}/generate"
        
        payload = {
            "prompt": prompt,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }
        payload.update(kwargs)
        
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            # ✅ Return full response for sources access
            return data
        except Exception as e:
            logger.error(f"RunPod API Call Failed: {e}")
            return {"output": f"AI Error: {str(e)}"}
    
    def chat(self, text: str, model: str = None, options: dict = None) -> dict:
        """
        일반 챗봇 대화
        
        Args:
            text: 사용자 입력
            model: 사용할 모델 (선택)
            options: 추가 옵션 (max_new_tokens, use_rag, use_db_rag 등)
            
        Returns:
            {"response": "AI 응답", "sources": [...]}  # RAG 사용 시 출처 포함
        """
        opts = options or {}
        max_tokens = opts.pop('max_new_tokens', 512)
        use_db_rag = opts.pop('use_db_rag', True)  # ✅ 기본적으로 DB RAG 활성화
        
        # ✅ DB RAG: 질문에서 지역/연도 추출하여 DB 데이터 컨텍스트 추가
        db_context = ""
        if use_db_rag:
            try:
                from belong.services.ai.db_rag import get_db_context
                from belong.extensions import db
                db_context = get_db_context(text, db.session)
                if db_context:
                    logger.info(f"📊 DB RAG Context added ({len(db_context)} chars)")
            except Exception as e:
                logger.warning(f"DB RAG failed: {e}")
        
        # ✅ DB 컨텍스트가 있으면 질문에 추가
        prompt_text = text
        if db_context:
            prompt_text = f"{db_context}\n\n---\n사용자 질문: {text}"
        
        result = self._call_runpod(prompt_text, max_tokens=max_tokens, model=model, **opts)
        
        # ✅ Build response with optional sources
        response = {"response": result.get("output", str(result))}
        if "sources" in result:
            response["sources"] = result["sources"]
        if db_context:
            response["db_context_used"] = True
        return response
