import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def send_daily_digest(webhook_url: str, date_str: str, articles: List[Dict[str, Any]], metrics: Dict[str, Any]) -> bool:
    """
    Sends a tiered, intelligent summary to Discord.
    - Top 3 (Global 1 + Personal 2) in detail.
    - Top 4-10 in compact list.
    """
    if not webhook_url:
        logger.warning("Discord Webhook URL missing. Skipping digest notification.")
        return False
        
    # 1. Selection Logic (G1 + P2)
    # Sort by global for G1, by personalized for others
    global_sorted = sorted(articles, key=lambda x: x.get('global_score', 0), reverse=True)
    personal_sorted = sorted(articles, key=lambda x: x.get('personalized_score', 0), reverse=True)
    
    top_3 = []
    if global_sorted:
        g1 = global_sorted[0]
        top_3.append(g1)
        
        # Pick 2 more from personal list, excluding g1
        p_count = 0
        for p_art in personal_sorted:
            if p_art.get('id') != g1.get('id'):
                top_3.append(p_art)
                p_count += 1
            if p_count >= 2: break
            
    # Top 4-10 (Personalized ranking)
    top_3_ids = {a.get('id') for a in top_3}
    list_items = [a for a in personal_sorted if a.get('id') not in top_3_ids][:7] # Up to 10th total
    
    # 2. Build Embed Fields
    fields = []
    # Add 상세 Highlights (Top 3)
    for i, art in enumerate(top_3):
        icon = "🔥" if i == 0 else "🎯"
        score = int(round(art.get('personalized_score', 0)))
        fields.append({
            "name": f"{icon} [{score}%] {art.get('title')}",
            "value": f"{art.get('summary', '')[:130]}...\n[Read More]({art.get('url')})",
            "inline": False
        })
        
    # Add 주요 트렌드 (4-10)
    if list_items:
        list_text = ""
        for art in list_items:
            tag = art.get('tags', ['news'])[0] if art.get('tags') else 'news'
            score = int(round(art.get('personalized_score', 0)))
            list_text += f"- `[{tag}]` {art.get('title')} ({score}%)\n"
        
        fields.append({
            "name": "📊 Today's Other Trends (Top 4-10)",
            "value": list_text[:1024], # Discord field value limit
            "inline": False
        })
        
    # 3. Final Footer & Link
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
        "footer": { "text": "Powered by Antigravity Intelligent Pipeline" }
    }
    
    try:
        response = requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        logger.error(f"Failed to send Daily Digest: {e}")
        return False
