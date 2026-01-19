# belong/services/region_risk_service.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from belong.extensions import logger
from belong.repositories.elderly_stats_repo import ElderlyStatsRepository
from belong.services.prediction_service import PredictionService


# 레이더 차트에 사용할 컬럼과 라벨 정의
RADAR_METRICS: List[tuple[str, str]] = [
    ("single_household_ratio", "1인가구 비율"),
    ("low_inc_65_79_ratio", "저소득 65~79세"),
    ("low_inc_80_plus_ratio", "저소득 80세 이상"),
    ("aging_index", "고령화 지수"),
    ("cpi_index", "소비자 물가"),
]


class RegionRiskService:
    """
    특정 '구'의 리스크 상세 정보를 제공하는 서비스 레이어.

    - 노인 인구 타임라인 (실측 + 예측 포인트)
    - 예측 분포 기반 리스크 레벨 (low / medium / high)
    - 레이더 차트용 지표 (해당 구 vs 서울 평균)

    웹 라우트에서는 이 서비스만 호출해서,
    템플릿에 넘길 dict을 그대로 받아 사용하는 것을 목표로 한다.
    """

    def __init__(
        self,
        prediction_service: PredictionService,
        elderly_stats_repo: ElderlyStatsRepository = None,
    ):
        """
        Args:
            prediction_service: 예측 서비스
            elderly_stats_repo: 노인 통계 Repository (DI)
        """
        self.prediction_service = prediction_service
        self.elderly_stats_repo = elderly_stats_repo or ElderlyStatsRepository()

    # -----------------------------
    # 공개 API
    # -----------------------------
    def get_region_detail(
        self, region_name: str, focus_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        지역 상세 페이지에서 사용할 전체 데이터를 한번에 구성해 반환한다.

        반환 형식:
        {
          "region_name": "강남구",
          "focus_year": 2023,
          "available_years": [2010, ..., 2023],
          "risk_level": "medium" | "low" | "high" | None,
          "risk_level_display": "보통",
          "risk_level_class": "medium",
          "risk_score": 12345.0,
          "prediction": {...},  # PredictionService.predict(...) 결과
          "region_detail_data": {
             "region": "강남구",
             "focus_year": 2023,
             "timeline": [...],
             "prediction": {...},
             "radar": {
                "labels": [...],
                "region_values": [...],
                "seoul_avg_values": [...],
             }
          }
        }
        """

        # 1) 사용 가능한 연도 목록
        available_years = self._get_available_years(region_name)
        available_years_sorted = sorted(available_years) if available_years else []

        default_year: Optional[int] = (
            available_years_sorted[-1] if available_years_sorted else None
        )
        year = focus_year or default_year

        prediction: Optional[Dict[str, Any]] = None
        timeline: List[Dict[str, Any]] = []
        risk_score: Optional[float] = None
        risk_level: Optional[str] = None

        if year is not None:
            # 2) 예측 + 히스토리
            prediction = self.prediction_service.predict(region_name, year)
            if prediction:
                timeline = self._build_timeline_from_prediction(prediction)
                risk_score = float(prediction.get("prediction") or 0.0)
                risk_level = self._compute_risk_level(region_name, year, risk_score)

        # 3) 레이더 차트 데이터
        if year is not None:
            radar_data = self._get_radar_data(region_name, year)
        else:
            radar_data = {
                "labels": [label for _field, label in RADAR_METRICS],
                "region_values": [0.0 for _ in RADAR_METRICS],
                "seoul_avg_values": [0.0 for _ in RADAR_METRICS],
            }

        # 4) UI 표시용 매핑
        risk_level_display_map = {
            "low": "낮음",
            "medium": "보통",
            "high": "높음",
            None: "정보 부족",
        }
        risk_level_display = risk_level_display_map.get(risk_level, "정보 부족")
        risk_level_class = risk_level or "none"

        region_detail_data = {
            "region": region_name,
            "focus_year": year,
            "timeline": timeline,
            "prediction": prediction or {},
            "radar": radar_data,
        }

        return {
            "region_name": region_name,
            "focus_year": year,
            "available_years": available_years_sorted,
            "risk_level": risk_level,
            "risk_level_display": risk_level_display,
            "risk_level_class": risk_level_class,
            "risk_score": risk_score,
            "prediction": prediction,
            "region_detail_data": region_detail_data,
        }

    # -----------------------------
    # 내부 헬퍼
    # -----------------------------
    def _get_available_years(self, region_name: str) -> List[int]:
        """
        ELDERLY_STATS 기준으로, 해당 구의 데이터가 존재하는 연도 목록을 반환.
        """
        # Repository를 통한 데이터 접근
        return self.elderly_stats_repo.get_available_years(region_name)

    def _build_timeline_from_prediction(
        self, prediction: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        PredictionService.predict(...) 의 history + 예측 포인트를
        타임라인 차트에서 사용하기 좋은 형태로 변환.
        """
        items: List[Dict[str, Any]] = []

        history = prediction.get("history") or []
        for h in sorted(history, key=lambda x: x["year"]):
            items.append(
                {
                    "year": int(h["year"]),
                    "value": float(h.get("elderly_population") or 0.0),
                    "type": "actual",
                }
            )

        # 예측 포인트 추가
        try:
            pred_year = int(prediction.get("year"))
            pred_value = float(prediction.get("prediction"))
        except (TypeError, ValueError):
            pred_year = None
            pred_value = None

        if pred_year is not None and pred_value is not None:
            items.append(
                {
                    "year": pred_year,
                    "value": pred_value,
                    "type": "forecast",
                }
            )

        return items

    def _compute_risk_level(
        self, region_name: str, year: int, risk_score: float
    ) -> Optional[str]:
        """
        같은 연도 내 다른 구들의 예측 분포를 기준으로
        해당 구의 리스크 레벨을 low / medium / high 로 분류.
        """
        try:
            prediction_map = self.prediction_service.ensure_predictions_for_year(year)
        except Exception as e:  # 방어용
            logger.warning(
                "[RegionRiskService] ensure_predictions_for_year 실패: %s", e
            )
            return None

        values = [float(v) for v in prediction_map.values() if v is not None]
        if not values:
            return None

        vmin = min(values)
        vmax = max(values)
        vrange = vmax - vmin or 1.0

        low_thr = vmin + vrange * (1.0 / 3.0)
        high_thr = vmin + vrange * (2.0 / 3.0)

        if risk_score <= low_thr:
            return "low"
        elif risk_score <= high_thr:
            return "medium"
        else:
            return "high"

    def _get_radar_data(self, region_name: str, year: int) -> Dict[str, Any]:
        """
        레이더 차트용 데이터 구성:
        - labels: 축 이름
        - region_values: 해당 구의 값
        - seoul_avg_values: 같은 연도 전체 구 평균 값
        """
        metric_fields = [field for field, _label in RADAR_METRICS]
        labels = [label for _field, label in RADAR_METRICS]

        # (1) 해당 구 + 연도 값 (Repository를 통한 데이터 접근)
        region_stats = self.elderly_stats_repo.get_stats_by_region_year(
            region_name, year
        )

        if region_stats is not None:
            region_values = [
                float(getattr(region_stats, field, 0.0) or 0.0)
                for field in metric_fields
            ]
        else:
            region_values = [0.0 for _ in metric_fields]

        # (2) 같은 연도 전체 구 평균 (Repository를 통한 데이터 접근)
        avg_row = self.elderly_stats_repo.get_avg_metrics(year, metric_fields)

        if avg_row is not None:
            seoul_avg_values = [float(v or 0.0) for v in avg_row]
        else:
            seoul_avg_values = [0.0 for _ in metric_fields]

        return {
            "labels": labels,
            "region_values": region_values,
            "seoul_avg_values": seoul_avg_values,
        }
