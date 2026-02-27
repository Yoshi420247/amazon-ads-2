"""Executor agent: applies approved actions via Amazon Ads API.

Part of the EXECUTE step in the agentic loop.
Takes approved actions, validates against guardrails, and executes.
Logs every action with reasoning to the database.
"""

from datetime import datetime
from typing import Any

from ..api.client import SPClient
from ..db.client import get_store
from ..engine.guardrails import Guardrails, GuardrailResult


class Executor:
    """Executes approved optimization actions with guardrail validation."""

    def __init__(
        self,
        sp_client: SPClient | None = None,
        guardrails: Guardrails | None = None,
        dry_run: bool = True,
    ):
        self.sp = sp_client or SPClient()
        self.guardrails = guardrails or Guardrails()
        self.store = get_store()
        self.dry_run = dry_run

    def execute_bid_change(
        self,
        keyword_id: str,
        current_bid: float,
        new_bid: float,
        reasoning: str,
        session_id: str | None = None,
    ) -> dict:
        """Change a keyword bid with guardrail validation."""
        # Check guardrails
        checks = self.guardrails.check_bid_change(current_bid, new_bid)
        hard_fails = self.guardrails.hard_failures(checks)

        if hard_fails:
            return {
                "status": "blocked",
                "reason": "; ".join(f.message for f in hard_fails),
                "checks": [{"rule": c.rule_name, "passed": c.passed, "msg": c.message} for c in checks],
            }

        # Log decision
        decision = {
            "session_id": session_id,
            "decision_type": "bid_increase" if new_bid > current_bid else "bid_decrease",
            "entity_type": "keyword",
            "entity_id": keyword_id,
            "previous_value": current_bid,
            "new_value": new_bid,
            "reasoning": reasoning,
            "guardrail_check": "PASS",
            "status": "executed" if not self.dry_run else "dry_run",
        }

        # Execute if not dry run
        if not self.dry_run:
            try:
                result = self.sp.update_keyword_bid(keyword_id, new_bid)
                decision["executed_at"] = datetime.now().isoformat()
                decision["status"] = "executed"
            except Exception as e:
                decision["status"] = "failed"
                decision["reasoning"] += f" | EXECUTION FAILED: {e}"

        self.store.insert("agent_decisions", decision)
        return decision

    def execute_budget_change(
        self,
        campaign_id: str,
        current_budget: float,
        new_budget: float,
        reasoning: str,
        session_id: str | None = None,
    ) -> dict:
        """Change a campaign budget with guardrail validation."""
        checks = self.guardrails.check_budget_change(current_budget, new_budget)
        hard_fails = self.guardrails.hard_failures(checks)

        if hard_fails:
            return {
                "status": "blocked",
                "reason": "; ".join(f.message for f in hard_fails),
            }

        decision = {
            "session_id": session_id,
            "decision_type": "budget_increase" if new_budget > current_budget else "budget_decrease",
            "entity_type": "campaign",
            "entity_id": campaign_id,
            "previous_value": current_budget,
            "new_value": new_budget,
            "reasoning": reasoning,
            "guardrail_check": "PASS",
            "status": "executed" if not self.dry_run else "dry_run",
        }

        if not self.dry_run:
            try:
                result = self.sp.update_campaign_budget(campaign_id, new_budget)
                decision["executed_at"] = datetime.now().isoformat()
                decision["status"] = "executed"
            except Exception as e:
                decision["status"] = "failed"
                decision["reasoning"] += f" | EXECUTION FAILED: {e}"

        self.store.insert("agent_decisions", decision)
        return decision

    def execute_negative_keyword(
        self,
        campaign_id: str,
        keyword_text: str,
        match_type: str = "NEGATIVE_EXACT",
        reasoning: str = "",
        session_id: str | None = None,
    ) -> dict:
        """Add a negative keyword to a campaign."""
        decision = {
            "session_id": session_id,
            "decision_type": "negation",
            "entity_type": "keyword",
            "entity_name": keyword_text,
            "entity_id": campaign_id,
            "reasoning": reasoning,
            "guardrail_check": "PASS",
            "status": "executed" if not self.dry_run else "dry_run",
        }

        if not self.dry_run:
            try:
                result = self.sp.create_campaign_negative_keywords([{
                    "campaignId": campaign_id,
                    "keywordText": keyword_text,
                    "matchType": match_type,
                    "state": "ENABLED",
                }])
                decision["executed_at"] = datetime.now().isoformat()
                decision["status"] = "executed"
            except Exception as e:
                decision["status"] = "failed"
                decision["reasoning"] += f" | EXECUTION FAILED: {e}"

        # Also log in negative_keywords table
        self.store.insert("negative_keywords", {
            "keyword_text": keyword_text,
            "match_type": match_type,
            "campaign_id": campaign_id,
            "reason": reasoning,
            "source": "agent",
        })

        self.store.insert("agent_decisions", decision)
        return decision

    def execute_pause_campaign(
        self,
        campaign_id: str,
        reasoning: str,
        session_id: str | None = None,
    ) -> dict:
        """Pause a campaign."""
        decision = {
            "session_id": session_id,
            "decision_type": "pause_campaign",
            "entity_type": "campaign",
            "entity_id": campaign_id,
            "reasoning": reasoning,
            "guardrail_check": "PASS",
            "status": "executed" if not self.dry_run else "dry_run",
        }

        if not self.dry_run:
            try:
                result = self.sp.pause_campaign(campaign_id)
                decision["executed_at"] = datetime.now().isoformat()
                decision["status"] = "executed"
            except Exception as e:
                decision["status"] = "failed"
                decision["reasoning"] += f" | EXECUTION FAILED: {e}"

        self.store.insert("agent_decisions", decision)
        return decision

    def execute_action(self, action: dict, session_id: str | None = None) -> dict:
        """Execute a generic action from the rules engine or LLM."""
        action_type = action.get("action_type", "")

        if action_type in ("bid_increase", "bid_decrease"):
            return self.execute_bid_change(
                keyword_id=action["entity_id"],
                current_bid=action.get("current_value", 0),
                new_bid=action.get("recommended_value", 0),
                reasoning=action.get("rationale", ""),
                session_id=session_id,
            )
        elif action_type in ("budget_increase", "budget_decrease"):
            return self.execute_budget_change(
                campaign_id=action["entity_id"],
                current_budget=action.get("current_value", 0),
                new_budget=action.get("recommended_value", 0),
                reasoning=action.get("rationale", ""),
                session_id=session_id,
            )
        elif action_type == "negate":
            return self.execute_negative_keyword(
                campaign_id=action["campaign_id"],
                keyword_text=action["entity_name"],
                reasoning=action.get("rationale", ""),
                session_id=session_id,
            )
        elif action_type == "pause":
            return self.execute_pause_campaign(
                campaign_id=action["entity_id"],
                reasoning=action.get("rationale", ""),
                session_id=session_id,
            )
        else:
            return {
                "status": "skipped",
                "reason": f"Unknown action type: {action_type}",
            }
