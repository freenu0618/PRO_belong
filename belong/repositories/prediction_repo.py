from typing import Optional, List
from belong.extensions import db
from belong.models.prediction_result import PredictionResult


class PredictionRepository:
    def save(self, region: str, year: int, value: float, source: str) -> PredictionResult:
        existing = self.get(region, year)
        if existing:
            existing.prediction_value = value
            existing.source = source
            db.session.commit()
            return existing

        obj = PredictionResult(
            region_name=region,
            year=year,
            prediction_value=value,
            source=source,
        )
        db.session.add(obj)
        db.session.commit()
        return obj

    def get(self, region: str, year: int) -> Optional[PredictionResult]:
        return PredictionResult.query.filter_by(region_name=region, year=year).one_or_none()

    def list_by_region(self, region: str) -> List[PredictionResult]:
        return PredictionResult.query.filter_by(region_name=region).order_by(PredictionResult.year).all()
