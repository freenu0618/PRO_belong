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
            
            result = generator(full_prompt, max_new_tokens=256, temperature=0.1)
            
            if isinstance(result, list) and len(result) > 0:
                generated = result[0].get("generated_text", "")
                
                # JSON 파싱 시도
                json_match = re.search(r'\{.*\}', generated, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        return {
                            "function_name": parsed.get("name", parsed.get("function", "")),
                            "arguments": parsed.get("arguments", parsed.get("params", {})),
                            "raw_output": generated
                        }
                    except json.JSONDecodeError:
                        pass
                
                return {"function_name": None, "arguments": {}, "raw_output": generated}
            
            return {"function_name": None, "arguments": {}, "raw_output": str(result)}
            
        except Exception as e:
            logger.error(f"Function call error: {e}")
            return {"error": str(e), "raw_output": None}
