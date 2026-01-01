# inference_server/services/generate.py
"""텍스트 생성 전담 서비스"""

import os
import re
import logging
from fastapi import HTTPException

from inference_server import state
from ..schemas import GenerateRequest

logger = logging.getLogger(__name__)


def clean_response(text: str) -> str:
    """
    RAG 오염 텍스트 및 불필요한 패턴 제거
    
    제거 대상:
    - 시스템 프롬프트 관련 텍스트 (assistantsystem, system, user 등)
    - 이전 대화 이력 패턴 (사용자 질문:, 응:, 답변: 등)
    - RAG 문서에서 유입된 노이즈 텍스트
    """
    if not text:
        return ""
    
    cleaned = text.strip()
    
    # 1. 응답 시작 부분의 오염된 prefix 제거
    noise_prefixes = [
        r'^\.ai\s*\n*',                  # .ai 로 시작
        r'^assistantsystem[^\n]*\n*',    # assistantsystem으로 시작하는 라인
        r'^assistantAI[^\n]*\n*',        # assistantAI로 시작
        r'^assistant\s*:?\s*',           # assistant: 로 시작
        r'^system\s*:?\s*',              # system: 로 시작
        r'^시스템\s*:?\s*안녕하세요[^\n]*\n*',  # "시스템 : 안녕하세요..." 로 시작
        r'^안녕하세요!?\s*저는[^\n]*설계되었습니다[^\n]*\n*',  # 챗봇 소개 템플릿
        r'^AI\s*:?\s*',                  # AI: 로 시작
        r'^봇\s*:?\s*',                  # 봇: 로 시작
        r'^응\s*:?\s*',                  # 응: 로 시작 (이전 대화 유출)
        r'^답변\s*:?\s*',                # 답변: 로 시작
        r'^---+\s*\n*',                  # --- 로 시작
        r'^사용자\s*질문\s*:[^\n]*\n*',    # "사용자 질문: ..." 로 시작
        r'^사용자가\s*입력한\s*값\s*:[^\n]*\n*',  # "사용자가 입력한 값 : ..." 로 시작
    ]
    
    for pattern in noise_prefixes:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # 2. 이전 대화 이력 패턴 제거 (RAG에서 유입된 경우)
    # "사용자 질문: ... 응: ..." 형태의 텍스트 블록 제거
    conversation_patterns = [
        r'사용자\s*질문\s*:\s*[^\n]+\n*응\s*:\s*[^\n]+',  # 사용자 질문: ... 응: ...
        r'User\s*:\s*[^\n]+\n*Assistant\s*:\s*[^\n]+',    # User: ... Assistant: ...
    ]
    
    for pattern in conversation_patterns:
        # 응답에서 이전 대화 이력이 섞여있으면 첫 번째 것만 제거하고 중단
        cleaned = re.sub(pattern, '', cleaned, count=3, flags=re.IGNORECASE)
    
    # 3. 특정 오염 키워드가 응답 시작에 있으면 제거
    contamination_keywords = [
        'chatbot', 'artificialintelligence', '인공지능', '톡톡AI',
        'AIchatbot', '고독사독거', 
        'intelligencechatbot', 'chatbotkorean', '취업력',
        'chatgptopenai', 'openai', 'chatgpt', 'NLPseoul',
    ]
    
    # 응답 시작 부분(처음 100자)에서 오염 키워드 체크
    first_100 = cleaned[:100].lower() if len(cleaned) > 100 else cleaned.lower()
    
    for keyword in contamination_keywords:
        if keyword.lower() in first_100:
            # 키워드가 포함된 첫 번째 줄 제거 시도
            lines = cleaned.split('\n')
            if lines and keyword.lower() in lines[0].lower():
                cleaned = '\n'.join(lines[1:]).strip()
    
    # 4. 빈 줄 정리
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()



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
            target_model = getattr(request, "model", "base")  # ✅ 기본값: 베이스 모델
            if target_model == "constant_with_warmup":
                target_model = "base"  # Fallback for old requests

            # RAG Context Retrieval
            rag_context = ""
            rag_sources = []  # ✅ 출처 정보 저장
            use_rag = getattr(request, 'use_rag', False)
            
            # ✅ 디버깅: VectorDB 상태 확인
            print(f"🔧 DEBUG: state.vectordb = {state.vectordb}, type = {type(state.vectordb)}")
            
            # ✅ RAG 사용 여부 명시적 로깅
            logger.info(f"🔍 RAG Status: {'ENABLED' if use_rag else 'DISABLED'} for model={target_model}")
            
            if use_rag:
                if state.vectordb is not None:  # ✅ Chroma 객체는 빈 상태에서 bool() = False이므로 명시적 체크
                    try:
                        # ✅ RAG 검색 쿼리: user_query 필드 우선, 없으면 프롬프트에서 추출
                        search_query = getattr(request, 'user_query', None) or ""
                        
                        if not search_query:
                            # 프롬프트에서 사용자 질문 추출 시도
                            prompt = request.prompt
                            if "사용자 질문:" in prompt:
                                # DB RAG 컨텍스트 형식: "...사용자 질문: 실제질문"
                                search_query = prompt.split("사용자 질문:")[-1].strip()
                            elif "<|start_header_id|>user<|end_header_id|>" in prompt:
                                # Llama 3 프롬프트 형식
                                parts = prompt.split("<|start_header_id|>user<|end_header_id|>")
                                search_query = parts[-1].split("<|eot_id|>")[0].strip()
                            else:
                                search_query = prompt[:500]  # 최대 500자만 사용
                        
                        print(f"🔍 Searching RAG for: {search_query[:100]}...")  # 처음 100자만 로그
                        # ✅ 1단계: 넉넉하게 20개 검색
                        docs = state.vectordb.similarity_search(search_query, k=20)
                        print(f"🔎 RAG Search returned: {len(docs)} documents")  # ✅ 디버깅용
                        
                        # ✅ 2단계: Reranker로 Top 3 선별
                        from .reranker import reranker
                        if docs and reranker.load_model():
                            reranked = reranker.rerank(search_query, docs, top_k=3)
                            docs = [doc for doc, score in reranked]
                            print(f"📊 Reranked: {len(reranked)} docs selected")
                        elif docs:
                            docs = docs[:3]  # Reranker 없으면 상위 3개만
                        
                        if docs:
                            context_parts = []
                            for i, doc in enumerate(docs, 1):
                                context_parts.append(doc.page_content)
                                # ✅ 출처 메타데이터 추출
                                source = doc.metadata.get("source", "Unknown")
                                page = doc.metadata.get("page", "")
                                source_info = {"source": source, "page": page} if page else {"source": source}
                                if source_info not in rag_sources:
                                    rag_sources.append(source_info)
                            
                            context_text = "\n---\n".join(context_parts)
                            # ✅ 한국어 RAG 컨텍스트 (영어 → 한국어)
                            rag_context = f"""다음은 참고 문서입니다:

{context_text}

---
위 문서 내용을 참고하여 질문에 답변하세요."""
                            print(f"✅ RAG Context Added ({len(docs)} chunks from {len(rag_sources)} sources)")
                    except Exception as e:
                        print(f"⚠️ RAG Search Error: {e}")
                else:
                    print("⚠️ RAG requested but VectorDB not initialized.")

            # ✅ 프롬프트 처리: 알파카 포맷 (파인튜닝 시 사용한 포맷과 동일)
            user_question = request.prompt or ""
            
            # 알파카 포맷 템플릿
            # 파인튜닝 시 사용한 포맷: convert_to_alpaca_format(instruction, response)
            
            if rag_context:
                # RAG 사용: 지시사항에 참고 문서 포함
                instruction_text = f"""다음은 참고 문서입니다:

{rag_context}

위 문서 내용을 참고하여 질문에 답변하세요.

질문: {user_question}"""
                
                full_prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction_text}

