# inference_server/state.py
"""전역 상태 관리 - 모델, 토크나이저, 학습 작업 상태"""

import asyncio

# AI 모델 전역 상태
model = None
tokenizer = None
vectordb = None
mcp_server = None  # MCP Server 인스턴스
model_lock = asyncio.Lock()

# 학습 작업 상태 (job_id -> status dict)
training_jobs = {}
training_lock = asyncio.Lock()
