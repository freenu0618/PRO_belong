#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL 데이터베이스 테이블 생성 스크립트
"""
import os
import sys
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

# DATABASE_URL 확인
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL이 설정되지 않았습니다.")
    print("   .env 파일에 DATABASE_URL을 추가하세요.")
    print("   예: DATABASE_URL=postgresql://postgres:postgres@localhost:5432/belong_db")
    sys.exit(1)

print(f"✅ DATABASE_URL: {DATABASE_URL}")

try:
    from sqlalchemy import create_engine
    from belong.models import Base  # Base를 import

    # 엔진 생성
    engine = create_engine(DATABASE_URL)

    print("\n📊 데이터베이스에 테이블 생성 중...")

    # 모든 테이블 생성
    Base.metadata.create_all(engine)

    print("✅ 테이블 생성 완료!")

    # 생성된 테이블 목록 출력
    print("\n📋 생성된 테이블:")
    for table in Base.metadata.tables:
        print(f"   - {table}")

except ImportError as e:
    print(f"\n❌ Import 오류: {e}")
    print("   belong.models에서 Base를 import할 수 없습니다.")
    print("   belong/models/__init__.py를 확인하세요.")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ 테이블 생성 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🎉 데이터베이스 초기화 완료!")
print("\n다음 단계:")
print("1. pgAdmin에서 테이블 확인")
print("2. 테스트 실행: python test_mcp_tools.py")
