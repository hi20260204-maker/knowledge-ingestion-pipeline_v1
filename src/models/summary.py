"""
LLM 요약 응답 데이터 모델.

OpenAI Structured Output을 위한 Pydantic 모델을 정의합니다.
"""
from pydantic import BaseModel, Field
from typing import List


class LLMSummaryResponse(BaseModel):
    """LLM으로부터 반환되는 구조화된 요약 응답 모델.

    OpenAI의 Structured Output 기능과 함께 사용되어
    일관된 JSON 응답을 보장합니다.

    Attributes:
        summary: 3문장의 한국어 요약
        key_points: 2~5개의 핵심 기술 포인트
        topics: 감지된 기술 토픽 (LLM, Python, Rust 등)
        tags: 뉴스 성격 태그 (release, architecture, research 등)
        confidence_score: 정보 가용성 기반 신뢰도 (0.0~1.0)
    """
    summary: str = Field(..., description="A clear 3-sentence summary of the content in Korean.")
    key_points: List[str] = Field(..., description="Array of 2 to 5 key technical takeaways in Korean.")
    topics: List[str] = Field(..., description="Detected tech topics like LLM, Python, Rust, MLOps, etc.")
    tags: List[str] = Field(..., description="Nature of the news: release, architecture, research, case_study, news.")
    confidence_score: float = Field(..., description="Confidence from 0.0 to 1.0 based on information availability.")
