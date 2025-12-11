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

# 미니1: 감정 분석
# POST /api/ai/sentiment
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

# 미니2: 개체(객체) 분석
# POST /api/ai/entities
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

# 미니3: 질의응답
# POST /api/ai/qa
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

# 미니4: 텍스트 요약
# POST /api/ai/summary
@api_bp.post("/ai/summary")
def api_ai_summary():
    """
    텍스트 요약 API
    Body:
      {
        "text": "...",
        "options": {
          "max_length": 64,
          "min_length": 16
        }
      }
    """
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="summary",
            input_text=text,
            result={"error": "text(요약할 텍스트)는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    max_length = int(options.get("max_length", 64))
    min_length = int(options.get("min_length", 16))

    result = ai_service.summarize(
        text=text,
        max_length=max_length,
        min_length=min_length,
    )

    return _make_ai_response(
        service="summary",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200

# 미니5: 번역
# POST /api/ai/translate
@api_bp.post("/ai/translate")
def api_ai_translate():
    """
    번역 API
    Body:
      {
        "text": "...",
        "options": {
          "direction": "ko-en" or "en-ko"
        }
      }
    """
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="translate",
            input_text=text,
            result={"error": "text(번역할 텍스트)는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    direction = (options.get("direction") or "ko-en").strip()

    result = ai_service.translate(
        text=text,
        direction=direction,
    )

    return _make_ai_response(
        service="translate",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200
