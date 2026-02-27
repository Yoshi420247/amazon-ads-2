#!/usr/bin/env python3
"""Pull all campaign data from Amazon Ads API and store snapshots.

Usage:
    python scripts/pull_data.py              # Pull last 30 days
    python scripts/pull_data.py --days 60    # Pull last 60 days
    python scripts/pull_data.py --campaigns  # Pull campaigns only (no reports)
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.client import SPClient
from src.agents.observer import Observer


def main():
    parser = argparse.ArgumentParser(description="Pull Amazon Ads data")
    parser.add_argument("--days", type=int, default=30, help="Days of history to pull")
    parser.add_argument("--campaigns", action="store_true", help="Pull campaigns only, skip reports")
    parser.add_argument("--output", type=str, help="Save raw data to JSON file")
    args = parser.parse_args()

    observer = Observer()

    if args.campaigns:
        campaigns = observer.pull_campaigns()
        print(f"\nPulled {len(campaigns)} campaigns:")
        for c in campaigns:
            state = c.get("state", "?")
            name = c.get("name", "?")
            budget = c.get("budget", {}).get("budget", 0)
            print(f"  [{state:8s}] {name} (budget: ${budget})")

        if args.output:
            Path(args.output).write_text(json.dumps(campaigns, indent=2, default=str))
            print(f"\nSaved to {args.output}")
    else:
        print(f"Starting full data pull (last {args.days} days)...")
        results = observer.full_pull(days_back=args.days)
        print(f"\nResults: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()
