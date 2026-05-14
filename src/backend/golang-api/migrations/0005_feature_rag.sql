INSERT INTO settings (key, value) VALUES
    ('feature_rag', 'true')
ON CONFLICT (key) DO NOTHING;
