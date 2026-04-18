"""
Discord 웹훅 알림 모듈.

당일 분석 결과를 Discord Embed 형식으로 발송합니다.
G1+P2 선별 로직으로 상위 기사를 하이라이트합니다.
"""
import requests
from typing import List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


def send_daily_digest(webhook_url: str, date_str: str,
                      articles: List[Dict[str, Any]],
                      metrics: Dict[str, Any]) -> bool:
    """일일 지능형 다이제스트를 Discord로 발송합니다.

    선별 로직 (G1 + P2):
    - Global Score 1위: 🔥 기술적으로 가장 중요한 기사
    - Personalized Score 상위 2건: 🎯 개인 관심사 기반 추천
    - 나머지 4~10위: 📊 컴팩트 목록

    Args:
        webhook_url: Discord 웹훅 URL
        date_str: 리포트 날짜 (YYYY-MM-DD)
        articles: DB에서 조회된 기사 목록
        metrics: 파이프라인 실행 통계

    Returns:
        발송 성공 여부
    """
    if not webhook_url:
        logger.warning("Discord Webhook URL missing. Skipping digest notification.")
        return False

    # 1. G1 + P2 선별
    top_3 = _select_top_articles(articles)

    # 4~10위 (Personalized 순위 기반)
    top_3_ids = {a.get('id') for a in top_3}
    personal_sorted = sorted(articles, key=lambda x: x.get('personalized_score', 0), reverse=True)
    list_items = [a for a in personal_sorted if a.get('id') not in top_3_ids][:7]

    # 2. Discord Embed 필드 구성
    fields = _build_highlight_fields(top_3)
    fields += _build_trend_fields(list_items)

    # 3. 최종 Embed 조립 및 발송
    report_url = f"https://github.com/hi20260204-maker/knowledge-ingestion-pipeline/blob/main/docs/report_{date_str}.md"
    embed = {
        "title": f"🚀 Daily IT Knowledge Digest - {date_str}",
        "color": 15158332,
        "description": (
            f"**Execution Summary**\n"
            f"📊 Sources: {metrics.get('source_count', 0)} | Extracted: {metrics.get('fetched', 0)}\n"
            f"🔗 [오늘 전체 {metrics.get('fetched', 0)}건 보기 (Topics별 정리됨)]({report_url})\n"
        ),
        "fields": fields,
        "footer": {"text": "Powered by Antigravity Intelligent Pipeline"}
    }

    try:
        response = requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        logger.error(f"Failed to send Daily Digest: {e}")
        return False


def _select_top_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """G1(Global 1위) + P2(Personal 상위 2건)를 선별합니다.

    Args:
        articles: 전체 기사 목록

    Returns:
        선별된 최대 3건의 기사 목록
    """
    global_sorted = sorted(articles, key=lambda x: x.get('global_score', 0), reverse=True)
    personal_sorted = sorted(articles, key=lambda x: x.get('personalized_score', 0), reverse=True)

    top_3 = []
    if global_sorted:
        g1 = global_sorted[0]
        top_3.append(g1)

        # G1을 제외한 Personal 상위 2건 추가
        p_count = 0
        for p_art in personal_sorted:
            if p_art.get('id') != g1.get('id'):
                top_3.append(p_art)
                p_count += 1
            if p_count >= 2:
                break

    return top_3


def _build_highlight_fields(top_articles: List[Dict[str, Any]]) -> List[Dict]:
    """상위 3건의 상세 하이라이트 필드를 구성합니다.

    Args:
        top_articles: 상위 기사 목록 (최대 3건)

    Returns:
        Discord Embed 필드 목록
    """
    fields = []
    for i, art in enumerate(top_articles):
        icon = "🔥" if i == 0 else "🎯"
        score = int(round(art.get('personalized_score', 0)))
        fields.append({
            "name": f"{icon} [{score}%] {art.get('title')}",
            "value": f"{art.get('summary', '')[:130]}...\n[Read More]({art.get('url')})",
            "inline": False
        })
    return fields


def _build_trend_fields(list_items: List[Dict[str, Any]]) -> List[Dict]:
    """4~10위 트렌드 컴팩트 목록 필드를 구성합니다.

    Args:
        list_items: 4~10위 기사 목록

    Returns:
        Discord Embed 필드 목록 (1건의 통합 필드)
    """
    if not list_items:
        return []

    list_text = ""
    for art in list_items:
        tag = art.get('tags', ['news'])[0] if art.get('tags') else 'news'
        score = int(round(art.get('personalized_score', 0)))
        list_text += f"- `[{tag}]` {art.get('title')} ({score}%)\n"

    return [{
        "name": "📊 Today's Other Trends (Top 4-10)",
        "value": list_text[:1024],
        "inline": False
    }]
