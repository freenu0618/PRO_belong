# belong/services/ai/function_call.py
"""
Function Call 생성 서비스
- LLM을 통한 함수 호출 생성
- JSON 파싱 및 검증
"""

import json
import re
from belong.extensions import logger
from .model_loader import ModelLoaderService, UTILITY_MODELS


class FunctionCallService:
    """
    Function Call 생성 서비스
    
    역할:
    - 사용자 요청에서 함수 호출 정보 추출
    - 함수 정의 기반 프롬프트 생성
    - JSON 응답 파싱
    """
    
    def __init__(self, loader: ModelLoaderService = None):
        self._loader = loader or ModelLoaderService()
    
    def _parse_llm_json(self, response_text: str) -> dict:
        """
        LLM 응답에서 JSON을 안전하게 추출
        
        처리 순서:
        1. 코드블록(```json...```) 추출
        2. JSON 객체 패턴 매칭
        3. 파싱 시도 및 복구
        """
        try:
            # 1. 코드블록 추출 시도
            code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
            if code_block:
                response_text = code_block.group(1).strip()
            
            # 2. JSON 객체 추출 (중첩된 객체 지원)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if not json_match:
                # 간단한 패턴 재시도
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if not json_match:
                return None
            
            json_str = json_match.group()
            
            # 3. 파싱 시도
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 4. 복구 시도: 흔한 오류 수정
                # 작은따옴표 -> 큰따옴표
                fixed = json_str.replace("'", '"')
                # 후행 쉼표 제거
                fixed = re.sub(r',\s*}', '}', fixed)
                fixed = re.sub(r',\s*]', ']', fixed)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {json_str[:100]}...")
                    return None
        except Exception as e:
            logger.error(f"JSON 추출 오류: {e}")
            return None
    
    def generate(self, prompt: str, functions: list = None, model: str = None) -> dict:
        """
        Function Call 생성
        
        Args:
            prompt: 사용자 요청
            functions: 사용 가능한 함수 정의 리스트 [{name, description}, ...]
            model: 사용할 모델 (선택)
            
        Returns:
            {"function_name": "...", "arguments": {...}, "raw_output": "..."}
        """
        model_id = UTILITY_MODELS.get("text_gen", "LiquidAI/LFM2-350M")
        
        # 함수 정의가 있으면 프롬프트에 포함
        if functions:
            func_desc = "\n".join([
                f"- {f.get('name')}: {f.get('description', '')}" 
                for f in functions
            ])
            full_prompt = f"""Available functions:
{func_desc}

User request: {prompt}

Generate a function call to handle this request."""
        else:
            full_prompt = prompt
        
        try:
            generator = self._loader.get_pipeline("text-generation", model_id)
            if generator is None:
                return {"error": f"모델 로드 실패: {model_id}", "raw_output": None}
            
            result = generator(full_prompt, max_new_tokens=256, temperature=0.05, top_p=0.95)
            
            if isinstance(result, list) and len(result) > 0:
                generated = result[0].get("generated_text", "")
                
                # ✅ 강화된 JSON 파싱
                parsed = self._parse_llm_json(generated)
                if parsed:
                    return {
                        "function_name": parsed.get("name", parsed.get("function", "")),
                        "arguments": parsed.get("arguments", parsed.get("params", {})),
                        "raw_output": generated
                    }
                
                return {"function_name": None, "arguments": {}, "raw_output": generated}
            
            return {"function_name": None, "arguments": {}, "raw_output": str(result)}
            
        except Exception as e:
            logger.error(f"Function call error: {e}")
            return {"error": str(e), "raw_output": None}
