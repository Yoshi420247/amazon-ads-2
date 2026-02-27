"""Observer agent: pulls fresh data from Amazon Ads API.

Part of the OBSERVE step in the agentic loop.
Pulls campaign, keyword, search term, and placement data,
stores snapshots in the database.
"""

import time
from datetime import date, timedelta
from typing import Any

from ..api.client import AmazonAdsClient, SPClient
from ..db.client import get_store


class Observer:
    """Pulls current state from Amazon Ads and stores snapshots."""

    def __init__(self, sp_client: SPClient | None = None):
        self.sp = sp_client or SPClient()
        self.store = get_store()

    def pull_campaigns(self, states: list[str] | None = None) -> list[dict]:
        """Pull all campaigns and store snapshot."""
        campaigns = self.sp.list_all_campaigns(states=states)
        print(f"Pulled {len(campaigns)} campaigns")
        return campaigns

    def pull_ad_groups(self, campaign_id: str | None = None) -> list[dict]:
        """Pull ad groups, optionally filtered by campaign."""
        groups = self.sp.list_all_ad_groups(campaign_id=campaign_id)
        print(f"Pulled {len(groups)} ad groups")
        return groups

    def pull_keywords(self, campaign_id: str | None = None) -> list[dict]:
        """Pull all keywords, optionally filtered by campaign."""
        keywords = self.sp.list_all_keywords(campaign_id=campaign_id)
        print(f"Pulled {len(keywords)} keywords")
        return keywords

    def pull_report(
        self,
        report_type: str = "campaign",
        days_back: int = 30,
    ) -> list[dict]:
        """Request, wait for, and download a report.

        report_type: 'campaign', 'keyword', 'search_term', 'placement'
        """
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        print(f"Requesting {report_type} report: {start_str} to {end_str}...")

        request_fn = {
            "campaign": self.sp.request_campaign_report,
            "keyword": self.sp.request_keyword_report,
            "search_term": self.sp.request_search_term_report,
            "placement": self.sp.request_placement_report,
        }

        if report_type not in request_fn:
            raise ValueError(f"Unknown report type: {report_type}")

        result = request_fn[report_type](start_str, end_str)
        report_id = result.get("reportId")
        if not report_id:
            raise RuntimeError(f"No reportId in response: {result}")

        print(f"Report requested: {report_id}. Waiting for completion...")
        status = self.sp.wait_for_report(report_id)

        url = status.get("url")
        if not url:
            raise RuntimeError(f"No download URL in completed report: {status}")

        print("Downloading report...")
        data = self.sp.download_report(url)
        print(f"Downloaded {len(data)} rows")
        return data

    def store_campaign_snapshot(self, campaigns: list[dict], report_data: list[dict] | None = None):
        """Store campaign data as a snapshot in the database."""
        today = date.today().isoformat()
        rows = []

        # Build lookup from report data if available
        report_lookup = {}
        if report_data:
            for row in report_data:
                cid = row.get("campaignId")
                if cid:
                    report_lookup[str(cid)] = row

        for c in campaigns:
            cid = str(c.get("campaignId", ""))
            report = report_lookup.get(cid, {})

            spend = float(report.get("cost") or 0)
            impressions = int(report.get("impressions") or 0)
            clicks = int(report.get("clicks") or 0)
            orders_7d = int(report.get("purchases7d") or 0)
            sales_7d = float(report.get("sales7d") or 0)
            orders_14d = int(report.get("purchases14d") or 0)
            sales_14d = float(report.get("sales14d") or 0)

            row = {
                "snapshot_date": today,
                "campaign_id": cid,
                "campaign_name": c.get("name", ""),
                "state": c.get("state", ""),
                "daily_budget": c.get("budget", {}).get("budget", 0),
                "bidding_strategy": c.get("dynamicBidding", {}).get("strategy", ""),
                "impressions": impressions,
                "clicks": clicks,
                "spend": float(spend),
                "orders_7d": orders_7d,
                "sales_7d": float(sales_7d),
                "orders_14d": orders_14d,
                "sales_14d": float(sales_14d),
                "acos_7d": round(float(spend) / float(sales_7d) * 100, 2) if float(sales_7d) > 0 else 0,
                "acos_14d": round(float(spend) / float(sales_14d) * 100, 2) if float(sales_14d) > 0 else 0,
                "cpc": round(float(spend) / clicks, 4) if clicks > 0 else 0,
                "ctr": round(clicks / impressions, 4) if impressions > 0 else 0,
                "cvr_7d": round(orders_7d / clicks, 4) if clicks > 0 else 0,
            }
            rows.append(row)

        if rows:
            self.store.insert_many("campaign_snapshots", rows)
            print(f"Stored {len(rows)} campaign snapshots")

    def store_keyword_snapshot(self, report_data: list[dict]):
        """Store keyword report data as snapshots."""
        today = date.today().isoformat()
        rows = []
        for row in report_data:
            spend = float(row.get("cost") or 0)
            clicks = int(row.get("clicks") or 0)
            sales_7d = float(row.get("sales7d") or 0)
            orders_7d = int(row.get("purchases7d") or 0)

            rows.append({
                "snapshot_date": today,
                "campaign_name": row.get("campaignName") or "",
                "ad_group_name": row.get("adGroupName") or "",
                "keyword_text": row.get("keyword") or row.get("targeting") or "",
                "match_type": row.get("matchType") or row.get("keywordType") or "",
                "bid": float(row.get("keywordBid") or 0),
                "impressions": int(row.get("impressions") or 0),
                "clicks": clicks,
                "spend": spend,
                "orders_7d": orders_7d,
                "sales_7d": sales_7d,
                "acos_7d": round(spend / sales_7d * 100, 2) if sales_7d > 0 else 0,
                "cpc": round(spend / clicks, 4) if clicks > 0 else 0,
                "cvr_7d": round(orders_7d / clicks, 4) if clicks > 0 else 0,
            })

        if rows:
            self.store.insert_many("keyword_snapshots", rows)
            print(f"Stored {len(rows)} keyword snapshots")

    def store_search_term_snapshot(self, report_data: list[dict]):
        """Store search term report data as snapshots."""
        today = date.today().isoformat()
        rows = []
        for row in report_data:
            spend = float(row.get("cost") or 0)
            sales_7d = float(row.get("sales7d") or 0)

            rows.append({
                "snapshot_date": today,
                "campaign_name": row.get("campaignName") or "",
                "ad_group_name": row.get("adGroupName") or "",
                "targeting": row.get("targeting") or "",
                "search_term": row.get("searchTerm") or "",
                "impressions": int(row.get("impressions") or 0),
                "clicks": int(row.get("clicks") or 0),
                "spend": spend,
                "orders_7d": int(row.get("purchases7d") or 0),
                "sales_7d": sales_7d,
                "acos_7d": round(spend / sales_7d * 100, 2) if sales_7d > 0 else 0,
            })

        if rows:
            self.store.insert_many("search_term_reports", rows)
            print(f"Stored {len(rows)} search term snapshots")

    def full_pull(self, days_back: int = 30) -> dict:
        """Pull all data types and store snapshots. Returns summary."""
        results = {}

        # Pull live campaign data
        campaigns = self.pull_campaigns()
        results["campaigns"] = len(campaigns)

        # Pull reports
        try:
            campaign_report = self.pull_report("campaign", days_back)
            self.store_campaign_snapshot(campaigns, campaign_report)
            results["campaign_report_rows"] = len(campaign_report)
        except Exception as e:
            print(f"Campaign report failed: {e}")
            self.store_campaign_snapshot(campaigns)
            results["campaign_report_error"] = str(e)

        try:
            keyword_report = self.pull_report("keyword", days_back)
            self.store_keyword_snapshot(keyword_report)
            results["keyword_report_rows"] = len(keyword_report)
        except Exception as e:
            print(f"Keyword report failed: {e}")
            results["keyword_report_error"] = str(e)

        try:
            st_report = self.pull_report("search_term", days_back)
            self.store_search_term_snapshot(st_report)
            results["search_term_report_rows"] = len(st_report)
        except Exception as e:
            print(f"Search term report failed: {e}")
            results["search_term_report_error"] = str(e)

        return results
