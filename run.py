"""
파이프라인 실행 진입점.

이 스크립트는 프로젝트 루트에서 실행되어 전체 파이프라인을 시작합니다.
GitHub Actions 및 로컬 실행 모두 이 파일을 통해 파이프라인을 실행합니다.

Usage:
    python run.py
"""
from src.pipeline.main_pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline()
