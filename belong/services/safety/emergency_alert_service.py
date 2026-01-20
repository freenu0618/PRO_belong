# belong/services/safety/emergency_alert_service.py
"""EmergencyAlertService - 신고 시스템 비즈니스 로직"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from belong.repositories.safety.emergency_alert_repo import EmergencyAlertRepository
from belong.repositories.safety.safety_event_repo import SafetyEventRepository

logger = logging.getLogger(__name__)


class EmergencyAlertService:
    """
    긴급 신고 서비스

    역할:
    - 신고 생성 및 관리
    - 신고 상태 업데이트
    - Mock API 호출 (Phase 1)
    """

    def __init__(
        self,
        emergency_alert_repo: EmergencyAlertRepository,
        safety_event_repo: SafetyEventRepository
    ):
        """
        EmergencyAlertService 초기화

        Args:
            emergency_alert_repo: EmergencyAlert Repository
            safety_event_repo: SafetyEvent Repository
        """
        self.emergency_alert_repo = emergency_alert_repo
        self.safety_event_repo = safety_event_repo

        logger.info("[EmergencyAlertService] Initialized")

    def create_alert(
        self,
        event_id: int,
        elderly_name: Optional[str] = None,
        elderly_phone: Optional[str] = None
    ) -> int:
        """
        신고 생성

        Args:
            event_id: 사고 이벤트 ID
            elderly_name: 노인 이름 (선택, Phase 2에서 암호화)
            elderly_phone: 노인 전화번호 (선택, Phase 2에서 암호화)

        Returns:
            생성된 신고 ID
        """
        # 사고 이벤트 조회
        event = self.safety_event_repo.get_by_id(event_id)
        if not event:
            logger.error(f"[EmergencyAlertService] Event not found: event_id={event_id}")
            raise ValueError(f"Event not found: {event_id}")

        # 이미 신고된 경우
        if event.alert_sent:
            logger.warning(f"[EmergencyAlertService] Alert already sent: event_id={event_id}")
            existing_alert = self.emergency_alert_repo.get_by_event_id(event_id)
            return existing_alert.id if existing_alert else None

        # CLAUDE.md 규칙: 개인정보 로깅 금지
        logger.info(
            f"[EmergencyAlertService] Creating alert: "
            f"event_id={event_id}, type={event.event_type}, confidence={event.confidence:.2f}"
        )

        # TODO Phase 2: 개인정보 암호화
        # encrypted_name = self.encrypt(elderly_name) if elderly_name else None
        # encrypted_phone = self.encrypt(elderly_phone) if elderly_phone else None

        # 신고 생성
        alert = self.emergency_alert_repo.create(
            event_id=event_id,
            event_type=event.event_type,
            confidence=event.confidence,
            elderly_name_encrypted=None,  # Phase 2에서 암호화
            elderly_phone_encrypted=None   # Phase 2에서 암호화
        )

        # SafetyEvent 업데이트
        self.safety_event_repo.mark_alert_sent(event_id, alert.id)

        # Mock API 호출 (Phase 1)
        self._send_mock_alert(alert.id)

        logger.info(f"[EmergencyAlertService] Alert created: alert_id={alert.id}")
        return alert.id

    def _send_mock_alert(self, alert_id: int):
        """
        Mock 신고 API 호출 (Phase 1)

        Phase 6에서 실제 API로 변경

        Args:
            alert_id: 신고 ID
        """
        logger.info(f"[EmergencyAlertService][MOCK] Sending alert: alert_id={alert_id}")

        # Mock: 신고 상태를 'sent'로 변경
        self.emergency_alert_repo.update_status(alert_id, "sent")

        logger.info(f"[EmergencyAlertService][MOCK] Alert sent successfully")

    def respond_to_alert(
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
        logger.info(
            f"[EmergencyAlertService] Recording response: "
            f"alert_id={alert_id}, responder={responder_name}"
        )

        success = self.emergency_alert_repo.record_response(
            alert_id=alert_id,
            responder_name=responder_name,
            response_note=response_note
        )

        if success:
            logger.info(f"[EmergencyAlertService] Response recorded: alert_id={alert_id}")
        else:
            logger.error(f"[EmergencyAlertService] Failed to record response: alert_id={alert_id}")

        return success

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
        logger.info(f"[EmergencyAlertService] Cancelling alert: alert_id={alert_id}")

        success = self.emergency_alert_repo.cancel_alert(
            alert_id=alert_id,
            reason=reason
        )

        if success:
            logger.info(f"[EmergencyAlertService] Alert cancelled: alert_id={alert_id}")
        else:
            logger.error(f"[EmergencyAlertService] Failed to cancel alert: alert_id={alert_id}")

        return success

    def get_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        신고 조회

        Args:
            alert_id: 신고 ID

        Returns:
            신고 정보 (JSON 직렬화)
        """
        alert = self.emergency_alert_repo.get_by_id(alert_id)
        return alert.to_dict() if alert else None

    def get_pending_alerts(self, time_window_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        대기 중인 신고 조회

        Args:
            time_window_minutes: 조회 시간 범위 (분)

        Returns:
            신고 리스트 (JSON 직렬화)
        """
        alerts = self.emergency_alert_repo.list_pending_alerts(time_window_minutes)
        return [alert.to_dict() for alert in alerts]

    def get_recent_alerts(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        최근 신고 조회

        Args:
            days: 조회 기간 (일)
            limit: 최대 조회 개수

        Returns:
            신고 리스트 (JSON 직렬화)
        """
        alerts = self.emergency_alert_repo.list_recent_alerts(days, limit)
        return [alert.to_dict() for alert in alerts]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        신고 통계 조회

        Returns:
            통계 딕셔너리
        """
        pending_count = self.emergency_alert_repo.count_by_status("pending")
        sent_count = self.emergency_alert_repo.count_by_status("sent")
        responded_count = self.emergency_alert_repo.count_by_status("responded")
        cancelled_count = self.emergency_alert_repo.count_by_status("cancelled")

        return {
            "pending": pending_count,
            "sent": sent_count,
            "responded": responded_count,
            "cancelled": cancelled_count,
            "total": pending_count + sent_count + responded_count + cancelled_count
        }
