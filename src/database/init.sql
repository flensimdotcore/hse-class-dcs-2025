CREATE TABLE IF NOT EXISTS processed_numbers (
    id SERIAL PRIMARY KEY,
    number INTEGER UNIQUE NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_number ON processed_numbers(number);
CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_numbers(processed_at);
