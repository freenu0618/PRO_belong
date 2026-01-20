# check_regions.py
"""REGION 테이블 데이터 확인 스크립트"""

from belong.app import create_app
from belong.extensions import db

def check_regions():
    """REGION 테이블의 데이터 확인"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("REGION 테이블 데이터 확인")
        print("=" * 60)

        # 먼저 테이블 목록 확인
        print("\n[Step 1] 데이터베이스 테이블 목록 확인:")
        tables_result = db.session.execute(db.text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        ))
        tables = tables_result.fetchall()
        for table in tables:
            print(f"  - {table[0]}")

        # REGION 데이터 조회 (대소문자 구분)
        print("\n[Step 2] REGION 테이블 데이터 조회:")
        try:
            result = db.session.execute(db.text('SELECT id, name, code FROM "REGION" ORDER BY id LIMIT 10'))
            regions = result.fetchall()
        except Exception as e:
            print(f"  [ERROR] REGION 테이블 조회 실패: {e}")
            regions = []

        if not regions:
            print("[WARNING] REGION 테이블에 데이터가 없습니다!")
            print("\n테스트 Region 데이터를 생성하시겠습니까?")
            print("(create_test_regions.py 스크립트를 실행하세요)")
        else:
            print(f"\n총 {len(regions)}개의 Region 발견:")
            print("\nID | 이름 | 코드")
            print("-" * 40)
            for region in regions:
                print(f"{region[0]:2d} | {region[1]:20s} | {region[2] if region[2] else 'N/A'}")

        print("\n" + "=" * 60)

if __name__ == "__main__":
    check_regions()
