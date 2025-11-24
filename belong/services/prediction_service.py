from belong.ml.model_loader import load_model

class PredictionService:

    def predict(self, region: str):
        model = load_model()

        # TODO: 여기에 region 기반 데이터 전처리 추가
        # 지금은 테스트라 단일 입력 샘플 예시
        sample_input = [[1, 0, 0, 0]]  # 가짜 샘플 → 나중에 실제 데이터 구조로 교체

        prediction = model.predict(sample_input)

        return {
            "region": region,
            "forecast": float(prediction[0])
        }
