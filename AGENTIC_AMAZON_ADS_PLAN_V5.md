# Agentic Amazon Ads Operating System: Master Plan V5.0
## Claude Opus 4.6 as Autonomous Campaign Strategist & Operator

---

## Vision

**Replace Perpetua ($695+/mo) and Quartile ($5K+/mo) with Claude Opus 4.6 as your full-stack Amazon advertising strategist, analyst, and operator.** Not a dashboard that shows you recommendations — an AI agent that thinks deeply about your campaigns, reasons through strategy, and executes changes directly via the Amazon Ads MCP Server.

This is what happens when you combine:
- **Deep extended thinking** (Opus 4.6 reasoning through multi-variable campaign strategy)
- **Amazon Ads MCP Server** (direct API execution — create campaigns, adjust bids, manage keywords, pull reports through natural language)
- **Historical intelligence** (Supabase as persistent memory — every decision, every outcome, every trend)
- **Agentic loops** (Claude doesn't just answer questions — it researches, hypothesizes, validates, executes, and learns)

---

## Architecture: Three-Layer Agentic Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: AGENTIC BRAIN                    │
│              Claude Opus 4.6 (Extended Thinking)             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   Strategist  │  │   Analyst    │  │    Operator       │  │
│  │               │  │              │  │                   │  │
│  │ Campaign      │  │ Performance  │  │ Execute bids      │  │
│  │ architecture  │  │ deep-dives   │  │ Create campaigns  │  │
│  │ Budget alloc  │  │ Trend detect │  │ Add/negate KWs    │  │
│  │ Market pos    │  │ Anomaly root │  │ Adjust budgets    │  │
│  │ Competitive   │  │ cause        │  │ Pause/enable      │  │
│  │ strategy      │  │ Attribution  │  │ Generate reports  │  │
│  │               │  │ analysis     │  │                   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬────────────┘  │
│         │                 │                  │               │
└─────────┼─────────────────┼──────────────────┼───────────────┘
          │                 │                  │
┌─────────┼─────────────────┼──────────────────┼───────────────┐
│         ▼                 ▼                  ▼               │
│                    LAYER 2: MCP SERVERS                       │
│           (Tools Claude Uses to See & Act)                    │
│                                                              │
│  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │  Supabase MCP     │  │  Amazon Ads MCP Server         │   │
│  │                   │  │  (Open Beta - Feb 2025)        │   │
│  │  • Query history  │  │                                │   │
│  │  • Store decisions│  │  • Campaign CRUD               │   │
│  │  • Track outcomes │  │  • Bid management              │   │
│  │  • Trend data     │  │  • Keyword operations          │   │
│  │  • Product data   │  │  • Budget adjustments          │   │
│  │  • Rules config   │  │  • Report generation           │   │
│  │  • Audit trail    │  │  • Geographic expansion        │   │
│  │                   │  │  • Account-level operations     │   │
│  └───────────────────┘  └────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │  Filesystem MCP   │  │  Web Search / Fetch            │   │
│  │                   │  │                                │   │
│  │  • Read/write     │  │  • Competitor research         │   │
│  │    local files    │  │  • Market trends               │   │
│  │  • Export reports │  │  • Keyword ideas               │   │
│  │  • Bulksheet gen  │  │  • Category intelligence       │   │
│  └───────────────────┘  └────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
          │                 │                  │
┌─────────┼─────────────────┼──────────────────┼───────────────┐
│         ▼                 ▼                  ▼               │
│                LAYER 1: PERSISTENT MEMORY                     │
│                      (Supabase)                               │
│                                                              │
│  Campaign history • Decision logs • Performance snapshots    │
│  Product profiles • Keyword intelligence • SOV trends        │
│  Rules config • Execution audit trail • Strategy docs        │
│  Attribution data • Competitive intel • Budget tracking       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## What Makes This Different From V4.2 (Web App) Approach

| Dimension | V4.2 (Web App + Rules Engine) | V5.0 (Agentic Opus 4.6) |
|-----------|-------------------------------|--------------------------|
| **Interface** | Web dashboard you log into | Claude Code session you talk to |
| **Decision maker** | Rules engine (60-70%) + LLM suggestions | Claude reasons through everything with extended thinking |
| **Execution** | Generate bulksheet → manual upload | Amazon Ads MCP Server → direct API execution |
| **Strategy** | Predefined decision trees | Opus 4.6 builds strategy from first principles per your business |
| **Adaptability** | Edit rule thresholds manually | Claude learns from outcomes and adjusts approach |
| **Depth of analysis** | Module-specific prompts | Full-context reasoning across all data simultaneously |
| **Competitive intel** | Structured module output | Live web research + Brand Analytics + reasoning |
| **Reporting** | Dashboard charts | Claude writes you narrative strategy reports with reasoning |
| **Cost** | ~$20/mo (Vercel) + ~$5/mo (API) | ~$0 infra + API usage costs per session |
| **Setup** | Build entire Next.js app | Connect MCP servers + create database schema |

---

## How It Works: The Agentic Loop

### Daily Automated Cycle (can be scheduled via cron or on-demand)

```
1. OBSERVE
   Claude pulls fresh data via Amazon Ads MCP Server:
   - Campaign performance (last 7d, 14d, 30d)
   - Search term reports
   - Placement performance
   - Budget utilization

   Claude queries Supabase for:
   - Historical snapshots (trend comparison)
   - Previous decisions and their outcomes
   - Product profiles and targets
   - Active strategy notes

2. THINK (Extended Thinking — this is where Opus 4.6 shines)
   Claude reasons through:
   - What changed since last review?
   - Which campaigns are off-target and why?
   - Are there anomalies that need investigation?
   - What is the attribution-adjusted performance?
   - Are previous bid changes producing expected results?
   - What is the competitive landscape signaling?
   - What should the bid/budget strategy be for the NEXT period?

3. DECIDE
   Claude produces a structured action plan:
   - Bid adjustments (with reasoning for each)
   - Keyword additions/negations (with evidence)
   - Budget reallocations (with expected impact)
   - Campaign structural changes (if needed)
   - Items requiring human review (flagged with urgency)

4. EXECUTE (with guardrails)
   Via Amazon Ads MCP Server:
   - Apply approved bid changes
   - Add negative keywords
   - Adjust budgets
   - Create new campaigns/ad groups if strategy calls for it

   Via Supabase MCP:
   - Log every action with reasoning
   - Store performance snapshot
   - Update strategy state
   - Record expected outcomes for future validation

5. REPORT
   Claude writes a narrative summary:
   - What was done and why
   - Key metrics and trends
   - Concerns or items needing attention
   - Strategic outlook for next period
```

### Weekly Strategic Review (Deep Thinking Session)

```
1. DEEP ANALYSIS (Opus 4.6 extended thinking — minutes of reasoning)
   - Full portfolio performance review
   - Keyword-level P&L analysis
   - Search term mining across all campaigns
   - Share of Voice trend analysis (Brand Analytics)
   - Competitive position assessment
   - TACoS trajectory and organic halo effect
   - Campaign lifecycle stage assessment
   - Budget allocation efficiency across portfolio

2. STRATEGIC RECOMMENDATIONS
   - Campaign architecture changes
   - New keyword opportunities (4-layer discovery)
   - Competitive targeting adjustments
   - Budget rebalancing across campaigns
   - Lifecycle phase transitions
   - Launch/scale/maintain/sunset decisions

3. EXECUTION PLAN
   - Prioritized action list with expected impact
   - Risk assessment for each major change
   - Rollback plan if results disappoint
   - Timeline for evaluation
```

### Monthly Business Review

```
1. COMPREHENSIVE REPORTING
   - Month-over-month performance narrative
   - TACoS trend and organic growth attribution
   - SOV movement and market position
   - ROI analysis by campaign/product/keyword tier
   - Competitive landscape changes
   - Strategy effectiveness assessment

2. STRATEGY EVOLUTION
   - Adjust target ACoS based on margin/inventory
   - Evolve campaign architecture based on data
   - Update competitive positioning
   - Set objectives for next month
```

---

## Amazon Ads MCP Server: The Execution Layer

### What It Is
Amazon's official MCP (Model Context Protocol) server, launched in open beta. It translates natural language into structured Amazon Ads API calls, enabling AI agents to manage campaigns directly.

### Key Capabilities
Claude can execute through the MCP Server:

| Action | What Claude Can Do |
|--------|-------------------|
| **Campaign Management** | Create, update, pause, enable, archive campaigns |
| **Bid Management** | Adjust keyword bids, placement modifiers, default bids |
| **Keyword Operations** | Add keywords, change match types, adjust bids per keyword |
| **Negative Keywords** | Add negative keywords at campaign or ad group level |
| **Budget Management** | Set/adjust daily budgets, portfolio budgets |
| **Targeting** | Add/remove product targeting, category targeting |
| **Reports** | Request and download performance reports |
| **Geographic** | Expand campaigns to new marketplaces |
| **Account Operations** | Account-level settings and configurations |

### Setup Requirements
1. Active Amazon Advertising API credentials (you have this)
2. MCP-compatible AI platform (Claude Code — yes)
3. MCP Server configuration in Claude Code's settings

### Critical Limitation (Why We Still Need the Brain)
> "The system executes instructions as provided without evaluating campaign architecture, bidding logic, or financial alignment — strategic decisions remain human responsibilities while operational execution becomes automated."

This is exactly where Opus 4.6 fills the gap. The MCP Server is the hands; Claude is the brain. Perpetua and Quartile charge thousands for their "brain" — we're replacing it with the most capable reasoning model available.

---

## What I Need From You

### 1. Amazon Advertising API Access (CRITICAL)

You mentioned you've been granted API access. I need:

- [ ] **Client ID** — from your Amazon Advertising API application
- [ ] **Client Secret** — from your Amazon Advertising API application
- [ ] **Refresh Token** — OAuth 2.0 refresh token for your advertising account
- [ ] **Profile ID(s)** — your advertising profile IDs (one per marketplace, e.g., US, CA)
- [ ] **Seller ID / Entity ID** — identifies your seller account

**How to get these if you don't have them yet:**
1. Go to https://advertising.amazon.com/API
2. Your approved application will show Client ID and Client Secret
3. Complete the OAuth flow to get a Refresh Token
4. Use the Profiles endpoint to list your Profile IDs

### 2. Amazon Ads MCP Server Setup

- [ ] **Confirm MCP Server access** — The Amazon Ads MCP Server is in open beta. You need to:
  1. Verify your API credentials work with the MCP Server
  2. We'll configure it in your Claude Code MCP settings (`.claude/mcp_servers.json`)

  If the MCP Server isn't available to you yet, we can fall back to direct API calls through a custom MCP server we build ourselves.

### 3. Supabase Database

- [ ] **Supabase project URL** — your project's URL
- [ ] **Supabase service role key** — for server-side operations (NOT the anon key)
- [ ] **Confirm Supabase MCP server** is connected — the V4.2 plan mentions you already have this

### 4. Product & Business Information

For each product/ASIN you're advertising:

- [ ] **ASIN(s)** — the products being advertised
- [ ] **Product cost (landed)** — per unit cost including shipping/FBA fees
- [ ] **Current selling price** — or price range
- [ ] **Target ACoS** — your break-even and target advertising cost of sale
- [ ] **Target TACoS** — if you have a total advertising cost of sale target
- [ ] **Current lifecycle stage** — Launch / Growth / Optimization / Maintenance / Clearance
- [ ] **Monthly ad budget** — total and per-product if applicable
- [ ] **Brand Registered?** — yes/no (affects available features like Brand Analytics, Sponsored Brands)

### 5. Current Campaign State

- [ ] **Export of current campaigns** — Bulk download from Campaign Manager (Sponsored Products)
- [ ] **Recent Search Term Report** — last 30-60 days
- [ ] **Brand Analytics data** — Search Query Performance if Brand Registered
- [ ] **Business Report** — for organic sales/TACoS baseline
- [ ] **Any existing campaign naming conventions** you want preserved

### 6. Strategic Preferences & Guardrails

- [ ] **Risk tolerance** — Conservative (small bid changes, slow), Moderate (standard), Aggressive (larger swings, faster optimization)
- [ ] **Campaign architecture preference** — Standard (multi-keyword) or Precision (single-keyword Quartile-style)?
- [ ] **Auto-execution comfort level:**
  - Level 1: Claude recommends, you approve everything
  - Level 2: Claude auto-executes routine (bid adjustments, negations), you approve strategic (new campaigns, budget changes)
  - Level 3: Claude auto-executes everything within guardrails, you review daily summary
  - Level 4: Full autonomous with weekly review only
- [ ] **Maximum single bid change** — e.g., no more than ±30% per adjustment
- [ ] **Maximum daily budget change** — e.g., no more than ±20% per day
- [ ] **Emergency stop conditions** — e.g., if daily spend exceeds $X, pause everything
- [ ] **Excluded actions** — anything Claude should NEVER do without asking

### 7. Competitive Context

- [ ] **Top 3-5 competitor ASINs** — products you compete against most
- [ ] **Competitive stance** — Defend position / Actively attack / Avoid head-to-head
- [ ] **Brand defense priority** — How important is bidding on your own brand terms?

### 8. Reporting Preferences

- [ ] **How do you want to receive reports?** — In Claude Code session / Generated markdown files / Both
- [ ] **Reporting cadence** — Daily summary / Weekly deep dive / Both
- [ ] **Key metrics you care about most** — ACoS, TACoS, Revenue, Profit, SOV, Organic rank, etc.

---

## Implementation Plan

### Phase 0: Infrastructure Setup (Day 1)

```
1. Set up Supabase database schema
   - All tables from V4.2 spec (campaign_registry, snapshots, etc.)
   - New tables for agentic operations:
     - agent_sessions (log every agentic run)
     - agent_decisions (every decision with reasoning chain)
     - agent_outcomes (track results of previous decisions)
     - strategy_state (current strategic context & directives)
     - guardrails_config (all safety limits and constraints)

2. Configure MCP Servers in Claude Code
   - Amazon Ads MCP Server (campaign execution)
   - Supabase MCP Server (persistent memory)
   - Filesystem MCP (local file operations)

3. Create CLAUDE.md with:
   - Product profiles and targets
   - Guardrail configuration
   - Strategic directives
   - Standard operating procedures
```

### Phase 1: Data Foundation (Day 1-2)

```
1. Pull all current campaign data via Amazon Ads MCP
   - All active campaigns, ad groups, keywords
   - Performance data (7d, 14d, 30d, 60d windows)
   - Search term reports
   - Placement performance

2. Store baseline in Supabase
   - First historical snapshot
   - Campaign registry populated
   - Keyword universe cataloged

3. Import supplementary data
   - Brand Analytics (manual upload initially)
   - Business Report (for TACoS baseline)
   - Inventory levels

4. Initial Assessment
   - Claude performs deep analysis of current state
   - Identifies immediate opportunities and problems
   - Produces "State of the Account" report
   - Establishes performance baselines
```

### Phase 2: Strategy Design (Day 2-3)

```
1. Claude designs campaign architecture
   - Audit current structure vs. ideal
   - Recommend Standard or Precision mode per product
   - Identify structural gaps (missing match types, no brand defense, etc.)

2. Keyword strategy
   - 4-layer keyword discovery
   - Tier assignment (Hero / Core / Discovery / Brand Defense)
   - Negative keyword audit
   - Search term mining for graduates

3. Bidding framework
   - Target ACoS by keyword tier
   - Placement modifier strategy
   - Budget allocation across campaigns
   - Daypart strategy (if data supports it)

4. Competitive positioning
   - Competitor advantage scoring
   - ASIN targeting strategy
   - Brand defense plan

5. Document strategy in Supabase + CLAUDE.md
   - So Claude has persistent context for all future sessions
```

### Phase 3: Execution & Optimization Loop (Day 3+)

```
1. Implement campaign changes via MCP
   - Restructure campaigns if needed
   - Add new keywords from discovery
   - Set bids per strategy
   - Add negative keywords
   - Adjust placement modifiers
   - Set budgets

2. Begin daily optimization cycle
   - Pull fresh data
   - Compare to previous snapshot
   - Execute routine optimizations
   - Log everything

3. Weekly strategic reviews
   - Deep performance analysis
   - Strategy adjustments
   - New keyword discovery
   - Competitive reassessment

4. Monthly business reviews
   - Full narrative report
   - Strategy evolution
   - Goal reassessment
```

### Phase 4: Continuous Learning (Ongoing)

```
1. Outcome tracking
   - For every bid change: what was the result 7 days later?
   - For every negation: was it the right call?
   - For every new keyword: did it perform as expected?

2. Strategy refinement
   - Adjust approach based on what works for YOUR account
   - Learn your products' seasonality
   - Calibrate aggressiveness to your risk tolerance

3. Expanding scope
   - Add Sponsored Brands (if Brand Registered)
   - Add Sponsored Display
   - Multi-marketplace expansion
   - DSP integration (future)
```

---

## How This Compares to Perpetua & Quartile

### Perpetua ($695-2,500+/month)
| Feature | Perpetua | Our System |
|---------|----------|------------|
| AI bid optimization | Goal-based algorithm | Opus 4.6 reasoning through multi-factor analysis |
| Campaign creation | Template-based | Custom architecture per product from first principles |
| Keyword management | Automated harvesting | 4-layer discovery + web research + competitive intel |
| Reporting | Dashboard + charts | Narrative strategy reports with reasoning |
| Strategy | Predefined playbooks | Custom strategy that evolves based on YOUR data |
| Human oversight | Dashboard monitoring | Conversational — ask Claude why it did anything |
| Transparency | Black-box algorithm | Full reasoning chain logged for every decision |
| Cross-marketplace | Yes | Yes (via Amazon Ads MCP) |
| Dayparting | Yes | Yes (Phase 3+) |
| Cost | $695-2,500+/mo | API usage only (~$10-50/mo) |

### Quartile ($5,000+/month)
| Feature | Quartile | Our System |
|---------|----------|------------|
| Hourly bidding | Yes (their core differentiator) | Yes, via Amazon Marketing Stream (Phase 4) |
| Single-keyword campaigns | Yes (Quartile Versa) | Yes (Precision Mode) |
| AI/ML optimization | Proprietary ML models | Opus 4.6 (arguably more capable at reasoning) |
| Scale | Enterprise (1000s of campaigns) | Scales with API limits, not software limits |
| Keyword research | Automated | 4-layer + LLM creative expansion + web research |
| Reporting | Custom dashboards | Custom narrative reports |
| Transparency | Limited (proprietary) | Full — every decision has a reasoning chain |
| Cost | $5,000+/mo | API usage only |

### Our Unique Advantages
1. **Deep reasoning** — Opus 4.6 extended thinking doesn't just pattern-match; it reasons through complex multi-variable scenarios the way a senior strategist would
2. **Full transparency** — Every decision comes with a reasoning chain you can read, question, and learn from
3. **Conversational interface** — Ask "Why did you increase the bid on [keyword]?" and get a real answer
4. **Adaptive strategy** — Not locked into predefined playbooks; strategy evolves based on YOUR specific data and outcomes
5. **Web-augmented intelligence** — Can research competitors, market trends, and category dynamics via web search
6. **Cost** — Orders of magnitude cheaper than enterprise platforms
7. **Control** — You own everything: the data, the logic, the strategy docs, the decision history

---

## Guardrail Framework

### Hard Limits (Cannot Be Overridden by Claude)
```
- Maximum bid: $X.XX (set per product based on margins)
- Maximum daily budget: $XXX (set per campaign)
- Maximum portfolio daily spend: $X,XXX
- Maximum bid change per adjustment: ±30% (configurable)
- Maximum budget change per day: ±20% (configurable)
- Minimum data threshold: 20 clicks before negation decisions
- Attribution window respect: No action on data < 14 days old
- Emergency stop: If daily spend exceeds 150% of target, pause all
- Cooldown period: 7 days between bid changes on same keyword
```

### Soft Limits (Claude Can Override With Reasoning)
```
- Preferred bid adjustment range: ±10-20%
- Preferred evaluation period: 7-14 days between changes
- New keyword initial bid: Historical CPC × 1.1
- Target campaign count: Warn if creating > 100 campaigns
- Budget reallocation: Prefer incremental over dramatic shifts
```

### Audit Trail (Every Action Logged)
```
{
  "session_id": "uuid",
  "timestamp": "ISO-8601",
  "action_type": "bid_adjustment",
  "entity": "campaign_id/keyword_id",
  "previous_value": 1.25,
  "new_value": 1.45,
  "reasoning": "ACoS improved from 28% to 22% over 14 days with 47 clicks.
                Current bid is leaving impressions on the table (impression share
                estimated at 35%). Increasing 16% to capture more volume while
                ACoS has headroom vs 30% target.",
  "confidence": "high",
  "expected_outcome": "Impressions +20-30%, ACoS may increase to 24-26% range",
  "review_in_days": 7,
  "guardrail_check": "PASS — within ±30% limit, 14-day data, cooldown respected"
}
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **AI Brain** | Claude Opus 4.6 (Extended Thinking) | Strategy, analysis, decisions |
| **Campaign Execution** | Amazon Ads MCP Server | Direct API campaign management |
| **Persistent Memory** | Supabase (PostgreSQL) + Supabase MCP | Historical data, decisions, outcomes |
| **Local Operations** | Filesystem MCP | Reports, exports, strategy docs |
| **Web Intelligence** | WebSearch / WebFetch | Competitor research, market trends |
| **Orchestration** | Claude Code CLI / Agent SDK | Agentic loops, scheduling |
| **Scheduling** | Cron job / GitHub Actions / Manual | Trigger daily/weekly cycles |
| **Bulksheet Backup** | SheetJS (local) | Fallback for manual upload if needed |

---

## Estimated Costs

| Item | Cost | Notes |
|------|------|-------|
| Amazon Ads MCP Server | Free | Open beta, requires API credentials |
| Supabase | Free tier | 500MB DB, more than sufficient |
| Claude API (daily ops) | ~$5-15/mo | Routine bid/budget analysis |
| Claude API (weekly strategy) | ~$10-30/mo | Deep thinking sessions |
| Claude API (monthly review) | ~$5-10/mo | Comprehensive analysis |
| **Total** | **~$20-55/month** | vs. Perpetua $695+ or Quartile $5K+ |

---

## FAQ

**Q: What if the Amazon Ads MCP Server doesn't support something I need?**
A: We build a custom MCP server that wraps the Amazon Advertising API directly. The V4.2 spec already has the full API integration planned. The official MCP server accelerates development; the direct API is the fallback.

**Q: What about the web dashboard from V4.2?**
A: It becomes optional. The agentic approach means Claude IS the interface. However, we can still build a lightweight dashboard (Phase 5) for visual monitoring if you want one. Or use Supabase's built-in dashboard for ad-hoc queries.

**Q: How do I trigger the daily optimization?**
A: Multiple options:
1. **Manual**: Open Claude Code, say "run daily optimization"
2. **Scheduled**: Cron job or GitHub Action that invokes Claude Code
3. **On-demand**: "Hey Claude, check on my campaigns" anytime

**Q: What if Claude makes a bad decision?**
A: Every action has:
- A reasoning chain (you can review why)
- A rollback path (reverse the change)
- Guardrails that prevent catastrophic mistakes
- Outcome tracking (Claude learns what doesn't work)
- You can set the autonomy level from "approve everything" to "fully autonomous"

**Q: Can this handle multiple ASINs / a large catalog?**
A: Yes. The Amazon Ads API and MCP Server handle the scale. Claude's context window (200K tokens) can reason about hundreds of campaigns simultaneously. For very large catalogs (1000+ ASINs), we batch by product group.

**Q: What about Sponsored Brands and Sponsored Display?**
A: Phase 1 focuses on Sponsored Products (the highest-ROI ad type). Sponsored Brands and Display are natural Phase 4+ extensions using the same architecture.

---

## Next Steps

Once you provide the items in the "What I Need From You" section above, here's what happens:

1. **I set up the Supabase schema** (takes ~30 minutes)
2. **We configure MCP servers** (Amazon Ads + Supabase)
3. **I pull your current campaign data** and perform initial assessment
4. **I design your campaign strategy** using extended thinking
5. **We agree on guardrails and autonomy level**
6. **I begin optimizing** — first with your approval on every action, then gradually increasing autonomy as you build trust

**The goal: Within one week, Claude is managing your Amazon ads better than any human agency, at a fraction of the cost.**

---

*This plan supersedes V4.2's web-app-first approach with an agent-first approach. The V4.2 database schema, rules logic, and module specifications remain valuable as the knowledge base that informs Claude's reasoning. The web dashboard can be built later as an optional monitoring layer.*
