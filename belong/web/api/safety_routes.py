# belong/web/api/safety_routes.py
"""Safety Monitoring API Routes - 사고 감지 및 신고 시스템"""

from flask import jsonify, request
from . import api_bp
from datetime import datetime

from belong.services.safety.safety_monitor_service import SafetyMonitorService
from belong.services.safety.emergency_alert_service import EmergencyAlertService
from belong.repositories.safety.safety_event_repo import SafetyEventRepository
from belong.repositories.safety.emergency_alert_repo import EmergencyAlertRepository
from belong.repositories.safety.video_stream_repo import VideoStreamRepository

from .response_utils import success_response, bad_request, not_found, server_error

# -----------------------------
# Service 인스턴스 (전역 - 간단한 DI)
# -----------------------------
safety_event_repo = SafetyEventRepository()
emergency_alert_repo = EmergencyAlertRepository()
video_stream_repo = VideoStreamRepository()

safety_monitor_service = SafetyMonitorService(
    safety_event_repo=safety_event_repo,
    video_stream_repo=video_stream_repo
)

emergency_alert_service = EmergencyAlertService(
    emergency_alert_repo=emergency_alert_repo,
    safety_event_repo=safety_event_repo
)


# =========================================================
# 1) GET /api/safety/events - 사고 이벤트 조회
# =========================================================
@api_bp.route("/safety/events", methods=["GET"])
def get_safety_events():
    """
    사고 이벤트 조회 API

    쿼리 파라미터:
      - region_id: 필수, 지역 ID (정수)
      - event_type: 선택, 사고 유형 (fall, fire, violence, abnormal)
      - limit: 선택, 최대 조회 개수 (기본: 50)

    예:
      GET /api/safety/events?region_id=1
      GET /api/safety/events?region_id=1&event_type=fall
      GET /api/safety/events?region_id=1&event_type=fall&limit=100
    """
    try:
        # 파라미터 파싱
        region_id = request.args.get("region_id", type=int)
        event_type = request.args.get("event_type")
        limit = request.args.get("limit", default=50, type=int)

        # 필수 파라미터 검증
        if not region_id:
            return bad_request("Missing required parameter: region_id")

        # 서비스 호출
        events = safety_monitor_service.get_recent_events(
            region_id=region_id,
            event_type=event_type,
            limit=limit
        )

        return success_response({
            "events": events,
            "count": len(events),
            "filters": {
                "region_id": region_id,
                "event_type": event_type,
                "limit": limit
            }
        })

    except Exception as e:
        return server_error(f"Failed to retrieve events: {str(e)}")


# =========================================================
# 2) POST /api/safety/alerts - 신고 생성
# =========================================================
@api_bp.route("/safety/alerts", methods=["POST"])
def create_safety_alert():
    """
    긴급 신고 생성 API

    Request Body (JSON):
      {
        "event_id": 123,                   # 필수, 사고 이벤트 ID
        "elderly_name": "홍길동",          # 선택, 노인 이름 (Phase 2에서 암호화)
        "elderly_phone": "010-1234-5678"   # 선택, 전화번호 (Phase 2에서 암호화)
      }

    Response:
      {
        "status": "success",
        "data": {
          "alert_id": 456,
          "event_id": 123,
          "status": "sent",
          "created_at": "2026-01-19T15:30:00"
        },
        "message": "Alert created successfully"
      }
    """
    try:
        # Request Body 파싱
        data = request.get_json()
        if not data:
            return bad_request("Missing request body")

        # 필수 파라미터 검증
        event_id = data.get("event_id")
        if not event_id:
            return bad_request("Missing required field: event_id")

        # 선택 파라미터
        elderly_name = data.get("elderly_name")
        elderly_phone = data.get("elderly_phone")

        # 서비스 호출
        alert_id = emergency_alert_service.create_alert(
            event_id=event_id,
            elderly_name=elderly_name,
            elderly_phone=elderly_phone
        )

        # 생성된 신고 조회
        alert = emergency_alert_service.get_alert(alert_id)

        return success_response(
            data={"alert": alert},
            message="Alert created successfully",
            status_code=201
        )

    except ValueError as e:
        return bad_request(str(e))

    except Exception as e:
        return server_error(f"Failed to create alert: {str(e)}")


# =========================================================
# 3) GET /api/safety/alerts - 신고 이력 조회
# =========================================================
@api_bp.route("/safety/alerts", methods=["GET"])
def get_safety_alerts():
    """
    신고 이력 조회 API

    쿼리 파라미터:
      - status: 선택, 신고 상태 (pending, sent, responded, cancelled)
      - days: 선택, 조회 기간 (일, 기본: 7)
      - limit: 선택, 최대 조회 개수 (기본: 100)

    예:
      GET /api/safety/alerts
      GET /api/safety/alerts?status=pending
      GET /api/safety/alerts?days=30&limit=200
    """
    try:
        # 파라미터 파싱
        status = request.args.get("status")
        days = request.args.get("days", default=7, type=int)
        limit = request.args.get("limit", default=100, type=int)

        # 상태별 조회 또는 최근 조회
        if status:
            alerts = emergency_alert_repo.list_by_status(status, limit)
            alerts = [alert.to_dict() for alert in alerts]
        else:
            alerts = emergency_alert_service.get_recent_alerts(days, limit)

        # 통계 조회
        statistics = emergency_alert_service.get_alert_statistics()

        return success_response({
            "alerts": alerts,
            "count": len(alerts),
            "statistics": statistics,
            "filters": {
                "status": status,
                "days": days,
                "limit": limit
            }
        })

    except Exception as e:
        return server_error(f"Failed to retrieve alerts: {str(e)}")


