import pytest
from src.config.parser import load_sources
from src.models import SourceConfig


def test_load_sources(tmp_path):
    """sources.yaml 파일이 정상적으로 파싱되는지 검증합니다."""
    yaml_content = """
    sources:
      - id: "tech_blog_1"
        category: "AI"
        url: "https://example.com/rss"
        priority: 5
    """
    yaml_file = tmp_path / "sources.yaml"
    yaml_file.write_text(yaml_content)

    sources = load_sources(str(yaml_file))
    assert len(sources) == 1
    assert isinstance(sources[0], SourceConfig)
    assert sources[0].id == "tech_blog_1"
    assert sources[0].priority == 5
    assert sources[0].category == "AI"
