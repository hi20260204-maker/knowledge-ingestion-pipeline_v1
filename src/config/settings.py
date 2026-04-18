
"""
중앙 집중식 설정 관리 모듈.

프로젝트 전역에서 사용되는 경로, 상수, 환경변수 기반 설정을 관리합니다.
환경변수가 설정되어 있으면 우선 사용하고, 없으면 기본값을 적용합니다.
"""
import os

# --- 데이터베이스 설정 ---
DB_PATH = os.environ.get("DB_PATH", "knowledge.db")
SCHEMA_PATH = os.path.join("src", "db", "schema.sql")

# --- 소스 및 관심사 설정 ---
SOURCES_PATH = os.environ.get("SOURCES_PATH", "config/sources.yaml")
INTERESTS_PATH = os.environ.get("INTERESTS_PATH", "config/interests.yaml")

# --- 파이프라인 임계값 ---
QUALITY_THRESHOLD_CHARS = 200

# --- 출력 경로 ---
DOCS_DIR = "docs"

# --- Full-fetch 대상 도메인 목록 ---
# 이 도메인의 기사는 snippet만으로 부족하여 전체 본문을 가져옵니다.
FULL_FETCH_DOMAINS = [
    "ai.meta.com", "blog.research.google", "techcrunch.com",
    "bytebytego.com", "developers.openai.com", "anthropic.com",
    "github.blog", "nvidia.com", "theverge.com"
]
