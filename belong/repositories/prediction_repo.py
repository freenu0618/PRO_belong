from typing import List, Dict
from sqlalchemy import func
from belong.extensions import db
from belong.models.prediction_result import PredictionResult


class PredictionRepository:
    """
    PREDICTION_RESULT 테이블 접근용 레포지토리.

    기존 기능:
    - save_predictions(data, source)
    - get_predictions(region, start_year, end_year, source)

    추가 구현:
    - save(region, year, prediction_value, source)
    - list_by_region(region)
    """

    # ----------------------------------------
    # 1) 단일 저장 (서비스 predict_and_store 에서 사용)
    # ----------------------------------------
    def save(self, region: str, year: int, value: float, source: str) -> None:
        """
        단일 예측값 저장.

        (region, year) 기준으로:
          - 기존 row가 있으면 모두 삭제
          - 새 row 1개를 삽입

        DB 제약: (region_name, year)에 유니크 인덱스가 있는 상황을 가정.
        """

        # ✅ 기존 값 삭제: source 상관없이 (region, year) 기준으로 삭제
        db.session.query(PredictionResult).filter_by(
            region_name=region,
            year=year,
        ).delete()

        # 새 값 삽입
        new_row = PredictionResult(
            region_name=region,
            year=year,
            prediction_value=value,
            source=source,
        )
        db.session.add(new_row)
        db.session.commit()


    # ----------------------------------------
    # 2) 이력 조회 (API: /api/predictions/history/<region>)
    # ----------------------------------------
    def list_by_region(self, region: str) -> List[PredictionResult]:
        """
        특정 지역(region)의 모든 예측 이력을 반환.
        최신순 or 과거순? → API에서 정렬 원하지 않으므로 여기서는 연도순 정렬.
        """
        rows = (
            db.session.query(PredictionResult)
            .filter(PredictionResult.region_name == region)
            .order_by(PredictionResult.year.asc())
            .all()
        )
        return rows

    # ----------------------------------------
    # 기존 다중 조회 로직
    # ----------------------------------------
    def get_predictions(
        self, region: str, start_year: int, end_year: int, source: str
    ) -> List[Dict]:

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
