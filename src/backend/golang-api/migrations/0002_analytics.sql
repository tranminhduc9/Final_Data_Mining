ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

CREATE TABLE IF NOT EXISTS page_visits (
    visit_date DATE        NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    PRIMARY KEY (visit_date, ip_address)
);

CREATE TABLE IF NOT EXISTS keyword_searches (
    id          BIGSERIAL PRIMARY KEY,
    keyword     TEXT        NOT NULL,
    endpoint    VARCHAR(50) NOT NULL,
    searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keyword_searches_keyword     ON keyword_searches(keyword);
CREATE INDEX IF NOT EXISTS idx_keyword_searches_searched_at ON keyword_searches(searched_at);
