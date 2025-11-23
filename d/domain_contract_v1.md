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
| 필드명                | 타입 | 설명        |
|--------------------|------|-----------|
| region             | string | 서울 25개 구  |
| year               | int | 기준 연도     |
| solo_household     | int | 1인 가구 수   |
| age_65_plus         | int | 65세 이상 인구 |
| aging_index        | float | 고령화지수     |
| low_income_old     | int | 저소득 노인    |
| welfare_facilities | int | 노인 복지시설   |
| etc_features       | ... | 확장용       |

---

## 3-3. 마스터 데이터 구조 (merged_dataset.csv)

### 필수 컬럼 목록
- region  
- year  
- elderly_population  
- solo_household  
- aging_index  
- low_income_old  
- age_65_plus  
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
age_65_plus
solo_household
```

### feature_desc
```
low_income_old: "저소득 노인 수"
aging_index: "고령화 지수"
welfare_facilities: "노인 복지시설 수"
age_65_plus: "65세 이상 노인"
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


## 추가 컬럼 
 "구": "region",
    "연도": "year",

    # 주거 유형 (계 = total)
    "단독주택_계": "single_house_total",
    "아파트_계": "apartment_total",
    "연립주택_계": "row_house_total",
    "다세대주택_계": "multi_house_total",
    "비주거용 건물내 주택_계": "non_residential_housing_total",

    # Target (값 → 모델 예측값 또는 고독사 값이라면 아래 중 선택)
    # → 데이터 정의 확정 필요
    "값": "target_value",

    # 인구 지표
    "총인구": "population_total",
    "총인구_남자": "population_male",
    "총인구_여자": "population_female",

    # 연령 구조
    "20세 미만": "under_20",
    "65세 이상": "age_65_over",
    "0~14세": "age_0_14",

    # 1인가구 관련
    "1인가구_비율": "single_household_ratio",

    # 경제/환경 지표
    "소비자물가": "cpi_index",  # Consumer Price Index

    # 노령화 지표
    "노령화지수": "aging_index",

    # 변화율 관련
    "전년 대비 증감": "population_change_count",
    "증감률": "population_growth_ratio",

    # 저소득 노인 비율
    "저소득노인_65~79비율": "low_income_elderly_65_79_ratio",
    "저소득노인_80이상비율": "low_income_elderly_80_over_ratio",

    # 기초생활수급자
    "기초생활수급자총인원": "basic_pension_recipient_count",
    "기초생활수급자비율": "basic_pension_recipient_ratio"
}