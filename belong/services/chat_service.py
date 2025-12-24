# belong/services/chat_service.py
from typing import Dict, Any, Optional, Tuple

from belong.models.chat_message import ChatMessage
from belong.repositories.chat_message_repo import ChatMessageRepository
from belong.services.ai_service import AIService
import json


class ChatService:
    """
    챗봇 + 대화 히스토리 관리 서비스

    - 로그인한 사용자의 대화를 DB에 저장하고
    - AIService를 통해 실제 AI 응답을 생성하고
    - 최근 히스토리를 함께 반환한다.
    공통 입력처리
    service, text, options = self._normalize_inputs(service, text, options)
    """

    def __init__(
        self,
        repo: Optional[ChatMessageRepository] = None,
        ai_service: Optional[AIService] = None,
    ) -> None:
        self.repo = repo or ChatMessageRepository()
        self.ai_service = ai_service or AIService()

    # ---------------------------
    # 내부 헬퍼: ChatMessage -> dict
    # ---------------------------
    def _serialize_message(self, msg: ChatMessage) -> Dict[str, Any]:
        return {
            "id": msg.id,
            "user_id": msg.user_id,
            "role": msg.role,
            "service": msg.service,
            "content": msg.content,
            # datetime 은 JSON 직렬화를 위해 문자열로 변환
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }

    # ---------------------------
    # 내부 헬퍼: 입력 정리
    # ---------------------------
    def _normalize_inputs(
        self,
        service: str,
        text: str,
        options: Optional[Dict[str, Any]],
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        service / text / options 에 기본값 및 공백 제거 등 공통 전처리 적용
        """
        normalized_service = (service or "qa").strip()
        # text 는 사용자가 입력한 그대로 두는 것이 자연스러워서 strip 은 하지 않음
        normalized_text = text or ""
        normalized_options: Dict[str, Any] = options or {}
        return normalized_service, normalized_text, normalized_options

    # ---------------------------
    # 내부 헬퍼: 메시지 저장
    # ---------------------------
    def _save_user_message(self, user_id: int, service: str, content: str) -> ChatMessage:
        """
        사용자(user) 역할 메시지를 CHAT_MESSAGE 에 저장
        """
        return self.repo.save(
            user_id=user_id,
            role="user",
            service=service,
            content=content,
        )

    def _save_assistant_message(self, user_id: int, service: str, content: str) -> ChatMessage:
        """
        어시스턴트(assistant) 역할 메시지를 CHAT_MESSAGE 에 저장
        """
        return self.repo.save(
            user_id=user_id,
            role="assistant",
            service=service,
            content=content,
        )

    # ---------------------------
    # 내부 헬퍼: service 별 AI 호출
    # ---------------------------
    def _run_sentiment(self, text: str) -> Tuple[Any, str]:
        """
        감정 분석 service 에 대한 실제 호출 + 사용자에게 보여줄 요약 텍스트 생성
        """
        result = self.ai_service.analyze_sentiment(text)
        # 사람이 볼 수 있게 간단히 요약 텍스트 생성
        if isinstance(result, dict):
            label = result.get("label")
            score = result.get("score")
            if score is not None:
                assistant_text = f"감정 분석 결과: {label} (score={score:.3f})"
            else:
                assistant_text = str(result)
        else:
            assistant_text = str(result)
        return result, assistant_text

    def _run_entities(self, text: str) -> Tuple[Any, str]:
        """
        개체 분석 service 에 대한 실제 호출 + 요약 텍스트 생성
        """
        result = self.ai_service.analyze_entities(text)
        if isinstance(result, dict):
            entities = result.get("entities", [])
            parts = [
                f"{e.get('text')}({e.get('entity')})"
                for e in entities
            ]
            assistant_text = "인식된 개체들: " + ", ".join(parts) if parts else "인식된 개체가 없습니다."
        else:
            assistant_text = str(result)
        return result, assistant_text

    def _run_qa(self, text: str, options: Dict[str, Any]) -> Tuple[Any, str]:
        """
        질의응답(Question Answering) service 에 대한 호출 + 답변 텍스트 생성
        """
        context = (options.get("context") or "").strip()
        result = self.ai_service.answer_question(
            question=text,
            context=context,
        )
        if isinstance(result, dict):
            assistant_text = result.get("answer") or str(result)
        else:
            assistant_text = str(result)
        return result, assistant_text

    def _run_free_chat(self, text: str) -> Tuple[Any, str]:
        """
        자유 대화(chat) service 에 대한 호출 + 답변 텍스트 생성
        """
        result = self.ai_service.chat(text)
        # ai_service.chat()은 "response" 키 반환
        assistant_text = result.get("response", "응답을 생성하지 못했어.") if isinstance(result, dict) else str(result)
        return result, assistant_text

    def _run_translate(self, text: str, options: Dict[str, Any]) -> Tuple[Any, str]:
        """
        번역 service 에 대한 호출 + 결과 텍스트 생성
        """
        direction = options.get("direction", "ko-en")
        result = self.ai_service.translate(text, direction=direction)
        if isinstance(result, dict):
            assistant_text = result.get("translation", str(result))
        else:
            assistant_text = str(result)
        return result, assistant_text

    def _run_summarize(self, text: str) -> Tuple[Any, str]:
        """
        요약 service 에 대한 호출 + 결과 텍스트 생성
        """
        result = self.ai_service.summarize(text)
        if isinstance(result, dict):
            assistant_text = result.get("summary", str(result))
        else:
            assistant_text = str(result)
        return result, assistant_text

    def _run_ai_for_service(self,service: str,text: str,options: Dict[str, Any],) -> Tuple[Any, str]:
        """
        service 값에 따라 적절한 AIService 메서드를 호출하고,
        (원본 result, 사용자에게 보여줄 assistant_text) 튜플을 반환한다.
        """
        if service == "sentiment":
            return self._run_sentiment(text)
        elif service == "entities":
            return self._run_entities(text)
        elif service == "qa":
            return self._run_qa(text, options)
        elif service == "chat":
            return self._run_free_chat(text)
        elif service == "translate":
            return self._run_translate(text, options)
        elif service == "summarize":
            return self._run_summarize(text)
        else:
            # 알 수 없는 service 값인 경우
            result: Dict[str, Any] = {"error": f"지원하지 않는 service 입니다: {service}"}
            assistant_text = "지원하지 않는 서비스입니다."
            return result, assistant_text

    # ---------------------------
    # 내부 헬퍼: 응답 JSON 조립
    # ---------------------------
    def _build_response(
        self,service: str, user_id: int,text: str,result: Any,history: Any,) -> Dict[str, Any]:
        """
        외부 API에 그대로 반환할 응답 JSON을 한 곳에서 조립한다.
        """
        return {
            "ok": True,
            "service": service,
            "user_id": user_id,
            "input": {"text": text},
            "result": result,
            "history": history,
            "debug": {"mode": "local_gpu"},
        }

    # ---------------------------
    # 외부 API: 한 번의 질문/응답 처리 (UC2)
    # ---------------------------
    def process(
        self,
        user_id: int,
        service: str,
        text: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        1) 사용자의 입력을 CHAT_MESSAGE(user) 로 저장
        2) service 종류에 맞게 AIService 호출
        3) 모델 응답을 CHAT_MESSAGE(assistant) 로 저장
        4) 최종 결과 + 최신 히스토리 리턴
        """

        # 0) 입력 값 정리
        service, text, options = self._normalize_inputs(service, text, options)

        # 1) 사용자 메시지 저장
        self._save_user_message(user_id, service, text)

        # 2) AI 서비스 호출 (service 종류에 따라 분기)
        result, assistant_text = self._run_ai_for_service(service, text, options)

        # 3) 모델 응답을 assistant 역할로 저장
        self._save_assistant_message(user_id, service, assistant_text)

        # 4) 최신 히스토리 함께 리턴
        history_data = self.get_history(user_id=user_id, limit=20)

        # 5) 응답 JSON 조립
        return self._build_response(
            service=service,
            user_id=user_id,
            text=text,
            result=result,
            history=history_data["history"],
        )

    # ---------------------------
    # 외부 API: 히스토리 조회
    # ---------------------------
    def get_history(self, user_id: int, limit: int = 20) -> Dict[str, Any]:
        messages = self.repo.list_by_user(user_id=user_id, limit=limit)
        history = [self._serialize_message(m) for m in messages]

        return {
            "ok": True,
            "user_id": user_id,
            "history": history,
        }
