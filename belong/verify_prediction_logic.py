
import unittest
from unittest.mock import MagicMock
import sys
import os

# 프로젝트 루트 추가
sys.path.append(r"c:\project_belong")

# 모듈 import 시도 (실패 시 mock 처리)
try:
    from belong.services.prediction_service import PredictionService
    from belong.services.feature_stats_service import FeatureStatsService
except ImportError:
    # 만약 환경 문제로 import가 안되면 sys.path 문제일 수 있음
    print("Failed to import modules. Check sys.path")
    sys.exit(1)

class TestPredictionService(unittest.TestCase):
    def setUp(self):
        # Mock Dependencies
        self.mock_stats_service = MagicMock(spec=FeatureStatsService)
        self.mock_repo = MagicMock()
        
        # Create Service Instance
        # model load 실패 시 rule-based fallback 되므로 mock 모델 안 만들어도 됨
        self.service = PredictionService(
            feature_stats_service=self.mock_stats_service,
            prediction_repo=self.mock_repo
        )
        # 강제로 모델 제거 (Rule-based / Ratio-based 테스트 위함)
        self.service.model = None

    def test_lonely_death_prediction_logic(self):
        print("\nTesting Lonely Death Prediction Logic (Ratio Based)...")
        region = "강남구"
        year = 2025
        
        # 1. Mock Data Setup
        # (1) get_all_years_for_region 반환값 (History)
        # 고독사(target_value)와 노인인구(elderly_population)가 같이 들어옴
        mock_history = [
            {"year": 2020, "elderly_population": 1000, "target_value": 10}, # Ratio: 0.01
            {"year": 2021, "elderly_population": 1100, "target_value": 11}, # Ratio: 0.01
            {"year": 2022, "elderly_population": 1200, "target_value": 12}, # Ratio: 0.01
            {"year": 2023, "elderly_population": 1300, "target_value": 13}, # Ratio: 0.01
        ]
        self.mock_stats_service.get_all_years_for_region.return_value = mock_history
        self.mock_docs = mock_history # save for debug

        # (2) get_elderly_population (마지막 연도 노인 인구 조회용)
        # 로직상 2023년 노인 인구를 조회할 것임
        self.mock_stats_service.get_elderly_population.side_effect = lambda r, y: next((item["elderly_population"] for item in mock_history if item["year"] == y), 0)

        # (3) _get_or_create_prediction -> elderly_population 예측 결과를 mock으로 리턴
        # 2025년 노인 인구가 1500으로 예측되었다고 가정
        # 실제로는 내부에서 self.predict_and_store를 호출함.
        # 이를 mocking 할지, 아니면 실제 로직을 태울지 결정.
        # 내부 메서드 _get_or_create_prediction을 mock 하여 노인 인구 예측값 제어
        
        # partial mocking의 어려움이 있으므로, 그냥 predict_and_store가 
        # type="elderly_population"일 때 정상 작동하도록 기대.
        # 우리가 model=None으로 했으므로 rule-based (3% 증가) 로직이 돌 것임.
        # 2023(1300) -> 2024(1339) -> 2025(1379.17 -> 1379) 예상
        
        # 실행
        result = self.service.predict(region, year, prediction_type="lonely_death")
        
        # 검증
        print(f"Prediction Result: {result}")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "ratio_based")
        
        pred_val = result["prediction"]
        # 예상 로직:
        # 1. 노인 인구 2025 예측: 1300 * 1.03^2 ≈ 1379
        # 2. 비율: last_lonely(13) / last_elderly(1300) = 0.01
        # 3. 고독사 예측: 1379 * 0.01 = 13.79 -> float
        
        print(f"Predicted Value: {pred_val}")
        self.assertAlmostEqual(pred_val, 13.79, delta=0.5)

    def test_elderly_population_prediction(self):
        print("\nTesting Elderly Population Prediction (Rule Based)...")
        region = "강남구"
        year = 2025
        
        mock_history = [
            {"year": 2023, "elderly_population": 1000, "target_value": 10},
        ]
        self.mock_stats_service.get_all_years_for_region.return_value = mock_history

        result = self.service.predict(region, year, prediction_type="elderly_population")
        
        print(f"Prediction Result: {result}")
        self.assertEqual(result["source"], "rule_based")
        # 1000 * 1.03^2 = 1060.9
        self.assertAlmostEqual(result["prediction"], 1061, delta=1)

if __name__ == "__main__":
    unittest.main()
