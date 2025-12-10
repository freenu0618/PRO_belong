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

if __name__ == "__main__":
    test_sentiment()
    test_entities()
    test_qa()
