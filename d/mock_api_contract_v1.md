# 5. Mock API 계약 (Mock API Contract – V1)

## 5-1. Mock API 제공 목적
- 프론트가 백엔드를 기다리지 않고 UI 개발을 먼저 진행하기 위함  
- API 응답 JSON 구조(Contract)를 먼저 확정  
- 백엔드는 Mock을 기준으로 API를 정확히 개발  
- 데이터 구조 충돌 방지  
- 병렬 개발 가능

---

## 5-2. Mock API 저장 위치
```
/mock
 ├ population.json
 ├ correlation.json
 └ forecast_jongno.json
```

---

## 5-3. Mock 파일 목록 및 스펙

### 1) population.json  
→ /api/v1/elderly/population 대응 Mock

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

### 2) correlation.json  
→ /api/v1/elderly/correlation 대응 Mock

```json
{
  "status": "success",
  "data": {
    "correlations": [
      {"feature": "single_household_ratio", "corr": 0.72},
      {"feature": "aging_index", "corr": 0.63},
      {"feature": "cpi_index", "corr": -0.28},
      {"feature": "age_65_over", "corr": -0.28},
      {"feature": "single_house_total", "corr": 0.71}
    ],
    "feature_desc": {
      "single_household_ratio": "1인가구 비율",
      "aging_index": "고령화 지수",
      "cpi_index": "소비자 물가",
      "age_65_over": "65세 이상 노인",
      "single_house_total": "1인 가구 수",
    }
  }
}

---

### 3) forecast_jongno.json  
→ /api/v1/elderly/forecast/jongno 대응 Mock

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

## 5-4. Mock ↔ Real API 전환 규칙

### 개발(Mock) 모드
```
const API_BASE = "/mock";
```

### 운영(Real) 모드
```
const API_BASE = "/api/v1";
```

### 절대 규칙
- Mock JSON key와 실제 API JSON key는 **100% 동일**해야 한다  
- 타입, 구조, 배열 형태까지 완벽히 일치해야 한다

---

## 5-5. 프론트 Mock 체크리스트
- JSON 구조 정상 파싱  
- key 이름 정확한가  
- values / history / forecast 배열 구조  
- 그래프 렌더링 정상  
- null/undefined 처리  
- 페이지·탭 이동 시 데이터 정상 유지  

---

## 5-6. 백엔드 Mock 검증 체크리스트
- Mock JSON과 API Response 구조 완전 비교  
- missing key 여부  
- value 타입(number/string) 일치  
- snake_case 규칙 준수  
- region 이름 매칭  
- Swagger Schema와 일치 여부  
