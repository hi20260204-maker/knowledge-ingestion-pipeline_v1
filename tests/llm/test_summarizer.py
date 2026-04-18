import pytest
from unittest.mock import patch, MagicMock
from src.llm.summarizer import summarize_content
from src.models import LLMSummaryResponse
import os


@patch("src.llm.summarizer.OpenAI")
def test_summarize_content(mock_openai):
    """LLM 요약이 정상적으로 수행되는지 검증합니다."""
    mock_client_instance = MagicMock()
    mock_openai.return_value = mock_client_instance

    # Phase 4 스키마에 맞춘 모의 응답
    mock_parsed = LLMSummaryResponse(
        summary="This is a mocked 3-sentence summary.",
        key_points=["Point 1", "Point 2"],
        topics=["LLM", "Python"],
        tags=["release", "news"],
        confidence_score=0.85
    )

    mock_message = MagicMock()
    mock_message.parsed = mock_parsed

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client_instance.beta.chat.completions.parse.return_value = mock_completion

    # API 키를 직접 전달하여 실행
    result = summarize_content("Mock tech news content", api_key="sk-fake-key")

    assert "LLM" in result.topics
    assert len(result.key_points) == 2
    assert result.confidence_score == 0.85

    # OpenAI 호출 검증
    mock_client_instance.beta.chat.completions.parse.assert_called_once()
    args, kwargs = mock_client_instance.beta.chat.completions.parse.call_args
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["response_format"] == LLMSummaryResponse


def test_missing_api_key():
    """API 키 미설정 시 ValueError가 발생하는지 검증합니다."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError, match="API Key is missing"):
            summarize_content("won't work", api_key="")
