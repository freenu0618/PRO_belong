# [Project] Belong: AI 기반 독거노인 케어 및 위험 예측 플랫폼

## 1. 프로젝트 개요 (Overview)
### 1.1 기획 배경 (Background)
* **급증하는 1인 가구와 고독사:** 통계청 및 서울시 공공 데이터(2017~2023) 분석 결과, 독거노인 가구 수와 고독사 발생 건수가 비례하여 매년 급증하고 있습니다.
* **돌봄의 사각지대:** 기존 인력 중심의 방문 서비스는 야간/공휴일 등 '돌봄 공백' 시간대에 발생하는 응급 상황(낙상, 실신)에 취약합니다.
* **패러다임 전환:** 사후 처리가 아닌, 데이터와 AI를 통한 예방 시스템이 필요합니다.

### 1.2 기획 의도 (Intent)
> **"기술로 연결된 안전망 (Connected Safety Net)"**
본 프로젝트는 RAG를 이용한 AI Agent 기술과 YOLOv8을 이용한 Object Detection을 결합하여, 위험에 노출된 독거노인을 위험으로부터 예방하고 고독사 위험을 사전에 차단을 목표로 합니다.

---

## 2. 개발 목표 (Development Goals)
1.  **Hybrid AI 엔진 구축 (Cost-Effective Intelligence):** 단순 분석(감정/NER)은 경량 모델로, 심층 대화는 거대 모델(LLM)로 이원화하여 비용과 속도를 최적화합니다.
2.  **도메인 특화 LLM 엔지니어링:** Llama 3 모델을 한국어 노인 상담 데이터로 **Fine-tuning**하여 공감 능력과 문맥 이해도를 극대화합니다.
3.  **데이터 기반 위험 예측 (Data-Driven Safety):** 서울시 과거 7년 치 데이터를 머신러닝으로 분석하여 지역별 '고독사 위험 지도'를 시각화합니다.
4.  **확장 가능한 아키텍처 (Scalable Architecture):** Controller-Service-Repository 패턴을 적용하여 추후 Vision AI 및 IoT 확장에 유연한 구조를 설계합니다.

---

## 3. 사용 기술 및 경험 (Tech Stack)

| 구분 | 기술 스택 (Tech Stack) | 활용 내용 (Description) |
| :--- | :--- | :--- |
| **Backend** | Python, Flask | REST API 서버, JWT 기반 Stateless 인증 구현 |
| **Database** | Oracle, SQLAlchemy | 대용량 통계 데이터 저장 및 ORM을 통한 쿼리 최적화 |
| **AI (Generative)** | **Llama 3 (8B), Ollama** | QLoRA 기법으로 파인튜닝된 노인 케어 특화 챗봇 구현 |
| **AI (Analysis)** | **Hugging Face** | KoELECTRA(감정/개체명), T5(요약) 파이프라인 구축 |
| **Data Science** | Scikit-learn, XGBoost | 시계열 데이터 분석을 통한 위험도 예측 모델링 |
| **Infra/DevOps** | Docker | 로컬 DB 및 AI 모델 서빙 환경 컨테이너화 |

---

## 4. 핵심 기술 전략 (Technical Strategy)

### 4.1 Hybrid AI Engine Architecture
**"Right Model for the Right Task"**
모든 요청을 LLM에 보내는 비효율을 개선하기 위해 작업의 난이도에 따라 모델을 분리했습니다.
* **Fast Track (Latency < 100ms):** 감정 분석, 요약 등은 `KoELECTRA`, `T5` 등 가벼운 모델이 즉시 처리.
* **Deep Track (Context Aware):** 위로, 상담 등 맥락이 필요한 대화는 `Fine-tuned Llama 3`가 처리.

### 4.2 LLM Fine-tuning Engineering
**"Domain Adaptation with QLoRA"**
* **Problem:** Base 모델의 기계적인 말투와 한국어 뉘앙스 부족.
* **Solution:** AI Hub 노인 헬스케어 데이터셋을 활용하여 Llama 3-8B 모델을 학습. 메모리 효율을 위해 **QLoRA(4bit 양자화)** 기법 적용.
* **Deploy:** 학습된 LoRA 어댑터를 병합(Merge)하고 **GGUF 포맷**으로 변환하여 로컬 환경(Ollama)에서도 구동 가능하도록 경량화.

### 4.3 Layered Architecture
**"Separation of Concerns"**
* **Presentation Layer (`ai_route.py`):** 요청 검증 및 DTO 변환 담당.
* **Business Layer (`ai_service.py`):** AI 모델 호출 및 데이터 가공 로직 집중.
* **Data Access Layer (`forecast_repo.py`):** DB 종속성을 격리하여 유지보수성 확보.

---

## 5. 기능 명세 및 데이터 설계 (Specs & ERD)

### 5.1 주요 기능
* **심리 상담 챗봇:** 사용자의 발화를 분석하여 우울감 감지 시 위로 메시지 및 대화 유도.
* **고독사 위험 지도:** 자치구별 독거노인 비율과 고독사 수치를 Heatmap으로 시각화.
* **상담 리포트:** 보호자를 위해 노인의 주요 대화 내용과 감정 상태를 3줄 요약하여 제공.

### 5.2 ERD 설계 (핵심 구조)
* **Users:** 사용자 정보 및 권한 (Admin/User).
* **Elderly_History:** 연도별, 지역별 독거노인 현황 및 고독사 통계 (정규화).
* **Prediction_Result:** 머신러닝 모델이 예측한 미래 위험도 점수 저장.
* **Chat_Logs:** 대화 내용 및 감정 분석 점수(Sentiment Score) 기록.

---

## 6. 향후 발전 계획 (Future Roadmap)
* **Phase 1 (Intelligence):** RAG(검색 증강 생성)를 도입하여 지자체 복지 혜택 정보를 정확하게 답변하는 기능 추가.
* **Phase 2 (Vision):** **YOLOv8**을 활용하여 CCTV 영상에서 '쓰러짐(Fall Detection)'을 감지하고 즉시 신고하는 기능 개발.
* **Phase 3 (Agent):** LangChain 기반의 AI Agent가 노인의 상태를 주기적으로 체크하고 능동적으로 말을 거는 시스템 구현.

---

## 7. 프로젝트 회고 (Retrospective)
* **Keep:** 단순히 API를 연동하는 것을 넘어, 로컬 환경에서 직접 **모델 튜닝(Fine-tuning)**과 **경량화(Quantization)**를 수행하며 AI 엔지니어링 역량을 확보함. 아키텍처 설계를 통해 확장성을 고려한 개발 습관을 기름.
* **Try:** 공공 데이터의 업데이트 주기가 느려 실시간성이 부족했던 점을 보완하기 위해, 향후 실시간 웹 크롤링 파이프라인을 구축할 예정.