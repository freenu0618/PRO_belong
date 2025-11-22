from flask import Flask

from belong.web.api import api_bp # belong패키지/web패키지/api.py or api/__init__.py 모듈에서 api_bp 객체 import
from belong.web.main import web_bp # web/__init__.py안에 web_bp



'''
api_bp → /api/v1/... 같은 REST API 엔드포인트 모음
web_bp → /, /login, /dashboard 같은 화면 렌더링용 엔드포인트 모음

앱실행시 실행되는 것들, init으로 create_app를 옮겨도 됨
'''
def safe_register(app, bp):
    if bp.name not in app.blueprints:
        app.register_blueprint(bp)
    else:
        print(f"[WARN] Blueprint '{bp.name}' already registered. Skipping.")

def create_app():
    '''
    __name__은 현재 모듈의 이름
    app객체를 만들고 라우터 등록 (@app.route/app.register_blueprint)
    설정 적용 app.config
    '''

    app = Flask(__name__) 
    app.config.from_object("config.Config")
    # config안에 Config 클래스에 있는 Flask 설정을 담고있는 객체 생성

    # 블루 프린트 등록    
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(web_bp)
    # url_prefix가 있을경우 api_bp가 가지고있는 라우트가 뒤에 붙음 (/api/v1/user, api/v1/predict)
    # url_prefix가 없을경우 web_bp안에 정의된 URL들이 그대로 루트 기준으로 매핑

    return app


if __name__ == "__main__":   # 실행되는곳 파일이름이랑 같음(main이 실행되면 name=main이됨)
    app = create_app()
    app.run(debug=True)

# 실제 실행  python app.py 일때 __name__ = "__main__"
# import app 할때는 __name__ 값은 "app"(파일명)이 됨