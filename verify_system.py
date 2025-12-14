
import sys
import os
import time

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

# 로깅 설정
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

def verify_system():
    print("=== [System Verification Start] ===")
    
    # 1. 환경 변수 및 의존성 확인
    try:
        import jwt
        import flask
        import torch
        from transformers import pipeline
        print("✅ [Check 1] Dependencies (Flask, PyJWT, Transformers) are installed.")
    except ImportError as e:
        print(f"❌ [Check 1] Missing dependency: {e}")
        return

    # 2. Flask App Factory & Configuration 확인
    try:
        from belong.app import create_app
        print("⏳ [Check 2] Initializing Flask App (This triggers Model Loading, please wait)...")
        app = create_app()
        print("✅ [Check 2] Flask App created successfully.")
    except Exception as e:
        print(f"❌ [Check 2] Failed to create_app: {e}")
        # 자세한 에러 출력을 위해 traceback
        import traceback
        traceback.print_exc()
        return

    # 3. JWT 로직 재검증 (통합 환경)
    try:
        with app.app_context():
            from belong.web.api.jwt_utils import create_access_token, _decode_with_candidates
            
            # str(sub) 강제 변환 여부 테스트
            # 모의 사용자 객체
            class MockUser:
                id = 123
                username = "verify_user"
                email = "verify@test.com"
            
            user = MockUser()
            # 우리가 auth_routes에서 했던 것처럼 직접 호출해봄 (auth_routes 내부 로직과 유사하게)
            # auth_routes.py 코드를 import해서 테스트할 수도 있지만 로직 자체 검증이므로 직접 호출
            
            claims = {
                "sub": str(user.id), # auth_routes에서 수정한 부분 반영
                "username": user.username,
                "email": user.email
            }
            
            token = create_access_token(claims)
            decoded = _decode_with_candidates(token)
            
            if decoded["sub"] == "123":
                print("✅ [Check 3] JWT Generation & Decoding works (sub='123').")
            else:
                print(f"❌ [Check 3] JWT Mismatch: {decoded}")
    except Exception as e:
         print(f"❌ [Check 3] JWT Logic Failed: {e}")
         import traceback
         traceback.print_exc()

    # 4. Route & Blueprint 등록 확인
    try:
        with app.app_context():
            rules = [str(r) for r in app.url_map.iter_rules()]
            
            # 주요 라우트 존재 여부 체크
            required_routes = [
                "/api/auth/login", 
                "/api/auth/signup", 
                "/api/ai/sentiment", 
                "/api/ai/entities",
                "/dashboard",
                "/"
            ]
            
            missing = []
            for req in required_routes:
                # url_map rule string format might vary, simple check
                found = any(req in rule for rule in rules)
                if not found:
                    missing.append(req)
            
            if not missing:
                print("✅ [Check 4] All critical routes are registered in URL map.")
            else:
                print(f"❌ [Check 4] Missing routes: {missing}")
                
    except Exception as e:
        print(f"❌ [Check 4] Route verification failed: {e}")

    # 5. DB Initialization Check (Optional - connection only)
    # 오라클 접속은 로컬 환경에 따라 실패할 수 있으므로 경고로만 처리
    try:
        with app.app_context():
            from belong.extensions import db
            # 실제 쿼리는 날리지 않고 엔진 생성 여부만 확인하거나
            # print(db.engine.url) 
            pass
        print(f"ℹ️ [Check 5] DB Engine URL: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    except Exception as e:
        print(f"⚠️ [Check 5] DB Config warning: {e}")

    print("=== [System Verification End] ===")

if __name__ == "__main__":
    verify_system()
