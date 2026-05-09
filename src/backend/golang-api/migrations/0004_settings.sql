CREATE TABLE IF NOT EXISTS settings (
    key        VARCHAR(100) PRIMARY KEY,
    value      VARCHAR(255) NOT NULL,
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO settings (key, value) VALUES
    ('maintenance_web',    'false'),
    ('maintenance_mobile', 'false'),
    ('feature_graph',      'true')
ON CONFLICT (key) DO NOTHING;
