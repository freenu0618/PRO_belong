# belong/services/ai/text_gen.py
"""
AI 텍스트 생성 서비스 (메모리 기능 포함)
- LFM2-350M 모델 사용
- ChromaDB 기반 대화 기억
"""

from belong.extensions import logger
from .model_loader import ModelLoaderService, UTILITY_MODELS, DEVICE
from .memory import MemoryService


class TextGenerationService:
    """
    AI 텍스트 생성 서비스 (메모리 기능 포함)
    
    역할:
    - 사용자 요청에 대한 텍스트 생성
    - 이전 대화 기억 및 컨텍스트 활용
    """
    
    def __init__(self, loader: ModelLoaderService = None):
        self._loader = loader or ModelLoaderService()
        self._generator = None
        self._tokenizer = None
    
    def _get_generator(self):
        """생성기 파이프라인 가져오기"""
        if self._generator is not None:
            return self._generator
        
        model_id = UTILITY_MODELS.get("text_gen", "LiquidAI/LFM2-350M")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            logger.info(f"📥 Loading text generation model: {model_id}")
            
            self._tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(model_id)
            
            if DEVICE == "cuda":
                model = model.cuda()
            
            self._generator = model
            logger.info(f"✅ Text generation model loaded: {model_id}")
            
            return self._generator
            
        except Exception as e:
            logger.error(f"❌ Failed to load text generation model: {e}")
            return None
    
    def generate(
        self, 
        prompt: str, 
        user_id: int = None,
        use_memory: bool = True,
        save_to_memory: bool = True,
        max_new_tokens: int = 256
    ) -> dict:
        """
        텍스트 생성 (메모리 기능 포함)
        
        Args:
            prompt: 사용자 요청
            user_id: 사용자 ID (메모리 기능용)
            use_memory: 이전 대화 컨텍스트 사용 여부
            save_to_memory: 대화를 메모리에 저장할지 여부
            max_new_tokens: 최대 생성 토큰 수
            
        Returns:
            {"raw_output": "생성된 텍스트", "context_used": "사용된 컨텍스트"}
        """
        model = self._get_generator()
        if model is None:
            return {"error": "모델 로드 실패", "raw_output": None}
        
        # 메모리에서 컨텍스트 가져오기
        context = ""
        memory = None
        
        if user_id and use_memory:
            try:
                memory = MemoryService(user_id)
                context = memory.get_context(prompt, max_tokens=500)
                if context:
                    logger.debug(f"🧠 Memory context found: {context[:100]}...")
            except Exception as e:
                logger.warning(f"Memory search failed: {e}")
        
        # 프롬프트 구성 (ChatML 형식 for Qwen)
        system_msg = "너는 사용자의 질문에 친절하고 정확하게 답변하는 AI 어시스턴트야. 이전 대화 기록이 있으면 그것을 참고해서 답변해."
        
        if context:
            full_prompt = f"""<|im_start|>system
{system_msg}

{context}
<|im_end|>
<|im_start|>user
{prompt}
<|im_end|>
<|im_start|>assistant
"""
        else:
            full_prompt = f"""<|im_start|>system
{system_msg}
<|im_end|>
<|im_start|>user
{prompt}
<|im_end|>
<|im_start|>assistant
"""
        
        try:
            # 토크나이징
            inputs = self._tokenizer(
                full_prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=1024
            )
            
            if DEVICE == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 생성
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.05,  # ✅ 낮은 temperature로 일관된 응답
                top_p=0.95,
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id
            )
            
            # 디코딩 (입력 부분 제외)
            generated = self._tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], 
                skip_special_tokens=True
            )
            
            # GPU 메모리 정리
            del outputs
            del inputs
            if DEVICE == "cuda":
                import torch
                torch.cuda.empty_cache()
            
            # 메모리에 저장
            if user_id and save_to_memory and memory:
                try:
                    memory.save(prompt, role="user")
                    memory.save(generated.strip(), role="assistant")
                    logger.info(f"💾 Conversation saved to memory for user {user_id}")
                except Exception as e:
                    logger.warning(f"Memory save failed: {e}")
            
            return {
                "raw_output": generated.strip(),
                "context_used": context if context else None
            }
            
        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return {"error": str(e), "raw_output": None}
    
    def clear_memory(self, user_id: int) -> dict:
        """사용자 메모리 초기화"""
        try:
            memory = MemoryService(user_id)
            count = memory.clear()
            return {"ok": True, "deleted_count": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}
