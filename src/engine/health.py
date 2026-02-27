"""Campaign and keyword health scoring.

Computes health scores (0-100) based on multiple performance signals.
Spend-weighted so high-spend entities surface first.
"""

from dataclasses import dataclass


@dataclass
class HealthScore:
    score: int              # 0-100
    grade: str              # A, B, C, D, F
    weighted_score: float   # score * spend_weight
    factors: dict           # breakdown of what contributed


def compute_campaign_health(
    campaign: dict,
    target_acos: float = 30.0,
) -> HealthScore:
    """Compute health score for a campaign."""
    score = 100
    factors = {}
    spend = campaign.get("spend", 0)
    orders = campaign.get("orders_7d", 0) or campaign.get("orders", 0)
    clicks = campaign.get("clicks", 0)
    impressions = campaign.get("impressions", 0)
    sales = campaign.get("sales_7d", 0) or campaign.get("sales", 0)
    acos = (spend / sales * 100) if sales > 0 else 0

    # ACoS component (40 points)
    if spend > 0 and sales == 0:
        score -= 40
        factors["acos"] = "No sales, -40"
    elif acos > 0:
        acos_ratio = acos / target_acos
        if acos_ratio <= 0.8:
            factors["acos"] = f"ACoS {acos:.1f}% excellent vs {target_acos}% target"
        elif acos_ratio <= 1.0:
            score -= 5
            factors["acos"] = f"ACoS {acos:.1f}% good, -5"
        elif acos_ratio <= 1.3:
            score -= 15
            factors["acos"] = f"ACoS {acos:.1f}% above target, -15"
        elif acos_ratio <= 1.5:
            score -= 25
            factors["acos"] = f"ACoS {acos:.1f}% high, -25"
        else:
            score -= 40
            factors["acos"] = f"ACoS {acos:.1f}% critical, -40"

    # CTR component (20 points)
    if impressions > 100:
        ctr = clicks / impressions * 100 if impressions > 0 else 0
        if ctr >= 0.5:
            factors["ctr"] = f"CTR {ctr:.2f}% healthy"
        elif ctr >= 0.3:
            score -= 5
            factors["ctr"] = f"CTR {ctr:.2f}% below average, -5"
        elif ctr >= 0.15:
            score -= 10
            factors["ctr"] = f"CTR {ctr:.2f}% low, -10"
        else:
            score -= 20
            factors["ctr"] = f"CTR {ctr:.2f}% very low, -20"

    # Conversion component (20 points)
    if clicks >= 10:
        cvr = orders / clicks * 100 if clicks > 0 else 0
        if cvr >= 15:
            factors["cvr"] = f"CVR {cvr:.1f}% excellent"
        elif cvr >= 10:
            score -= 5
            factors["cvr"] = f"CVR {cvr:.1f}% good, -5"
        elif cvr >= 5:
            score -= 10
            factors["cvr"] = f"CVR {cvr:.1f}% below average, -10"
        else:
            score -= 20
            factors["cvr"] = f"CVR {cvr:.1f}% low, -20"

    # Volume component (20 points)
    if impressions < 100:
        score -= 20
        factors["volume"] = f"Only {impressions} impressions, insufficient data, -20"
    elif clicks < 5:
        score -= 15
        factors["volume"] = f"Only {clicks} clicks, low volume, -15"

    score = max(0, min(100, score))
    grade = _score_to_grade(score)
    weighted = score * (spend / 100 if spend > 0 else 0.01)

    return HealthScore(score=score, grade=grade, weighted_score=weighted, factors=factors)


def _score_to_grade(score: int) -> str:
    if score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 35:
        return "D"
    return "F"
