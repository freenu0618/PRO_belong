# belong/repositories/safety/emergency_alert_repo.py
"""EmergencyAlert Repository - 신고 이력 DB 접근"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc, and_
from belong.extensions import db
from belong.models.safety.emergency_alert import EmergencyAlert


class EmergencyAlertRepository:
    """
    EmergencyAlert 테이블 접근용 Repository

    주요 기능:
    - 신고 생성 및 조회
    - 상태 업데이트 (pending → sent → responded)
    - 응답 기록
    """

    def create(
        self,
        event_id: int,
        event_type: str,
        confidence: float,
        elderly_name_encrypted: Optional[bytes] = None,
        elderly_phone_encrypted: Optional[bytes] = None
    ) -> EmergencyAlert:
        """
        새로운 신고 생성

        Args:
            event_id: 사고 이벤트 ID
            event_type: 사고 유형
            confidence: 신뢰도
            elderly_name_encrypted: 암호화된 노인 이름 (선택)
            elderly_phone_encrypted: 암호화된 전화번호 (선택)

        Returns:
            생성된 EmergencyAlert 객체
        """
        alert = EmergencyAlert(
            event_id=event_id,
            event_type=event_type,
            confidence=confidence,
            elderly_name_encrypted=elderly_name_encrypted,
            elderly_phone_encrypted=elderly_phone_encrypted,
            status="pending",
            created_at=datetime.utcnow()
        )

        db.session.add(alert)
        db.session.commit()
        return alert

    def get_by_id(self, alert_id: int) -> Optional[EmergencyAlert]:
        """ID로 신고 조회"""
        return db.session.query(EmergencyAlert).filter_by(id=alert_id).first()

    def get_by_event_id(self, event_id: int) -> Optional[EmergencyAlert]:
        """사고 이벤트 ID로 신고 조회"""
        return db.session.query(EmergencyAlert).filter_by(event_id=event_id).first()

    def list_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[EmergencyAlert]:
        """
        상태별 신고 조회

        Args:
            status: 신고 상태 (pending, sent, responded, cancelled)
            limit: 최대 조회 개수

        Returns:
            EmergencyAlert 리스트 (최신순)
        """
        return (
            db.session.query(EmergencyAlert)
            .filter_by(status=status)
            .order_by(desc(EmergencyAlert.created_at))
            .limit(limit)
            .all()
        )

    def list_pending_alerts(
        self,
        time_window_minutes: int = 30
    ) -> List[EmergencyAlert]:
        """
        대기 중인 신고 조회 (시간 범위 내)

        Args:
            time_window_minutes: 조회 시간 범위 (분)

        Returns:
            대기 중인 EmergencyAlert 리스트
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        return (
            db.session.query(EmergencyAlert)
            .filter(
                and_(
                    EmergencyAlert.status == "pending",
                    EmergencyAlert.created_at >= cutoff_time
                )
            )
            .order_by(desc(EmergencyAlert.confidence))
            .all()
        )

    def update_status(
        self,
        alert_id: int,
        new_status: str
    ) -> bool:
        """
        신고 상태 업데이트

        Args:
            alert_id: 신고 ID
            new_status: 새로운 상태 (sent, responded, cancelled)

        Returns:
            성공 여부
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            return False

        alert.status = new_status
        db.session.commit()
        return True

    def record_response(
        self,
        alert_id: int,
        responder_name: str,
        response_note: Optional[str] = None
    ) -> bool:
        """
        신고 응답 기록

        Args:
            alert_id: 신고 ID
            responder_name: 응답자 이름
            response_note: 응답 메모 (선택)

        Returns:
            성공 여부
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            return False

        alert.status = "responded"
        alert.responder_name = responder_name
        alert.responded_at = datetime.utcnow()
        alert.response_note = response_note

        db.session.commit()
        return True

    def cancel_alert(
        self,
        alert_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        신고 취소

        Args:
            alert_id: 신고 ID
            reason: 취소 사유 (선택)

        Returns:
            성공 여부
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            return False

        alert.status = "cancelled"
        alert.response_note = reason
        alert.responded_at = datetime.utcnow()

        db.session.commit()
        return True

    def count_by_status(self, status: str) -> int:
        """
        상태별 신고 개수 집계

        Args:
            status: 신고 상태

        Returns:
            신고 개수
        """
        return db.session.query(EmergencyAlert).filter_by(status=status).count()

    def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        날짜 범위별 신고 개수 집계

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            신고 개수
        """
        return (
            db.session.query(EmergencyAlert)
            .filter(
                and_(
                    EmergencyAlert.created_at >= start_date,
                    EmergencyAlert.created_at <= end_date
                )
            )
            .count()
        )

    def list_recent_alerts(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[EmergencyAlert]:
        """
        최근 신고 조회

        Args:
            days: 조회 기간 (일)
            limit: 최대 조회 개수

        Returns:
            EmergencyAlert 리스트 (최신순)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return (
            db.session.query(EmergencyAlert)
            .filter(EmergencyAlert.created_at >= cutoff_date)
            .order_by(desc(EmergencyAlert.created_at))
            .limit(limit)
            .all()
        )
