"""Rules engine for deterministic optimizations.

Handles the 60-70% of optimization decisions that are pure IF/THEN logic,
running at zero API cost. The LLM handles the rest.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class RuleAction:
    """An action produced by a rule evaluation."""
    rule_name: str
    action_type: str      # bid_increase, bid_decrease, negate, pause, flag_for_review
    entity_type: str      # keyword, campaign, search_term
    entity_id: str
    entity_name: str
    campaign_id: str
    campaign_name: str
    current_value: float | None = None
    recommended_value: float | None = None
    rationale: str = ""
    confidence: str = "high"
    data_points: dict | None = None


class RulesEngine:
    """Evaluates deterministic rules against campaign/keyword data."""

    def __init__(self, target_acos: float = 30.0):
        self.target_acos = target_acos

    def evaluate_keyword(self, kw: dict) -> list[RuleAction]:
        """Evaluate all rules against a single keyword's data."""
        actions = []
        clicks = kw.get("clicks", 0)
        orders = kw.get("orders_7d", 0) or kw.get("orders", 0)
        spend = kw.get("spend", 0)
        sales = kw.get("sales_7d", 0) or kw.get("sales", 0)
        acos = (spend / sales * 100) if sales > 0 else (999 if spend > 0 else 0)
        bid = kw.get("bid", 0)
        impressions = kw.get("impressions", 0)

        campaign_id = kw.get("campaign_id", "")
        campaign_name = kw.get("campaign_name", "")
        keyword_id = kw.get("keyword_id", "")
        keyword_text = kw.get("keyword_text", "")

        # Rule 1: High spend, zero orders -> flag for negation review
        if clicks >= 20 and orders == 0 and spend > 5:
            actions.append(RuleAction(
                rule_name="zero_orders_high_spend",
                action_type="negate",
                entity_type="keyword",
                entity_id=keyword_id,
                entity_name=keyword_text,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                current_value=bid,
                rationale=f"{clicks} clicks, ${spend:.2f} spend, 0 orders. Consider negation.",
                confidence="high",
                data_points={"clicks": clicks, "spend": spend, "orders": orders},
            ))

        # Rule 2: ACoS significantly above target -> decrease bid
        elif orders > 0 and acos > self.target_acos * 1.3 and clicks >= 10:
            reduction_pct = min(0.20, (acos - self.target_acos) / acos)
            new_bid = round(bid * (1 - reduction_pct), 2)
            actions.append(RuleAction(
                rule_name="acos_above_target",
                action_type="bid_decrease",
                entity_type="keyword",
                entity_id=keyword_id,
                entity_name=keyword_text,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                current_value=bid,
                recommended_value=new_bid,
                rationale=f"ACoS {acos:.1f}% vs target {self.target_acos}%. Reducing bid {reduction_pct*100:.0f}%.",
                confidence="high",
                data_points={"clicks": clicks, "acos": acos, "orders": orders},
            ))

        # Rule 3: ACoS well below target with good volume -> increase bid
        elif orders >= 3 and acos < self.target_acos * 0.7 and clicks >= 15:
            increase_pct = min(0.20, (self.target_acos - acos) / self.target_acos * 0.5)
            new_bid = round(bid * (1 + increase_pct), 2)
            actions.append(RuleAction(
                rule_name="acos_below_target_scale",
                action_type="bid_increase",
                entity_type="keyword",
                entity_id=keyword_id,
                entity_name=keyword_text,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                current_value=bid,
                recommended_value=new_bid,
                rationale=f"ACoS {acos:.1f}% well below target {self.target_acos}%. Increasing bid to capture more volume.",
                confidence="medium",
                data_points={"clicks": clicks, "acos": acos, "orders": orders, "sales": sales},
            ))

        # Rule 4: High impressions, low CTR -> flag for review (ad copy or relevance issue)
        elif impressions > 1000 and clicks > 0 and (clicks / impressions) < 0.002:
            ctr = clicks / impressions * 100
            actions.append(RuleAction(
                rule_name="low_ctr",
                action_type="flag_for_review",
                entity_type="keyword",
                entity_id=keyword_id,
                entity_name=keyword_text,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                rationale=f"CTR {ctr:.3f}% very low ({impressions} impressions, {clicks} clicks). Possible relevance issue.",
                confidence="medium",
                data_points={"impressions": impressions, "clicks": clicks, "ctr": ctr},
            ))

        return actions

    def evaluate_search_term(self, st: dict) -> list[RuleAction]:
        """Evaluate rules against a search term."""
        actions = []
        clicks = st.get("clicks", 0)
        orders = st.get("orders_7d", 0) or st.get("orders", 0)
        spend = st.get("spend", 0)
        sales = st.get("sales_7d", 0) or st.get("sales", 0)
        acos = (spend / sales * 100) if sales > 0 else (999 if spend > 0 else 0)
        search_term = st.get("search_term", "")

        # Rule: Search term with spend and no orders -> negate
        if clicks >= 20 and orders == 0 and spend > 3:
            actions.append(RuleAction(
                rule_name="search_term_no_convert",
                action_type="negate",
                entity_type="search_term",
                entity_id=search_term,
                entity_name=search_term,
                campaign_id=st.get("campaign_id", ""),
                campaign_name=st.get("campaign_name", ""),
                rationale=f"Search term '{search_term}': {clicks} clicks, ${spend:.2f} spend, 0 orders.",
                confidence="high",
                data_points={"clicks": clicks, "spend": spend},
            ))

        # Rule: Search term converting well -> graduate to exact match
        elif orders >= 2 and acos <= self.target_acos and clicks >= 10:
            actions.append(RuleAction(
                rule_name="search_term_graduate",
                action_type="graduate",
                entity_type="search_term",
                entity_id=search_term,
                entity_name=search_term,
                campaign_id=st.get("campaign_id", ""),
                campaign_name=st.get("campaign_name", ""),
                rationale=f"Search term '{search_term}' converting at {acos:.1f}% ACoS with {orders} orders. Graduate to exact.",
                confidence="high",
                data_points={"clicks": clicks, "orders": orders, "acos": acos, "sales": sales},
            ))

        return actions

    def evaluate_campaign(self, campaign: dict) -> list[RuleAction]:
        """Evaluate rules against a campaign."""
        actions = []
        spend = campaign.get("spend", 0)
        budget = campaign.get("daily_budget", 0)
        acos = campaign.get("acos_7d", 0) or campaign.get("acos", 0)
        orders = campaign.get("orders_7d", 0) or campaign.get("orders", 0)

        # Rule: Budget utilization > 95% and good performance -> increase budget
        if budget > 0 and spend > 0:
            utilization = spend / budget
            if utilization > 0.95 and acos < self.target_acos and orders > 0:
                new_budget = round(budget * 1.15, 2)
                actions.append(RuleAction(
                    rule_name="budget_capped_good_perf",
                    action_type="budget_increase",
                    entity_type="campaign",
                    entity_id=campaign.get("campaign_id", ""),
                    entity_name=campaign.get("campaign_name", ""),
                    campaign_id=campaign.get("campaign_id", ""),
                    campaign_name=campaign.get("campaign_name", ""),
                    current_value=budget,
                    recommended_value=new_budget,
                    rationale=f"Budget {utilization*100:.0f}% utilized, ACoS {acos:.1f}% below target. Increase 15%.",
                    confidence="medium",
                    data_points={"utilization": utilization, "acos": acos, "orders": orders},
                ))

        return actions

    def run_all(
        self,
        campaigns: list[dict],
        keywords: list[dict],
        search_terms: list[dict],
    ) -> list[RuleAction]:
        """Run all rules against all data. Returns list of recommended actions."""
        actions = []
        for c in campaigns:
            actions.extend(self.evaluate_campaign(c))
        for kw in keywords:
            actions.extend(self.evaluate_keyword(kw))
        for st in search_terms:
            actions.extend(self.evaluate_search_term(st))
        return actions
