# belong/ml/train_elderly_population.py

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

from belong.app import create_app
from belong.extensions import db
from belong.models.elderly_history import ElderlyHistory
from belong.models.region import Region

# 모델 저장 위치: belong/ml/elderly_population_model.pkl
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "elderly_population_model.pkl"

FORECAST_LAST_YEAR = 2035
def load_timeseries(start_year: int = 2017, end_year: int = 2023) -> pd.DataFrame:
    """
    ELDERLY_HISTORY(실측, is_forecast='N')에서 노인 인구 타임시리즈 로딩.
    REGION + ELDERLY_HISTORY 조인해서 (region_id, region, year, elderly_population) DataFrame 생성.
    """
    query = (
        db.session.query(
            Region.id.label("region_id"),
            Region.name.label("region"),
            ElderlyHistory.year.label("year"),
            ElderlyHistory.elderly_population.label("elderly_population"),
        )
        .join(ElderlyHistory, ElderlyHistory.region_id == Region.id)
        .filter(ElderlyHistory.is_forecast == "N")
        .filter(ElderlyHistory.year.between(start_year, end_year))
        .order_by(Region.name, ElderlyHistory.year)
    )
    engine = db.engine
    df = pd.read_sql(query.statement, con=engine)

    # 타입 정리
    df["year"] = df["year"].astype(int)
    df["elderly_population"] = pd.to_numeric(df["elderly_population"], errors="coerce")
    df = df.dropna(subset=["elderly_population"])
    df["region"] = df["region"].astype(str).str.strip()

    print(f"[ELD_ML] 실측 타임시리즈 shape: {df.shape}")
    return df


def train_all_models(ts: pd.DataFrame):
    """
    구별(year → elderly_population) 선형회귀 모델을 학습하고,
    전체 RMSE / MAE / R^2 를 계산해서 리턴.
    """
    models: dict[str, dict] = {}
    all_true: list[float] = []
    all_pred: list[float] = []

    for region, group in ts.groupby("region"):
        g = group.sort_values("year")
        if g["year"].nunique() < 3:
            print(f"[ELD_ML] region={region}: 연도 데이터가 3개 미만 → 스킵")
            continue

        X = g["year"].values.reshape(-1, 1)
        y = g["elderly_population"].values.astype(float)

        model = LinearRegression()
        model.fit(X, y)
        y_hat = model.predict(X)

        all_true.extend(y.tolist())
        all_pred.extend(y_hat.tolist())

        models[region] = {
            "coef": float(model.coef_[0]),
            "intercept": float(model.intercept_),
            "history": g[["year", "elderly_population"]].to_dict(orient="records"),
        }

    all_true_arr = np.array(all_true)
    all_pred_arr = np.array(all_pred)

    rmse = float(np.sqrt(mean_squared_error(all_true_arr, all_pred_arr)))
    mae = float(mean_absolute_error(all_true_arr, all_pred_arr))
    r2 = float(r2_score(all_true_arr, all_pred_arr))

    metrics = {"rmse": rmse, "mae": mae, "r2": r2}
    print("[ELD_ML] 학습 완료 - 전체 메트릭")
    print(f"  RMSE: {rmse:.3f}")
    print(f"  MAE : {mae:.3f}")
    print(f"  R^2 : {r2:.3f}")

    return models, metrics


def save_models(models: dict):
    """
    구별 선형 모델(coef, intercept, history)을 pkl로 저장.
    서비스에서는 이 파일을 읽어서 year를 넣으면 예측값을 계산할 수 있음.
    """
    joblib.dump(models, MODEL_PATH)
    print(f"[ELD_ML] 모델 저장 완료: {MODEL_PATH}")


def make_forecast_df(
    ts: pd.DataFrame,
    models: dict,
    start_year: int = 2017,
    end_year: int = FORECAST_LAST_YEAR,
) -> pd.DataFrame:
    """
    학습된 per-region 선형 모델을 이용해 start_year~end_year 예측 DataFrame 생성.
    """
    # region -> region_id 매핑
    region_map = (
        ts[["region", "region_id"]]
        .drop_duplicates()
        .set_index("region")["region_id"]
        .to_dict()
    )

    rows = []
    for region, model_info in models.items():
        coef = model_info["coef"]
        intercept = model_info["intercept"]
        region_id = region_map.get(region)
        if region_id is None:
            print(f"[ELD_ML] 경고: region_id를 찾을 수 없음 - region={region}, 스킵")
            continue

        for year in range(start_year, end_year + 1):
            pred = coef * year + intercept
            rows.append(
                {
                    "region": region,
                    "region_id": int(region_id),
                    "year": int(year),
                    "predicted_elderly_population": int(round(pred)),
                }
            )

    df_future = pd.DataFrame(rows)
    print(f"[ELD_ML] 예측 DataFrame shape: {df_future.shape}")
    return df_future


def save_forecast_to_db(df_future: pd.DataFrame, forecast_start_year: int = 2024) -> None:
    """
    df_future의 예측값 중 forecast_start_year~end_year 구간을
    ELDERLY_HISTORY 에 is_forecast='Y' 로 upsert.
    """
    inserted = 0
    updated = 0

    for _, row in df_future.iterrows():
        year = int(row["year"])
        if year < forecast_start_year:
            # 2017~2023 구간은 이미 실측(is_forecast='N')이 있으므로 스킵
            continue

        region_id = int(row["region_id"])
        predicted_value = int(row["predicted_elderly_population"])

        history = (
            ElderlyHistory.query
            .filter_by(region_id=region_id, year=year, is_forecast="Y")
            .one_or_none()
        )

        if history is None:
            history = ElderlyHistory(
                region_id=region_id,
                year=year,
                is_forecast="Y",
            )
            db.session.add(history)
            inserted += 1
        else:
            updated += 1

        history.elderly_population = predicted_value

    db.session.commit()
    print(f"[ELD_ML] 예측값 DB 저장 완료: insert={inserted}, update={updated}")


def main():
    app = create_app()
    with app.app_context():
        # 1) 실측 타임시리즈 로딩 (2017~2023)
        ts = load_timeseries(start_year=2017, end_year=2023)

        # 2) 구별 선형 모델 학습 + 메트릭 출력
        models, metrics = train_all_models(ts)

        # 3) pkl 저장
        save_models(models)

        # 4) 2017~2035 예측 DataFrame 생성
        df_future = make_forecast_df(ts, models, start_year=2017, end_year=2035)

        # 5) 2024~2035 구간을 ELDERLY_HISTORY(is_forecast='Y')에 upsert
        save_forecast_to_db(df_future, forecast_start_year=2024)


if __name__ == "__main__":
    main()
