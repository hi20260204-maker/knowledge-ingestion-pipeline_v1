import pytest
import os
from unittest.mock import patch, MagicMock
from src.distribution.discord_notifier import send_discord_notification

@patch("src.distribution.discord_notifier.requests.post")
def test_send_discord_notification(mock_post):
    # Mocking successful HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_post.return_value = mock_response
    
    # Needs a dummy webhook URL
    result = send_discord_notification(
        webhook_url="https://fake-discord.com/api/webhooks/123",
        title="Breaking Tech News",
        summary="A major breakthrough in AI occurred today.",
        url="https://techcrunch.com/sample",
        score=9,
        keywords=["#AI", "#Innovation"]
    )
    
    assert result is True
    mock_post.assert_called_once()
    
    # Assert JSON payload structure
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert "embeds" in payload
    assert payload["embeds"][0]["title"] == "Breaking Tech News"
    assert "Importance Score: 9/10" in payload["embeds"][0]["description"]

def test_missing_webhook_url():
    with pytest.raises(ValueError, match="Discord Webhook URL is missing"):
        send_discord_notification("", "Title", "Sum", "url", 1, [])
