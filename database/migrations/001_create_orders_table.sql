CREATE TABLE IF NOT EXISTS orders (
    id BIGINT PRIMARY KEY,
    created_at DATE NOT NULL,
    closed_at DATE,
    
    status_id INTEGER NOT NULL,
    status_name VARCHAR(255) NOT NULL,
    
    manager_id INTEGER,
    manager_name VARCHAR(255),
    
    grand_total DECIMAL(10,2) NOT NULL,
    
    prp_date DATE,
    
    scraped_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status_id ON orders(status_id);
CREATE INDEX IF NOT EXISTS idx_orders_status_name ON orders(status_name);
CREATE INDEX IF NOT EXISTS idx_orders_manager_id ON orders(manager_id);
CREATE INDEX IF NOT EXISTS idx_orders_prp_date ON orders(prp_date);
CREATE INDEX IF NOT EXISTS idx_orders_scraped_at ON orders(scraped_at);

COMMENT ON TABLE orders IS 'KeyCRM orders data';
COMMENT ON COLUMN orders.id IS 'Order ID from KeyCRM';
COMMENT ON COLUMN orders.created_at IS 'Order creation date (without time)';
COMMENT ON COLUMN orders.closed_at IS 'Order closing date (without time)';
COMMENT ON COLUMN orders.status_id IS 'Status ID from KeyCRM';
COMMENT ON COLUMN orders.status_name IS 'Status name (text)';
COMMENT ON COLUMN orders.manager_id IS 'Manager ID from KeyCRM (can be NULL)';
COMMENT ON COLUMN orders.manager_name IS 'Manager full name (can be NULL)';
COMMENT ON COLUMN orders.grand_total IS 'Total order amount';
COMMENT ON COLUMN orders.prp_date IS 'PRP date from custom_fields (field_id=121), can be NULL';
COMMENT ON COLUMN orders.scraped_at IS 'When data was scraped';
COMMENT ON COLUMN orders.updated_at IS 'When record was last updated';

DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed successfully!';
    RAISE NOTICE 'Table "orders" created with indexes.';
END $$;
