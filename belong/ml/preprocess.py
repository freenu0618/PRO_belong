import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent[3]
#__file__: 현재 실행 중인 파일(예: preprocess.py)의 파일 경로 문자열.
#.resolve(): 심볼릭 링크나 상대경로가 있을 경우, 절대경로로 변환.
#.parent: 디렉터리의 바로 상위 폴더.

RAW_DIR = BASE_DIR / "dataset" / "raw_data"
PROCESSED_DIR = BASE_DIR / "dataset"


def load_raw_files():
    # TODO : 각 파일 로드
    pass

def build_merged_dataset():
    '''
    raw 폴더의 여러 데이터들을 읽어서
    merged_datatset.csv를 만드는 메인 함수 
    구현 준비중
    '''
    pass


if __name__ == "__main__":
    build_merged_dataset()
