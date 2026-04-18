import os
import sys
import logging
import requests
import time

# Ensure src is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import List, Dict, Any
from src.config.parser import load_sources
from src.extractor.fallback_engine import (
    perform_extraction, engine_rss_itemized, engine_hn_listing, 
    engine_reddit_listing, engine_rss_fallback, ExtractedItem
)
from src.processor.hasher import generate_url_hash, generate_content_hash, normalize_url, normalize_content
from src.db.client import (
    init_db, check_duplicate, save_article, save_summary, 
    find_latest_article_id, find_reusable_summary, CURRENT_SUMMARY_VERSION
)
from src.processor.scorer import Scorer
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "knowledge.db"
SCHEMA_PATH = os.path.join("src", "db", "schema.sql")
QUALITY_THRESHOLD_CHARS = 200

def should_full_fetch(item: ExtractedItem) -> bool:
    """Decide whether to perform a secondary fetch for full content."""
    blog_domains = [
        "ai.meta.com", "blog.research.google", "techcrunch.com", 
        "bytebytego.com", "developers.openai.com", "anthropic.com",
        "github.blog", "nvidia.com", "theverge.com"
    ]
    if any(domain in item.url for domain in blog_domains):
        return True
    if not item.snippet or len(item.snippet) < 150:
        return True
    return False

