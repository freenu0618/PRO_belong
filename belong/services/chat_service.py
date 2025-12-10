# belong/services/chat_service.py
from typing import Dict, Any, Optional

from belong.models.chat_message import ChatMessage
from belong.repositories.chat_message_repo import ChatMessageRepository
from belong.services.ai_service import AIService
import json

class ChatService:
    """
    챗봇 + 대화 히스토리 관리 서비스
    """

    def __init__(
        self,
        repo: Optional[ChatMessageRepository] = None,
        ai_service: Optional[AIService] = None,
    ) -> None:
        self.repo = repo or ChatMessageRepository()
        self.ai_service = ai_service or AIService()

    # ---------------------------
    # 내부 헬퍼: ChatMessage -> dict
    # ---------------------------
    def _serialize_message(self, msg: ChatMessage) -> Dict[str, Any]:
        return {
            "id": msg.id,
            "user_id": msg.user_id,
            "role": msg.role,
            "service": msg.service,
            "content": msg.content,
            # datetime 은 JSON 직렬화를 위해 문자열로 변환
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }

    # ---------------------------
    # 외부 API: 한 번의 질문/응답 처리
    # ---------------------------
    def process(
        self,
        user_id: int,
        service: str,
        text: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        1) 사용자의 입력을 CHAT_MESSAGE(user) 로 저장
        2) service 종류에 맞게 AIService 호출
        3) 모델 응답을 CHAT_MESSAGE(assistant) 로 저장
        4) 최종 결과 + 최신 히스토리 리턴
        """

        # 1) 사용자 메시지 저장
        self.repo.save(
            user_id=user_id,
            role="user",
            service=service,
            content=text,
        )

        # 2) AI 서비스 호출
        service = (service or "qa").strip()

        if service == "sentiment":
            result = self.ai_service.analyze_sentiment(text)
            # 사람이 볼 수 있게 간단히 요약 텍스트 생성
            if isinstance(result, dict):
                label = result.get("label")
                score = result.get("score")
                assistant_text = f"감정 분석 결과: {label} (score={score:.3f})" if score is not None else str(result)
            else:
                assistant_text = str(result)

        elif service == "entities":
            result = self.ai_service.analyze_entities(text)
            if isinstance(result, dict):
                entities = result.get("entities", [])
                parts = [
                    f"{e.get('text')}({e.get('entity')})"
                    for e in entities
                ]
                assistant_text = "인식된 개체들: " + ", ".join(parts)
            else:
                assistant_text = str(result)

        elif service == "qa":
            context = (options.get("context") or "").strip()
            result = self.ai_service.answer_question(
                question=text,
                context=context,
            )
            if isinstance(result, dict):
                assistant_text = result.get("answer") or str(result)
            else:
                assistant_text = str(result)
        
        elif service == "chat":
            result = self.ai_service.chat(text)
            assistant_text = result.get("answer", "응답을 생성하지 못했어.")
            
        else:
            # 알 수 없는 service 값인 경우
            result = {"error": f"지원하지 않는 service 입니다: {service}"}
            assistant_text = "지원하지 않는 서비스입니다."

        # 3) 모델 응답을 assistant 역할로 저장
        self.repo.save(
            user_id=user_id,
            role="assistant",
            service=service,
            content=assistant_text,
        )

        # 4) 최신 히스토리 함께 리턴
        history_data = self.get_history(user_id=user_id, limit=20)

        return {
            "ok": True,
            "service": service,
            "user_id": user_id,
            "input": {"text": text},
            "result": result,
            "history": history_data["history"],
            "debug": {"mode": "mock"},
        }

    # ---------------------------
    # 외부 API: 히스토리 조회
    # ---------------------------
    def get_history(self, user_id: int, limit: int = 20) -> Dict[str, Any]:
        messages = self.repo.list_by_user(user_id=user_id, limit=limit)
        history = [self._serialize_message(m) for m in messages]

        return {
            "ok": True,
            "user_id": user_id,
            "history": history,
        }
