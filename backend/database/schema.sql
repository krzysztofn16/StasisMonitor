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
-- Fundusze Generali Investments TFI — FIO
-- Tickery Stooq potwierdzone przez wyszukiwanie, NULL = wymaga ręcznej weryfikacji na stooq.pl

INSERT OR IGNORE INTO funds (code, name, stooq_ticker, analizy_code) VALUES
('UNI23', 'Generali Stabilny Wzrost',                      '3965.n', 'UNI23'),
('UNI02', 'Generali Korona Zrównoważony',                  '3962.n', 'UNI02'),
('UNI07', 'Generali Korona Obligacje',                     '3960.n', 'UNI07'),
('UNI04', 'Generali Korona Akcje',                         '3959.n', 'UNI04'),
('UNI66', 'Generali Akcji Megatrendy',                     '3953.n', 'UNI66'),
('UNI19', 'Generali Akcje Małych i Średnich Spółek',       '3954.n', 'UNI19'),
('UNI67', 'Generali Złota',                                '3971.n', 'UNI67'),
('UNI03', 'Generali Korona Obligacji Uniwersalny',         '3961.n', 'UNI03'),
('UNI32', 'Generali Obligacji Krótkoterminowy',            '3963.n', 'UNI32'),
('UNI28', 'Generali Obligacje Aktywny',                    '3975.n', 'UNI28'),
('UNI49', 'Generali Obligacji Uniwersalny Plus',           '3972.n', 'UNI49'),
('UNI64', 'Generali Obligacje Globalne Rynki Wschodzące',  '1606.n', 'UNI64'),
('UNI73', 'Generali Konserwatywny',                        '3964.n', 'UNI73'),
('UNI75', 'Generali Surowców',                             '3965.n', 'UNI75'),
('UNI77', 'Generali Akcje Value',                          '3957.n', 'UNI77'),
('UNI74', 'Generali Akcji Rynków Wschodzących',            '3955.n', 'UNI74'),
('UNI78', 'Generali Akcji Ekologicznych Globalny',         '3970.n', 'UNI78'),
('UNI70', 'Generali Akcji Ekologicznych Europejski',       '1178.n', 'UNI70'),
('UNI25_E', 'Generali Euro',                               '3973.n', 'UNI25_E'),
('UNI30_U', 'Generali Dolar',                              '3958.n', 'UNI30_U'),
('PZU01',  'PZU Akcji KRAKOWIAK',                          '1140.n', 'PZU01'),
('PZU02',  'PZU Akcji Polskich',                           '1137.n', 'PZU02'),
('PZU10',  'PZU Akcji Małych i Średnich Spółek',           '1139.n', 'PZU10'),
('PZU69',  'PZU Akcji Odpowiedzialnego Rozwoju',           '1138.n', 'PZU69'),
('PZU08',  'PZU Zrównoważony',                             '1122.n', 'PZU08'),
('PZU05',  'PZU Stabilnego Wzrostu Mazurek',               '1124.n', 'PZU05'),
('PZU13',  'PZU Aktywny Globalny',                         '1136.n', 'PZU13'),
('PZU11',  'PZU Globalny Akcji Medycznych',                '1131.n', 'PZU11'),
('PZU14',  'PZU Dłużny Rynków Wschodzących',               '1135.n', 'PZU14'),
('PZU96',  'PZU Dłużny Korporacyjny',                      '1141.n', 'PZU96');

-- Tabela uytkowników (nick + pin)
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    pin         TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
)