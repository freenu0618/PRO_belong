# create_test_regions.py
"""테스트용 REGION 데이터 생성 스크립트"""

from belong.app import create_app
from belong.extensions import db

def create_test_regions():
    """서울시 25개 구 중 테스트용 Region 생성"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("테스트용 REGION 데이터 생성")
        print("=" * 60)

        # 서울시 주요 구 (테스트용 5개)
        test_regions = [
            {"name": "강남구", "code": "11680"},
            {"name": "서초구", "code": "11650"},
            {"name": "송파구", "code": "11710"},
            {"name": "강동구", "code": "11740"},
            {"name": "종로구", "code": "11110"},
        ]

        print(f"\n{len(test_regions)}개의 Region 생성 중...")

        for region_data in test_regions:
            # 이미 존재하는지 확인
            existing = db.session.execute(
                db.text('SELECT id FROM "REGION" WHERE name = :name'),
                {"name": region_data["name"]}
            ).fetchone()

            if existing:
                print(f"  [SKIP] {region_data['name']} (이미 존재)")
                continue

            # 새 Region 생성
            db.session.execute(
                db.text('INSERT INTO "REGION" (name, code) VALUES (:name, :code)'),
                region_data
            )
            print(f"  [OK] {region_data['name']} (코드: {region_data['code']})")

        db.session.commit()

        print("\n" + "=" * 60)
        print("테스트용 REGION 데이터 생성 완료!")
        print("=" * 60)

        # 생성된 Region 확인
        print("\n생성된 Region 목록:")
        result = db.session.execute(db.text('SELECT id, name, code FROM "REGION" ORDER BY id'))
        for row in result:
            print(f"  ID {row[0]:2d}: {row[1]:10s} (코드: {row[2]})")

if __name__ == "__main__":
    create_test_regions()
