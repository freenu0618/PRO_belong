from flask import request
from . import api_bp
from .jwt_utils import jwt_required
from belong.services.ai_service import AIService
import os

# Initialize AIService (Uses RunPod Config)
ai_service = AIService()

@api_bp.post("/tuning/chat")
@jwt_required
def api_tuning_chat():
    payload = request.get_json() or {}
    messages = payload.get("messages", [])
    model = payload.get("model", "constant-100")
    options = payload.get("options", {})
    
    # Extract last user message for simple prompt (Adapter adaptation)
    user_text = ""
    if messages:
        # Find last user message
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_text = msg.get("content", "")
                break
    
    if not user_text and "text" in payload:
        user_text = payload["text"]

    # Use AIService (RunPod) instead of OllamaService
    result = ai_service.chat(user_text, model=model, options=options)
    
    # Adapt response to frontend expectation
    if "response" in result:
        return {
            "ok": True, 
            "result": result['response'], # Frontend expects raw text here usually or message object? 
            # Looking at original code: result['message']['content'] or result['response']
            # Let's return structure compatible with what frontend likely expects from this route
            # If original was ollama chat, it returned 'result' as text or message object.
            # Let's infer based on "result: result['response']" in legacy fallback
            # We will return the text directly in 'result' key as expected by many simple UIs
        }, 200
        
    return {"ok": False, "message": "Failed to generate response"}, 500


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
        
    # Use AIService (RunPod)
    # Reusing chat or creating a generation method? chat is fine for now.
    result = ai_service.chat(text, model=model, options=options)
    
    if "response" in result:
        return {"ok": True, "result": result["response"]}, 200

    return {"ok": False, "message": "Unknown response"}, 500
