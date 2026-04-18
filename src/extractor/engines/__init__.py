"""
추출 엔진 패키지.

각 소스 유형별 추출 엔진을 제공합니다.
외부에서는 이 패키지를 통해 모든 엔진에 접근합니다.
"""
from src.extractor.engines.rss import engine_rss_itemized, engine_rss_fallback
from src.extractor.engines.hackernews import engine_hn_listing
from src.extractor.engines.reddit import engine_reddit_listing

__all__ = [
    "engine_rss_itemized",
    "engine_rss_fallback",
    "engine_hn_listing",
    "engine_reddit_listing",
]
