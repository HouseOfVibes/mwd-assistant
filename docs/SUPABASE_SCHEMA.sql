-- MWD Agent Supabase Schema
-- Run this in your Supabase SQL editor to set up the database

-- =============================================================================
-- CONVERSATIONS TABLE
-- Stores Slack bot conversation history for context
-- =============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id VARCHAR(50) NOT NULL,
    thread_ts VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    actions_taken JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for quick thread lookups
CREATE INDEX IF NOT EXISTS idx_conversations_thread
ON conversations(channel_id, thread_ts);

-- Index for user history
CREATE INDEX IF NOT EXISTS idx_conversations_user
ON conversations(user_id, created_at DESC);

-- =============================================================================
-- PROJECTS TABLE
-- Stores project state and deliverables
-- =============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_lead_id VARCHAR(50),
    invoice_project_id VARCHAR(50),
    company_name VARCHAR(255) NOT NULL,
    intake_data JSONB,
    status VARCHAR(50) DEFAULT 'new',
    payment_status VARCHAR(50),
    deliverables JSONB DEFAULT '{}',
    notion_url TEXT,
    google_drive_folder TEXT,
    slack_channel VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for invoice system lookups
CREATE INDEX IF NOT EXISTS idx_projects_invoice_lead
ON projects(invoice_lead_id);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_projects_status
ON projects(status);

-- =============================================================================
-- DELIVERABLES TABLE
-- Stores AI-generated deliverables
-- =============================================================================

CREATE TABLE IF NOT EXISTS deliverables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    deliverable_type VARCHAR(50) NOT NULL,
    ai_model VARCHAR(50),
    content JSONB NOT NULL,
    formatted_output JSONB,
    tokens_used JSONB,
    cost DECIMAL(10, 4),
    status VARCHAR(20) DEFAULT 'generated',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for project deliverables
CREATE INDEX IF NOT EXISTS idx_deliverables_project
ON deliverables(project_id);

-- =============================================================================
-- WEBHOOK_LOGS TABLE
-- Logs all webhook events for debugging
-- =============================================================================

CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(50),
    payload JSONB,
    response_status INTEGER,
    response_body JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for event type filtering
CREATE INDEX IF NOT EXISTS idx_webhook_logs_event
ON webhook_logs(event_type, created_at DESC);

-- =============================================================================
-- AI_USAGE TABLE
-- Track AI API usage and costs
-- =============================================================================

CREATE TABLE IF NOT EXISTS ai_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ai_provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    operation VARCHAR(100),
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 6),
    project_id UUID REFERENCES projects(id),
    user_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for usage reporting
CREATE INDEX IF NOT EXISTS idx_ai_usage_provider
ON ai_usage(ai_provider, created_at DESC);

-- Index for project cost tracking
CREATE INDEX IF NOT EXISTS idx_ai_usage_project
ON ai_usage(project_id);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable if you need multi-tenant security
-- =============================================================================

-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE deliverables ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for projects table
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
