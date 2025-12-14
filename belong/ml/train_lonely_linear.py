"""
belong/ml/train_lonely_linear.py

ELDERLY_STATS 기반 다중선형회귀(Multiple Linear Regression)로
고독사 예측을 수행하고, 결과를 PREDICTION_RESULT(source='ml_linear')에 저장하는 스크립트.

실행 예:
    python -m belong.ml.train_lonely_linear
또는
    python belong/ml/train_lonely_linear.py  (PYTHONPATH 설정에 따라 다름)
"""

from typing import List, Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score

from belong.app import create_app
from belong.extensions import db
from belong.models.feature_stats import ElderlyStats
from belong.models.region import Region
from belong.models.prediction_result import PredictionResult

# -------------------------------
# 설정 값
# -------------------------------

ACTUAL_LAST_YEAR = 2023       # 실측 끝나는 연도 (ELDERLY_STATS 기준)
FORECAST_LAST_YEAR = 2035     # 예측 마지막 연도
ML_SOURCE = "rule_base"       # PREDICTION_RESULT.source 값 (사용자 요청)

from belong.ml.model_loader import load_model

# ... (중략) ...


# -------------------------------
# 1) 학습용 데이터 로딩
# -------------------------------
def load_training_dataframe() -> pd.DataFrame:
    """
    ELDERLY_STATS + REGION join 해서
    다중회귀 학습용 DataFrame 생성.
    """
    rows = (
        db.session.query(
            Region.name.label("region_name"),
            ElderlyStats.year.label("year"),
            ElderlyStats.target_value.label("target_value"),
            ElderlyStats.elderly_population.label("elderly_population"),
            ElderlyStats.aging_index.label("aging_index"),
            ElderlyStats.single_household_ratio.label("single_household_ratio"),
            ElderlyStats.low_income_elderly_65_79_ratio.label("low_inc_65_79"),
            ElderlyStats.low_income_elderly_80_over_ratio.label("low_inc_80_plus"),
            ElderlyStats.cpi_index.label("cpi_index"),
        )
        .join(Region, ElderlyStats.region_id == Region.id)
        .filter(ElderlyStats.year <= ACTUAL_LAST_YEAR)
        .order_by(Region.name, ElderlyStats.year)
        .all()
    )

    df = pd.DataFrame(rows)

    # target_value 없는 행은 학습에서 제외
    df = df.dropna(subset=["target_value"])

    return df


# -------------------------------
# 2) 피처 구성 (다중선형회귀용)
# -------------------------------
def build_features(df: pd.DataFrame):
    """
    - 숫자 피처 + 구 원-핫 인코딩
    - year는 중심화(center)해서 사용
    """
    df = df.copy()

    # year 중심화 (마지막 실측 연도 기준)
    df["year_centered"] = df["year"] - ACTUAL_LAST_YEAR

    numeric_cols = [
        "year_centered",
        "elderly_population",
        "aging_index",
        "single_household_ratio",
        "low_inc_65_79",
        "low_inc_80_plus",
        "cpi_index",
    ]

    # NaN 처리 (간단히 0으로 채움; 필요 시 다른 전략으로 변경 가능)
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # 구 이름 원-핫 인코딩
    region_ohe = pd.get_dummies(df["region_name"], prefix="gu")

    X = pd.concat([df[numeric_cols], region_ohe], axis=1)
    y = df["target_value"]

    return X, y, region_ohe.columns.tolist(), numeric_cols


# -------------------------------
# 3) 학습 + 간단 평가 (2023년 test)
# -------------------------------
def train_and_evaluate(df: pd.DataFrame) -> Ridge:
    """
    2017~2022 → train, 2023 → test 로 성능 확인 후
    전체(<=2023) 데이터로 다시 학습한 모델을 반환.
    """
    X, y, region_cols, numeric_cols = build_features(df)

    train_mask = df["year"] < ACTUAL_LAST_YEAR
    test_mask = df["year"] == ACTUAL_LAST_YEAR

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    model = Ridge(alpha=1.0, random_state=42)
    model.fit(X_train, y_train)

    if len(X_test) > 0:
        y_pred = model.predict(X_test)
        rmse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        print(f"[EVAL] {ACTUAL_LAST_YEAR}년 RMSE={rmse:.3f}, R²={r2:.3f}")
    else:
        print("[WARN] 테스트용 연도 데이터가 없습니다. 평가 스킵.")

    # 전체 연도(<=ACTUAL_LAST_YEAR)로 다시 학습
    model.fit(X, y)
    print("[INFO] 전체 실측 데이터(<= {0})로 재학습 완료.".format(ACTUAL_LAST_YEAR))

    model.feature_columns_ = X.columns.tolist()
    model.region_ohe_columns_ = region_cols
    model.numeric_columns_ = numeric_cols

    return model

