"""
파이프라인 Step 4: LLM 요약 및 스코어링.

OpenAI를 통해 콘텐츠를 요약하고, 규칙 기반 스코어링 후 DB에 저장합니다.
"""
from src.models import ExtractedItem
from src.llm.summarizer import summarize_content
from src.processor.scorer import Scorer
from src.processor.hasher import generate_content_hash
from src.config.settings import DB_PATH
from src.db.client import find_reusable_summary, save_summary
from src.pipeline.metrics import PipelineMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def summarize_item(article_id: int, item: ExtractedItem, content: str,
                   scorer: Scorer, source_weight: float, fetch_mode: str,
                   metrics: PipelineMetrics) -> None:
    """아티클에 대해 LLM 요약 및 스코어링을 수행하고 DB에 저장합니다.

    1. 기존 동일 콘텐츠의 요약 재사용 시도 (LLM 비용 절감)
    2. 새로운 요약 필요 시 LLM 호출
    3. 규칙 기반 Dual-Score 계산 (Global + Personalized)
    4. 결과 DB 저장

    Args:
        article_id: 저장된 아티클 ID
        item: 원본 아이템
        content: 최종 콘텐츠 텍스트
        scorer: Dual-Score 스코어링 엔진
        source_weight: 소스 신뢰도 가중치
        fetch_mode: 가져오기 모드 ("snippet" 또는 "full")
        metrics: 파이프라인 메트릭 (in-place 업데이트)
    """
    content_hash = generate_content_hash(content)

    # 기존 요약 재사용 시도
    existing_summary = find_reusable_summary(DB_PATH, content_hash)
    if existing_summary:
        metrics.reused_summary += 1
        return

    # 새로운 LLM 분석 수행
    try:
        # 1. LLM 시그널 추출
        llm_signals = summarize_content(content, fetch_mode=fetch_mode)

        # 2. 규칙 기반 스코어링
        metadata = {
            "source_weight": source_weight,
            "fetch_mode": fetch_mode
        }
        scoring_result = scorer.calculate_score(llm_signals.dict(), metadata)

        summary_data = {
            'global_score': scoring_result['global_score'],
            'personalized_score': scoring_result['personalized_score'],
            'reason': scoring_result['reason'],
            'summary': llm_signals.summary,
            'key_points': llm_signals.key_points,
            'keywords': llm_signals.topics
        }
    except Exception as e:
        logger.error(f"Summarization/Scoring failed for {item.url}: {e}")
        # 에러 시 안전한 폴백 데이터로 저장
        summary_data = {
            'global_score': 50.0,
            'personalized_score': 50.0,
            'reason': "Analysis error fallback",
            'summary': "Summary bypass (Error or API issue)",
            'key_points': [],
            'keywords': ["General"]
        }

    save_summary(DB_PATH, article_id, summary_data)
