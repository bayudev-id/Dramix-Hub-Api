-- Create table to store Viu sessions and account details
CREATE TABLE IF NOT EXISTS viu_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    nickname VARCHAR(255),
    token TEXT NOT NULL,
    access_token TEXT,
    is_vip BOOLEAN DEFAULT FALSE,
    plan_name VARCHAR(100),
    payment_status VARCHAR(100),
    device_list JSONB DEFAULT '[]'::jsonb,
    last_login_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by user_id
CREATE INDEX IF NOT EXISTS idx_viu_sessions_user_id ON viu_sessions(user_id);

-- Index for searching active VIP tokens
CREATE INDEX IF NOT EXISTS idx_viu_sessions_is_vip ON viu_sessions(is_vip) WHERE is_vip = TRUE;
