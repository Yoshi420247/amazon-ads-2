#!/usr/bin/env python3
"""Quick test of Amazon Ads API connectivity.

Usage:
    python scripts/test_api.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.auth import TokenManager, Credentials
from src.api.client import AmazonAdsClient, SPClient


def main():
    print("Testing Amazon Ads API connection...\n")

    # Test 1: Token refresh
    print("[1] Token refresh...")
    try:
        creds = Credentials.from_env()
        tm = TokenManager(creds)
        token = tm.refresh()
        print(f"    OK - Got access token ({token[:20]}...)")
    except Exception as e:
        print(f"    FAILED - {e}")
        return

    # Test 2: List campaigns
    print("[2] List campaigns...")
    try:
        sp = SPClient()
        campaigns = sp.list_all_campaigns()
        active = [c for c in campaigns if c.get("state") == "ENABLED"]
        paused = [c for c in campaigns if c.get("state") == "PAUSED"]
        print(f"    OK - {len(campaigns)} campaigns ({len(active)} active, {len(paused)} paused)")

        if active:
            print("\n    Active campaigns:")
            for c in active[:10]:
                budget = c.get("budget", {}).get("budget", "?")
                strategy = c.get("dynamicBidding", {}).get("strategy", "?")
                print(f"      - {c['name']} (budget: ${budget}, bidding: {strategy})")
    except Exception as e:
        print(f"    FAILED - {e}")
        return

    # Test 3: List ad groups for first active campaign
    if active:
        print(f"\n[3] List ad groups for '{active[0]['name']}'...")
        try:
            groups = sp.list_all_ad_groups(campaign_id=active[0]["campaignId"])
            print(f"    OK - {len(groups)} ad groups")
            for g in groups[:5]:
                print(f"      - {g.get('name', '?')} (state: {g.get('state', '?')})")
        except Exception as e:
            print(f"    FAILED - {e}")

    # Test 4: List keywords
    if active:
        print(f"\n[4] List keywords for '{active[0]['name']}'...")
        try:
            keywords = sp.list_all_keywords(campaign_id=active[0]["campaignId"])
            print(f"    OK - {len(keywords)} keywords")
            for kw in keywords[:5]:
                print(f"      - [{kw.get('matchType', '?'):8s}] {kw.get('keywordText', '?')} (bid: ${kw.get('bid', 0)})")
        except Exception as e:
            print(f"    FAILED - {e}")

    print("\n--- All tests complete ---")


if __name__ == "__main__":
    main()
