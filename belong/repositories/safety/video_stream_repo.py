# belong/repositories/safety/video_stream_repo.py
"""VideoStream Repository - 비디오 스트림 정보 DB 접근"""

from typing import List, Optional
from datetime import datetime
from belong.extensions import db
from belong.models.safety.video_stream import VideoStream


class VideoStreamRepository:
    """
    VideoStream 테이블 접근용 Repository

    주요 기능:
    - 스트림 등록 및 조회
    - 활성 상태 관리
    - 스트림 통계 업데이트
    """

    def create(
        self,
        stream_id: str,
        stream_url: str,
        region_id: int,
        location_name: Optional[str] = None
    ) -> VideoStream:
        """
        새로운 비디오 스트림 등록

        Args:
            stream_id: 고유 스트림 ID (UUID)
            stream_url: RTSP/HTTP 스트림 URL
            region_id: 지역 ID
            location_name: 위치 설명 (선택)

        Returns:
            생성된 VideoStream 객체
        """
        stream = VideoStream(
            stream_id=stream_id,
            stream_url=stream_url,
            region_id=region_id,
            location_name=location_name,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.session.add(stream)
        db.session.commit()
        return stream

    def get_by_id(self, id: int) -> Optional[VideoStream]:
        """ID로 스트림 조회"""
        return db.session.query(VideoStream).filter_by(id=id).first()

    def get_by_stream_id(self, stream_id: str) -> Optional[VideoStream]:
        """스트림 ID로 조회"""
        return db.session.query(VideoStream).filter_by(stream_id=stream_id).first()

    def list_active_streams(
        self,
        region_id: Optional[int] = None
    ) -> List[VideoStream]:
        """
        활성 스트림 목록 조회

        Args:
            region_id: 지역 ID 필터 (선택)

        Returns:
            활성 VideoStream 리스트
        """
        query = db.session.query(VideoStream).filter_by(is_active=True)

        if region_id:
            query = query.filter_by(region_id=region_id)

        return query.all()

    def list_by_region(self, region_id: int) -> List[VideoStream]:
        """
        지역별 스트림 조회

        Args:
            region_id: 지역 ID

        Returns:
            VideoStream 리스트
        """
        return db.session.query(VideoStream).filter_by(region_id=region_id).all()

    def update_last_frame(self, stream_id: str) -> bool:
        """
        마지막 프레임 수신 시간 업데이트

        Args:
            stream_id: 스트림 ID

        Returns:
            성공 여부
        """
        stream = self.get_by_stream_id(stream_id)
        if not stream:
            return False

        stream.last_frame_at = datetime.utcnow()
        stream.updated_at = datetime.utcnow()
        db.session.commit()
        return True

    def increment_event_count(self, stream_id: str) -> bool:
        """
        이벤트 카운트 증가

        Args:
            stream_id: 스트림 ID

        Returns:
            성공 여부
        """
        stream = self.get_by_stream_id(stream_id)
        if not stream:
            return False

        stream.total_events += 1
        stream.last_event_at = datetime.utcnow()
        stream.updated_at = datetime.utcnow()
        db.session.commit()
        return True

    def activate_stream(self, stream_id: str) -> bool:
        """
        스트림 활성화

        Args:
            stream_id: 스트림 ID

        Returns:
            성공 여부
        """
        stream = self.get_by_stream_id(stream_id)
        if not stream:
            return False

        stream.is_active = True
        stream.updated_at = datetime.utcnow()
        db.session.commit()
        return True

    def deactivate_stream(self, stream_id: str) -> bool:
        """
        스트림 비활성화

        Args:
            stream_id: 스트림 ID

        Returns:
            성공 여부
        """
        stream = self.get_by_stream_id(stream_id)
        if not stream:
            return False

        stream.is_active = False
        stream.updated_at = datetime.utcnow()
        db.session.commit()
        return True

    def delete_stream(self, stream_id: str) -> bool:
        """
        스트림 삭제

        Args:
            stream_id: 스트림 ID

        Returns:
            성공 여부
        """
        stream = self.get_by_stream_id(stream_id)
        if not stream:
            return False

        db.session.delete(stream)
        db.session.commit()
        return True

    def count_active_streams(self, region_id: Optional[int] = None) -> int:
        """
        활성 스트림 개수 집계

        Args:
            region_id: 지역 ID 필터 (선택)

        Returns:
            활성 스트림 개수
        """
        query = db.session.query(VideoStream).filter_by(is_active=True)

        if region_id:
            query = query.filter_by(region_id=region_id)

        return query.count()

    def get_stream_statistics(self, stream_id: str) -> Optional[dict]:
        """
        스트림 통계 조회

        Args:
            stream_id: 스트림 ID

        Returns:
            통계 딕셔너리 또는 None
        """
        stream = self.get_by_stream_id(stream_id)
        if not stream:
            return None

        return {
            "stream_id": stream.stream_id,
            "total_events": stream.total_events,
            "last_event_at": stream.last_event_at.isoformat() if stream.last_event_at else None,
            "last_frame_at": stream.last_frame_at.isoformat() if stream.last_frame_at else None,
            "is_active": stream.is_active
        }
