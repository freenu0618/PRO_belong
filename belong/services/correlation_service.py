import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from belong.extensions import db
from belong.models.feature_stats import ElderlyStats  # :contentReference[oaicite:3]{index=3}

from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


# ---- 분석에 사용할 컬럼 정의 (ORM 속성명 기준) ----
FEATURE_COLUMNS: List[str] = [
    "single_household_ratio",  # 1인가구 비율
    "aging_index",             # 고령화 지수
    "cpi_index",               # 소비자 물가
    "age_65_over",             # 65세 이상 노인 수
    "single_house_total",      # 1인 가구 수
]

TARGET_COLUMN: str = "elderly_population"  # 타깃 컬럼 (현재는 노인 인구 수)


FEATURE_DESC: Dict[str, str] = {
    "single_household_ratio": "1인가구 비율",
    "aging_index": "고령화 지수",
    "cpi_index": "소비자 물가",
    "age_65_over": "65세 이상 노인 수",
    "single_house_total": "1인 가구 수",
}


class CorrelationService:
    """
    ELDERLY_STATS 테이블 기반 상관관계 + VIF + 선형회귀 분석 서비스.

    - 기존: 피어슨 상관계수만 계산
    - 변경: 피어슨 상관계수 + VIF 기반 컬럼 선택 + 표준화 선형회귀 계수까지 제공

    기본 타깃은 elderly_population(노인 인구 수)이고,
    FEATURE_COLUMNS에 정의된 피처를 대상으로 분석한다.
    """

    def __init__(self, session: Optional[Session] = None):
        # 세션 주입 가능하게 만들어두면 나중에 테스트/DI에 유리함
        self.session: Session = session or db.session

    # ------------------------------------------------------------------
    # 내부: DB → pandas.DataFrame 로딩
    # ------------------------------------------------------------------
    def _load_dataframe(
        self,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        region_ids: Optional[List[int]] = None,
    ) -> Optional[pd.DataFrame]:
        """
        ELDERLY_STATS에서 필요한 행들을 조회해서 pandas.DataFrame으로 변환.

        year_from/year_to, region_ids 로 간단한 필터링을 할 수 있게 해놨지만,
        지금 API에서는 파라미터 없이 전체 기간을 대상으로 사용해도 됨.
        """
        query = self.session.query(ElderlyStats)  # :contentReference[oaicite:4]{index=4}

        if year_from is not None:
            query = query.filter(ElderlyStats.year >= year_from)
        if year_to is not None:
            query = query.filter(ElderlyStats.year <= year_to)
        if region_ids:
            query = query.filter(ElderlyStats.region_id.in_(region_ids))

        rows: List[ElderlyStats] = query.all()
        if not rows:
            return None

        records: List[Dict[str, Any]] = []
        for r in rows:
            # ORM 속성명 기준으로 dict 구성
            record: Dict[str, Any] = {
                TARGET_COLUMN: getattr(r, TARGET_COLUMN, None),
            }
            for col in FEATURE_COLUMNS:
                record[col] = getattr(r, col, None)
            records.append(record)

        df = pd.DataFrame(records)
        if df.empty:
            return None
        return df

    # ------------------------------------------------------------------
    # 내부: 숫자 컬럼 정리
    # ------------------------------------------------------------------
    @staticmethod
    def _prepare_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        타깃 + 피처 컬럼을 float로 변환하고 NaN 포함 행 제거.
        """
        numeric_columns: List[str] = [TARGET_COLUMN] + FEATURE_COLUMNS
        df = df.copy()

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=[c for c in numeric_columns if c in df.columns])
        return df

    # ------------------------------------------------------------------
    # 내부: VIF 계산 관련
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
        """
        주어진 DataFrame과 feature 컬럼 리스트에 대해 VIF 계산.
        반환: {컬럼명: VIF 값}
        """
        if not feature_cols:
            return {}

        X = df[feature_cols].astype(float).values
        vifs: Dict[str, float] = {}

        for i, col in enumerate(feature_cols):
            try:
                v = variance_inflation_factor(X, i)
                vifs[col] = float(round(v, 4))
            except Exception as e:
                # 완전히 상수인 컬럼 등에서 에러 나는 경우 방어
                print(f"[CorrelationService] VIF computation failed for {col}: {e}")
                vifs[col] = float("nan")

        return vifs

    @classmethod
    def _select_features_by_vif(
        cls,
        df: pd.DataFrame,
        candidate_features: List[str],
        threshold: float = 10.0,
    ) -> (List[str], Dict[str, float]):
        """
        VIF가 threshold보다 큰 컬럼을 하나씩 제거하면서
        다중공선성이 줄어든 feature 리스트를 반환.
        """
        remaining = [c for c in candidate_features if c in df.columns]
        if len(remaining) <= 1:
            # 1개 이하면 선택 과정 의미 없음
            final_vifs = cls._compute_vif(df, remaining) if remaining else {}
            return remaining, final_vifs

        while True:
            vifs = cls._compute_vif(df, remaining)
            # NaN 제거
            valid_vifs = {k: v for k, v in vifs.items() if not np.isnan(v)}

            if not valid_vifs or len(valid_vifs) <= 1:
                # 더 이상 판단할 수 없으면 종료
                final_vifs = vifs
                break

            # 가장 VIF가 큰 컬럼 찾기
            worst_feature = max(valid_vifs, key=valid_vifs.get)
            worst_vif = valid_vifs[worst_feature]

            if worst_vif <= threshold or len(remaining) <= 1:
                # 기준 이하면 여기서 종료
                final_vifs = vifs
                break

            # 아니면 가장 큰 애를 제거
            print(f"[CorrelationService] drop {worst_feature} (VIF={worst_vif:.2f})")
            remaining.remove(worst_feature)

        # 마지막 보정
        if not remaining:
            remaining = [c for c in candidate_features if c in df.columns]
            final_vifs = cls._compute_vif(df, remaining)
        else:
            # 위 while에서 vifs를 계산했지만, 남은 컬럼 기준으로 다시 한 번 계산
            final_vifs = cls._compute_vif(df, remaining)

        return remaining, final_vifs

    # ------------------------------------------------------------------
    # 내부: 표준화 선형회귀 계수 계산
    # ------------------------------------------------------------------
    @staticmethod
    def _fit_standardized_regression(
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
    ) -> Dict[str, float]:
        """
        feature_cols에 대해:
          1) X, y 표준화
          2) LinearRegression 학습
          3) 표준화된 회귀 계수 반환 ({컬럼명: coef_std})
        """
        if not feature_cols or target_col not in df.columns:
            return {}

        X = df[feature_cols].astype(float).values
        y = df[target_col].astype(float).values.reshape(-1, 1)

        if X.shape[0] <= 1:
            return {}

        x_scaler = StandardScaler()
        y_scaler = StandardScaler()

        X_scaled = x_scaler.fit_transform(X)
        y_scaled = y_scaler.fit_transform(y).ravel()

        model = LinearRegression()
        model.fit(X_scaled, y_scaled)

        coef_std = model.coef_  # 각 feature에 대응되는 표준화 계수

        return {
            col: float(round(c, 4))
            for col, c in zip(feature_cols, coef_std)
        }

    # ------------------------------------------------------------------
    # 외부: 상관계수 + VIF + 회귀계수 계산 메인 메서드
    # ------------------------------------------------------------------
    def compute(
        self,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        region_ids: Optional[List[int]] = None,
        vif_threshold: float = 10.0,
    ) -> Dict[str, Any]:
        """
        상관 + VIF + 선형회귀 계수를 모두 계산한 결과를 반환.

        1. ELDERLY_STATS에서 필요한 행들을 조회해서 DataFrame으로 로드
        2. 타깃 컬럼 + 피처 컬럼들을 숫자형(float)으로 강제 변환
        3. NaN 포함된 행 제거
        4. 피어슨 상관계수 계산
        5. VIF 기준으로 컬럼 선택 (threshold 기본 10.0)
        6. 선택된 컬럼들로 표준화 선형회귀 계수 계산
        7. JSON 형태로 반환

        반환 구조 예시:

        {
          "target": "elderly_population",
          "vif_threshold": 10.0,
          "features": [
            {
              "feature": "single_household_ratio",
              "label": "1인가구 비율",
              "corr": 0.82,
              "vif": 2.31,
              "coef_std": 0.55,
              "selected": true
            },
            ...
          ],
          "correlations": [
            {"feature": "single_household_ratio", "corr": 0.82},
            ...
          ],
          "feature_desc": { ... }
        }
        """
        # 1) 데이터 로드
        raw_df = self._load_dataframe(
            year_from=year_from,
            year_to=year_to,
            region_ids=region_ids,
        )

        if raw_df is None:
            return {
                "target": TARGET_COLUMN,
                "vif_threshold": vif_threshold,
                "features": [],
                "correlations": [],
                "feature_desc": FEATURE_DESC,
            }

        # 2) 숫자 컬럼 정리
        df = self._prepare_numeric_df(raw_df)

        if df.empty or TARGET_COLUMN not in df.columns:
            return {
                "target": TARGET_COLUMN,
                "vif_threshold": vif_threshold,
                "features": [],
                "correlations": [],
                "feature_desc": FEATURE_DESC,
            }

        # 실제로 존재하는 피처만 사용
        candidate_features = [c for c in FEATURE_COLUMNS if c in df.columns]
        if not candidate_features:
            return {
                "target": TARGET_COLUMN,
                "vif_threshold": vif_threshold,
                "features": [],
                "correlations": [],
                "feature_desc": FEATURE_DESC,
            }

        # 3) 피어슨 상관계수 계산
        numeric_cols = [TARGET_COLUMN] + candidate_features
        corr_matrix = df[numeric_cols].corr(numeric_only=True)
        target_corr_series = corr_matrix[TARGET_COLUMN].dropna()

        corr_map: Dict[str, float] = {}
        for col in candidate_features:
            val = target_corr_series.get(col, np.nan)
            if not np.isnan(val):
                corr_map[col] = float(round(val, 4))

        # 4) VIF 기반 컬럼 선택
        selected_features, vif_values = self._select_features_by_vif(
            df,
            candidate_features=candidate_features,
            threshold=vif_threshold,
        )

        # 5) 선택된 컬럼들로 표준화 선형회귀 계수 계산
        coef_std_map = self._fit_standardized_regression(
            df,
            feature_cols=selected_features,
            target_col=TARGET_COLUMN,
        )

        # 6) feature별 상세 정보 구성
        feature_items: List[Dict[str, Any]] = []
        for col in candidate_features:
            feature_items.append({
                "feature": col,
                "label": FEATURE_DESC.get(col, col),
                "corr": corr_map.get(col),
                "vif": vif_values.get(col) if vif_values else None,
                "coef_std": coef_std_map.get(col),
                "selected": col in selected_features,
            })

        # selected + 계수 기준으로 정렬 (selected 먼저, 그 안에서는 |coef_std| 큰 순)
        feature_items.sort(
            key=lambda x: (
                not x["selected"],
                0 if x["coef_std"] is None else -abs(x["coef_std"]),
            )
        )

        # 7) 기존 구조와 호환되는 correlations 리스트 (corr만 모아서 제공)
        correlations_list: List[Dict[str, Any]] = [
            {"feature": f["feature"], "corr": f["corr"]}
            for f in sorted(
                feature_items,
                key=lambda x: 0 if x["corr"] is None else -abs(x["corr"] or 0.0),
            )
        ]

        return {
            "target": TARGET_COLUMN,
            "vif_threshold": vif_threshold,
            "features": feature_items,
            "correlations": correlations_list,
            "feature_desc": FEATURE_DESC,
        }
