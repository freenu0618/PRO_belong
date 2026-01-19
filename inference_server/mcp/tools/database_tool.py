# inference_server/mcp/tools/database_tool.py
"""DatabaseTool - PostgreSQL 데이터베이스 쿼리 도구"""

import os
import logging
import asyncio
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base import BaseTool

logger = logging.getLogger(__name__)


class DatabaseTool(BaseTool):
    """
    PostgreSQL 데이터베이스에서 고독사 예측 데이터 조회

    기능:
    - 지역별, 연도별 필터링
    - 예측 데이터 또는 과거 데이터 조회
    - belong/services/ai/db_rag.py 로직 재사용
    """

    def __init__(self):
        """DB 연결 초기화"""
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("[DatabaseTool] Initialized with DATABASE_URL")
        else:
            self.engine = None
            self.Session = None
            logger.warning("[DatabaseTool] DATABASE_URL not set")

    def get_schema(self) -> Dict[str, Any]:
        """
        Tool Schema (OpenAI Function Calling 표준 형식)

        Returns:
            {
                "type": "function",
                "function": {
                    "name": "database_query",
                    "description": "...",
                    "parameters": {...}
                }
            }
        """
        return {
            "type": "function",
            "function": {
                "name": "database_query",
                "description": (
                    "서울시 25개 구의 고독사 예측 데이터를 PostgreSQL에서 조회합니다. "
                    "지역별, 연도별 필터링이 가능하며 예측값 또는 과거 데이터를 반환합니다."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "조회할 지역명 리스트 (예: ['강남구', '서초구']). "
                                "빈 배열이면 전체 지역 조회"
                            ),
                            "maxItems": 25
                        },
                        "years": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "조회할 연도 리스트 (예: [2024, 2025])",
                            "minItems": 1,
                            "maxItems": 10
                        },
                        "data_type": {
                            "type": "string",
                            "enum": ["prediction", "history", "both"],
                            "description": (
                                "조회할 데이터 타입. "
                                "prediction=예측값, history=과거 데이터, both=둘 다"
                            ),
                            "default": "prediction"
                        }
                    },
                    "required": ["years"]
                }
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        DB 쿼리 실행 (비동기)

        Args:
            arguments: {
                "regions": ["강남구", "서초구"] (선택),
                "years": [2024, 2025] (필수),
                "data_type": "prediction" (선택)
            }

        Returns:
            {
                "success": True,
                "predictions": [
                    {"region": "강남구", "year": 2024, "prediction": 123.4},
                    ...
                ],
                "count": 2
            }
            또는
            {
                "success": False,
                "error": "에러 메시지"
            }
        """
        if not self.Session:
            logger.error("[DatabaseTool] Database connection not available")
            return {
                "success": False,
                "error": "Database connection not available. Please set DATABASE_URL"
            }

        # 인자 추출
        regions = arguments.get("regions", [])
        years = arguments.get("years", [])
        data_type = arguments.get("data_type", "prediction")

        logger.info(f"[DatabaseTool] Query: regions={regions}, years={years}, type={data_type}")

        # DB 쿼리를 별도 스레드에서 실행 (논블로킹)
        session = self.Session()
        try:
            # asyncio.to_thread: 동기 함수를 비동기로 실행
            result = await asyncio.to_thread(
                self._query_database, session, regions, years, data_type
            )

            logger.info(f"[DatabaseTool] Retrieved {len(result)} records")

            return {
                "success": True,
                "predictions": result,
                "count": len(result)
            }

        except Exception as e:
            logger.error(f"[DatabaseTool] Query failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

        finally:
            session.close()

    def _query_database(self, session, regions, years, data_type):
        """
        실제 DB 쿼리 로직 (동기)

        Args:
            session: SQLAlchemy 세션
            regions: 지역 리스트
            years: 연도 리스트
            data_type: 데이터 타입

        Returns:
            예측 데이터 리스트
        """
        # belong/services/ai/db_rag.py의 DBRagService 재사용
        from belong.services.ai.db_rag import DBRagService

        service = DBRagService(session)

        if data_type == "prediction":
            # 예측 데이터만 조회
            return service.get_prediction_data(regions, years)

        elif data_type == "history":
            # 과거 데이터만 조회
            return service.get_historical_data(regions)

        elif data_type == "both":
            # 둘 다 조회
            predictions = service.get_prediction_data(regions, years)
            history = service.get_historical_data(regions)
            return {
                "predictions": predictions,
                "history": history
            }

        else:
            raise ValueError(f"Invalid data_type: {data_type}")
