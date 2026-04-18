"""
LLM 기반 콘텐츠 요약 모듈.

OpenAI Structured Output을 사용하여 기사를 분석하고,
한국어 요약, 핵심 포인트, 토픽, 태그, 신뢰도를 추출합니다.
"""
import os
from openai import OpenAI
from src.models import LLMSummaryResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)


def summarize_content(clean_content: str, fetch_mode: str = "full", api_key: str = None) -> LLMSummaryResponse:
    """콘텐츠를 분석하여 구조화된 요약을 생성합니다.

    Snippet/Full 모드에 따라 다른 분석 깊이를 적용합니다:
    - Snippet 모드: 보수적 분석, 낮은 신뢰도 기준선 (0.6~0.7)
    - Full 모드: 심층 기술 분석, 높은 신뢰도 기준선 (0.8~1.0)

    Args:
        clean_content: 분석할 텍스트 콘텐츠
        fetch_mode: 가져오기 모드 ("snippet" 또는 "full")
        api_key: OpenAI API 키 (미지정 시 환경변수에서 로드)

    Returns:
        LLMSummaryResponse: 구조화된 요약 응답

    Raises:
        ValueError: API 키가 없는 경우
        Exception: OpenAI API 호출 실패 시
    """
    logger.info(f"Initiating Mode-aware LLM analysis (Mode: {fetch_mode}, Length: {len(clean_content)} chars)")

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        logger.error("OPENAI_API_KEY is not set. Summarization failed.")
        raise ValueError("API Key is missing")

    client = OpenAI(api_key=key)

    # 모드별 시스템 프롬프트 분기
    system_instruction = _build_system_prompt(fetch_mode)

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Analyze and Summarize (Mode: {fetch_mode}):\n\n{clean_content}"}
            ],
            response_format=LLMSummaryResponse,
        )
        parsed_response = completion.choices[0].message.parsed

        logger.info(f"LLM analysis completed. Topics: {parsed_response.topics}, Confidence: {parsed_response.confidence_score}")

        return parsed_response

    except Exception as e:
        logger.error(f"Error during LLM analysis: {str(e)}")
        raise e


def _build_system_prompt(fetch_mode: str) -> str:
    """fetch_mode에 따른 시스템 프롬프트를 생성합니다.

    Args:
        fetch_mode: "snippet" 또는 "full"

    Returns:
        시스템 프롬프트 문자열
    """
    if fetch_mode == "snippet":
        return (
            "You are a cautious senior tech lead. Analyze a LIMITED SNIPPET of IT news. "
            "1. Output a Korean summary and key points. "
            "2. DO NOT make assumptions beyond the text. Say '정보 부족' if unclear. "
            "3. Provide topics and tags based only on visible text. "
            "4. Start with a baseline confidence_score of 0.6 to 0.7. "
            "5. Stick strictly to facts. No hallucinations."
        )
    else:
        return (
            "You are an insightful senior tech lead. Analyze the FULL BODY of IT news. "
            "1. Focus on technical background, core changes, and specific technical points. "
            "2. Provide a deep technical summary in Korean. "
            "3. Extract precise topics and tags. "
            "4. Confidence_score should be generally high (0.8 to 1.0) unless the text is noisy. "
            "5. Maintain high technical accuracy."
        )
