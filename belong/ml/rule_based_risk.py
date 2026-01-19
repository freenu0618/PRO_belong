
from dataclasses import dataclass
from typing import Literal, Dict
from belong.ml.region_weights import get_weights_for_region

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass
class ElderlyRiskFeatures:
    single_household_ratio: float
    low_income_65_79_ratio: float
    low_income_80_over_ratio: float
    aging_index: float
    elderly_population_ratio: float


def _normalize(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    x = value / max_value
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return x


def compute_risk_score(region_name: str, features: ElderlyRiskFeatures) -> float:
    """
    region별 weight를 사용해 0~1 사이 위험지수 계산
    """
    # 1) feature 정규화
    scores: Dict[str, float] = {
        "single_household_ratio":           _normalize(features.single_household_ratio, max_value=40.0),
        "low_income_elderly_65_79_ratio":   _normalize(features.low_income_65_79_ratio, max_value=30.0),
        "low_income_elderly_80_over_ratio": _normalize(features.low_income_80_over_ratio, max_value=30.0),
        "aging_index":                      _normalize(features.aging_index, max_value=250.0),
        "elderly_population_ratio":         _normalize(features.elderly_population_ratio, max_value=35.0),
    }

    # 2) region별 weight 가져오기
    weights = get_weights_for_region(region_name)

    # 3) 가중합
    risk = 0.0
    for feat, s in scores.items():
        w = weights.get(feat, 0.0)
        risk += w * s

    if risk < 0:
        risk = 0.0
    if risk > 1:
        risk = 1.0
    return risk

# 추가적으로 risk기능을 추가할때 사용가능
def to_risk_level(score: float) -> RiskLevel:
    if score >= 0.7:
        return "HIGH"
    elif score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"
