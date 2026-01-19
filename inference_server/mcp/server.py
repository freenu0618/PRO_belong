# inference_server/mcp/server.py
"""BelongMCPServer - MCP Tool 관리 및 실행"""

import logging
from typing import Dict, Any, List

from .tools import DatabaseTool, RagTool, PredictionTool

logger = logging.getLogger(__name__)


class BelongMCPServer:
    """
    Belong AI Server의 MCP 서버

    역할:
    - Tool 등록 및 관리
    - Tool 실행 (동기/비동기)
    - Tool 스키마 제공
    """

    def __init__(self):
        """MCP 서버 초기화 및 Tool 등록"""
        logger.info("[MCP] Initializing Belong MCP Server...")

        self.tools: Dict[str, Any] = {
            "database_query": DatabaseTool(),
            "rag_search": RagTool(),
            "prediction": PredictionTool(),
        }

        logger.info(f"[MCP] Registered {len(self.tools)} tools: {list(self.tools.keys())}")

    def get_available_tools(self) -> List[str]:
        """사용 가능한 Tool 목록 반환"""
        return list(self.tools.keys())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """모든 Tool의 스키마 반환"""
        schemas = []
        for tool_name, tool_instance in self.tools.items():
            try:
                schema = tool_instance.get_schema()
                schemas.append(schema)
            except Exception as e:
                logger.error(f"[MCP] Failed to get schema for {tool_name}: {e}")

        return schemas

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool 실행

        Args:
            name: Tool 이름 (예: "database_query")
            arguments: Tool 실행 인자

        Returns:
            Tool 실행 결과

        Raises:
            ValueError: Tool이 존재하지 않는 경우
        """
        if name not in self.tools:
            logger.error(f"[MCP] Unknown tool: {name}")
            raise ValueError(f"Unknown tool: {name}. Available tools: {self.get_available_tools()}")

        logger.info(f"[MCP] Calling tool: {name}")
        logger.debug(f"[MCP] Arguments: {arguments}")

        try:
            tool_instance = self.tools[name]
            result = await tool_instance.execute(arguments)
            logger.info(f"[MCP] Tool {name} succeeded")
            return result
        except Exception as e:
            logger.error(f"[MCP] Tool {name} failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "tool": name,
                "success": False
            }

    def get_tool_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """
        LLM이 이해할 수 있는 형식으로 Tool Schema 반환
        (OpenAI Function Calling 표준 형식)

        Returns:
            [
                {
                    "type": "function",
                    "function": {
                        "name": "database_query",
                        "description": "...",
                        "parameters": {...}
                    }
                },
                ...
            ]
        """
        return self.get_tool_schemas()  # 기존 메서드 재사용

    def get_tool_description(self, name: str) -> str:
        """Tool 설명 반환"""
        if name not in self.tools:
            return f"Unknown tool: {name}"

        try:
            schema = self.tools[name].get_schema()
            return schema.get("description", "No description available")
        except Exception as e:
            logger.error(f"[MCP] Failed to get description for {name}: {e}")
            return f"Error getting description: {e}"
