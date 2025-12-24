from flask import request
from . import api_bp
from .jwt_utils import jwt_required
from belong.services.ai_service import AIService
from .response_utils import success_response, bad_request, server_error
import os

# Initialize AIService (Uses RunPod Config)
ai_service = AIService()

@api_bp.post("/tuning/chat")
@jwt_required
def api_tuning_chat():
    payload = request.get_json() or {}
    messages = payload.get("messages", [])
    model = payload.get("model", "lora_best_r32")  # 기본값: lora_best_r32
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

    if not user_text:
        return bad_request("텍스트를 입력해주세요")

    # Use AIService (RunPod) instead of OllamaService
    result = ai_service.chat(user_text, model=model, options=options)
    
    # Adapt response to frontend expectation
    if "response" in result:
        return success_response(
            data={"result": result['response']},
            message="AI 응답 생성 완료"
        )
        
    return server_error("응답 생성에 실패했습니다")


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
        return bad_request("텍스트와 모델이 필요합니다")
        
    # Use AIService (RunPod)
    result = ai_service.chat(text, model=model, options=options)
    
    if "response" in result:
        return success_response(
            data={"result": result["response"]},
            message="비교 응답 생성 완료"
        )

    return server_error("응답 생성에 실패했습니다")


@api_bp.route("/tuning/models", methods=["GET"])
def api_tuning_models():
    """사용 가능한 모델 리스트 반환"""
    models = ai_service.get_available_models()
    return success_response(
        data={"models": models},
        message="모델 목록 조회 성공"
    )


@api_bp.route("/tuning/start", methods=["POST"])
@jwt_required
def api_tuning_start():
    """학습 시작 (파라미터 + 모델명 처리)"""
    payload = request.get_json() or {}
    model_name = payload.get("model_name")
    
    if not model_name:
        return bad_request("모델 이름이 필요합니다")
        
    # Start Training
    result = ai_service.start_training(model_name, payload)
    return success_response(
        data=result,
        message="학습이 시작되었습니다"
    )


@api_bp.route("/tuning/status/<job_id>", methods=["GET"])
@jwt_required
def api_tuning_status(job_id):
    """학습 상태 조회 (Mock or Real)"""
    result = ai_service.get_training_status(job_id)
    return success_response(
        data=result,
        message="학습 상태 조회 성공"
    )


@api_bp.route("/tuning/models/<model_name>", methods=["DELETE"])
@jwt_required
def api_delete_model(model_name):
    """파인튜닝 모델 삭제"""
    result = ai_service.delete_model(model_name)
    if result.get("ok"):
        return success_response(
            data=result,
            message=result.get("message", "모델 삭제 완료")
        )
    else:
        return bad_request(result.get("error", "삭제 실패"))


@api_bp.route("/docs/upload", methods=["POST"])
@jwt_required
def api_docs_upload():
    """RAG 문서 업로드 (단일/다중 지원)"""
    # 1. Check for multiple files
    files = request.files.getlist('files')
    
    # Fallback to single 'file' key if 'files' is empty
    if not files and 'file' in request.files:
        files = [request.files['file']]
        
    if not files or all(f.filename == '' for f in files):
        return bad_request("파일을 선택해주세요")
        
    results = []
    errors = []
    
    for file in files:
        if file and file.filename:
            try:
                # Pass FileStorage directly to service
                res = ai_service.upload_document(file)
                results.append(res)
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
    
    if not results and errors:
         return server_error("모든 파일 업로드가 실패했습니다")
         
    return success_response(
        data={"results": results, "errors": errors if errors else []},
        message=f"{len(results)}개 파일 업로드 성공"
    )
