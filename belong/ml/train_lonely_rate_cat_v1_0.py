"""
belong/ml/train_lonely_rate_v0_3.py

1) ELDERLY_STATS + REGION (필요시 ELDERLY_HISTORY) 를 이용해
   "고독사율" (고독사 수 / 노인 인구)을 다중선형회귀(Ridge)로 예측하고,
2) ELDERLY_HISTORY의 노인 인구 예측값과 곱해서
   미래(2024~2035) 고독사 수를 추정한 뒤,
3) 각 구별로 "연도별 감소 금지(단조비감소)" 후처리를 거쳐
   PREDICTION_RESULT(source='ml_linear_rate_v0_3')에 저장하는 스크립트.

실행 예:
    python -m belong.ml.train_lonely_rate_v0_3
"""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

from belong.app import create_app
from belong.extensions import db

from belong.models.feature_stats import ElderlyStats
from belong.models.region import Region
from belong.models.prediction_result import PredictionResult
from belong.models.elderly_history import ElderlyHistory


# -------------------------------
# 설정 상수
# -------------------------------

ACTUAL_LAST_YEAR = 2023          # ELDERLY_STATS 실측 마지막 연도
FORECAST_START_YEAR = 2024
FORECAST_LAST_YEAR = 2030        # 예측 마지막 연도
TRAIN_START_YEAR = 2017          # 학습 데이터 시작 연도 (필요시 2020으로 조정 가능)

ML_SOURCE = "ml_catboost_rate_v1_0"

# -------------------------------
# 유틸: 구/연도별 노인 인구 (ELDERLY_HISTORY)
# -------------------------------

def load_elderly_population_forecast() -> Dict[Tuple[int, int], float]:
    """
    ELDERLY_HISTORY에서 (region_id, year) -> elderly_population 매핑 생성.
    - 2017~2035 전체를 가져오되, 우리는 주로 2024~2035를 사용.
    """
    rows = (
        db.session.query(
            ElderlyHistory.region_id,
            ElderlyHistory.year,
            ElderlyHistory.elderly_population,
        )
        .filter(ElderlyHistory.year >= 2017)
        .filter(ElderlyHistory.year <= FORECAST_LAST_YEAR)
        .all()
    )

    result: Dict[Tuple[int, int], float] = {}
    for r in rows:
        if r.elderly_population is None:
            continue
        result[(r.region_id, r.year)] = float(r.elderly_population)

    return result

# -------------------------------
# 1) 학습용 DataFrame 로딩
# -------------------------------

def load_training_dataframe() -> pd.DataFrame:
    """
    ELDERLY_STATS + REGION join:
      - region_name
      - year
      - target_value (고독사 수)
      - elderly_population (분모)
      - aging_index, single_household_ratio, CPI 등

    그리고 rate = target_value / elderly_population 을 계산한다.
    """

    rows = (
        db.session.query(
            Region.id.label("region_id"),
            Region.name.label("region_name"),
            ElderlyStats.year.label("year"),
            ElderlyStats.target_value.label("target_value"),
            ElderlyStats.elderly_population.label("elderly_population"),
            ElderlyStats.aging_index.label("aging_index"),
            ElderlyStats.single_household_ratio.label("single_household_ratio"),
            ElderlyStats.cpi_index.label("cpi_index"),
        )
        .join(Region, ElderlyStats.region_id == Region.id)
        .filter(ElderlyStats.year >= TRAIN_START_YEAR)
        .filter(ElderlyStats.year <= ACTUAL_LAST_YEAR)
        .order_by(Region.name, ElderlyStats.year)
        .all()
    )

    df = pd.DataFrame(rows)

    # 유효한 분모/타깃만 사용
    df = df.dropna(subset=["target_value", "elderly_population"])
    df = df[df["elderly_population"] > 0]

    # 🔹 고독사율 (단순 비율) 계산
    df["death_rate"] = df["target_value"] / df["elderly_population"]

    return df

# -------------------------------
# 2) 피처 구성 (Ridge 다중회귀용)
# -------------------------------

