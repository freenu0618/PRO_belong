# 4. API 스펙 계약 (API Contract)

## 4-1. API 공통 규약

### Base URL
```
/api/v1
```

### Response Format (공통)
성공:
```json
{
  "status": "success",
  "data": {}
}
```

실패:
```json
{
  "status": "error",
  "message": "Region not found"
}
```

### Naming 규칙
- snake_case 사용
- key 이름 변경 금지 (Contract)

### Content-Type
```
application/json; charset=utf-8
```

---

## 4-2. API 엔드포인트 목록

| 구분 | 목적 | Method | URL |
|------|--------|---------|--------|
| Population | 서울 25개 구 전체 데이터 | GET | /elderly/population |
| Forecast | 특정 구 예측 | GET | /elderly/forecast/<region> |
| Correlation | 상관관계 분석 | GET | /elderly/correlation |
| Health | 서버 상태 확인 | GET | /health |

---

## 4-3. API 상세 명세

# 1) GET /elderly/population
대시보드에서 사용.

### Response
```json
{
  "status": "success",
  "data": [
    {
      "region": "종로구",
      "latest_value": 13100,
      "values": [
        {"year": 2019, "value": 12400},
        {"year": 2020, "value": 12600},
        {"year": 2021, "value": 12850},
        {"year": 2022, "value": 12980},
        {"year": 2023, "value": 13100}
      ],
      "growth_rate": 0.031
    }
  ]
}
```

---

# 2) GET /elderly/forecast/<region>
구 상세 페이지에서 사용.

### Response
```json
{
  "status": "success",
  "data": {
    "region": "종로구",
    "history": [
      {"year": 2019, "value": 12400},
      {"year": 2020, "value": 12600},
      {"year": 2021, "value": 12850},
      {"year": 2022, "value": 12980},
      {"year": 2023, "value": 13100}
    ],
    "forecast": [
      {"year": 2024, "value": 13300},
      {"year": 2025, "value": 13430}
    ]
  }
}
```

---

# 3) GET /elderly/correlation
상관관계 분석 페이지에서 사용.

### Response
```json
{
  "status": "success",
  "data": {
    "correlations": [
      {"feature": "low_income_old", "corr": 0.72},
      {"feature": "aging_index", "corr": 0.63},
      {"feature": "welfare_facilities", "corr": -0.28},
      {"feature": "age_80_plus", "corr": 0.71}
    ],
    "feature_desc": {
      "low_income_old": "저소득 노인 수",
      "aging_index": "고령화 지수",
      "welfare_facilities": "노인 복지시설 수",
      "age_80_plus": "80세 이상 노인"
    }
  }
}
```

---

# 4) GET /health

### Response
```json
{
  "status": "ok"
}
```

---

## 4-4. 에러 스펙

### region 잘못 입력
```json
{
  "status": "error",
  "message": "region_not_found"
}
```

### 서버 오류
```json
{
  "status": "error",
  "message": "internal_server_error"
}
```

### 상관분석 오류
```json
{
  "status": "error",
  "message": "correlation_failed"
}
```
