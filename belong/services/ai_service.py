# belong/services/ai_service.py
from typing import Dict, Any, List, Optional

import torch
from transformers import pipeline

from belong.extensions import logger


class AIService:
    """
    순수 모델 호출 담당 (PyTorch + HuggingFace)
    - 감정 분석
    - 개체명 인식
    - 질의응답
    - (추가) 챗봇 대화
    """

    def __init__(self, device: Optional[int] = None) -> None:
        # GPU / CPU 설정
        if device is None:
            self.device = 0 if torch.cuda.is_available() else -1
        else:
            self.device = device

        self._init_pipelines()

    def _init_pipelines(self) -> None:
        try:
            # 1) 감정 분석: beomi/KcELECTRA-base-v2022
            sentiment_model = "beomi/KcELECTRA-base-v2022"
            self.sentiment_pipe = pipeline(
                task="text-classification",
                model=sentiment_model,
                tokenizer=sentiment_model,
                device=self.device,
            )

            # 2) 개체 인식: Davlan/bert-base-multilingual-cased-ner-hrl
            ner_model = "Davlan/bert-base-multilingual-cased-ner-hrl"
            self.entities_pipe = pipeline(
                task="ner",
                model=ner_model,
                tokenizer=ner_model,
                aggregation_strategy="simple",
                device=self.device,
            )

            # 3) QA: monologg/koelectra-base-v3-finetuned-korquad
            qa_model = "monologg/koelectra-base-v3-finetuned-korquad"
            self.qa_pipe = pipeline(
                task="question-answering",
                model=qa_model,
                tokenizer=qa_model,
                device=self.device,
            )

            # 4) (추가) 챗봇: 한국어 대화형 텍스트 생성 모델
            # 필요하면 여기 모델명만 나중에 교체하면 됨.
            chat_model = "beomi/KoAlpaca-Polyglot-5.8B"
            self.chat_pipe = pipeline(
                task="text-generation",
                model=chat_model,
                tokenizer=chat_model,
                device=self.device,
            )

            logger.info("AIService pipelines initialized successfully.")

        except Exception as e:
            logger.exception(f"Failed to initialize AIService pipelines: {e}")
            raise

    # -----------------------
    # 감정 분석
    # -----------------------
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        outputs: List[Dict[str, Any]] = self.sentiment_pipe([text])
        if not outputs:
            return {"label": "UNKNOWN", "score": 0.0}
        out = outputs[0]
        return {
            "label": str(out.get("label", "")),
            "score": float(out.get("score", 0.0)),
        }

    # -----------------------
    # 개체 인식
    # -----------------------
    def analyze_entities(self, text: str) -> Dict[str, Any]:
        raw_entities: List[Dict[str, Any]] = self.entities_pipe(text)
        entities: List[Dict[str, Any]] = []
        for ent in raw_entities:
            entities.append(
                {
                    "entity": str(ent.get("entity_group") or ent.get("entity") or ""),
                    "text": str(ent.get("word") or ""),
                    "score": float(ent.get("score", 0.0)),
                    "start": int(ent.get("start", 0)),
                    "end": int(ent.get("end", 0)),
                }
            )
        return {"entities": entities}

    # -----------------------
    # 질의응답
    # -----------------------
    def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        # context가 비어 있으면 모델 호출 대신 안전하게 빈 답변 반환
        if not context:
            return {
                "answer": "",
                "score": 0.0,
                "start": 0,
                "end": 0,
            }

        raw = self.qa_pipe({"question": question, "context": context})
        return {
            "answer": str(raw.get("answer", "")),
            "score": float(raw.get("score", 0.0)),
            "start": int(raw.get("start", 0)),
            "end": int(raw.get("end", 0)),
        }

    # -----------------------
    # (추가) 챗봇 대화
    # -----------------------
    def chat(self, text: str, max_new_tokens: int = 128) -> Dict[str, Any]:
        """
        사용자의 입력 텍스트에 대해 대화형 응답을 생성.
        history를 쓰고 싶으면 나중에 프롬프트에 같이 붙이는 방식으로 확장하면 됨.
        """
        outputs = self.chat_pipe(
            text,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )
        if not outputs:
            return {"answer": ""}

        generated = outputs[0].get("generated_text", "")
        return {"answer": str(generated)}
