from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return default
        return float(value)
    except Exception:
        return default


def _contains_any(text: str, needles: list[str]) -> bool:
    t = (text or "").lower()
    return any(n in t for n in needles)


@dataclass(frozen=True)
class StrictScoringConfig:
    ten_price_max: float = 50_000
    ten_roi_min: float = 200.0
    nine_price_max: float = 60_000
    nine_roi_min: float = 150.0


class LLMAnalyzer:
    """Free, deterministic "AI" scoring.

    This is intentionally *not* a cloud LLM. For GitHub Pages, you want scoring
    to happen during data generation (locally or in CI) and publish the JSON.

    Public API is kept compatible with older code:
    - analyze_description(description)
    - analyze_property(property_data)
    - is_available()
    """

    def __init__(self, config: StrictScoringConfig | None = None):
        self.config = config or StrictScoringConfig()
        self.provider = "rules"

    def is_available(self) -> bool:
        return True

    def analyze_description(self, description: str) -> dict:
        # Backwards-compatible method used by scripts/scrape_for_web.py
        return self._score(
            description=description or "",
            title="",
            agent="",
            price=0.0,
            roi=0.0,
        )

    def analyze_property(self, property_data: dict) -> dict:
        return self._score(
            description=str(property_data.get("description") or ""),
            title=str(property_data.get("title") or ""),
            agent=str(property_data.get("agent") or ""),
            price=_to_float(property_data.get("price"), 0.0),
            roi=_to_float(property_data.get("roi"), 0.0),
        )

    def _score(self, *, description: str, title: str, agent: str, price: float, roi: float) -> dict:
        text = f"{title} {description} {agent}".lower()

        auction_terms = [
            "auction",
            "guide price",
            "starting bid",
            "lot ",
            "buyers premium",
            "buyer's premium",
            "reserve price",
        ]
        caveat_terms = [
            "cash buyers only",
            "cash buyer only",
            "tenant in situ",
            "tenanted",
            "shared ownership",
            "short lease",
            "leasehold",
            "subject to contract",
            "buyers premium",
            "buyer's premium",
        ]
        severe_distress_terms = [
            "fire damage",
            "derelict",
            "uninhabitable",
            "uninhabitable",
            "unlivable",
            "unliveable",
            "condemned",
            "structural",
            "subsidence",
            "gutted",
            "shell",
            "unsafe",
            "dangerous",
            "rebuild",
            "major works",
            "complete renovation",
        ]
        medium_works_terms = [
            "modernisation",
            "modernization",
            "refurbishment",
            "renovation",
            "updating",
            "project",
            "in need of",
            "requires",
        ]

        is_auction = _contains_any(text, auction_terms)
        has_caveat = _contains_any(text, caveat_terms)
        severe_distress = _contains_any(text, severe_distress_terms)
        medium_works = _contains_any(text, medium_works_terms)

        # Hard definition for 10 (your requirement)
        if (
            price > 0
            and price < self.config.ten_price_max
            and roi >= self.config.ten_roi_min
            and severe_distress
            and not is_auction
            and not has_caveat
        ):
            return {
                "score": 10,
                "reasoning": "Meets strict 10/10: <£50k, ROI>=200%, severe distress, no auction/caveats.",
            }

        # Base score from condition
        score = 3.0
        if medium_works:
            score = 5.0
        if severe_distress:
            score = 7.0

        # Price influence (only if known)
        if price <= 0:
            score = min(score, 5.0)  # unknown price cannot be top tier
        elif price < 50_000:
            score += 2.0
        elif price < 60_000:
            score += 1.5
        elif price < 80_000:
            score += 1.0
        elif price < 100_000:
            score += 0.5
        elif price > 120_000:
            score -= 1.0

        # ROI influence (only if present)
        if roi > 0:
            if roi >= 200:
                score += 2.5
            elif roi >= 150:
                score += 2.0
            elif roi >= 120:
                score += 1.0
            elif roi >= 100:
                score += 0.5
            elif roi < 80:
                score -= 0.5

        # Penalties
        if is_auction and price > 40_000:
            score -= 3.0
        if "tenant in situ" in text or "tenanted" in text:
            score -= 3.0
        if "shared ownership" in text:
            score -= 4.0
        if "cash buyers only" in text or "cash buyer only" in text:
            score -= 2.0
        if "leasehold" in text or "short lease" in text:
            score -= 2.0

        # Caps to prevent score inflation
        if not severe_distress:
            score = min(score, 6.0)
        if is_auction:
            score = min(score, 7.0)

        # Near-perfect (9) still requires very strong signal
        if price > 0 and price < self.config.nine_price_max and roi >= self.config.nine_roi_min and severe_distress and not is_auction and not has_caveat:
            score = max(score, 9.0)

        final = int(round(max(1.0, min(10.0, score))))

        reasons = []
        if price > 0:
            reasons.append(f"price £{int(price):,}")
        if roi > 0:
            reasons.append(f"ROI {roi:.0f}%")
        reasons.append("severe distress" if severe_distress else "needs work" if medium_works else "no major works signaled")
        if is_auction:
            reasons.append("auction mentioned")
        if has_caveat:
            reasons.append("caveats mentioned")

        return {"score": final, "reasoning": ", ".join(reasons)[:200]}
