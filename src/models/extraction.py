"""
추출 결과 데이터 모델.

소스로부터 추출된 개별 기사 및 추출 결과를 타입 안전하게 표현합니다.
"""
from pydantic import BaseModel
from typing import Callable, List, Optional


class ExtractedItem(BaseModel):
    """소스에서 추출된 단일 기사/포스트를 나타내는 데이터 모델.

    Attributes:
        title: 기사 제목
        url: 원본 URL
        canonical_url: 정규화된 URL (중복 검사용)
        snippet: 짧은 요약/발췌
        published_at: 게시 일시
        source_name: 소스 이름
        source_type: 소스 유형 (rss_item, hn_listing 등)
        fetch_mode: 가져오기 모드 ("snippet" 또는 "full")
        raw_content: 원본 콘텐츠 (full-fetch 시)
    """
    title: str
    url: str
    canonical_url: Optional[str] = None
    snippet: Optional[str] = None
    published_at: Optional[str] = None
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    fetch_mode: str = "snippet"
    raw_content: Optional[str] = None


class ExtractionResult(BaseModel):
    """추출 엔진의 실행 결과를 담는 데이터 모델.

    Attributes:
        success: 추출 성공 여부
        items: 추출된 아이템 목록 (목록형 소스)
        content: 단일 페이지 원본 콘텐츠 (레거시 호환)
        title: 단일 페이지 제목 (레거시 호환)
        url: 단일 페이지 URL (레거시 호환)
        error: 실패 시 에러 메시지
        used_engine: 사용된 추출 엔진 이름
    """
    success: bool
    items: List[ExtractedItem] = []
    content: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    used_engine: Optional[str] = None


# 추출 엔진 함수의 타입 별칭
ExtractorFunc = Callable[[str], ExtractionResult]
