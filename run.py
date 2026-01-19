import os
from belong.app import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0으로 해야 도커 컨테이너 외부(내 PC)에서 접속 가능합니다.
    # FLASK_DEBUG 환경변수 확인 (기본값 True)
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "on"]
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
