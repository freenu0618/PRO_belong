## 📌 작업 개요 (Summary)

> 이번 PR이 무엇을 해결하거나 추가하는지 한 줄 요약

- 예: "백엔드 프로젝트 초기 설정 및 API 구조 세팅"


---

## 🔧 변경 사항 (Changes)

- [ ] 새로운 기능 추가 (Feature)
- [ ] 버그 수정 (Fix)
- [ ] 문서 업데이트 (Docs)
- [ ] 리팩토링 (Refactor)
- [ ] 테스트 추가 / 수정 (Test)
- [ ] 프로젝트 구조 변경
- [ ] 기타

### 상세 내용

- Flask 프로젝트 구조 정리
- Blueprint 적용
- `/api/v1/health` 헬스체크 엔드포인트 추가
- dataset 폴더 구조 정의 및 `preprocess.py` skeleton 작성


---

## 🧪 테스트 결과 (Test Result)

- [ ] 로컬 실행 검증
- [ ] API 요청 테스트 완료
- [ ] 기존 기능에 영향 없음 확인
- [ ] 테스트 코드 포함됨 (선택)

**테스트 방법:**

python -m belong.app
GET /api/v1/health → response: {"status": "ok"}

yaml
코드 복사

---

## 🎯 관련 이슈 (Linked Issues)

> 있으면 아래 형식으로 자동으로 Close 처리됨  
예: `Closes #21` 또는 `Related to #15`

- 관련 이슈: `Closes #___`


---

## 🤔 참고 사항 (Notes)

- 리뷰 전에 확인해야 할 내용이나 논의할 사항
- 설계 방향, 추가 질문, 개선해야 할 포인트 등

예:

> dataset 기준 경로 재정의 필요 — Day2 회의에서 논의 예정


---

## 👤 리뷰어 체크리스트 (Reviewer Checklist)

리뷰어는 아래 항목 체크 후 Approve

- [ ] 브랜치 네이밍 규칙 준수 (`feature/XXX`, `fix/XXX`, etc.)
- [ ] 코딩 컨벤션 준수
- [ ] 기능 정상 작동 확인
- [ ] 파일 구조 적절성 확인
- [ ] 변경된 코드 이해 가능한 수준인지 확인
- [ ] 테스트 케이스/수동 테스트 포함 여부 확인