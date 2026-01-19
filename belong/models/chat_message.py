# belong/models/chat_message.py
from datetime import datetime

from sqlalchemy import Sequence
from belong.extensions import db


class ChatMessage(db.Model):
    """
    사용자별 챗봇 대화 로그 저장용 테이블.

    - user_id: belong.models.user.User 의 PK를 FK로 사용
    - role: 'user' or 'assistant'
    - service: 'sentiment', 'entities', 'qa' 등 어떤 AI 서비스인지
    """
    __tablename__ = "CHAT_MESSAGE"

    id = db.Column(
        db.Integer,
        Sequence("CHAT_MESSAGE_ID_SEQ"),
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )

    role = db.Column(db.String(20), nullable=False, default="user")  # user / assistant
    service = db.Column(db.String(30), nullable=False)               # sentiment / entities / qa / etc
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # User 모델과의 관계 (이미 user.py 에 User 모델 있다고 가정)
    user = db.relationship(
        "User",
        backref=db.backref("chat_messages", lazy=True),
    )