# =========================================================
# 4) GET /api/safety/alerts/<alert_id> - 특정 신고 조회
# =========================================================
@api_bp.route("/safety/alerts/<int:alert_id>", methods=["GET"])
def get_safety_alert_detail(alert_id):
    """
    특정 신고 상세 조회 API

    경로 파라미터:
      - alert_id: 신고 ID (정수)

    예:
      GET /api/safety/alerts/123
    """
    try:
        alert = emergency_alert_service.get_alert(alert_id)

        if not alert:
            return not_found(f"Alert not found: {alert_id}")

        return success_response({"alert": alert})

    except Exception as e:
        return server_error(f"Failed to retrieve alert: {str(e)}")


# =========================================================
# 5) PATCH /api/safety/alerts/<alert_id>/status - 신고 상태 업데이트
# =========================================================
@api_bp.route("/safety/alerts/<int:alert_id>/status", methods=["PATCH"])
def update_alert_status(alert_id):
    """
    신고 상태 업데이트 API

    경로 파라미터:
      - alert_id: 신고 ID (정수)

    Request Body (JSON):
      {
        "status": "responded",              # 필수, 새로운 상태 (sent, responded, cancelled)
        "responder_name": "김철수",         # 선택, 응답자 이름 (responded 시 필수)
        "response_note": "응급팀 출동 완료"  # 선택, 응답 메모
      }

    예:
      PATCH /api/safety/alerts/123/status
      {
        "status": "responded",
        "responder_name": "김철수",
        "response_note": "응급팀 출동 완료"
      }
    """
    try:
        # Request Body 파싱
        data = request.get_json()
        if not data:
            return bad_request("Missing request body")

        # 필수 파라미터 검증
        new_status = data.get("status")
        if not new_status:
            return bad_request("Missing required field: status")

        # 상태별 처리
        if new_status == "responded":
            # 응답 처리
            responder_name = data.get("responder_name")
            if not responder_name:
                return bad_request("Missing required field: responder_name (for responded status)")

            response_note = data.get("response_note")

            success = emergency_alert_service.respond_to_alert(
                alert_id=alert_id,
                responder_name=responder_name,
                response_note=response_note
            )

        elif new_status == "cancelled":
            # 취소 처리
            reason = data.get("response_note")
            success = emergency_alert_service.cancel_alert(
                alert_id=alert_id,
                reason=reason
            )

        else:
            # 기타 상태 업데이트 (sent 등)
            success = emergency_alert_repo.update_status(alert_id, new_status)

        if not success:
            return not_found(f"Alert not found: {alert_id}")

        # 업데이트된 신고 조회
        alert = emergency_alert_service.get_alert(alert_id)

        return success_response(
            data={"alert": alert},
            message=f"Alert status updated to: {new_status}"
        )

    except Exception as e:
        return server_error(f"Failed to update alert status: {str(e)}")


# =========================================================
# 6) GET /api/safety/streams - 비디오 스트림 목록 조회
# =========================================================
@api_bp.route("/safety/streams", methods=["GET"])
def get_video_streams():
    """
    비디오 스트림 목록 조회 API (Phase 4)

    쿼리 파라미터:
      - region_id: 선택, 지역 ID 필터

    예:
      GET /api/safety/streams
      GET /api/safety/streams?region_id=1
    """
    try:
        region_id = request.args.get("region_id", type=int)

        streams = safety_monitor_service.get_active_streams(region_id)

        return success_response({
            "streams": streams,
            "count": len(streams),
            "filters": {
                "region_id": region_id
            }
        })

    except Exception as e:
        return server_error(f"Failed to retrieve streams: {str(e)}")


# =========================================================
# 7) GET /api/safety/statistics - 사고 및 신고 통계
# =========================================================
@api_bp.route("/safety/statistics", methods=["GET"])
def get_safety_statistics():
    """
    사고 및 신고 통계 조회 API

    쿼리 파라미터:
      - region_id: 선택, 지역 ID
      - event_type: 선택, 사고 유형

    예:
      GET /api/safety/statistics
      GET /api/safety/statistics?region_id=1&event_type=fall
    """
    try:
        region_id = request.args.get("region_id", type=int)
        event_type = request.args.get("event_type")

        # 신고 통계
        alert_statistics = emergency_alert_service.get_alert_statistics()

        # 사고 통계 (지역/유형 지정 시)
        event_statistics = None
        if region_id and event_type:
            event_statistics = safety_monitor_service.get_event_statistics(
                region_id=region_id,
                event_type=event_type
            )

        return success_response({
            "alert_statistics": alert_statistics,
            "event_statistics": event_statistics
        })

    except Exception as e:
        return server_error(f"Failed to retrieve statistics: {str(e)}")
