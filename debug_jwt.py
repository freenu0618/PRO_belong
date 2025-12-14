
import sys
import os
from flask import Flask

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from belong.app import create_app
from belong.web.api.jwt_utils import create_access_token, _decode_with_candidates, _jwt_secret_candidates

def debug_jwt():
    print("--- [JWT Debug Start] ---")
    
    # 1. 앱 생성 및 컨텍스트 진입
    app = create_app()
    
    with app.app_context():
        print(f"1. Flask Config SECRET_KEY: '{app.config.get('SECRET_KEY')}'")
        print(f"2. Flask Config JWT_SECRET: '{app.config.get('JWT_SECRET')}'")
        
        candidates = _jwt_secret_candidates()
        print(f"3. Secret Candidates (Order matters!): {candidates}")
        
        # 4. 토큰 생성 테스트
        claims = {"sub": "1", "username": "testuser", "email": "test@example.com"}
        token = create_access_token(claims)
        print(f"4. Generated Token: {token}")
        
        # 5. 토큰 디코딩 테스트 (직접 호출)
        try:
            payload = _decode_with_candidates(token)
            print(f"5. Decoded Payload (Direct): {payload}")
            print(">>> SUCCESS: Token generation and decoding logic works internally.")
        except Exception as e:
            print(f">>> FAIL: Token generation/decoding mismatch. Error: {e}")
            return

    print("--- [JWT Debug End] ---")

if __name__ == "__main__":
    debug_jwt()
