"""
설정 데이터 모델.

sources.yaml의 구조를 Pydantic 모델로 정의합니다.
"""
from pydantic import BaseModel


class SourceConfig(BaseModel):
    """소스 설정 모델. sources.yaml의 각 소스 항목을 나타냅니다.

    Attributes:
        id: 소스 고유 식별자
        category: 소스 카테고리 (Sensing, Filtering, Deep Dive 등)
        url: 소스 URL
        priority: 소스 우선순위 (1~5)
        source_weight: 소스 신뢰도 가중치 (0.0~1.0)
    """
    id: str
    category: str
    url: str
    priority: int = 1
    source_weight: float = 0.0
