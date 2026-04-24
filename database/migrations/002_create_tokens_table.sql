CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    token_type VARCHAR(50) NOT NULL,
    token_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT unique_token_type UNIQUE(token_type)
);

CREATE INDEX IF NOT EXISTS idx_tokens_type ON tokens(token_type);
CREATE INDEX IF NOT EXISTS idx_tokens_active ON tokens(is_active);

COMMENT ON TABLE tokens IS 'Authentication tokens storage';
COMMENT ON COLUMN tokens.token_type IS 'Type of token (e.g., bearer_token)';
COMMENT ON COLUMN tokens.token_value IS 'Encrypted or plain token value';
COMMENT ON COLUMN tokens.created_at IS 'When token was first created';
COMMENT ON COLUMN tokens.updated_at IS 'When token was last updated';
COMMENT ON COLUMN tokens.expires_at IS 'Token expiration time (optional)';
COMMENT ON COLUMN tokens.is_active IS 'Whether token is currently active';

DO $$
BEGIN
    RAISE NOTICE 'Migration 002 completed successfully!';
    RAISE NOTICE 'Table "tokens" created with indexes.';
END $$;
