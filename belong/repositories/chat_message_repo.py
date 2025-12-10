# belong/repositories/chat_message_repo.py
from typing import List
from belong.extensions import db
from belong.models.chat_message import ChatMessage


class ChatMessageRepository:
    """
    CHAT_MESSAGE 테이블 접근용 레포지토리
    """

    def save(self, user_id: int, role: str, service: str, content: str) -> ChatMessage:
        """
        한 건 저장하고, 저장된 ChatMessage 객체를 그대로 반환
        """
        msg = ChatMessage(
            user_id=user_id,
            role=role,
            service=service,
            content=content,
        )
        db.session.add(msg)
        db.session.commit()
        return msg

    def list_by_user(self, user_id: int, limit: int = 20) -> List[ChatMessage]:
        """
        특정 user_id의 최근 대화 목록 (최신순)
        """
        return (
            ChatMessage.query
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
