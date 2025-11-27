from typing import List, Optional

from belong.models.region import Region


class RegionRepository:
    """REGION 마스터 테이블 조회용 Repository"""

    def get_all(self) -> List[Region]:
        """모든 구 목록 조회"""
        return Region.query.order_by(Region.id).all()

    def get_by_id(self, region_id: int) -> Optional[Region]:
        """ID로 1개 구 조회"""
        return Region.query.get(region_id)

    def get_by_code(self, code: str) -> Optional[Region]:
        """행정 코드(또는 우리가 정한 region_code)로 1개 구 조회"""
        return Region.query.filter_by(code=code).one_or_none()

    def get_by_name(self, name: str) -> Optional[Region]:
        """'강남구' 같은 이름으로 조회하고 싶을 때"""
        return Region.query.filter_by(name=name).one_or_none()
