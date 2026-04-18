"""
파이프라인 실행 메트릭 모듈.

파이프라인 실행 중 수집되는 각종 통계를 추적하는 데이터 클래스를 정의합니다.
"""
from dataclasses import dataclass, asdict


@dataclass
class PipelineMetrics:
    """파이프라인 실행 통계를 추적하는 데이터 클래스.

    각 단계별 처리 결과를 누적하여, 최종 리포트 및 디스코드 알림에 사용됩니다.

    Attributes:
        source_count: 처리된 소스 수
        item_extracted_count: 추출된 총 아이템 수
        item_full_fetched_count: Full-fetch 보강된 아이템 수
        item_duplicate_count: 중복으로 건너뛴 아이템 수
        item_low_quality_count: 저품질로 필터링된 아이템 수
        item_parse_failed_count: 파싱 실패 아이템 수
        fetched: 처리 시도된 소스 수
        stored_new: 새로 저장된 기사 수
        stored_updated: 업데이트된 기사 수
        reused_summary: 재사용된 요약 수
        errors: 에러 발생 횟수
    """
    source_count: int = 0
    item_extracted_count: int = 0
    item_full_fetched_count: int = 0
    item_duplicate_count: int = 0
    item_low_quality_count: int = 0
    item_parse_failed_count: int = 0
    fetched: int = 0
    stored_new: int = 0
    stored_updated: int = 0
    reused_summary: int = 0
    errors: int = 0

    def to_dict(self) -> dict:
        """메트릭을 딕셔너리로 변환합니다. 리포트 및 로깅에 사용됩니다."""
        return asdict(self)
