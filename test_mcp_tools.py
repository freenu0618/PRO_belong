# test_mcp_tools.py
# -*- coding: utf-8 -*-
"""
MCP Tool 단위 테스트 스크립트
- Docker/서버 실행 없이 Tool만 독립적으로 테스트
- 빠른 개발 사이클 (5-10초)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

# 환경변수 로드
load_dotenv()

# 환경변수 확인
print("=" * 60)
print("🔧 환경변수 확인")
print("=" * 60)

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {'✅ Set' if DATABASE_URL else '❌ NOT SET'}")

if not DATABASE_URL:
    print("\n⚠️ WARNING: DATABASE_URL이 설정되지 않았습니다.")
    print("일부 테스트가 실패할 수 있습니다.")
    print("\n해결 방법:")
    print("1. .env 파일에 다음 추가:")
    print("   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/belong_db")
    print("2. PostgreSQL 설치 확인 (ENVIRONMENT_SETUP.md 참조)")
    print("3. belong_db 데이터베이스 생성 확인")
    print("")

print("=" * 60)
print("")

# Tool import
try:
    from inference_server.mcp.tools.database_tool import DatabaseTool
    from inference_server.mcp.tools.rag_tool import RagTool
    from inference_server.mcp.tools.prediction_tool import PredictionTool
    print("✅ Tool 모듈 import 성공\n")
except ImportError as e:
    print(f"❌ Tool 모듈 import 실패: {e}")
    sys.exit(1)


async def test_database_tool():
    """DatabaseTool 테스트"""
    print("=" * 60)
    print("[TEST 1] DatabaseTool - PostgreSQL 쿼리")
    print("=" * 60)

    tool = DatabaseTool()

    # Schema 확인
    schema = tool.get_schema()
    print(f"✅ Tool Name: {schema['function']['name']}")
    print(f"✅ Description: {schema['function']['description'][:80]}...")
    print(f"✅ Parameters: {list(schema['function']['parameters']['properties'].keys())}")
    print("")

    if not DATABASE_URL:
        print("⚠️ DATABASE_URL이 없어 실행 테스트를 건너뜁니다.\n")
        return

    # 실행 테스트
    print("🔄 Executing: database_query(regions=['강남구'], years=[2024])")
    result = await tool.execute({
        "regions": ["강남구"],
        "years": [2024],
        "data_type": "prediction"
    })

    if result.get("success"):
        print(f"✅ SUCCESS")
        print(f"   - Count: {result.get('count', 0)} records")
        if result.get("predictions"):
            print(f"   - Sample: {result['predictions'][0]}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

    print("")


async def test_rag_tool():
    """RagTool 테스트"""
    print("=" * 60)
    print("[TEST 2] RagTool - 문서 검색")
    print("=" * 60)

    tool = RagTool()

    # Schema 확인
    schema = tool.get_schema()
    print(f"✅ Tool Name: {schema['function']['name']}")
    print(f"✅ Description: {schema['function']['description'][:80]}...")
    print(f"✅ Parameters: {list(schema['function']['parameters']['properties'].keys())}")
    print("")

    # 실행 테스트
    print("🔄 Executing: rag_search(query='고독사 예방 정책', top_k=3)")
    result = await tool.execute({
        "query": "고독사 예방 정책",
        "top_k": 3
    })

    if result.get("success"):
        print(f"✅ SUCCESS")
        print(f"   - Count: {result.get('count', 0)} documents")
        if result.get("documents"):
            doc = result["documents"][0]
            print(f"   - Top document (rank {doc['rank']}): {doc['content'][:100]}...")
            print(f"   - Score: {doc['score']}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        if "VectorDB not initialized" in result.get("error", ""):
            print("\n   ℹ️ 이것은 예상된 동작입니다.")
            print("   VectorDB는 서버 시작 시에만 초기화됩니다.")
            print("   서버 실행 후 E2E 테스트(test_mcp_e2e.py)에서 확인하세요.")
            print("   서버 실행: cd C:\\project_belong && python -m uvicorn inference_server.main:app --reload")

    print("")


async def test_prediction_tool():
    """PredictionTool 테스트"""
    print("=" * 60)
    print("[TEST 3] PredictionTool - 예측 실행")
    print("=" * 60)

    tool = PredictionTool()

    # Schema 확인
    schema = tool.get_schema()
    print(f"✅ Tool Name: {schema['function']['name']}")
    print(f"✅ Description: {schema['function']['description'][:80]}...")
    print(f"✅ Parameters: {list(schema['function']['parameters']['properties'].keys())}")
    print("")

    # 실행 테스트
    print("🔄 Executing: prediction(region='송파구', year=2026)")
    result = await tool.execute({
        "region": "송파구",
        "year": 2026
    })

    if result.get("success"):
        print(f"✅ SUCCESS")
        print(f"   - Region: {result.get('region')}")
        print(f"   - Year: {result.get('year')}")
        print(f"   - Prediction: {result.get('prediction')}")
        print(f"   - Source: {result.get('source')}")
        print(f"   - Trend: {result.get('trend')}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

    print("")


async def test_tool_call_detection():
    """Tool Call 감지 로직 테스트"""
    print("=" * 60)
    print("[TEST 4] Tool Call Detection")
    print("=" * 60)

    from inference_server.services.generate import _detect_tool_calls

    # Test Case 1: [TOOL_CALL] 태그 형식
    response1 = """
    [TOOL_CALL]
    {
      "name": "database_query",
      "arguments": {
        "regions": ["강남구"],
        "years": [2024]
      }
    }
    [/TOOL_CALL]
    """

    tool_calls1 = _detect_tool_calls(response1)
    print(f"Test Case 1 (Tagged JSON): Detected {len(tool_calls1)} tool call(s)")
    if tool_calls1:
        print(f"   ✅ {tool_calls1[0]}")
    else:
        print(f"   ❌ No tool calls detected")

    # Test Case 2: 여러 Tool Call
    response2 = """
    [TOOL_CALL]{"name": "rag_search", "arguments": {"query": "정책", "top_k": 3}}[/TOOL_CALL]

    [TOOL_CALL]{"name": "database_query", "arguments": {"regions": ["서초구"], "years": [2024]}}[/TOOL_CALL]
    """

    tool_calls2 = _detect_tool_calls(response2)
    print(f"\nTest Case 2 (Multiple): Detected {len(tool_calls2)} tool call(s)")
    if len(tool_calls2) == 2:
        print(f"   ✅ Correct! Found {tool_calls2[0]['name']} and {tool_calls2[1]['name']}")
    else:
        print(f"   ❌ Expected 2, got {len(tool_calls2)}")

    # Test Case 3: 순수 JSON (태그 없음)
    response3 = '{"name": "prediction", "arguments": {"region": "강남구", "year": 2025}}'

    tool_calls3 = _detect_tool_calls(response3)
    print(f"\nTest Case 3 (Pure JSON): Detected {len(tool_calls3)} tool call(s)")
    if tool_calls3:
        print(f"   ✅ {tool_calls3[0]}")
    else:
        print(f"   ❌ No tool calls detected")

    # Test Case 4: 일반 텍스트 (Tool Call 없음)
    response4 = "강남구의 2024년 고독사 예측은 약 123건입니다."

    tool_calls4 = _detect_tool_calls(response4)
    print(f"\nTest Case 4 (No Tool Call): Detected {len(tool_calls4)} tool call(s)")
    if len(tool_calls4) == 0:
        print(f"   ✅ Correct! No false positives")
    else:
        print(f"   ❌ False positive detected")

    print("")


async def test_mcp_server():
    """MCP Server 통합 테스트"""
    print("=" * 60)
    print("[TEST 5] MCP Server Integration")
    print("=" * 60)

    try:
        from inference_server.mcp import BelongMCPServer

        server = BelongMCPServer()
        print(f"✅ MCP Server 초기화 성공")

        # 사용 가능한 Tool 목록
        tools = server.get_available_tools()
        print(f"✅ Available Tools: {tools}")

        # Tool Schema 확인
        schemas = server.get_tool_schemas_for_llm()
        print(f"✅ Tool Schemas: {len(schemas)} tools registered")

        # Tool 호출 테스트
        if DATABASE_URL:
            print("\n🔄 Testing tool execution via MCP Server...")
            result = await server.call_tool(
                "database_query",
                {"regions": ["강남구"], "years": [2024]}
            )
            if result.get("success"):
                print(f"   ✅ Tool execution successful")
            else:
                print(f"   ❌ Tool execution failed: {result.get('error')}")
        else:
            print("\n⚠️ Skipping tool execution test (no DATABASE_URL)")

    except Exception as e:
        print(f"❌ MCP Server 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    print("")


async def main():
    """모든 테스트 실행"""
    print("\n")
    print("🚀 MCP Tool 단위 테스트 시작")
    print("=" * 60)
    print("")

    start_time = asyncio.get_event_loop().time()

    # 각 테스트 실행
    await test_database_tool()
    await test_rag_tool()
    await test_prediction_tool()
    await test_tool_call_detection()
    await test_mcp_server()

    end_time = asyncio.get_event_loop().time()
    elapsed = end_time - start_time

    print("=" * 60)
    print(f"✅ 모든 테스트 완료! (소요 시간: {elapsed:.2f}초)")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
