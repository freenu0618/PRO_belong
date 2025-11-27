# belong/ml/train_lonely_death.py

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from statsmodels.stats.outliers_influence import variance_inflation_factor
import joblib

from belong.app import create_app
from belong.extensions import db
from belong.models.feature_stats import ElderlyStats
from belong.models.region import Region


# ----------------------------------------------------------------------
# 모델 저장 경로: belong/ml/forecast_model.pkl
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "forecast_model.pkl"


# ----------------------------------------------------------------------
# 1) DB → pandas DataFrame 로딩
# ----------------------------------------------------------------------
def load_dataset_from_db() -> pd.DataFrame:
    """REGION + ELDERLY_STATS 조인해서 학습용 DataFrame 생성"""
    app = create_app()
    with app.app_context():
        query = (
            db.session.query(
                # --- 카테고리 & 기본 정보 ---
                Region.name.label("region"),
                ElderlyStats.year,

                # --- 주거 형태 ---
                ElderlyStats.single_house_total,
                ElderlyStats.apartment_total,
                ElderlyStats.row_house_total,
                ElderlyStats.multi_house_total,
                ElderlyStats.non_residential_housing_total,

                # --- 인구/경제 구조 ---
                ElderlyStats.aging_index,
                ElderlyStats.population_total,
                ElderlyStats.population_change_count,
                ElderlyStats.single_household_ratio,
                ElderlyStats.under_20,
                ElderlyStats.age_65_over,
                ElderlyStats.age_0_14,
                ElderlyStats.cpi_index,

                # 저소득 노인 비율 (DB 컬럼은 LOW_INC_... 이지만 attr 는 아래 이름)
                ElderlyStats.low_income_elderly_65_79_ratio.label("low_inc_65_79_ratio"),
                ElderlyStats.low_income_elderly_80_over_ratio.label("low_inc_80_over_ratio"),

                # 기초연금/독거 관련
                ElderlyStats.basic_pension_recipient_ratio,
                ElderlyStats.alone_household_count,
                ElderlyStats.elderly_population,

                # --- 타깃 ---
                ElderlyStats.target_value,
            )
            .join(Region, Region.id == ElderlyStats.region_id)
        )

        engine = db.engine
        df = pd.read_sql(query.statement, con=engine)

        # SQLAlchemy quoted_name → 전부 문자열로 강제
        df.columns = df.columns.astype(str)

    return df


# ----------------------------------------------------------------------
# 2) VIF 계산
# ----------------------------------------------------------------------
def compute_vif(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    X = df[features].astype(float)
    vif_list = []
    for i, col in enumerate(features):
        vif = variance_inflation_factor(X.values, i)
        vif_list.append({"feature": col, "vif": vif})
    return pd.DataFrame(vif_list)


# ----------------------------------------------------------------------
# 3) 메인 학습 로직
# ----------------------------------------------------------------------
def main():
    # 1) 데이터 로딩
    df_raw = load_dataset_from_db()

    # ====== 피처/타깃 정의 ======
    numeric_features = [
        "single_house_total",
        "apartment_total",
        "row_house_total",
        "multi_house_total",
        "non_residential_housing_total",
        "aging_index",
        "population_total",
        "population_change_count",
        "single_household_ratio",
        "under_20",
        "age_65_over",
        "age_0_14",
        "cpi_index",
        "low_inc_65_79_ratio",
        "low_inc_80_over_ratio",
        "basic_pension_recipient_ratio",
        "alone_household_count",
        "elderly_population",
    ]
    cat_features = ["region"]
    target_col = "target_value"

    # 2) NaN / inf 정리
    df = df_raw.copy()
    df.columns = df.columns.astype(str)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    before = len(df)
    df = df.dropna(subset=numeric_features + cat_features + [target_col])
    after = len(df)
    print(f"[INFO] NaN/inf 제거 후 행 수: {after} / 원본 {before}")

    # 3) VIF 출력 (df는 이미 클린 상태)
    vif_df = compute_vif(df, numeric_features)
    print("\n[INFO] VIF 결과 (내림차순):")
    print(vif_df.sort_values("vif", ascending=False))

    # ---- 여기서 numeric_features 수정하고 싶으면 직접 리스트에서 빼기 ----
    # 예시)
    # drop_cols = ["elderly_population", "age_65_over", "population_total"]
    # numeric_features = [c for c in numeric_features if c not in drop_cols]
    # ---------------------------------------------------------------

    # 4) 최종 X, y 구성 (이제 여기서부터는 numpy로만 진행)
    X_num = df[numeric_features].astype(float).to_numpy()
    X_cat = df[cat_features].astype(str).to_numpy()  # (n_samples, 1)
    X_all = np.concatenate([X_num, X_cat], axis=1)
    y = df[target_col].to_numpy()

    print(f"[INFO] X_all shape: {X_all.shape}, y shape: {y.shape}")

    # 5) Train / Test split (랜덤)
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y, test_size=0.2, random_state=42
    )

    # 🔥 여기서부터는 컬럼 "이름"을 전혀 쓰지 않고, "인덱스"만 사용
    num_indices = list(range(len(numeric_features)))
    cat_indices = list(
        range(len(numeric_features), len(numeric_features) + len(cat_features))
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_indices),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_indices),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("regressor", LinearRegression()),
        ]
    )

    # 7) 학습
    model.fit(X_train, y_train)

    # 8) 평가
    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred,)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\n[METRIC] RMSE: {rmse:.3f}")
    print(f"[METRIC] MAE : {mae:.3f}")
    print(f"[METRIC] R²  : {r2:.3f}")

    # 9) 모델 저장 (기존 forecast_service 호환되게, 순수 pipeline만 저장)
    joblib.dump(model, MODEL_PATH)
    print(f"\n[INFO] 모델 저장 완료: {MODEL_PATH}")


if __name__ == "__main__":
    main()
