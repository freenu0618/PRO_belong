from flask import request
from . import api_bp
from .jwt_utils import jwt_required
from belong.services.ollama_service import OllamaService
import os

# Initialize with environment variable flexibility (Docker support)
ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
ollama_service = OllamaService(ollama_url=ollama_url)

@api_bp.post("/tuning/chat")
@jwt_required
def api_tuning_chat():
    payload = request.get_json() or {}
    messages = payload.get("messages", [])
    model = payload.get("model", "llama3-8b-base-q4")
    options = payload.get("options", {})
    
    # If explicit text is sent instead of messages list (shim)
    if "text" in payload and not messages:
        messages = [{"role": "user", "content": payload["text"]}]

    result = ollama_service.chat(messages, model, options)
    
    # Standardize response structure
    if "message" in result: # Ollama format: result['message']['content']
        return {
            "ok": True, 
            "result": result['message']['content'],
            "raw": result
        }, 200
    
    if "response" in result: # Legacy generate format fallback
         return {"ok": True, "result": result['response']}, 200

    if "error" in result:
        return {"ok": False, "message": result['error']}, 500
        
    return {"ok": False, "message": "Unknown response from Ollama"}, 500


@api_bp.post("/tuning/compare")
@jwt_required
def api_tuning_compare():
    """
    Compare requires prompt and model.
    """
    payload = request.get_json() or {}
    text = payload.get("text")
    model = payload.get("model")
    options = payload.get("options", {})
    
    if not text or not model:
        return {"ok": False, "message": "Text and Model are required"}, 400
        
    # Use generate for simple comparison (faster/simpler than chat history)
    result = ollama_service.generate(text, model, options)
    
    if "response" in result:
        return {"ok": True, "result": result["response"]}, 200
    if "error" in result:
        return {"ok": False, "message": result["error"]}, 500

    return {"ok": False, "message": "Unknown response"}, 500
