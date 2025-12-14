from belong.app import create_app
from belong.extensions import db
from belong.models.prediction_result import PredictionResult

app = create_app()
with app.app_context():
    print("--- Checking PredictionResult for '강남구' (year > 2023) ---")
    rows = (
        db.session.query(PredictionResult)
        .filter(PredictionResult.region_name == '강남구')
        .filter(PredictionResult.year > 2023)
        .order_by(PredictionResult.year)
        .all()
    )
    
    if not rows:
        print("No rows found for 강남구 > 2023")
    else:
        for r in rows:
            print(f"Year: {r.year}, Value: {r.prediction_value}, Source: {r.source}")

    print("\n--- Checking Distinct Sources ---")
    sources = db.session.query(PredictionResult.source).distinct().all()
    print("Sources in DB:", sources)
