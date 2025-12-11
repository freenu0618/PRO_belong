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
            # 1) 감정 분석: KoELECTRA 기반 감성 분석
            sentiment_model = "Copycats/koelectra-base-v3-generalized-sentiment-analysis"
            self.sentiment_pipe = pipeline(
                task="text-classification",
                model=sentiment_model,
                tokenizer=sentiment_model,
                device=self.device,
            )

            # 2) 개체 인식: KoELECTRA 기반 한국어 NER
            ner_model = "Leo97/KoELECTRA-small-v3-modu-ner"
            self.entities_pipe = pipeline(
                task="ner",
                model=ner_model,
                tokenizer=ner_model,
                aggregation_strategy="simple",  # 토큰 여러 개를 하나의 엔티티로 합침
                device=self.device,
            )

            # 3) QA: KorQuAD 파인튜닝 KoELECTRA
            qa_model = "monologg/koelectra-base-v3-finetuned-korquad"
            self.qa_pipe = pipeline(
                task="question-answering",
                model=qa_model,
                tokenizer=qa_model,
                device=self.device,
            )

            # 4) 텍스트 요약: 한국어 T5 Summarization
            summarizer_model = "eenzeenee/t5-small-korean-summarization"
            self.summarization_pipe = pipeline(
                task="summarization",
                model=summarizer_model,
                tokenizer=summarizer_model,
                device=self.device,
            )

            # 5) 번역: Mbart 기반 한↔영

            model_id = "facebook/mbart-large-50-many-to-many-mmt"

            self.translate_ko_en_pipe = pipeline(
                task="translation",
                model=model_id,
                tokenizer=model_id,
                device=self.device,
                src_lang="ko_KR",
                tgt_lang="en_XX",
            )

            self.translate_en_ko_pipe = pipeline(
                task="translation",
                model=model_id,
                tokenizer=model_id,
                device=self.device,
                src_lang="en_XX",
                tgt_lang="ko_KR",
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
                    "text": str(ent.get("word", "")),
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
    # 텍스트 요약
    # -----------------------
    def summarize( self, text: str, max_length: int = 64, min_length: int = 16,) -> Dict[str, Any]:
        """
        긴 한국어 텍스트를 요약해서 반환.
        """
        if not text.strip():
            return {"summary": ""}

        outputs = self.summarization_pipe(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False,
        )
        if not outputs:
            return {"summary": ""}

        out = outputs[0]
        # T5 기반 summarization의 key 는 보통 summary_text
        summary = out.get("summary_text") or out.get("generated_text", "")
        return {"summary": str(summary)}

    # -----------------------
    # 번역 (한↔영)
    # -----------------------
    def translate( self, text: str, direction: str = "ko-en", ) -> Dict[str, Any]:
        """
        direction:
          - "ko-en" : 한국어 -> 영어
          - "en-ko" : 영어   -> 한국어
        """
        if not text.strip():
            return {"translation": "", "direction": direction}

        if direction == "en-ko":
            pipe = self.translate_en_ko_pipe
        else:
            # 기본값: ko-en
            direction = "ko-en"
            pipe = self.translate_ko_en_pipe

        outputs = pipe(text)
        if not outputs:
            return {"translation": "", "direction": direction}

        out = outputs[0]
        translated = out.get("translation_text") or out.get("generated_text", "")
        return {
            "translation": str(translated),
            "direction": direction,
        }
