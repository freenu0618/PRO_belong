# belong/repositories/chat_message_repo.py
from typing import List

from belong.extensions import db
from belong.models.chat_message import ChatMessage


class ChatMessageRepository:
    """
    CHAT_MESSAGE 테이블 접근용 레포지토리.

    - save_message(user_id, role, service, content)
    - get_recent_messages(user_id, limit)
    - build_context(user_id, limit) : 최근 대화들을 하나의 문자열로 합쳐서 QA context로 사용
    """

    def save_message(
        self,
        user_id: int,
        role: str,
        service: str,
        content: str,
    ) -> ChatMessage:
        msg = ChatMessage(
            user_id=user_id,
            role=role,
            service=service,
            content=content,
        )
        db.session.add(msg)
        db.session.commit()
        return msg

    def get_recent_messages(self, user_id: int, limit: int = 10) -> List[ChatMessage]:
        return (
            ChatMessage.query.filter_by(user_id=user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

    def build_context(self, user_id: int, limit: int = 10) -> str:
        """
        최근 대화 N개를 시간순(오래된 → 최신)으로 이어붙여서
        QA 모델의 context 로 사용할 문자열 생성.
        """
        messages = (
            ChatMessage.query.filter_by(user_id=user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

        # 오래된 순으로 정렬
        messages = list(reversed(messages))

        # "사용자: ~~~\n챗봇: ~~~" 형식으로 합치기
        lines = []
        for m in messages:
            prefix = "사용자" if m.role == "user" else "챗봇"
            lines.append(f"{prefix}: {m.content}")

        return "\n".join(lines)
