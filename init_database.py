#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask 앱 컨텍스트에서 데이터베이스 테이블 생성
"""
import os
import sys
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# DATABASE_URL 확인
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL이 설정되지 않았습니다.")
    print("   .env 파일을 확인하세요.")
    sys.exit(1)

print(f"✅ DATABASE_URL: {DATABASE_URL}\n")

try:
    # Flask 앱 import
    from belong.app import create_app
    from belong.extensions import db

    # Flask 앱 생성
    app = create_app()

    # 앱 컨텍스트 안에서 실행
    with app.app_context():
        print("📊 데이터베이스에 테이블 생성 중...")

        # 모든 테이블 생성
        db.create_all()

        print("✅ 테이블 생성 완료!\n")

        # 생성된 테이블 확인
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        print("📋 생성된 테이블:")
        for table in tables:
            print(f"   - {table}")

        print("\n🎉 데이터베이스 초기화 완료!")

except ImportError as e:
    print(f"\n❌ Import 오류: {e}")
    print("   belong.app 또는 belong.extensions를 찾을 수 없습니다.")
    import traceback
    traceback.print_exc()
    sys.exit(1)

except Exception as e:
    print(f"\n❌ 테이블 생성 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n📝 다음 단계:")
print("1. pgAdmin에서 테이블 확인")
print("2. 테스트 실행: conda activate belong && python test_mcp_tools.py")
