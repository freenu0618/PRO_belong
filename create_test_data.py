# create_test_data.py
"""Safety Monitoring API 테스트 데이터 생성 스크립트"""

from belong.app import create_app
from belong.extensions import db
from belong.repositories.safety.safety_event_repo import SafetyEventRepository
from belong.repositories.safety.emergency_alert_repo import EmergencyAlertRepository

def create_test_data():
    """테스트용 SafetyEvent 및 EmergencyAlert 데이터 생성"""
    app = create_app()

    with app.app_context():
        safety_repo = SafetyEventRepository()
        alert_repo = EmergencyAlertRepository()

        print("=" * 60)
        print("테스트 데이터 생성 시작")
        print("=" * 60)

        # 1. SafetyEvent 3개 생성 (낙상 이벤트)
        print("\n[Step 1] SafetyEvent 생성 중...")

        event1 = safety_repo.create(
            event_type="fall",
            confidence=0.92,
            region_id=1,
            stream_id="test-stream-001",
            location_detail="서울시 강남구 테헤란로 123",
            detection_metadata={
                "keypoints": [[100, 200, 0.9]] * 17,
                "body_angle": 65,
                "fall_duration_seconds": 3.2
            }
        )
        print(f"[OK] Event 1 생성: ID={event1.id}, type={event1.event_type}, confidence={event1.confidence}")

        event2 = safety_repo.create(
            event_type="fall",
            confidence=0.85,
            region_id=1,
            stream_id="test-stream-002",
            location_detail="서울시 강남구 역삼동 456",
            detection_metadata={
                "keypoints": [[110, 210, 0.8]] * 17,
                "body_angle": 70,
                "fall_duration_seconds": 2.8
            }
        )
        print(f"[OK] Event 2 생성: ID={event2.id}, type={event2.event_type}, confidence={event2.confidence}")

        event3 = safety_repo.create(
            event_type="fall",
            confidence=0.78,
            region_id=2,
            stream_id="test-stream-003",
            location_detail="서울시 서초구 서초동 789",
            detection_metadata={
                "keypoints": [[105, 205, 0.75]] * 17,
                "body_angle": 62,
                "fall_duration_seconds": 2.5
            }
        )
        print(f"[OK] Event 3 생성: ID={event3.id}, type={event3.event_type}, confidence={event3.confidence}")

        # 2. EmergencyAlert 1개 생성 (event1에 대한 신고)
        print("\n[Step 2] EmergencyAlert 생성 중...")

        alert1 = alert_repo.create(
            event_id=event1.id,
            event_type="fall",
            confidence=0.92
            # elderly_name_encrypted 및 elderly_phone_encrypted는 선택 사항
            # Phase 2에서는 암호화 없이 진행
        )
        print(f"[OK] Alert 1 생성: ID={alert1.id}, event_id={alert1.event_id}, status={alert1.status}")

        # 3. SafetyEvent의 alert_sent 플래그 업데이트
        print("\n[Step 3] SafetyEvent alert_sent 업데이트 중...")

        safety_repo.mark_alert_sent(event1.id, alert1.id)
        print(f"[OK] Event {event1.id}의 alert_sent=True, alert_id={alert1.id} 업데이트 완료")

        # 4. 추가 이벤트 생성 (다양한 타입)
        print("\n[Step 4] 추가 이벤트 생성 중...")

        event4 = safety_repo.create(
            event_type="fire",
            confidence=0.88,
            region_id=1,
            stream_id="test-stream-001",
            location_detail="서울시 강남구 테헤란로 123",
            detection_metadata={
                "fire_detected": True,
                "flame_size": "medium"
            }
        )
        print(f"[OK] Event 4 생성: ID={event4.id}, type={event4.event_type}, confidence={event4.confidence}")

        event5 = safety_repo.create(
            event_type="violence",
            confidence=0.75,
            region_id=3,
            stream_id="test-stream-004",
            location_detail="서울시 송파구 잠실동 111",
            detection_metadata={
                "violence_type": "hitting",
                "persons_count": 2
            }
        )
        print(f"[OK] Event 5 생성: ID={event5.id}, type={event5.event_type}, confidence={event5.confidence}")

        print("\n" + "=" * 60)
        print("테스트 데이터 생성 완료!")
        print("=" * 60)
        print(f"\n총 생성된 데이터:")
        print(f"  - SafetyEvent: 5개")
        print(f"  - EmergencyAlert: 1개")
        print(f"\n이제 API를 테스트할 수 있습니다:")
        print(f"  GET  http://127.0.0.1:5000/api/safety/events?region_id=1")
        print(f"  GET  http://127.0.0.1:5000/api/safety/alerts")
        print(f"  GET  http://127.0.0.1:5000/api/safety/alerts/{alert1.id}")

if __name__ == "__main__":
    create_test_data()
