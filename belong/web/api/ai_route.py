from flask import jsonify, request
from . import api_bp

from belong.services.ai_service import AIService
from belong.services.chat_service import ChatService
ai_service = AIService()
chat_service = ChatService()

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

# ===========================
# 챗봇: 프롬프트 + DB 저장 + 히스토리
# ===========================

@api_bp.post("/chat/ask")
def api_chat_ask():
    """
    body 예시:
    {
      "user_id": 1,
      "service": "qa",            # "sentiment" / "entities" / "qa"
      "text": "내 이름은 상엽이야",
      "options": {}               # qa일 때 context 직접 넘기고 싶으면 여기
    }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    service = (data.get("service") or "qa").strip()
    text = (data.get("text") or "").strip()
    options = data.get("options") or {}

    if not user_id or not text:
        return jsonify(
            {
                "ok": False,
                "service": service,
                "input": {"text": text},
                "result": {"error": "user_id와 text는 필수입니다."},
                "debug": {"mode": "mock"},
            }
        ), 400

    resp = chat_service.process(
        user_id=int(user_id),
        service=service,
        text=text,
        options=options,
    )
    return jsonify(resp), 200


@api_bp.get("/chat/history/<int:user_id>")
def api_chat_history(user_id: int):
    """
    특정 user_id의 최근 대화 히스토리 조회
    """
    resp = chat_service.get_history(user_id=user_id, limit=20)
    return jsonify(resp), 200
