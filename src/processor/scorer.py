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
        Calculates global_score (tech significance) and personalized_score (interest re-ranking).
        Returns scores in 0-100 range.
        """
        # --- 1. Calculate Global Score (G) ---
        g_base = 30.0
        g_tag_bonus = 0.0
        tags = [t.lower() for t in signals.get("tags", [])]
        if "architecture" in tags or "research" in tags: g_tag_bonus += 30.0
        elif "release" in tags or "news" in tags: g_tag_bonus += 15.0
        elif "tooling" in tags: g_tag_bonus += 10.0
        
        g_source_bonus = min(20.0, metadata.get("source_weight", 0.0) * 2) # Scaling source weight to 20 max
        g_fetch_bonus = 20.0 if metadata.get("fetch_mode") == "full" else 0.0
        
        global_score = min(100.0, g_base + g_tag_bonus + g_source_bonus + g_fetch_bonus)
        
        # --- 2. Calculate Personalized Score (P) ---
        # Personalization acts as a 60% weight re-ranker
        interest_match_score = 0.0
        matched_interests = []
        interests = self.interests.get("interests", {})
        detected_topics = [t.lower() for t in signals.get("topics", [])]
        
        for kw in interests.get("high", []):
            if kw.lower() in detected_topics:
                interest_match_score += 100.0 # Intentional strong signal
                matched_interests.append(kw)
                break # Take highest match
        
        if not matched_interests:
            for kw in interests.get("medium", []):
                if kw.lower() in detected_topics:
                    interest_match_score += 70.0
                    matched_interests.append(kw)
                    break
        
        if not matched_interests:
            for kw in interests.get("low", []):
                if kw.lower() in detected_topics:
                    interest_match_score += 40.0
                    matched_interests.append(kw)
                    break

        # Blend: 40% Global + 60% Personal Match
        personalized_score = (global_score * 0.4) + (interest_match_score * 0.6)
        personalized_score = min(100.0, personalized_score)

        # --- 3. Generate Unified Reason ---
        reasons = []
        if g_tag_bonus >= 25: reasons.append("기술적 중요도 높음")
        elif "release" in tags: reasons.append("신규 릴리즈")
        
        if matched_interests:
            reasons.append(f"관심사({matched_interests[0]}) 매칭")
        
        if metadata.get("source_weight", 0.0) > 5:
            reasons.append("신뢰 소스 가산")

        reason_str = " + ".join(reasons) if reasons else "일반 기술 소식"
        
        return {
            "global_score": round(global_score, 1),
            "personalized_score": round(personalized_score, 1),
            "reason": reason_str
        }
