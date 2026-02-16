# Amazon PPC Operating System: Master Plan & Module Specifications v4.2 (Production)

## Document Purpose

This is the complete blueprint for building an Amazon Sponsored Products PPC management application using Claude Code (Opus 4.6). The receiving Claude Code instance should use this plan to build a production-quality Next.js web application backed by Supabase, deployed to Vercel, with the analysis brain powered by Claude API calls AND an in-app rules engine. The codebase lives on GitHub.

**V4.2 is the production-hardened release.** All known architectural vulnerabilities from V4.1 have been resolved. See V4.2 Upgrade Summary below for the complete list of fixes.

The system has three layers: (1) a web application that handles data ingestion, storage, visualization, bulksheet generation, and workflow management, (2) a rules engine that executes user-configurable IF/THEN optimizations deterministically in-app at zero API cost, and (3) a set of LLM analysis modules that encode expert-level PPC decision logic, called via Claude API when the user needs judgment, synthesis, or creative reasoning.

The deliverable is a working application, not documentation. The module specification documents (.md files) serve as both the system prompts embedded in the app's API calls AND standalone reference documentation.

---

## V4.2 Upgrade Summary: Production Hardening From V4.1

V4.1 was architecturally sound. V4.2 closes every known vulnerability identified during red team review before handing the plan to Claude Code.

**1. Fixed: Campaign ID as Canonical Join Key.** V4.1 joined most tables on `campaign_name`, which breaks silently if a campaign is renamed in Seller Central. V4.2 introduces a `campaign_registry` table that maps Amazon's Campaign ID to the current campaign name. All snapshot and analytics tables now join on `campaign_id` (Amazon's ID, not a UUID). When a renamed campaign appears in a new upload, the registry updates the name while preserving the full historical data chain. Campaign name remains the display value; campaign_id is the join key.

**2. Fixed: Real Postgres Transactions for Upload Deduplication.** V4.1 used sequential delete-then-insert via the Supabase JS client, which is not a true transaction. If the insert failed after the delete, data was lost. V4.2 replaces this with a Supabase RPC function (`upsert_upload_batch`) that wraps both operations in a real Postgres `BEGIN/COMMIT` block. If insertion fails, the delete rolls back and the previous data is fully preserved.

**3. Fixed: Row-Level Security (RLS) + user_id on All Tables.** V4.1 relied solely on auth middleware in API routes, but Supabase's anon key (visible in frontend JS via browser dev tools) can bypass API routes and query the database directly. V4.2 adds a `user_id UUID REFERENCES auth.users(id)` column to every data table, enables RLS on every table, and adds policies enforcing `auth.uid() = user_id` on all operations. The database is now secure even if someone extracts the anon key.

**4. Fixed: Attribution Window Handling.** Amazon's Sponsored Products reports use 7-day and 14-day attribution windows, meaning order counts backfill over time. V4.1 treated each upload as ground truth. V4.2 adds an `attribution_window` column to snapshot tables, a `report_end_date` field, and a `data_maturity` flag ('partial' for reports within the attribution window, 'mature' for reports past it). The rules engine only acts on mature data by default, preventing premature negation of keywords that haven't finished attributing orders.

**5. Fixed: Spend-Weighted Health Scores.** V4.1's health score treated a $2/week campaign the same as a $500/week campaign. V4.2 adds a spend-weight modifier to the health score formula so high-spend campaigns naturally surface on the dashboard. The dashboard also now sorts by `health_score * weekly_spend` by default, ensuring the campaigns that matter most get attention first.

**6. Added: Precision Mode Ceiling & Guardrails.** V4.1 allowed unlimited Precision Mode campaigns without warning. V4.2 adds guardrails: (a) warns the user if Precision Mode would generate >300 campaigns, (b) recommends Precision Mode only for accounts with <5 ASINs in file-upload mode (no limit when API direct is connected), (c) the UI displays estimated campaign count before confirming architecture generation.

**7. Fixed: Real Rollback for Applied Bulksheets.** V4.1 had no way to undo a bad bulksheet after upload to Amazon. V4.2 adds an "Undo Last Bulksheet" feature that generates a reversal bulksheet: for every bid change, it restores the `current_value` from `optimization_actions`; for every new entity created, it generates a pause or archive row. The `bulksheet_history` table stores every generated bulksheet's actions with a batch ID for grouped rollback.

**8. Added: Brand Analytics Discovery Blind Spot Mitigation.** Brand Analytics SQP only shows terms where your products already appear, creating a discovery blind spot for net-new keywords. V4.2 adds an explicit "Discovery Gap" notice in the Module 2 UI when no Helium 10 data is present, and upgrades Module 2's LLM Layer 4 prompt to specifically generate keyword hypotheses for adjacent categories, problem-solution phrasing, and competitor vocabulary analysis based on the product profile. The system also cross-references the auto campaign search term report to surface terms Amazon's algorithm matched that don't appear in Brand Analytics.

**9. Fixed: SOV Tracker Honest Visualization.** V4.1 described SOV trend charts as continuous curves, but the data only updates on Brand Analytics import (monthly in steady state). V4.2 uses step-line charts (not smooth curves) in Recharts, labels each data point with its import date, and adds a "Data Frequency" indicator showing how often SOV is being tracked. The UI recommends weekly Brand Analytics imports during active SOV tracking periods.

**10. Restructured: Sprint Plan with Earlier API Integration.** V4.1 placed Amazon API direct connection in Sprint 6, making the entire system dependent on weekly manual uploads for the first 5 sprints. V4.2 moves read-only API integration (automated report pulling for Reports 1, 2, and 7) to Sprint 5, before the full campaign architecture and competitive intel modules. This dramatically reduces the adoption friction that kills personal tools. Write-back API (automated bulksheet application) remains in Sprint 6.

---

V3 was a strong plan. V4.0 makes it meaningfully better by incorporating proven architectural concepts from enterprise PPC platforms (particularly Quartile and Pacvue) while keeping the system lean, self-hosted, and cost-efficient. V4.2 then production-hardens the entire architecture.

**1. Added: In-App Rules Engine (inspired by Quartile Versa).** This is the single biggest addition. 60-70% of weekly optimization decisions are deterministic IF/THEN logic: "keyword has 20+ clicks and 0 orders, negate it." V3 routed all of these through Haiku API calls. V4 runs them in-app at zero API cost, with instant execution. The LLM is reserved for decisions requiring genuine judgment. Users can define custom rules, use the built-in default ruleset, or combine rules with LLM analysis.

**2. Added: Placement Optimization Module.** V3 mentioned placements in the bulksheet spec but had no logic for optimizing Top of Search, Product Pages, and Rest of Search placement modifiers. V4 adds placement-level performance tracking and bid modifier recommendations as part of the in-app analytics engine (deterministic math) with strategic interpretation available via LLM call.

**3. Added: Budget Pacing & Reallocation.** V3 had no budget intelligence. V4 adds budget utilization tracking, pacing analysis, and reallocation recommendations. In-app code handles the math; the LLM call (when triggered) provides strategic budget allocation reasoning.

**4. Added: Single-Keyword Campaign Architecture Mode.** V3 used traditional multi-keyword campaign structures. V4 offers two modes in Module 1: "Standard Mode" (multi-keyword, fewer campaigns, easier to manage manually) and "Precision Mode" (one ASIN, one keyword, one match type per campaign, Quartile-style, maximum granularity and attribution clarity). The user chooses based on their comfort level and catalog size.

**5. Added: Share of Voice (SOV) Tracking Over Time.** V3 stored Brand Analytics snapshots but didn't track SOV trends. V4 adds a dedicated SOV history table and trend visualization. Tracking click share and conversion share over weeks/months answers the strategic question: "Is my ad spend building market position or just treading water?"

**6. Upgraded: Keyword Graduation Pipeline.** V3 recommended graduating keywords but left the campaign-creation cascade partially manual. V4 fully automates the graduation-to-bulksheet pipeline: when a keyword graduates, the system generates the complete campaign structure (campaign + ad group + product ad + keyword + cross-campaign negative keywords) in the bulksheet, ready to upload.

**7. Added: Multi-Marketplace Schema Support.** V4 adds a `marketplace_id` field to core tables so the system can eventually support multiple Amazon marketplaces (US, CA, UK, DE, etc.) without schema migration. No functional change in V1, but the schema is future-proof.

**8. Added: Dayparting Execution Framework.** V3 mentioned dayparting analysis. V4 specs out the data model and scheduling framework for time-based bid adjustments when the Amazon API direct connection is built (Sprint 6). This is the path to Quartile-style hourly bidding.

**9. Added: Campaign Tagging & Segmentation.** Users can tag campaigns with custom labels (e.g., "hero products," "seasonal," "test batch") and filter/segment the dashboard by tags. Simple feature, high usability impact.

**10. Preserved: Everything good from V3.** All V3 corrections (Module 6 in-app, Brand Analytics primary, combined 3+4 call, corrected token estimates, chunking strategy, prompt caching) are carried forward.

---

## Accounts, Platforms & Tools: What You Need

Here is everything you need, ranked by priority. Treat this as your setup checklist.

### Must-Have (Free)

**GitHub** (free private repos)
- Create a private repository for the project
- Claude Code commits directly to this repo as it builds
- You own the code permanently
- Sign up: github.com

**Supabase** (free tier: 500MB database, 1GB file storage, 50K monthly active users, unlimited API calls)
- This is your database. Campaign snapshots, keyword history, search term data, optimization logs, product profiles, rules engine configuration, SOV tracking
- You already have it connected as an MCP server
- Free tier is more than enough for this use case. A year of weekly data for a mid-size account uses maybe 50-100MB.
- The real advantage over flat file storage: SQL queries. "Show me every keyword where ACoS improved after a bid decrease in the last 60 days" is a single query.

**Vercel** (Pro tier required: $20/month for 60-second function timeout)
- Hosts your application. One-click deploy from GitHub.
- **You need Vercel Pro ($20/month), not free tier.** The free tier has a 10-second serverless function timeout. Claude API calls take 10-30+ seconds depending on input size. The first LLM call on free tier will timeout and fail. Vercel Pro gives you 60-second timeouts which handles all realistic API calls.
- Additionally, implement Claude API calls using Vercel's streaming response pattern (`ReadableStream` in API routes) so the client receives partial responses and the connection stays alive. This is belt-and-suspenders: even on Pro, streaming prevents timeout issues on very large accounts.
- Your app gets a real URL you can access from any device.
- Sign up: vercel.com, connect your GitHub account, upgrade to Pro after initial deploy

**Supabase Auth** (free tier includes authentication)
- **Required, not optional.** The app will be deployed to a public URL. Without auth, anyone who discovers your URL can access your Amazon advertising data, product costs, margins, and competitive strategy.
- Use Supabase Auth with email/password login. Single user is fine for personal use.
- Implementation: add auth middleware to all API routes and page layouts. Redirect to login page if not authenticated.
- Free tier handles this with no additional cost.

**Claude API** (pay-per-use, starts with $5 free credits)
- Powers the analysis modules (the ones that need judgment, not the rules engine)
- Sign up: platform.claude.com
- You get $5 free credits, no credit card required
- After that, pay as you go. Realistic monthly cost for this system: $1-10/month depending on account size, analysis frequency, and how much the rules engine handles vs LLM.

**Amazon Advertising API** (free, but requires developer registration)
- Register NOW even though Mode 2 (direct API) isn't built in Sprint 1
- Approval takes 2-5 business days
- Register: advertising.amazon.com/API
- Having credentials ready means you can add direct API integration whenever you want without waiting

### Already Have (Free - Brand Registry)

**Amazon Brand Analytics** (free, you already have access through Brand Registry)
- This is your primary keyword intelligence source and it costs nothing
- Search Query Performance (SQP): shows exactly which search terms drive clicks and conversions to YOUR products, with click share and conversion share data. This is first-party Amazon data, more accurate than any third-party tool
- Top Search Terms: relative search frequency rankings across Amazon. Not exact volume numbers, but relative rank (term #1,247 vs #58,302) tells you everything you need about demand
- Market Basket Analysis: what customers buy alongside your products (informs cross-targeting)
- Repeat Purchase Behavior: identifies your loyal customer base keywords
- You export these as CSV from Seller Central > Brands > Brand Analytics, upload to the application
- This data feeds Module 2 (Keyword Research) and the SOV tracking system

### Optional (Paid, Only If You Outgrow Brand Analytics)

**Helium 10** (Platinum plan: $129/month or $99/month annual. No free or Starter plan available as of 2026.)
- The only thing Helium 10 gives you that Brand Analytics doesn't: reverse ASIN on competitors (see what keywords competitors rank for, with their organic and sponsored rank positions) and absolute search volume numbers
- At $99-129/month, this is hard to justify unless you're launching multiple new products and need deep competitive keyword intelligence regularly
- Alternative: Jungle Scout ($49/month for Growing plan) offers similar reverse ASIN capability at a lower price point

### Nice to Have (Not Required for V1)

**Claude Pro subscription** ($20/month)
- For using Claude Code to build the application
- If you're already subscribed (you likely are), you're set

**Domain name** (optional, ~$12/year)
- Vercel gives you a free .vercel.app subdomain
- A custom domain (like ppc.oilslick.com) is more professional but not required

---

## System Philosophy

### Core Principles

1. **Methodology Fusion, Not Regurgitation.** Each module synthesizes the strongest elements from multiple proven Amazon PPC thought leaders into a unified decision framework. Where methodologies conflict, the module specifies which approach wins based on the scenario.

2. **Decision Trees Over Opinions.** Every recommendation flows from explicit logic: "IF [condition] THEN [action] BECAUSE [reason]." No ambiguity, no improvisation.

3. **Data In, Decisions Out.** Every module has a defined input schema and output schema. The system is a pipeline, not a chatbot.

4. **Rules First, LLM Second.** Routine optimizations (bid adjustments on clear signals, keyword negation on spending thresholds, budget pacing corrections) run through the in-app rules engine at zero cost. The LLM is only called when the task requires judgment, synthesis, creative reasoning, or when the rules engine encounters an ambiguous situation it can't resolve.

5. **Math In The App, Judgment In The LLM.** Anything that can be calculated deterministically (ACoS, health scores, trend slopes, anomaly detection, placement analysis, budget pacing, SOV tracking) runs in application code. The LLM handles strategy, synthesis, and creative problem-solving.

6. **Always Improving.** Historical data in Supabase enables trend analysis that gets smarter with every optimization cycle. After 30 days of data, the system detects patterns no human tracks manually. After 90 days, the rules engine auto-tunes thresholds based on observed outcomes.

7. **Practitioner-Grade.** The system operates at the level of a senior PPC manager. No hand-holding.

8. **No AI Slop.** All output is direct, specific, actionable. No filler.

9. **Choose Your Control Level.** Users pick their automation comfort zone: full rules engine (zero LLM cost, deterministic), full LLM analysis (maximum judgment, higher cost), or hybrid (rules handle routine, LLM handles complex). This mirrors the Quartile One vs Quartile Versa philosophy.

10. **Better Than A Human Expert.** A human analyzes 50-100 keywords per session. This system analyzes everything simultaneously with perfect consistency. The rules engine catches threshold violations in milliseconds. The LLM synthesizes patterns across the entire account.

---

## Thought Leader Methodology Index

### Mina Elias (Trivium Group)
- **Extract:** Tiered campaign aggression model (Launch > Optimization > Scale phases). ASIN targeting by individual competitor based on competitive advantage. 60-day launch protocol.
- **Apply to:** Module 1 (Architecture), Module 5 (Competitive Intelligence), Module 3 (phase-based bid logic), Rules Engine (phase-based rule presets)

### Elizabeth Greene
- **Extract:** Search term isolation methodology (one-way funneling, source negation on graduation). Single-match-type-per-campaign structure. Naming conventions for scalable management.
- **Apply to:** Module 1 (Architecture, both Standard and Precision modes), Module 4 (Search Term Harvesting), Rules Engine (graduation rules), system-wide naming

### Destaney Wishon (BTR Media / BetterAMS)
- **Extract:** PPC as organic rank lever (not standalone profit center). TACoS-centric measurement. New-to-brand metrics and share of voice as leading indicators. Full-funnel keyword intent tiering.
- **Apply to:** Performance Analysis (app-computed), SOV tracking system, Module 2 (keyword intent), Module 1 (strategic objectives)

### Mansour Norouzi (Incrementum Digital)
- **Extract:** Bid adjustment formulas from CVR/CTR trends. Kill vs. scale decision framework with numeric thresholds. Budget allocation by marginal return. Dayparting analysis.
- **Apply to:** Module 3 (Bid Optimization), Rules Engine (bid adjustment rules), Performance Analysis (health scoring formulas), Budget Pacing engine

### Brandon Young (Seller Systems / Data Dive)
- **Extract:** Reverse ASIN workflow (pull converting keywords from top competitors). Keyword relevancy scoring. Cross-referencing search volume data to build demand maps.
- **Apply to:** Module 2 (Keyword Research), Module 5 (competitor ASIN selection)

### Pacvue / Perpetua / Quartile (Automation Platforms)
- **Extract:** Rules-based IF/THEN optimization framework. Dayparting logic. Optimization velocity concept (how frequently to change based on data volume). Single-keyword campaign architecture for maximum granularity. Placement-level optimization. Budget pacing and predictive reallocation. Share of voice tracking.
- **Apply to:** Rules Engine (core architecture), Module 3 (automation rules), Module 4 (harvesting thresholds), Module 1 (Precision Mode), Placement Optimization, Budget Pacing, SOV Tracker

---

## System Architecture

### Technology Stack

```
FRONTEND:       Next.js 14+ (React) + Tailwind CSS + Recharts
DATABASE:       Supabase (Postgres) + Supabase Auth (required)
AUTH:           Supabase Auth - email/password login (required for security)
FILE PARSING:   SheetJS (xlsx) + PapaParse (csv) - server-side in API routes
ANALYSIS:       Claude API (Sonnet 4.5 primary, Haiku 4.5 for high-frequency)
API PATTERN:    Vercel streaming responses (ReadableStream) for all Claude API calls
RULES ENGINE:   In-app TypeScript (zero API cost)
BULKSHEET GEN:  SheetJS (xlsx) - server-side
DEPLOYMENT:     Vercel Pro ($20/month, required for 60-second function timeout)
VERSION CONTROL: GitHub (private repo)
BUILD TOOL:     Claude Code (Opus 4.6)
```

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                     NEXT.JS APPLICATION (Vercel)                      │
│                                                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │  Dashboard  │  │  Upload &  │  │  Analysis  │  │  Bulksheet   │  │
│  │  (React)   │  │  Parse     │  │  Workspace │  │  Generator   │  │
│  │            │  │  (React +  │  │  (React)   │  │  (React +    │  │
│  │  Charts,   │  │  API Route)│  │            │  │  API Route)  │  │
│  │  Scores,   │  │            │  │  Claude    │  │              │  │
│  │  SOV,      │  │  SheetJS,  │  │  API calls │  │  SheetJS     │  │
│  │  Alerts    │  │  PapaParse │  │    +       │  │              │  │
│  │            │  │            │  │  Rules     │  │              │  │
│  │            │  │            │  │  Engine    │  │              │  │
│  └──────┬─────┘  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘  │
│         │              │               │                 │           │
│  ┌──────┴──────────────┴───────────────┴─────────────────┴────────┐ │
│  │                    SUPABASE CLIENT                              │ │
│  └──────────────────────────┬─────────────────────────────────────┘ │
│                              │                                       │
│  ┌───────────────────────────┴──────────────────────────────────┐   │
│  │                    RULES ENGINE (TypeScript)                   │   │
│  │                                                               │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │   │
│  │  │ Default     │  │ User-Defined │  │ Execution Log      │  │   │
│  │  │ Ruleset     │  │ Rules (CRUD) │  │ (audit trail)      │  │   │
│  │  └─────────────┘  └──────────────┘  └────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                   ┌───────────┴───────────────┐
                   │     SUPABASE (Postgres)    │
                   │                            │
                   │  product_profiles          │
                   │  campaign_snapshots        │
                   │  keyword_snapshots         │
                   │  search_term_reports       │
                   │  organic_data              │
                   │  inventory_data            │
                   │  placement_snapshots  [V4] │
                   │  optimization_actions      │
                   │  graduated_keywords        │
                   │  negative_keywords         │
                   │  brand_analytics           │
                   │  sov_history          [V4] │
                   │  keyword_research_imports  │
                   │  rules_config         [V4] │
                   │  rules_execution_log  [V4] │
                   │  budget_snapshots     [V4] │
                   │  campaign_tags        [V4] │
                   │  daypart_profiles     [V4] │
                   │  app_settings              │
                   │  system_state              │
                   └───────────────────────────┘
```

### Data Flow

```
Mode 1 (File Upload - Available Day 1):

    USER downloads reports from Amazon Seller Central
    USER exports Brand Analytics data from Seller Central (free via Brand Registry)
    USER exports keyword data from Helium 10 (optional, paid)
        ↓
    USER uploads files into the application
        ↓
    API ROUTE parses files (SheetJS/PapaParse), validates, stores in Supabase
        ↓
    DEDUPLICATION: Before inserting, DELETE existing rows for this upload_date
        in the target table (campaign_snapshots, keyword_snapshots, etc.).
        This makes every upload a clean replacement, not an append.
        Wrapped in a Supabase transaction: if insertion fails partway,
        the delete rolls back and the previous data is preserved.
        ↓
    APPLICATION computes metrics in-app:
        health scores, ACoS, TACoS, trends, anomalies,
        placement analysis, budget pacing, SOV deltas (deterministic math)
        ↓
    RULES ENGINE runs automatically on new data:
        executes all active rules, generates actions for threshold violations,
        logs every rule execution with rationale
        ↓
    DASHBOARD renders current state with charts, alerts, rule-generated actions
        ↓
    USER reviews rule-generated actions (auto-approved or pending based on config)
        ↓
    USER optionally clicks "Run LLM Analysis" for deeper strategic analysis
        ↓
    APPLICATION sends data + module system prompt to Claude API
        ↓
    CLAUDE returns structured JSON: strategic recommendations, complex bid logic
        ↓
    APPLICATION merges rule actions + LLM actions, deduplicates, presents unified view
        ↓
    USER approves actions (rules-generated may be auto-approved, LLM always manual)
        ↓
    APPLICATION generates upload-ready .xlsx bulksheet (SheetJS in API route)
        ↓
    USER downloads and uploads to Amazon Bulk Operations
        ↓
    REPEAT (weekly, or more frequently with rules engine handling routine)


Mode 2 (Amazon API Direct - Future Sprint 6):

    APPLICATION pulls data from Amazon Advertising API on schedule
    RULES ENGINE runs automatically on fresh data (daily or more)
    APPLICATION pushes rule-approved changes back via API (with guardrails)
    LLM analysis runs weekly for strategic review
    USER reviews weekly digest instead of managing upload/download cycle

Mode 3 (Hourly Optimization - Future Sprint 7, requires Amazon Marketing Stream):

    AMS pushes hourly performance data to AWS infrastructure
    APPLICATION ingests hourly metrics
    RULES ENGINE evaluates intra-day performance against daypart profiles
    Bid adjustments execute hourly through Amazon Ads API
    Weekly LLM review for strategic recalibration
```

---

## Supabase Database Schema

### Tables

```sql
-- =====================================================================
-- [V4.2] ROW-LEVEL SECURITY FOUNDATION
-- =====================================================================
-- Every data table includes user_id for RLS enforcement.
-- RLS policies ensure the Supabase anon key (exposed in frontend JS)
-- cannot access data without a valid auth session.
-- =====================================================================

-- Enable RLS on all tables (applied after each CREATE TABLE below)
-- Policy pattern: authenticated users can only access their own rows

-- =====================================================================
-- [V4.2] Campaign Registry (canonical campaign identity)
-- =====================================================================
-- Amazon's Campaign ID is the stable identifier. Campaign names can
-- change at any time in Seller Central. This registry maps campaign_id
-- to the CURRENT campaign_name and updates on every upload.
-- All other tables join on campaign_id, not campaign_name.
-- =====================================================================

CREATE TABLE campaign_registry (
    campaign_id TEXT PRIMARY KEY,        -- Amazon's Campaign ID (stable, never changes)
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    marketplace_id TEXT DEFAULT 'ATVPDKIKX0DER',
    current_name TEXT NOT NULL,          -- latest campaign name from most recent upload
    previous_names TEXT[],               -- history of past names (for audit trail)
    first_seen_date DATE DEFAULT CURRENT_DATE,
    last_seen_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,      -- false if campaign not present in last 2 uploads
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE campaign_registry ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own campaigns" ON campaign_registry
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_campaign_registry_name ON campaign_registry(current_name);
CREATE INDEX idx_campaign_registry_user ON campaign_registry(user_id);

-- On each upload, the parser calls this function to upsert the registry:
-- If campaign_id exists: update current_name (append old name to previous_names if changed),
--   update last_seen_date
-- If campaign_id is new: insert with current_name, first_seen_date = today

-- Product profiles (user enters once, updates as needed)
CREATE TABLE product_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    marketplace_id TEXT DEFAULT 'ATVPDKIKX0DER', -- US marketplace default, future-proof for international
    asin TEXT NOT NULL,
    sku TEXT,
    title TEXT,
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    margin_pct DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN price > 0 THEN ((price - cost) / price * 100) ELSE 0 END
    ) STORED,
    target_acos DECIMAL(5,2),
    breakeven_acos DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN price > 0 THEN ((price - cost) / price * 100) ELSE 0 END
    ) STORED,
    category TEXT,
    brand TEXT,
    review_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0,
    competitive_position TEXT DEFAULT 'new_entrant',
    architecture_mode TEXT DEFAULT 'standard', -- 'standard' or 'precision' (single-keyword)
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE product_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own profiles" ON product_profiles
    FOR ALL USING (auth.uid() = user_id);

