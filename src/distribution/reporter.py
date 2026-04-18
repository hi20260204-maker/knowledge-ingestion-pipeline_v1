"""
Markdown 리포트 생성 모듈.

토픽별 그룹화된 기사 데이터를 Markdown 형식의 일일 아카이브로 변환합니다.
"""
import os
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse
from src.models import GroupedReportItem
from src.processor.aggregator import group_by_topic
from src.config.settings import DOCS_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_markdown_archive(items: List[GroupedReportItem], metrics: Dict[str, Any] = None):
    """토픽별로 그룹화된 Markdown 일일 리포트를 생성합니다.

    리포트 구조:
    1. 파이프라인 실행 통계 (선택)
    2. 토픽별 섹션
    3. 각 기사: 상태 태그([NEW]/[UPDATED]), 점수, 요약, 소스 링크

    Args:
        items: 토픽별 그룹화된 GroupedReportItem 목록
        metrics: 파이프라인 실행 통계 딕셔너리 (선택)
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(DOCS_DIR, exist_ok=True)
    filename = os.path.join(DOCS_DIR, f"report_{date_str}.md")

    # 토픽별 그룹화 및 정렬
    topic_groups = group_by_topic(items)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🚀 IT Knowledge Digest - {date_str}\n\n")

            # 파이프라인 통계 섹션
            if metrics:
                _write_metrics_section(f, metrics)

            if not topic_groups:
                f.write("> 📭 **오늘의 새로운 소식이 없습니다.** 내일을 기대해 주세요!\n")
                return

            total_items_count = sum(len(g) for g in topic_groups.values())
            f.write(f"현재 총 **{total_items_count}건**의 선별된 기술 소식이 토픽별로 정리되어 있습니다.\n\n")

            # 토픽별 기사 섹션
            for topic, group in topic_groups.items():
                _write_topic_section(f, topic, group)

        logger.info(f"Consolidated Topic-Grouped report generated: {filename}")
    except Exception as e:
        logger.error(f"Failed to write markdown archive: {str(e)}")


def _write_metrics_section(f, metrics: Dict[str, Any]):
    """파이프라인 실행 통계 섹션을 작성합니다.

    Args:
        f: 파일 핸들
        metrics: 통계 딕셔너리
    """
    f.write("### 📊 Pipeline Statistics\n")
    f.write(f"- **Sources Processed:** {metrics.get('source_count', 0)}\n")
    f.write(f"- **Total Extracted:** {metrics.get('fetched', 0)}\n")
    f.write(f"- **New Articles:** {metrics.get('stored_new', 0)}\n")
    f.write(f"- **Updates Found:** {metrics.get('stored_updated', 0)}\n")
    f.write(f"- **Noise Filtered:** {metrics.get('item_low_quality_count', 0)}\n\n")
    f.write("---\n\n")


def _write_topic_section(f, topic: str, group: List[GroupedReportItem]):
    """단일 토픽 섹션을 작성합니다.

    Args:
        f: 파일 핸들
        topic: 토픽명
        group: 해당 토픽의 GroupedReportItem 목록
    """
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
