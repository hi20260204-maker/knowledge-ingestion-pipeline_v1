"""
규칙 기반 스코어링 엔진.

LLM이 추출한 시그널과 소스 메타데이터를 기반으로
Global Score(기술적 중요도)와 Personalized Score(개인 관심도)를 계산합니다.
"""
import os
import yaml
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Scorer:
    """Dual-Score(Global + Personalized) 계산 엔진.

    - Global Score: 기술적 중요도 (태그, 소스 가중치, fetch 모드 기반)
    - Personalized Score: 사용자 관심사 매칭 기반 재순위화

    Attributes:
        interests_path: interests.yaml 파일 경로
        interests: 로드된 관심사 설정 딕셔너리
    """

    def __init__(self, interests_path: str = "config/interests.yaml"):
        """Scorer를 초기화하고 관심사 설정을 로드합니다.

        Args:
            interests_path: interests.yaml 파일 경로
        """
        self.interests_path = interests_path
        self.interests = self._load_interests()

    def _load_interests(self) -> Dict[str, Any]:
        """interests.yaml 파일에서 관심사 설정을 로드합니다.

        파일이 없거나 로드 실패 시 빈 기본값을 반환합니다.

        Returns:
            관심사 설정 딕셔너리 (high/medium/low 계층)
        """
        if not os.path.exists(self.interests_path):
            logger.warning(f"Interests file not found at {self.interests_path}. Using empty defaults.")
            return {"interests": {"high": [], "medium": [], "low": []}}

        try:
            with open(self.interests_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load interests: {e}")
            return {"interests": {"high": [], "medium": [], "low": []}}

    def calculate_score(self, signals: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Global Score와 Personalized Score를 계산합니다.

        점수 구성:
        - Global Score (0-100): base(30) + tag_bonus(0-30) + source_bonus(0-20) + fetch_bonus(0-20)
        - Personalized Score (0-100): Global(40%) + Interest Match(60%)

        Interest Match 가중치:
        - high 매칭: 100점
        - medium 매칭: 70점
        - low 매칭: 40점

        Args:
            signals: LLM이 추출한 시그널 (tags, topics 등)
            metadata: 소스 메타데이터 (source_weight, fetch_mode)

        Returns:
            {'global_score': float, 'personalized_score': float, 'reason': str}
        """
        # --- 1. Global Score (G) 계산 ---
        global_score = self._calculate_global_score(signals, metadata)

        # --- 2. Personalized Score (P) 계산 ---
        personalized_score, matched_interests = self._calculate_personalized_score(
            global_score, signals
        )

        # --- 3. 통합 사유 생성 ---
        reason = self._generate_reason(signals, metadata, matched_interests)

        return {
            "global_score": round(global_score, 1),
            "personalized_score": round(personalized_score, 1),
            "reason": reason
        }

    def _calculate_global_score(self, signals: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        """기술적 중요도 기반 Global Score를 계산합니다.

        Args:
            signals: LLM 시그널 (tags 필드 사용)
            metadata: 소스 메타데이터 (source_weight, fetch_mode 사용)

        Returns:
            Global Score (0-100)
        """
        g_base = 30.0

        # 태그 기반 보너스
        tags = [t.lower() for t in signals.get("tags", [])]
        g_tag_bonus = 0.0
        if "architecture" in tags or "research" in tags:
            g_tag_bonus += 30.0
        elif "release" in tags or "news" in tags:
            g_tag_bonus += 15.0
        elif "tooling" in tags:
            g_tag_bonus += 10.0

        # 소스 신뢰도 보너스 (최대 20점)
        g_source_bonus = min(20.0, metadata.get("source_weight", 0.0) * 2)

        # Full-fetch 보너스 (전체 본문 분석 시 가산)
        g_fetch_bonus = 20.0 if metadata.get("fetch_mode") == "full" else 0.0

        return min(100.0, g_base + g_tag_bonus + g_source_bonus + g_fetch_bonus)

    def _calculate_personalized_score(self, global_score: float, signals: Dict[str, Any]) -> tuple:
        """사용자 관심사 기반 Personalized Score를 계산합니다.

        블렌딩 공식: 40% Global + 60% Interest Match

        Args:
            global_score: 이미 계산된 Global Score
            signals: LLM 시그널 (topics 필드 사용)

        Returns:
            (personalized_score, matched_interests) 튜플
        """
        interest_match_score = 0.0
        matched_interests = []
        interests = self.interests.get("interests", {})
        detected_topics = [t.lower() for t in signals.get("topics", [])]

        # High → Medium → Low 우선순위로 매칭
        for level, score in [("high", 100.0), ("medium", 70.0), ("low", 40.0)]:
            if matched_interests:
                break
            for kw in interests.get(level, []):
                if kw.lower() in detected_topics:
                    interest_match_score = score
                    matched_interests.append(kw)
                    break

        # 블렌딩: 40% Global + 60% Personal
        personalized_score = (global_score * 0.4) + (interest_match_score * 0.6)
        personalized_score = min(100.0, personalized_score)

        return personalized_score, matched_interests

    def _generate_reason(self, signals: Dict[str, Any], metadata: Dict[str, Any],
                         matched_interests: list) -> str:
        """점수 산정 이유를 한국어 문자열로 생성합니다.

        Args:
            signals: LLM 시그널
            metadata: 소스 메타데이터
            matched_interests: 매칭된 관심사 키워드 목록

        Returns:
            이유 문자열 (예: "기술적 중요도 높음 + 관심사(LLM) 매칭")
        """
        reasons = []
        tags = [t.lower() for t in signals.get("tags", [])]

        if "architecture" in tags or "research" in tags:
            reasons.append("기술적 중요도 높음")
        elif "release" in tags:
            reasons.append("신규 릴리즈")

        if matched_interests:
            reasons.append(f"관심사({matched_interests[0]}) 매칭")

        if metadata.get("source_weight", 0.0) > 5:
            reasons.append("신뢰 소스 가산")

        return " + ".join(reasons) if reasons else "일반 기술 소식"
