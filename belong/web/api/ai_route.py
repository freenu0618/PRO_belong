from flask import jsonify, request
from . import api_bp

from belong.services.ai_service import AIService

ai_service = AIService()


def _parse_request():
    """
    공통 Request 포맷

    {
      "text": "분석할 텍스트 or 질문",
      "options": { ... }
    }
    """
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    options = data.get("options") or {}
    return text, options


def _make_ai_response(service: str, input_text: str, result: dict,
                      ok: bool = True, mode: str = "mock"):
    """
    공통 Response 포맷

    {
      "ok": true,
      "service": "sentiment",
      "input": { "text": "..." },
      "result": { ... },
      "debug": { "mode": "mock" }
    }
    """
    return jsonify(
        {
            "ok": ok,
            "service": service,
            "input": {"text": input_text},
            "result": result,
            "debug": {"mode": mode},
        }
    )


# ===========================
# 미니1: 감정 분석
# POST /api/ai/sentiment
# ===========================
@api_bp.post("/ai/sentiment")
def api_ai_sentiment():
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="sentiment",
            input_text=text,
            result={"error": "text 필드는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    result = ai_service.analyze_sentiment(text)
    return _make_ai_response(
        service="sentiment",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200


# ===========================
# 미니2: 개체(객체) 분석
# POST /api/ai/entities
# ===========================
@api_bp.post("/ai/entities")
def api_ai_entities():
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="entities",
            input_text=text,
            result={"error": "text 필드는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    result = ai_service.analyze_entities(text)
    return _make_ai_response(
        service="entities",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200


# ===========================
# 미니3: 질의응답
# POST /api/ai/qa
# ===========================
@api_bp.post("/ai/qa")
def api_ai_qa():
    question, options = _parse_request()
    context = (options.get("context") or "").strip()

    if not question or not context:
        return _make_ai_response(
            service="qa",
            input_text=question,
            result={
                "error": "text(질문)와 options.context(지문)는 모두 필수입니다."
            },
            ok=False,
            mode="mock",
        ), 400

    result = ai_service.answer_question(question=question, context=context)
    return _make_ai_response(
        service="qa",
        input_text=question,
        result=result,
        ok=True,
        mode="mock",
    ), 200
