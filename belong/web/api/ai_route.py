# belong/web/api/ai_route.py
from flask import request, g
from . import api_bp
from .jwt_utils import jwt_required

# 너 프로젝트에서 이미 쓰고 있는 서비스들(존재한다고 가정)
from belong.services.ai_service import AIService


def _parse_request():
    payload = request.get_json() or {}
    text = payload.get("text")
    # options 안에 model, temperature 등이 들어있음
    options = payload.get("options") or {}
    
    # 모델 ID 추출 (별도 필드로 올 수도 있고 options 안에 있을 수도 있음 - 여기선 options 우선)
    model = payload.get("model") or options.get("model")
    
    if not text:
        return None, None, None, {"ok": False, "result": {"error": "text가 필요합니다."}}
    return text, model, options, None


def _make_ai_response(service, text, result, debug=None):
    return {
        "ok": True,
        "service": service,
        "input": text,
        "result": result,
        "debug": debug or {},
    }


def get_ai_service():
    """Flask application context 내에서 AIService 가져오기"""
    if not hasattr(g, 'ai_service'):
        g.ai_service = AIService()
    return g.ai_service


# ---------------------------------------------------
# [NEW] General Chat Endpoint
# ---------------------------------------------------
@api_bp.post("/ai/chat")
@jwt_required
def api_ai_chat():
    text, model, options, err = _parse_request()
    if err:
        return err, 400
    
    # general chat service call
    ai_service = get_ai_service()
    result = ai_service.chat(text, model=model, options=options)
    return _make_ai_response("chat", text, result), 200


@api_bp.post("/ai/sentiment")
@jwt_required
def api_ai_sentiment():
    text, model, options, err = _parse_request()
    if err:
        return err, 400
    
    ai_service = get_ai_service()
    result = ai_service.analyze_sentiment(text, model=model)
    return _make_ai_response("sentiment", text, result), 200


@api_bp.post("/ai/entities")
@jwt_required
def api_ai_entities():
    text, model, options, err = _parse_request()
    if err:
        return err, 400
    
    ai_service = get_ai_service()
    result = ai_service.analyze_entities(text, model=model)
    return _make_ai_response("entities", text, result), 200


@api_bp.post("/ai/qa")
@jwt_required
def api_ai_qa():
    text, model, options, err = _parse_request()
    if err:
        return err, 400

    context = options.get("context")
    use_rag = options.get("use_rag", False)
    
    # RAG를 안 쓰는데 Context도 없으면 에러
    if not use_rag and not context:
        return {"ok": False, "result": {"error": "qa는 options.context(지문)가 필요합니다. (또는 use_rag 옵션 사용)"}}, 400

    ai_service = get_ai_service()
    result = ai_service.answer_question(question=text, context=context, model=model, use_rag=use_rag)
    return _make_ai_response("qa", text, result), 200


@api_bp.post("/ai/summary")
@jwt_required
def api_ai_summary():
    text, model, options, err = _parse_request()
    if err:
        return err, 400

    ai_service = get_ai_service()
    result = ai_service.summarize(text, model=model)
    return _make_ai_response("summary", text, result), 200


@api_bp.post("/ai/translate")
@jwt_required
def api_ai_translate():
    text, model, options, err = _parse_request()
    if err:
        return err, 400

    direction = options.get("direction", "ko-en")
    ai_service = get_ai_service()
    result = ai_service.translate(text, direction=direction, model=model)
    return _make_ai_response("translate", text, result), 200


@api_bp.post("/ai/rerank")
@jwt_required
def api_ai_rerank():
    """RAG 문서 재순위 API
    
    Request:
        {"query": "검색어", "documents": ["doc1", "doc2", ...]}
    
    Response:
        {"ok": true, "ranked_documents": [{"text": "...", "score": 0.95}, ...]}
    """
    payload = request.get_json() or {}
    query = payload.get("query")
    documents = payload.get("documents", [])
    
    if not query:
        return {"ok": False, "result": {"error": "query가 필요합니다."}}, 400
    if not documents or not isinstance(documents, list):
        return {"ok": False, "result": {"error": "documents 리스트가 필요합니다."}}, 400
    
    ai_service = get_ai_service()
    result = ai_service.rerank(query=query, documents=documents)
    return {"ok": True, "service": "rerank", "result": result}, 200


@api_bp.post("/ai/text-gen")
@jwt_required
def api_ai_text_gen():
    """AI 텍스트 생성 API (메모리 기능 포함)
    
    Request:
        {
            "prompt": "내 이름은 이영욱이야",
            "use_memory": true,      # 이전 대화 컨텍스트 사용
            "save_to_memory": true   # 대화를 메모리에 저장
        }
    
    Response:
        {"ok": true, "result": {"raw_output": "...", "context_used": "..."}}
    """
    from flask import g
    from belong.extensions import logger
    
    payload = request.get_json() or {}
    prompt = payload.get("prompt")
    use_memory = payload.get("use_memory", True)
    save_to_memory = payload.get("save_to_memory", True)
    
    if not prompt:
        return {"ok": False, "result": {"error": "prompt가 필요합니다."}}, 400
    
    # JWT에서 user_id 가져오기 (sub 필드)
    jwt_payload = getattr(g, 'jwt_payload', {})
    user_id = jwt_payload.get('sub')
    
    logger.info(f"🧠 Text-gen request: user_id={user_id}, use_memory={use_memory}")
    
    ai_service = get_ai_service()
    result = ai_service.generate_text(
        prompt=prompt,
        user_id=user_id,
        use_memory=use_memory,
        save_to_memory=save_to_memory
    )
    return {"ok": True, "service": "text_gen", "result": result}, 200


@api_bp.post("/ai/clear-memory")
@jwt_required
def api_ai_clear_memory():
    """대화 메모리 초기화 API"""
    from flask import g
    
    jwt_payload = getattr(g, 'jwt_payload', {})
    user_id = jwt_payload.get('sub')
    if not user_id:
        return {"ok": False, "error": "로그인이 필요합니다."}, 401
    
    ai_service = get_ai_service()
    result = ai_service.clear_memory(user_id)
    return {"ok": True, "result": result}, 200


@api_bp.get("/ai/utility-models")
def api_utility_models():
    """사용 가능한 유틸리티 모델 목록 조회"""
    ai_service = get_ai_service()
    models = ai_service.get_utility_models()
    return {"ok": True, "models": models}, 200