def build_features(df: pd.DataFrame):
    """
    - numeric 피처 + region_name 원-핫 인코딩
    - year는 중심화해서 사용 (year - ACTUAL_LAST_YEAR)
    """
    df = df.copy()

    df["year_centered"] = df["year"] - ACTUAL_LAST_YEAR

    # ✅ 여기 있는 이름들이 df.columns에 반드시 있어야 함
    numeric_cols = [
        "year_centered",
        "elderly_population",
        "aging_index",
        "single_household_ratio",
        "cpi_index",
    ]

    # 혹시라도 빼먹은 게 있으면 바로 확인할 수 있게 체크
    missing = [c for c in numeric_cols if c not in df.columns]
    if missing:
        print("[DEBUG] df.columns:", list(df.columns))
        raise KeyError(f"numeric_cols에 있는데 DataFrame에 없는 컬럼: {missing}")

    df[numeric_cols] = df[numeric_cols].fillna(0)

    # 구 이름 원-핫 인코딩
    region_ohe = pd.get_dummies(df["region_name"], prefix="gu")

    X = pd.concat([df[numeric_cols], region_ohe], axis=1)
    y = df["death_rate"]

    return X, y, region_ohe.columns.tolist(), numeric_cols

# -------------------------------
# 3) 학습 + 2023 평가
# -------------------------------


def train_and_evaluate(df: pd.DataFrame) -> CatBoostRegressor:
    """
    CatBoostRegressor로 death_rate를 학습.
    TimeSeriesSplit + GridSearchCV로 하이퍼파라미터 튜닝 후,
    최적 파라미터로 최종 모델 학습.

    - 학습: TRAIN_START_YEAR ~ ACTUAL_LAST_YEAR-1
    - 테스트: ACTUAL_LAST_YEAR(=2023) 한 해
    """

    # 0) 연도 기준 정렬 (시계열 CV를 위해)
    df_sorted = df.sort_values(["year", "region_name"]).reset_index(drop=True)

    # 1) 피처/타깃 생성 (기존 build_features 그대로 사용)
    X, y, region_cols, numeric_cols = build_features(df_sorted)

    # 2) train / test 마스크
    train_mask = (df_sorted["year"] >= TRAIN_START_YEAR) & (
        df_sorted["year"] < ACTUAL_LAST_YEAR
    )
    test_mask = df_sorted["year"] == ACTUAL_LAST_YEAR

    X_train_all = X[train_mask]
    y_train_all = y[train_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]

    print(f"[INFO] CatBoost train size={len(X_train_all)}, test size={len(X_test)}")

    # 3) TimeSeriesSplit 설정 (연도가 적으니 3-split 정도)
    tscv = TimeSeriesSplit(n_splits=3)

    # 4) 하이퍼파라미터 후보 설정
    #    너무 넓게 가지 말고, 작은 범위에서만 탐색
    param_grid = {
        "depth": [3, 4, 5],
        "learning_rate": [0.03, 0.1],
        "l2_leaf_reg": [1.0, 3.0, 5.0],
        "iterations": [200, 400],
        # 필요하면 "subsample": [0.8, 1.0] 도 추가 가능
    }

    base_model = CatBoostRegressor(
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
    )

    grid = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        scoring="neg_mean_squared_error",
        cv=tscv,
        n_jobs=-1,
    )

    print("[STEP] CatBoost TimeSeriesSplit + GridSearchCV 로 하이퍼파라미터 튜닝 시작 ...")
    grid.fit(X_train_all, y_train_all)

    best_params = grid.best_params_
    best_cv_mse = -grid.best_score_

    print(f"[CV] best params={best_params}")
    print(f"[CV] best CV MSE={best_cv_mse:.8f}")

    # 5) 최종 모델: best_params로 train 전체 구간 재학습
    final_model = CatBoostRegressor(
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
        **best_params,
    )

    print(
        f"[STEP] best params로 TRAIN_START_YEAR~{ACTUAL_LAST_YEAR-1} 전체 구간 재학습 ..."
    )
    final_model.fit(X_train_all, y_train_all)

    # 6) 2023년 평가
    if len(X_test) > 0:
        y_pred_test = final_model.predict(X_test)
        rmse = mean_squared_error(y_test, y_pred_test)
        r2 = r2_score(y_test, y_pred_test)
        print(
            f"[EVAL] {ACTUAL_LAST_YEAR}년 death_rate "
            f"RMSE={rmse:.8f}, R²={r2:.3f} (CatBoost tuned)"
        )

    # 7) 미래 피처 생성용 메타데이터를 모델 객체에 심어둔다.
    final_model.feature_columns_ = X.columns.tolist()
    final_model.region_ohe_columns_ = region_cols
    final_model.numeric_columns_ = numeric_cols

    return final_model



# -------------------------------
# 4) 미래 피처 DataFrame 생성
# -------------------------------

