# inference_server/services/generate.py
"""텍스트 생성 전담 서비스"""

import os
import logging
from fastapi import HTTPException

from .. import state
from ..schemas import GenerateRequest

logger = logging.getLogger(__name__)


async def generate_text(request: GenerateRequest) -> dict:
    """
    텍스트 생성 처리
    
    Args:
        request: GenerateRequest (prompt, max_new_tokens, temperature, etc.)
        
    Returns:
        {"output": "생성된 텍스트"}
    """
    if not state.model or not state.tokenizer:
        raise HTTPException(status_code=500, detail="Model is not loaded.")

    try:
        # 🔒 Critical Section: Lock model usage to prevent adapter race conditions
        async with state.model_lock:
            target_model = getattr(request, "model", "lora_best_r32")
            if target_model == "constant_with_warmup":
                target_model = "lora_best_r32"  # Fallback for old requests

            # RAG Context Retrieval
            rag_context = ""
            if request.use_rag:
                if state.vectordb:
                    try:
                        print(f"🔍 Searching RAG for: {request.prompt}")
                        docs = state.vectordb.similarity_search(request.prompt, k=3)
                        if docs:
                            context_text = "\n".join([doc.page_content for doc in docs])
                            rag_context = f"Here is some context to help you answer:\n{context_text}\n\n"
                            print(f"✅ RAG Context Added ({len(docs)} chunks)")
                    except Exception as e:
                        print(f"⚠️ RAG Search Error: {e}")
                else:
                    print("⚠️ RAG requested but VectorDB not initialized.")

            # Construct Prompt
            full_prompt = f"{rag_context}{request.prompt}" if rag_context else request.prompt

            # 어댑터 선택 및 동적 로딩
            if target_model == "base" or "base" in target_model:
                # Base 모델 사용
                context = state.model.disable_adapter()
            else:
                # 1. 이미 로드된 adapter인지 확인
                if target_model in state.model.peft_config:
                    logger.info(f"✅ Using cached adapter: {target_model}")
                    state.model.set_adapter(target_model)
                    context = None
                else:
                    # 2. /workspace/output에서 동적 로드 시도
                    adapter_path = f"/workspace/output/{target_model}"
                    if os.path.exists(adapter_path):
                        try:
                            logger.info(f"🔧 Loading adapter dynamically: {target_model} from {adapter_path}")
                            state.model.load_adapter(adapter_path, adapter_name=target_model)
                            state.model.set_adapter(target_model)
                            logger.info(f"✅ Adapter {target_model} loaded successfully")
                            context = None
                        except Exception as e:
                            logger.error(f"❌ Failed to load adapter {target_model}: {e}")
                            # Fallback to default
                            if "lora_best_r32" in state.model.peft_config:
                                logger.warning(f"Falling back to lora_best_r32")
                                state.model.set_adapter("lora_best_r32")
                                context = None
                            else:
                                logger.warning("No adapters available, using base model")
                                context = state.model.disable_adapter()
                    else:
                        # 3. Fallback to default adapter
                        logger.warning(f"Adapter {target_model} not found at {adapter_path}")
                        if "lora_best_r32" in state.model.peft_config:
                            logger.info("Using default adapter: lora_best_r32")
                            state.model.set_adapter("lora_best_r32")
                            context = None
                        else:
                            logger.warning("Default adapter not found, using base model")
                            context = state.model.disable_adapter()

            inputs = state.tokenizer(full_prompt, return_tensors="pt").to(state.model.device)

            # 🔧 Temperature Validation
            safe_temp = max(request.temperature, 0.01) if request.temperature else 0.7

            # Base Model Context 처리
            if target_model == "base" or "base" in target_model:
                with state.model.disable_adapter():
                    outputs = state.model.generate(
                        **inputs,
                        max_new_tokens=request.max_new_tokens,
                        temperature=safe_temp,
                        top_p=request.top_p,
                        repetition_penalty=1.2,
                        do_sample=True,
                        pad_token_id=state.tokenizer.eos_token_id,
                        eos_token_id=[state.tokenizer.eos_token_id, state.tokenizer.convert_tokens_to_ids("<|eot_id|>")]
                    )
            else:
                outputs = state.model.generate(
                    **inputs,
                    max_new_tokens=request.max_new_tokens,
                    temperature=safe_temp,
                    top_p=request.top_p,
                    repetition_penalty=1.2,
                    do_sample=True,
                    pad_token_id=state.tokenizer.eos_token_id,
                    eos_token_id=[state.tokenizer.eos_token_id, state.tokenizer.convert_tokens_to_ids("<|eot_id|>")]
                )

            # 토큰 개수 기반으로 정확하게 응답만 추출
            prompt_token_len = inputs.input_ids.shape[1]
            response_tokens = outputs[0][prompt_token_len:]
            response_text = state.tokenizer.decode(response_tokens, skip_special_tokens=True)

            return {"output": response_text.strip()}

    except Exception as e:
        print(f"Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def reload_model():
    """
    학습 완료 후 추론 모델 재로드
    """
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
    
    logger.info("🔄 Reloading inference model...")
    
    # GPU 캐시 정리
    torch.cuda.empty_cache()
    
    hf_token = os.environ.get("HF_TOKEN")
    base_model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
    
    # 4-bit 양자화 설정
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )
    
    try:
        # 토크나이저 로드
        state.tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            token=hf_token,
            trust_remote_code=True
        )
        state.tokenizer.pad_token = state.tokenizer.eos_token
        
        # 베이스 모델 로드
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            token=hf_token,
            trust_remote_code=True
        )
        
        # 기본 어댑터 로드 (lora_best_r32)
        adapter_path = "/workspace/fine_tune/lora_best_r32"
        if os.path.exists(adapter_path):
            state.model = PeftModel.from_pretrained(base_model, adapter_path, adapter_name="lora_best_r32")
            logger.info(f"✅ Model reloaded with adapter: lora_best_r32")
        else:
            state.model = base_model
            logger.warning("⚠️ No adapter found, using base model only")
        
        logger.info("✅ Inference model reload complete")
        
    except Exception as e:
        logger.error(f"❌ Model reload failed: {e}")
        raise

