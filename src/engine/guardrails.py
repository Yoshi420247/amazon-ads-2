"""Guardrail framework for the agentic system.

Hard limits cannot be overridden. Soft limits can be overridden with reasoning.
Every action must pass guardrail checks before execution.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuardrailResult:
    passed: bool
    rule_name: str
    message: str
    severity: str = "hard"  # hard = block, soft = warn


@dataclass
class GuardrailConfig:
    """Default guardrails. Override via Supabase guardrails_config table."""

    # Hard limits (cannot be overridden)
    max_bid: float = 10.00                    # Maximum keyword bid in dollars
    max_daily_budget: float = 500.00          # Maximum daily budget per campaign
    max_portfolio_daily_spend: float = 2000.00
    max_bid_change_pct: float = 30.0          # Maximum bid change per adjustment (%)
    max_budget_change_pct: float = 20.0       # Maximum budget change per day (%)
    min_clicks_before_negate: int = 20        # Minimum clicks before negating a keyword
    min_data_age_days: int = 14               # Don't act on data less than 14 days old
    emergency_spend_multiplier: float = 1.5   # Pause if daily spend > 150% of target
    cooldown_days: int = 7                    # Days between bid changes on same keyword

    # Soft limits (can be overridden with reasoning)
    preferred_bid_change_pct: float = 15.0    # Preferred bid adjustment range (%)
    preferred_eval_period_days: int = 10      # Preferred days between changes
    new_keyword_bid_multiplier: float = 1.1   # New keyword bid = historical CPC * this
    max_campaigns_warn: int = 100             # Warn if creating more than this


class Guardrails:
    """Validates actions against guardrail configuration."""

    def __init__(self, config: GuardrailConfig | None = None):
        self.config = config or GuardrailConfig()

    def check_bid_change(
        self,
        current_bid: float,
        new_bid: float,
        keyword_id: str | None = None,
        last_change_date: str | None = None,
    ) -> list[GuardrailResult]:
        results = []

        # Check absolute max bid
        if new_bid > self.config.max_bid:
            results.append(GuardrailResult(
                passed=False,
                rule_name="max_bid",
                message=f"New bid ${new_bid:.2f} exceeds max ${self.config.max_bid:.2f}",
                severity="hard",
            ))

        # Check bid change percentage
        if current_bid > 0:
            change_pct = abs(new_bid - current_bid) / current_bid * 100
            if change_pct > self.config.max_bid_change_pct:
                results.append(GuardrailResult(
                    passed=False,
                    rule_name="max_bid_change_pct",
                    message=f"Bid change {change_pct:.1f}% exceeds max {self.config.max_bid_change_pct}%",
                    severity="hard",
                ))
            elif change_pct > self.config.preferred_bid_change_pct:
                results.append(GuardrailResult(
                    passed=True,
                    rule_name="preferred_bid_change_pct",
                    message=f"Bid change {change_pct:.1f}% exceeds preferred {self.config.preferred_bid_change_pct}%",
                    severity="soft",
                ))

        # Check cooldown period
        if last_change_date:
            from datetime import date, datetime
            last = datetime.fromisoformat(last_change_date).date() if isinstance(last_change_date, str) else last_change_date
            days_since = (date.today() - last).days
            if days_since < self.config.cooldown_days:
                results.append(GuardrailResult(
                    passed=False,
                    rule_name="cooldown",
                    message=f"Only {days_since}d since last change (min {self.config.cooldown_days}d)",
                    severity="hard",
                ))

        if not results:
            results.append(GuardrailResult(
                passed=True, rule_name="all_checks", message="All bid guardrails passed"
            ))
        return results

    def check_budget_change(
        self,
        current_budget: float,
        new_budget: float,
    ) -> list[GuardrailResult]:
        results = []

        if new_budget > self.config.max_daily_budget:
            results.append(GuardrailResult(
                passed=False,
                rule_name="max_daily_budget",
                message=f"New budget ${new_budget:.2f} exceeds max ${self.config.max_daily_budget:.2f}",
                severity="hard",
            ))

        if current_budget > 0:
            change_pct = abs(new_budget - current_budget) / current_budget * 100
            if change_pct > self.config.max_budget_change_pct:
                results.append(GuardrailResult(
                    passed=False,
                    rule_name="max_budget_change_pct",
                    message=f"Budget change {change_pct:.1f}% exceeds max {self.config.max_budget_change_pct}%",
                    severity="hard",
                ))

        if not results:
            results.append(GuardrailResult(
                passed=True, rule_name="all_checks", message="All budget guardrails passed"
            ))
        return results

    def check_negation(self, clicks: int, orders: int) -> list[GuardrailResult]:
        results = []

        if clicks < self.config.min_clicks_before_negate:
            results.append(GuardrailResult(
                passed=False,
                rule_name="min_clicks_before_negate",
                message=f"Only {clicks} clicks (min {self.config.min_clicks_before_negate} required)",
                severity="hard",
            ))

        if not results:
            results.append(GuardrailResult(
                passed=True, rule_name="all_checks", message="Negation guardrails passed"
            ))
        return results

    def check_all(self, action: dict) -> list[GuardrailResult]:
        """Check all applicable guardrails for an action."""
        action_type = action.get("type", "")

        if action_type in ("bid_increase", "bid_decrease"):
            return self.check_bid_change(
                current_bid=action.get("current_value", 0),
                new_bid=action.get("new_value", 0),
                last_change_date=action.get("last_change_date"),
            )
        elif action_type in ("budget_increase", "budget_decrease"):
            return self.check_budget_change(
                current_budget=action.get("current_value", 0),
                new_budget=action.get("new_value", 0),
            )
        elif action_type == "negate":
            return self.check_negation(
                clicks=action.get("clicks", 0),
                orders=action.get("orders", 0),
            )
        return [GuardrailResult(passed=True, rule_name="no_check", message="No guardrail for this action type")]

    def all_passed(self, results: list[GuardrailResult]) -> bool:
        return all(r.passed or r.severity == "soft" for r in results)

    def hard_failures(self, results: list[GuardrailResult]) -> list[GuardrailResult]:
        return [r for r in results if not r.passed and r.severity == "hard"]
