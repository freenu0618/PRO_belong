# belong/ml/load_elderly_stats_from_csv.py

from pathlib import Path

import pandas as pd

from belong.app import create_app
from belong.extensions import db
from belong.models.region import Region
from belong.models.feature_stats import ElderlyStats  # 공식 모델만 사용!


# ----------------------------------------------------------------------
# 설정
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "merged_dataset.csv"


# ----------------------------------------------------------------------
# 유틸: NaN → None, 숫자 변환
# ----------------------------------------------------------------------
def _to_int(value):
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------------
# REGION 로딩
# ----------------------------------------------------------------------
def load_regions(df: pd.DataFrame) -> dict:
    """CSV의 region 컬럼에서 25개 구 이름을 추출해서 REGION 테이블에 적재."""
    region_names = sorted(df["region"].unique())
    print(f"[REGION] CSV에서 발견된 구 개수: {len(region_names)}")

    inserted = 0
    for name in region_names:
        existing = Region.query.filter_by(name=name).one_or_none()
        if existing:
            continue
        region = Region(name=name)
        db.session.add(region)
        inserted += 1

    if inserted > 0:
        db.session.commit()
        print(f"[REGION] 새로 추가된 구 개수: {inserted}")
    else:
        print("[REGION] 새로 추가된 구 없음 (이미 모두 존재)")

    regions = Region.query.filter(Region.name.in_(region_names)).all()
    region_map = {r.name: r.id for r in regions}
    print(f"[REGION] 총 {len(region_map)}개 구 로딩됨.")
    return region_map


# ----------------------------------------------------------------------
# ELDERLY_STATS 로딩
# ----------------------------------------------------------------------
def load_elderly_stats(df: pd.DataFrame, region_map: dict) -> None:
    """
    merged_dataset.csv 한 행(row)마다 ELDERLY_STATS 한 행을 생성/갱신.
    - (region, year) → REGION_ID / YEAR 로 매핑
    - 이미 (REGION_ID, YEAR)가 있으면 UPDATE, 없으면 INSERT
    """
    total_rows = len(df)
    print(f"[ELDERLY_STATS] 적재 대상 행 수: {total_rows}")

    inserted = 0
    updated = 0

    for _, row in df.iterrows():
        region_name = row["region"]
        year = int(row["year"])

        region_id = region_map.get(region_name)
        if region_id is None:
            print(f"[ELDERLY_STATS] 경고: REGION '{region_name}' 을(를) 찾을 수 없음. 건너뜀.")
            continue

        existing = ElderlyStats.query.filter_by(region_id=region_id, year=year).one_or_none()

        if existing:
            stats = existing
            updated += 1
        else:
            stats = ElderlyStats(region_id=region_id, year=year)
            db.session.add(stats)
            inserted += 1

        # ---- CSV → 모델 필드 매핑 (컬럼명 그대로 사용) ----
        stats.single_house_total = _to_int(row["single_house_total"])
        stats.apartment_total = _to_int(row["apartment_total"])
        stats.row_house_total = _to_int(row["row_house_total"])
        stats.multi_house_total = _to_int(row["multi_house_total"])
        stats.non_residential_housing_total = _to_int(row["non_residential_housing_total"])

        stats.target_value = _to_int(row["target_value"])

        stats.aging_index = _to_float(row["aging_index"])

        stats.population_total = _to_int(row["population_total"])
        stats.population_male = _to_int(row["population_male"])
        stats.population_female = _to_int(row["population_female"])
        stats.population_change_count = _to_int(row["population_change_count"])
        stats.population_growth_ratio = _to_float(row["population_growth_ratio"])

        stats.single_household_ratio = _to_float(row["single_household_ratio"])

        stats.under_20 = _to_int(row["under_20"])
        stats.age_65_over = _to_int(row["age_65_over"])
        stats.age_0_14 = _to_int(row["age_0_14"])

        stats.cpi_index = _to_float(row["cpi_index"])

        stats.low_income_elderly_65_79_ratio = _to_float(
            row["low_income_elderly_65_79_ratio"]
        )
        stats.low_income_elderly_80_over_ratio = _to_float(
            row["low_income_elderly_80_over_ratio"]
        )

        stats.basic_pension_recipient_count = _to_int(
            row["basic_pension_recipient_count"]
        )
        stats.basic_pension_recipient_ratio = _to_float(
            row["basic_pension_recipient_ratio"]
        )

        stats.alone_household_count = _to_int(row["alone_household_count"])
        stats.elderly_population = _to_int(row["elderly_population"])

    db.session.commit()
    print(f"[ELDERLY_STATS] 적재 완료: inserted={inserted}, updated={updated}")


# ----------------------------------------------------------------------
# 메인
# ----------------------------------------------------------------------
def main():
    print(f"[LOADER] BASE_DIR: {BASE_DIR}")
    print(f"[LOADER] DATASET_PATH: {DATASET_PATH}")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"데이터셋 파일을 찾을 수 없습니다: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    app = create_app()
    with app.app_context():
        region_map = load_regions(df)
        load_elderly_stats(df, region_map)


if __name__ == "__main__":
    main()
