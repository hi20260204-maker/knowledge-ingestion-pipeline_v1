import os
import sys
import logging
from typing import List

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.config.parser import load_sources
from src.extractor.fallback_engine import perform_extraction, engine_rss_fallback
from src.processor.hasher import generate_url_hash, generate_content_hash
from src.llm.summarizer import summarize_content
from src.distribution.discord_notifier import send_discord_notification
from src.distribution.reporter import generate_markdown_archive
from src.db.client import init_db, check_duplicate, save_article, save_summary
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "knowledge.db"
SCHEMA_PATH = os.path.join("src", "db", "schema.sql")

def run_pipeline():
    # 1. Initialize DB
    if not os.path.exists(DB_PATH):
        logger.info("Initializing database...")
        init_db(DB_PATH, SCHEMA_PATH)
    
    # 2. Load Sources
    sources = load_sources("sources.yaml")
    logger.info(f"Loaded {len(sources)} sources from configuration.")
    
    processed_items = []

    # 3. Process Each Source
    for source in sources:
        logger.info(f"Processing source: {source.id} ({source.url})")
        
        # 4. Extraction
        extraction_result = perform_extraction(source.url, [engine_rss_fallback])
        
        if not extraction_result.success:
            logger.error(f"Failed to extract from {source.url}: {extraction_result.error}")
            continue
            
        # 5. Deduplication
        url_hash = generate_url_hash(source.url)
        content_hash = generate_content_hash(extraction_result.content)
        
        if check_duplicate(DB_PATH, url_hash, content_hash):
            logger.info(f"Skipping duplicate content from {source.url}")
            continue
            
        # 6. Summarization (LLM)
        try:
            summary_response = summarize_content(extraction_result.content)
        except Exception as e:
            logger.error(f"Summarization failed for {source.url}: {str(e)}")
            if not os.environ.get("OPENAI_API_KEY"):
                logger.warning("Bypassing LLM due to missing API key")
                # Dummy response for testing
                summary_response = type('obj', (object,), {
                    'importance_score': 5,
                    'summary': "Summary bypass (No API Key provided)",
                    'key_points': ["Point 1", "Point 2"],
                    'keywords': ["#Test", "#Manual"]
                })
            else:
                continue

        # 7. Save to DB
        article_data = {
            'source_id': source.id,
            'raw_url': source.url,
            'canonical_url': source.url,
            'title': extraction_result.title or f"Article from {source.id}",
            'url_hash': url_hash,
            'content_hash': content_hash,
            'raw_content': extraction_result.content
        }
        
        article_id = save_article(DB_PATH, article_data)
        
        summary_data = {
            'importance_score': summary_response.importance_score,
            'summary': summary_response.summary,
            'key_points': summary_response.key_points,
            'keywords': summary_response.keywords
        }
        
        save_summary(DB_PATH, article_id, summary_data)
        
        # Collect for archiving
        processed_items.append({
            'title': article_data['title'],
            'url': article_data['raw_url'],
            'score': summary_data['importance_score'],
            'summary': summary_data['summary']
        })

        # 8. Discord Notification
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if webhook_url:
            send_discord_notification(
                webhook_url=webhook_url,
                title=article_data['title'],
                summary=summary_data['summary'],
                url=article_data['raw_url'],
                score=summary_data['importance_score'],
                keywords=summary_data['keywords']
            )
        else:
            logger.warning("DISCORD_WEBHOOK_URL not set. Skipping notification.")

    # 9. Generate Archives
    if processed_items:
        generate_markdown_archive(processed_items)

    logger.info("Pipeline execution completed.")

if __name__ == "__main__":
    run_pipeline()

if __name__ == "__main__":
    run_pipeline()
