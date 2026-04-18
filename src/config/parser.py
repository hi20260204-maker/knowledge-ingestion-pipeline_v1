"""
소스 설정 파서.

sources.yaml 파일을 읽어서 SourceConfig 모델 목록으로 파싱합니다.
"""
import yaml
from typing import List
from src.models import SourceConfig


def load_sources(file_path: str) -> List[SourceConfig]:
    """YAML 파일에서 소스 설정 목록을 로드합니다.

    Args:
        file_path: sources.yaml 파일 경로

    Returns:
        파싱된 SourceConfig 객체 목록

    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        yaml.YAMLError: YAML 파싱 실패 시
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return [SourceConfig(**source) for source in data.get('sources', [])]
