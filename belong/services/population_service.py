import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from pandas import Series

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "ml" / "dataset"/ "merged_dataset.csv"

class PopulationService:
    '''
    연도별 값을 리스트로 저장
    [{"year": 2019, "value": 5400},...]
    결과 리스트에 가공된 dict 추가 .
    [{"region": "강남구",
      "latest_value": 5800,
      "value": [ {"year": 2017, "value": 5000},{...}],
      "growth_rate": 0.334}, {....}]
    get_summary()함수에서 DataFrame을 사용해서 지역별 요약 정보 리스트를 만들기
    실행 시점 : service = PopulationService(); service.get_summary() 이런식
    '''
    def __init__(self):
        self.df = pd.read_csv(DATA_PATH)

    def get_summary(self) -> List[Dict[str, Any]]:
        # type힌트를 붙일수 있는것들은 추가해서 붙여놨음
        result : list = [] # 리스트안에 dict으로 들어감 [{"region":강남구","latest_value"....},{강서구..}]
        for region, group in self.df.groupby("region"):
            group = group.sort_values("year")
            latest : Series = group.iloc[-1] # iloc 인덱싱 기반 마지막행 ex 강남구 마지막연도, 강서구 마지막연도
            first : Series = group.iloc[0] # iloc을 사용해 첫번째 행 ex 강남구 가장 오래된년도, 강서구 ...
            growth_rate = ((latest["elderly_population"] - first["elderly_population"])
                           / first["elderly_population"])
            #고령 인구 증가율 계산 = (최신연도 고령 인구 - 기준연도 고령 인구)
            #                     / 기준연도   EX)(5000 - 4000) /4000 = 0.25 = 25% 증가

            values : List[Dict[str, int]]= [      #해당 행의 연도                   해당 연도의 고령 인구 수
                {"year" : int(row["year"]), "value" : int(row["elderly_population"])}
                for _, row in group.iterrows() # 한 행(row)씩 (index, row) 튜플로 반환 _는 무시
            ] # group이 각 region으로 묶여있기 때문에 region은 _무시하고 year와value를 row로 빼내서 딕셔너리 안에 넣음
            result.append({"region" : region,
                           "latest_value" : int(latest["elderly_population"]),
                           "value" : values, # 위에서 만든 리스트 컴프맇핸션
                           "growth_rate" : round(float(growth_rate), 3)})
        return result


