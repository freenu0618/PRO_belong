# belong/ml/load_elderly_stats_from_csv.py

import os
import math
import pandas as pd

from belong.app import create_app
from belong.extensions import db
from belong.models import Region, ElderlyStats  # ElderlyHistory는 그대로 둠


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "ml", "dataset", "merged_dataset.csv")


def to_int(value):
    """NaN 이면 None, 아니면 int로 변환."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_float(value):
    """NaN 이면 None, 아니면 float로 변환."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_regions(df: pd.DataFrame):
    """CSV의 region 컬럼을 기준으로 REGION 테이블 채우기."""
    region_names = sorted(df["region"].unique())
    print(f"[REGION] CSV에서 발견한 구 개수: {len(region_names)}")

    for name in region_names:
        existed = Region.query.filter_by(name=name).first()
        if existed:
            print(f"  - 이미 존재: {name} (id={existed.id})")
            continue

        region = Region(name=name)  # code는 나중에 UPDATE로 채워도 됨
        db.session.add(region)
        print(f"  + 새로 추가: {name}")

    db.session.commit()
    print("[REGION] 커밋 완료.")

    regions = {r.name: r.id for r in Region.query.all()}
    print(f"[REGION] 총 {len(regions)}개 구 로딩됨.")
    return regions


def load_elderly_stats(df: pd.DataFrame, region_map: dict[str, int]):
    """CSV 데이터를 ELDERLY_STATS 테이블에 적재."""
    total_rows = len(df)
    print(f"[ELDERLY_STATS] 적재 대상 행 수: {total_rows}")

    inserted = 0
    skipped = 0

    for idx, row in df.iterrows():
        region_name = row["region"]
        year = int(row["year"])

        region_id = region_map.get(region_name)
        if region_id is None:
            print(f"  ! REGION 미정의: {region_name} (row={idx}) → 스킵")
            skipped += 1
            continue

        # 이미 (region_id, year) 데이터가 있다면 스킵 (중복 방지)
        existed = ElderlyStats.query.filter_by(
            region_id=region_id,
            year=year,
        ).first()
        if existed:
            skipped += 1
            continue

        stats = ElderlyStats(
            region_id=region_id,
            year=year,

            # ===== merged_dataset.csv 컬럼 매핑 =====
            single_house_total=to_int(row.get("single_house_total")),
            apartment_total=to_int(row.get("apartment_total")),
            row_house_total=to_int(row.get("row_house_total")),
            multi_house_total=to_int(row.get("multi_house_total")),
            non_residential_housing_total=to_int(row.get("non_residential_housing_total")),

            target_value=to_int(row.get("target_value")),
            aging_index=to_float(row.get("aging_index")),
            population_total=to_int(row.get("population_total")),
            population_male=to_int(row.get("population_male")),
            population_female=to_int(row.get("population_female")),
            population_change_count=to_int(row.get("population_change_count")),
            population_growth_ratio=to_float(row.get("population_growth_ratio")),
            single_household_ratio=to_float(row.get("single_household_ratio")),

            under_20=to_int(row.get("under_20")),
            age_65_over=to_int(row.get("age_65_over")),
            age_0_14=to_int(row.get("age_0_14")),
            cpi_index=to_float(row.get("cpi_index")),

            low_income_elderly_65_79_ratio=to_float(row.get("low_income_elderly_65_79_ratio")),
            low_income_elderly_80_over_ratio=to_float(row.get("low_income_elderly_80_over_ratio")),
            basic_pension_recipient_count=to_int(row.get("basic_pension_recipient_count")),
            basic_pension_recipient_ratio=to_float(row.get("basic_pension_recipient_ratio")),

            alone_household_count=to_int(row.get("alone_household_count")),
            elderly_population=to_int(row.get("elderly_population")),
        )

        db.session.add(stats)
        inserted += 1

        if inserted % 50 == 0:
            print(f"  - {inserted}행 처리 중...")

    db.session.commit()
    print(f"[ELDERLY_STATS] 적재 완료: inserted={inserted}, skipped={skipped}")


def main():
    print(f"[ETL] CSV 경로: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    print(f"[ETL] CSV 로드 완료: shape={df.shape}")

    app = create_app()
    with app.app_context():
        # 1) REGION 채우기
        region_map = load_regions(df)

        # 2) ELDERLY_STATS 채우기
        load_elderly_stats(df, region_map)


if __name__ == "__main__":
    main()
