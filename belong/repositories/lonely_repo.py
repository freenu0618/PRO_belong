from typing import List, Dict
from sqlalchemy import func

from belong.extensions import db
from belong.models.feature_stats import ElderlyStats  # target_value 컬럼 포함
from belong.models.region import Region
from belong.models.prediction_result import PredictionResult

# 실측 데이터가 존재하는 마지막 연도
ACTUAL_LAST_YEAR = 2023

# ✅ PREDICTION_RESULT.source 에 사용되는 고독사 예측 식별자
#    실제 DB에 맞게 'rule_based' 로 통일
LONELY_SOURCE = "rule_based"

class LonelyStatsRepository:
    """
    고독사(ELDERLY_STATS.target_value / PREDICTION_RESULT.prediction_value) 조회용 Repo.

    - get_total_trend(start_year, end_year)
      -> 서울 전체 고독사 인원 추세 (실측 + 예측)
    - get_region_values_for_years(base_year, target_year)
      -> 특정 두 연도 기준으로, 구별 고독사 수(실측/예측)를 합쳐서 반환
         (TOP5 증가율/증가수 계산용)
    """

    # =========================
    # 내부 헬퍼 – 전체 합계 쿼리
    # =========================
    def _query_actual_total(self, start_year: int, end_year: int):
        """
        ELDERLY_STATS 에서 연도별(서울 전체) 고독사 실측 합계를 조회.
        """
        return (
            db.session.query(
                ElderlyStats.year.label("year"),
                func.sum(ElderlyStats.target_value).label("value"),
            )
            .filter(
                ElderlyStats.year >= start_year,
                ElderlyStats.year <= end_year,
            )
            .group_by(ElderlyStats.year)
            .order_by(ElderlyStats.year)
            .all()
        )

    def _query_forecast_total(self, start_year: int, end_year: int):
        """
        PREDICTION_RESULT 에서 연도별(서울 전체) 고독사 예측 합계를 조회.
        """
        return (
            db.session.query(
                PredictionResult.year.label("year"),
                func.sum(PredictionResult.prediction_value).label("value"),
            )
            .filter(
                PredictionResult.year >= start_year,
                PredictionResult.year <= end_year,
                PredictionResult.source == LONELY_SOURCE,
            )
            .group_by(PredictionResult.year)
            .order_by(PredictionResult.year)
            .all()
        )

    # =========================
    # 공개 메서드 – 전체 추세
    # =========================
    def get_total_trend(self, start_year: int, end_year: int) -> List[Dict]:
        """
        연도별(전체 서울) 고독사 인원 추세.

        - year <= ACTUAL_LAST_YEAR : ELDERLY_STATS.target_value 합(실측)
        - year >  ACTUAL_LAST_YEAR : PREDICTION_RESULT.prediction_value 합(예측)

        반환 형식:
        [
            {"year": 2017, "value": 123, "is_forecast": False},
            {"year": 2018, "value": 140, "is_forecast": False},
            ...
            {"year": 2024, "value": 200, "is_forecast": True},
        ]
        """
        items: List[Dict] = []

        # 1) 실측 구간
        actual_end = min(end_year, ACTUAL_LAST_YEAR)
        if start_year <= actual_end:
            for r in self._query_actual_total(start_year, actual_end):
                items.append(
                    {
                        "year": int(r.year),
                        "value": int(r.value or 0),
                        "is_forecast": False,
                    }
                )

        # 2) 예측 구간
        forecast_start = max(start_year, ACTUAL_LAST_YEAR + 1)
        if forecast_start <= end_year:
            for r in self._query_forecast_total(forecast_start, end_year):
                items.append(
                    {
                        "year": int(r.year),
                        "value": int(r.value or 0),
                        "is_forecast": True,
                    }
                )

        # 혹시라도 섞여 들어온 경우를 대비해서 연도 기준 정렬
        items.sort(key=lambda x: x["year"])
        return items

    # =========================
    # 내부 헬퍼 – 연도별 구별 값
    # =========================
    def _get_region_values_for_year(self, year: int) -> List[Dict]:
        """
        특정 연도에 대해, 구별 고독사 값(실측 또는 예측)을 가져온다.

        year <= ACTUAL_LAST_YEAR:
            - ELDERLY_STATS.target_value 기준
        year > ACTUAL_LAST_YEAR:
            - PREDICTION_RESULT.prediction_value (source='lonely_death') 기준

        반환 형식:
        [
            {"region_id": 1, "region": "강남구", "value": 10},
            {"region_id": 2, "region": "강동구", "value": 5},
            ...
        ]
        """
        # 1) 실측 구간
        if year <= ACTUAL_LAST_YEAR:
            rows = (
                db.session.query(
                    Region.id.label("region_id"),
                    Region.name.label("region"),
                    func.sum(ElderlyStats.target_value).label("value"),
                )
                .join(Region, ElderlyStats.region_id == Region.id)
                .filter(ElderlyStats.year == year)
                .group_by(Region.id, Region.name)
                .order_by(Region.id)
                .all()
            )
        else:
            # 2) 예측 구간 – PredictionResult.region_name 과 Region.name 을 매칭
            rows = (
                db.session.query(
                    Region.id.label("region_id"),
                    Region.name.label("region"),
                    func.sum(PredictionResult.prediction_value).label("value"),
                )
                .join(Region, Region.name == PredictionResult.region_name)
                .filter(
                    PredictionResult.year == year,
                    PredictionResult.source == LONELY_SOURCE,
                )
                .group_by(Region.id, Region.name)
                .order_by(Region.id)
                .all()
            )

        return [
            {
                "region_id": int(r.region_id),
                "region": r.region,
                "value": int(r.value or 0),
            }
            for r in rows
        ]

    # =========================
    # 공개 메서드 – TOP5용 구별 값
    # =========================
    def get_region_values_for_years(
        self, base_year: int, target_year: int
    ) -> List[Dict]:
        """
        base_year, target_year 두 시점의 구별 고독사 값을 합쳐서 반환.

        반환 형식:
        [
            {
                "region_id": 1,
                "region": "강남구",
                "base_year": 2017,
                "base_value": 10,
                "target_year": 2023,
                "target_value": 25,
            },
            ...
        ]

        이 결과를 바탕으로 서비스 레이어에서
        - 증가수(diff = target_value - base_value)
        - 증가율(ratio = diff / base_value)
        등을 계산해서 TOP5를 뽑는다.
        """
        base_rows = self._get_region_values_for_year(base_year)
        target_rows = self._get_region_values_for_year(target_year)

        # region 이름을 key 로 합치기 (id도 같이 보관)
        data: Dict[str, Dict] = {}

        # 1) base_year 값 채우기
        for r in base_rows:
            key = r["region"]
            data[key] = {
                "region_id": r["region_id"],
                "region": r["region"],
                "base_year": base_year,
                "base_value": r["value"],
                "target_year": target_year,
                "target_value": None,
            }

        # 2) target_year 값 채우기 (없는 지역은 base_value=None 으로 생성)
        for r in target_rows:
            key = r["region"]
            if key not in data:
                data[key] = {
                    "region_id": r["region_id"],
                    "region": r["region"],
                    "base_year": base_year,
                    "base_value": None,
                    "target_year": target_year,
                    "target_value": r["value"],
                }
            else:
                data[key]["target_value"] = r["value"]

        return list(data.values())