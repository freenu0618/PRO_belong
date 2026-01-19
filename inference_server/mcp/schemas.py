# inference_server/mcp/schemas.py
"""MCP 요청/응답 스키마 정의"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ToolCallRequest(BaseModel):
    """Tool 호출 요청 스키마"""
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    """Tool 호출 응답 스키마"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tool: str


class MCPGenerateRequest(BaseModel):
    """MCP 기반 생성 요청 스키마"""
    prompt: str
    use_mcp: bool = True
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50


class MCPGenerateResponse(BaseModel):
    """MCP 기반 생성 응답 스키마"""
    output: str
    tool_calls: Optional[List[ToolCallRequest]] = None
    tool_results: Optional[List[ToolCallResponse]] = None
    iterations: int = 0
    warning: Optional[str] = None
