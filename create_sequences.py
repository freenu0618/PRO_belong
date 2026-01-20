# create_sequences.py
"""Safety Monitoring 시퀀스 생성 스크립트"""

from belong.app import create_app
from belong.extensions import db

def create_sequences():
    """Safety Monitoring 테이블에 필요한 시퀀스 생성"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("시퀀스 생성 시작")
        print("=" * 60)

        # 1. SAFETY_EVENT_ID_SEQ 생성 (대문자로 생성)
        try:
            db.session.execute(db.text('CREATE SEQUENCE IF NOT EXISTS "SAFETY_EVENT_ID_SEQ" START 1 INCREMENT BY 1'))
            print("[OK] SAFETY_EVENT_ID_SEQ 생성 완료")
        except Exception as e:
            print(f"[ERROR] SAFETY_EVENT_ID_SEQ 생성 실패: {e}")

        # 2. EMERGENCY_ALERT_ID_SEQ 생성 (대문자로 생성)
        try:
            db.session.execute(db.text('CREATE SEQUENCE IF NOT EXISTS "EMERGENCY_ALERT_ID_SEQ" START 1 INCREMENT BY 1'))
            print("[OK] EMERGENCY_ALERT_ID_SEQ 생성 완료")
        except Exception as e:
            print(f"[ERROR] EMERGENCY_ALERT_ID_SEQ 생성 실패: {e}")

        # 3. VIDEO_STREAM_ID_SEQ 생성 (대문자로 생성)
        try:
            db.session.execute(db.text('CREATE SEQUENCE IF NOT EXISTS "VIDEO_STREAM_ID_SEQ" START 1 INCREMENT BY 1'))
            print("[OK] VIDEO_STREAM_ID_SEQ 생성 완료")
        except Exception as e:
            print(f"[ERROR] VIDEO_STREAM_ID_SEQ 생성 실패: {e}")

        # 커밋
        db.session.commit()

        print("\n" + "=" * 60)
        print("시퀀스 생성 완료!")
        print("=" * 60)

        # 시퀀스 확인
        print("\n시퀀스 목록 확인:")
        result = db.session.execute(db.text(
            "SELECT sequence_name FROM information_schema.sequences WHERE sequence_name LIKE '%SAFETY%' OR sequence_name LIKE '%EMERGENCY%' OR sequence_name LIKE '%VIDEO%'"
        ))
        for row in result:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    create_sequences()
