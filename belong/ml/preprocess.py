import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
#__file__: 현재 실행 중인 파일(예: preprocess.py)의 파일 경로 문자열.
#.resolve(): 심볼릭 링크나 상대경로가 있을 경우, 절대경로로 변환.
#.parent: 디렉터리의 바로 상위 폴더.

RAW_DIR = BASE_DIR / "dataset" / "raw_data"
PROCESSED_DIR = BASE_DIR / "dataset"
rename_map = {
    "구": "region",
    "연도": "year",

    # 주거 유형 (계 = total)
    "단독주택_계": "single_house_total",
    "아파트_계": "apartment_total",
    "연립주택_계": "row_house_total",
    "다세대주택_계": "multi_house_total",
    "비주거용 건물내 주택_계": "non_residential_housing_total",

    # Target (값 → 모델 예측값 또는 고독사 값이라면 아래 중 선택)
    # → 데이터 정의 확정 필요
    "값": "target_value",

    # 인구 지표
    "총인구": "population_total",
    "총인구_남자": "population_male",
    "총인구_여자": "population_female",

    # 연령 구조
    "20세 미만": "under_20",
    "65세 이상": "age_65_over",
    "0~14세": "age_0_14",

    # 1인가구 관련
    "1인가구_비율": "single_household_ratio",

    # 경제/환경 지표
    "소비자물가": "cpi_index",  # Consumer Price Index

    # 노령화 지표
    "노령화지수": "aging_index",

    # 변화율 관련
    "전년 대비 증감": "population_change_count",
    "증감률": "population_growth_ratio",

    # 저소득 노인 비율
    "저소득노인_65~79비율": "low_income_elderly_65_79_ratio",
    "저소득노인_80이상비율": "low_income_elderly_80_over_ratio",

    # 기초생활수급자
    "기초생활수급자총인원": "basic_pension_recipient_count",
    "기초생활수급자비율": "basic_pension_recipient_ratio"
}

'''
데이터 csv파일은 이미 전처리를 해놨기 때문에
함수만 만들어놓고 지금은 작성하지 않고 pass만 함.

실제 컬럼 처리는 원래 raw 데이터에 맞게 넣고 파일구조 + 함수나누기를 만들어줘야함
'''
def load_alone_person():
    """1인가구 데이터"""
    df = pd.read_csv(RAW_DIR / "alone_person.csv")
    df.columns = ["region","year","alone_household_count"]
    return df


def load_elderly_population():
  # raw 파일 읽어서 region/year/elderly_population 형태로 반환
  """65세 이상 노인 인구수"""
  df = pd.read_csv(RAW_DIR / "elderly_person_value.csv")
  df.columns = ["region", "year", "elderly_population"]

  return df

def load_merged_sum():
    '''그 외 모든 feature 포함된  dataset'''
    df = pd.read_csv(RAW_DIR / "merged_sum.csv")
    # 구별 column 선택 제거 후 rename
    df = df.rename(columns = rename_map, errors="ignore")
    return df


def ensure_dtype(df):
    df["region"] = df["region"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    return df


def merge_all():
    """세 개의 데이터셋을 key(region,year) 기준으로 병합"""
    alone = load_alone_person()
    elderly = load_elderly_population()
    merged = load_merged_sum()

    alone = ensure_dtype(alone)
    elderly = ensure_dtype(elderly)
    merged = ensure_dtype(merged)

    df = merged.merge(alone, on=["region", "year"], how="left")
    df = df.merge(elderly, on=["region", "year"], how="left")

    return df


def build_merged_dataset():
    df = merge_all()
    out_path = PROCESSED_DIR / "merged_dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"📁 저장 완료 → {out_path}")


if __name__ == "__main__":
    build_merged_dataset()