-- Campaign snapshots (one row per campaign per upload)
CREATE TABLE campaign_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    marketplace_id TEXT DEFAULT 'ATVPDKIKX0DER',
    upload_date DATE NOT NULL,
    report_end_date DATE,                -- [V4.2] last day of the report period
    report_period TEXT,                   -- "7d", "14d", "30d", "60d"
    attribution_window TEXT DEFAULT '14d', -- [V4.2] Amazon's attribution window for this report
    data_maturity TEXT DEFAULT 'mature',  -- [V4.2] 'partial' if report_end_date < 14 days ago, 'mature' otherwise
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2] canonical join key
    campaign_name TEXT NOT NULL,          -- display value, may change over time
    campaign_type TEXT,                   -- classified: auto, exact, broad, phrase, conquest, defense
    targeting_type TEXT,                  -- AUTO or MANUAL
    bidding_strategy TEXT,
    daily_budget DECIMAL(10,2),
    state TEXT,                           -- enabled, paused, archived
    start_date DATE,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr DECIMAL(6,4) DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    orders INTEGER DEFAULT 0,
    sales DECIMAL(10,2) DEFAULT 0,
    acos DECIMAL(6,2) DEFAULT 0,
    roas DECIMAL(6,2) DEFAULT 0,
    cpc DECIMAL(6,4) DEFAULT 0,
    conversion_rate DECIMAL(6,4) DEFAULT 0,
    -- Computed by app, stored for history:
    health_score INTEGER,
    spend_weight DECIMAL(6,2),           -- [V4.2] weekly spend for dashboard sorting
    target_acos DECIMAL(5,2),            -- snapshot of target at time of analysis
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE campaign_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own snapshots" ON campaign_snapshots
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_campaign_snapshots_date ON campaign_snapshots(upload_date);
CREATE INDEX idx_campaign_snapshots_campaign_id ON campaign_snapshots(campaign_id);
CREATE INDEX idx_campaign_snapshots_name ON campaign_snapshots(campaign_name);
CREATE INDEX idx_campaign_snapshots_mkt ON campaign_snapshots(marketplace_id);
CREATE INDEX idx_campaign_snapshots_user ON campaign_snapshots(user_id);

-- Keyword snapshots (one row per keyword per upload)
CREATE TABLE keyword_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    upload_date DATE NOT NULL,
    data_maturity TEXT DEFAULT 'mature',  -- [V4.2] 'partial' or 'mature'
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2] canonical join key
    campaign_name TEXT,
    ad_group_id TEXT,
    ad_group_name TEXT,
    record_id TEXT, -- Amazon's Record ID (needed for updates)
    keyword_text TEXT,
    match_type TEXT,
    bid DECIMAL(6,4),
    state TEXT,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    orders INTEGER DEFAULT 0,
    sales DECIMAL(10,2) DEFAULT 0,
    acos DECIMAL(6,2) DEFAULT 0,
    cpc DECIMAL(6,4) DEFAULT 0,
    conversion_rate DECIMAL(6,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE keyword_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own keywords" ON keyword_snapshots
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_keyword_snapshots_date ON keyword_snapshots(upload_date);
CREATE INDEX idx_keyword_snapshots_text ON keyword_snapshots(keyword_text);
CREATE INDEX idx_keyword_snapshots_campaign_id ON keyword_snapshots(campaign_id);
CREATE INDEX idx_keyword_snapshots_user ON keyword_snapshots(user_id);

-- Search term reports (one row per search term per upload)
CREATE TABLE search_term_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    upload_date DATE NOT NULL,
    data_maturity TEXT DEFAULT 'mature',  -- [V4.2] 'partial' or 'mature'
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    campaign_name TEXT,
    ad_group_name TEXT,
    targeting TEXT, -- the keyword/target that was matched
    match_type TEXT,
    customer_search_term TEXT NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    orders INTEGER DEFAULT 0,
    sales DECIMAL(10,2) DEFAULT 0,
    acos DECIMAL(6,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE search_term_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own search terms" ON search_term_reports
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_search_terms_date ON search_term_reports(upload_date);
CREATE INDEX idx_search_terms_term ON search_term_reports(customer_search_term);
CREATE INDEX idx_search_terms_campaign_id ON search_term_reports(campaign_id);
CREATE INDEX idx_search_terms_user ON search_term_reports(user_id);

-- [V4] Placement data (TWO sources, loaded differently)
-- Source A: Current placement MODIFIERS come from bulk download Bidding Adjustment rows.
--   These rows contain only the percentage bid modifier you've set (e.g., +50% for Top of Search).
--   They do NOT contain performance metrics (impressions, clicks, spend, sales) by placement.
-- Source B: Placement PERFORMANCE data comes from a separate report:
--   Advertising Console > Measurement & Reporting > Sponsored Products > Campaign Report
--   with "Placement" segment selected. This report breaks out metrics by placement type.
--   This is Report 7 (added in V4.1). Without it, placement optimization is modifier-only.
--
-- In Sprints 1-5 (file upload mode): if the user uploads Report 7, full placement
-- optimization runs. If they only upload Report 1, the system tracks modifiers but
-- cannot compute placement-level ACoS/CVR. It still recommends modifiers based on
-- campaign-level performance heuristics.
-- In Sprint 6+ (API mode): the API provides placement performance data directly.

CREATE TABLE placement_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    upload_date DATE NOT NULL,
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    campaign_name TEXT,
    placement TEXT NOT NULL, -- 'Top of Search', 'Product Pages', 'Rest of Search'
    -- Performance metrics (from Report 7 or API; NULL if only Report 1 available):
    impressions INTEGER,
    clicks INTEGER,
    spend DECIMAL(10,2),
    orders INTEGER,
    sales DECIMAL(10,2),
    acos DECIMAL(6,2),
    cpc DECIMAL(6,4),
    conversion_rate DECIMAL(6,4),
    -- Modifier data (from Report 1 Bidding Adjustment rows; always available):
    current_modifier INTEGER DEFAULT 0, -- current placement bid percentage adjustment
    recommended_modifier INTEGER, -- computed by app or LLM
    has_performance_data BOOLEAN DEFAULT FALSE, -- TRUE if Report 7 was uploaded
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE placement_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own placements" ON placement_snapshots
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_placement_date ON placement_snapshots(upload_date);
CREATE INDEX idx_placement_campaign_id ON placement_snapshots(campaign_id);
CREATE INDEX idx_placement_campaign ON placement_snapshots(campaign_name);

-- Organic/business report data (one row per ASIN per upload)
CREATE TABLE organic_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    upload_date DATE NOT NULL,
    asin TEXT NOT NULL,
    sku TEXT,
    sessions INTEGER DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    buy_box_pct DECIMAL(5,2) DEFAULT 0,
    units_ordered INTEGER DEFAULT 0,
    conversion_rate DECIMAL(6,4) DEFAULT 0,
    ordered_product_sales DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE organic_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own organic data" ON organic_data
    FOR ALL USING (auth.uid() = user_id);

-- Inventory data (one row per SKU per upload)
CREATE TABLE inventory_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    upload_date DATE NOT NULL,
    sku TEXT NOT NULL,
    asin TEXT,
    product_name TEXT,
    available INTEGER DEFAULT 0,
    inbound INTEGER DEFAULT 0,
    reserved INTEGER DEFAULT 0,
    days_of_stock INTEGER, -- calculated by app
    urgency TEXT DEFAULT 'normal', -- normal, low_stock, overstock, clearance
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE inventory_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own inventory" ON inventory_data
    FOR ALL USING (auth.uid() = user_id);

-- Optimization actions (every recommendation, approved or rejected)
CREATE TABLE optimization_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    created_date DATE NOT NULL DEFAULT CURRENT_DATE,
    source TEXT NOT NULL, -- 'rules_engine', 'module_3', 'module_4', 'module_3_4_combined', etc.
    rule_id UUID, -- [V4] if generated by rules engine, references rules_config.id
    bulksheet_batch_id UUID, -- [V4.2] groups actions into a single bulksheet for rollback
    action_type TEXT NOT NULL, -- bid_increase, bid_decrease, pause, enable, negate, graduate, budget_increase, budget_decrease, new_keyword, new_negative, new_campaign, new_ad_group, new_product_ad, placement_adjust
    entity_type TEXT, -- campaign, keyword, product_targeting, placement, etc.
    operation TEXT, -- Create or Update (for bulksheet)
    campaign_name TEXT,
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    ad_group_name TEXT,
    ad_group_id TEXT,
    record_id TEXT, -- for bulksheet updates
    target_identifier TEXT, -- keyword text, ASIN, or SKU
    match_type TEXT,
    current_value DECIMAL(10,4),
    recommended_value DECIMAL(10,4),
    confidence TEXT, -- high, medium, low
    data_points INTEGER, -- clicks/impressions driving decision
    rationale TEXT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected, applied, auto_approved, rolled_back
    applied_date DATE,
    rolled_back_date DATE, -- [V4.2] if this action was undone
    outcome_notes TEXT, -- after applying, what happened
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE optimization_actions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own actions" ON optimization_actions
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_actions_status ON optimization_actions(status);
CREATE INDEX idx_actions_date ON optimization_actions(created_date);
CREATE INDEX idx_actions_source ON optimization_actions(source);
CREATE INDEX idx_actions_batch ON optimization_actions(bulksheet_batch_id);
CREATE INDEX idx_actions_user ON optimization_actions(user_id);

-- Graduated keywords (tracks what's been promoted to exact)
CREATE TABLE graduated_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    keyword_text TEXT NOT NULL,
    source_campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    source_campaign TEXT,
    source_match_type TEXT, -- what match type triggered the graduation
    destination_campaign TEXT, -- generated campaign name
    destination_match_type TEXT DEFAULT 'exact',
    graduated_date DATE DEFAULT CURRENT_DATE,
    source_acos DECIMAL(6,2),
    source_orders INTEGER,
    source_clicks INTEGER,
    starting_bid DECIMAL(6,4),
    -- [V4] full cascade tracking:
    negated_in_campaigns TEXT[], -- array of campaign names where negative was added
    -- NOTE FOR CLAUDE CODE: Postgres TEXT[] arrays require curly brace syntax for inserts:
    -- INSERT INTO ... (negated_in_campaigns) VALUES ('{campaign_a,campaign_b}')
    -- Or use the Supabase JS client array syntax: [campaign_a, campaign_b]
    -- The Supabase JS client handles arrays natively, but raw SQL needs the curly brace format.
    bulksheet_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE graduated_keywords ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own graduations" ON graduated_keywords
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_graduated_text ON graduated_keywords(keyword_text);

-- Negative keywords (master list of negated terms)
CREATE TABLE negative_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    keyword_text TEXT NOT NULL,
    match_type TEXT DEFAULT 'exact', -- exact or phrase
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    campaign_name TEXT, -- which campaign it's negated in
    level TEXT DEFAULT 'campaign', -- campaign or ad_group
    added_date DATE DEFAULT CURRENT_DATE,
    reason TEXT,
    source TEXT DEFAULT 'manual', -- 'manual', 'rules_engine', 'module_4', 'graduation'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE negative_keywords ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own negatives" ON negative_keywords
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_negatives_text ON negative_keywords(keyword_text);

-- Brand Analytics data (primary keyword intelligence, free via Brand Registry)
CREATE TABLE brand_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    import_date DATE DEFAULT CURRENT_DATE,
    report_type TEXT NOT NULL, -- 'search_query_performance' or 'top_search_terms'
    search_term TEXT NOT NULL,
    search_frequency_rank INTEGER, -- from Top Search Terms report
    search_query_score DECIMAL(10,2), -- from SQP report
    impressions INTEGER,
    clicks INTEGER,
    cart_adds INTEGER,
    purchases INTEGER,
    click_share DECIMAL(6,4), -- your product's share of clicks for this term
    conversion_share DECIMAL(6,4), -- your product's share of conversions
    top_clicked_asin_1 TEXT,
    top_clicked_share_1 DECIMAL(6,4),
    top_clicked_asin_2 TEXT,
    top_clicked_share_2 DECIMAL(6,4),
    top_clicked_asin_3 TEXT,
    top_clicked_share_3 DECIMAL(6,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_brand_analytics_term ON brand_analytics(search_term);
CREATE INDEX idx_brand_analytics_date ON brand_analytics(import_date);
ALTER TABLE brand_analytics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own brand analytics" ON brand_analytics
    FOR ALL USING (auth.uid() = user_id);

-- [V4] Share of Voice history (tracks SOV trends over time per keyword)
CREATE TABLE sov_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    tracking_date DATE NOT NULL,
    search_term TEXT NOT NULL,
    search_frequency_rank INTEGER,
    click_share DECIMAL(6,4),
    conversion_share DECIMAL(6,4),
    click_share_delta DECIMAL(6,4), -- change from previous period
    conversion_share_delta DECIMAL(6,4), -- change from previous period
    top_competitor_asin TEXT,
    top_competitor_share DECIMAL(6,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sov_date ON sov_history(tracking_date);
CREATE INDEX idx_sov_term ON sov_history(search_term);
ALTER TABLE sov_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own SOV" ON sov_history
    FOR ALL USING (auth.uid() = user_id);

-- Third-party keyword tool imports (optional: Helium 10, Jungle Scout, etc.)
CREATE TABLE keyword_research_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    import_date DATE DEFAULT CURRENT_DATE,
    source TEXT DEFAULT 'helium10', -- helium10, jungle_scout, manual
    keyword_text TEXT NOT NULL,
    search_volume INTEGER,
    search_volume_trend TEXT, -- up, down, flat
    organic_rank INTEGER,
    sponsored_rank INTEGER,
    competing_products INTEGER,
    relevancy_score TEXT, -- high, medium, low (user or LLM assigned)
    competitor_asin TEXT, -- if from reverse ASIN, which competitor
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE keyword_research_imports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own keyword imports" ON keyword_research_imports
    FOR ALL USING (auth.uid() = user_id);

-- [V4] Rules engine configuration
CREATE TABLE rules_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE, -- ships with app, user can modify
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100, -- lower number = higher priority, for conflict resolution
    -- Trigger conditions (stored as JSONB for flexibility):
    trigger_conditions JSONB NOT NULL,
    -- Example: {"metric": "acos", "operator": ">", "value": 50, "min_clicks": 20, "lookback_days": 14}
    -- Example: {"metric": "clicks", "operator": ">=", "value": 20, "orders_equals": 0, "lookback_days": 30}
    -- Action:
    action_type TEXT NOT NULL, -- bid_increase, bid_decrease, negate, pause, budget_increase, budget_decrease, graduate, placement_adjust
    action_value JSONB NOT NULL,
    -- Example: {"adjustment_type": "percentage", "value": -15}
    -- Example: {"adjustment_type": "negate", "match_type": "exact"}
    -- Scope:
    scope TEXT DEFAULT 'keyword', -- account, campaign, keyword, search_term, placement
    scope_filter JSONB, -- optional filter: {"campaign_type": ["exact", "broad"], "tags": ["hero"]}
    -- Schedule:
    schedule TEXT DEFAULT 'on_upload', -- on_upload, daily, weekly
    -- Behavior:
    auto_approve BOOLEAN DEFAULT FALSE, -- if true, actions skip approval queue
    max_actions_per_run INTEGER DEFAULT 50, -- safety limit
    cooldown_days INTEGER DEFAULT 7, -- minimum days between acting on same entity
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE rules_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own rules" ON rules_config
    FOR ALL USING (auth.uid() = user_id);

-- [V4] Rules execution log (audit trail)
CREATE TABLE rules_execution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    rule_id UUID REFERENCES rules_config(id),
    execution_date TIMESTAMPTZ DEFAULT NOW(),
    entities_evaluated INTEGER,
    entities_matched INTEGER,
    actions_generated INTEGER,
    actions_auto_approved INTEGER,
    actions_pending INTEGER,
    actions_skipped_cooldown INTEGER,
    execution_time_ms INTEGER,
    details JSONB -- summary of what was evaluated and decided
);
CREATE INDEX idx_rules_log_date ON rules_execution_log(execution_date);
CREATE INDEX idx_rules_log_rule ON rules_execution_log(rule_id);
ALTER TABLE rules_execution_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own rule logs" ON rules_execution_log
    FOR ALL USING (auth.uid() = user_id);

-- =====================================================================
-- RULES ENGINE: Supported Metric Types & Evaluator Contracts
-- =====================================================================
-- Each `metric` value in rules_config.trigger_conditions requires a
-- corresponding evaluator function. Below is the complete set of
-- supported metrics, what data they evaluate, and their required
-- condition parameters.
--
-- METRIC: "search_term_performance"
--   Evaluates: search_term_reports rows grouped by customer_search_term
--   Required params: min_clicks (int), orders_equals (int), lookback_days (int)
--   Optional: max_acos_pct_of_target (int), not_already_graduated (bool)
--   Logic: SUM(clicks) >= min_clicks AND SUM(orders) == orders_equals
--          within last lookback_days
--   Used by: Negate rules, Graduate rules
--
-- METRIC: "search_term_spend_vs_price"
--   Evaluates: search_term_reports joined with product_profiles
--   Required params: spend_multiplier (float), orders_equals (int)
--   Logic: SUM(spend) >= product_profiles.price * spend_multiplier 
--          AND SUM(orders) == orders_equals
--   Used by: Emergency negate rule
--
-- METRIC: "acos_vs_target"
--   Evaluates: keyword_snapshots joined with product_profiles
--   Required params: threshold_pct (int, e.g. 120 = ACoS is 120% of target)
--   Optional: min_clicks (int), min_orders (int), max_impressions (int), 
--             lookback_days (int)
--   Logic: (actual_acos / target_acos * 100) >= threshold_pct (for over-target rules)
--          OR (actual_acos / target_acos * 100) <= threshold_pct (for under-target rules)
--          Direction inferred from action_type: bid_decrease = over, bid_increase = under
--   Used by: Bid up/down rules
--
-- METRIC: "impressions"
--   Evaluates: keyword_snapshots
--   Required params: operator (string: "==", ">", "<", ">=", "<="), value (int),
--                    lookback_days (int)
--   Optional: min_campaign_age_days (int)
--   Logic: SUM(impressions) {operator} value within lookback_days
--   Used by: Pause zero-impression keywords
--
-- METRIC: "budget_utilization"
--   Evaluates: budget_snapshots (derived from campaign_snapshots spend vs daily_budget)
--   Required params: min_utilization_pct (int), consecutive_days (int)
--   Optional: max_acos_pct_of_target (int)
--   Logic: utilization_pct >= min_utilization_pct for >= consecutive_days days
--   Used by: Budget increase rules
--
-- METRIC: "cpc_change_wow"
--   Evaluates: keyword_snapshots comparing current upload_date vs previous upload_date
--   Required params: threshold_pct (int, e.g. 30 = 30% increase)
--   Optional: conversion_rate_change_max_pct (int), min_clicks (int)
--   Logic: (current_cpc - previous_cpc) / previous_cpc * 100 >= threshold_pct
--          AND (current_cvr - previous_cvr) / previous_cvr * 100 <= conversion_rate_change_max_pct
--   Used by: CPC spike bid-down rule
--
-- METRIC: "conversion_rate"
--   Evaluates: keyword_snapshots
--   Required params: operator (string), value (float), min_clicks (int), lookback_days (int)
--   Logic: conversion_rate {operator} value, with min_clicks data threshold
--   Used by: Custom rules (e.g., negate keywords with CVR < 1% after 100 clicks)
--
-- METRIC: "spend"
--   Evaluates: keyword_snapshots or campaign_snapshots (based on scope)
--   Required params: operator (string), value (float), lookback_days (int)
--   Optional: orders_equals (int), orders_operator (string)
--   Logic: SUM(spend) {operator} value, optionally combined with order conditions
--   Used by: Custom spend-based rules
--
-- To add a new metric type: create an evaluator function in 
-- src/lib/rules/evaluators.ts that accepts the trigger_conditions JSONB
-- and returns an array of matching entity IDs with their current values.
-- Register it in the evaluator registry map.
-- =====================================================================

-- [V4] Budget snapshots (track budget utilization over time)
CREATE TABLE budget_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    snapshot_date DATE NOT NULL,
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    campaign_name TEXT NOT NULL,
    daily_budget DECIMAL(10,2),
    actual_spend DECIMAL(10,2),
    utilization_pct DECIMAL(5,2), -- actual_spend / daily_budget * 100
    pacing_status TEXT, -- 'underspending', 'on_track', 'overspending', 'budget_capped'
    days_in_period INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE budget_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own budget data" ON budget_snapshots
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_budget_date ON budget_snapshots(snapshot_date);

-- [V4] Campaign tags (user-defined labels for segmentation)
CREATE TABLE campaign_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    campaign_name TEXT NOT NULL,
    tag TEXT NOT NULL, -- e.g., 'hero', 'seasonal', 'test', 'clearance', 'new_launch'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, tag)
);
ALTER TABLE campaign_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own tags" ON campaign_tags
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_campaign_tags_tag ON campaign_tags(tag);
CREATE INDEX idx_campaign_tags_campaign_id ON campaign_tags(campaign_id);
CREATE INDEX idx_campaign_tags_campaign ON campaign_tags(campaign_name);

-- [V4] Daypart profiles (for future hourly bidding)
CREATE TABLE daypart_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    profile_name TEXT NOT NULL,
    campaign_id TEXT REFERENCES campaign_registry(campaign_id), -- [V4.2]
    campaign_name TEXT, -- null = default profile
    -- 24 hourly multipliers (1.0 = no change, 1.3 = +30%, 0.7 = -30%)
    hour_multipliers JSONB NOT NULL,
    -- Example: {"0": 0.5, "1": 0.4, ..., "8": 1.2, "9": 1.4, ..., "23": 0.6}
    day_of_week_multipliers JSONB, -- optional: {"monday": 1.0, ..., "sunday": 0.8}
    is_active BOOLEAN DEFAULT FALSE, -- only active when API direct connection is live
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE daypart_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own daypart profiles" ON daypart_profiles
    FOR ALL USING (auth.uid() = user_id);

-- [V4.2] Bulksheet history (tracks every generated bulksheet for rollback)
CREATE TABLE bulksheet_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    batch_id UUID NOT NULL UNIQUE,       -- groups all actions in one bulksheet
    generated_date TIMESTAMPTZ DEFAULT NOW(),
    action_count INTEGER NOT NULL,
    action_summary JSONB,                -- {"bid_changes": 12, "negations": 5, "graduations": 2}
    status TEXT DEFAULT 'generated',     -- 'generated', 'uploaded', 'rolled_back'
    rolled_back_date TIMESTAMPTZ,
    rollback_batch_id UUID,              -- the batch_id of the reversal bulksheet
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE bulksheet_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own bulksheet history" ON bulksheet_history
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_bulksheet_history_batch ON bulksheet_history(batch_id);
CREATE INDEX idx_bulksheet_history_date ON bulksheet_history(generated_date);

-- App settings
CREATE TABLE app_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, key)
);
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own settings" ON app_settings
    FOR ALL USING (auth.uid() = user_id);

