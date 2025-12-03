-- Migration: Update reconciliation_results table for multi-cloud reconciliation
-- Date: 2025-11-27
-- Phase: 2 - Reconciliation Engine

-- Drop old table structure (this is safe in development)
DROP TABLE IF EXISTS reconciliation_results CASCADE;

-- Create new reconciliation_results table
CREATE TABLE reconciliation_results (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reconciliation run identification
    run_id VARCHAR(255) NOT NULL,

    -- Event identification
    event_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,

    -- Reconciliation window
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,

    -- Overall status
    status VARCHAR(50) NOT NULL,
    -- Possible values: consistent, missing, inconsistent, duplicate, out_of_order

    -- Source comparison
    expected_sources TEXT[] NOT NULL,
    found_in_sources TEXT[],
    missing_from_sources TEXT[],

    -- Event data comparison (JSONB)
    event_instances JSONB,

    -- Detected issues (JSONB array)
    issues JSONB,

    -- Metrics
    consistency_score FLOAT,
    latency_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    reconciled_at TIMESTAMP,

    -- Indexes
    CONSTRAINT chk_consistency_score CHECK (consistency_score >= 0.0 AND consistency_score <= 1.0)
);

-- Create indexes for performance
CREATE INDEX idx_reconciliation_run_status ON reconciliation_results(run_id, status);
CREATE INDEX idx_reconciliation_event_id ON reconciliation_results(event_id);
CREATE INDEX idx_reconciliation_created_at_desc ON reconciliation_results(created_at DESC);
CREATE INDEX idx_reconciliation_status_severity ON reconciliation_results(status, created_at);
CREATE INDEX idx_reconciliation_window_start ON reconciliation_results(window_start);
CREATE INDEX idx_reconciliation_event_type ON reconciliation_results(event_type);

-- Add comments for documentation
COMMENT ON TABLE reconciliation_results IS 'Results of multi-cloud event reconciliation comparing events across AWS, GCP, Azure';
COMMENT ON COLUMN reconciliation_results.run_id IS 'Groups all results from the same reconciliation execution';
COMMENT ON COLUMN reconciliation_results.consistency_score IS 'Score from 0.0 (totally inconsistent) to 1.0 (perfect match)';
COMMENT ON COLUMN reconciliation_results.event_instances IS 'JSON map of source -> event data for comparison';
COMMENT ON COLUMN reconciliation_results.issues IS 'Array of detected issues with severity levels';
