-- =====================================================================
-- Amazon Ads Agentic Operating System - V5.0 Schema
-- =====================================================================
-- Phase 0: Initial schema for persistent memory layer.
-- Designed for Supabase (Postgres) with RLS.
-- =====================================================================

-- Campaign registry: canonical identity for campaigns
CREATE TABLE IF NOT EXISTS campaign_registry (
    campaign_id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    marketplace_id TEXT DEFAULT 'ATVPDKIKX0DER',
    current_name TEXT NOT NULL,
    previous_names TEXT[],
    campaign_type TEXT,          -- auto, exact, broad, phrase, conquest, defense
    targeting_type TEXT,          -- AUTO or MANUAL
    first_seen_date DATE DEFAULT CURRENT_DATE,
    last_seen_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE campaign_registry ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_campaigns" ON campaign_registry
    FOR ALL USING (auth.uid() = user_id);

-- Product profiles
CREATE TABLE IF NOT EXISTS product_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    marketplace_id TEXT DEFAULT 'ATVPDKIKX0DER',
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
    target_tacos DECIMAL(5,2),
    lifecycle_stage TEXT DEFAULT 'optimization',
    architecture_mode TEXT DEFAULT 'standard',
    monthly_budget DECIMAL(10,2),
    brand TEXT,
    category TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE product_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_profiles" ON product_profiles
    FOR ALL USING (auth.uid() = user_id);

-- Campaign performance snapshots (daily)
CREATE TABLE IF NOT EXISTS campaign_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    snapshot_date DATE NOT NULL,
    report_period TEXT DEFAULT '7d',
    attribution_window TEXT DEFAULT '14d',
    data_maturity TEXT DEFAULT 'mature',
    campaign_id TEXT,
    campaign_name TEXT NOT NULL,
    state TEXT,
    daily_budget DECIMAL(10,2),
    bidding_strategy TEXT,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    orders_7d INTEGER DEFAULT 0,
    sales_7d DECIMAL(10,2) DEFAULT 0,
    orders_14d INTEGER DEFAULT 0,
    sales_14d DECIMAL(10,2) DEFAULT 0,
    acos_7d DECIMAL(6,2) DEFAULT 0,
    acos_14d DECIMAL(6,2) DEFAULT 0,
    cpc DECIMAL(6,4) DEFAULT 0,
    ctr DECIMAL(6,4) DEFAULT 0,
    cvr_7d DECIMAL(6,4) DEFAULT 0,
    cvr_14d DECIMAL(6,4) DEFAULT 0,
    roas_7d DECIMAL(6,2) DEFAULT 0,
    roas_14d DECIMAL(6,2) DEFAULT 0,
    health_score INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE campaign_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_snapshots" ON campaign_snapshots
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX IF NOT EXISTS idx_camp_snap_date ON campaign_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_camp_snap_cid ON campaign_snapshots(campaign_id);

-- Keyword performance snapshots
CREATE TABLE IF NOT EXISTS keyword_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    snapshot_date DATE NOT NULL,
    data_maturity TEXT DEFAULT 'mature',
    campaign_id TEXT,
    campaign_name TEXT,
    ad_group_id TEXT,
    ad_group_name TEXT,
    keyword_id TEXT,
    keyword_text TEXT,
    match_type TEXT,
    bid DECIMAL(6,4),
    state TEXT,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    orders_7d INTEGER DEFAULT 0,
    sales_7d DECIMAL(10,2) DEFAULT 0,
    orders_14d INTEGER DEFAULT 0,
    sales_14d DECIMAL(10,2) DEFAULT 0,
    acos_7d DECIMAL(6,2) DEFAULT 0,
    acos_14d DECIMAL(6,2) DEFAULT 0,
    cpc DECIMAL(6,4) DEFAULT 0,
    cvr_7d DECIMAL(6,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE keyword_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_kw_snapshots" ON keyword_snapshots
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX IF NOT EXISTS idx_kw_snap_date ON keyword_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_kw_snap_text ON keyword_snapshots(keyword_text);

-- Search term reports
CREATE TABLE IF NOT EXISTS search_term_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    snapshot_date DATE NOT NULL,
    data_maturity TEXT DEFAULT 'mature',
    campaign_id TEXT,
    campaign_name TEXT,
    ad_group_name TEXT,
    targeting TEXT,
    search_term TEXT NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    orders_7d INTEGER DEFAULT 0,
    sales_7d DECIMAL(10,2) DEFAULT 0,
    acos_7d DECIMAL(6,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE search_term_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_search_terms" ON search_term_reports
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX IF NOT EXISTS idx_str_date ON search_term_reports(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_str_term ON search_term_reports(search_term);

-- Agent sessions (every agentic run)
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    session_type TEXT NOT NULL,   -- daily_optimization, weekly_review, monthly_review, ad_hoc
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running', -- running, completed, failed
    summary TEXT,
    actions_taken INTEGER DEFAULT 0,
    metrics_snapshot JSONB,       -- key metrics at time of session
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE agent_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_sessions" ON agent_sessions
    FOR ALL USING (auth.uid() = user_id);

-- Agent decisions (every decision with reasoning)
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    session_id UUID REFERENCES agent_sessions(id),
    decision_type TEXT NOT NULL,   -- bid_adjustment, negation, budget_change, campaign_create, etc.
    entity_type TEXT,              -- campaign, keyword, search_term, etc.
    entity_id TEXT,
    entity_name TEXT,
    previous_value DECIMAL(10,4),
    new_value DECIMAL(10,4),
    reasoning TEXT NOT NULL,
    confidence TEXT DEFAULT 'medium', -- high, medium, low
    data_points JSONB,            -- supporting data for the decision
    expected_outcome TEXT,
    review_in_days INTEGER DEFAULT 7,
    guardrail_check TEXT,         -- PASS/FAIL + details
    status TEXT DEFAULT 'pending', -- pending, approved, executed, rejected, rolled_back
    executed_at TIMESTAMPTZ,
    outcome_actual TEXT,
    outcome_measured_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE agent_decisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_decisions" ON agent_decisions
    FOR ALL USING (auth.uid() = user_id);
CREATE INDEX IF NOT EXISTS idx_decisions_session ON agent_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON agent_decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_type ON agent_decisions(decision_type);

-- Strategy state (current strategic context)
CREATE TABLE IF NOT EXISTS strategy_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    key TEXT NOT NULL,             -- e.g., 'overall_strategy', 'bid_philosophy', 'competitive_stance'
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, key)
);
ALTER TABLE strategy_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_strategy" ON strategy_state
    FOR ALL USING (auth.uid() = user_id);

-- Guardrails configuration
CREATE TABLE IF NOT EXISTS guardrails_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    rule_name TEXT NOT NULL,
    rule_type TEXT NOT NULL,       -- hard_limit, soft_limit
    parameter TEXT NOT NULL,       -- max_bid, max_budget_change_pct, min_clicks_before_negate, etc.
    value DECIMAL(10,4) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, parameter)
);
ALTER TABLE guardrails_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_guardrails" ON guardrails_config
    FOR ALL USING (auth.uid() = user_id);

-- Negative keywords master list
CREATE TABLE IF NOT EXISTS negative_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    keyword_text TEXT NOT NULL,
    match_type TEXT DEFAULT 'NEGATIVE_EXACT',
    campaign_id TEXT,
    campaign_name TEXT,
    level TEXT DEFAULT 'campaign',
    reason TEXT,
    source TEXT DEFAULT 'agent',   -- agent, manual, rules_engine
    added_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE negative_keywords ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_negatives" ON negative_keywords
    FOR ALL USING (auth.uid() = user_id);
