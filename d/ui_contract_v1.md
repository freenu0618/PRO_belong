# 2. 화면(UI) 구성 계약 (UI Contract)

## 2-1. 전체 페이지 구조
```
/dashboard
/region/<region_name>
/correlation
/error
```

---

## 2-2. 페이지 상세 정의

# 1) /dashboard — 서울 25개 구 요약 대시보드

### 목적
서울 25개 구의 독거노인 인구 현황과 증가율, 추세를 한눈에 보여주는 메인 페이지.

### 구성 요소
- 상단 Summary Bar  
  - 총 독거노인 인구  
  - 전년 대비 증가율  
  - 증가 TOP/하락 TOP 구  
- 구별 리스트 테이블  
  - 구명, 최신 인구, 증가율, 추세 미니그래프, 상세 보기  
- 미니 스파크라인 그래프  
- 상세 페이지 이동 버튼  

### 필요한 데이터(API Request)
- region  
- latest_value  
- values[] (연도-값 리스트)  
- growth_rate  

---

# 2) /region/<region_name> — 구 상세 페이지

### 목적
특정 구의 연도별 변화와 예측을 상세 분석.

### 구성 요소
- 구명 / 요약 정보(최근 증가율 등)  
- 연도별 라인 그래프(history)  
- 향후 예측 그래프(forecast)  
- 요약 인사이트 카드  

### 필요한 데이터(API Request)
- region  
- history[]  
- forecast[]  

---

# 3) /correlation — 상관관계 분석

### 목적
독거노인 인구와 변수 간 상관계수를 시각적으로 보여줌.

### 구성 요소
- 히트맵 또는 테이블  
- feature 설명 tooltip  
- 상관계수 정렬  

### 필요한 데이터(API Request)
- correlations[]  
- feature_desc{}  

---

# 4) /error — 오류 페이지
API 실패 또는 region_not_found 처리용 기본 페이지.

---

## 2-3. 디자인 가이드
- 파랑·회색 공공데이터 UI 스타일  
- 차트는 Chart.js 기본 테마  
- 카드형 레이아웃  
- 모바일 대응 V1 제외  

---

## 2-4. 페이지 이동 규칙
- /dashboard → 구 클릭 → /region/<구>  
- /region/<구> → breadcrumb or 뒤로가기  
- 상단 고정 네비게이션: Dashboard / Region / Correlation  

---

## 2-5. 이 계약의 협업 효과
- 프론트: 데이터 요구 명확  
- 백엔드: API 스펙 결정에 직접 활용  
- Mock 데이터 생성 기준 확립  
- 화면-API 충돌 방지  
- 병렬 개발 가능  
