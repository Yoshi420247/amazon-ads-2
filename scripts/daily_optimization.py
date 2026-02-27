#!/usr/bin/env python3
"""Daily optimization cycle - the core agentic loop.

This script implements the OBSERVE -> THINK -> DECIDE -> EXECUTE -> REPORT cycle.

Usage:
    python scripts/daily_optimization.py                    # Dry run (recommend only)
    python scripts/daily_optimization.py --execute          # Execute approved actions
    python scripts/daily_optimization.py --target-acos 25   # Custom target ACoS
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.client import SPClient
from src.agents.observer import Observer
from src.agents.executor import Executor
from src.agents.reporter import Reporter
from src.engine.rules import RulesEngine
from src.engine.guardrails import Guardrails
from src.db.client import get_store


def main():
    parser = argparse.ArgumentParser(description="Daily optimization cycle")
    parser.add_argument("--execute", action="store_true", help="Execute changes (default: dry run)")
    parser.add_argument("--target-acos", type=float, default=30.0, help="Target ACoS percentage")
    parser.add_argument("--days", type=int, default=30, help="Days of report data to analyze")
    parser.add_argument("--report-only", action="store_true", help="Skip optimization, just report")
    parser.add_argument("--output", type=str, help="Save report to file")
    args = parser.parse_args()

    store = get_store()
    sp = SPClient()
    observer = Observer(sp)
    rules = RulesEngine(target_acos=args.target_acos)
    guardrails = Guardrails()
    executor = Executor(sp, guardrails, dry_run=not args.execute)
    reporter = Reporter(target_acos=args.target_acos)

    # Log session start
    session = {
        "session_type": "daily_optimization",
        "started_at": datetime.now().isoformat(),
        "status": "running",
    }
    store.insert("agent_sessions", session)

    print("=" * 60)
    print(f"  DAILY OPTIMIZATION - {date.today().isoformat()}")
    print(f"  Target ACoS: {args.target_acos}%")
    print(f"  Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print("=" * 60)

    # ── STEP 1: OBSERVE ──────────────────────────────────────
    print("\n[1/5] OBSERVE: Pulling fresh data...")

    campaigns = observer.pull_campaigns()
    active_campaigns = [c for c in campaigns if c.get("state") == "ENABLED"]
    print(f"  {len(campaigns)} total campaigns ({len(active_campaigns)} active)")

    campaign_report = []
    keyword_report = []
    search_term_report = []

    try:
        campaign_report = observer.pull_report("campaign", days_back=args.days)
        print(f"  Campaign report: {len(campaign_report)} rows")
    except Exception as e:
        print(f"  Campaign report failed: {e}")

    try:
        keyword_report = observer.pull_report("keyword", days_back=args.days)
        print(f"  Keyword report: {len(keyword_report)} rows")
    except Exception as e:
        print(f"  Keyword report failed: {e}")

    try:
        search_term_report = observer.pull_report("search_term", days_back=args.days)
        print(f"  Search term report: {len(search_term_report)} rows")
    except Exception as e:
        print(f"  Search term report failed: {e}")

    # Store snapshots
    observer.store_campaign_snapshot(campaigns, campaign_report)
    if keyword_report:
        observer.store_keyword_snapshot(keyword_report)
    if search_term_report:
        observer.store_search_term_snapshot(search_term_report)

    # ── STEP 2: THINK (Generate Report) ──────────────────────
    print("\n[2/5] THINK: Analyzing performance...")

    report = reporter.campaign_summary(campaign_report or campaigns)
    health = reporter.health_report(campaign_report or campaigns)

    print(report)
    print()
    print(health)

    if args.report_only:
        if args.output:
            Path(args.output).write_text(f"{report}\n\n{health}")
            print(f"\nReport saved to {args.output}")
        return

    # ── STEP 3: DECIDE (Rules Engine) ────────────────────────
    print("\n[3/5] DECIDE: Running rules engine...")

    # Normalize report data for rules engine
    normalized_keywords = []
    for row in keyword_report:
        normalized_keywords.append({
            "keyword_id": row.get("keywordId", ""),
            "keyword_text": row.get("keyword", row.get("targeting", "")),
            "campaign_id": row.get("campaignId", ""),
            "campaign_name": row.get("campaignName", ""),
            "bid": float(row.get("keywordBid", 0)),
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "spend": float(row.get("cost", 0)),
            "orders_7d": int(row.get("purchases7d", 0)),
            "sales_7d": float(row.get("sales7d", 0)),
        })

    normalized_search_terms = []
    for row in search_term_report:
        normalized_search_terms.append({
            "search_term": row.get("searchTerm", ""),
            "campaign_id": row.get("campaignId", ""),
            "campaign_name": row.get("campaignName", ""),
            "clicks": int(row.get("clicks", 0)),
            "spend": float(row.get("cost", 0)),
            "orders_7d": int(row.get("purchases7d", 0)),
            "sales_7d": float(row.get("sales7d", 0)),
        })

    normalized_campaigns = []
    for row in campaign_report:
        normalized_campaigns.append({
            "campaign_id": row.get("campaignId", ""),
            "campaign_name": row.get("campaignName", ""),
            "spend": float(row.get("cost", 0)),
            "daily_budget": float(row.get("campaignBudgetAmount", 0)),
            "orders_7d": int(row.get("purchases7d", 0)),
            "sales_7d": float(row.get("sales7d", 0)),
            "acos_7d": (float(row.get("cost", 0)) / float(row.get("sales7d", 1)) * 100)
                if float(row.get("sales7d", 0)) > 0 else 0,
        })

    actions = rules.run_all(normalized_campaigns, normalized_keywords, normalized_search_terms)
    print(f"  Rules engine produced {len(actions)} actions")

    actions_report = reporter.actions_summary(
        [{"action_type": a.action_type, "entity_name": a.entity_name, "rationale": a.rationale,
          "status": "pending"} for a in actions]
    )
    print(actions_report)

    # ── STEP 4: EXECUTE ──────────────────────────────────────
    print(f"\n[4/5] EXECUTE: {'Applying' if args.execute else 'Would apply'} {len(actions)} actions...")

    results = []
    for action in actions:
        action_dict = {
            "action_type": action.action_type,
            "entity_type": action.entity_type,
            "entity_id": action.entity_id,
            "entity_name": action.entity_name,
            "campaign_id": action.campaign_id,
            "current_value": action.current_value,
            "recommended_value": action.recommended_value,
            "rationale": action.rationale,
        }
        result = executor.execute_action(action_dict)
        results.append(result)
        status = result.get("status", "unknown")
        print(f"  [{status:8s}] {action.entity_name}: {action.rationale[:80]}")

    # ── STEP 5: REPORT ───────────────────────────────────────
    print("\n[5/5] REPORT: Summary")

    executed = sum(1 for r in results if r.get("status") in ("executed", "dry_run"))
    blocked = sum(1 for r in results if r.get("status") == "blocked")
    failed = sum(1 for r in results if r.get("status") == "failed")

    summary = f"""
## Daily Optimization Summary - {date.today().isoformat()}
- **Mode:** {'LIVE' if args.execute else 'DRY RUN'}
- **Actions produced:** {len(actions)}
- **Executed:** {executed}
- **Blocked by guardrails:** {blocked}
- **Failed:** {failed}
"""
    print(summary)

    # Save full report
    full_report = f"{report}\n\n{health}\n\n{actions_report}\n\n{summary}"
    if args.output:
        Path(args.output).write_text(full_report)
        print(f"Full report saved to {args.output}")
    else:
        report_path = Path("data/reports") / f"daily_{date.today().isoformat()}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(full_report)
        print(f"Full report saved to {report_path}")


if __name__ == "__main__":
    main()