-- System state (lifecycle phase tracking)
CREATE TABLE system_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL UNIQUE,
    current_phase TEXT DEFAULT 'new_setup',
    last_optimization_date DATE,
    last_rules_run_date TIMESTAMPTZ, -- [V4]
    last_bulk_upload DATE,
    last_search_term_upload DATE,
    last_business_report_upload DATE,
    last_inventory_upload DATE,
    last_helium10_import DATE,
    last_brand_analytics_import DATE,
    last_competitive_refresh DATE,
    earliest_campaign_start DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE system_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access own state" ON system_state
    FOR ALL USING (auth.uid() = user_id);
);
```

### Default Rules (Ship With App)

The rules engine ships with a battle-tested default ruleset. Users can modify thresholds, disable individual rules, or add custom rules. These defaults encode the consensus best practices from the thought leader methodologies.

```sql
-- Insert default rules on first setup
-- Rule 1: Negate zero-conversion high-spend search terms
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Negate: Zero Orders, High Spend', 'Negate search terms with significant spend but zero conversions', true,
 '{"metric": "search_term_performance", "min_clicks": 20, "orders_equals": 0, "lookback_days": 30}',
 'negate', '{"match_type": "exact"}', 'search_term', false);

-- Rule 2: Negate search terms spending more than 2x product price with 0 orders
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Negate: Spend > 2x Price, Zero Orders', 'Emergency negate for terms burning budget with no return', true,
 '{"metric": "search_term_spend_vs_price", "spend_multiplier": 2.0, "orders_equals": 0}',
 'negate', '{"match_type": "exact"}', 'search_term', false);

-- Rule 3: Reduce bid when ACoS exceeds target by 20%+
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Bid Down: ACoS 20%+ Over Target', 'Reduce bid on keywords significantly exceeding ACoS target', true,
 '{"metric": "acos_vs_target", "threshold_pct": 120, "min_clicks": 15, "lookback_days": 14}',
 'bid_decrease', '{"adjustment_type": "percentage", "value": -15, "floor_pct_of_cpc": 50}', 'keyword', false);

-- Rule 4: Increase bid on high-performing keywords with low impression share
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Bid Up: Strong ACoS, Low Impressions', 'Increase bid on keywords converting well but getting limited visibility', true,
 '{"metric": "acos_vs_target", "threshold_pct": 80, "max_impressions": 100, "min_orders": 1, "lookback_days": 14}',
 'bid_increase', '{"adjustment_type": "percentage", "value": 20, "ceiling_pct_of_breakeven": 90}', 'keyword', false);

-- Rule 5: Graduate search terms meeting thresholds
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Graduate: Proven Converters', 'Promote search terms with strong conversion history to exact match campaigns', true,
 '{"metric": "search_term_performance", "min_orders": 2, "min_clicks": 10, "max_acos_pct_of_target": 150, "not_already_graduated": true}',
 'graduate', '{"destination_match_type": "exact", "starting_bid_source": "historical_cpc", "bid_multiplier": 1.1}', 'search_term', false);

-- Rule 6: Pause keywords with zero impressions for 14+ days
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Pause: Zero Impressions 14d', 'Pause keywords getting no visibility after 14 days', true,
 '{"metric": "impressions", "operator": "==", "value": 0, "lookback_days": 14, "min_campaign_age_days": 14}',
 'pause', '{}', 'keyword', false);

-- Rule 7: Budget alert when campaign is consistently budget-capped
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Budget Up: Consistently Capped + Good ACoS', 'Increase budget for campaigns hitting budget ceiling while performing well', true,
 '{"metric": "budget_utilization", "min_utilization_pct": 95, "consecutive_days": 3, "max_acos_pct_of_target": 100}',
 'budget_increase', '{"adjustment_type": "percentage", "value": 25, "max_daily_budget": 100}', 'campaign', false);

-- Rule 8: Bid down on keywords with high CPC spike
INSERT INTO rules_config (rule_name, description, is_default, trigger_conditions, action_type, action_value, scope, auto_approve) VALUES
('Bid Down: CPC Spike > 30%', 'Reduce bid when CPC spikes sharply without corresponding conversion improvement', true,
 '{"metric": "cpc_change_wow", "threshold_pct": 30, "conversion_rate_change_max_pct": 5, "min_clicks": 10}',
 'bid_decrease', '{"adjustment_type": "percentage", "value": -10}', 'keyword', false);
```

### Key Queries The App Uses

```sql
-- Portfolio summary for dashboard
SELECT 
    upload_date,
    COUNT(DISTINCT campaign_name) as campaign_count,
    SUM(spend) as total_spend,
    SUM(sales) as total_sales,
    CASE WHEN SUM(sales) > 0 THEN SUM(spend) / SUM(sales) * 100 ELSE 0 END as portfolio_acos,
    SUM(orders) as total_orders
FROM campaign_snapshots
WHERE upload_date = (SELECT MAX(upload_date) FROM campaign_snapshots)
GROUP BY upload_date;

-- Trend data for a specific campaign (last 8 weeks)
SELECT upload_date, acos, spend, sales, cpc, conversion_rate
FROM campaign_snapshots
WHERE campaign_name = $1
ORDER BY upload_date DESC
LIMIT 8;

-- Keyword performance trend
SELECT upload_date, bid, acos, clicks, orders, conversion_rate
FROM keyword_snapshots
WHERE keyword_text = $1 AND match_type = $2
ORDER BY upload_date DESC;

-- Find search terms ready to graduate (used by rules engine)
SELECT 
    customer_search_term,
    SUM(clicks) as total_clicks,
    SUM(orders) as total_orders,
    SUM(spend) as total_spend,
    SUM(sales) as total_sales,
    CASE WHEN SUM(sales) > 0 THEN SUM(spend) / SUM(sales) * 100 ELSE 0 END as acos
FROM search_term_reports
WHERE upload_date = (SELECT MAX(upload_date) FROM search_term_reports)
GROUP BY customer_search_term
HAVING SUM(orders) >= 2 AND SUM(clicks) >= 10;

-- Check if a search term was already graduated
SELECT EXISTS(
    SELECT 1 FROM graduated_keywords WHERE keyword_text = $1
) as already_graduated;

-- Check if a term was already negated
SELECT EXISTS(
    SELECT 1 FROM negative_keywords WHERE keyword_text = $1
) as already_negated;

-- Optimization action history with outcomes
SELECT * FROM optimization_actions
WHERE created_date >= $1
ORDER BY created_date DESC;

-- Calculate TACoS (requires joining ad data with organic data)
SELECT 
    cs.upload_date,
    SUM(cs.spend) as total_ad_spend,
    SUM(od.ordered_product_sales) as total_revenue,
    CASE WHEN SUM(od.ordered_product_sales) > 0 
        THEN SUM(cs.spend) / SUM(od.ordered_product_sales) * 100 
        ELSE 0 END as tacos
FROM campaign_snapshots cs
JOIN organic_data od ON cs.upload_date = od.upload_date
GROUP BY cs.upload_date
ORDER BY cs.upload_date DESC;

-- Bid change effectiveness: compare keyword performance before/after a bid change
SELECT 
    oa.target_identifier,
    oa.current_value as old_bid,
    oa.recommended_value as new_bid,
    oa.applied_date,
    ks_before.acos as acos_before,
    ks_after.acos as acos_after,
    ks_before.conversion_rate as cvr_before,
    ks_after.conversion_rate as cvr_after
FROM optimization_actions oa
JOIN keyword_snapshots ks_before ON oa.target_identifier = ks_before.keyword_text 
    AND ks_before.upload_date <= oa.applied_date
JOIN keyword_snapshots ks_after ON oa.target_identifier = ks_after.keyword_text 
    AND ks_after.upload_date > oa.applied_date
WHERE oa.action_type IN ('bid_increase', 'bid_decrease')
    AND oa.status = 'applied';

-- Brand Analytics: find high-opportunity keywords (high search rank, low click share)
SELECT 
    search_term,
    search_frequency_rank,
    click_share,
    conversion_share,
    top_clicked_asin_1,
    top_clicked_share_1
FROM brand_analytics
WHERE import_date = (SELECT MAX(import_date) FROM brand_analytics)
    AND search_frequency_rank < 50000
    AND click_share < 0.05
ORDER BY search_frequency_rank ASC;

-- Cross-reference: keywords converting in ads but missing from Brand Analytics
-- (indicates organic rank opportunity)
SELECT DISTINCT str.customer_search_term, str.orders, str.acos
FROM search_term_reports str
LEFT JOIN brand_analytics ba ON LOWER(str.customer_search_term) = LOWER(ba.search_term)
WHERE str.orders >= 2
    AND ba.search_term IS NULL
    AND str.upload_date = (SELECT MAX(upload_date) FROM search_term_reports);

-- [V4] Placement performance by campaign
SELECT 
    campaign_name,
    placement,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(spend) as spend,
    SUM(sales) as sales,
    CASE WHEN SUM(sales) > 0 THEN SUM(spend) / SUM(sales) * 100 ELSE 0 END as acos,
    CASE WHEN SUM(clicks) > 0 THEN SUM(spend) / SUM(clicks) ELSE 0 END as cpc,
    CASE WHEN SUM(clicks) > 0 THEN SUM(orders)::DECIMAL / SUM(clicks) * 100 ELSE 0 END as cvr
