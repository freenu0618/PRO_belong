# belong/web/api/ai_route.py
from flask import request
from . import api_bp
from .jwt_utils import jwt_required

# 너 프로젝트에서 이미 쓰고 있는 서비스들(존재한다고 가정)
from belong.services.ai_service import AIService


def _parse_request():
    payload = request.get_json() or {}
    text = payload.get("text")
    options = payload.get("options") or {}
    if not text:
        return None, None, {"ok": False, "result": {"error": "text가 필요합니다."}}
    return text, options, None


def _make_ai_response(service, text, result, debug=None):
    return {
        "ok": True,
        "service": service,
        "input": text,
        "result": result,
        "debug": debug or {},
    }


# Service Instantiation
ai_service = AIService()


@api_bp.post("/ai/sentiment")
@jwt_required
def api_ai_sentiment():
    text, options, err = _parse_request()
    if err:
        return err, 400
    # methods are instance methods now
    result = ai_service.analyze_sentiment(text)
    return _make_ai_response("sentiment", text, result), 200


@api_bp.post("/ai/entities")
@jwt_required
def api_ai_entities():
    text, options, err = _parse_request()
    if err:
        return err, 400
    # extract_entities -> analyze_entities
    result = ai_service.analyze_entities(text)
    return _make_ai_response("entities", text, result), 200


@api_bp.post("/ai/qa")
@jwt_required
def api_ai_qa():
    text, options, err = _parse_request()
    if err:
        return err, 400

    context = options.get("context")
    if not context:
        return {"ok": False, "result": {"error": "qa는 options.context(지문)가 필요합니다."}}, 400

    result = ai_service.answer_question(question=text, context=context)
    return _make_ai_response("qa", text, result), 200


@api_bp.post("/ai/summary")
@jwt_required
def api_ai_summary():
    text, options, err = _parse_request()
    if err:
        return err, 400
    # summarize_text -> summarize
    result = ai_service.summarize(text)
    return _make_ai_response("summary", text, result), 200


@api_bp.post("/ai/translate")
@jwt_required
def api_ai_translate():
    text, options, err = _parse_request()
    if err:
        return err, 400

    direction = options.get("direction", "ko-en")
    # translate_text -> translate
    result = ai_service.translate(text, direction=direction)
    return _make_ai_response("translate", text, result), 200
