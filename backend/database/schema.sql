-- Tabela funduszy (statyczna, tworzona ze schema.sql przy każdym starcie)
CREATE TABLE IF NOT EXISTS funds (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    stooq_ticker TEXT,
    analizy_code TEXT,
    currency     TEXT    NOT NULL DEFAULT 'PLN',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Tabela transakcji (dane użytkownika)
CREATE TABLE IF NOT EXISTS transactions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL DEFAULT 'default',
    fund_code      TEXT NOT NULL,
    type           TEXT NOT NULL CHECK (type IN ('BUY', 'SELL')),
    date           TEXT NOT NULL,
    units          REAL NOT NULL CHECK (units > 0),
    price_per_unit REAL NOT NULL CHECK (price_per_unit > 0),
    total_value    REAL NOT NULL,
    notes          TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (fund_code) REFERENCES funds (code)
);

-- Fundusze dostępne na platformie (uzupełniasz Ty jako deweloper)
INSERT OR IGNORE INTO funds (code, name, stooq_ticker, analizy_code)
VALUES ('UNI23', 'Generali Stabilny Wzrost', '3965.n', 'UNI23');

-- Tabela uytkowników (nick + pin)
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    pin         TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
)