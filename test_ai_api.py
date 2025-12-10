# test_ai_api.py
import requests

BASE = "http://127.0.0.1:5000"

def test_sentiment():
    url = f"{BASE}/api/ai/sentiment"
    payload = {
        "text": "오늘 하루 너무 힘들었어",
        "options": {}
    }
    resp = requests.post(url, json=payload)
    print("### /api/ai/sentiment")
    print("status:", resp.status_code)
    print("body:", resp.json())

def test_entities():
    url = f"{BASE}/api/ai/entities"
    payload = {
        "text": "삼성전자는 수원에 본사를 두고 있다.",
        "options": {}
    }
    resp = requests.post(url, json=payload)
    print("### /api/ai/entities")
    print("status:", resp.status_code)
    print("body:", resp.json())

def test_qa():
    url = f"{BASE}/api/ai/qa"
    payload = {
        "text": "서울은 어디에 위치해 있나요?",
        "options": {
            "context": "서울은 대한민국의 수도이자 특별시로, 한반도 중앙에 위치해 있다."
        }
    }
    resp = requests.post(url, json=payload)
    print("### /api/ai/qa")
    print("status:", resp.status_code)
    print("body:", resp.json())

def test_chat():
    print("\n### /api/chat/ask 1 (이름 알려주기)")
    url = f"{BASE}/api/chat/ask"
    payload = {
        "user_id": 1,
        "service": "chat",
        "text": "내 이름은 상엽이야",
        "options": {}
    }
    resp = requests.post(url, json=payload)
    print("status:", resp.status_code)
    try:
        print("body:", resp.json())
    except Exception:
        print("raw text:", resp.text)

    print("\n### /api/chat/ask 2 (다시 물어보기)")
    payload = {
        "user_id": 2,
        "service": "qa",
        "text": "내가 누구라고?",
        "options": {}
    }
    resp = requests.post(url, json=payload)
    print("status:", resp.status_code)
    try:
        print("body:", resp.json())
    except Exception:
        print("raw text:", resp.text)

def test_chat_history():
    print("\n### /api/chat/history/1")
    url = f"{BASE}/api/chat/history/1"
    resp = requests.get(url)
    print("status:", resp.status_code)
    print("body:", resp.json())


if __name__ == "__main__":
    test_sentiment()
    test_entities()
    test_qa()
    test_chat()
    test_chat_history()

