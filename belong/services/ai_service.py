import torch
from transformers import pipeline
from typing import Dict, Any, List, Optional
from belong.extensions import logger

class AIService:
    """
    HuggingFace Pipelines 기반 AI 서비스 (Reverted)
    - 감정 분석 (KoELECTRA)
    - 개체 인식 (KoELECTRA NER)
    - 질의 응답 (KoELECTRA QA)
    - 텍스트 요약 (T5)
    - 번역 (mBART)
    """

    def __init__(self) -> None:
        self.device = 0 if torch.cuda.is_available() else -1
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
    # 1. 감정 분석
    # -----------------------
    def analyze_sentiment(self, text: str, model: str = None) -> Dict[str, Any]:
        result = self.sentiment_pipe(text)
        # [{'label': '1', 'score': 0.9}] (1=Positive, 0=Negative typically for this model)
        return result

    # -----------------------
    # 2. 개체 인식
    # -----------------------
    def analyze_entities(self, text: str, model: str = None) -> Dict[str, Any]:
        result = self.entities_pipe(text)
        return {"entities": result}

    # -----------------------
    # 3. 질의 응답
    # -----------------------
    def answer_question(self, question: str, context: str, model: str = None) -> Dict[str, Any]:
        result = self.qa_pipe(question=question, context=context)
        return {"answer": result['answer']}

    # -----------------------
    # 4. 텍스트 요약
    # -----------------------
    def summarize(self, text: str, model: str = None) -> Dict[str, Any]:
        result = self.summarization_pipe(text)
        # [{'summary_text': '...'}]
        return {"summary": result[0]['summary_text']}

    # -----------------------
    # 5. 번역
    # -----------------------
    def translate(self, text: str, direction: str = "ko-en", model: str = None) -> Dict[str, Any]:
        if direction == "ko-en":
            result = self.translate_ko_en_pipe(text)
            return {"translation": result[0]['translation_text']}
        else:
            result = self.translate_en_ko_pipe(text)
            return {"translation": result[0]['translation_text']}