def run_pipeline():
    metrics = {
        'source_count': 0,
        'item_extracted_count': 0,
        'item_full_fetched_count': 0,
        'item_duplicate_count': 0,
        'item_low_quality_count': 0,
        'item_parse_failed_count': 0,
        'fetched': 0,
        'stored_new': 0,
        'stored_updated': 0,
        'reused_summary': 0,
        'errors': 0
    }
    
    if not os.path.exists(DB_PATH):
        logger.info("Initializing database...")
        init_db(DB_PATH, SCHEMA_PATH)
    
    sources = load_sources("sources.yaml")
    metrics['source_count'] = len(sources)
    logger.info(f"Loaded {len(sources)} sources.")
    
    # Engines and Scorer ordered by specificity
    extraction_engines = [
        engine_rss_itemized, 
        engine_hn_listing, 
        engine_reddit_listing, 
        engine_rss_fallback
    ]
    scorer = Scorer()

    # 3. Process Each Source
    for source in sources:
        logger.info(f"Processing source: {source.id} ({source.url})")
        extraction_result = perform_extraction(source.url, extraction_engines)
        metrics['fetched'] += 1
        
        if not extraction_result.success:
            logger.error(f"Failed to extract from {source.url}: {extraction_result.error}")
            metrics['errors'] += 1
            continue
            
        items = extraction_result.items
        if not items and extraction_result.content:
            items = [ExtractedItem(
                title=extraction_result.title or f"Article from {source.id}",
                url=extraction_result.url or source.url,
                raw_content=extraction_result.content,
                source_name=source.id,
                source_type="legacy_fallback",
                fetch_mode="full"
            )]
        
        metrics['item_extracted_count'] += len(items)

        for item in items:
            try:
                item.canonical_url = item.canonical_url or normalize_url(item.url)
                url_hash = generate_url_hash(item.url)
                
                # Preliminary duplicate check to avoid unnecessary full-fetching
                initial_content = item.raw_content or item.snippet or ""
                if check_duplicate(DB_PATH, url_hash, generate_content_hash(initial_content)):
                    metrics['item_duplicate_count'] += 1
                    continue

                if item.fetch_mode == "snippet" and should_full_fetch(item):
                    logger.info(f"Enriching item via full-fetch: {item.title}")
                    try:
                        time.sleep(0.5) # Simple rate limiting
                        resp = requests.get(item.url, timeout=10, headers={"User-Agent": "Knowledge-Bot/1.0"})
                        resp.raise_for_status()
                        item.raw_content = resp.text[:20000]
                        item.fetch_mode = "full"
                        metrics['item_full_fetched_count'] += 1
                    except Exception as fe:
                        logger.warning(f"Full-fetch failed for {item.url}, using snippet: {fe}")
                        metrics['item_parse_failed_count'] += 1

                final_content = item.raw_content or item.snippet or ""
                normalized_text = normalize_content(final_content)
                content_hash = generate_content_hash(final_content)
                
                if check_duplicate(DB_PATH, url_hash, content_hash):
                    metrics['item_duplicate_count'] += 1
                    continue

                status = "NEW"
                if len(normalized_text) < QUALITY_THRESHOLD_CHARS:
                    status = "LOW_QUALITY"
                    metrics['item_low_quality_count'] += 1
                else:
                    parent_id = find_latest_article_id(DB_PATH, url_hash)
                    if parent_id:
                        status = "UPDATED"

                article_data = {
                    'source_id': source.id,
                    'raw_url': item.url,
                    'canonical_url': item.canonical_url,
                    'title': item.title,
                    'url_hash': url_hash,
                    'content_hash': content_hash,
                    'raw_content': final_content,
                    'status': status,
                    'parent_id': parent_id if status == "UPDATED" else None
                }
                
                article_id = save_article(DB_PATH, article_data)
                if status == "NEW": metrics['stored_new'] += 1
                elif status == "UPDATED": metrics['stored_updated'] += 1

                if status in ["NEW", "UPDATED"]:
                    summary_data = find_reusable_summary(DB_PATH, content_hash)
                    if not summary_data:
                        from src.llm.summarizer import summarize_content
                        try:
                            # 1. Extract Signals from LLM
                            llm_signals = summarize_content(final_content, fetch_mode=item.fetch_mode)
                            
                            # 2. Logic-based Scoring
                            metadata = {
                                "source_weight": source.source_weight,
                                "fetch_mode": item.fetch_mode
                            }
                            scoring_result = scorer.calculate_score(llm_signals.dict(), metadata)
                            
                            summary_data = {
                                'importance_score': scoring_result['importance_score'],
                                'importance_reason': scoring_result['importance_reason'],
                                'summary': llm_signals.summary,
                                'key_points': llm_signals.key_points,
                                'keywords': llm_signals.topics # Mapping topics to keywords for legacy DB support
                            }
                        except Exception as e:
                            logger.error(f"Summarization/Scoring failed for {item.url}: {e}")
                            summary_data = {
                                'importance_score': 5,
                                'importance_reason': "Analysis error fallback",
                                'summary': "Summary bypass (No API Key or Error)",
                                'key_points': [], 'keywords': []
                            }
                    metrics['reused_summary'] += 1 if find_reusable_summary(DB_PATH, content_hash) else 0
                    save_summary(DB_PATH, article_id, summary_data)
                    
            except Exception as e:
                logger.error(f"Error processing item {item.url}: {e}")
                metrics['errors'] += 1

    # 9. Final Report & Aggregation (Task 3 / Phase 1 Improvement)
    logger.info("--- Pipeline Execution Summary ---")
    for k, v in metrics.items():
        logger.info(f"{k.replace('_', ' ').title()}: {v}")
        
    if metrics['stored_new'] == 0 and metrics['stored_updated'] == 0:
        if metrics['fetched'] > 0:
            logger.info("Pipeline completed successfully, but no new/updated data found (All duplicates or low quality).")
        else:
            logger.error("Pipeline finished with 0 fetches. Check connectivity or sources.yaml.")

    # 10. Trigger Distribution (Phase 1: DB-driven snapshots)
    from src.processor.aggregator import aggregate_items
    from src.distribution.reporter import generate_markdown_archive
    from datetime import datetime
    from src.db.client import get_daily_summary
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Generating consolidated daily report for: {today_str}")
    
    # Query the database for the definitive unique set of today's successes
    latest_daily_items = get_daily_summary(DB_PATH, today_str)
    
    if latest_daily_items:
        # Group similar items by content_hash (Still useful for multi-source content)
        grouped_items = aggregate_items(latest_daily_items)
        generate_markdown_archive(grouped_items, metrics)
    elif metrics['fetched'] > 0:
        # Zero-data reporting (Passing metrics even when 0 items, to show status)
        generate_markdown_archive([], metrics)

    logger.info("Pipeline execution completed.")

if __name__ == "__main__":
    run_pipeline()