def load_latest_stats_per_region() -> pd.DataFrame:
    """
    각 구별로 ELDERLY_STATS에서 마지막 연도(ACTUAL_LAST_YEAR)의 행을 가져온다.
    (aging_index, single_household_ratio 등 미래 시나리오 기본값으로 사용)
    """
    rows = (
        db.session.query(
            Region.id.label("region_id"),
            Region.name.label("region_name"),
            ElderlyStats.year.label("year"),
            ElderlyStats.elderly_population.label("elderly_population"),
            ElderlyStats.aging_index.label("aging_index"),
            ElderlyStats.single_household_ratio.label("single_household_ratio"),
            ElderlyStats.low_income_elderly_65_79_ratio.label("LOW_INC_65_79_RATIO"),
            ElderlyStats.low_income_elderly_80_over_ratio.label("LOW_INC_80_PLUS_RATIO"),
            ElderlyStats.cpi_index.label("cpi_index"),
            ElderlyStats.target_value.label("target_value"),
        )
        .join(Region, ElderlyStats.region_id == Region.id)
        .filter(ElderlyStats.year == ACTUAL_LAST_YEAR)
        .order_by(Region.name)
        .all()
    )
    return pd.DataFrame(rows)


def build_future_feature_df(latest_stats: pd.DataFrame,
                            elderly_forecast_map: Dict[Tuple[int, int], float]) -> pd.DataFrame:
    """
    각 구별로 2024~2035 연도에 대한 피처를 생성:
      - year: 2024~2035
      - elderly_population: ELDERLY_HISTORY에서 가져오고, 없으면 2023 값 사용
      - 그 외 aging_index 등은 2023 값 유지
    """
    future_rows: List[Dict] = []

    for _, row in latest_stats.iterrows():
        region_id = int(row["region_id"])
        region_name = row["region_name"]

        base_elderly = float(row["elderly_population"]) if row["elderly_population"] else 0.0

        for year in range(FORECAST_START_YEAR, FORECAST_LAST_YEAR + 1):
            # 노인 인구: 우선 ELDERLY_HISTORY 예측값, 없으면 2023 값
            elderly_pop = elderly_forecast_map.get((region_id, year), base_elderly)

            future_rows.append(
                {
                    "region_id": region_id,
                    "region_name": region_name,
                    "year": year,
                    "elderly_population": elderly_pop,
                    "aging_index": row["aging_index"],
                    "single_household_ratio": row["single_household_ratio"],
                    "cpi_index": row["cpi_index"],
                }
            )

    future_df = pd.DataFrame(future_rows)
    return future_df



def build_future_design_matrix(future_df: pd.DataFrame, model: CatBoostRegressor) -> pd.DataFrame:
    """
    미래 피처 DataFrame → 학습 때와 동일한 X 컬럼 구성.
    """
    df = future_df.copy()
    df["year_centered"] = df["year"] - ACTUAL_LAST_YEAR

    numeric_cols = model.numeric_columns_
    df[numeric_cols] = df[numeric_cols].fillna(0)

    region_ohe = pd.get_dummies(df["region_name"], prefix="gu")

    # 학습 때 사용된 구 컬럼이 다 들어오도록 맞추기
    for col in model.region_ohe_columns_:
        if col not in region_ohe.columns:
            region_ohe[col] = 0
    region_ohe = region_ohe[model.region_ohe_columns_]

    X_future = pd.concat([df[numeric_cols], region_ohe], axis=1)
    X_future = X_future[model.feature_columns_]

    return X_future

# -------------------------------
# 5) 단조비 감소(non-decreasing) 후처리
# -------------------------------

def enforce_smooth_change_by_region(
    future_df: pd.DataFrame,
    raw_counts: np.ndarray,
    latest_stats: pd.DataFrame,
    max_up: float = 0.15,    # 연간 최대 +15% 증가
    max_down: float = 0.15,  # 연간 최대 -15% 감소
) -> np.ndarray:
    """
    region_name, year 순으로 정렬된 future_df와 raw 예측값을 받아,
    각 구별로 '연도별 급격한 점프/폭락만 막고, 완만한 증감은 허용'하는 규칙을 적용한다.

    시작값은 2023년 실제 ELDERLY_STATS.target_value.
    """
    df = future_df.copy()
    df["raw_pred"] = raw_counts

    # 2023년 실제 고독사 수 (없는 경우 0)
    last_actual_map: Dict[str, float] = {
        row["region_name"]: float(row["target_value"] or 0.0)
        for _, row in latest_stats.iterrows()
    }

    adjusted_values: List[float] = []

    df = df.sort_values(["region_name", "year"])

    for region_name, group in df.groupby("region_name"):
        prev = last_actual_map.get(region_name, 0.0)

        for _, row in group.iterrows():
            raw_val = float(row["raw_pred"])

            if prev <= 0:
                # 이전 값이 0이면 그대로 사용 (혹은 약간의 최소값 부여 가능)
                val = raw_val
            else:
                # 허용 범위 [prev * (1 - max_down), prev * (1 + max_up)] 안으로 클램핑
                lower = prev * (1.0 - max_down)
                upper = prev * (1.0 + max_up)

                val = raw_val
                if val < lower:
                    val = lower
                elif val > upper:
                    val = upper

            adjusted_values.append(val)
            prev = val

    return np.array(adjusted_values)

