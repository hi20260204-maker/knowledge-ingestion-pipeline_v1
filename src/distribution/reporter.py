import os
import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

DOCS_DIR = "docs"

def generate_markdown_archive(articles_summaries: List[dict]):
    """
    Generate a daily archive markdown file in the docs directory.
    Aggregates all processed articles for the day.
    """
    if not os.path.exists(DOCS_DIR):
        try:
            os.makedirs(DOCS_DIR)
            logger.info(f"Created directory: {DOCS_DIR}")
        except Exception as e:
            logger.error(f"Failed to create directory {DOCS_DIR}: {str(e)}")
            return
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(DOCS_DIR, f"report_{date_str}.md")
    
    try:
        # Append mode to allow incremental updates during the same day
        with open(file_path, "a", encoding="utf-8") as f:
            # If file is empty, write header
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                f.write(f"# IT Knowledge Ingestion Report - {date_str}\n\n")
            
            for item in articles_summaries:
                f.write(f"## {item['title']}\n")
                f.write(f"- **URL:** {item['url']}\n")
                f.write(f"- **Score:** {item['score']}/10\n")
                f.write(f"- **Summary:** {item['summary']}\n\n")
        
        logger.info(f"Successfully archived {len(articles_summaries)} items to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to write markdown archive: {str(e)}")
