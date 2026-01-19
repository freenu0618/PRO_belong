
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

def clean_predictions_raw():
    """
    2024년 이후 예측 데이터를 삭제하는 일회성 스크립트
    ORM 방식으로 안전하게 데이터 삭제
    """
    # 최소한의 앱 생성
    app = Flask(__name__)
    app.config.from_object(Config)
    db = SQLAlchemy(app)

    print("Connecting to DB...")
    with app.app_context():
        # ORM 방식으로 안전하게 삭제
        try:
            from belong.models.prediction_result import PredictionResult

            # 2024년 이후 데이터 조회
            rows_to_delete = PredictionResult.query.filter(PredictionResult.year >= 2024).all()
            count = len(rows_to_delete)

            # 삭제 실행
            PredictionResult.query.filter(PredictionResult.year >= 2024).delete()
            db.session.commit()

            print(f"✅ Successfully deleted {count} rows from PREDICTION_RESULT (year >= 2024)")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_predictions_raw()
