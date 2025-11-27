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
MODEL_PATH = BASE_DIR / "lonely_death_model.pkl"


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
# 3) 메인 학습 로직 (v1.1 피처셋)
# ----------------------------------------------------------------------
def main():
    # 1) 데이터 로딩
    df_raw = load_dataset_from_db()

    # ====== 전체 numeric 피처 정의 (v1.0 기준 풀셋) ======
    numeric_features_full = [
        # 주거 형태
        "single_house_total",
        "apartment_total",
        "row_house_total",
        "multi_house_total",
        "non_residential_housing_total",
        # 인구/지표
        "aging_index",
        "population_total",
        "population_change_count",
        "single_household_ratio",
        "under_20",
        "age_65_over",
        "age_0_14",
        "cpi_index",
        # 저소득 노인 비율
        "low_inc_65_79_ratio",
        "low_inc_80_over_ratio",
        # 기초연금/독거/노인인구
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
    df = df.dropna(subset=numeric_features_full + cat_features + [target_col])
    after = len(df)
    print(f"[INFO] NaN/inf 제거 후 행 수: {after} / 원본 {before}")

    # 3) v1.0 풀셋 기준 VIF 확인
    vif_full = compute_vif(df, numeric_features_full)
    print("\n[INFO] v1.0 풀셋 VIF (내림차순):")
    print(vif_full.sort_values("vif", ascending=False))

    # 4) v1.1에서 제거할 고 VIF/중복 피처 목록
    drop_cols = [
        "elderly_population",   # 노인 인구수 (population_total, 저소득 비율 등과 강한 중복)
        "age_65_over",          # 65세 이상 인구수 (elderly_population 과 거의 동일 정보)
        "age_0_14",             # 유소년 비율은 under_20 으로 대표
        "alone_household_count",# 1인가구 비율(single_household_ratio)와 중복
        "aging_index",          # 연령구조를 요약한 지표 (위 인구 피처들과 중복)
    ]

    numeric_features = [c for c in numeric_features_full if c not in drop_cols]

    print("\n[INFO] v1.1에서 사용할 numeric_features:")
    print(numeric_features)

    # 5) v1.1 피처셋 기준 VIF 재확인
    vif_v11 = compute_vif(df, numeric_features)
    print("\n[INFO] v1.1 피처셋 VIF (내림차순):")
    print(vif_v11.sort_values("vif", ascending=False))

    # 6) 최종 X, y 구성 (sklearn 에는 numpy 만 넘긴다)
    X_num = df[numeric_features].astype(float).to_numpy()
    X_cat = df[cat_features].astype(str).to_numpy()
    X_all = np.concatenate([X_num, X_cat], axis=1)
    y = df[target_col].to_numpy()

    print(f"[INFO] X_all shape: {X_all.shape}, y shape: {y.shape}")

    # 7) Train / Test split (랜덤, 나중에 연도 기준으로 바꿔도 됨)
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y, test_size=0.2, random_state=42
    )

    # 인덱스로 수치/카테고리 위치 구분
    num_indices = list(range(len(numeric_features)))
    cat_indices = list(range(len(numeric_features), len(numeric_features) + len(cat_features)))

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

    # 8) 학습
    model.fit(X_train, y_train)

    # 9) 평가 (네 sklearn 버전 호환 방식)
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\n[METRIC] RMSE: {rmse:.3f}")
    print(f"[METRIC] MAE : {mae:.3f}")
    print(f"[METRIC] R²  : {r2:.3f}")

    # 10) 모델 저장
    joblib.dump(model, MODEL_PATH)
    print(f"\n[INFO] 모델 저장 완료: {MODEL_PATH}")


if __name__ == "__main__":
    main()
