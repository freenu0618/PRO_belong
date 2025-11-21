# 7. 협업 규칙 계약 (Collaboration Rules Contract – V1)

## 7-1. Git 브랜치 전략 (Branch Strategy)

```
main        ← 운영(배포) 브랜치
dev         ← 개발 통합 브랜치
feature/*   ← 기능 단위 브랜치
```

### 규칙
- main 직접 수정 금지  
- 모든 개발은 feature 브랜치에서 작업  
- feature → dev → main 순서로 merge  
- PR 머지 전 최소 1회 코드 리뷰 필수  

---

## 7-2. 커밋 컨벤션 (Conventional Commits)

```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 수정
style: 포맷 변경
refactor: 기능 변화 없는 개선
test: 테스트 코드
chore: 기타 작업
```

예시:
```
feat: Add forecast service and model loader
fix: Correct region name mapping in population API
docs: Add API Contract v1
```

---

## 7-3. 네이밍 규칙

### 파일/폴더: snake_case  
### 클래스명: PascalCase  
### JSON 응답 키: snake_case  
### ML 변수명: snake_case  
### HTML/CSS class: kebab-case

---

## 7-4. 협업 프로세스 규칙

### 기능 개발 순서
1) UI 설계  
2) API 요구 데이터 추출  
3) Mock API 제작  
4) 프론트: Mock 기반 UI 개발  
5) 백엔드: 실제 API 개발  
6) Mock → Real API 전환  
7) 통합 테스트  

### API 스펙 변경 규칙
- key 이름/구조/타입 변경 금지  
- 새 key 추가는 허용(기존 유지 필수)  

### ML 모델 변경 규칙
- forecast_v1.pkl → forecast_v2.pkl  
- API 구조 동일 유지  

### PR 리뷰 절차
1) feature 브랜치 작업  
2) dev로 PR  
3) 팀원 리뷰 후 merge  

---

## 7-5. 역할 분배 계약

### A (너)
- 데이터 정제/통합  
- 상관관계 분석  
- 예측 모델 v1 개발  
- API 3종 개발  
- Repository/Service 구조  
- Flask 설정  
- Mock API 제공  
- 통합 테스트  

### B (팀원)
- UI 설계  
- dashboard / region / correlation 화면  
- Mock 기반 그래프/표 구현  
- API 연동  
- 에러/로딩 처리  
- 화면 품질 개선  

---

## 7-6. 변경 관리 규칙
- 코드 변경 전 문서(contract) 먼저 수정  
- 문서 없이 코드 수정 금지  
- Contract 변경은 팀원 모두 동의  

---

## 7-7. 협업 규칙 목적
- 충돌 없는 개발  
- 일정 지연 최소화  
- 코드 품질 유지  
- 팀 간 의사소통 비용 절감  
