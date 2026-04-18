"""
로깅 유틸리티 모듈.

프로젝트 전역에서 사용되는 통합 로깅 설정을 제공합니다.
콘솔 출력과 로테이팅 파일 로그를 동시에 지원합니다.
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """콘솔 + 파일 핸들러가 설정된 커스텀 로거를 반환합니다.

    중복 핸들러 등록을 방지하며, 로그 파일은 5MB 로테이션으로 관리됩니다.
    프로젝트의 모든 모듈에서 이 함수를 통해 로거를 얻어야 합니다.

    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)

    Returns:
        설정된 logging.Logger 인스턴스
    """
    logger = logging.getLogger(name)

    # 핸들러 중복 등록 방지
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # logs/ 디렉토리 자동 생성
    log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # 로테이팅 파일 핸들러 (5MB, 3개 백업)
    log_file = os.path.join(log_dir, 'pipeline.log')
    fh = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger
