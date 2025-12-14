
import sys
import os

sys.path.append(r"c:\project_belong")

# flask app context 없이 sqlalchemy만 써서 접속 시도하면 설정 로드가 번거로움
# 따라서 앱 컨텍스트를 쓰되, import 에러가 나는 부분(typing 이슈)을 피해야 함.
# 하지만 typing 이슈는 sqlalchemy 버전 문제로 보임.
# 우회법: cx_Oracle 직접 사용하거나, 
# db.session.execute(text("DELETE FROM PREDICTION_RESULT WHERE year >= 2024")) 사용.

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

def clean_predictions_raw():
    # 최소한의 앱 생성
    app = Flask(__name__)
    app.config.from_object(Config)
    db = SQLAlchemy(app)
    
    print("Connecting to DB...")
    with app.app_context():
        # Raw SQL 실행
        try:
            sql = text("DELETE FROM PREDICTION_RESULT WHERE \"year\" >= 2024")
            # Oracle은 컬럼명 대소문자 구분이 엄격할 수 있음. 보통 대문자. 
            # 모델 정의를 보면 year = db.Column("year", ...) 소문자임.
            # 하지만 Oracle은 기본적으로 대문자로 저장됨. 따옴표 쓰면 소문자 유지.
            # 안전하게 대소문자 없이 시도하거나 모델 정의 확인 필요.
            # 일단 모델 정의상 "year"이므로 따옴표 시도.
            
            result = db.session.execute(sql)
            db.session.commit()
            print(f"Executed delete. Rows affected: {result.rowcount}")
        except Exception as e:
            print(f"Error: {e}")
            # 대문자로 재시도
            try:
                print("Retrying with uppercase YEAR...")
                sql2 = text("DELETE FROM PREDICTION_RESULT WHERE YEAR >= 2024")
                result = db.session.execute(sql2)
                db.session.commit()
                print(f"Executed delete. Rows affected: {result.rowcount}")
            except Exception as e2:
                print(f"Retry Error: {e2}")

if __name__ == "__main__":
    clean_predictions_raw()
