# belong/services/ai/translation.py
"""
번역 서비스
- 한→영, 영→한 번역
- 로컬 GPU transformers pipeline 사용
"""

from belong.extensions import logger
from .model_loader import ModelLoaderService, UTILITY_MODELS, DEVICE


class TranslationService:
    """
    번역 전용 서비스
    
    지원:
    - ko-en: 한국어 → 영어
    - en-ko: 영어 → 한국어
    """
    
    def __init__(self, loader: ModelLoaderService = None):
        self._loader = loader or ModelLoaderService()
        self._translator_cache = {}
    
    def _get_translator(self, direction: str):
        """방향별 번역 파이프라인 또는 모델 가져오기"""
        if direction in self._translator_cache:
            return self._translator_cache[direction]
        
        model_key = "translate_ko_en" if direction == "ko-en" else "translate_en_ko"
        model_id = UTILITY_MODELS.get(model_key)
        
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            
            logger.info(f"📥 Loading translation model: {model_id} for {direction}")
            
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
            
            if DEVICE == "cuda":
                model = model.cuda()
            
            self._translator_cache[direction] = (tokenizer, model, model_id)
            logger.info(f"✅ Translation model loaded: {model_id}")
            
            return self._translator_cache[direction]
            
        except Exception as e:
            logger.error(f"❌ Failed to load translation model: {e}")
            return None
    
    def translate(self, text: str, direction: str = "ko-en") -> dict:
        """
        텍스트 번역
        
        Args:
            text: 번역할 텍스트
            direction: "ko-en" 또는 "en-ko"
            
        Returns:
            {"translation": "번역된 텍스트"}
        """
        try:
            result = self._get_translator(direction)
            if result is None:
                return {"translation": "[번역 실패] 모델 로드 실패"}
            
            tokenizer, model, model_id = result
            
            # SMaLL-100 또는 M2M100 계열 모델인 경우 src_lang/tgt_lang 설정
            if "small100" in model_id.lower() or "m2m" in model_id.lower():
                if direction == "ko-en":
                    tokenizer.src_lang = "ko"
                    tokenizer.tgt_lang = "en"
                else:
                    tokenizer.src_lang = "en"
                    tokenizer.tgt_lang = "ko"
            
            # 인코딩
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            if DEVICE == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 생성
            outputs = model.generate(
                **inputs,
                max_length=512,
                num_beams=4,
                early_stopping=True
            )
            
            # 디코딩
            translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {"translation": translation}
            
        except Exception as e:
            logger.error(f"Translate error: {e}")
            return {"translation": f"[번역 실패] {str(e)}"}
