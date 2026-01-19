import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
import joblib

# BASE_DIR should be the directory containing 'dataset'
# Since dataset is in c:\project_belong\belong\ml\dataset, and this file is in c:\project_belong\belong\ml\forecast.py
# BASE_DIR should be c:\project_belong\belong\ml (which is Path(__file__).parent)
BASE_DIR = Path(__file__).resolve().parent 

ALONE_POPULATION_PATH = BASE_DIR / "dataset/raw_data/alone_person.csv"
# 2007년~ 2023년도 독거노인 인구수 데이터 추가해서 넣어놨음
DATA_PATH = BASE_DIR / "dataset" / "merged_sum.csv"
MODEL_PATH = Path(__file__).resolve().parent / "forecast_model.pkl"

TARGET_COLUMN = "value"

def load_dataset():
    # Check if file exists
    if not ALONE_POPULATION_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {ALONE_POPULATION_PATH}")
    return pd.read_csv(ALONE_POPULATION_PATH)

def make_timeseries(df):
    ts = df[["region", "year", TARGET_COLUMN]].dropna().copy()

    # 데이터 타입 및 정렬 처리
    ts["year"] = ts["year"].astype(int)
    return ts.sort_values(["region", "year"])

def train_region_model(region_df):
    if region_df["year"].nunique() < 3:
        return None
    X = region_df["year"].values.reshape(-1, 1)
    y = region_df[TARGET_COLUMN].values
    model = LinearRegression()
    model.fit(X, y)
    return model

def train_all_models(ts):
    models = {}
    for region, group in ts.groupby("region"):
        model = train_region_model(group)
        if model is None:
            continue
        models[region] = {
            "coef": float(model.coef_[0]),
            "intercept": float(model.intercept_),
            "history": group[["year", TARGET_COLUMN]].to_dict(orient="records")
        }
    return models

def save_models(models):
    joblib.dump(models, MODEL_PATH)

if __name__ == "__main__":
    try:
        df = load_dataset()
        ts = make_timeseries(df)
        models = train_all_models(ts)
        save_models(models)
        print("saved:", MODEL_PATH)
    except Exception as e:
        print("Error running forecast.py:", e)
