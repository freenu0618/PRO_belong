# belong/repositories/safety/safety_event_repo.py
"""SafetyEvent Repository - 사고 이벤트 DB 접근"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_
from belong.extensions import db
from belong.models.safety.safety_event import SafetyEvent


class SafetyEventRepository:
    """
    SafetyEvent 테이블 접근용 Repository

    주요 기능:
    - 사고 이벤트 생성 및 조회
    - 지역별/유형별 필터링
    - 신고 미전송 이벤트 조회
    """

    def create(
        self,
        event_type: str,
        confidence: float,
        region_id: int,
        stream_id: Optional[str] = None,
        location_detail: Optional[str] = None,
        frame_timestamp: Optional[float] = None,
        frame_data: Optional[bytes] = None,
        detection_metadata: Optional[Dict] = None
    ) -> SafetyEvent:
        """
        새로운 사고 이벤트 생성

        Args:
            event_type: 사고 유형 (fall, fire, violence, abnormal)
            confidence: 신뢰도 (0.0 - 1.0)
            region_id: 지역 ID
            stream_id: 스트림 ID (선택)
            location_detail: 상세 주소 (선택, 암호화 필요)
            frame_timestamp: 프레임 타임스탬프 (선택)
            frame_data: 프레임 데이터 (선택, 암호화 필요)
            detection_metadata: 감지 메타데이터 (선택)

        Returns:
            생성된 SafetyEvent 객체
        """
        event = SafetyEvent(
            event_type=event_type,
            confidence=confidence,
            region_id=region_id,
            stream_id=stream_id,
            location_detail=location_detail,
            frame_timestamp=frame_timestamp,
            frame_data=frame_data,
            detection_metadata=detection_metadata,
            detected_at=datetime.utcnow()
        )

        db.session.add(event)
        db.session.commit()
        return event

    def get_by_id(self, event_id: int) -> Optional[SafetyEvent]:
        """ID로 사고 이벤트 조회"""
        return db.session.query(SafetyEvent).filter_by(id=event_id).first()

    def list_by_region(
        self,
        region_id: int,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SafetyEvent]:
        """
        지역별 사고 이벤트 조회

        Args:
            region_id: 지역 ID
            event_type: 사고 유형 필터 (선택)
            start_date: 시작 날짜 (선택)
            end_date: 종료 날짜 (선택)
            limit: 최대 조회 개수

        Returns:
            SafetyEvent 리스트 (최신순)
        """
        query = db.session.query(SafetyEvent).filter_by(region_id=region_id)

        if event_type:
            query = query.filter_by(event_type=event_type)

        if start_date:
            query = query.filter(SafetyEvent.detected_at >= start_date)

        if end_date:
            query = query.filter(SafetyEvent.detected_at <= end_date)

        return query.order_by(desc(SafetyEvent.detected_at)).limit(limit).all()

    def list_by_stream(
        self,
        stream_id: str,
        limit: int = 50
    ) -> List[SafetyEvent]:
        """
        스트림별 사고 이벤트 조회

        Args:
            stream_id: 스트림 ID
            limit: 최대 조회 개수

        Returns:
            SafetyEvent 리스트 (최신순)
        """
        return (
            db.session.query(SafetyEvent)
            .filter_by(stream_id=stream_id)
            .order_by(desc(SafetyEvent.detected_at))
            .limit(limit)
            .all()
        )

    def list_unsent_alerts(
        self,
        confidence_threshold: float = 0.7,
        time_window_minutes: int = 10
    ) -> List[SafetyEvent]:
        """
        신고 미전송 고신뢰도 이벤트 조회

        Args:
            confidence_threshold: 신뢰도 임계값
            time_window_minutes: 조회 시간 범위 (분)

        Returns:
            신고가 필요한 SafetyEvent 리스트
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        return (
            db.session.query(SafetyEvent)
            .filter(
                and_(
                    SafetyEvent.alert_sent == False,  # noqa: E712
                    SafetyEvent.confidence >= confidence_threshold,
                    SafetyEvent.detected_at >= cutoff_time
                )
            )
            .order_by(desc(SafetyEvent.confidence))
            .all()
        )

    def mark_alert_sent(self, event_id: int, alert_id: int) -> bool:
        """
        이벤트를 신고 전송 완료로 마킹

        Args:
            event_id: 이벤트 ID
            alert_id: 신고 ID

        Returns:
            성공 여부
        """
        event = self.get_by_id(event_id)
        if not event:
            return False

        event.alert_sent = True
        event.alert_id = alert_id
        db.session.commit()
        return True

    def count_by_region_and_type(
        self,
        region_id: int,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        지역 및 유형별 이벤트 개수 집계

        Args:
            region_id: 지역 ID
            event_type: 사고 유형
            start_date: 시작 날짜 (선택)
            end_date: 종료 날짜 (선택)

        Returns:
            이벤트 개수
        """
        query = db.session.query(SafetyEvent).filter_by(
            region_id=region_id,
            event_type=event_type
        )

        if start_date:
            query = query.filter(SafetyEvent.detected_at >= start_date)

        if end_date:
            query = query.filter(SafetyEvent.detected_at <= end_date)

        return query.count()

    def delete_old_events(self, days_to_keep: int = 30) -> int:
        """
        오래된 이벤트 자동 삭제 (데이터 보관 정책)

        Args:
            days_to_keep: 보관 일수 (기본 30일)

        Returns:
            삭제된 이벤트 개수
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # 신고와 연결되지 않은 오래된 이벤트만 삭제
        deleted_count = (
            db.session.query(SafetyEvent)
            .filter(
                and_(
                    SafetyEvent.detected_at < cutoff_date,
                    SafetyEvent.alert_sent == False  # noqa: E712
                )
            )
            .delete()
        )

        db.session.commit()
        return deleted_count
