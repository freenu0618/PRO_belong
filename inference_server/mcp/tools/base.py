# inference_server/mcp/tools/base.py
"""BaseTool 추상 클래스 - 모든 MCP Tool의 기본 인터페이스"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    모든 MCP Tool이 상속받는 추상 기본 클래스

    각 Tool은 다음 메서드를 구현해야 합니다:
    - get_schema(): Tool의 JSON Schema 정의 반환
    - execute(): Tool의 실제 로직 실행
    """

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Tool의 JSON Schema 정의 반환

        Returns:
            {
                "name": "tool_name",
                "description": "Tool 설명",
                "inputSchema": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        """
        pass

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool의 실제 로직 실행

        Args:
            arguments: Tool 실행에 필요한 인자들

        Returns:
            Tool 실행 결과 (dict)
        """
        pass

    def validate_arguments(self, arguments: Dict[str, Any], required_keys: list) -> bool:
        """
        인자 검증 헬퍼 메서드

        Args:
            arguments: 검증할 인자들
            required_keys: 필수 키 목록

        Returns:
            모든 필수 키가 존재하면 True, 아니면 False
        """
        missing_keys = [key for key in required_keys if key not in arguments]
        if missing_keys:
            logger.warning(f"[{self.__class__.__name__}] Missing required keys: {missing_keys}")
            return False
        return True
