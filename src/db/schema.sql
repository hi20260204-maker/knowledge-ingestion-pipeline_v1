CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    raw_url TEXT,
    canonical_url TEXT,
    display_url TEXT,
    title TEXT,
    url_hash TEXT,
    content_hash TEXT,
    published_at DATETIME,
    raw_content TEXT,
    clean_content TEXT
);

CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    importance_score INTEGER,
    summary_text TEXT,
    key_points TEXT,
    keywords TEXT,
    created_at DATETIME,
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS pipeline_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    target_url TEXT,
    stage TEXT,
    status TEXT,
    retry_count INTEGER DEFAULT 0,
    last_attempt DATETIME,
    error_message TEXT,
    resolved_at DATETIME,
    processing_duration_ms INTEGER
);
