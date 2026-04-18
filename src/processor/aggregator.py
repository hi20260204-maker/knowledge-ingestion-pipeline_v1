from typing import List, Dict, Any, Optional

class GroupedReportItem:
    def __init__(self, content_hash: str, title: str, summary: str, 
                 global_score: float, personalized_score: float, 
                 reason: str, topic: str, tags: List[str], status: str):
        self.content_hash = content_hash
        self.title = title
        self.summary = summary
        self.global_score = global_score
        self.personalized_score = personalized_score
        self.reason = reason
        self.topic = topic
        self.tags = tags
        self.status = status # NEW, UPDATED
        self.urls = []

    def add_url(self, url: str):
        if url not in self.urls:
            self.urls.append(url)

def aggregate_items(items: List[Dict[str, Any]]) -> List[GroupedReportItem]:
    """
    Deduplicates and enriches items. Maps DB status to report status.
    Filters out REPEAT items implicitly by only processing items passed from the pipeline.
    """
    groups: Dict[str, GroupedReportItem] = {}
    
    for item in items:
        c_hash = item['content_hash']
        if c_hash not in groups:
            # Map DB status to UI tags
            status_tag = "NEW"
            if item.get('status') == "UPDATED":
                status_tag = "UPDATED"
            elif item.get('status') == "SUMMARY_REUSED":
                # If content is same but it was triggered, it's usually REPEAT. 
                # But here we assume pipeline handles filtering, so we mark as NEW if it reached here.
                status_tag = "NEW"

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

def group_by_topic(items: List[GroupedReportItem]) -> Dict[str, List[GroupedReportItem]]:
    """
    Groups items by topic and sorts them hierarchically.
    1. Topics are sorted by the highest personalized_score item within them.
    2. Items within topics are sorted by personalized_score DESC, then global_score DESC.
    """
    topic_groups: Dict[str, List[GroupedReportItem]] = {}
    
    for item in items:
        topic = item.topic
        if topic not in topic_groups:
            topic_groups[topic] = []
        topic_groups[topic].append(item)
        
    # Sort items within each topic
    for topic in topic_groups:
        topic_groups[topic].sort(key=lambda x: (x.personalized_score, x.global_score), reverse=True)
        
    # Sort the dictionary (topics) by the max personalized score of its best item
    sorted_topics = sorted(
        topic_groups.items(), 
        key=lambda x: max(item.personalized_score for item in x[1]), 
        reverse=True
    )
    
    return dict(sorted_topics)
