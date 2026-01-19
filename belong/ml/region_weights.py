# belong/ml/region_weights.py
from __future__ import annotations
from pathlib import Path
import csv
from collections import defaultdict
from typing import Dict

# global_corr.ipynb에서 계산한 값
GLOBAL_WEIGHTS: Dict[str, float] = {
    "single_household_ratio":              0.368467,
    "low_income_elderly_65_79_ratio":      0.038977,
    "low_income_elderly_80_over_ratio":    0.095469,
    "aging_index":                         0.311710,
    "elderly_population_ratio":            0.185376,
}

# REGION_WEIGHTS["강남구"]["single_household_ratio"] -> weight
REGION_WEIGHTS: Dict[str, Dict[str, float]] = defaultdict(dict)


def load_region_weights(csv_path: str | Path) -> None:
    """
    앱 시작 시 한 번만 호출해서 REGION_WEIGHTS 캐시에 적재.
    """
    global REGION_WEIGHTS
    REGION_WEIGHTS = defaultdict(dict)

    csv_path = Path(csv_path)
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["region"]
            feature = row["feature"]
            weight = float(row["weight"])
            REGION_WEIGHTS[region][feature] = weight


def get_weights_for_region(region_name: str) -> Dict[str, float]:
    """
    특정 구에 대한 weight 집합을 반환.
    CSV에 값이 없으면 GLOBAL_WEIGHTS 사용.
    """
    region_w = REGION_WEIGHTS.get(region_name)
    if not region_w:
        return GLOBAL_WEIGHTS
    return region_w
