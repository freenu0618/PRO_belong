import sys
import os
print("Python executable:", sys.executable)
print("CWD:", os.getcwd())
print("sys.path:", sys.path)

try:
    from belong.ml.model_loader import load_model
    print("✅ Import load_model success")
    model = load_model()
    print("✅ Model loaded successfully. Type:", type(model))
    if isinstance(model, dict):
        print("Keys sample:", list(model.keys())[:3])
    else:
        print("Model content:", model)
except Exception as e:
    print("❌ Import/Load load_model failed:", e)

try:
    from belong.services.prediction_service import PredictionService
    print("✅ Import PredictionService success")
except Exception as e:
    print("❌ Import PredictionService failed:", e)

try:
    from belong.app import create_app
    print("✅ Import create_app success")
    app = create_app()
    print("✅ create_app() execution success")
except Exception as e:
    print("❌ Import/Run create_app failed:", e)
    import traceback
    traceback.print_exc()
