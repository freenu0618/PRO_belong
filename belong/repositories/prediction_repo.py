from typing import List, Dict, Optional
from sqlalchemy import func

from belong.extensions import db
from belong.models.prediction_result import PredictionResult


class PredictionRepository:
    """
    PREDICTION_RESULT 테이블 접근용 레포지토리.

    - save_predictions(data, source)
    - get_predictions(region, start_year, end_year, source)
    """

    def save_predictions(self, data: List[Dict], source: str) -> None:
        """
        예측 결과를 일괄 저장.
        기존 source + region + year 일치 데이터는 삭제 후 새로 삽입.
        """
        for row in data:
            region = row.get("region")
            year = row.get("year")
            value = row.get("value")

            # 기존 동일 레코드 삭제
            db.session.query(PredictionResult).filter_by(
                region_name=region, year=year, source=source
            ).delete()

            db.session.add(
                PredictionResult(
                    region_name=region,
                    year=year,
                    prediction_value=value,
                    source=source,
                )
            )

        db.session.commit()

    def get_predictions(
        self, region: str, start_year: int, end_year: int, source: str
    ) -> List[Dict]:
        """
        특정 구(region) + source 기준으로 예측 결과 조회.

        반환 형식:
        [
            {"year": 2024, "value": 12000},
            {"year": 2025, "value": 12200},
        ]
        """
        rows = (
            db.session.query(
                PredictionResult.year.label("year"),
                func.sum(PredictionResult.prediction_value).label("value"),
            )
            .filter(
                PredictionResult.region_name == region,
                PredictionResult.source == source,
                PredictionResult.year >= start_year,
                PredictionResult.year <= end_year,
            )
            .group_by(PredictionResult.year)
            .order_by(PredictionResult.year)
            .all()
        )

        return [{"year": int(r.year), "value": int(r.value or 0)} for r in rows]
