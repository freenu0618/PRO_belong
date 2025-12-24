import os
import pandas as pd
import numpy as np
from belong.app import create_app
from belong.extensions import db
from belong.models.region import Region
from belong.models.elderly_history import ElderlyHistory
from belong.models.prediction_result import PredictionResult
from belong.models.user import User # Register User model for create_all()

def seed_data():
    app = create_app()
    with app.app_context():
        # 1. DB 테이블 생성 (SQLite 파일이 없으면 생성됨)
        print(f"🔌 Connecting to Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Unknown')}")
        try:
            db.create_all()
            print("✅ Database tables checked/created.")
        except Exception as e:
            print(f"⚠️ ensure_tables warning (could be pre-existing): {e}")

        # 2. CSV 파일 경로 설정
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "belong", "ml", "dataset", "raw_data")
        
        elderly_csv = os.path.join(data_dir, "elderly_person_value.csv")

        # Check if data already seeded
        existing_count = ElderlyHistory.query.count()
        if existing_count > 0:
            print(f"ℹ️ Database already has {existing_count} records. Skipping history seed.")
        else:
            if not os.path.exists(elderly_csv):
                print(f"⚠️ Warning: {elderly_csv} not found. Skipping seeding.")
                return

            # 3. 데이터 로드
            print(f"📂 Loading data from {elderly_csv}...")
            df_elderly = pd.read_csv(elderly_csv)
            
            # Region 캐싱 (DB 조회 최소화)
            regions = {r.name: r for r in Region.query.all()}

            # 4. 데이터 적재 (Upsert Logic)
            count = 0
            for _, row in df_elderly.iterrows():
                region_name = row['region']
                year = int(row['year'])
                val = int(row['elderly_population'])

                # A. Region 확인 및 생성
                if region_name not in regions:
                    new_region = Region(name=region_name)
                    db.session.add(new_region)
                    db.session.flush()
                    regions[region_name] = new_region
                    print(f"   Created Region: {region_name}")

                region = regions[region_name]

                # B. History 확인 및 생성/수정
                history = ElderlyHistory.query.filter_by(
                    region_id=region.id, 
                    year=year, 
                    is_forecast='N'
                ).first()

                if not history:
                    history = ElderlyHistory(
                        region_id=region.id,
                        year=year,
                        elderly_population=val,
                        is_forecast='N'
                    )
                    db.session.add(history)
                    count += 1

            db.session.commit()
            print(f"✅ History Seeding Complete! {count} records added.")

        # ========================================
        # 5. 예측 데이터 생성 (PREDICTION_RESULT + ELDERLY_HISTORY)
        # ========================================
        pred_count = PredictionResult.query.count()
        elderly_forecast_count = ElderlyHistory.query.filter_by(is_forecast='Y').count()
        
        if pred_count > 0 and elderly_forecast_count > 0:
            print(f"ℹ️ Forecast data already exists. Skipping forecast seed.")
        else:
            print("📊 Generating forecast data (2024-2028)...")
            generate_forecast_data()
        
        print("✅ Seeding Complete!")


def generate_forecast_data():
    """
    ElderlyHistory 데이터를 기반으로 간단한 선형 회귀 예측을 생성하여
    1) PREDICTION_RESULT 테이블 (고독사 예측용)
    2) ELDERLY_HISTORY 테이블 is_forecast='Y' (독거노인 예측용)
    양쪽에 저장.
    """
    from sklearn.linear_model import LinearRegression
    
    FORECAST_YEARS = [2024, 2025, 2026, 2027, 2028]
    
    # 각 구별로 예측
    regions = Region.query.all()
    pred_result_count = 0
    elderly_forecast_count = 0
    
    for region in regions:
        # 해당 구의 실측 데이터 가져오기
        history = (
            ElderlyHistory.query
            .filter_by(region_id=region.id, is_forecast='N')
            .order_by(ElderlyHistory.year)
            .all()
        )
        
        if len(history) < 2:
            print(f"   ⚠️ {region.name}: 데이터 부족 (skip)")
            continue
        
        # 선형 회귀 학습
        X = np.array([[h.year] for h in history])
        y = np.array([h.elderly_population for h in history])
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 미래 연도 예측
        for year in FORECAST_YEARS:
            pred_value = max(0, model.predict([[year]])[0])  # 음수 방지
            
            # 1. PREDICTION_RESULT에 저장 (고독사 5년 예측용)
            existing_pred = PredictionResult.query.filter_by(
                region_name=region.name,
                year=year
            ).first()
            
            if not existing_pred:
                pred = PredictionResult(
                    region_name=region.name,
                    year=year,
                    prediction_value=float(pred_value),
                    source="linear_regression"
                )
                db.session.add(pred)
                pred_result_count += 1
            
            # 2. ELDERLY_HISTORY에 저장 (독거노인 5년 예측용)
            existing_elderly = ElderlyHistory.query.filter_by(
                region_id=region.id,
                year=year,
                is_forecast='Y'
            ).first()
            
            if not existing_elderly:
                elderly_pred = ElderlyHistory(
                    region_id=region.id,
                    year=year,
                    elderly_population=int(pred_value),
                    is_forecast='Y'
                )
                db.session.add(elderly_pred)
                elderly_forecast_count += 1
    
    db.session.commit()
    print(f"✅ Forecast Seeding Complete!")
    print(f"   - PREDICTION_RESULT: {pred_result_count} records")
    print(f"   - ELDERLY_HISTORY (forecast): {elderly_forecast_count} records")


if __name__ == "__main__":
    seed_data()