### Response:
"""
            else:
                # RAG 미사용: 질문만
                full_prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{user_question}

### Response:
"""
            
            
            print(f"📜 Final prompt length: {len(full_prompt)} chars")

            # 어댑터 선택 및 동적 로딩
            is_peft_model = hasattr(state.model, 'peft_config')  # ✅ PeftModel 여부 체크
            
            if target_model == "base" or "base" in target_model:
                # Base 모델 사용
                if is_peft_model:
                    context = state.model.disable_adapter()
                else:
                    context = None  # Base model 그대로 사용
            else:
                if not is_peft_model:
                    # PeftModel이 아니면 어댑터 사용 불가
                    logger.warning("Model is not a PeftModel, using base model for all requests")
                    context = None
                elif target_model in state.model.peft_config:
                    # 1. 이미 로드된 adapter인지 확인
                    logger.info(f"✅ Using cached adapter: {target_model}")
                    state.model.set_adapter(target_model)
                    context = None
                else:
                    # 2. /workspace/output에서 동적 로드 시도
                    base_adapter_path = f"/workspace/output/{target_model}"
                    adapter_path = None
                    
                    if os.path.exists(base_adapter_path):
                        # adapter_config.json이 직접 있는지 확인
                        if os.path.exists(os.path.join(base_adapter_path, "adapter_config.json")):
                            adapter_path = base_adapter_path
                        else:
                            # checkpoint 폴더에서 최신 것 찾기
                            try:
                                subdirs = [d for d in os.listdir(base_adapter_path) 
                                          if os.path.isdir(os.path.join(base_adapter_path, d)) and d.startswith("checkpoint-")]
                                if subdirs:
                                    subdirs.sort(key=lambda x: int(x.split('-')[-1]) if x.split('-')[-1].isdigit() else 0)
                                    latest_checkpoint = subdirs[-1]
                                    checkpoint_path = os.path.join(base_adapter_path, latest_checkpoint)
                                    if os.path.exists(os.path.join(checkpoint_path, "adapter_config.json")):
                                        adapter_path = checkpoint_path
                                        logger.info(f"📁 Found adapter in checkpoint: {latest_checkpoint}")
                            except Exception as e:
                                logger.warning(f"Error searching checkpoints: {e}")
                    
                    if adapter_path:
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
                        logger.warning(f"Adapter {target_model} not found at {base_adapter_path}")
                        if "lora_best_r32" in state.model.peft_config:
                            logger.info("Using default adapter: lora_best_r32")
                            state.model.set_adapter("lora_best_r32")
                            context = None
                        else:
                            logger.warning("Default adapter not found, using base model")
                            context = state.model.disable_adapter()

            inputs = state.tokenizer(full_prompt, return_tensors="pt").to(state.model.device)

            # 🔧 Temperature Validation
            safe_temp = max(request.temperature, 0.01) if request.temperature else 0.4  # ✅ 기본값 0.4 (일관성 향상)
            
            # 🔧 do_sample 자동 설정 (Temperature == 0이면 False)
            do_sample_flag = safe_temp > 0.0

            # Base Model Context 처리
            use_base_mode = target_model == "base" or "base" in target_model
            
            if use_base_mode and is_peft_model:
                # PeftModel에서 base 모델 사용
                with state.model.disable_adapter():
                    outputs = state.model.generate(
                        **inputs,
                        max_new_tokens=request.max_new_tokens,
                        temperature=safe_temp,
                        top_p=request.top_p,
                        repetition_penalty=1.15,  # ✅ 반복 억제 균형
                        do_sample=do_sample_flag,
                        pad_token_id=state.tokenizer.eos_token_id,
                        eos_token_id=state.tokenizer.eos_token_id  # ✅ <|eot_id|> 제거 (조기 종료 방지)
                    )
            elif use_base_mode and not is_peft_model:
                # 일반 모델 (PeftModel 아님) - 그냥 생성
                outputs = state.model.generate(
                    **inputs,
                    max_new_tokens=request.max_new_tokens,
                    temperature=safe_temp,
                    top_p=request.top_p,
                    repetition_penalty=1.15,
                    do_sample=do_sample_flag,
                    pad_token_id=state.tokenizer.eos_token_id,
                    eos_token_id=state.tokenizer.eos_token_id  # ✅ <|eot_id|> 제거 (조기 종료 방지)
                )
            else:
                outputs = state.model.generate(
                    **inputs,
                    max_new_tokens=request.max_new_tokens,
                    temperature=safe_temp,
                    top_p=request.top_p,
                    repetition_penalty=1.15,
                    do_sample=do_sample_flag,
                    pad_token_id=state.tokenizer.eos_token_id,
                    eos_token_id=state.tokenizer.eos_token_id  # ✅ <|eot_id|> 제거 (조기 종료 방지)
                )

            # 토큰 개수 기반으로 정확하게 응답만 추출
            prompt_token_len = inputs.input_ids.shape[1]
            response_tokens = outputs[0][prompt_token_len:]
            response_text = state.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
            # ✅ 디버깅 로그 추가
            print(f"📊 Prompt tokens: {prompt_token_len}, Generated tokens: {len(response_tokens)}")
            print(f"📝 Raw response (first 500 chars): {response_text[:500] if response_text else '(EMPTY)'}")
            
            # ✅ 응답 정제: RAG 오염 텍스트 필터링
            final_response = clean_response(response_text)
            
            if not final_response:
                final_response = "(AI가 응답을 생성하지 못했습니다. 다시 시도해주세요.)"
                logger.warning(f"Empty response! Prompt tokens: {prompt_token_len}, max_new_tokens: {request.max_new_tokens}")

            # ✅ RAG 사용 시 출처 정보 포함
            result = {"output": final_response}
            if rag_sources:
                result["sources"] = rag_sources
            return result

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Generation Error: {e}")
        print(f"📋 Stack trace:\n{error_trace}")
        logger.error(f"Generation Error: {e}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"생성 오류: {str(e)}")


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

