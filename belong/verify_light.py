
import sys
from unittest.mock import MagicMock

# 1. 무거운 의존성 미리 Mock 처리 (Import 방지)
sys.modules["belong.extensions"] = MagicMock()
sys.modules["belong.models"] = MagicMock()
sys.modules["belong.models.prediction_result"] = MagicMock() # PredictionResult
sys.modules["belong.ml"] = MagicMock()
sys.modules["belong.ml.model_loader"] = MagicMock()

# 2. 이제 타겟 모듈 임포트 (경로 추가)
sys.path.append(r"c:\project_belong")

# model_loader.load_model이 호출될 때 에러 안나게 설정
sys.modules["belong.ml.model_loader"].load_model.return_value = None

try:
    from belong.services.prediction_service import PredictionService
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_logic():
    print("--- Starting Light Verification ---")
    
    # Mock Services
    mock_stats_service = MagicMock()
    mock_repo = MagicMock()
    
    # Instantiate
    # FeatureStatsService type hint가 있지만 런타임엔 상관없음
    service = PredictionService(mock_stats_service, mock_repo)
    
    # Force no model
    service.model = None 
    
    # ----------------------------------------------------
    # Case 1: Lonely Death (Ratio Based)
    # ----------------------------------------------------
    print("\n[Case 1] Lonely Death Prediction")
    region = "강남구"
    year = 2025
    
    # Mock History Data
    # 2023년 데이터: 노인 1000명, 고독사 10명 (비율 0.01)
    mock_history = [
        {"year": 2022, "elderly_population": 900, "target_value": 9},
        {"year": 2023, "elderly_population": 1000, "target_value": 10},
    ]
    mock_stats_service.get_all_years_for_region.return_value = mock_history
    
    # get_elderly_population: 2023년값 요청 시 1000 리턴하도록
    mock_stats_service.get_elderly_population.side_effect = lambda r, y: 1000 if y == 2023 else 0
    
    # predict 실행
    # 내부적으로: 
    # 1. ratio = 10 / 1000 = 0.01
    # 2. elderly prediction (2025): 1000 * 1.03^2 = 1060.9
    # 3. lonely prediction: 1060.9 * 0.01 = 10.609
    
    result = service.predict(region, year, prediction_type="lonely_death")
    
    print("Result:", result)
    
    if result and result["source"] == "ratio_based":
        print(">> SUCCESS: Source is ratio_based")
        
        pred = result["prediction"]
        expected = 10.609
        if abs(pred - expected) < 0.1:
            print(f">> SUCCESS: Value {pred} is close to expected {expected}")
        else:
            print(f">> FAIL: Value {pred} differs from expected {expected}")
    else:
        print(">> FAIL: Unexpected result structure or source")

    # ----------------------------------------------------
    # Case 2: Elderly Population (Rule Based)
    # ----------------------------------------------------
    print("\n[Case 2] Elderly Population Prediction")
    
    result_elderly = service.predict(region, year, prediction_type="elderly_population")
    print("Result:", result_elderly)
    
    if result_elderly and result_elderly["source"] == "rule_based":
        print(">> SUCCESS: Source is rule_based")
        pred = result_elderly["prediction"]
        expected = 1061 # round(1060.9) -> 1061
        if abs(pred - expected) < 1:
            print(f">> SUCCESS: Value {pred} is close to expected {expected}")
        else:
            print(f">> FAIL: Value {pred} differs from expected {expected}")

if __name__ == "__main__":
    test_logic()
