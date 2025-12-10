# belong/services/chat_service.py
from typing import Dict, Any, Optional

from belong.repositories.chat_message_repo import ChatMessageRepository
from belong.services.ai_service import AIService
from belong.extensions import logger


class ChatService:
    """
    사용자별 대화 기록 + 모델 호출까지 묶는 서비스 레이어.
    - 질문/답변을 DB에 저장
    - QA의 경우, DB에 저장된 이전 대화들을 context로 사용
    """

    def __init__(
        self,
        chat_repo: Optional[ChatMessageRepository] = None,
        ai_service: Optional[AIService] = None,
    ) -> None:
        self.chat_repo = chat_repo or ChatMessageRepository()
        self.ai_service = ai_service or AIService()

    def _save_user_message(self, user_id: int, service: str, text: str) -> None:
        self.chat_repo.save_message(
            user_id=user_id,
            role="user",
            service=service,
            content=text,
        )

    def _save_bot_message(self, user_id: int, service: str, content: str) -> None:
        self.chat_repo.save_message(
            user_id=user_id,
            role="assistant",
            service=service,
            content=content,
        )

    def process(
        self,
        user_id: int,
        service: str,
        text: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        메인 진입점.
        - user_id: 사용자 식별자
        - service: 'sentiment' | 'entities' | 'qa'
        - text: 사용자의 질문/입력 문장
        - options: QA의 경우 context를 직접 줄 때 사용 (없으면 history 사용)
        """
        options = options or {}
        self._save_user_message(user_id, service, text)

        if service == "sentiment":
            result = self.ai_service.analyze_sentiment(text)
            bot_content = f"감정 분석 결과: {result['label']} (score={result['score']:.2f})"

        elif service == "entities":
            result = self.ai_service.analyze_entities(text)
            ents = [f"{e['text']}({e['entity']})" for e in result["entities"]]
            bot_content = "인식된 개체: " + (", ".join(ents) if ents else "없음")

        elif service == "qa":
            # 1) options.context가 있으면 우선 사용
            explicit_context = (options.get("context") or "").strip()

            if explicit_context:
                context = explicit_context
            else:
                # 2) 없으면 DB에 저장된 최근 대화 N개를 context로 사용
                context = self.chat_repo.build_context(user_id=user_id, limit=10)

            if not context:
                # context가 전혀 없다면, 그냥 text만 가지고 QA 시도
                logger.warning(
                    f"[ChatService] QA without context. user_id={user_id}, text={text}"
                )
                context = text

            result = self.ai_service.answer_question(question=text, context=context)
            bot_content = result["answer"]

        else:
            result = {}
            bot_content = "지원하지 않는 서비스입니다."

        # 챗봇 응답을 DB에 저장
        self._save_bot_message(user_id, service, bot_content)

        # 최근 히스토리 개수
        history_count = len(self.chat_repo.get_recent_messages(user_id))

        return {
            "ok": True,
            "service": service,
            "input": {"text": text},
            "result": result,
            "debug": {
                "mode": "mock",   # UI 협업자랑 약속한 값
                "history_count": history_count,
            },
        }

    def get_history(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        messages = self.chat_repo.get_recent_messages(user_id=user_id, limit=limit)
        items = [
            {
                "role": m.role,
                "service": m.service,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
        return {"ok": True, "user_id": user_id, "history": items}
