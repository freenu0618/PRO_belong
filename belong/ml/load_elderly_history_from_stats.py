

from belong.app import create_app
from belong.extensions import db
from belong.models.feature_stats import ElderlyStats
from belong.models.elderly_history import ElderlyHistory


def load_elderly_history_from_stats(start_year: int = 2017, end_year: int = 2023) -> None:
    """
    ELDERLY_STATS 테이블에서 실측 노인 인구를 읽어
    ELDERLY_HISTORY 테이블에 is_forecast='N'으로 적재/업데이트한다.
    """
    app = create_app()

    with app.app_context():
        # 1) ELDERLY_STATS 에서 필요한 컬럼만 조회
        query = (
            db.session.query(
                ElderlyStats.region_id.label("region_id"),
                ElderlyStats.year.label("year"),
                ElderlyStats.elderly_population.label("elderly_population"),
                ElderlyStats.alone_household_count.label("alone_household_count"),
            )
            .filter(ElderlyStats.year.between(start_year, end_year))
            .order_by(ElderlyStats.region_id, ElderlyStats.year)
        )

        rows = query.all()
        print(f"[ELD_HIST] 적재 대상 행 수: {len(rows)}")

        inserted = 0
        updated = 0

        for row in rows:
            region_id = int(row.region_id)
            year = int(row.year)

            # 2) (region_id, year, is_forecast='N') 기준으로 upsert
            history = (
                ElderlyHistory.query
                .filter_by(
                    region_id=region_id,
                    year=year,
                    is_forecast="N",
                )
                .one_or_none()
            )

            if history is None:
                history = ElderlyHistory(
                    region_id=region_id,
                    year=year,
                    is_forecast="N",
                )
                db.session.add(history)
                inserted += 1
            else:
                updated += 1

            # 3) 값 매핑
            history.elderly_population = int(row.elderly_population) if row.elderly_population is not None else None

            # 현재 ELDERLY_STATS 에는 독거노인 인구 컬럼이 따로 없어서
            # 일단 alone_household_count(1인가구수)를 임시로 넣어두는 구조
            history.alone_elderly_population = (
                int(row.alone_household_count) if row.alone_household_count is not None else None
            )

        db.session.commit()
        print(f"[ELD_HIST] INSERT={inserted}, UPDATE={updated}")
        print("[ELD_HIST] ELDERLY_HISTORY 실측 적재 완료")


def main():
    load_elderly_history_from_stats(start_year=2017, end_year=2023)


if __name__ == "__main__":
    main()
