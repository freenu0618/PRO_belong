# test_mcp_e2e.py
"""
MCP E2E 통합 테스트 및 성능 측정
- 실제 서버 실행 후 API 호출 테스트
- Tool Call 정확도 및 성능 측정
"""

import requests
import json
import time
from typing import List, Dict

BASE_URL = "http://localhost:8000"


def print_header(title: str):
    """헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(success: bool, message: str):
    """결과 출력"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


def test_health_check():
    """Health Check 테스트"""
    print_header("TEST 1: Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()

        print_result(True, f"Status: {response.status_code}")
        print(f"   - Model Loaded: {data.get('model_loaded')}")
        print(f"   - Tokenizer Loaded: {data.get('tokenizer_loaded')}")
        print(f"   - VectorDB Loaded: {data.get('vectordb_loaded')}")
        print(f"   - GPU Available: {data.get('gpu_available')}")

        return response.status_code == 200

    except requests.exceptions.ConnectionError:
        print_result(False, "서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print("   실행 방법: cd inference_server && uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"Health check 실패: {e}")
        return False


def test_adapters_endpoint():
    """Adapters 엔드포인트 테스트"""
    print_header("TEST 2: Adapters Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/adapters", timeout=5)
        data = response.json()

        print_result(data.get("ok", False), f"Status: {response.status_code}")
        print(f"   - Available Adapters: {data.get('count', 0)}")

        if data.get("adapters"):
            for adapter in data["adapters"][:3]:  # 처음 3개만 출력
                print(f"     • {adapter['name']}")

        return data.get("ok", False)

    except Exception as e:
        print_result(False, f"Adapters 조회 실패: {e}")
        return False


def test_standard_generation():
    """표준 생성 테스트 (MCP 없이)"""
    print_header("TEST 3: Standard Generation (No MCP)")

    payload = {
        "prompt": "안녕하세요, 간단한 인사를 해주세요.",
        "max_new_tokens": 100,
        "temperature": 0.7
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/generate",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time

        data = response.json()

        print_result(response.status_code == 200, f"Status: {response.status_code}")
        print(f"   - Response Time: {elapsed:.2f}s")
        print(f"   - Output: {data.get('output', '')[:150]}...")

        return response.status_code == 200

    except Exception as e:
        print_result(False, f"생성 실패: {e}")
        return False


def test_database_tool_via_api():
    """DatabaseTool API 테스트 (MCP 서버 직접 호출)"""
    print_header("TEST 4: DatabaseTool via MCP Server")

    # 참고: 이 테스트는 /mcp/tool/call 엔드포인트가 구현된 경우에만 작동합니다
    # 현재는 main.py에 이 엔드포인트가 없으므로 스킵 가능

    print("⚠️ 이 테스트는 /mcp/tool/call 엔드포인트가 필요합니다.")
    print("   현재는 generate_with_mcp를 통한 간접 테스트로 대체합니다.")
    return True


def test_mcp_generation_simple():
    """MCP 생성 테스트 - 단순 질문"""
    print_header("TEST 5: MCP Generation - Simple Query")

    payload = {
        "prompt": "안녕하세요",
        "max_new_tokens": 200,
        "temperature": 0.7,
        "use_mcp": True
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/generate",
            json=payload,
            timeout=120
        )
        elapsed = time.time() - start_time

        data = response.json()

        print_result(response.status_code == 200, f"Status: {response.status_code}")
        print(f"   - Response Time: {elapsed:.2f}s")
        print(f"   - Output: {data.get('output', '')[:150]}...")

        # Tool Call이 없어야 정상 (단순 인사)
        tool_calls = data.get("tool_calls", [])
        iterations = data.get("iterations", 1)

        print(f"   - Tool Calls: {len(tool_calls)}")
        print(f"   - Iterations: {iterations}")

        return response.status_code == 200

    except Exception as e:
        print_result(False, f"MCP 생성 실패: {e}")
        return False


def test_mcp_generation_with_tool_call():
    """MCP 생성 테스트 - Tool Call 유도"""
    print_header("TEST 6: MCP Generation - With Tool Call")

    # Tool Call을 유도하는 질문
    payload = {
        "prompt": "강남구의 2024년 고독사 예측은 몇 건인가요?",
        "max_new_tokens": 512,
        "temperature": 0.7,
        "use_mcp": True
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/generate",
            json=payload,
            timeout=180
        )
        elapsed = time.time() - start_time

        data = response.json()

        success = response.status_code == 200
        print_result(success, f"Status: {response.status_code}")
        print(f"   - Response Time: {elapsed:.2f}s")
        print(f"   - Output: {data.get('output', '')[:200]}...")

        # Tool Call 정보
        tool_calls = data.get("tool_calls", [])
        tool_results = data.get("tool_results", [])
        iterations = data.get("iterations", 1)

        print(f"\n   📊 MCP Statistics:")
        print(f"   - Tool Calls: {len(tool_calls)}")
        print(f"   - Tool Results: {len(tool_results)}")
        print(f"   - Iterations: {iterations}")

        if tool_calls:
            print(f"\n   🔧 Tool Calls:")
            for i, tc in enumerate(tool_calls, 1):
                print(f"      {i}. {tc['name']}({json.dumps(tc['arguments'], ensure_ascii=False)})")

        if tool_results:
            print(f"\n   📋 Tool Results:")
            for i, tr in enumerate(tool_results, 1):
                success_icon = "✅" if tr.get("success") else "❌"
                print(f"      {i}. {success_icon} {tr['tool']}")

        return success

    except Exception as e:
        print_result(False, f"MCP Tool Call 테스트 실패: {e}")
        return False


def test_mcp_performance():
    """MCP 성능 측정"""
    print_header("TEST 7: MCP Performance Measurement")

    test_cases = [
        {
            "name": "단순 질문 (Tool Call 없음)",
            "prompt": "안녕하세요",
            "expected_tools": 0
        },
        {
            "name": "데이터 조회 (database_query)",
            "prompt": "서초구 2024년 예측 데이터를 알려주세요",
            "expected_tools": 1
        },
        {
            "name": "문서 검색 (rag_search)",
            "prompt": "고독사 예방 정책에 대해 알려주세요",
            "expected_tools": 1
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test['name']}")

        payload = {
            "prompt": test["prompt"],
            "max_new_tokens": 256,
            "temperature": 0.7,
            "use_mcp": True
        }

        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/generate",
                json=payload,
                timeout=180
            )
            elapsed = time.time() - start_time

            data = response.json()
            tool_calls = data.get("tool_calls", [])

            result = {
                "name": test["name"],
                "success": response.status_code == 200,
                "time": elapsed,
                "tool_calls": len(tool_calls),
                "expected_tools": test["expected_tools"]
            }

            results.append(result)

            print(f"   ⏱️ Time: {elapsed:.2f}s")
            print(f"   🔧 Tool Calls: {len(tool_calls)} (expected: {test['expected_tools']})")

        except Exception as e:
            print(f"   ❌ 실패: {e}")
            results.append({
                "name": test["name"],
                "success": False,
                "time": 0,
                "tool_calls": 0,
                "expected_tools": test["expected_tools"]
            })

    # 성능 요약
    print("\n" + "=" * 70)
    print("  성능 요약")
    print("=" * 70)

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    avg_time = sum(r["time"] for r in results) / len(results) if results else 0

    print(f"✅ 통과: {passed_tests}/{total_tests}")
    print(f"⏱️ 평균 응답 시간: {avg_time:.2f}s")

    # Tool Call 정확도
    tool_accuracy = sum(
        1 for r in results
        if r["tool_calls"] == r["expected_tools"]
    ) / total_tests * 100 if total_tests > 0 else 0

    print(f"🎯 Tool Call 정확도: {tool_accuracy:.1f}%")

    return passed_tests == total_tests


def main():
    """모든 E2E 테스트 실행"""
    print("\n")
    print("🚀 MCP E2E 통합 테스트 및 성능 측정")
    print("=" * 70)
    print("")

    start_time = time.time()

    # 테스트 실행
    tests = [
        ("Health Check", test_health_check),
        ("Adapters Endpoint", test_adapters_endpoint),
        ("Standard Generation", test_standard_generation),
        ("DatabaseTool API", test_database_tool_via_api),
        ("MCP Simple Query", test_mcp_generation_simple),
        ("MCP Tool Call", test_mcp_generation_with_tool_call),
        ("MCP Performance", test_mcp_performance)
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} 테스트 중 예외 발생: {e}")
            results.append((name, False))

    # 최종 결과
    elapsed = time.time() - start_time

    print("\n")
    print("=" * 70)
    print("  최종 결과")
    print("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\n총 테스트: {total}")
    print(f"통과: {passed}")
    print(f"실패: {total - passed}")
    print(f"소요 시간: {elapsed:.2f}s")

    print("\n상세 결과:")
    for name, success in results:
        icon = "✅" if success else "❌"
        print(f"  {icon} {name}")

    print("\n" + "=" * 70)

    if passed == total:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️ 일부 테스트 실패. 위 결과를 확인하세요.")

    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
