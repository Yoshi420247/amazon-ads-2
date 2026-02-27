"""Base Amazon Advertising API client.

Provides authenticated HTTP methods for all Amazon Ads API endpoints.
All specific modules (campaigns, keywords, etc.) build on this.
"""

from typing import Any

import httpx

from .auth import Credentials, TokenManager

# Amazon Ads API version
SP_API_VERSION = "v2"  # Sponsored Products v2
SP_V3_PREFIX = "/sp"   # v3 endpoints use /sp prefix


class AmazonAdsClient:
    """Authenticated client for the Amazon Advertising API."""

    def __init__(self, credentials: Credentials | None = None):
        self.credentials = credentials or Credentials.from_env()
        self.token_manager = TokenManager(self.credentials)
        self._http = httpx.Client(
            base_url=self.credentials.api_base_url,
            timeout=60,
        )

    def _headers(self, **extra) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token_manager.get_access_token()}",
            "Amazon-Advertising-API-ClientId": self.credentials.client_id,
            "Amazon-Advertising-API-Scope": self.credentials.profile_id,
            "Content-Type": "application/vnd.spCampaign.v3+json",
            "Accept": "application/vnd.spCampaign.v3+json",
        }
        headers.update(extra)
        return headers

    def get(self, path: str, params: dict | None = None, **header_overrides) -> Any:
        resp = self._http.get(path, params=params, headers=self._headers(**header_overrides))
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, json: dict | list | None = None, **header_overrides) -> Any:
        resp = self._http.post(path, json=json, headers=self._headers(**header_overrides))
        resp.raise_for_status()
        return resp.json()

    def put(self, path: str, json: dict | list | None = None, **header_overrides) -> Any:
        resp = self._http.put(path, json=json, headers=self._headers(**header_overrides))
        resp.raise_for_status()
        return resp.json()

    def delete(self, path: str, **header_overrides) -> Any:
        resp = self._http.delete(path, headers=self._headers(**header_overrides))
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class SPClient:
    """Sponsored Products specific client with convenience methods."""

    def __init__(self, client: AmazonAdsClient | None = None):
        self.client = client or AmazonAdsClient()

    # ── Campaigns ──────────────────────────────────────────────

    def list_campaigns(
        self,
        states: list[str] | None = None,
        max_results: int = 100,
        next_token: str | None = None,
    ) -> dict:
        """List SP campaigns with optional state filter."""
        body: dict[str, Any] = {"maxResults": max_results}
        if states:
            body["stateFilter"] = {"include": states}
        if next_token:
            body["nextToken"] = next_token
        return self.client.post("/sp/campaigns/list", json=body)

    def list_all_campaigns(self, states: list[str] | None = None) -> list[dict]:
        """Paginate through all campaigns."""
        all_campaigns = []
        next_token = None
        while True:
            resp = self.list_campaigns(states=states, max_results=100, next_token=next_token)
            all_campaigns.extend(resp.get("campaigns", []))
            next_token = resp.get("nextToken")
            if not next_token:
                break
        return all_campaigns

    def get_campaign(self, campaign_id: str) -> dict:
        return self.client.post(
            "/sp/campaigns/list",
            json={"campaignIdFilter": {"include": [campaign_id]}},
        )

    def update_campaign(self, campaign_id: str, **updates) -> dict:
        """Update a campaign. Common updates: state, budget, name, biddingStrategy."""
        body = {"campaignId": campaign_id, **updates}
        return self.client.put("/sp/campaigns", json={"campaigns": [body]})

    def update_campaign_budget(self, campaign_id: str, daily_budget: float) -> dict:
        return self.update_campaign(
            campaign_id, budget={"budgetType": "DAILY", "budget": daily_budget}
        )

    def pause_campaign(self, campaign_id: str) -> dict:
        return self.update_campaign(campaign_id, state="PAUSED")

    def enable_campaign(self, campaign_id: str) -> dict:
        return self.update_campaign(campaign_id, state="ENABLED")

    # ── Ad Groups ──────────────────────────────────────────────

    def list_ad_groups(
        self,
        campaign_id: str | None = None,
        max_results: int = 100,
        next_token: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"maxResults": max_results}
        if campaign_id:
            body["campaignIdFilter"] = {"include": [campaign_id]}
        if next_token:
            body["nextToken"] = next_token

        headers = {
            "Content-Type": "application/vnd.spAdGroup.v3+json",
            "Accept": "application/vnd.spAdGroup.v3+json",
        }
        return self.client.post("/sp/adGroups/list", json=body, **headers)

    def list_all_ad_groups(self, campaign_id: str | None = None) -> list[dict]:
        all_groups = []
        next_token = None
        while True:
            resp = self.list_ad_groups(
                campaign_id=campaign_id, max_results=100, next_token=next_token,
            )
            all_groups.extend(resp.get("adGroups", []))
            next_token = resp.get("nextToken")
            if not next_token:
                break
        return all_groups

    # ── Keywords ───────────────────────────────────────────────

    def list_keywords(
        self,
        campaign_id: str | None = None,
        ad_group_id: str | None = None,
        max_results: int = 100,
        next_token: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"maxResults": max_results}
        if campaign_id:
            body["campaignIdFilter"] = {"include": [campaign_id]}
        if ad_group_id:
            body["adGroupIdFilter"] = {"include": [ad_group_id]}
        if next_token:
            body["nextToken"] = next_token

        headers = {
            "Content-Type": "application/vnd.spKeyword.v3+json",
            "Accept": "application/vnd.spKeyword.v3+json",
        }
        return self.client.post("/sp/keywords/list", json=body, **headers)

    def list_all_keywords(
        self,
        campaign_id: str | None = None,
        ad_group_id: str | None = None,
    ) -> list[dict]:
        all_kws = []
        next_token = None
        while True:
            resp = self.list_keywords(
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                max_results=100,
                next_token=next_token,
            )
            all_kws.extend(resp.get("keywords", []))
            next_token = resp.get("nextToken")
            if not next_token:
                break
        return all_kws

    def create_keywords(self, keywords: list[dict]) -> dict:
        """Create keywords. Each dict needs: campaignId, adGroupId, keywordText, matchType, bid."""
        headers = {
            "Content-Type": "application/vnd.spKeyword.v3+json",
            "Accept": "application/vnd.spKeyword.v3+json",
        }
        return self.client.post("/sp/keywords", json={"keywords": keywords}, **headers)

    def update_keywords(self, keywords: list[dict]) -> dict:
        """Update keywords. Each dict needs: keywordId, plus fields to update (bid, state)."""
        headers = {
            "Content-Type": "application/vnd.spKeyword.v3+json",
            "Accept": "application/vnd.spKeyword.v3+json",
        }
        return self.client.put("/sp/keywords", json={"keywords": keywords}, **headers)

    def update_keyword_bid(self, keyword_id: str, new_bid: float) -> dict:
        return self.update_keywords([{"keywordId": keyword_id, "bid": new_bid}])

    # ── Negative Keywords ──────────────────────────────────────

    def list_negative_keywords(
        self,
        campaign_id: str | None = None,
        max_results: int = 100,
        next_token: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"maxResults": max_results}
        if campaign_id:
            body["campaignIdFilter"] = {"include": [campaign_id]}
        if next_token:
            body["nextToken"] = next_token

        headers = {
            "Content-Type": "application/vnd.spNegativeKeyword.v3+json",
            "Accept": "application/vnd.spNegativeKeyword.v3+json",
        }
        return self.client.post("/sp/negativeKeywords/list", json=body, **headers)

    def create_negative_keywords(self, negatives: list[dict]) -> dict:
        """Add negative keywords. Each dict needs: campaignId, adGroupId, keywordText, matchType."""
        headers = {
            "Content-Type": "application/vnd.spNegativeKeyword.v3+json",
            "Accept": "application/vnd.spNegativeKeyword.v3+json",
        }
        return self.client.post(
            "/sp/negativeKeywords", json={"negativeKeywords": negatives}, **headers
        )

    # ── Campaign Negative Keywords ─────────────────────────────

    def create_campaign_negative_keywords(self, negatives: list[dict]) -> dict:
        """Add campaign-level negative keywords."""
        headers = {
            "Content-Type": "application/vnd.spCampaignNegativeKeyword.v3+json",
            "Accept": "application/vnd.spCampaignNegativeKeyword.v3+json",
        }
        return self.client.post(
            "/sp/campaignNegativeKeywords",
            json={"campaignNegativeKeywords": negatives},
            **headers,
        )

    # ── Targets (Product/Category Targeting) ───────────────────

    def list_targets(
        self,
        campaign_id: str | None = None,
        max_results: int = 100,
        next_token: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"maxResults": max_results}
        if campaign_id:
            body["campaignIdFilter"] = {"include": [campaign_id]}
        if next_token:
            body["nextToken"] = next_token

        headers = {
            "Content-Type": "application/vnd.spTargetingClause.v3+json",
            "Accept": "application/vnd.spTargetingClause.v3+json",
        }
        return self.client.post("/sp/targets/list", json=body, **headers)

    # ── Reports ────────────────────────────────────────────────

    def create_report(self, start_date: str, end_date: str, configuration: dict, name: str = "Report") -> dict:
        """Request an async report. Returns response with reportId."""
        headers = {
            "Content-Type": "application/vnd.createAsyncReportRequest.v3+json",
            "Accept": "application/vnd.createAsyncReportRequest.v3+json",
        }
        body = {
            "name": name,
            "startDate": start_date,
            "endDate": end_date,
            "configuration": {
                "adProduct": "SPONSORED_PRODUCTS",
                **configuration,
            },
        }
        return self.client.post("/reporting/reports", json=body, **headers)

    def get_report_status(self, report_id: str) -> dict:
        """Check if a report is ready."""
        return self.client.get(f"/reporting/reports/{report_id}")

    def download_report(self, url: str) -> list[dict]:
        """Download a completed report from its URL."""
        import gzip
        import json

        resp = httpx.get(url, timeout=120)
        resp.raise_for_status()
        try:
            data = gzip.decompress(resp.content)
            return json.loads(data)
        except gzip.BadGzipFile:
            return resp.json()

    def request_campaign_report(
        self,
        start_date: str,
        end_date: str,
        metrics: list[str] | None = None,
    ) -> dict:
        """Request a Sponsored Products campaign performance report."""
        if metrics is None:
            metrics = [
                "campaignName", "campaignId",
                "impressions", "clicks", "cost", "purchases7d", "sales7d",
                "purchases14d", "sales14d",
                "campaignBudgetAmount", "campaignStatus",
            ]
        return self.create_report(
            start_date, end_date,
            configuration={
                "reportTypeId": "spCampaigns",
                "groupBy": ["campaign"],
                "columns": metrics,
                "timeUnit": "SUMMARY",
                "format": "GZIP_JSON",
            },
            name="Campaign Performance Report",
        )

    def request_keyword_report(
        self,
        start_date: str,
        end_date: str,
        metrics: list[str] | None = None,
    ) -> dict:
        """Request a Sponsored Products keyword/targeting performance report."""
        if metrics is None:
            metrics = [
                "impressions", "clicks", "cost", "purchases7d", "sales7d",
                "purchases14d", "sales14d", "keywordBid",
                "campaignName", "adGroupName", "keyword", "matchType", "keywordType",
            ]
        return self.create_report(
            start_date, end_date,
            configuration={
                "reportTypeId": "spTargeting",
                "groupBy": ["targeting"],
                "columns": metrics,
                "timeUnit": "SUMMARY",
                "format": "GZIP_JSON",
            },
            name="Keyword Performance Report",
        )

    def request_search_term_report(
        self,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Request a search term report."""
        return self.create_report(
            start_date, end_date,
            configuration={
                "reportTypeId": "spSearchTerm",
                "groupBy": ["searchTerm"],
                "columns": [
                    "impressions", "clicks", "cost", "purchases7d", "sales7d",
                    "purchases14d", "sales14d",
                    "campaignName", "adGroupName", "targeting", "searchTerm",
                ],
                "timeUnit": "SUMMARY",
                "format": "GZIP_JSON",
            },
            name="Search Term Report",
        )

    def request_placement_report(
        self,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Request a placement performance report."""
        return self.create_report(
            start_date, end_date,
            configuration={
                "reportTypeId": "spCampaigns",
                "groupBy": ["campaign"],
                "columns": [
                    "impressions", "clicks", "cost", "purchases7d", "sales7d",
                    "campaignBudgetAmount", "placementClassification",
                ],
                "timeUnit": "SUMMARY",
                "format": "GZIP_JSON",
            },
            name="Placement Performance Report",
        )

    def wait_for_report(self, report_id: str, max_wait: int = 300, poll_interval: int = 5) -> dict:
        """Poll until report is ready, then return the download URL."""
        import time

        elapsed = 0
        while elapsed < max_wait:
            status = self.get_report_status(report_id)
            if status.get("status") == "COMPLETED":
                return status
            if status.get("status") == "FAILURE":
                raise RuntimeError(f"Report failed: {status}")
            time.sleep(poll_interval)
            elapsed += poll_interval
        raise TimeoutError(f"Report {report_id} not ready after {max_wait}s")
