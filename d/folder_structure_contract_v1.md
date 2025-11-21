# 6. 프로젝트 폴더 구조 계약 (Folder Structure Contract – V1)

## 6-1. 전체 폴더 구조 (최종 확정)

```
project_belong/
 ├ app.py
 ├ config.py
 ├ requirements.txt
 ├ dataset/
 │    ├ raw/
 │    ├ processed/
 │    └ merged_dataset.csv
 ├ mock/
 │    ├ population.json
 │    ├ correlation.json
 │    └ forecast_jongno.json
 ├ belong/
 │    ├ __init__.py
 │    ├ web/
 │    │    ├ __init__.py
 │    │    ├ api/
 │    │    │    ├ __init__.py
 │    │    │    └ routes.py
 │    │    ├ templates/
 │    │    │    ├ base.html
 │    │    │    ├ dashboard.html
 │    │    │    ├ region_detail.html
 │    │    │    └ correlation.html
 │    │    └ static/
 │    │         ├ css/
 │    │         ├ js/
 │    │         └ img/
 │    ├ services/
 │    │    ├ __init__.py
 │    │    ├ population_service.py
 │    │    ├ forecast_service.py
 │    │    └ correlation_service.py
 │    ├ repositories/
 │    │    ├ __init__.py
 │    │    ├ population_repository.py
 │    │    ├ forecast_repository.py
 │    │    └ correlation_repository.py
 │    ├ ml/
 │    │    ├ __init__.py
 │    │    ├ preprocess.py
 │    │    ├ correlation.py
 │    │    ├ forecast.py
 │    │    └ forecast_v1.pkl
 │    └ utils/
 │         ├ __init__.py
 │         └ helpers.py
 ├ docs/
 │    ├ project_scope_v1.md
 │    ├ ui_contract_v1.md
 │    ├ domain_contract_v1.md
 │    ├ api_contract_v1.md
 │    └ mock_api_contract_v1.md
 └ tests/
      ├ test_population_api.py
      ├ test_forecast_api.py
      └ test_correlation_api.py
```

---

## 6-2. 폴더별 역할 정의

### 📁 belong/web  
Flask 기반 웹 모듈 전체.

### api/  
- API 라우트 정의  
- URL → Service Layer 호출 구조 유지

### templates/  
- 화면 템플릿(Jinja2)  
- dashboard.html, region_detail.html, correlation.html

### static/  
- CSS, JS, 이미지 리소스

---

## 6-3. services  
Service Layer — 비즈니스 로직 처리  
- Repository + ML 모듈 조합  
- 데이터 가공 및 검증 담당  

---

## 6-4. repositories  
Repository Layer — 데이터 접근 계층  
- CSV 읽기  
- ML 모델(pkl) 로딩  
- (추후) DB 연결  

---

## 6-5. ml  
ML/데이터 분석 레이어  
- preprocess.py → raw → merged_dataset.csv  
- correlation.py → 상관분석 처리  
- forecast.py → 예측 모델 호출  
- forecast_v1.pkl → 모델 파일  

---

## 6-6. mock  
Mock API JSON 파일 저장 폴더  
- 프론트 개발용  

---

## 6-7. dataset  
데이터 정제 및 처리 파일 저장  
- raw: KOSIS 원본  
- processed: 전처리 후 파일  
- merged_dataset.csv: 최종 마스터 데이터  

---

## 6-8. docs  
협업 계약 문서 저장 폴더  

---

## 6-9. tests  
pytest 기반 백엔드 단위 테스트  
- test_population_api.py  
- test_forecast_api.py  
- test_correlation_api.py  

---

## 6-10. 개발 규칙

- 레이어 구조(service/repository/ml/web)는 반드시 유지  
- ML 파일은 belong/ml 안에만 위치  
- raw 데이터는 절대 API에서 직접 읽지 않음  
- Mock과 실제 API는 프론트에서 쉽게 전환 가능해야 함  
- 신규 기능 추가 시 폴더 구조에 맞춰 파일 생성  
