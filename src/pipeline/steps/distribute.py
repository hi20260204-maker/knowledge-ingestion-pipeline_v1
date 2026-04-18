"""
파이프라인 Step 5: 리포트 생성 및 알림 발송.

DB에서 당일 데이터를 조회하여 Markdown 리포트를 생성하고,
Discord 웹훅으로 알림을 발송합니다.
"""
import os
from datetime import datetime
from src.config.settings import DB_PATH
from src.db.client import get_daily_summary
from src.processor.aggregator import aggregate_items
from src.distribution.reporter import generate_markdown_archive
from src.distribution.discord_notifier import send_daily_digest
from src.pipeline.metrics import PipelineMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def distribute_results(metrics: PipelineMetrics) -> None:
    """당일 결과를 기반으로 리포트 생성 및 Discord 알림을 발송합니다.

    1. DB에서 당일 아티클 + 요약 데이터 조회
    2. 토픽별 그룹화
    3. Markdown 리포트 생성
    4. Discord 웹훅으로 알림 발송

    Args:
        metrics: 파이프라인 메트릭 (리포트 통계에 사용)
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Generating high-intelligence report for: {today_str}")

    metrics_dict = metrics.to_dict()
    latest_daily_items = get_daily_summary(DB_PATH, today_str)

    if latest_daily_items:
        # 토픽별 그룹화 후 Markdown 리포트 생성
        grouped_items = aggregate_items(latest_daily_items)
        generate_markdown_archive(grouped_items, metrics_dict)

        # Discord 알림 발송
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if webhook_url:
            logger.info("Sending Intelligent Daily Digest to Discord...")
            send_daily_digest(webhook_url, today_str, latest_daily_items, metrics_dict)
    elif metrics.fetched > 0:
        # 데이터 없음 - 빈 리포트 생성
        generate_markdown_archive([], metrics_dict)

        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if webhook_url:
            send_daily_digest(webhook_url, today_str, [], metrics_dict)
