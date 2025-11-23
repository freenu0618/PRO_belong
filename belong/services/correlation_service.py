import pandas as pd
from pathlib import Path
from typing import List,Dict,Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR /"ml"/ "dataset" / "merged_dataset.csv"

FEATURE_COLUMNS = [
    "single_household_ratio",
    "aging_index",
    "cpi_index",
    "age_65_over",
    "single_house_total",
]
TARGET_COLUMN = "elderly_population"

FEATURE_DESC = {
    "single_household_ratio": "1인가구 비율",
    "aging_index": "고령화 지수",
    "cpi_index": "소비자 물가",
    "age_65_over": "65세 이상 노인",
    "single_house_total": "1인 가구 수",
}

class CorrelationService:
    '''
    TARGET은 인구 변호하이기때문에 노인가구 인구 예측 서비스 class임
    컬럼들 이름 변경됨으로 FEATURE_COLUMNS의 변화 있음
    이전: 저소득 노인 수, 고령화 지수, 노인 복지시설 수, 80세 이상 노인, 1인 가구 수에서
    변경: 1인가구 비율, 고령화 지수, 소비자 물가, 65세 이상 노인, 1인가구 수 로 변경
    '''


    def __init__(self):
        self.df = pd.read_csv(DATA_DIR)

    def compute(self) -> Dict[str, Any]:
        """
        상관계수 계산 로직:
        1. 타깃 컬럼 + 피처 컬럼들을 숫자형(float)으로 강제 변환
        2. 변환 불가능한 값은 NaN 처리
        3. NaN 포함된 행 제거
        4. 피어슨 상관계수를 계산하여 JSON 형태로 반환
        """
        # 원본 훼손 방지
        df: pd.DataFrame = self.df.copy()

        numeric_columns: List[str] = [TARGET_COLUMN] + FEATURE_COLUMNS

        # ---- 숫자 변환 단계 ----
        for col in numeric_columns:
            # 문자열·기호 포함된 수치라면 숫자로 변환, 변환 불가한 값은 NaN
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # ---- 결측치 제거 ----
        before_count: int = len(df)
        df = df.dropna(subset=numeric_columns)
        after_count: int = len(df)

        # (선택) 데이터 손실 기록 — 협업 및 데이터 품질 확인용
        dropped_rows: int = before_count - after_count
        if dropped_rows > 0:
            print(f"[INFO] {dropped_rows} rows removed due to invalid numeric values.")

        # ---- 상관계수 계산 ----
        results: Dict[str, float] = {}
        target_series: pd.Series = df[TARGET_COLUMN]

        for col in FEATURE_COLUMNS:
            corr_value: float = float(df[col].corr(target_series))  # 피어슨 상관계수 계산
            results[col] = round(corr_value, 4)

        # ---- 결과를 JSON 형태로 가공 ----
        correlations: List[Dict[str, Any]] = [
            {"feature": feature, "corr": value} for feature, value in results.items()
        ]

        return {
            "correlations": correlations,
            "feature_desc": FEATURE_DESC
        }
