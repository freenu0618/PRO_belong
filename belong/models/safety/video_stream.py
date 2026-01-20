# belong/models/safety/video_stream.py
"""VideoStream ORM 모델 - 비디오 스트림 정보"""

from belong.extensions import db
from datetime import datetime
from sqlalchemy import Sequence


class VideoStream(db.Model):
    """
    비디오 스트림 정보 테이블

    CCTV/웹캠 스트림의 메타데이터 및 상태 관리
    """

    __tablename__ = "VIDEO_STREAM"

    id = db.Column(
        db.Integer,
        Sequence("VIDEO_STREAM_ID_SEQ"),
        primary_key=True
    )

    # 스트림 식별 정보
    stream_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="고유 스트림 ID (UUID)"
    )
    stream_url = db.Column(
        db.String(500),
        nullable=False,
        comment="RTSP/HTTP 스트림 URL"
    )

    # 위치 정보
    region_id = db.Column(
        db.Integer,
        db.ForeignKey("REGION.id"),
        nullable=False,
        index=True
    )
    location_name = db.Column(
        db.String(200),
        nullable=True,
        comment="스트림 위치 설명 (예: 강남구 논현동 독거노인 A씨 거실)"
    )

    # 상태 관리
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="활성 상태"
    )
    last_frame_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="마지막 프레임 수신 시간"
    )

    # 통계
    total_events = db.Column(
        db.Integer,
        default=0,
        nullable=False,
        comment="누적 감지 이벤트 수"
    )
    last_event_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="마지막 이벤트 발생 시간"
    )

    # 생성 시간
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    region = db.relationship("Region", backref="video_streams")

    def __repr__(self):
        return f"<VideoStream id={self.id} stream_id={self.stream_id} active={self.is_active}>"

    def to_dict(self):
        """JSON 직렬화를 위한 딕셔너리 변환"""
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "stream_url": self.stream_url,  # 프로덕션에서는 제외 고려
            "region_id": self.region_id,
            "location_name": self.location_name,
            "is_active": self.is_active,
            "last_frame_at": self.last_frame_at.isoformat() if self.last_frame_at else None,
            "total_events": self.total_events,
            "last_event_at": self.last_event_at.isoformat() if self.last_event_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
