import os
import yaml
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class Scorer:
    def __init__(self, interests_path: str = "interests.yaml"):
        self.interests_path = interests_path
        self.interests = self._load_interests()
        
    def _load_interests(self) -> Dict[str, Any]:
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
        """
        Calculates importance_score and generates importance_reason.
        
        signals: {topics: List[str], tags: List[str], confidence_score: float}
        metadata: {source_weight: float, fetch_mode: str}
        """
        base_score = 3.0 # Default base
        keyword_score = 0.0
        reasons = []
        
        # 1. Keyword Weighting (Interests)
        interests = self.interests.get("interests", {})
        detected_topics = [t.lower() for t in signals.get("topics", [])]
        
        # Check High
        for kw in interests.get("high", []):
            if kw.lower() in detected_topics:
                keyword_score += 3.0
                reasons.append(f"주요 관심사({kw})")
                
        # Check Medium
        for kw in interests.get("medium", []):
            if kw.lower() in detected_topics:
                keyword_score += 1.5
                reasons.append(f"관심 기술({kw})")
                
        # 2. Confidence Correction (Suppression)
        # Low confidence shrinks the keyword score boost
        confidence = signals.get("confidence_score", 0.8)
        adjusted_keyword_score = keyword_score * (0.5 + 0.5 * confidence)
        
        # 3. Source & Metadata Bonuses
        source_bonus = metadata.get("source_weight", 0.0)
        if source_bonus > 0:
            reasons.append("신뢰 소스 가산점")
            
        fetch_bonus = 0.5 if metadata.get("fetch_mode") == "full" else 0.0
        if fetch_bonus > 0:
            reasons.append("본문 분석 완료")
            
        # Tag bonuses
        tag_bonus = 0.0
        tags = [t.lower() for t in signals.get("tags", [])]
        if "release" in tags or "news" in tags:
            tag_bonus += 0.5
            reasons.append("신규 릴리즈/소식")
        if "architecture" in tags or "research" in tags:
            tag_bonus += 0.8
            reasons.append("기술적 중요도")

        # Result Calculation
        final_score = base_score + adjusted_keyword_score + source_bonus + fetch_bonus + tag_bonus
        
        # Clamp score to 1-10
        final_score = max(1, min(10, round(final_score)))
        
        # Generate reason string
        reason_str = " + ".join(reasons) if reasons else "일반 기술 소식"
        
        return {
            "importance_score": final_score,
            "importance_reason": reason_str
        }