def build_future_feature_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    각 구별로 마지막 실측 연도(ACTUAL_LAST_YEAR)의 피처를 가져와서
    - year만 2024~FORECAST_LAST_YEAR로 확장
    - **중요**: 'elderly_population'은 forecast_model.pkl (단순회귀) 사용하여 연도별 예측값 적용
    - 나머지 지표(비율 등)는 "현 수준 유지" 가정
    """
    base_rows: List[Dict] = []

    # 각 구별 마지막 실측 행
    last_rows = (
        df.sort_values(["region_name", "year"])
          .groupby("region_name")
          .tail(1)
    )
    
    # 노인 인구 예측 모델 로드 (dict: region -> {coef, intercept, ...})
    pop_model = load_model()
    
    for _, row in last_rows.iterrows():
        r_name = row["region_name"]
        
        # 해당 구의 모델 파라미터 가져오기
        pm = pop_model.get(r_name) if pop_model else None
        
        for year in range(ACTUAL_LAST_YEAR + 1, FORECAST_LAST_YEAR + 1):
            
            # 1. 노인 인구 예측 (선형 회귀: y = ax + b)
            if pm:
                pred_pop = pm["coef"] * year + pm["intercept"]
            else:
                # 모델 없으면 마지막 값 유지 (fallback)
                pred_pop = row["elderly_population"]
                
            base_rows.append(
                {
                    "region_name": r_name,
                    "year": year,
                    "elderly_population": pred_pop,  # ✅ 예측된 인구수 적용
                    "aging_index": row["aging_index"],
                    "single_household_ratio": row["single_household_ratio"],
                    "low_inc_65_79": row["low_inc_65_79"],
                    "low_inc_80_plus": row["low_inc_80_plus"],
                    "cpi_index": row["cpi_index"],
                }
            )

    future_df = pd.DataFrame(base_rows)
    return future_df


def build_future_design_matrix(future_df: pd.DataFrame, model):
    """
    미래 연도용 DataFrame → 학습 때와 동일한 컬럼 구성으로 X_future 생성.
    """
    df = future_df.copy()
    df["year_centered"] = df["year"] - ACTUAL_LAST_YEAR
    # 학습 때 사용한 numeric 컬럼 이름 재사용
    numeric_cols = model.numeric_columns_

    df[numeric_cols] = df[numeric_cols].fillna(0)

    # region_name 원-핫 (학습 때 쓰인 구만 사용, 없는 컬럼은 0으로 채움)
    region_ohe = pd.get_dummies(df["region_name"], prefix="gu")

    for col in model.region_ohe_columns_:
        if col not in region_ohe.columns:
            region_ohe[col] = 0

    region_ohe = region_ohe[model.region_ohe_columns_]

    X_future = pd.concat([df[numeric_cols], region_ohe], axis=1)
    X_future = X_future[model.feature_columns_]  # 컬럼 순서 맞추기

    return X_future


# -------------------------------
# 5) PREDICTION_RESULT 저장
# -------------------------------
def save_predictions_to_db(future_df: pd.DataFrame, y_pred) -> None:
    """
    - 기존 미래 예측(year > ACTUAL_LAST_YEAR)은 모두 삭제
    - 새로운 ml_linear 예측을 INSERT
    """
    print("[INFO] 기존 미래 예측 삭제 중 (year > {0}) ...".format(ACTUAL_LAST_YEAR))
    (
        PredictionResult.query
        .filter(PredictionResult.year > ACTUAL_LAST_YEAR)
        .delete(synchronize_session=False)
    )
    db.session.commit()

    print("[INFO] 새로운 ml_linear_2 예측 INSERT ...")
    for (idx, row), pred in zip(future_df.iterrows(), y_pred):
        # 음수 예측은 0으로 클램프
        value = float(pred)
        if value < 0:
            value = 0.0

        pr = PredictionResult(
            region_name=row["region_name"],
            year=int(row["year"]),
            prediction_value=value,
            source=ML_SOURCE,
        )

        db.session.add(pr)

    db.session.commit()
    print("[DONE] PREDICTION_RESULT 저장 완료 (source='{0}')".format(ML_SOURCE))


# -------------------------------
# main
# -------------------------------
def main():
    app = create_app()
    with app.app_context():
        print("[STEP] 학습용 데이터 로딩 ...")
        df_train = load_training_dataframe()
        print(f"[INFO] 학습용 샘플 수: {len(df_train)}")

        print("[STEP] 모델 학습 + 2023년 평가 ...")
        model = train_and_evaluate(df_train)

        print("[STEP] 미래 연도(2024~{0}) 데이터 생성 ...".format(FORECAST_LAST_YEAR))
        df_future = build_future_feature_df(df_train)

        print("[STEP] 미래 디자인 행렬 생성 ...")
        X_future = build_future_design_matrix(df_future, model)

        print("[STEP] 미래 고독사 예측 ...")
        y_future_pred = model.predict(X_future)

        print("[STEP] DB에 저장 ...")
        save_predictions_to_db(df_future, y_future_pred)


if __name__ == "__main__":
    main()
