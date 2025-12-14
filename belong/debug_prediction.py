
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.append(os.getcwd())

from belong.app import create_app
from belong.services.prediction_service import PredictionService

def debug_prediction():
    app = create_app()
    with app.app_context():
        # Service 가져오기
        services = app.config.get("services", {})
        prediction_service: PredictionService = services.get("prediction_service")
        
        if not prediction_service:
            print("PredictionService not found in services")
            return

        region_name = "강남구" # 테스트할 구 이름
        year = 2025

        print(f"--- Debugging Prediction for {region_name} {year} ---")
        
        # 1. Features 확인
        features = prediction_service._build_features(region_name, year)
        if features:
            print("Features built:")
            print(f"  History len: {len(features['history'])}")
            print(f"  Last value (input to rule): {features['last_value']}")
            print(f"  Slope: {features['slope']}")
            # history의 첫 3개와 마지막 3개 출력
            print(f"  History start: {features['history'][:3]}")
            print(f"  History end: {features['history'][-3:]}")
        else:
            print("Features could not be built (no history?)")

        # 2. Predict 실행 (DB 저장 없이 단순 계산 로직)
        result = prediction_service.predict(region_name, year)
        print("\nPrediction Result (Service Calc):")
        print(result)

        # 3. DB 실제 저장 값 확인 (Repository 직접 조회)
        print("\n[DB Verification] Checking 'rule_base' in PREDICTION_RESULT...")
        from belong.repositories.prediction_repo import PredictionRepository
        repo = PredictionRepository()
        
        # 2025년 rule_base 데이터 조회
        db_rows = repo.get_predictions(region_name, year, year, source="rule_base")
        if db_rows:
            print(f"✅ Found in DB (rule_base): {db_rows}")
        else:
            print("❌ NOT Found in DB (rule_base). train_lonely_linear.py execution might have failed or not finished.")

if __name__ == "__main__":
    debug_prediction()
