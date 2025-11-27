# 5일 협업 업무 분장표 (2인, 백엔드 ↔ 프론트 번갈아 수행)

## 📌 요약 표

| Day | A(너) 역할 | B(팀원) 역할 |
|-----|-------------|--------------|
| 1일차 | 백엔드 세팅 + Mock 제작 | 프론트 UI 설계 + 템플릿 구조 |
| 2일차 | 프론트(Mock 기반 UI) | 데이터 정제 + ML 모델 v1 |
| 3일차 | API 3종 개발 | 상세/히트맵 화면 구현 |
| 4일차 | 프론트 실제 API 연동 | 백엔드 에러 처리 + 리팩토링 |
| 5일차 | 백엔드 안정화·배포 준비 | 프론트 최종 마감·테스트 |
3. 협업/시연을 기준으로 “표준 워크플로우”를 만들어보자

이제 앞으로를 생각해서, 우리 프로젝트 표준 흐름을 정해보자.

✅ 1) 너(메인 개발자) 쪽

모델/스키마 변경 → 코드 수정 (SQLAlchemy 모델)

flask db migrate -m "..." → 새로운 migration 파일 생성

flask db upgrade → 너의 개발 DB에 반영

코드 + migrations 폴더 같이 git commit & push

✅ 2) 팀원 쪽 (새로 시작하는 사람)

repo clone / git pull

.env 에 본인 Oracle 정보 설정

set FLASK_APP=app:create_app

flask db upgrade만 실행

init이나 migrate는 하지 않음 (그건 “새 프로젝트 시작하는 사람”이 하는 거)

그러면:

Alembic이 ALEMBIC_VERSION 테이블을 만들고

migrations 폴더 안의 revision들을 순서대로 적용해서

DB 구조를 너와 동일한 상태로 맞춰 줌

✅ 3) 시연용 환경(서버/공용 DB)

시연용 서버(또는 공용 Oracle 스키마)를 하나 잡고

그 DB에도 똑같이

코드를 배포하고

flask db upgrade 실행

그러면 그 DB도 같은 revision 상태가 되고,

팀원/너는 그냥 그 DSN으로 접속해서 시연하면 됨.
---

# 📆 상세 업무 설명

---

# **Day 1 — 프로젝트 기반 세팅 & Mock 기반 구조 잡기**

## ✔ A(너): 백엔드 역할
- Flask 프로젝트 기본 구조 생성  
- belong/web, services, repositories, ml 폴더 구성  
- dataset/raw 파일 수집  
- preprocess.py 초안  
- Mock API JSON 3종(population/correlation/forecast)

## ✔ B(팀원): 프론트 역할
- `/dashboard`, `/region/<구>`, `/correlation` Figma/초안 설계  
- base.html + 공통 템플릿 구축  
- Mock JSON fetch 테스트 코드 작성

---

# **Day 2 — 역할 변경 / 프론트 & ML 교차 경험**

## ✔ A(너): 프론트 역할
- `/dashboard` UI 구현  
- Mock 값 기반 카드 및 그래프 표시  
- API_BASE(Mock/Real) 전환 구조 설계  

## ✔ B(팀원): 백엔드 역할
- raw → processed → merged_dataset.csv 생성  
- 상관관계 분석 코드 구현  
- 예측 모델(v1) 학습 + forecast_v1.pkl 저장  

---

# **Day 3 — API 개발 + 상세 UI 확장**

## ✔ A(너): 백엔드 역할
- population_service/repository 작성  
- forecast_service(pkl 로딩)  
- correlation_service  
- `/api/v1/elderly/*` 3종 API 실제 개발  

## ✔ B(팀원): 프론트 역할
- 상세 페이지(history+forecast 그래프)  
- 상관관계 히트맵 UI  
- 네비게이션 구성  

---

# **Day 4 — Mock 제거 → 실제 API 연결**

## ✔ A(너): 프론트 역할
- 모든 페이지 Mock → Real API 연결  
- 로딩/에러 처리 추가  
- 전체 화면 데이터 정상 흐름 확인  

## ✔ B(팀원): 백엔드 역할
- API 응답 형식 검증(Mock과 완전 동일하게)  
- region validation  
- 에러 핸들러(400/404/500) 추가  
- 라우트/서비스 리팩토링  

---

# **Day 5 — 전체 통합 테스트 & 배포 준비**

## ✔ A(너): 백엔드 역할
- 서비스/레포지토리 구조 정리  
- 예측 모델 로딩 안정화  
- CORS 및 config.py 프로덕션 설정  
- 간단한 배포 준비(Dockerfile 초안 포함 가능)

## ✔ B(팀원): 프론트 역할
- UI 전체 테스트  
- 그래프/표 데이터 연결 최종 점검  
- 스타일 마감(폰트·간격·정렬)  
- Demo 페이지 완성  

---

# 🎯 최종 출력물 (5일 간)

- Flask 기반 API 3종  
- 상관관계 분석 결과  
- 예측 모델 v1(forecast_v1.pkl)  
- dashboard / region / correlation 전체 UI  
- Mock → Real API 전환 완료  
- 통합 테스트 완료  
- 시연 가능한 MVP 완성

