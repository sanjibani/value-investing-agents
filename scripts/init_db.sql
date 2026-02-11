-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Episodic Memory: All insights generated
CREATE TABLE insights (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    signal_type VARCHAR(100), -- 'insider_buy', 'merger_arb', 'spinoff', etc.
    company_symbol VARCHAR(20),
    company_name VARCHAR(200),
    headline TEXT,
    evidence JSONB, -- Array of facts with sources
    analysis TEXT,
    interestingness_score FLOAT,
    shown_to_user BOOLEAN DEFAULT FALSE,
    embedding vector(384), -- For semantic search (MiniLM-L6)
    metadata JSONB -- Flexible additional data
);

-- Feedback Memory: Human ratings and comments
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    insight_id INTEGER REFERENCES insights(id),
    created_at TIMESTAMP DEFAULT NOW(),
    star_rating INTEGER CHECK (star_rating BETWEEN 1 AND 5),
    tags TEXT[], -- ['excellent', 'interesting', 'meh', 'irrelevant']
    comment TEXT,
    invested BOOLEAN,
    outcome_return FLOAT, -- If invested, what was return
    outcome_date DATE
);

-- Procedural Memory: What works
CREATE TABLE research_patterns (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(200),
    pattern_description TEXT,
    success_rate FLOAT, -- Based on feedback
    avg_rating FLOAT,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    embedding vector(384),
    metadata JSONB
);

-- Semantic Memory: Company knowledge
CREATE TABLE companies (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(200),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    last_updated TIMESTAMP,
    fundamentals JSONB, -- Financial metrics
    filing_history JSONB, -- Recent filings summary
    embedding vector(384)
);

-- Signal tracking
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    discovered_at TIMESTAMP DEFAULT NOW(),
    signal_type VARCHAR(100),
    company_symbol VARCHAR(20),
    raw_data JSONB,
    processed BOOLEAN DEFAULT FALSE,
    resulted_in_insight BOOLEAN DEFAULT FALSE,
    insight_id INTEGER REFERENCES insights(id)
);

-- Reward model training data
CREATE TABLE reward_training (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    insight_features JSONB, -- Features extracted from insight
    human_rating FLOAT,
    used_in_training BOOLEAN DEFAULT FALSE
);

-- Cache for API responses
CREATE TABLE api_cache (
    cache_key VARCHAR(500) PRIMARY KEY,
    response_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_insights_created ON insights(created_at DESC);
CREATE INDEX idx_insights_company ON insights(company_symbol);
CREATE INDEX idx_insights_score ON insights(interestingness_score DESC);
CREATE INDEX idx_feedback_rating ON feedback(star_rating);
CREATE INDEX idx_signals_processed ON signals(processed, discovered_at);

-- Vector similarity search indexes (using HNSW for speed)
CREATE INDEX ON insights USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON research_patterns USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON companies USING hnsw (embedding vector_cosine_ops);
