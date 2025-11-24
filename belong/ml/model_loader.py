import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "forecast_model.pkl")

_model = None

def load_model():
    global _model
    if _model is None:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model
