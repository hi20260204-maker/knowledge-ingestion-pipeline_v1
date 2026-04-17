import requests
import logging
from typing import List

logger = logging.getLogger(__name__)

def send_discord_notification(webhook_url: str, title: str, summary: str, url: str, score: int, keywords: List[str]) -> bool:
    """
    Sends a Rich Embed card to a Discord Webhook.
    """
    if not webhook_url:
        logger.error("Failed to send notification: Webhook URL is missing.")
        raise ValueError("Discord Webhook URL is missing")
        
    embed = {
        "title": title,
        "url": url,
        "color": 3447003, # Blueish tint
        "description": f"**Importance Score: {score}/10**\n\n{summary}\n\n**Keywords:** {' '.join(keywords)}",
        "footer": {
            "text": "IT Knowledge Ingestion Pipeline"
        }
    }
    
    payload = {
        "embeds": [embed]
    }
    
    try:
        logger.info(f"Dispatching Discord notification for '{title}'")
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            logger.info("Discord notification sent successfully.")
            return True
        else:
            logger.error(f"Discord API returned status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to post to Discord webhook: {str(e)}")
        return False
