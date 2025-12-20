
import requests
import json
from flask import current_app
from belong.extensions import logger

class AIService:
    """
    RunPod Serverless vLLM 기반 AI 서비스
    - 로컬 모델 로딩 없이 가볍게 HTTP 요청으로 처리
    - Chat, Summarization, Translation 등 모든 기능을 LLM Prompting으로 수행
    """

    def __init__(self) -> None:
        pass

    def _call_runpod(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """RunPod Custom Inference Server로 요청 전송"""
        api_url = current_app.config.get("RUNPOD_ENDPOINT_URL")
        # Custom Server는 별도 인증 없이 열려있거나, 필요시 추가 구현.
        # RunPod Proxy URL은 기본적으로 공개 접근 가능 (또는 설정에 따라 다름)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Custom Inference Server Payload (inference_server.py)
        # GenerateRequest(prompt, max_new_tokens, temperature, top_p)
        payload = {
            "prompt": prompt,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            # Response: {"output": "generated text"}
            return data.get("output", "")
                
        except Exception as e:
            logger.error(f"RunPod API Call Failed: {e}")
            return f"AI Error: {str(e)}"

    def chat(self, text: str, model: str = None, options: dict = None) -> dict:
        """일반 챗봇 대화"""
        # Llama-3 Prompt Template 적용
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant for the Belong platform.<|eot_id|><|start_header_id|>user<|end_header_id|>

{text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        
        response_text = self._call_runpod(prompt, max_tokens=1024)
        return {"response": response_text}

    def analyze_sentiment(self, text: str, model: str = None) -> dict:
        """감정 분석 (LLM Prompting)"""
        prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>
Analyze the sentiment of the following text and return ONLY JSON format: {{"label": "POSITIVE" or "NEGATIVE", "score": 0.0 to 1.0}}

Text: {text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        
        try:
            raw_res = self._call_runpod(prompt, max_tokens=100)
            # JSON 파싱 시도 (LLM이 잡설 섞을 수 있음)
            start = raw_res.find("{")
            end = raw_res.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(raw_res[start:end])
            return {"label": "UNKNOWN", "score": 0.0, "raw": raw_res}
        except:
            return {"label": "ERROR", "score": 0.0}

    def summarize(self, text: str, model: str = None) -> dict:
        """요약"""
        prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>
Summarize the following text in Korean concisely.

Text: {text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        res = self._call_runpod(prompt)
        return {"summary": res}

    def translate(self, text: str, direction: str = "ko-en", model: str = None) -> dict:
        """번역"""
        lang_map = {"ko-en": "Korean to English", "en-ko": "English to Korean"}
        target_lang = lang_map.get(direction, "Korean to English")
        
        prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>
Translate the following text from {target_lang}.

Text: {text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        res = self._call_runpod(prompt)
        return {"translation": res}

    def analyze_entities(self, text: str, model: str = None) -> dict:
        """개체명 인식 (NER)"""
        return {"entities": []} # LLM NER은 복잡하므로 일단 Skip or Simple

    def answer_question(self, question: str, context: str, model: str = None) -> dict:
        """QA"""
        prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>
Use the following context to answer the question.

Context: {context}

Question: {question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        res = self._call_runpod(prompt)
        return {"answer": res}