# -------------------------------
# 6) PREDICTION_RESULT 저장
# -------------------------------

def save_predictions_to_db(future_df: pd.DataFrame, final_counts: np.ndarray) -> None:
    """
    - 기존 PREDICTION_RESULT 중 예측 구간(year >= FORECAST_START_YEAR)은
      source와 상관없이 전부 삭제
    - 새로운 ml_linear_rate_v0_3 예측을 INSERT
    """
    print(
        f"[INFO] 기존 예측 삭제: year >= {FORECAST_START_YEAR} (source 무관)"
    )
    deleted = (
        PredictionResult.query
        .filter(PredictionResult.year >= FORECAST_START_YEAR)
        .delete(synchronize_session=False)
    )
    db.session.commit()
    print(f"[INFO] 삭제된 행 수: {deleted}")

    print("[INFO] 새로운 예측 INSERT ...")

    # future_df는 region_name, year 기준으로 정렬된 상태로 들어온다고 가정
    df = future_df.sort_values(["region_name", "year"]).reset_index(drop=True)

    for idx, row in df.iterrows():
        value = float(final_counts[idx])
        if value < 0:
            value = 0.0  # 음수 방지

        pr = PredictionResult(
            region_name=row["region_name"],
            year=int(row["year"]),
            prediction_value=value,
            source=ML_SOURCE,   # "ml_linear_rate_v0_3"
        )
        db.session.add(pr)

    db.session.commit()
    print(f"[DONE] PREDICTION_RESULT 저장 완료 (source='{ML_SOURCE}')")

# -------------------------------
# main
# -------------------------------

def main():
    app = create_app()
    with app.app_context():
        print("[STEP] ELDERLY_HISTORY 노인 인구 예측 로딩 ...")
        elderly_forecast_map = load_elderly_population_forecast()
        print(f"[INFO] 노인 인구 (region_id, year) 매핑 수: {len(elderly_forecast_map)}")

        print("[STEP] 학습용 ELDERLY_STATS 데이터 로딩 ...")
        df_train = load_training_dataframe()
        print(f"[INFO] 학습 샘플 수: {len(df_train)}")

        print("[STEP] Ridge 다중회귀 학습 + 2023 평가 ...")
        model = train_and_evaluate(df_train)

        print("[STEP] 2023년 최신 통계(ELDERLY_STATS) 로딩 ...")
        latest_stats = load_latest_stats_per_region()
        print(f"[INFO] 구 개수: {len(latest_stats)}")

        print(f"[STEP] 미래 피처 DataFrame 생성 ({FORECAST_START_YEAR}~{FORECAST_LAST_YEAR}) ...")
        df_future = build_future_feature_df(latest_stats, elderly_forecast_map)

        print("[STEP] 미래 디자인 행렬 생성 ...")
        X_future = build_future_design_matrix(df_future, model)

        print("[STEP] 미래 고독사율 예측 ...")
        pred_rates = model.predict(X_future)
        # 음수율은 0으로 잘라줌
        pred_rates = np.clip(pred_rates, 0.0, None)

        # 🔹 예측된 "율" × 노인 인구 = 고독사 수
        elderly_pop_array = df_future["elderly_population"].to_numpy(dtype=float)
        raw_counts = pred_rates * elderly_pop_array

        print("[STEP] 단조비감소(연도별 감소 금지) 후처리 ...")
        final_counts = enforce_smooth_change_by_region(
            df_future,
            raw_counts,
            latest_stats,
            max_up=0.15,  # 한 해에 최대 +15% 증가
            max_down=0.15,  # 한 해에 최대 -15% 감소
        )

        print("[STEP] DB 저장 ...")
        save_predictions_to_db(df_future, final_counts)

        print("[ALL DONE] ml_linear_rate_v0_3 파이프라인 완료.")


if __name__ == "__main__":
    main()
