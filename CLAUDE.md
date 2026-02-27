# Amazon Ads Agentic Operating System

## What This Is

An AI-powered Amazon PPC management system. Claude acts as the strategist, analyst, and operator — pulling data from the Amazon Ads API, analyzing performance, making optimization decisions, and executing changes directly.

## Project Structure

```
src/
  api/          Amazon Advertising API client
    auth.py     OAuth 2.0 token management
    client.py   API client + Sponsored Products operations
  db/           Persistent memory layer
    client.py   Supabase or local JSON storage
  engine/       Decision-making logic
    rules.py    Deterministic rules engine (zero API cost)
    guardrails.py  Safety limits on all actions
    health.py   Campaign/keyword health scoring
  agents/       Agentic loop components
    observer.py   Pull fresh data (OBSERVE step)
    executor.py   Apply changes via API (EXECUTE step)
    reporter.py   Generate reports (REPORT step)
scripts/
  test_api.py           Test API connectivity
  pull_data.py          Pull campaign data
  daily_optimization.py Full daily optimization cycle
migrations/
  001_initial_schema.sql  Supabase database schema
```

## How to Use

### Test API Connection
```bash
python scripts/test_api.py
```

### Pull Fresh Data
```bash
python scripts/pull_data.py                # Pull all data (30 days)
python scripts/pull_data.py --days 60      # Pull 60 days
python scripts/pull_data.py --campaigns    # Campaigns only
```

### Run Daily Optimization
```bash
python scripts/daily_optimization.py                     # Dry run
python scripts/daily_optimization.py --execute           # Live execution
python scripts/daily_optimization.py --target-acos 25    # Custom ACoS target
python scripts/daily_optimization.py --report-only       # Just generate report
```

## Guardrails (Safety Limits)

All actions must pass guardrail checks before execution:

**Hard Limits (cannot be overridden):**
- Maximum bid: $10.00
- Maximum daily budget: $500
- Maximum bid change: ±30% per adjustment
- Maximum budget change: ±20% per day
- Minimum 20 clicks before negating a keyword
- 7-day cooldown between bid changes on same keyword

**Soft Limits (can be overridden with reasoning):**
- Preferred bid change: ±15%
- Preferred 10-day evaluation period between changes
- New keyword bid: Historical CPC × 1.1

## Environment Variables

Required in `.env`:
```
AMAZON_ADS_CLIENT_ID=...
AMAZON_ADS_CLIENT_SECRET=...
AMAZON_ADS_REFRESH_TOKEN=...
AMAZON_ADS_PROFILE_ID=...
AMAZON_ADS_REGION=NA

# Optional - for Supabase persistent memory:
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## The Agentic Loop

1. **OBSERVE** - Pull fresh campaign, keyword, search term data
2. **THINK** - Analyze performance, detect anomalies, compare to history
3. **DECIDE** - Rules engine handles routine (60-70%), LLM handles complex
4. **EXECUTE** - Apply changes via API with guardrail validation
5. **REPORT** - Generate narrative summary with reasoning

## Rules Engine

The rules engine handles deterministic optimizations at zero cost:
- **Zero orders, high spend** → negate keyword
- **ACoS above target** → decrease bid
- **ACoS below target with volume** → increase bid
- **Low CTR** → flag for review
- **Search term converting** → graduate to exact match
- **Budget capped + good performance** → increase budget
