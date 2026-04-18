from typing import List, Dict, Any

class GroupedReportItem:
    def __init__(self, content_hash: str, title: str, summary: str, score: int):
        self.content_hash = content_hash
        self.title = title
        self.summary = summary
        self.score = score
        self.urls = []

    def add_url(self, url: str):
        if url not in self.urls:
            self.urls.append(url)

def aggregate_items(items: List[Dict[str, Any]]) -> List[GroupedReportItem]:
    """
    동일한 content_hash를 가진 항목들을 그룹화하여 '중복 압축'을 수행합니다.
    1차: Exact-match (content_hash) 기반.
    향후 확장: Semantic similarity 기반 near-duplicate 그룹화 지원 예정.
    """
    groups: Dict[str, GroupedReportItem] = {}
    
    for item in items:
        c_hash = item['content_hash']
        if c_hash not in groups:
            groups[c_hash] = GroupedReportItem(
                content_hash=c_hash,
                title=item['title'],
                summary=item['summary'],
                score=item['score']
            )
        groups[c_hash].add_url(item['url'])
        
    return list(groups.values())