FROM placement_snapshots
WHERE upload_date = (SELECT MAX(upload_date) FROM placement_snapshots)
GROUP BY campaign_name, placement
ORDER BY campaign_name, placement;

-- [V4] SOV trend for a keyword over time
SELECT tracking_date, click_share, conversion_share, click_share_delta, top_competitor_asin
FROM sov_history
WHERE search_term = $1
ORDER BY tracking_date DESC
LIMIT 12;

-- [V4] Budget pacing: campaigns that are consistently budget-capped
SELECT 
    campaign_name,
    AVG(utilization_pct) as avg_utilization,
    COUNT(*) FILTER (WHERE utilization_pct >= 95) as days_capped,
    COUNT(*) as total_days
FROM budget_snapshots
WHERE snapshot_date >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY campaign_name
HAVING AVG(utilization_pct) >= 90;

-- [V4] Rules engine: check cooldown before acting on an entity
SELECT MAX(created_date) as last_action_date
FROM optimization_actions
WHERE target_identifier = $1 
    AND source = 'rules_engine'
    AND status IN ('approved', 'applied', 'auto_approved');

-- [V4] Campaign performance filtered by tag (uses campaign_id join, not name)
SELECT cs.*, ct.tag, cr.current_name
FROM campaign_snapshots cs
JOIN campaign_registry cr ON cs.campaign_id = cr.campaign_id
JOIN campaign_tags ct ON cs.campaign_id = ct.campaign_id
WHERE ct.tag = $1
    AND cs.upload_date = (SELECT MAX(upload_date) FROM campaign_snapshots)
ORDER BY (cs.health_score * cs.spend_weight) DESC; -- [V4.2] spend-weighted sort

-- [V4] Rules engine effectiveness report
SELECT 
    rc.rule_name,
    COUNT(oa.id) as total_actions,
    COUNT(*) FILTER (WHERE oa.status = 'applied') as applied,
    COUNT(*) FILTER (WHERE oa.status = 'rejected') as rejected,
    AVG(CASE WHEN oa.status = 'applied' THEN 
        (SELECT ks.acos FROM keyword_snapshots ks 
         WHERE ks.keyword_text = oa.target_identifier 
         AND ks.upload_date > oa.applied_date 
         ORDER BY ks.upload_date ASC LIMIT 1) - oa.current_value
    END) as avg_acos_impact
FROM rules_config rc
LEFT JOIN optimization_actions oa ON oa.rule_id = rc.id
GROUP BY rc.id, rc.rule_name;
```

---

## Amazon Data Sources

Four reports from Amazon Seller Central, plus Brand Analytics (free via Brand Registry) as your keyword intelligence source, plus optional third-party keyword tool exports.

### Report 1: Sponsored Products Bulk Download
- **Path:** Advertising Console > Bulk Operations > Create & download a custom spreadsheet
- **Settings:** 30-day range, check SP Data + Placement Data + Zero Impression Items, uncheck Terminated + Brand Assets
- **Format:** .xlsx, primary sheet "Sponsored Products Campaigns"
- **Key columns:** Entity, Campaign ID, Ad Group ID, Campaign Name, Ad Group Name, Targeting Type, State, Daily Budget, SKU, Bid, Keyword Text, Match Type, Bidding Strategy, Placement, Percentage, Product Targeting Expression, Impressions, Clicks, Spend, Orders, Sales, ACoS, CPC, ROAS
- **Critical:** Store Record IDs, Campaign IDs, Ad Group IDs. These are required for Update operations in bulksheet output.
- **[V4] Placement MODIFIER extraction:** Rows where Entity = "Bidding Adjustment" contain the placement modifier percentages you've set (e.g., Top of Search +50%). Parse these into `placement_snapshots` as `current_modifier` values. These rows do NOT contain performance metrics (impressions, clicks, etc.) by placement. For placement performance data, see Report 7.
- **Dual purpose:** This file is both the data source AND the template for bulksheet generation.
- **Frequency:** Weekly (optimization phase), every 3-5 days (launch phase)

### Report 2: Search Term Report
- **Path:** Bundled as tab in Report 1, or standalone from Advertising Console > Measurement & Reporting > Search Term Report
- **Key columns:** Campaign Name, Ad Group Name, Targeting, Customer Search Term, Match Type, Impressions, Clicks, Spend, Orders, Sales
- **"Customer Search Term" is THE critical column.** Everything Module 4 and the rules engine graduation/negation logic depends on this.
- **Frequency:** Weekly (optimization), bi-weekly (maintenance)

### Report 3: Business Report (Detail Page Sales and Traffic)
- **Path:** Seller Central > Reports > Business Reports > Detail Page Sales and Traffic by Child Item
- **Key columns:** ASIN, SKU, Sessions, Page Views, Buy Box Percentage, Units Ordered, Unit Session Percentage, Ordered Product Sales
- **Why it matters:** Only source for organic sales. Required for TACoS calculation. Without it, the system is blind to whether PPC is building organic rank.
- **Frequency:** Weekly, aligned with ad report dates

### Report 4: FBA Inventory Report
- **Path:** Seller Central > Reports > Fulfillment > FBA Manage Inventory (or Inventory > FBA Inventory)
- **Key columns:** SKU, ASIN, Available, Inbound Shipped, Inbound Receiving, Reserved
- **App calculates:** days_of_stock = available / avg_daily_units. Sets urgency flags: <14 days = low_stock, >180 days = overstock.
- **Frequency:** Monthly (normal), weekly (clearance or launch)

### Report 5: Brand Analytics Export (Primary Keyword Intelligence + SOV Source)
- **Path:** Seller Central > Brands > Brand Analytics > Search Query Performance (or Top Search Terms)
- **Search Query Performance columns:** Search Query, Search Query Score, Impressions, Clicks, Cart Adds, Purchases, Click Share, Conversion Share, Brand/ASIN breakdowns
- **Top Search Terms columns:** Search Term, Search Frequency Rank, Top Clicked ASIN #1-3, Click Share #1-3, Conversion Share #1-3
- **This is first-party Amazon data.** More accurate than any third-party tool.
- **[V4] SOV Tracking:** On each import, the application automatically calculates click_share_delta and conversion_share_delta vs the previous import and inserts records into `sov_history`. This builds the SOV trend over time.
- **Frequency:** Monthly for keyword expansion, weekly during launch phase, and whenever SOV tracking is desired

### Report 6 (Optional): Helium 10 / Third-Party Keyword Export
- **Only relevant if you subscribe to Helium 10 ($99+/month) or Jungle Scout**
- **Path:** In Helium 10, run Cerebro (reverse ASIN) or Magnet, then Export CSV
- **Key columns:** Keyword, Search Volume, Search Volume Trend, Competing Products, Cerebro IQ Score
- **Value:** Absolute search volume numbers and competitor keyword rankings. Useful but not essential given Brand Analytics covers the core need.
- **Frequency:** As needed for competitive deep-dives

### Report 7 (Recommended): Sponsored Products Placement Performance Report
- **Path:** Advertising Console > Measurement & Reporting > Create Report > Sponsored Products > Campaign > set Segment = "Placement"
- **Settings:** Same date range as Report 1 (30 days). Format: CSV or XLSX.
- **Key columns:** Campaign Name, Placement (Top of Search on Amazon, Detail Page on Amazon, Other on Amazon), Impressions, Clicks, Spend, Sales, Orders, ACoS, CPC, ROAS
- **Why it matters:** This is the ONLY source for placement-level performance metrics in file upload mode. Report 1's Bidding Adjustment rows only give you what modifier percentages you've set. This report tells you how each placement actually performed. Without it, the placement optimizer can only recommend modifiers based on campaign-level heuristics.
- **Frequency:** Weekly, same cadence as Report 1
- **When API is connected (Sprint 6+):** This report becomes unnecessary because the API provides placement performance data directly.

### File Auto-Detection Logic

The application detects report type from file contents, not user selection:
- .xlsx with sheet containing "Sponsored Products Campaigns": Report 1
- .xlsx with sheet containing "Search Term": Report 2 (or tab within Report 1)
- .csv with columns "Sessions" + "Page Views" + "Buy Box": Report 3
- .csv/.txt with columns "Available" + "Inbound" + "Reserved": Report 4
- .csv with columns "Search Query Score" or "Search Frequency Rank": Report 5 (Brand Analytics)
- .csv with columns "Search Volume" + ("Cerebro IQ" or "Competing Products"): Report 6 (Helium 10, optional)
- .csv/.xlsx with columns "Placement" + "Campaign Name" + segment-level Impressions/Clicks/Spend (NOT the bulk download Entity format): Report 7 (Placement Performance)
- .xlsx containing both SP Campaign and Search Term sheets: parse both as Reports 1+2

---

## Module Inventory

| # | Module Name | Runs Where | Model | Frequency | Priority |
|---|------------|-----------|-------|-----------|----------|
| 1 | Campaign Architecture Designer | Claude API | Sonnet 4.5 | As needed | P1 |
| 2 | Keyword Research & Intelligence | Claude API | Sonnet 4.5 | Monthly | P2 |
| 3 | Bid & Budget Optimization | Claude API | Haiku 4.5 or Sonnet 4.5 | Weekly (LLM layer) | P1 |
| 4 | Search Term Harvesting & Negation | Claude API | Haiku 4.5 or Sonnet 4.5 | Weekly (LLM layer) | P1 |
| 5 | Competitive Intelligence & ASIN Targeting | Claude API | Sonnet 4.5 | Monthly | P3 |
| 6 | Performance Analysis & Metrics | **In-App Code** (no API call) | N/A | Every upload | P1 |
| 7 | Bulksheet Builder | **In-App Code** (SheetJS) | N/A | After approval | DONE |
| 8 | Orchestrator & Lifecycle Manager | **In-App Code** (state machine) | N/A | Always | P2 |
| 9 | **[V4] Rules Engine** | **In-App Code** (TypeScript) | N/A | On upload + scheduled | P1 |
| 10 | **[V4] Placement Optimizer** | **In-App Code** + optional Claude API | N/A / Haiku | Every upload + weekly | P2 |
| 11 | **[V4] Budget Pacer** | **In-App Code** (TypeScript) | N/A | Every upload | P2 |
| 12 | **[V4] SOV Tracker** | **In-App Code** (TypeScript) | N/A | Every Brand Analytics import | P3 |

**Model Selection Rationale:**

Modules 3 and 4 remain available as LLM calls for complex strategic analysis that the rules engine can't handle (e.g., "This keyword has borderline performance with a rising trend, a CPC spike, and a seasonal factor - what's the right move?"). However, the rules engine now handles 60-70% of the routine bid adjustments and negations that V3 sent to the LLM. This means:
- Weekly API cost drops by 60-70% because most actions are rule-generated
- LLM calls are reserved for the remaining 30-40% that genuinely need judgment
- Users can choose: rules-only (zero API cost), LLM-only (maximum intelligence), or hybrid (recommended default)

Modules 1, 2, and 5 still require genuine reasoning: architectural decisions, creative keyword generation, competitive strategy. Sonnet 4.5 at $3/$15 per MTok is the right choice.

**Combined Weekly Optimization Call (when using LLM):**

Modules 3 and 4 can still be combined into a single API call. In V4, this call receives pre-filtered data: only the keywords and search terms that the rules engine flagged as "ambiguous" or "needs judgment" are sent to the LLM. This dramatically reduces input tokens.

**Prompt Caching:**

The module system prompts are 3,000-5,000 tokens each and identical across every call. With prompt caching enabled (90% savings on cache reads after the first call), the system prompt portion of input costs drops to nearly zero for subsequent calls in the same session.

---

## Data Schemas

### Product Profile
```typescript
interface ProductProfile {
    id: string;
    marketplace_id: string;          // [V4] default 'ATVPDKIKX0DER' (US)
    asin: string;
    sku: string;
    title: string;
    price: number;
    cost: number;
    margin_pct: number;              // computed: (price - cost) / price * 100
    target_acos: number;             // default: margin_pct * 0.75
    breakeven_acos: number;          // computed: margin_pct
    category: string;
    brand: string;
    review_count: number;
    rating: number;
    competitive_position: 'leader' | 'challenger' | 'niche' | 'new_entrant';
    architecture_mode: 'standard' | 'precision'; // [V4] standard = multi-keyword, precision = single-keyword
}
```

### Optimization Action
```typescript
interface OptimizationAction {
    id: string;
    source: 'rules_engine' | 'module_1' | 'module_2' | 'module_3' | 'module_4' | 'module_3_4_combined' | 'module_5' | 'placement_optimizer' | 'budget_pacer';
    rule_id?: string;                // [V4] if source is rules_engine
    action_type: 'bid_increase' | 'bid_decrease' | 'pause' | 'enable' | 'negate' | 'graduate' | 'budget_increase' | 'budget_decrease' | 'new_keyword' | 'new_negative' | 'new_campaign' | 'new_ad_group' | 'new_product_ad' | 'placement_adjust';
    entity_type: string;
    operation: 'Create' | 'Update';
    campaign_name: string;
    campaign_id: string;
    ad_group_name: string;
    ad_group_id: string;
    record_id: string;
    target_identifier: string;
    match_type: string;
    current_value: number;
    recommended_value: number;
    confidence: 'high' | 'medium' | 'low';
    data_points: number;
    rationale: string;
    status: 'pending' | 'approved' | 'rejected' | 'applied' | 'auto_approved';
}
```

### Campaign Blueprint (Module 1 output)
```typescript
interface CampaignBlueprint {
    campaign_name: string;
    campaign_type: 'auto_discovery' | 'exact_high_intent' | 'broad_discovery' | 'phrase_discovery' | 'asin_conquest' | 'brand_defense';
    architecture_mode: 'standard' | 'precision'; // [V4]
    targeting_type: 'AUTO' | 'MANUAL';
    bidding_strategy: 'Dynamic bids - down only' | 'Dynamic bids - up and down' | 'Fixed bid';
    daily_budget: number;
    phase: 'launch' | 'optimization' | 'scale' | 'maintenance' | 'clearance';
    objective: string;
    ad_groups: AdGroup[];
    placement_adjustments: PlacementAdjustment[];
    campaign_negatives: Keyword[];
    tags: string[];                  // [V4] initial campaign tags
}
```

### [V4] Rule Configuration
```typescript
interface RuleConfig {
    id: string;
    rule_name: string;
    description: string;
    is_default: boolean;
    is_active: boolean;
    priority: number;
    trigger_conditions: {
        metric: string;
        operator?: string;
        value?: number;
        min_clicks?: number;
        min_orders?: number;
        orders_equals?: number;
        lookback_days?: number;
        max_acos_pct_of_target?: number;
        threshold_pct?: number;
        // ... flexible condition set
    };
    action_type: string;
    action_value: {
        adjustment_type?: 'percentage' | 'absolute' | 'negate' | 'pause';
        value?: number;
        match_type?: string;
        floor_pct_of_cpc?: number;
        ceiling_pct_of_breakeven?: number;
        // ... flexible action set
    };
    scope: 'account' | 'campaign' | 'keyword' | 'search_term' | 'placement';
    scope_filter?: {
        campaign_type?: string[];
        tags?: string[];
    };
    schedule: 'on_upload' | 'daily' | 'weekly';
    auto_approve: boolean;
    max_actions_per_run: number;
    cooldown_days: number;
}
```

### [V4] Placement Analysis
```typescript
interface PlacementAnalysis {
    campaign_name: string;
    placements: {
        placement: 'Top of Search' | 'Product Pages' | 'Rest of Search';
        impressions: number;
        clicks: number;
        spend: number;
        sales: number;
        acos: number;
        cpc: number;
        conversion_rate: number;
        current_modifier: number;    // current bid % adjustment
        recommended_modifier: number; // computed optimal adjustment
        recommendation_rationale: string;
    }[];
}
```

### [V4] Graduation Cascade
```typescript
interface GraduationCascade {
    keyword_text: string;
    source_campaign: string;
    source_match_type: string;
    // The full set of bulksheet actions generated:
    actions: {
        // 1. Create new exact match campaign (in Precision mode) or add to existing exact campaign (Standard mode)
        new_campaign?: OptimizationAction;   // only in Precision mode
        new_ad_group: OptimizationAction;
        new_product_ad: OptimizationAction;
        new_keyword: OptimizationAction;
        // 2. Cross-campaign negative keywords
        source_negatives: OptimizationAction[]; // negate in source auto/broad/phrase campaigns
    };
}
```

Full TypeScript type definitions should be generated by Claude Code as a shared types file (`src/types/schemas.ts`) that both the application and module prompts reference.

---

## Module Specifications

### MODULE 1: Campaign Architecture Designer

**System prompt file:** `src/modules/module_01_architecture.ts`

**When it runs:** New product setup, or when Module 6 (in-app analysis) flags structural issues

**[V4] Two Architecture Modes:**

**Standard Mode** (default): Multi-keyword campaigns. Each campaign contains an ad group with multiple related keywords of the same match type. Fewer campaigns, easier to manage manually, works well for small-to-mid catalogs (1-20 ASINs).

**Precision Mode** (Quartile-style single-keyword): One ASIN, one keyword, one match type per campaign. Creates 3x the campaigns (one per match type per keyword) but provides perfect performance attribution, atomic bid control, and zero keyword-level budget competition within campaigns. Best for users comfortable with high campaign counts who want maximum granularity. For a product with 50 keywords across 3 match types, this creates 150 campaigns for that single ASIN.

**[V4.2] Precision Mode Guardrails:**
- **Campaign count estimation:** Before generating architecture, the UI calculates and displays: "Precision Mode will create approximately {N} campaigns for {X} ASINs. Continue?" This prevents surprise campaign explosions.
- **File-upload mode ceiling:** In Sprints 1-4 (before API direct), Precision Mode is recommended only for accounts with **fewer than 5 ASINs** or **fewer than 300 total estimated campaigns**. Above this threshold, the UI displays a warning: "Precision Mode with {N} campaigns will make bulk file uploads very large. Consider Standard Mode until API direct is connected (Sprint 5), or proceed at your own risk."
- **No limit with API direct:** Once Sprint 5+ API integration is active, the campaign count ceiling is removed. The API handles thousands of campaigns without file size issues.
- **Hybrid option:** Users can run Standard Mode on most products and Precision Mode on their top 1-3 hero products. The `architecture_mode` is set per-product in the product profile, not globally.

The user selects their mode per-product in the product profile (`architecture_mode`). Module 1 generates the appropriate structure.

**Inputs to Claude API:**
- Product profiles (from Supabase `product_profiles`, including `architecture_mode`)
- Strategic objective (user selects: launch/optimize/scale/defend/clearance/seasonal)
- Monthly budget ceiling
- Competitor ASINs (user provides)
- Existing campaign structure (from latest `campaign_snapshots`)
- Brand Analytics data (from `brand_analytics`, recommended)
- Helium 10 keyword data (from `keyword_research_imports`, if available)

**Output schema (JSON from Claude):**
```json
{
    "blueprints": [
        {
            "campaign_name": "string",
            "campaign_type": "auto_discovery | exact_high_intent | broad_discovery | phrase_discovery | asin_conquest | brand_defense",
            "architecture_mode": "standard | precision",
            "targeting_type": "AUTO | MANUAL",
            "bidding_strategy": "Dynamic bids - down only | Dynamic bids - up and down | Fixed bid",
            "daily_budget": 0.00,
            "phase": "launch | optimization | scale | maintenance | clearance",
            "objective": "string",
            "ad_groups": [],
            "placement_adjustments": [],
            "campaign_negatives": [],
            "tags": []
        }
    ],
    "budget_allocation": {"campaign_name": {"daily": 0, "monthly": 0, "pct": 0}},
    "phase_timeline": {"14d": "string", "30d": "string", "60d": "string"},
    "naming_convention": {"pattern": "string", "examples": ["string"]},
    "placement_recommendations": {"campaign_name": {"top_of_search": 0, "product_pages": 0}},
    "suggested_rules": [],
    "tags": {"campaign_name": ["string"]},
    "summary": "string",
    "alerts": ["string"]
}
```

**Decision logic (from V2, extended for V4):** Objective-to-structure mapping (launch=5-7 campaigns standard or 50-150 precision, clearance=max velocity, etc.), naming convention enforcement, budget allocation formulas by phase, bid strategy selection by campaign type, placement adjustment rules, multi-product portfolio logic, Precision Mode campaign generation cascade, initial tag assignment, suggested rule configurations per phase.

**[V4] Precision Mode Naming Convention:**
```
{brand}_{asin_suffix}_{keyword_slug}_{match_type}
Example: oilslick_B08XYZ_silicone_container_4ml_exact
```

**Slug generation rules:**
- Lowercase, replace spaces with underscores
- Remove special characters (apostrophes, hyphens, etc.)
- Truncate keyword slug to 40 characters max (Amazon campaign name limit is 128 chars)
- If truncation creates a collision (two keywords slug to the same string), append a 4-character hash of the full keyword text: `oilslick_B08XYZ_silicone_container_4ml_a3f2_exact`
- The app maintains a slug registry in memory during campaign generation to detect collisions before they hit Amazon

This naming convention enables the system to programmatically identify the ASIN, keyword, and match type from the campaign name alone, which is critical for the rules engine and automated analysis.

### MODULE 2: Keyword Research & Intelligence

**When it runs:** New product launch, monthly keyword expansion cycle

**Three modes (from V3, unchanged):**
- **With Brand Analytics data (recommended, free)**
- **With Helium 10/Jungle Scout data (optional, paid)**
- **Without any keyword data (LLM brainstorming fallback)**

**[V4] Additional output:** For each keyword, the module now outputs a `priority_tier` that the rules engine can use for differentiated treatment:
- **Tier 1 (Hero):** Top 10-15 highest-value keywords. Rules engine applies aggressive bidding rules.
- **Tier 2 (Core):** Standard high-intent keywords. Default rules apply.
- **Tier 3 (Discovery):** Broad/exploratory keywords. Rules engine applies conservative thresholds.
- **Tier 4 (Brand Defense):** Branded terms. Rules engine applies defense-specific rules.

### MODULE 3: Bid & Budget Optimization (LLM Layer)

**When it runs:** Weekly optimization cycle, but only for entities the rules engine couldn't resolve

**[V4] Key change:** The rules engine handles 60-70% of bid adjustments before this module runs. Module 3 receives only the "ambiguous" cases: keywords with conflicting signals, borderline performance, complex multi-factor situations, or entities the user specifically flagged for LLM review.

**Inputs:** Pre-filtered keyword list (rules engine excluded clear-cut cases), campaign and keyword performance data with trend context, product profiles, current bids/budgets with Record IDs, placement analysis from Module 10, budget pacing from Module 11, anomaly flags

**[V4] Additional decision logic:**
- Placement modifier recommendations (coordinate with Module 10's deterministic output, add strategic interpretation)
- Budget reallocation reasoning across campaign portfolio (beyond what the rules engine handles mechanically)
- Phase transition recommendations based on trend analysis

### MODULE 4: Search Term Harvesting & Negation (LLM Layer)

**When it runs:** Weekly optimization cycle, combined with Module 3

**[V4] Key change:** The rules engine handles clear-cut graduations and negations. Module 4 receives borderline cases: terms with mixed signals, terms that might be relevant but haven't hit thresholds, terms in categories the rules engine isn't configured for.

**[V4] Graduation cascade:** When Module 4 (or the rules engine) approves a graduation, the system now generates the COMPLETE campaign-creation cascade as bulksheet-ready actions:
1. New campaign (Precision Mode) or assignment to existing campaign (Standard Mode)
2. New ad group within the campaign
3. New product ad (ASIN association)
4. New keyword with initial bid (based on historical CPC * 1.1 bid multiplier)
5. Negative exact match in all source campaigns (auto, broad, phrase) where this term appeared
6. Record in `graduated_keywords` table with `negated_in_campaigns` tracking

This means a single "graduate" action in the UI generates 5-8 bulksheet rows automatically.

### MODULE 5: Competitive Intelligence & ASIN Targeting

**When it runs:** Monthly competitive refresh, or when setting up ASIN conquest campaigns

**Unchanged from V3.** Inputs, logic, and outputs remain the same.

### MODULE 6: Performance Analysis (IN-APP, NOT API)

**Implementation:** TypeScript functions in the application, not a Claude API call.

**Computed metrics (deterministic math):**
- Portfolio totals: sum spend, sales, orders across campaigns
- Per-campaign: ACoS, ROAS, CPC, CTR, conversion rate
- TACoS: total ad spend / total product sales (requires organic data join)
- Health score: 1-10, computed per campaign using this exact formula:
```typescript
function calculateHealthScore(
    actual_acos: number,
    target_acos: number,
    trend_direction: 'improving' | 'stable' | 'worsening', // from last 3 uploads
    total_clicks: number,
    days_active: number,
    weekly_spend: number,        // [V4.2] spend for the current period
    portfolio_total_spend: number // [V4.2] total portfolio spend for relative weighting
): { score: number, spend_weight: number, weighted_score: number } {
    // Base score: how close is ACoS to target? (0-7 range)
    const acos_ratio = actual_acos / target_acos;
    let base: number;
    if (acos_ratio <= 0.5) base = 7;          // ACoS at half of target or better
    else if (acos_ratio <= 0.75) base = 6;     // 25%+ below target
    else if (acos_ratio <= 1.0) base = 5;      // At or below target
    else if (acos_ratio <= 1.2) base = 4;      // Up to 20% over target
    else if (acos_ratio <= 1.5) base = 3;      // 20-50% over target
    else if (acos_ratio <= 2.0) base = 2;      // 50-100% over target
    else base = 1;                              // 100%+ over target

    // Trend modifier: +1 if improving, 0 if stable, -1 if worsening
    const trend_mod = trend_direction === 'improving' ? 1 : 
                      trend_direction === 'worsening' ? -1 : 0;

    // Data sufficiency modifier: penalize if not enough data to trust the numbers
    let data_mod = 0;
    if (total_clicks < 20) data_mod = -2;       // very low data, score unreliable
    else if (total_clicks < 50) data_mod = -1;  // low data, somewhat unreliable

    // New campaign grace: don't penalize campaigns less than 7 days old
    if (days_active < 7) {
        return { score: 5, spend_weight: weekly_spend, weighted_score: 5 * weekly_spend };
    }

    const score = Math.max(1, Math.min(10, base + trend_mod + data_mod));
    
    // [V4.2] Spend weight: what % of portfolio spend does this campaign represent?
    // Used for dashboard sorting so high-spend campaigns surface first.
    const spend_weight = portfolio_total_spend > 0 
        ? weekly_spend / portfolio_total_spend 
        : 0;
    
    // Weighted score for dashboard sorting: score * spend_weight
    // A score-3 campaign spending $500/week ranks above a score-1 campaign spending $2/week
    const weighted_score = score * weekly_spend;
    
    return { score, spend_weight: weekly_spend, weighted_score };
}
```
**[V4.2] Dashboard default sort:** `weighted_score DESC` (health_score * weekly_spend). This ensures the campaigns that are both problematic AND high-impact surface first. Users can toggle to sort by raw health_score if preferred.
- Anomaly flags: CPC spike >30% WoW, conversion rate drop >25%, impression drop >50%
- Trend analysis: linear regression on historical snapshots for each metric
- Period-over-period comparison: delta and % change vs previous upload
- Inventory urgency: days of stock classification
- **[V4] Placement performance analysis** (see Module 10)
- **[V4] Budget pacing analysis** (see Module 11)
- **[V4] SOV trend calculation** (see Module 12)

**Output:** Rendered directly in the dashboard. No JSON round-trip to Claude needed.

**When Claude IS needed for analysis:** If the user wants a strategic interpretation ("why is my ACoS climbing despite more orders?"), they can trigger a one-off analysis call. But the routine metrics are always computed in-app.

### MODULE 7: Bulksheet Builder (IN-APP, SheetJS)

**Implementation:** Server-side API route using SheetJS.

**Key rules (from V2 and the existing MODULE_07 document):**
- Uses the user's uploaded bulk download as the template base
- Operation = "Create" for new entities, "Update" for modifications  
- Record ID required for Updates, blank for Creates
- All value formatting: lowercase state/match_type, uppercase targeting_type, camelCase placement, YYYYMMDD dates, "Fixed bid" singular, no currency symbols
- Row hierarchy: Campaign > Bidding Adjustment > Ad Group > Product Ad/Keyword/Targeting
- Remove non-standard sheets before generating output
- **[V4] Graduation cascade rows:** When a keyword graduation is approved, the bulksheet generator produces the full cascade: Campaign row (Create), Bidding Adjustment rows for placement modifiers, Ad Group row (Create), Product Ad row (Create), Keyword row (Create), and Negative Keyword rows (Create) in all source campaigns. This is 5-8 rows per graduation, all correctly formatted and ordered.
- **[V4] Placement modifier rows:** When placement adjustments are approved, generates Bidding Adjustment rows with the correct Placement values ("placementTop", "placementProductPage") and Percentage values.

### MODULE 8: Orchestrator & Lifecycle Manager (IN-APP, State Machine)

**Implementation:** Application logic in TypeScript. Manages lifecycle phase, determines which modules to run, tracks data freshness.

**State machine (from V2, extended):**
- new_setup > launch_phase (when campaigns created)
- launch_phase > optimization_phase (14+ days, 200+ clicks)
- optimization_phase > scale_phase (60+ days, target ACoS on 60% of spend)
- scale_phase > maintenance (90+ days, stable TACoS)
- any > troubleshooting (high-severity anomaly detected)

**[V4] The orchestrator also manages:**
- Rules engine execution scheduling (trigger rules on each data upload, track last run)
- LLM call routing: determines which entities go to rules engine vs LLM based on the following concrete logic:

**Ambiguous Entity Routing (how the orchestrator decides what goes to the LLM):**
```
Step 1: ALL entities go through the rules engine first. Every keyword, search term,
        and campaign is evaluated against active rules.

