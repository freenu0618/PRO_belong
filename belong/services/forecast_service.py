import joblib
from pathlib import Path
from typing import List, Dict, Any,Optional

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "forecast_model.pkl"


class ForecastService:
    '''
    예측 관련 기능 서비스 클래스
    '''

    def __init__(self) -> None:
        if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
            try:
                self.models: Dict[str, Dict[str, Any]] = joblib.load(MODEL_PATH)
            except Exception:
                print("[WARNING] Forecast model file exists but is invalid/corrupted.")
                self.models = {}
        else:
            print("[INFO] No trained forecast model found. Forecasting disabled.")
            self.models = {}  # 모델 없이 동작
        #                     강남구,강서구등  기본2년예측 =5로바꾸면 기본 5년
    def forecast_region(self, region : str, n_years: int =2) -> Optional[Dict[str, Any]]:
        if not self.models:
            return {
                "region": region,
                "forecast": None,
                "message": "Forecast model not trained yet."
            }

        if region not in self.models:
            return {
                "region": region,
                "forecast": None,
                "message": f"No trained forecast model for region: {region}"
            }
        # region에 대한 모델 정보가 없으면 예측 불가능이기때문에 None반환

        info: Dict[str,any]= self.models[region]
        coef: float = float(info["coef"])
        intercept: float = float(info["intercept"])
        history: List[Dict[str,any]] = info["history"]
        last_year: int = max(h["year"] for h in history)
        # history 안에 모든 원소 h에 대한 h["year"]값을 뽑아서 최대값=마지막 연도를 구함
        # last_year 기준으로 n_years =2라면 last_year,last_year-1의 예측을함

        forecast: List[Dict[str,any]] = []
        for i in range(1, n_years +1): # n_year =2 : 1,2
            year = last_year + i # last_year=2020이면 year = 2021,2022년도
            value = coef * year + intercept # y = ax + b 를 생각하면됨 예측값 = 기울기 x 연도 + 절편
            forecast.append({"year": year, "value": round(float(value))})

        return {
            "region": region,
            "history": history,
            "forecast": forecast,
        }
