# belong/services/safety/safety_monitor_service.py
"""SafetyMonitorService - 사고 감지 비즈니스 로직"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from belong.repositories.safety.safety_event_repo import SafetyEventRepository
from belong.repositories.safety.video_stream_repo import VideoStreamRepository

logger = logging.getLogger(__name__)


class SafetyMonitorService:
    """
    사고 모니터링 서비스

    역할:
    - 사고 이벤트 기록
    - 비디오 스트림 상태 관리
    - 신고 트리거 (신뢰도 임계값 기반)
    """

    def __init__(
        self,
        safety_event_repo: SafetyEventRepository,
        video_stream_repo: VideoStreamRepository
    ):
        """
        SafetyMonitorService 초기화

        Args:
            safety_event_repo: SafetyEvent Repository
            video_stream_repo: VideoStream Repository
        """
        self.safety_event_repo = safety_event_repo
        self.video_stream_repo = video_stream_repo

        logger.info("[SafetyMonitorService] Initialized")

    def record_safety_event(
        self,
        event_type: str,
        confidence: float,
        region_id: int,
        stream_id: Optional[str] = None,
        frame_timestamp: Optional[float] = None,
        frame_data: Optional[bytes] = None,
        detection_metadata: Optional[Dict] = None
    ) -> int:
        """
        사고 이벤트 기록

        Args:
            event_type: 사고 유형 (fall, fire, violence)
            confidence: 신뢰도 (0.0 - 1.0)
            region_id: 지역 ID
            stream_id: 스트림 ID (선택)
            frame_timestamp: 프레임 타임스탬프 (선택)
            frame_data: 프레임 데이터 (선택, 암호화 필요)
            detection_metadata: 감지 메타데이터 (선택)

        Returns:
            생성된 이벤트 ID
        """
        # CLAUDE.md 규칙: 개인정보 로깅 금지
        logger.info(
            f"[SafetyMonitorService] Recording event: "
            f"type={event_type}, confidence={confidence:.2f}, "
            f"region_id={region_id}"
        )

        # DB 저장 (Repository 패턴 준수)
        event = self.safety_event_repo.create(
            event_type=event_type,
            confidence=confidence,
            region_id=region_id,
            stream_id=stream_id,
            frame_timestamp=frame_timestamp,
            frame_data=frame_data,
            detection_metadata=detection_metadata
        )

        # 스트림 통계 업데이트
        if stream_id:
            self.video_stream_repo.increment_event_count(stream_id)

        logger.info(f"[SafetyMonitorService] Event recorded: event_id={event.id}")
        return event.id

    def should_send_alert(self, event_id: int, threshold: float = 0.7) -> bool:
        """
        신고 필요 여부 판단

        Args:
            event_id: 사고 이벤트 ID
            threshold: 신뢰도 임계값

        Returns:
            신고 필요 여부
        """
        event = self.safety_event_repo.get_by_id(event_id)

        if not event:
            logger.warning(f"[SafetyMonitorService] Event not found: event_id={event_id}")
            return False

        # 이미 신고된 경우
        if event.alert_sent:
            logger.debug(f"[SafetyMonitorService] Alert already sent: event_id={event_id}")
            return False

        # 신뢰도 임계값 체크
        if event.confidence >= threshold:
            logger.info(
                f"[SafetyMonitorService] Alert needed: "
                f"event_id={event_id}, confidence={event.confidence:.2f}"
            )
            return True

        return False

    def get_recent_events(
        self,
        region_id: int,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        최근 사고 이벤트 조회

        Args:
            region_id: 지역 ID
            event_type: 사고 유형 필터 (선택)
            limit: 최대 조회 개수

        Returns:
            사고 이벤트 리스트 (JSON 직렬화)
        """
        events = self.safety_event_repo.list_by_region(
            region_id=region_id,
            event_type=event_type,
            limit=limit
        )

        return [event.to_dict() for event in events]

    def get_event_statistics(
        self,
        region_id: int,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        사고 통계 조회

        Args:
            region_id: 지역 ID
            event_type: 사고 유형
            start_date: 시작 날짜 (선택)
            end_date: 종료 날짜 (선택)

        Returns:
            통계 딕셔너리
        """
        count = self.safety_event_repo.count_by_region_and_type(
            region_id=region_id,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "region_id": region_id,
            "event_type": event_type,
            "count": count,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }

    def register_video_stream(
        self,
        stream_id: str,
        stream_url: str,
        region_id: int,
        location_name: Optional[str] = None
    ) -> int:
        """
        비디오 스트림 등록

        Args:
            stream_id: 스트림 ID (UUID)
            stream_url: 스트림 URL (RTSP/HTTP)
            region_id: 지역 ID
            location_name: 위치 설명 (선택)

        Returns:
            생성된 스트림 DB ID
        """
        # CLAUDE.md 규칙: 개인정보 로깅 금지 (위치 정보도 마스킹)
        logger.info(
            f"[SafetyMonitorService] Registering stream: "
            f"stream_id={stream_id}, region_id={region_id}"
        )

        stream = self.video_stream_repo.create(
            stream_id=stream_id,
            stream_url=stream_url,
            region_id=region_id,
            location_name=location_name
        )

        logger.info(f"[SafetyMonitorService] Stream registered: db_id={stream.id}")
        return stream.id

    def update_stream_status(self, stream_id: str, is_active: bool) -> bool:
        """
        스트림 상태 업데이트

        Args:
            stream_id: 스트림 ID
            is_active: 활성 상태

        Returns:
            성공 여부
        """
        if is_active:
            return self.video_stream_repo.activate_stream(stream_id)
        else:
            return self.video_stream_repo.deactivate_stream(stream_id)

    def get_active_streams(self, region_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        활성 스트림 조회

        Args:
            region_id: 지역 ID 필터 (선택)

        Returns:
            스트림 리스트 (JSON 직렬화)
        """
        streams = self.video_stream_repo.list_active_streams(region_id=region_id)
        return [stream.to_dict() for stream in streams]
