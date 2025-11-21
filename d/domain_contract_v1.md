# 3. 데이터 구조(도메인) 계약 (Domain Contract)

## 3-1. 데이터 단위 정의

### 공간 단위
- 서울특별시 25개 구 (region_name: string, region_code: int 선택)

### 시간 단위
- 연도(year): 정수(예: 2019)

---

## 3-2. 핵심 엔티티 정의

# Entity 1: ElderlyPopulation (독거노인 인구 데이터)
| 필드명 | 타입 | 설명 |
|--------|------|-------|
| region | string | 구명 |
| year | int | 연도 |
| elderly_population | int | 독거노인 인구수 |
| growth_rate | float | 전년 대비 증가율 |
| created_at | datetime | 데이터 생성일(선택) |

---

# Entity 2: RegionStatistics (독거노인 관련 지표)
| 필드명 | 타입 | 설명 |
|--------|------|-------|
| region | string | 서울 25개 구 |
| year | int | 기준 연도 |
| solo_household | int | 1인 가구 수 |
| age_80_plus | int | 80세 이상 인구 |
| aging_index | float | 고령화지수 |
| low_income_old | int | 저소득 노인 |
| welfare_facilities | int | 노인 복지시설 |
| etc_features | ... | 확장용 |

---

## 3-3. 마스터 데이터 구조 (merged_dataset.csv)

### 필수 컬럼 목록
- region  
- year  
- elderly_population  
- solo_household  
- aging_index  
- low_income_old  
- age_80_plus  
- welfare_facilities  
- elderly_growth_rate  

### 예시

| region | year | elderly_population | aging_index | low_income_old | age_80_plus | welfare_facilities |
|--------|------|--------------------|-------------|----------------|-------------|---------------------|
| 종로구 | 2019 | 12400 | 105 | 2300 | 4800 | 12 |
| 종로구 | 2020 | 12600 | 108 | 2410 | 4900 | 12 |

---

## 3-4. 상관관계 분석용 Feature 정의

### Feature 목록
```
elderly_population
low_income_old
aging_index
welfare_facilities
age_80_plus
solo_household
```

### feature_desc
```
low_income_old: "저소득 노인 수"
aging_index: "고령화 지수"
welfare_facilities: "노인 복지시설 수"
age_80_plus: "80세 이상 노인"
solo_household: "1인 가구 수"
elderly_population: "독거노인 인구"
```

---

## 3-5. 예측 모델 입·출력 구조

### 입력
```
[year, elderly_population]
```

### 출력
```
{
  "region": "...",
  "history": [...],
  "forecast": [...]
}
```

---

## 3-6. 데이터 유효성 규칙

- region: 25개 구만 허용  
- year: 4자리 숫자  
- 값 타입: 모두 숫자 타입(Number)  

---

## 3-7. 데이터 파이프라인 규칙

1) raw 데이터 수집  
2) preprocess.py → 컬럼 정규화  
3) melt 처리로 연도 단위 row 생성  
4) ElderlyPopulation + RegionStatistics 병합  
5) merged_dataset.csv 저장  
6) correlation.py, forecast.py는 오직 이 파일만 사용  

※ raw 데이터를 API에서 직접 읽는 것은 금지  
