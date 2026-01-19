
import sys
import os

sys.path.append(r"c:\project_belong")

from belong.app import create_app
from belong.extensions import db
from belong.models.prediction_result import PredictionResult

def clean_predictions():
    app = create_app()
    with app.app_context():
        # 미래 데이터 (2024년부터) 삭제
        # 혹은 source가 'ratio_based'가 아닌 것을 삭제해도 되지만, 확실하게 하기 위해
        # 2024년 이후 데이터는 모두 날리고 다시 생성하게 유도.
        target_year_start = 2024
        
        print(f"Deleting predictions from year {target_year_start}...")
        
        deleted_count = db.session.query(PredictionResult).filter(
            PredictionResult.year >= target_year_start
        ).delete()
        
        db.session.commit()
        print(f"Deleted {deleted_count} rows.")

if __name__ == "__main__":
    clean_predictions()
