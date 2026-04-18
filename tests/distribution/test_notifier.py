import pytest
from unittest.mock import patch, MagicMock
from src.distribution.discord_notifier import send_daily_digest


@patch("src.distribution.discord_notifier.requests.post")
def test_send_daily_digest(mock_post):
    """Discord 일일 다이제스트가 정상적으로 발송되는지 검증합니다."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_post.return_value = mock_response

    # Phase 4 스키마에 맞춘 모의 기사 데이터
    articles = [
        {
            'id': 1, 'title': 'AI Breakthrough', 'url': 'https://example.com/1',
            'summary': 'Major AI news', 'global_score': 95.0,
            'personalized_score': 88.0, 'tags': ['research']
        },
        {
            'id': 2, 'title': 'Python Update', 'url': 'https://example.com/2',
            'summary': 'Python 3.13 release', 'global_score': 70.0,
            'personalized_score': 92.0, 'tags': ['release']
        },
    ]
    metrics = {'source_count': 5, 'fetched': 10}

    result = send_daily_digest(
        webhook_url="https://fake-discord.com/api/webhooks/123",
        date_str="2026-04-18",
        articles=articles,
        metrics=metrics
    )

    assert result is True
    mock_post.assert_called_once()

    # Embed 구조 검증
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert "embeds" in payload
    assert "Daily IT Knowledge Digest" in payload["embeds"][0]["title"]


def test_missing_webhook_url():
    """웹훅 URL 누락 시 False를 반환하는지 검증합니다."""
    result = send_daily_digest("", "2026-04-18", [], {})
    assert result is False
