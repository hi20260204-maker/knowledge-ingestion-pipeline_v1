import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse
from src.processor.aggregator import GroupedReportItem, group_by_topic

logger = logging.getLogger(__name__)

DOCS_DIR = "docs"

def generate_markdown_archive(items: List[GroupedReportItem], metrics: Dict[str, Any] = None):
    """
    Generates a high-quality, topic-grouped markdown report.
    - Groups items by Topic.
    - Sorts topics and items by personalized scores.
    - Visualizes [NEW]/[UPDATED] status.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(DOCS_DIR, exist_ok=True)
    filename = os.path.join(DOCS_DIR, f"report_{date_str}.md")
    
    # 1. Group items by topic
    topic_groups = group_by_topic(items)
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🚀 IT Knowledge Digest - {date_str}\n\n")
            
            if metrics:
                f.write("### 📊 Pipeline Statistics\n")
                f.write(f"- **Sources Processed:** {metrics.get('source_count', 0)}\n")
                f.write(f"- **Total Extracted:** {metrics.get('fetched', 0)}\n")
                f.write(f"- **New Articles:** {metrics.get('stored_new', 0)}\n")
                f.write(f"- **Updates Found:** {metrics.get('stored_updated', 0)}\n")
                f.write(f"- **Noise Filtered:** {metrics.get('item_low_quality_count', 0)}\n\n")
                f.write("---\n\n")

            if not topic_groups:
                f.write("> 📭 **오늘의 새로운 소식이 없습니다.** 내일을 기대해 주세요!\n")
                return

            total_items_count = sum(len(g) for g in topic_groups.values())
            f.write(f"현재 총 **{total_items_count}건**의 선별된 기술 소식이 토픽별로 정리되어 있습니다.\n\n")

            for topic, group in topic_groups.items():
                f.write(f"## 📂 {topic}\n\n")
                
                for item in group:
                    status_emoji = "✨" if item.status == "NEW" else "🔄"
                    score_pct = int(round(item.personalized_score))
                    
                    f.write(f"### {status_emoji} [{item.status}] {item.title}\n")
                    f.write(f"- **Personalized Importance:** `{score_pct}%` ({item.reason})\n")
                    f.write(f"- **Technical Score:** `{int(round(item.global_score))}%` | **Tags:** {', '.join(item.tags)}\n")
                    f.write(f"- **Sources:**\n")
                    for url in item.urls:
                        f.write(f"  - [{urlparse(url).netloc}]({url})\n")
                    
                    f.write(f"\n> {item.summary}\n\n")
                
                f.write("---\n\n")

        logger.info(f"Consolidated Topic-Grouped report generated: {filename}")
    except Exception as e:
        logger.error(f"Failed to write markdown archive: {str(e)}")
