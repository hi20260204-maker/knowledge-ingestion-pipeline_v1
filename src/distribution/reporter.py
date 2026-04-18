import os
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DOCS_DIR = "docs"

def generate_markdown_archive(groups: List[Any], metrics: Dict[str, int] = None):
    """
    Generate a daily archive markdown file.
    Aggregates all processed articles for the day with support for multiple URLs.
    Handles 'Zero-data' scenarios gracefully.
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
        # Overwrite mode ('w') for a clean daily snapshot
        with open(file_path, "w", encoding="utf-8") as f:
            # Header and metrics are now written once per file creation
            f.write(f"# IT Knowledge Ingestion Report - {date_str}\n\n")
            
            if metrics:
                f.write("### 📊 Today's Pipeline Metrics\n")
                f.write(f"- **Sources Processed:** {metrics.get('source_count', 0)}\n")
                f.write(f"- **Total Items Extracted:** {metrics.get('item_extracted_count', 0)}\n")
                f.write(f"- **Full-fetch Success:** {metrics.get('item_full_fetched_count', 0)}\n")
                f.write(f"- **New/Updated (Saved):** {metrics.get('stored_new', 0) + metrics.get('stored_updated', 0)}\n")
                f.write(f"- **Duplicates Skipped:** {metrics.get('item_duplicate_count', 0)}\n")
                f.write(f"- **Low Quality/Parse Failed:** {metrics.get('item_low_quality_count', 0) + metrics.get('item_parse_failed_count', 0)}\n")
                f.write(f"- **Summary Reused:** {metrics.get('reused_summary', 0)}\n\n")
                f.write("---\n\n")

            if not groups:
                if metrics and metrics.get('fetched', 0) == 0:
                    f.write("> ⚠️ **Status: Data Ingestion Failed.** No sources could be reached. Please check connectivity.\n\n")
                else:
                    f.write("> ✅ **Status: Current Snapshot is empty or all items filtered.**\n\n")
                return

            for item in groups:
                # Safe attribute extraction for both GroupedReportItem (object) and dict
                if hasattr(item, 'title'):
                    title = item.title
                    summary = item.summary
                    score = item.score
                    reason = getattr(item, 'reason', '일반 기술 소식')
                    urls = item.urls
                else:
                    title = item.get('title')
                    summary = item.get('summary')
                    score = item.get('score')
                    reason = item.get('reason', '일반 기술 소식')
                    urls = item.get('urls', [item.get('url')]) if item.get('urls') else ([item.get('url')] if item.get('url') else [])
                
                f.write(f"## {title}\n")
                f.write(f"- **Importance:** {score}/10 ({reason})\n")
                f.write("- **Sources:**\n")
                for url in urls:
                    f.write(f"  - {url}\n")
                f.write(f"- **Summary:** {summary}\n\n")
        
        logger.info(f"Successfully archived {len(groups)} items to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to write markdown archive: {str(e)}")
