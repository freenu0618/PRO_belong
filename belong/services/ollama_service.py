import requests
import json
from typing import Dict, Any, List, Optional
from belong.extensions import logger

class OllamaService:
    """
    Ollama API 연동 서비스
    - AI 파인튜닝 페이지(/tuning)에서 사용
    - Fine-Tuned GGUF 모델과의 대화 및 비교 담당
    """

    def __init__(self, ollama_url: str = "http://localhost:11434") -> None:
        self.base_url = ollama_url
        self.api_generate = f"{self.base_url}/api/generate"
        self.api_chat = f"{self.base_url}/api/chat"

    def chat(self, messages: List[Dict[str, str]], model: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ollama Chat API 호출"""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options or {}  # temp, top_p, num_predict, etc.
        }

        try:
            response = requests.post(self.api_chat, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ollama Chat Failed: {e}")
            return {"error": str(e)}

    def generate(self, prompt: str, model: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ollama Generate API 호출"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options or {}
        }
        
        try:
            response = requests.post(self.api_generate, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ollama Generate Failed: {e}")
            return {"error": str(e)}
