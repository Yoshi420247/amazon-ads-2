"""Reporter agent: generates narrative performance reports.

Part of the REPORT step in the agentic loop.
Computes metrics and formats them for human consumption.
"""

from datetime import date, datetime
from typing import Any

from ..engine.health import HealthScore, compute_campaign_health


class Reporter:
    """Generates performance reports from campaign data."""

    def __init__(self, target_acos: float = 30.0):
        self.target_acos = target_acos

    def campaign_summary(self, campaigns: list[dict]) -> str:
        """Generate a campaign performance summary."""
        if not campaigns:
            return "No campaign data available."

        total_spend = sum(float(c.get("spend", 0) or c.get("cost", 0)) for c in campaigns)
        total_sales_7d = sum(float(c.get("sales_7d", 0) or c.get("sales7d", 0)) for c in campaigns)
        total_orders_7d = sum(int(c.get("orders_7d", 0) or c.get("purchases7d", 0)) for c in campaigns)
        total_clicks = sum(int(c.get("clicks", 0)) for c in campaigns)
        total_impressions = sum(int(c.get("impressions", 0)) for c in campaigns)
        overall_acos = (total_spend / total_sales_7d * 100) if total_sales_7d > 0 else 0
        overall_cpc = total_spend / total_clicks if total_clicks > 0 else 0
        overall_ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0
        overall_cvr = total_orders_7d / total_clicks * 100 if total_clicks > 0 else 0

        # Active vs paused
        active = [c for c in campaigns if c.get("state", "").upper() == "ENABLED"]
        paused = [c for c in campaigns if c.get("state", "").upper() == "PAUSED"]

        lines = [
            f"# Campaign Performance Summary",
            f"**Date:** {date.today().isoformat()}",
            f"",
            f"## Portfolio Overview",
            f"- **Total Campaigns:** {len(campaigns)} ({len(active)} active, {len(paused)} paused)",
            f"- **Total Spend:** ${total_spend:,.2f}",
            f"- **Total Sales (7d):** ${total_sales_7d:,.2f}",
            f"- **Total Orders (7d):** {total_orders_7d}",
            f"- **Overall ACoS:** {overall_acos:.1f}% (target: {self.target_acos}%)",
            f"- **Overall CPC:** ${overall_cpc:.2f}",
            f"- **Overall CTR:** {overall_ctr:.2f}%",
            f"- **Overall CVR:** {overall_cvr:.1f}%",
            f"- **Impressions:** {total_impressions:,}",
            f"",
        ]

        # Top performers
        performers = sorted(
            [c for c in campaigns if float(c.get("sales_7d", 0) or c.get("sales7d", 0)) > 0],
            key=lambda c: float(c.get("sales_7d", 0) or c.get("sales7d", 0)),
            reverse=True,
        )

        if performers:
            lines.append("## Top Performing Campaigns (by Sales)")
            for c in performers[:5]:
                name = c.get("campaign_name", c.get("name", c.get("campaignName", "Unknown")))
                spend = float(c.get("spend", 0) or c.get("cost", 0))
                sales = float(c.get("sales_7d", 0) or c.get("sales7d", 0))
                orders = int(c.get("orders_7d", 0) or c.get("purchases7d", 0))
                acos = (spend / sales * 100) if sales > 0 else 0
                lines.append(f"- **{name}**: ${sales:,.2f} sales, {orders} orders, {acos:.1f}% ACoS, ${spend:.2f} spend")
            lines.append("")

        # Problem campaigns
        problems = [
            c for c in campaigns
            if float(c.get("spend", 0) or c.get("cost", 0)) > 5
            and (
                float(c.get("sales_7d", 0) or c.get("sales7d", 0)) == 0
                or (
                    float(c.get("sales_7d", 0) or c.get("sales7d", 0)) > 0
                    and float(c.get("spend", 0) or c.get("cost", 0))
                    / float(c.get("sales_7d", 0) or c.get("sales7d", 0))
                    * 100
                    > self.target_acos * 1.5
                )
            )
        ]

        if problems:
            lines.append("## Campaigns Needing Attention")
            for c in sorted(problems, key=lambda c: float(c.get("spend", 0) or c.get("cost", 0)), reverse=True)[:5]:
                name = c.get("campaign_name", c.get("name", c.get("campaignName", "Unknown")))
                spend = float(c.get("spend", 0) or c.get("cost", 0))
                sales = float(c.get("sales_7d", 0) or c.get("sales7d", 0))
                acos = (spend / sales * 100) if sales > 0 else 0
                if sales == 0:
                    lines.append(f"- **{name}**: ${spend:.2f} spend, $0 sales (zero conversion)")
                else:
                    lines.append(f"- **{name}**: {acos:.1f}% ACoS (>${self.target_acos * 1.5:.0f}% threshold), ${spend:.2f} spend")
            lines.append("")

        return "\n".join(lines)

    def health_report(self, campaigns: list[dict]) -> str:
        """Generate health scores for all campaigns."""
        scores = []
        for c in campaigns:
            hs = compute_campaign_health(c, self.target_acos)
            name = c.get("campaign_name", c.get("name", c.get("campaignName", "Unknown")))
            scores.append((name, hs))

        scores.sort(key=lambda x: x[1].weighted_score, reverse=True)

        lines = [
            "## Campaign Health Scores",
            f"*Sorted by spend-weighted score (highest impact first)*",
            "",
        ]

        for name, hs in scores[:20]:
            lines.append(f"- [{hs.grade}] **{name}** (score: {hs.score}/100)")
            for factor, detail in hs.factors.items():
                lines.append(f"  - {factor}: {detail}")

        return "\n".join(lines)

    def actions_summary(self, actions: list[dict]) -> str:
        """Summarize proposed or executed actions."""
        if not actions:
            return "No actions to report."

        lines = [
            "## Optimization Actions",
            f"**Total actions:** {len(actions)}",
            "",
        ]

        by_type: dict[str, list] = {}
        for a in actions:
            t = a.get("action_type", a.get("decision_type", "unknown"))
            by_type.setdefault(t, []).append(a)

        for action_type, items in by_type.items():
            lines.append(f"### {action_type.replace('_', ' ').title()} ({len(items)})")
            for item in items[:10]:
                name = item.get("entity_name", item.get("entity_id", "Unknown"))
                rationale = item.get("rationale", item.get("reasoning", ""))
                status = item.get("status", "pending")
                lines.append(f"- **{name}** [{status}]: {rationale}")
            if len(items) > 10:
                lines.append(f"  *(+ {len(items) - 10} more)*")
            lines.append("")

        return "\n".join(lines)
