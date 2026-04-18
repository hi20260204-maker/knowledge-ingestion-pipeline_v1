"""
아이템 집계 및 그룹화 모듈.

DB에서 조회된 아이템을 콘텐츠 해시 기반으로 중복 제거하고,
토픽별로 그룹화하여 리포트 생성에 사용합니다.
"""
from typing import List, Dict, Any
from src.models import GroupedReportItem


def aggregate_items(items: List[Dict[str, Any]]) -> List[GroupedReportItem]:
    """DB 아이템 목록을 콘텐츠 해시 기반으로 중복 제거하고 GroupedReportItem으로 변환합니다.

    동일 content_hash를 가진 아이템은 하나로 합쳐지고,
    다수의 URL이 하나의 GroupedReportItem에 모입니다.

    Args:
        items: DB에서 조회된 아이템 딕셔너리 목록

    Returns:
        중복 제거된 GroupedReportItem 목록
    """
    groups: Dict[str, GroupedReportItem] = {}

    for item in items:
        c_hash = item['content_hash']
        if c_hash not in groups:
            # DB 상태를 리포트 상태 태그로 매핑
            status_tag = _map_status(item.get('status', 'NEW'))

            groups[c_hash] = GroupedReportItem(
                content_hash=c_hash,
                title=item['title'],
                summary=item['summary'],
                global_score=item.get('score', 0) if 'score' in item else item.get('global_score', 0),
                personalized_score=item.get('personalized_score', 0),
                reason=item.get('reason', '일반 기술 소식'),
                topic=item.get('keywords', ['General'])[0] if item.get('keywords') else 'General',
                tags=item.get('tags', []),
                status=status_tag
            )
        groups[c_hash].add_url(item['url'])

    return list(groups.values())


def _map_status(db_status: str) -> str:
    """DB 상태 값을 리포트 상태 태그로 매핑합니다.

    Args:
        db_status: DB의 status 필드 값

    Returns:
        리포트용 상태 태그 ("NEW" 또는 "UPDATED")
    """
    if db_status == "UPDATED":
        return "UPDATED"
    return "NEW"


def group_by_topic(items: List[GroupedReportItem]) -> Dict[str, List[GroupedReportItem]]:
    """아이템을 토픽별로 그룹화하고 점수 기준 계층적 정렬을 수행합니다.

    정렬 기준:
    1. 토픽 간: 해당 토픽의 최고 personalized_score 기준 내림차순
    2. 토픽 내: personalized_score → global_score 기준 내림차순

    Args:
        items: 그룹화할 GroupedReportItem 목록

    Returns:
        토픽명을 키로 하는 정렬된 딕셔너리
    """
    topic_groups: Dict[str, List[GroupedReportItem]] = {}

    for item in items:
        topic = item.topic
        if topic not in topic_groups:
            topic_groups[topic] = []
        topic_groups[topic].append(item)

    # 토픽 내 아이템 정렬
    for topic in topic_groups:
        topic_groups[topic].sort(key=lambda x: (x.personalized_score, x.global_score), reverse=True)

    # 토픽 간 정렬 (최고 personalized_score 기준)
    sorted_topics = sorted(
        topic_groups.items(),
        key=lambda x: max(item.personalized_score for item in x[1]),
        reverse=True
    )

    return dict(sorted_topics)
