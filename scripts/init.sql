-- Helios Database Initialization Script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    event_metadata JSONB,
    ingested_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,

    -- Extracted fields for fast queries
    order_id VARCHAR(255) GENERATED ALWAYS AS (payload->>'order_id') STORED,
    customer_id VARCHAR(255) GENERATED ALWAYS AS (payload->>'customer_id') STORED
);

-- Indexes for events table
CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id);
CREATE INDEX IF NOT EXISTS idx_events_order_id ON events(order_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_ingested_at ON events(ingested_at);
CREATE INDEX IF NOT EXISTS idx_events_customer_id ON events(customer_id);

-- Reconciliation results table
CREATE TABLE IF NOT EXISTS reconciliation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(255) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,

    -- Event references
    order_event_id UUID REFERENCES events(id),
    payment_event_id UUID REFERENCES events(id),
    inventory_event_id UUID REFERENCES events(id),

    -- Validation results
    missing_events TEXT[],
    validation_errors JSONB,

    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    reconciled_at TIMESTAMP
);

-- Indexes for reconciliation_results table
CREATE INDEX IF NOT EXISTS idx_reconciliation_order_id ON reconciliation_results(order_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_status ON reconciliation_results(status);
CREATE INDEX IF NOT EXISTS idx_reconciliation_window_start ON reconciliation_results(window_start);
CREATE INDEX IF NOT EXISTS idx_reconciliation_created_at ON reconciliation_results(created_at);

-- Self-healing actions table
CREATE TABLE IF NOT EXISTS self_healing_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(100) NOT NULL,
    trigger_reason VARCHAR(255) NOT NULL,
    triggered_by VARCHAR(50),

    -- Action details
    target JSONB,
    status VARCHAR(50) NOT NULL,

    -- Timing
    triggered_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER,

    -- Results
    success BOOLEAN,
    error_message TEXT
);

-- Indexes for self_healing_actions table
CREATE INDEX IF NOT EXISTS idx_actions_action_type ON self_healing_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_actions_status ON self_healing_actions(status);
CREATE INDEX IF NOT EXISTS idx_actions_triggered_at ON self_healing_actions(triggered_at);

-- Replay history table
CREATE TABLE IF NOT EXISTS replay_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    replay_id VARCHAR(255) UNIQUE NOT NULL,

    -- Replay parameters
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    filters JSONB,
    target_env VARCHAR(50),

    -- Results
    events_count INTEGER,
    status VARCHAR(50),

    -- Metadata
    initiated_by VARCHAR(255),
    initiated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Indexes for replay_history table
CREATE INDEX IF NOT EXISTS idx_replay_replay_id ON replay_history(replay_id);
CREATE INDEX IF NOT EXISTS idx_replay_status ON replay_history(status);
CREATE INDEX IF NOT EXISTS idx_replay_initiated_at ON replay_history(initiated_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO helios;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO helios;
