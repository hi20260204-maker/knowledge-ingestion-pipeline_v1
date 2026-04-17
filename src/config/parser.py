import yaml
from pydantic import BaseModel
from typing import List

class SourceConfig(BaseModel):
    id: str
    category: str
    url: str
    priority: int = 1

def load_sources(file_path: str) -> List[SourceConfig]:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return [SourceConfig(**source) for source in data.get('sources', [])]