Step 2: Entities where a rule fired get a rule-generated action. These are DONE 
        unless the user manually flags them for LLM review.

Step 3: Entities where NO rule fired are categorized:
  - If total_clicks < 10: SKIP (insufficient data for any optimization)
  - If total_clicks >= 10 AND has_anomaly_flag = true: SEND TO LLM 
    (conflicting signals the rules can't interpret)
  - If total_clicks >= 10 AND trend_direction = 'worsening' AND acos is 
    within 10% of target (borderline): SEND TO LLM (needs judgment)
  - If total_clicks >= 50 AND no action in last 30 days: SEND TO LLM
    (stale entity that may need strategic reassessment)
  - All other no-rule-match entities: SKIP (performing within normal range, 
    no action needed)

Step 4: User can manually flag any entity for LLM review via the UI, 
        regardless of whether a rule already acted on it.

Step 5: The LLM receives ONLY the Step 3 + Step 4 entities, pre-filtered.
        This is typically 30-40% of the full dataset, saving 60-70% of input tokens.
```

- Merging rule-generated actions with LLM-generated actions, with deduplication
- Conflict resolution: if rules and LLM disagree on the same entity, flag for manual review

**Data freshness tracking:** Alert when bulk download > 7 days old, search terms > 7 days, business report > 14 days, inventory > 30 days, Brand Analytics > 30 days.

### MODULE 9: [V4] Rules Engine

**Implementation:** TypeScript module in the application. Zero API cost.

**How it works:**

The rules engine is a configurable automation layer that runs deterministic IF/THEN optimizations against the current dataset. It operates alongside the LLM modules, handling routine decisions and freeing the LLM for complex judgment calls.

**Execution flow:**
1. **Trigger:** Runs automatically on each data upload. Can also be triggered manually or on a schedule (daily/weekly when API direct is connected).
2. **Load active rules:** Query `rules_config` for all `is_active = true` rules, ordered by `priority`.
3. **For each rule:**
   a. Query relevant entities from Supabase based on `scope` and `scope_filter`
   b. Evaluate `trigger_conditions` against each entity's current data
   c. For entities that match: check cooldown (has this entity been acted on within `cooldown_days`?)
   d. For entities passing cooldown: generate `OptimizationAction` with `source = 'rules_engine'`, `rule_id` reference, and clear `rationale` derived from the rule name and conditions
   e. Apply `max_actions_per_run` safety limit
   f. If `auto_approve = true`, set action status to 'auto_approved'. Otherwise 'pending'.
4. **Log execution:** Insert summary into `rules_execution_log`
5. **Return:** All generated actions for display in the Analysis view

**Conflict resolution:**
- If two rules produce conflicting actions on the same entity (e.g., Rule A says increase bid, Rule B says decrease), the higher-priority rule (lower `priority` number) wins
- If a rule-generated action and an LLM-generated action conflict on the same entity, flag both as 'needs_review' and present side-by-side in the UI

**User interface for rules:**
- Rules management page (in Settings view): list all rules, toggle active/inactive, edit thresholds
- Rule builder: form-based UI for creating new rules (select metric > operator > value > action > scope)
- Rule performance dashboard: shows how many actions each rule has generated, approval rate, and measured outcome impact
- Import/export rules as JSON (for sharing configurations)

### MODULE 10: [V4] Placement Optimizer

**Implementation:** Primarily in-app TypeScript (deterministic analysis). Optional LLM call for strategic interpretation.

**What it does:**
Analyzes placement performance and/or modifier data, and recommends bid modifier adjustments.

**Two operating modes depending on data availability:**

**Mode A - Full Performance Data (Report 7 uploaded or API connected):**
Has per-placement impressions, clicks, spend, sales, ACoS, CPC, CVR.
Runs the full optimization algorithm below.

**Mode B - Modifier Only (only Report 1 available, no Report 7):**
Has only the current bid modifier percentages. Cannot compute per-placement ACoS/CVR.
Uses campaign-level heuristics instead:
- If campaign ACoS < target * 0.7 AND TOS modifier is 0%: recommend TOS +25% (campaign is efficient, try to win more top placements)
- If campaign ACoS > target * 1.3 AND TOS modifier > 50%: recommend reducing TOS modifier by 25% (high modifier might be driving up costs)
- Otherwise: HOLD (insufficient data for confident placement adjustments)
- Dashboard displays: "Upload Report 7 (Placement Performance) for detailed placement optimization"

**Mode A: In-app computation (runs on every upload with Report 7):**
```typescript
function calculatePlacementModifier(
    placement_acos: number, 
    target_acos: number, 
    current_modifier: number,
    clicks: number // need statistical significance
): { recommended_modifier: number, rationale: string } {
    
    if (clicks < 10) return { recommended_modifier: current_modifier, rationale: 'Insufficient data' };
    
    const acos_ratio = placement_acos / target_acos;
    
    if (acos_ratio < 0.7) {
        // Placement is performing much better than target - increase modifier to get more
        const increase = Math.min(Math.round((1 - acos_ratio) * 100), 50); // cap at +50%
        return { 
            recommended_modifier: Math.min(current_modifier + increase, 900), 
            rationale: `ACoS ${placement_acos}% is ${Math.round((1-acos_ratio)*100)}% below target. Increase modifier to capture more of this placement.`
        };
    }
    
    if (acos_ratio > 1.3) {
        // Placement is performing much worse than target - decrease modifier
        const decrease = Math.min(Math.round((acos_ratio - 1) * 50), 30); // gentler decreases
        return { 
            recommended_modifier: Math.max(current_modifier - decrease, 0), 
            rationale: `ACoS ${placement_acos}% is ${Math.round((acos_ratio-1)*100)}% above target. Reduce modifier to limit exposure.`
        };
    }
    
    return { recommended_modifier: current_modifier, rationale: 'Placement performing within acceptable range.' };
}
```

**Key insight:** Top of Search typically has the highest conversion rate but also the highest CPC. Product Pages typically have the lowest CPC but also lower conversion rates. The optimizer balances these tradeoffs against the user's strategic objective.

### MODULE 11: [V4] Budget Pacer

**Implementation:** In-app TypeScript. Zero API cost.

**What it does:**
Tracks budget utilization across all campaigns, identifies underspending and budget-capped campaigns, and recommends budget redistributions.

**Computed on every upload:**
1. **Utilization calculation:** The bulk download gives total spend over the report period (e.g., 30 days), not daily spend. Derive average daily spend: `avg_daily_spend = total_campaign_spend / days_in_report_period`. Compare this to the campaign's `daily_budget`. `utilization_pct = avg_daily_spend / daily_budget * 100`. Store in `budget_snapshots` with `actual_spend = avg_daily_spend` (not total period spend).
2. **Pacing classification:**
   - `budget_capped`: utilization >= 95% (campaign is hitting its ceiling, likely leaving money on the table)
   - `overspending`: utilization 85-95% (healthy, maximizing budget)
   - `on_track`: utilization 50-85% (normal)
   - `underspending`: utilization < 50% (either low demand, low bids, or poor keyword relevance)
3. **Reallocation recommendations:**
   - Campaigns that are `budget_capped` AND `ACoS < target`: recommend budget increase (amount based on headroom in portfolio budget ceiling)
   - Campaigns that are `underspending` AND `ACoS > target * 1.5`: recommend budget decrease, reallocate to capped performers
   - Zero-sum mode: total portfolio budget stays constant, money shifts from underperformers to capped performers

**Output:** Budget recommendations appear in the dashboard as actionable cards and in the Analysis view alongside bid and keyword actions.

### MODULE 12: [V4] SOV Tracker

**Implementation:** In-app TypeScript. Zero API cost.

**What it does:**
On each Brand Analytics import, calculates and stores Share of Voice metrics over time.

**Computation:**
1. Match current Brand Analytics import terms against previous import (by `search_term`)
2. Calculate `click_share_delta` and `conversion_share_delta` for each term
3. Insert records into `sov_history`
4. Identify:
   - **SOV gainers:** terms where your click share increased >= 2 percentage points
   - **SOV losers:** terms where your click share decreased >= 2 percentage points
   - **Competitive threats:** terms where a competitor's click share is rising while yours falls
   - **Opportunity gaps:** high search frequency terms where your click share is < 5%

**Dashboard display:** SOV step-line charts (Recharts `type="stepAfter"` line chart, NOT smooth curves) showing click share over time for top 10-20 tracked keywords. Each data point is labeled with its import date. A "Data Frequency" indicator shows how often SOV is being updated (e.g., "Monthly" or "Weekly"). Gain/loss indicators. Competitor movement alerts. **[V4.2] Note:** SOV data only updates when Brand Analytics is imported. Monthly imports produce staircase charts with monthly steps. For more granular SOV tracking, the UI recommends weekly Brand Analytics imports during active optimization periods. The chart accurately represents the data frequency rather than interpolating between sparse points.

---

## Module Decision Trees & System Prompt Skeletons

These are the core decision logic specifications that Claude Code must embed into the system prompts for Modules 1-5. Each module's `.ts` file exports a system prompt string containing these rules. The system prompts should be 3,000-5,000 tokens each. The skeletons below provide the decision trees, formulas, and thresholds. Claude Code wraps them in full system prompt format with role definition, input schema description, and JSON output schema.

### MODULE 1: Campaign Architecture Designer - Decision Logic

**System prompt skeleton for `src/modules/module_01_architecture.ts`:**

```
ROLE: You are an Amazon Sponsored Products campaign architect. Given a product 
profile, strategic objective, and optional existing campaign data, you design 
the complete campaign structure.

ARCHITECTURE MODE SELECTION:
- If product_profile.architecture_mode == "standard": use multi-keyword campaigns
  (5-15 keywords per ad group, grouped by intent tier)
- If product_profile.architecture_mode == "precision": use single-keyword campaigns
  (1 ASIN, 1 keyword, 1 match type per campaign)

OBJECTIVE-TO-STRUCTURE MAPPING:

IF objective == "launch":
  Standard Mode: Create 5-7 campaigns:
    1. Auto Discovery (auto targeting, Dynamic bids - down only)
    2. Broad Discovery (top 15-20 seed keywords, broad match)
    3. Phrase Discovery (top 10-15 keywords, phrase match)  
    4. Exact High Intent (top 5-10 highest-conviction keywords, exact match)
    5. Brand Defense (branded terms, exact match, Fixed bid)
    6. ASIN Conquest (if competitor ASINs provided, product targeting)
    7. Category Targeting (if category is well-defined)
  Precision Mode: Create 1 auto campaign + (N keywords * 3 match types) campaigns
  Budget split: 40% auto/broad discovery, 30% exact/phrase, 20% conquest, 10% defense
  Bidding: Start with "Dynamic bids - down only" on all except conquest (Fixed bid)
  Timeline: 14d evaluation checkpoint, 30d first optimization, 60d full assessment

IF objective == "optimize":
  Analyze existing campaign structure from campaign_snapshots
  Identify gaps: missing match types, uncovered keyword groups, no brand defense
  Recommend additions only, do not restructure what's working
  Budget reallocation: shift from campaigns with ACoS > target*1.5 to campaigns with ACoS < target

IF objective == "scale":
  Increase budgets on campaigns with ACoS < target (room to grow)
  Add broad/phrase campaigns for keyword expansion
  Add ASIN conquest campaigns if not already present
  Budget split: 50% proven performers, 30% expansion, 20% conquest
  Switch top performers to "Dynamic bids - up and down"

IF objective == "defend":
  Ensure branded term coverage (all brand name variations, exact match)
  Ensure top 10 revenue keywords have exact match campaigns
  Bidding: aggressive on branded (up to breakeven ACoS), conservative on generic
  Budget split: 40% brand defense, 40% top performers, 20% maintenance

IF objective == "clearance":
  Maximize velocity: high bids, high budgets, accept higher ACoS up to breakeven
  Enable "Dynamic bids - up and down" on all campaigns
  Expand to all match types for maximum reach
  
IF objective == "seasonal":
  Create time-limited campaigns with seasonal keyword modifiers
  Set end dates on campaigns
  Budget front-loaded (60% in first 2 weeks)

BID STRATEGY SELECTION:
- Auto campaigns: always "Dynamic bids - down only"
- Exact match (proven keywords): "Dynamic bids - down only" initially, 
  upgrade to "up and down" after 30+ days if ACoS < target
- Broad/Phrase (discovery): "Dynamic bids - down only"
- Brand defense: "Fixed bid" (you want consistent presence, not variable)
- ASIN conquest: "Fixed bid" (you're paying for competitor placement, control cost)

INITIAL BID CALCULATION:
- If Brand Analytics data available: bid = estimated CPC from category * 0.8 (conservative start)
- If existing keyword data available: bid = current avg CPC * 1.0 (match market)
- If no data: bid = product_price * target_acos / 100 * estimated_CVR
  where estimated_CVR = 0.10 for new products, 0.15 for established
- Floor: $0.30 (below this you get zero impressions in most categories)
- Ceiling: product_price * breakeven_acos / 100 * 0.5 (never start above half breakeven)

PLACEMENT ADJUSTMENTS (initial):
- Launch: Top of Search +25%, Product Pages 0% (test TOS first)
- Scale: Top of Search +50% if TOS ACoS < target, Product Pages +25% if PP CVR > campaign avg
- Defense: Top of Search +75% (dominate branded search results)
- Clearance: Top of Search +50%, Product Pages +50% (maximum visibility)

NAMING CONVENTION:
Standard: {brand}_{asin_suffix}_{intent}_{match_type}
  Example: oilslick_B08XYZ_discovery_broad
Precision: {brand}_{asin_suffix}_{keyword_slug}_{match_type}
  Example: oilslick_B08XYZ_silicone_container_4ml_exact

NEGATIVE KEYWORD GENERATION:
- Cross-negate: exact match keywords negated in broad/phrase campaigns to prevent cannibalization
- Category negatives: irrelevant category terms (e.g., if selling dog bowls, negate "cat bowl")
- Intent negatives: "free", "DIY", "how to make" (unless selling instructional products)
- Competitor brand negatives in auto campaigns (unless running conquest strategy)

OUTPUT: Array of CampaignBlueprint objects + budget allocation + timeline + alerts
```

### MODULE 2: Keyword Research & Intelligence - Decision Logic

**System prompt skeleton for `src/modules/module_02_keywords.ts`:**

```
ROLE: You are an Amazon keyword research specialist. Given product data and 
optional keyword intelligence sources, you generate a prioritized keyword list 
with intent classification, bid suggestions, and campaign assignments.

FOUR-LAYER KEYWORD DISCOVERY:

Layer 1 - Seed Keywords (always available):
  Extract from: product title, bullet points, category, product attributes
  Method: break title into component noun phrases
  Example: "4ml Silicone Container Non-Stick Concentrate Jar" produces:
    silicone container, concentrate jar, 4ml container, non-stick jar, 
    silicone jar, concentrate container, silicone concentrate container

Layer 2 - Data-Driven Keywords (from Brand Analytics or search term reports):
  IF Brand Analytics available:
    Pull all terms with search_frequency_rank < 100000 and any click_share > 0
    Rank by: (1/search_frequency_rank) * conversion_share * 1000 = opportunity_score
    Top 50 by opportunity_score become keyword candidates
  IF search term reports available (existing campaigns):
    Pull all terms with orders >= 1
    These are PROVEN converters, highest confidence

Layer 3 - Competitor Intelligence (from Helium 10/Brand Analytics):
  IF Helium 10 data: pull keywords where competitor ranks top 10 organically
  IF Brand Analytics Top Search Terms: pull terms where competitor ASINs appear 
    in top_clicked_asin fields but your ASIN does not
  Filter: only keywords with relevancy to your product (LLM judgment call)

Layer 4 - Long-Tail & Adjacent Expansion (LLM reasoning):
  Take Layer 1-3 keywords and generate:
    - Long-tail variations (add modifiers: size, color, material, use case)
    - Problem-solution phrases ("best container for dabs", "non stick wax jar")
    - Comparison terms ("silicone vs glass container")
    - Adjacent use-case terms (what else do buyers of this product search for?)
  Mark all Layer 4 keywords as confidence: "estimated" if no search data backs them

[V4.2] Layer 4+ - Discovery Blind Spot Mitigation:
  Brand Analytics SQP only shows terms where YOUR products already appear.
  It CANNOT discover high-volume terms where you have zero visibility.
  When no Helium 10/Jungle Scout data is present, the LLM must compensate:
    - Generate "competitor vocabulary" hypotheses: based on the product category,
      what terms would a competitor's listing use that yours doesn't?
    - Generate "adjacent category" terms: what related product categories share
      vocabulary? (e.g., "dab tool" for a concentrate container seller)
    - Generate "problem-aware" terms: what problem does this product solve,
      phrased as a customer would search? ("how to store concentrates")
    - Cross-reference auto campaign search term report: if auto campaigns have
      surfaced search terms with impressions that do NOT appear in Brand Analytics,
      these represent Amazon's own algorithm finding you for terms you don't
      organically rank for. Flag these as "algorithm-discovered" keywords.
  The UI displays a "Discovery Gap" notice when only Brand Analytics is available:
    "Brand Analytics only shows terms where your products already appear.
    For net-new keyword discovery, consider: (a) Jungle Scout ($49/mo) for
    competitor reverse ASIN data, or (b) rely on auto campaign search term
    mining + LLM-generated hypotheses below."

INTENT TIER CLASSIFICATION (assign to every keyword):

Tier 1 (Hero) - High purchase intent, proven demand:
  Criteria: exact product match + high search volume + orders >= 2 in search term data
  Bid: aggressive (CPC * 1.2 or target_acos * price * CVR)
  Campaign: exact match, high priority
  Rules engine treatment: aggressive bid rules, high budget priority

Tier 2 (Core) - Moderate intent, relevant:
  Criteria: product-relevant + moderate search volume + general purchase intent
  Bid: moderate (CPC * 1.0)
  Campaign: phrase match or exact match depending on specificity
  Rules engine treatment: default rules apply

Tier 3 (Discovery) - Broad relevance, exploring:
  Criteria: category-relevant but not product-specific, or long-tail unproven
  Bid: conservative (CPC * 0.7)
  Campaign: broad match
  Rules engine treatment: conservative thresholds, longer evaluation periods

Tier 4 (Brand Defense) - Your brand terms:
  Criteria: contains your brand name or close misspellings
  Bid: up to breakeven ACoS (protect at all costs)
  Campaign: exact match, dedicated brand defense campaign
  Rules engine treatment: never auto-negate, never auto-pause

BID SUGGESTION FORMULAS:
- With CPC data: suggested_bid = historical_avg_cpc * tier_multiplier
  (Tier 1: 1.2x, Tier 2: 1.0x, Tier 3: 0.7x, Tier 4: 1.5x)
- Without CPC data: suggested_bid = (product_price * target_acos/100) * est_CVR
  (est_CVR: Tier 1: 0.15, Tier 2: 0.10, Tier 3: 0.07, Tier 4: 0.20)
- Floor: $0.30, Ceiling: breakeven_acos * price / 100

NEGATIVE KEYWORD GENERATION:
- Irrelevant terms that could match broad/phrase (e.g., wrong material, wrong size)
- Competitor brand names (unless conquest strategy)
- Service/informational queries ("repair", "fix", "how to")
- Wrong product category terms that share vocabulary

OUTPUT: Array of keywords with: text, intent_tier, suggested_bid, match_type, 
campaign_assignment, confidence, source_layer, reasoning
```

### MODULE 3: Bid & Budget Optimization - Decision Logic

**System prompt skeleton for `src/modules/module_03_bid_optimization.ts`:**

```
ROLE: You are an Amazon PPC bid optimization specialist. You receive pre-filtered
keywords that the rules engine could not resolve (ambiguous cases, conflicting 
signals, complex multi-factor situations). Apply expert judgment to determine 
the correct bid action.

NOTE: The rules engine has already handled clear-cut cases (zero-order negations,
obvious ACoS violations, straightforward bid adjustments). You are receiving ONLY
the cases that need human-level reasoning. Every entity you receive has a reason
it was escalated - evaluate that reason carefully.

OPTIMIZATION DECISION MATRIX:

For each keyword, evaluate these dimensions simultaneously:
  A. ACoS vs Target ratio (actual_acos / target_acos)
  B. Trend direction (improving, stable, worsening over last 3 data points)
  C. Data sufficiency (clicks: <20 = low, 20-50 = moderate, 50+ = high)
  D. Conversion rate vs category average
  E. CPC trend (stable, rising, falling)
  F. Campaign phase (launch, optimization, scale, maintenance)
  G. Anomaly flags (from in-app anomaly detection)

DECISION TREE:

IF data_sufficiency == LOW (clicks < 20):
  IF campaign_age < 14 days: HOLD (too early, gathering data)
  IF campaign_age >= 14 AND impressions > 500 AND clicks < 5:
    Increase bid 20-30% (getting impressions but not clicks = bid too low for good placement)
  IF campaign_age >= 14 AND impressions < 100:
    Increase bid 30-40% (not competitive enough to show)
  ELSE: HOLD with note "insufficient data for confident adjustment"

IF data_sufficiency >= MODERATE:

  IF acos_ratio <= 0.5 (ACoS at half target or better):
    IF trend == improving or stable:
      Increase bid 15-25% (room to grow, capture more volume)
      Consider budget increase if campaign is >80% utilized
    IF trend == worsening:
      HOLD (ACoS still great, but watch the direction)

  IF acos_ratio > 0.5 AND <= 1.0 (below target):
    IF trend == improving: HOLD (on good trajectory, don't disrupt)
    IF trend == stable: increase bid 5-10% (test for more volume at good efficiency)
    IF trend == worsening: decrease bid 5-10% (arrest the slide before it crosses target)

  IF acos_ratio > 1.0 AND <= 1.3 (up to 30% over target):
    IF trend == improving: HOLD (trending in right direction)
    IF trend == stable: decrease bid 10-15%
    IF trend == worsening: decrease bid 15-20%
    IF CVR is rising while CPC is falling: HOLD (market correction in progress)

  IF acos_ratio > 1.3 AND <= 2.0 (30-100% over target):
    IF conversion_rate > category_avg AND trend == improving:
      Decrease bid 10% (good CVR suggests the keyword works, just need cheaper clicks)
    IF conversion_rate < category_avg:
      Decrease bid 20-25% OR recommend pause if trend is worsening
    IF this is a Tier 1 (Hero) keyword: decrease bid 15% max (preserve presence)
    IF this is a Tier 3 (Discovery) keyword: decrease bid 25% or pause

  IF acos_ratio > 2.0 (more than double target):
    Decrease bid 25-30%
    IF clicks > 50 AND orders == 0: recommend negation (this keyword doesn't convert for you)
    IF this is Tier 4 (Brand Defense): flag for review, never auto-negate branded terms

BID ADJUSTMENT DAMPENING:
- Never change a bid by more than 30% in a single cycle (prevents volatility)
- Apply diminishing adjustments: if bid was changed last cycle, reduce this cycle's 
  adjustment by 50% (prevents oscillation)
- Minimum bid floor: $0.25 (below this you typically get zero impressions)
- Maximum bid ceiling: product_price * breakeven_acos / 100 (never bid above breakeven)

BUDGET RECOMMENDATIONS (strategic layer, beyond rules engine's mechanical redistribution):
- If 3+ campaigns are budget-capped with ACoS < target: recommend overall budget increase
- If portfolio ACoS < target by 20%+: recommend aggressive budget expansion
- If TACoS is rising while ACoS is stable: recommend budget reduction (PPC not driving organic)
- If TACoS is falling while ACoS is stable: PPC IS driving organic, maintain or increase

PLACEMENT MODIFIER RECOMMENDATIONS (strategic interpretation of Module 10 data):
- If Report 7 data available and Top of Search ACoS < campaign ACoS by 20%+:
  Recommend increasing TOS modifier by 10-25%
- If Product Pages CVR > campaign CVR: recommend PP modifier increase 10-15%
- If placement is bleeding money (ACoS > 2x target): recommend reducing modifier to 0%

OUTPUT: Array of OptimizationAction objects with action_type, recommended_value,
confidence, data_points, and detailed rationale for each decision
```

### MODULE 4: Search Term Harvesting & Negation - Decision Logic

**System prompt skeleton for `src/modules/module_04_search_terms.ts`:**

```
ROLE: You are an Amazon search term optimization specialist implementing the 
Elizabeth Greene isolation funnel methodology. You receive search terms that the 
rules engine flagged as ambiguous (borderline performance, mixed signals, or 
requiring contextual judgment). Determine: graduate, negate, watch, or ignore.

NOTE: The rules engine has already graduated clear winners (orders >= 2, ACoS <= 
target * 1.5, clicks >= 10) and negated clear losers (clicks >= 20 with 0 orders,
spend >= 2x price with 0 orders). You receive only the borderline cases.

GRADUATION DECISION TREE (promote search term to dedicated exact match campaign):

IF orders >= 2 AND acos <= target_acos * 1.5 AND clicks >= 10:
  (This should have been caught by rules engine. If it's here, confirm graduation.)
  → GRADUATE with confidence: high

IF orders == 1 AND clicks >= 15 AND acos <= target_acos * 2.0:
  IF the search term has appeared in multiple upload periods with consistent clicks:
    → GRADUATE with confidence: medium (single order but persistent demand signal)
  IF first appearance in data:
    → WATCH (one-time conversion could be fluky, need more data)

IF orders >= 2 BUT acos > target_acos * 1.5:
  IF acos <= breakeven_acos: 
    → GRADUATE with confidence: medium + note "profitable but above target, 
      monitor closely after graduation"
  IF acos > breakeven_acos:
    → WATCH (converting but unprofitable, may need listing optimization first)

IF orders >= 3 AND any ACoS:
  → GRADUATE with confidence: high (3+ orders is strong signal regardless of current ACoS,
    bid optimization in the new exact campaign will improve efficiency)

NEGATION DECISION TREE:

IF clicks >= 20 AND orders == 0:
  (Should have been caught by rules engine. Confirm negation.)
  → NEGATE (exact match) with confidence: high

IF clicks >= 10 AND clicks < 20 AND orders == 0:
  IF search term is clearly irrelevant (wrong product category, wrong intent):
    → NEGATE with confidence: high (don't need more data, the term is wrong)
  IF search term is plausibly relevant but not converting:
    → WATCH (give it more data, might convert with more impressions)
  IF search term contains competitor brand name:
    → NEGATE unless conquest strategy is active for that competitor

IF spend > product_price * 1.5 AND orders == 0:
  → NEGATE with confidence: high (spend threshold exceeded, even with few clicks)

IF conversion_rate < 1% AND clicks >= 50:
  → NEGATE with confidence: high (sufficient data to conclude it doesn't convert)

IF the search term is a close variant of an already-negated term:
  → NEGATE with confidence: medium (e.g., "container silicone" when "silicone container" 
    was already negated)

NEGATIVE MATCH TYPE LOGIC:
- Default: negative exact match (only blocks the exact term)
- Use negative phrase match when: the problematic word/phrase appears in multiple 
  search terms (e.g., if "wholesale" appears in 5+ non-converting terms, negate 
  "wholesale" as phrase to catch all variations)
- NEVER negate at phrase level if the phrase could match a converting term

WATCH LIST CRITERIA:
- 5-15 clicks, 0 orders, but search term is semantically relevant
- 1 order, insufficient clicks to determine if it's consistent
- ACoS between target and breakeven with only 1-2 orders
- New search term first appearing in this data period

CROSS-CAMPAIGN CONSIDERATIONS:
- Before graduating: check graduated_keywords table. If already graduated, skip.
- Before negating: check if this term is an active keyword in any exact match campaign.
  If yes, DO NOT negate (it's deliberately targeted elsewhere).
- After graduating: generate negative exact match in ALL source campaigns where this 
  term appeared (auto, broad, phrase) to prevent cannibalization.

GRADUATION CASCADE OUTPUT:
For each graduated term, output the complete campaign creation specification:
  1. Campaign name (following naming convention based on architecture_mode)
  2. Ad group name
  3. ASIN to associate
  4. Keyword text + match type (exact)
  5. Starting bid (historical_cpc * 1.1, floored at $0.30)
  6. List of campaigns to add negative exact match in
This feeds directly into the bulksheet generator for full cascade row generation.

OUTPUT: Array of search term actions: {term, action: graduate|negate|watch|skip,
match_type, confidence, rationale, graduation_cascade (if graduating)}
```

### MODULE 5: Competitive Intelligence & ASIN Targeting - Decision Logic

**System prompt skeleton for `src/modules/module_05_competitive.ts`:**

```
ROLE: You are an Amazon competitive intelligence analyst. Given your product 
profile, competitor ASINs, and available performance data, you design ASIN 
targeting strategies for product targeting campaigns.

COMPETITIVE ADVANTAGE SCORING MATRIX:

For each competitor ASIN, evaluate along these dimensions (score 1-5 each):

  Price advantage: 
    Your price < competitor: +2
    Within 10%: +1  
    Your price > competitor by 10-25%: 0
    Your price > competitor by 25%+: -1

  Review advantage:
    Your reviews > competitor by 2x+: +2
    Your reviews > competitor: +1
    Similar (within 20%): 0
    Competitor has 2x+ your reviews: -1

  Rating advantage:
    Your rating >= 4.5 AND > competitor: +2
    Your rating > competitor: +1
    Similar (within 0.2): 0
    Competitor rated higher: -1

  Total advantage score = sum of three dimensions (range: -3 to +6)

TARGETING STRATEGY BY ADVANTAGE SCORE:

IF advantage_score >= 3 (strong advantage):
  → TARGET aggressively
  Bid: CPC * 1.3 (pay premium for competitor's detail page)
  Placement: prioritize Product Pages modifier
  Budget: allocate up to 20% of conquest budget to this ASIN
  Rationale: shoppers who see your product on this competitor's page 
  will likely prefer yours on price/reviews/rating

IF advantage_score >= 1 (moderate advantage):
  → TARGET moderately
  Bid: CPC * 1.0
  Budget: standard allocation
  Monitor closely for first 14 days

IF advantage_score == 0 (neutral):
  → TARGET cautiously
  Bid: CPC * 0.7
  Budget: minimal allocation, test only
  Evaluate after 30 days, kill if ACoS > target * 1.5

IF advantage_score < 0 (disadvantage):
  → DO NOT TARGET
  Rationale: shoppers comparing your product to this competitor will likely 
  choose them. You're paying to show your weaknesses.
  Exception: if your product is a different sub-category that serves a niche 
  (e.g., premium version vs budget), targeting may work despite score

DEFENSIVE CROSS-TARGETING:
- Identify your top 5 ASINs by sales volume
- For each, check Brand Analytics for competitors appearing in top_clicked_asin fields
- Any competitor consistently appearing on your product pages: TARGET their ASIN
  (defense move: if they're on your pages, get on theirs)
- Bid aggressively on defensive targets (up to breakeven ACoS)

DO-NOT-TARGET RULES:
- Products in different categories (even if Amazon shows them as competitors)
- Products with 1000+ more reviews AND better rating AND lower price (you will lose)
- Your own other ASINs (Amazon may suggest them, always exclude)
- Products that are complementary rather than competitive

ASIN TARGET BID CALCULATION:
base_bid = category_average_CPC * advantage_multiplier
  advantage_multiplier: score >= 3 → 1.3, score 1-2 → 1.0, score 0 → 0.7
floor: $0.30
ceiling: product_price * target_acos / 100

OUTPUT: Array of ASIN target recommendations: {competitor_asin, advantage_score,
score_breakdown, strategy, suggested_bid, campaign_assignment, rationale}
```

### MODULE 3+4 COMBINED: Weekly Optimization - Decision Logic

**System prompt skeleton for `src/modules/module_03_04_combined.ts`:**

```
ROLE: You are an Amazon PPC optimization specialist performing the weekly 
optimization review. You handle BOTH bid optimization and search term management
in a single pass. You receive pre-filtered entities that the rules engine could
not resolve.

[Include the complete decision logic from Module 3 AND Module 4 above]

COMBINED OUTPUT SCHEMA:
{
  "bid_adjustments": [OptimizationAction],
  "search_term_graduations": [GraduationAction with cascade],
  "search_term_negations": [NegationAction],
  "search_term_watch_list": [WatchAction],
  "budget_recommendations": [BudgetAction],
  "placement_recommendations": [PlacementAction],
  "strategic_notes": ["string - any overarching observations"],
  "alerts": ["string - anything requiring immediate attention"]
}

COORDINATION RULES:
- If a search term is being graduated, do NOT also recommend a bid change on 
  the source keyword for that term (the graduation handles it)
- If recommending a budget increase on a campaign, ensure the campaign's keywords 
  don't simultaneously have bid decrease recommendations (contradictory signals)
- If multiple keywords in the same campaign are recommended for pause, consider 
  recommending a campaign-level budget decrease instead
```

---

## Upload Deduplication & Transaction Strategy

**Critical implementation detail for file upload handling.**

When the user uploads a report, the application must handle the case where data for that upload_date already exists (re-upload, correction, or overlapping date ranges).

**[V4.2] Strategy: Postgres RPC Function with Real Transaction**

V4.1 used sequential delete-then-insert via the Supabase JS client, which is NOT a real transaction. If the insert failed after the delete, data was lost. V4.2 uses a Supabase RPC function that wraps both operations in a real `BEGIN/COMMIT` block.

**Create this RPC function in Supabase SQL Editor (part of migration 001):**

```sql
-- [V4.2] Atomic upload deduplication: delete + insert in a real transaction
CREATE OR REPLACE FUNCTION upsert_upload_batch(
    p_table_name TEXT,
    p_upload_date DATE,
    p_user_id UUID,
    p_rows JSONB
) RETURNS JSONB AS $$
DECLARE
    v_deleted INTEGER;
    v_inserted INTEGER;
BEGIN
    -- Step 1: Delete existing rows for this user + upload_date
    EXECUTE format(
        'DELETE FROM %I WHERE upload_date = $1 AND user_id = $2',
        p_table_name
    ) USING p_upload_date, p_user_id;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    
    -- Step 2: Insert new rows from JSONB array
    EXECUTE format(
        'INSERT INTO %I SELECT * FROM jsonb_populate_recordset(null::%I, $1)',
        p_table_name, p_table_name
    ) USING p_rows;
    GET DIAGNOSTICS v_inserted = ROW_COUNT;
    
    -- If we get here, both operations succeeded. Postgres auto-commits.
    -- If either operation fails, the entire transaction rolls back.
    RETURN jsonb_build_object(
        'success', true,
        'deleted', v_deleted,
        'inserted', v_inserted
    );
EXCEPTION WHEN OTHERS THEN
    -- Transaction automatically rolls back on exception
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM,
        'deleted', 0,
        'inserted', 0
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**TypeScript client call:**

```typescript
async function processUpload(
    tableName: string,
    uploadDate: string,
    userId: string,
    parsedRows: any[]
): Promise<{ success: boolean; deleted: number; inserted: number; error?: string }> {
    
    const supabase = createClient();
    
    // Batch rows into chunks of 500 (JSONB has no row limit, but keep payloads reasonable)
    const batchSize = 500;
    let totalInserted = 0;
    let totalDeleted = 0;
    
    for (let i = 0; i < parsedRows.length; i += batchSize) {
        const batch = parsedRows.slice(i, i + batchSize);
        const isFirstBatch = i === 0;
        
        if (isFirstBatch) {
            // First batch: delete old data + insert (atomic via RPC)
            const { data, error } = await supabase.rpc('upsert_upload_batch', {
                p_table_name: tableName,
                p_upload_date: uploadDate,
                p_user_id: userId,
                p_rows: JSON.stringify(batch)
            });
            
            if (error || !data?.success) {
                return { 
                    success: false, 
                    deleted: 0, 
                    inserted: 0,
                    error: error?.message || data?.error || 'RPC call failed'
                };
            }
            totalDeleted = data.deleted;
            totalInserted = data.inserted;
        } else {
            // Subsequent batches: insert only (old data already cleared)
            const { error: insertError } = await supabase
                .from(tableName)
                .insert(batch);
            
            if (insertError) {
                return { 
                    success: false, 
                    deleted: totalDeleted,
                    inserted: totalInserted,
                    error: `Insert failed at batch starting row ${i}: ${insertError.message}. First batch was atomic. Re-upload to retry.`
                };
            }
            totalInserted += batch.length;
        }
    }
    
    return { success: true, deleted: totalDeleted, inserted: totalInserted };
}
```

**[V4.2] Attribution Window Handling During Upload:**

When processing Report 1 (bulk download) and Report 2 (search terms), the parser also sets `data_maturity`:

```typescript
function calculateDataMaturity(reportEndDate: Date, attributionWindow: string): string {
    const windowDays = attributionWindow === '7d' ? 7 : 14; // Amazon default is 14d
    const daysSinceEnd = Math.floor((Date.now() - reportEndDate.getTime()) / (1000 * 60 * 60 * 24));
    return daysSinceEnd >= windowDays ? 'mature' : 'partial';
}
```

The rules engine checks `data_maturity` before acting: rules with `auto_approve = true` only auto-approve on mature data. Partial data still generates pending actions for manual review, with a UI badge: "⚠ Based on partial attribution data (X days remaining)."

**[V4.2] Campaign Registry Update During Upload:**

On every upload, after parsing Campaign IDs and Campaign Names from Report 1:

```typescript
async function updateCampaignRegistry(
    supabase: SupabaseClient,
    userId: string,
    campaigns: { campaign_id: string; campaign_name: string }[]
): Promise<void> {
    for (const campaign of campaigns) {
        const { data: existing } = await supabase
            .from('campaign_registry')
            .select('current_name, previous_names')
            .eq('campaign_id', campaign.campaign_id)
            .single();
        
        if (existing) {
            // Campaign exists: check if name changed
            if (existing.current_name !== campaign.campaign_name) {
                const previousNames = existing.previous_names || [];
                previousNames.push(existing.current_name);
                await supabase
                    .from('campaign_registry')
                    .update({
                        current_name: campaign.campaign_name,
                        previous_names: previousNames,
                        last_seen_date: new Date().toISOString().split('T')[0],
                        updated_at: new Date().toISOString()
                    })
                    .eq('campaign_id', campaign.campaign_id);
            } else {
                // Name unchanged, just update last_seen_date
                await supabase
                    .from('campaign_registry')
                    .update({ last_seen_date: new Date().toISOString().split('T')[0] })
                    .eq('campaign_id', campaign.campaign_id);
            }
        } else {
            // New campaign: insert
            await supabase
                .from('campaign_registry')
                .insert({
                    campaign_id: campaign.campaign_id,
                    user_id: userId,
                    current_name: campaign.campaign_name,
                    previous_names: [],
                    first_seen_date: new Date().toISOString().split('T')[0],
                    last_seen_date: new Date().toISOString().split('T')[0]
                });
        }
    }
}
```

**Why RPC instead of Supabase JS sequential operations:** The Supabase JS client executes each `.delete()` and `.insert()` as separate HTTP requests to the PostgREST API. These are NOT transactional. If the server crashes between the delete and insert, data is lost. The RPC function runs both operations in a single Postgres session with implicit transaction boundaries. If the insert fails, the delete rolls back automatically. This is the only safe pattern for destructive data replacement.

---

## Realistic API Cost Estimates

**Sonnet 4.5 pricing:** $3/MTok input, $15/MTok output
**Haiku 4.5 pricing:** $1/MTok input, $5/MTok output
**Prompt caching:** 90% savings on cache reads (system prompt costs ~$0 after first call)

### Small Account (5-10 campaigns, 50-100 keywords, 200 search terms)

**Rules engine (runs on every upload): $0.00** (in-app, no API call)

**Weekly LLM optimization (Modules 3+4 combined, Haiku) -- only ambiguous cases:**
- System prompt: ~4,000 tokens (cached: effectively free)
- Input data: ~3,000 tokens (reduced 60%+ because rules engine handled the clear-cut cases)
- Output: ~1,500 tokens
- Cost per call: ~$0.01
- Monthly (4 weeks): ~$0.04

**Monthly keyword expansion (Module 2, Sonnet):**
- Input: ~6,000 tokens, Output: ~4,000 tokens
- Cost: ~$0.08

**Monthly competitive refresh (Module 5, Sonnet):**
- Input: ~4,000 tokens, Output: ~2,000 tokens  
- Cost: ~$0.04

**Monthly total: ~$0.16** (down from V3's $0.21)

### Mid-Size Account (20-30 campaigns, 200-300 keywords, 500-1000 search terms)

**Rules engine: $0.00**

**Weekly LLM optimization (Haiku, ambiguous cases only):**
- Input data: ~8,000 tokens (down from 20K in V3)
- Output: ~2,500 tokens
- Cost per call: ~$0.02
- Monthly: ~$0.08

**Monthly modules: ~$0.20**

**Monthly total: ~$0.28** (down from V3's $0.40)

### Large Account (50+ campaigns, 500+ keywords, 2000+ search terms)

**Rules engine: $0.00**

**Weekly LLM optimization (Sonnet for remaining complex cases):**
- Input data: ~15,000 tokens (down from 40K -- rules engine handled 60%+)
- Output: ~4,000 tokens
- Cost per call: ~$0.11
- Monthly: ~$0.44

**Monthly modules: ~$0.50**

**Monthly total: ~$0.94** (down from V3's $1.50)

### Cost Comparison

| Solution | Monthly Cost |
|----------|-------------|
| This system (small account) | ~$0.16 API + $20 Vercel Pro = ~$20.16 |
| This system (mid account) | ~$0.28 API + $20 Vercel Pro = ~$20.28 |
| This system (large account) | ~$0.94 API + $20 Vercel Pro = ~$20.94 |
| This system + Helium 10 (optional) | Add $99-129/month if you want reverse ASIN |
| Quartile | $895-9,995/month |
| Pacvue/Perpetua | $500-2,000/month |
| PPC Agency | $3,000-10,000/month |

The rules engine doesn't just reduce API costs -- it makes the system faster and more reliable. Rule-generated actions are deterministic and instant. No waiting for API responses, no non-determinism, no context window limits.

---

## Application UI Specification

Six main views, navigated by sidebar.

### View 1: Dashboard
- System phase badge (Launch/Optimization/Scale/Maintenance)
- Data freshness alerts (which reports are stale)
- Portfolio summary card (total spend, sales, ACoS, TACoS, trend arrows)
- Campaign health table (sortable, color-coded health scores 1-10)
- **[V4] Campaign tag filter** (filter table by tag: hero, seasonal, test, etc.)
- **[V4] Budget pacing summary** (campaigns capped, underspending, with mini bar chart)
- **[V4] Placement performance summary** (Top of Search vs Product Pages vs Rest of Search, portfolio-level)
- **[V4] SOV trend widget** (top 5 tracked keywords with click share sparklines and delta arrows)
- Top 5 pending optimization actions with approve/reject (from both rules engine and LLM)
- Trend sparklines (Recharts) for key metrics over available history

### View 2: Data Upload
- Drag-and-drop zone for all file types
- Auto-detection of report type with confirmation
- Parsing summary (rows parsed, warnings, errors)
- **[V4] Post-upload rules engine trigger** (shows "Rules engine evaluated 247 keywords, generated 18 actions" after upload)
- Product profile editor (triggered when new SKUs detected)
- Historical data indicator ("You have 6 weeks of data. Trend analysis: good.")

### View 3: Analysis & Optimization
- **[V4] Two-section layout:**
  - **Rules Engine Actions** (top section): Auto-generated actions from rules, with rule name and rationale. Quick approve/reject. "Approve All Auto" batch button for rules with auto_approve=false.
  - **LLM Analysis Actions** (bottom section): Strategic recommendations from Claude API calls
- "Run LLM Analysis" button (orchestrator determines which modules to run, sends only ambiguous cases)
- Pre-run checklist showing modules, estimated API cost, estimated time
- Module execution progress (queued/running/complete/error)
- Results by module: bid adjustments table, search term graduate/negate tables, placement adjustments, budget recommendations, watch list
- Each recommendation has approve/reject/modify controls
- "Approve All High-Confidence" batch action
- **[V4] Conflict indicator:** if rules and LLM disagree on same entity, show both side-by-side with explanation
- Action queue summary at bottom

### View 4: Bulksheet Generator
- Template selection (most recent bulk download is default)
- Approved actions summary grouped by operation type
- **[V4] Graduation cascade preview:** for each graduated keyword, show all rows that will be generated (campaign, ad group, product ad, keyword, negatives)
- **[V4] Placement modifier rows preview**
- Generate button (calls server-side API route)
- Download button
- Post-upload verification: upload Amazon's processing report, app checks for errors
- **[V4.2] Bulksheet history table: shows every generated bulksheet with date, action count, status (generated/uploaded/rolled_back)**
- **[V4.2] "Undo Last Bulksheet" button: generates reversal bulksheet (restores previous bids, pauses new entities). Confirmation dialog shows exactly what will be reversed. Marks original batch as rolled_back.**
- **[V4.2] "Mark as Uploaded" button: user confirms bulksheet was uploaded to Amazon, updates status for outcome tracking**

### View 5: Settings & History
- Product profile management (including architecture_mode selector: Standard / Precision)
- **[V4] Rules Engine management:**
  - List all rules (default + custom), toggle active/inactive
  - Rule builder form (metric > operator > value > action > scope > schedule)
  - Rule performance dashboard (actions generated, approval rate, measured impact)
  - Import/export rules as JSON
  - Auto-approve configuration per rule
  - Cooldown period configuration
- **[V4] Campaign tag management** (create, assign, remove tags)
- App settings (target ACoS, brand, marketplace, naming convention, approval mode, optimization mode: rules-only / LLM-only / hybrid)
- Optimization history log (filterable by source: rules/LLM, shows before/after and outcomes)
- Data management (export all, reset, individual snapshot deletion)
- API credential management (Claude API key, future Amazon API)
- Brand Analytics import instructions and data management
- Optional Helium 10/third-party keyword tool import

### View 6: [V4] SOV & Market Position
- SOV step-line charts (Recharts `type="stepAfter"` line charts, not smooth curves) for tracked keywords over time
- **[V4.2] Each data point labeled with import date. "Data Frequency" indicator (e.g., "Monthly imports" or "Weekly imports")**
- **[V4.2] "For more granular SOV tracking, import Brand Analytics weekly" prompt when import frequency > 14 days**
- Click share and conversion share side-by-side
- Competitor movement table (which competitor ASINs are gaining/losing share on your key terms)
- Opportunity gap table (high-frequency search terms where your share is < 5%)
- **[V4.2] "Discovery Gap" notice: "Brand Analytics only shows terms where your products appear. For terms where you have zero visibility, see Module 2 Keyword Research > Layer 4+ Discovery."**
- Integration with Module 2: "Add to keyword research queue" action for opportunity gaps
- Integration with Module 5: "Analyze competitor" action for rising competitor ASINs

---

## Development Plan: Sprint Sequence for Claude Code

Claude Code builds this incrementally. Each sprint produces a deployable application with increasing capability.

### Sprint 1: Project Setup + Data Infrastructure + Security Foundation
**Deliverables:**
- Initialize Next.js project with TypeScript, Tailwind CSS, Supabase client
- **[V4.1] Set up Supabase Auth: email/password login, auth middleware on all routes, login page, redirect logic**
- **[V4.2] Enable Row-Level Security on ALL tables. Add user_id column to every data table. Create RLS policies (`auth.uid() = user_id`) on every table. Without this, the Supabase anon key (visible in browser dev tools) bypasses auth middleware.**
- Set up GitHub repo, Vercel deployment pipeline (Vercel Pro for 60-second timeout)
- Create all Supabase tables (run migration SQL, including all V4 tables, V4.2 campaign_registry, bulksheet_history)
- **[V4.2] Create `upsert_upload_batch` RPC function for atomic upload deduplication**
- **[V4.2] Create `campaign_registry` table and registry update logic in upload pipeline**
- **[V4.2] Upload deduplication via RPC transaction (replaces V4.1 sequential delete-insert)**
- Build file upload API route with parsers for all 7 report types (SheetJS + PapaParse)
- **[V4.2] Attribution window detection: parser sets `data_maturity` based on report_end_date vs current date**
- **[V4] Placement modifier parser** (extract Bidding Adjustment rows from Report 1)
- **[V4.1] Placement performance parser** (Report 7: campaign placement report with performance metrics)
- File auto-detection logic
- Product profile CRUD (create/read/update/delete), including `architecture_mode` selector
- **[V4.2] Precision Mode campaign count estimator in product profile UI**
- Basic app shell with sidebar navigation (6 views, placeholder content)
- Upload view: functional drag-and-drop, parsing feedback, data stored in Supabase
- Settings view: product profiles, basic app config

**Exit criteria:** Upload any Amazon report, data parsed and stored in Supabase (including placement data) with RLS enforced, campaign_registry updated, attribution maturity calculated, viewable in UI. Deployed to Vercel. Database is secure even if anon key is extracted.

### Sprint 2: In-App Analytics + Dashboard + Rules Engine
**Deliverables:**
- Performance analysis engine (TypeScript): computes all metrics, health scores, anomalies, trends
- **[V4.2] Spend-weighted health scores: dashboard sorts by `health_score * weekly_spend` by default**
- **[V4] Placement analysis engine** (Module 10): supports two modes - full performance analysis when Report 7 is available, modifier-only heuristics when only Report 1 is available. Dashboard notes which mode is active and prompts for Report 7 upload.
- **[V4] Budget pacing engine** (Module 11): computes utilization and pacing classifications
- **[V4] Rules engine core** (Module 9): loads rules, evaluates against data, generates actions, logs execution
- **[V4.2] Rules engine respects `data_maturity`: auto-approve only on mature data, pending with warning badge on partial data**
- **[V4] Default ruleset insertion** (8 default rules loaded on first run)
- Dashboard view: portfolio summary, campaign health table with scores, trend sparklines (Recharts)
- **[V4] Dashboard: budget pacing summary, placement performance summary, tag filter**
- **[V4.2] Dashboard: campaign health table default sort = weighted_score DESC, toggle available for raw score**
- Period-over-period comparison (if 2+ uploads exist)
- TACoS calculation (requires organic data join)
- Anomaly detection and alert display
- Inventory urgency calculation and display
- Data freshness tracking and alerts
- **[V4] Post-upload rules engine execution with result summary**

**Exit criteria:** Upload reports, see full dashboard with spend-weighted health scores, trends, anomalies, placement analysis, budget pacing, and rules-engine-generated actions. Rules respect attribution maturity. All computed in-app, zero API calls. This already provides significant optimization value before any Claude integration.

### Sprint 3: Rules Engine UI + Claude API Integration + Weekly Optimization
**Deliverables:**
- **[V4] Rules engine management UI** (Settings > Rules): list, toggle, edit, create, delete rules
- **[V4] Rule builder form** (metric selector, operator, value, action type, scope, schedule)
- **[V4] Rule performance dashboard** (actions generated, approval rate)
- Claude API client with Haiku and Sonnet support, prompt caching enabled
- **[V4.1] All Claude API calls use Vercel streaming response pattern (ReadableStream in API routes)** to prevent timeout issues. The API route streams the response to the client, which accumulates the JSON and parses on completion.
- Module 3+4 combined system prompt and API call function
- **[V4] Pre-filtering logic:** orchestrator sends only ambiguous entities to LLM, not full dataset
- Analysis view: two-section layout (rules actions + LLM actions)
- Approve/reject/modify controls per action
- Cost estimation display before API calls
- Optimization action storage in Supabase (with `source` and `rule_id` tracking)
- Batch "Approve All High-Confidence" and "Approve All Rules" actions
- **[V4] Conflict detection and side-by-side display**

**Exit criteria:** Full weekly optimization cycle works: upload data > rules engine runs automatically > dashboard shows health + rule actions > optionally run LLM analysis for complex cases > review all recommendations > approve actions.

### Sprint 4: Bulksheet Generator + End-to-End Workflow + Rollback
**Deliverables:**
- Bulksheet generation API route (SheetJS, implements all Module 7 rules)
- **[V4.2] Bulksheet batch tracking: every generated bulksheet gets a `batch_id`, all actions in that bulksheet are tagged with the same `bulksheet_batch_id` in optimization_actions**
- **[V4.2] Bulksheet history table: stores every generated bulksheet's metadata, action count, and status**
- **[V4.2] "Undo Last Bulksheet" feature: generates a reversal bulksheet that restores previous bids from `current_value` in optimization_actions, and pauses/archives any newly-created entities. Marks original actions as `rolled_back`.**
- **[V4] Graduation cascade generation** (full 5-8 row campaign creation from a single graduate action)
- **[V4] Placement modifier row generation**
- Bulksheet view: template selection, action summary, graduation cascade preview, generate, download
- **[V4.2] Bulksheet view: "Undo Last Bulksheet" button with confirmation dialog, rollback history**
- Record ID / Campaign ID / Ad Group ID tracking through the full pipeline
- Post-upload verification (parse Amazon's processing report for errors)
- Optimization history log with outcome tracking
- **[V4] Campaign tag CRUD UI** (assign/remove tags, filter by tags)

**Exit criteria:** Complete workflow: upload Amazon reports > rules engine + optional LLM analysis > approve > generate bulksheet (including graduation cascades and placement modifiers) > download. Bulksheet uploads to Amazon successfully. If a bad bulksheet is applied, "Undo Last Bulksheet" generates a working reversal file.

### Sprint 5: Amazon API Read Integration + Campaign Architecture + Keyword Research + Competitive Intel + SOV
**[V4.2] Sprint 5 combines API read access with the remaining modules. Getting automated report pulling live at the same time as the strategic modules dramatically reduces adoption friction. Users no longer need to manually download/upload reports weekly once this sprint is complete.**

**Deliverables (API Read):**
- Amazon Advertising API OAuth 2.0 connector (read-only scopes first)
- Automated data pull for Reports 1, 2, and 7 (replaces file upload for ad data)
- **[V4.2] Rules engine scheduling: daily execution via API data, not just on-upload**
- **[V4.2] Budget pacing with daily granularity: API provides daily spend data instead of period averages**
- Scheduling UI: configure pull frequency (daily recommended, minimum weekly)
- File upload remains available as fallback for Reports 3, 4, 5, 6 (business report, inventory, Brand Analytics, Helium 10) which are not available via the Advertising API

**Deliverables (Strategic Modules):**
- Module 1 (Campaign Architecture) API integration + UI, with Standard and Precision mode support
- **[V4.2] Precision Mode campaign count estimator: shows "This will create ~{N} campaigns" before generating**
- Module 2 (Keyword Research) API integration + UI, with Brand Analytics data as primary input, keyword priority tiers output
- **[V4.2] Module 2 "Discovery Gap" notice when no Helium 10 data present, enhanced Layer 4+ prompting for blind spot mitigation**
- Module 5 (Competitive Intelligence) API integration + UI
- Brand Analytics CSV import parser and storage
- **[V4] SOV Tracker** (Module 12): automatic SOV calculation on Brand Analytics import
- **[V4.2] SOV & Market Position view** (View 6): step-line charts (not smooth curves), data frequency indicator, import date labels
- Optional Helium 10/Jungle Scout CSV import parser
- Orchestrator state machine (lifecycle phase management, module routing, rules/LLM coordination)
- Optimization calendar display
- Full trend analysis view with Recharts line charts

**Exit criteria:** All 12 modules operational. Amazon API pulls ad data automatically on schedule. Rules engine runs daily on fresh API data. System manages full campaign lifecycle from new setup through maintenance. Brand Analytics data flows into keyword research and SOV tracking. Manual file upload only needed for business reports, inventory, and Brand Analytics (not available via ad API). SOV charts display honestly with step-line visualization.

### Sprint 6 (Future): Amazon API Write-Back + Semi-Autonomous Mode
**[V4.2] Sprint 5 handles read-only API access. Sprint 6 adds the ability to push changes back to Amazon via API, eliminating manual bulksheet uploads.**

**Deliverables:**
- Amazon Advertising API write scopes (campaign/keyword/bid updates)
- Automated change push (replaces manual bulksheet upload for bid changes, negations, pauses)
- Bulksheet generation remains available as fallback/manual override
- **[V4.2] Write-back guardrails: maximum bid change per entity per day, maximum total budget change per day, emergency stop button**
- Semi-autonomous mode with guardrails (rules auto-execute, LLM recommendations require manual approval)
- Email/notification digest of actions taken
- Weekly LLM optimization auto-scheduled (runs Sunday night, results ready Monday morning)

**Exit criteria:** System runs with minimal manual intervention. Rules engine handles daily routine via API. LLM runs weekly for strategic review. User reviews weekly summary. Manual intervention only needed for strategic decisions and Brand Analytics/inventory uploads.

### Sprint 7 (Future): Hourly Bidding via Amazon Marketing Stream
**Deliverables:**
- Amazon Marketing Stream (AMS) integration via AWS infrastructure
- Hourly data ingestion pipeline
- **[V4] Daypart profile management UI** (create/edit hourly bid multiplier profiles)
- **[V4] Hourly rules engine execution** (evaluate intra-day performance against daypart profiles)
- Hourly bid adjustment execution via Amazon Ads API
- Real-time placement optimization (hourly placement modifier adjustments)
- Intra-day budget pacing (reallocate when a campaign is capped before peak hours)

**Exit criteria:** System operates at Quartile-level hourly optimization cadence. Daypart profiles active. Bid adjustments execute hourly based on AMS data.

---

## Quality Standards

### For Module System Prompts
1. Every decision point has explicit logic (no "use your judgment")
2. Concrete numbers and formulas (not "increase moderately" but "increase 15%")
3. JSON output schema specified with TypeScript interface
4. Methodology attribution on each decision framework
5. Error handling for missing/incomplete/contradictory data
6. Amazon-specific formatting rules are exact (lowercase "enabled", camelCase "placementTop", etc.)
7. No filler sentences

### For the Application
1. Works on first deploy (no complex setup beyond Supabase connection)
2. Graceful degradation with partial data (no business report? skip TACoS, note what's missing)
3. Error resilience (file parsing handles format variations, API failures show clear retry options)
4. Dashboard renders fast (<1s with cached Supabase queries)
5. API cost displayed before every Claude call
6. All parsed data viewable in the UI (user can verify parsing accuracy)
7. Mobile-responsive (Tailwind handles this naturally)
8. **[V4] Rules engine execution time < 500ms** for typical account sizes (< 500 keywords)
9. **[V4] Rules engine audit trail complete** (every rule execution logged, every action traceable to a rule)
10. **[V4] Rules-generated actions clearly labeled** with rule name and source in the UI
11. **[V4.2] RLS enforced on every table** (database secure even if anon key extracted)
12. **[V4.2] All tables joined on campaign_id, not campaign_name** (rename-proof data integrity)
13. **[V4.2] Upload deduplication uses real Postgres transactions via RPC** (no data loss on partial failure)
14. **[V4.2] Attribution maturity checked before auto-approving rule actions** (no premature negations)
15. **[V4.2] Bulksheet batch tracking enables one-click rollback** (safety net for bad uploads)
16. **[V4.2] Dashboard default sort = spend-weighted health score** (high-impact campaigns surface first)

### For the Rules Engine
1. Every default rule has a clear, concise name and description
2. Cooldown periods prevent rule oscillation (bidding up then down then up)
3. Safety limits prevent runaway automation (max_actions_per_run cap)
4. Conflict resolution is deterministic (priority number, not random)
5. Auto-approve is opt-in per rule and off by default
6. Rule performance is tracked and visible (so users can disable underperforming rules)

---

## File Manifest

```
PROJECT ROOT (GitHub repo):

  src/
    app/                          # Next.js app router pages
      page.tsx                    # Dashboard
      login/page.tsx              # [V4.1] Supabase Auth login page
      upload/page.tsx             # Data upload view
      analysis/page.tsx           # Analysis & optimization view
      bulksheet/page.tsx          # Bulksheet generator view
      settings/page.tsx           # Settings, rules, history view
      sov/page.tsx                # [V4] SOV & Market Position view
      layout.tsx                  # [V4.1] Root layout with auth check + redirect
      api/
        parse/route.ts            # File parsing API route
        analyze/route.ts          # Claude API call route
        bulksheet/route.ts        # Bulksheet generation route
        bulksheet/rollback/route.ts # [V4.2] Rollback bulksheet generation route
        rules/route.ts            # [V4] Rules engine execution route
    
    components/                   # React components
      Dashboard/                  # Dashboard widgets
        PortfolioSummary.tsx
        CampaignHealthTable.tsx
        BudgetPacingSummary.tsx   # [V4]
        PlacementSummary.tsx      # [V4]
        SOVWidget.tsx             # [V4]
        TagFilter.tsx             # [V4]
      Upload/                     # File upload, parser feedback
      Analysis/                   # Module results, approve/reject UI
        RulesActions.tsx          # [V4] Rules engine action section
        LLMActions.tsx            # [V4] LLM analysis action section
        ConflictResolver.tsx      # [V4] Side-by-side conflict display
      Bulksheet/                  # Generation controls
        GraduationCascadePreview.tsx  # [V4]
      Settings/                   # Product profiles, config, history
        RulesManager.tsx          # [V4] Rules list, toggle, CRUD
        RuleBuilder.tsx           # [V4] Rule creation form
        RulePerformance.tsx       # [V4] Rule effectiveness dashboard
        TagManager.tsx            # [V4] Campaign tag CRUD
      SOV/                        # [V4] SOV & Market Position components
        SOVTrendChart.tsx
        CompetitorMovement.tsx
        OpportunityGaps.tsx
      shared/                     # Charts, tables, alerts, layout
    
    lib/
      supabase.ts                 # Supabase client
      auth.ts                     # [V4.1] Supabase Auth middleware + login helpers
      claude.ts                   # Claude API client with prompt caching + streaming
      campaign-registry.ts        # [V4.2] Campaign registry upsert logic
      parsers/
        bulksheet-parser.ts       # Report 1 parser (campaign/keyword/ad group data)
        placement-modifier-parser.ts  # [V4] Extract Bidding Adjustment rows from Report 1
        placement-performance-parser.ts  # [V4.1] Report 7 parser (placement performance)
        search-term-parser.ts     # Report 2 parser
        business-report-parser.ts # Report 3 parser
        inventory-parser.ts       # Report 4 parser
        brand-analytics-parser.ts # Report 5 parser (Brand Analytics)
        helium10-parser.ts        # Report 6 parser (optional)
        auto-detect.ts            # File type detection
        upload-dedup.ts           # [V4.2] RPC-based atomic deduplication (replaces V4.1 sequential)
        attribution.ts            # [V4.2] Attribution window detection + data maturity calculation
      analytics/
        metrics.ts                # In-app metric computation
        health-scores.ts          # Campaign health scoring
        anomaly-detection.ts      # Anomaly detection rules
        trends.ts                 # Trend analysis (linear regression)
        placement-optimizer.ts    # [V4] Module 10: Placement analysis
        budget-pacer.ts           # [V4] Module 11: Budget pacing
        sov-tracker.ts            # [V4] Module 12: SOV calculation
      rules/                      # [V4] Rules engine
        engine.ts                 # Core rules evaluation loop
        evaluators.ts             # Metric evaluation functions per rule type
        actions.ts                # Action generation from matched rules
        conflicts.ts              # Conflict detection and resolution
        defaults.ts               # Default ruleset definitions
      bulksheet/
        generator.ts              # Bulksheet output generation (SheetJS)
        formatting-rules.ts       # All Module 7 formatting rules
        graduation-cascade.ts     # [V4] Full graduation row generation
        rollback-generator.ts     # [V4.2] Reversal bulksheet generation from batch history
        batch-tracker.ts          # [V4.2] Bulksheet batch ID assignment + history logging
      orchestrator.ts             # Lifecycle state machine + rules/LLM routing
    
    modules/                      # Claude API system prompts
      module_01_architecture.ts
      module_02_keywords.ts
      module_03_bid_optimization.ts
      module_04_search_terms.ts
      module_05_competitive.ts
      module_03_04_combined.ts    # Weekly optimization combined prompt
    
    types/
      schemas.ts                  # All shared TypeScript interfaces
      rules.ts                    # [V4] Rules engine type definitions
      amazon-api.ts               # [V4.2] Amazon Advertising API types
    
    amazon-api/                   # [V4.2] Amazon API integration (Sprint 5+)
      connector.ts                # OAuth 2.0 client + token management
      report-puller.ts            # Automated report request + download
      scheduler.ts                # Cron-style scheduling for daily pulls
    
  supabase/
    migrations/
      001_initial_schema.sql      # All table definitions (V4 + V4.2: RLS, user_id, campaign_registry, bulksheet_history)
      002_default_rules.sql       # [V4] Default ruleset insertion
      003_rpc_functions.sql       # [V4.2] upsert_upload_batch + campaign_registry_upsert RPC functions
    
  docs/
    MODULE_07_BULKSHEET_BUILDER.md  # Already complete, reference doc
    MASTER_PLAN_V4_2.md             # This document
    
  package.json
  .env.local.example              # Template for env vars (Supabase URL, keys, Claude API key)
  README.md
```

---

## What This System Cannot Do (Where You Stay Involved)

Being honest about limitations is what separates expert systems from hype:

1. **Listing optimization.** The system can tell you CTR is 40% below category average, but it can't redesign your images or rewrite your bullets.

2. **Initial product research.** Deciding WHAT to sell is outside scope. This system optimizes advertising for products you already have.

3. **Pricing strategy.** The system can flag that your CPC is rising because a competitor dropped their price by $3, but the pricing decision is yours.

4. **Creative and brand decisions.** When to run coupons, when to do Lightning Deals, how to position against a new competitor entering your niche.

5. **Amazon policy compliance.** The system doesn't monitor for restricted keywords, prohibited claims, or category-specific advertising rules.

6. **First 14 days of a new campaign.** The system needs data to optimize. The initial campaign architecture (Module 1) requires human judgment about positioning and competitive angle. After 14 days of data, the rules engine and LLM take over.

7. **Cross-channel strategy.** This system covers Sponsored Products only in V1. Sponsored Brands, Sponsored Display, DSP, and off-Amazon traffic are not in scope. However, the architecture (particularly the rules engine, placement optimizer, and cross-channel schema patterns) is designed to extend to additional ad types in future versions.

8. **Hourly bidding (V1-V6).** True Quartile-style hourly optimization requires Amazon Marketing Stream access and AWS infrastructure. The system architecture supports this (Sprint 7, daypart profiles), but V1 operates on a weekly cadence, progressing to daily in Sprint 5 when API read is connected.

Everything else, this system should handle as well or better than a human expert, and it will keep getting better as your data history grows and you tune your rules.
