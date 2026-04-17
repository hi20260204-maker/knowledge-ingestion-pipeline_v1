import pytest
from unittest.mock import patch, MagicMock
from src.llm.summarizer import summarize_content, LLMSummaryResponse
import os

@patch("src.llm.summarizer.OpenAI")
def test_summarize_content(mock_openai):
    # Mocking the client and its nested call structure
    mock_client_instance = MagicMock()
    mock_openai.return_value = mock_client_instance
    
    # Mocking the parsed response
    mock_parsed = LLMSummaryResponse(
        importance_score=8,
        summary="This is a mocked 3-sentence summary.",
        key_points=["Point 1", "Point 2"],
        keywords=["#Mock", "#Test"]
    )
    
    mock_message = MagicMock()
    mock_message.parsed = mock_parsed
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    
    mock_client_instance.beta.chat.completions.parse.return_value = mock_completion
    
    # Run Function with fake API key
    result = summarize_content("Mock tech news content", api_key="sk-fake-key")
    
    assert result.importance_score == 8
    assert "#Mock" in result.keywords
    assert len(result.key_points) == 2

    # Verify the mock was called
    mock_client_instance.beta.chat.completions.parse.assert_called_once()
    args, kwargs = mock_client_instance.beta.chat.completions.parse.call_args
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["response_format"] == LLMSummaryResponse

def test_missing_api_key():
    # Force the environment variable to be absent
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError, match="API Key is missing"):
            summarize_content("won't work", api_key="")
