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


# ============================================================
# MCP (Model Context Protocol) Integration
# ============================================================

def _detect_tool_calls(response: str) -> list:
    """
    LLM 응답에서 Tool Call 감지 (Llama 3.1 JSON 형식)

    지원 형식:
    1. [TOOL_CALL] {"name": "...", "arguments": {...}} [/TOOL_CALL]
    2. 순수 JSON: {"name": "...", "arguments": {...}}

    Args:
        response: LLM 생성 응답

    Returns:
        [
            {"name": "database_query", "arguments": {...}},
            ...
        ]
    """
    import json

    tool_calls = []

    # 방법 1: [TOOL_CALL] 태그로 감싸진 JSON
    pattern1 = r'\[TOOL_CALL\]\s*(\{.*?\})\s*\[/TOOL_CALL\]'
    matches1 = re.findall(pattern1, response, re.DOTALL)

    for match in matches1:
        try:
            data = json.loads(match.strip())
            # "parameters" 또는 "arguments" 모두 지원
            arguments = data.get("parameters", data.get("arguments", {}))
            tool_calls.append({
                "name": data["name"],
                "arguments": arguments
            })
            logger.info(f"[MCP] Detected tool call: {data['name']}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[MCP] Failed to parse tool call: {e}")
            continue

    # 방법 2: 순수 JSON (태그 없이) - 전체 응답이 JSON인 경우
    if not tool_calls:
        try:
            # 전체 응답이 JSON인지 확인
            data = json.loads(response.strip())
            if "name" in data and ("parameters" in data or "arguments" in data):
                arguments = data.get("parameters", data.get("arguments", {}))
                tool_calls.append({
                    "name": data["name"],
                    "arguments": arguments
                })
                logger.info(f"[MCP] Detected pure JSON tool call: {data['name']}")
        except json.JSONDecodeError:
            pass  # JSON이 아니면 무시

    return tool_calls


async def generate_with_mcp(request: GenerateRequest) -> dict:
    """
    MCP 기반 텍스트 생성 (Tool Call 지원)

    동작 흐름:
    1. LLM에 질문 전달
    2. Tool Call 감지
    3. Tool 실행 (병렬 가능)
    4. Tool 결과를 LLM에 다시 전달
    5. 최종 답변 생성
    6. 최대 5회 반복

    Args:
        request: GenerateRequest

    Returns:
        {
            "output": "최종 답변",
            "tool_calls": [{"name": "...", "arguments": {...}}],
            "tool_results": [{"tool": "...", "result": {...}}],
            "iterations": 3
        }
    """
    if not state.model or not state.tokenizer:
        raise HTTPException(status_code=500, detail="Model is not loaded.")

    if not state.mcp_server:
        logger.warning("[MCP] MCP Server not initialized, falling back to standard generation")
        return await generate_text(request)

    max_iterations = 5
    current_prompt = request.prompt
    all_tool_calls = []
    all_tool_results = []

    logger.info(f"[MCP] Starting MCP generation (max {max_iterations} iterations)")

    try:
        async with state.model_lock:
            for iteration in range(max_iterations):
                logger.info(f"[MCP] Iteration {iteration + 1}/{max_iterations}")

                # LLM 생성 (기존 generate_text 로직 재사용)
                temp_request = GenerateRequest(
                    prompt=current_prompt,
                    max_new_tokens=request.max_new_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    model=getattr(request, "model", "base"),
                    use_rag=getattr(request, "use_rag", False),
                    user_query=getattr(request, "user_query", None)
                )

                # 기존 generate_text의 핵심 로직 호출
                response_text = await _generate_llm_response_internal(temp_request)

                logger.debug(f"[MCP] LLM Response (first 300 chars): {response_text[:300]}...")

                # Tool Call 감지
                tool_calls = _detect_tool_calls(response_text)

                if not tool_calls:
                    logger.info("[MCP] No tool calls detected. Returning final response.")
                    # 최종 응답 정제
                    final_response = clean_response(response_text)
                    return {
                        "output": final_response,
                        "tool_calls": all_tool_calls,
                        "tool_results": all_tool_results,
                        "iterations": iteration + 1
                    }

                logger.info(f"[MCP] Detected {len(tool_calls)} tool call(s)")
                all_tool_calls.extend(tool_calls)

                # Tool 실행 (병렬)
                import asyncio
                tool_tasks = [
                    state.mcp_server.call_tool(
                        tool_call["name"],
                        tool_call["arguments"]
                    )
                    for tool_call in tool_calls
                ]

                tool_results = await asyncio.gather(*tool_tasks, return_exceptions=True)

                # 결과 정리
                iteration_results = []
                for tool_call, result in zip(tool_calls, tool_results):
                    if isinstance(result, Exception):
                        logger.error(f"[MCP] Tool '{tool_call['name']}' failed: {result}")
                        iteration_results.append({
                            "tool": tool_call["name"],
                            "success": False,
                            "error": str(result)
                        })
                    else:
                        logger.info(f"[MCP] Tool '{tool_call['name']}' succeeded")
                        iteration_results.append({
                            "tool": tool_call["name"],
                            "success": True,
                            "result": result
                        })

                all_tool_results.extend(iteration_results)

                # Tool 결과를 프롬프트에 추가하여 재생성
                import json
                tool_results_text = json.dumps(iteration_results, ensure_ascii=False, indent=2)

                current_prompt = f"""원래 질문: {request.prompt}

도구 실행 결과:
{tool_results_text}

위 도구 실행 결과를 바탕으로 사용자의 질문에 답변하세요. 필요하면 추가 도구를 호출할 수도 있습니다."""

            # 최대 반복 횟수 도달
            logger.warning("[MCP] Max iterations reached without final answer")
            final_response = clean_response(response_text)
            return {
                "output": final_response,
                "tool_calls": all_tool_calls,
                "tool_results": all_tool_results,
                "iterations": max_iterations,
                "warning": "Max iterations reached"
            }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[MCP] Generation Error: {e}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"MCP 생성 오류: {str(e)}")


async def _generate_llm_response_internal(request: GenerateRequest) -> str:
    """
    내부용 LLM 응답 생성 (generate_text의 핵심 로직만 추출)

    Args:
        request: GenerateRequest

    Returns:
        LLM 생성 텍스트 (정제 전)
    """
    # 기존 generate_text의 핵심 로직만 복사
    # (간소화: RAG, 어댑터 선택 등은 기본값 사용)

    target_model = getattr(request, "model", "base")
    user_question = request.prompt or ""

    # 알파카 포맷
    full_prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{user_question}

### Response:
"""

    inputs = state.tokenizer(full_prompt, return_tensors="pt").to(state.model.device)

    safe_temp = max(request.temperature, 0.01) if request.temperature else 0.7
    do_sample_flag = safe_temp > 0.0

    outputs = state.model.generate(
        **inputs,
        max_new_tokens=request.max_new_tokens,
        temperature=safe_temp,
        top_p=request.top_p,
        repetition_penalty=1.15,
        do_sample=do_sample_flag,
        pad_token_id=state.tokenizer.eos_token_id,
        eos_token_id=state.tokenizer.eos_token_id
    )

    # 응답 추출
    prompt_token_len = inputs.input_ids.shape[1]
    response_tokens = outputs[0][prompt_token_len:]
    response_text = state.tokenizer.decode(response_tokens, skip_special_tokens=True)

    return response_text

