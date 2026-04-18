import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def send_daily_digest(webhook_url: str, date_str: str, articles: List[Dict[str, Any]], metrics: Dict[str, Any]) -> bool:
    """
    Sends a consolidated summary of the daily ingestion to Discord.
    Highlights Top 3 articles.
    """
    if not webhook_url:
        logger.warning("Discord Webhook URL missing. Skipping digest notification.")
        return False
        
    top_articles = sorted(articles, key=lambda x: x.get('score', 0), reverse=True)[:3]
    
    fields = []
    for art in top_articles:
        fields.append({
            "name": f"⭐ [{art.get('score')}/10] {art.get('title')}",
            "value": f"[Read Article]({art.get('url')})\n{art.get('summary')[:150]}...",
            "inline": False
        })
        
    embed = {
        "title": f"🚀 Daily IT Knowledge Digest - {date_str}",
        "color": 15158332, # Red-ish/Orange
        "description": (
            f"**Pipeline Execution Completed!**\n"
            f"📊 Total Fetched: {metrics.get('fetched', 0)}\n"
            f"🆕 New/Updated: {metrics.get('stored_new', 0) + metrics.get('stored_updated', 0)}\n"
            f"♻️ Reused: {metrics.get('reused_summary', 0)}\n\n"
            f"--- **Top 3 Highlights** ---"
        ),
        "fields": fields,
        "footer": {
            "text": "IT Knowledge Ingestion Pipeline | Powered by Antigravity AI"
        }
    }
    
    payload = {"embeds": [embed]}
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        logger.error(f"Failed to send Daily Digest: {e}")
        return False
