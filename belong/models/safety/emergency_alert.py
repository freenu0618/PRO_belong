# belong/models/safety/emergency_alert.py
"""EmergencyAlert ORM 모델 - 신고 이력"""

from belong.extensions import db
from datetime import datetime
from sqlalchemy import Sequence


class EmergencyAlert(db.Model):
    """
    긴급 신고 이력 테이블

    SafetyEvent에서 신뢰도가 높은 사고 발생 시
    자동으로 생성되는 신고 레코드
    """

    __tablename__ = "EMERGENCY_ALERT"

    id = db.Column(
        db.Integer,
        Sequence("EMERGENCY_ALERT_ID_SEQ"),
        primary_key=True
    )

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("SAFETY_EVENT.id"),
        nullable=False,
        unique=True,  # 1:1 관계
        index=True
    )

    # 신고 내용
    event_type = db.Column(
        db.String(50),
        nullable=False,
        comment="사고 유형: fall, fire, violence"
    )
    confidence = db.Column(
        db.Float,
        nullable=False,
        comment="신뢰도 (0.0 - 1.0)"
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # 상태 관리
    status = db.Column(
        db.String(50),
        default="pending",
        nullable=False,
        index=True,
        comment="pending, sent, responded, cancelled"
    )

    # 응답 정보
    responder_name = db.Column(
        db.String(100),
        nullable=True,
        comment="응답자 이름"
    )
    responded_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="응답 시간"
    )
    response_note = db.Column(
        db.Text,
        nullable=True,
        comment="응답 메모"
    )

    # 노인 정보 (암호화 필요)
    elderly_name_encrypted = db.Column(
        db.LargeBinary,
        nullable=True,
        comment="노인 이름 (AES-256 암호화)"
    )
    elderly_phone_encrypted = db.Column(
        db.LargeBinary,
        nullable=True,
        comment="노인 전화번호 (AES-256 암호화)"
    )

    # Relationships
    event = db.relationship(
        "SafetyEvent",
        foreign_keys=[event_id],
        backref="alerts"
    )

    def __repr__(self):
        return f"<EmergencyAlert id={self.id} event_id={self.event_id} status={self.status}>"

    def to_dict(self):
        """JSON 직렬화를 위한 딕셔너리 변환 (암호화된 정보 제외)"""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "responder_name": self.responder_name,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "response_note": self.response_note
        }
