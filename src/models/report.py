"""
리포트 데이터 모델.

토픽별 그룹화된 기사 정보를 담는 리포트 아이템을 정의합니다.
"""
from typing import List


class GroupedReportItem:
    """토픽별 그룹화된 리포트 아이템.

    동일 콘텐츠의 여러 URL을 하나로 묶고,
    리포트/디스코드 출력에 필요한 메타데이터를 보관합니다.

    Attributes:
        content_hash: 콘텐츠 해시 (그룹핑 키)
        title: 기사 제목
        summary: 요약 텍스트
        global_score: 기술적 중요도 점수 (0-100)
        personalized_score: 개인화 관심도 점수 (0-100)
        reason: 점수 산정 이유
        topic: 주요 토픽
        tags: 성격 태그 목록
        status: 상태 태그 (NEW, UPDATED)
        urls: 관련 URL 목록
    """

    def __init__(self, content_hash: str, title: str, summary: str,
                 global_score: float, personalized_score: float,
                 reason: str, topic: str, tags: List[str], status: str):
        """GroupedReportItem을 초기화합니다."""
        self.content_hash = content_hash
        self.title = title
        self.summary = summary
        self.global_score = global_score
        self.personalized_score = personalized_score
        self.reason = reason
        self.topic = topic
        self.tags = tags
        self.status = status
        self.urls = []

    def add_url(self, url: str):
        """중복되지 않는 URL을 목록에 추가합니다."""
        if url not in self.urls:
            self.urls.append(url)
