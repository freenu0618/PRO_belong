# belong/models/safety/safety_event.py
"""SafetyEvent ORM 모델 - 사고 이벤트"""

from belong.extensions import db
from datetime import datetime
from sqlalchemy import Sequence


class SafetyEvent(db.Model):
    """
    독거노인 사고 이벤트 테이블

    감지된 사고(낙상, 화재, 폭력 등)를 기록하며,
    EmergencyAlert와 1:1 관계를 가질 수 있음
    """

    __tablename__ = "SAFETY_EVENT"

    id = db.Column(
        db.Integer,
        Sequence("SAFETY_EVENT_ID_SEQ"),
        primary_key=True
    )

    # 사고 유형 및 신뢰도
    event_type = db.Column(
        db.String(50),
        nullable=False,
        comment="사고 유형: fall, fire, violence, abnormal"
    )
    confidence = db.Column(
        db.Float,
        nullable=False,
        comment="신뢰도 (0.0 - 1.0)"
    )
    detected_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # 위치 정보
    region_id = db.Column(
        db.Integer,
        db.ForeignKey("REGION.id"),
        nullable=False,
        index=True
    )
    location_detail = db.Column(
        db.String(200),
        nullable=True,
        comment="상세 주소 (암호화 필요)"
    )

    # 스트림 정보
    stream_id = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )
    frame_timestamp = db.Column(
        db.Float,
        nullable=True,
        comment="프레임 타임스탬프 (초)"
    )
    frame_data = db.Column(
        db.LargeBinary,
        nullable=True,
        comment="감지된 프레임 (암호화, 30일 보관)"
    )

    # 감지 메타데이터 (JSON)
    detection_metadata = db.Column(
        db.JSON,
        nullable=True,
        comment="YOLOv8 결과, 키포인트 등"
    )

    # 신고 정보
    alert_sent = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )
    alert_id = db.Column(
        db.Integer,
        db.ForeignKey("EMERGENCY_ALERT.id"),
        nullable=True
    )

    # Relationships
    region = db.relationship("Region", backref="safety_events")

    def __repr__(self):
        return f"<SafetyEvent id={self.id} type={self.event_type} confidence={self.confidence:.2f}>"

    def to_dict(self):
        """JSON 직렬화를 위한 딕셔너리 변환 (개인정보 제외)"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "region_id": self.region_id,
            "stream_id": self.stream_id,
            "alert_sent": self.alert_sent,
            "alert_id": self.alert_id
        }
