from belong.app import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0으로 해야 도커 컨테이너 외부(내 PC)에서 접속 가능합니다.
    app.run(host="0.0.0.0", port=5000, debug=True)
