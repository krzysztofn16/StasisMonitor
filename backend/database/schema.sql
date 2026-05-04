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
);

-- ============================================================
-- Tabela alokacji funduszy
-- Źródło: analizy.pl, kupfundusz.pl, prospekty funduszu
-- Data: Kwiecień 2026
-- Uwaga: dane typowe/historyczne — aktualizuj raz na kwartał
-- ============================================================

CREATE TABLE IF NOT EXISTS fund_allocation (
    fund_code   TEXT NOT NULL,
    category    TEXT NOT NULL,   -- 'Akcje' | 'Obligacje' | 'Gotówka' | 'Surowce' | 'Inne'
    percentage  REAL NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (date('now')),
    PRIMARY KEY (fund_code, category)
);

-- ============================================================
-- GENERALI — fundusze mieszane
-- ============================================================

-- UNI23 Generali Stabilny Wzrost
-- Źródło: analizy.pl — dane na 31.12.2025
-- Akcje ~28% (krajowe 25.8% + zagraniczne 2.5%), Obligacje ~70%, Gotówka ~2%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI23', 'Akcje',     28.3),
('UNI23', 'Obligacje', 69.9),
('UNI23', 'Gotówka',    1.8);

-- UNI02 Generali Korona Zrównoważony
-- Źródło: analizy.pl — historycznie akcje 40-55%, benchmark 50/50 WIG+obligacje
-- Typowa alokacja: akcje ~48%, obligacje ~48%, gotówka ~4%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI02', 'Akcje',     48.0),
('UNI02', 'Obligacje', 48.0),
('UNI02', 'Gotówka',    4.0);

-- ============================================================
-- GENERALI — fundusze akcyjne
-- ============================================================

-- UNI04 Generali Korona Akcje
-- Źródło: polityka inwestycyjna — min. 66% akcje, reszta instrumenty dłużne
-- Typowa alokacja: akcje ~85%, obligacje ~10%, gotówka ~5%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI04', 'Akcje',     85.0),
('UNI04', 'Obligacje', 10.0),
('UNI04', 'Gotówka',    5.0);

-- UNI66 Generali Akcji Megatrendy
-- Fundusz akcji globalnych — min. 66% akcje globalne tematyczne
-- Typowa alokacja: akcje ~90%, gotówka ~10%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI66', 'Akcje',     90.0),
('UNI66', 'Obligacje',  0.0),
('UNI66', 'Gotówka',   10.0);

-- UNI19 Generali Akcje Małych i Średnich Spółek
-- Fundusz akcji MiŚ — min. 66% akcje małych i średnich spółek
-- Typowa alokacja: akcje ~90%, gotówka ~10%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI19', 'Akcje',     90.0),
('UNI19', 'Obligacje',  0.0),
('UNI19', 'Gotówka',   10.0);

-- UNI67 Generali Złota
-- Fundusz surowcowy — min. 66% w instrumenty powiązane ze złotem (spółki wydobywcze, ETF)
-- Typowa alokacja: surowce/złoto ~90%, gotówka ~10%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI67', 'Akcje',      0.0),
('UNI67', 'Obligacje',  0.0),
('UNI67', 'Surowce',   90.0),
('UNI67', 'Gotówka',   10.0);

-- UNI77 Generali Akcje Value
-- Fundusz akcji value — min. 66% akcje niedowartościowane
-- Typowa alokacja: akcje ~90%, gotówka ~10%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI77', 'Akcje',     90.0),
('UNI77', 'Obligacje',  0.0),
('UNI77', 'Gotówka',   10.0);

-- UNI74 Generali Akcji Rynków Wschodzących
-- Fundusz akcji emerging markets — min. 66% akcje rynków wschodzących
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI74', 'Akcje',     90.0),
('UNI74', 'Obligacje',  0.0),
('UNI74', 'Gotówka',   10.0);

-- UNI78 Generali Akcji Ekologicznych Globalny
-- Fundusz akcji ESG globalnych — min. 66% akcje spółek ekologicznych
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI78', 'Akcje',     90.0),
('UNI78', 'Obligacje',  0.0),
('UNI78', 'Gotówka',   10.0);

-- UNI70 Generali Akcji Ekologicznych Europejski
-- Fundusz akcji ESG europejskich — min. 66% akcje spółek ekologicznych z Europy
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI70', 'Akcje',     90.0),
('UNI70', 'Obligacje',  0.0),
('UNI70', 'Gotówka',   10.0);

-- ============================================================
-- GENERALI — fundusze dłużne
-- ============================================================

-- UNI07 Generali Korona Obligacje
-- Źródło: analizy.pl — trzon to obligacje skarbowe PL + CEE
-- Typowa alokacja: obligacje ~95%, gotówka ~5%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI07', 'Akcje',      0.0),
('UNI07', 'Obligacje', 95.0),
('UNI07', 'Gotówka',    5.0);

-- UNI03 Generali Korona Obligacji Uniwersalny
-- Źródło: analizy.pl — skarbowe ~20%, nieskarbowe ~40%, zagraniczne ~40%
-- Typowa alokacja: obligacje ~95%, gotówka ~5%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI03', 'Akcje',      0.0),
('UNI03', 'Obligacje', 95.0),
('UNI03', 'Gotówka',    5.0);

-- UNI32 Generali Obligacji Krótkoterminowy
-- Fundusz dłużny krótkoterminowy — instrumenty do 397 dni
-- Typowa alokacja: obligacje ~95%, gotówka ~5%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI32', 'Akcje',      0.0),
('UNI32', 'Obligacje', 95.0),
('UNI32', 'Gotówka',    5.0);

-- UNI28 Generali Obligacje Aktywny
-- Źródło: analizy.pl — skarbowe krajowe + zagraniczne, duration do 9 lat
-- Typowa alokacja: obligacje ~95%, gotówka ~5%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI28', 'Akcje',      0.0),
('UNI28', 'Obligacje', 95.0),
('UNI28', 'Gotówka',    5.0);

-- UNI49 Generali Obligacji Uniwersalny Plus
-- Fundusz dłużny — podobny do UNI03 z szerszym mandatem
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI49', 'Akcje',      0.0),
('UNI49', 'Obligacje', 95.0),
('UNI49', 'Gotówka',    5.0);

-- UNI64 Generali Obligacje Globalne Rynki Wschodzące
-- Fundusz dłużny emerging markets — obligacje rządowe i korporacyjne EM
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI64', 'Akcje',      0.0),
('UNI64', 'Obligacje', 92.0),
('UNI64', 'Gotówka',    8.0);

-- ============================================================
-- GENERALI — fundusze konserwatywne i walutowe
-- ============================================================

-- UNI73 Generali Konserwatywny
-- Fundusz konserwatywny — głównie krótkoterminowe instrumenty dłużne i depozyty
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI73', 'Akcje',      0.0),
('UNI73', 'Obligacje', 80.0),
('UNI73', 'Gotówka',   20.0);

-- UNI75 Generali Surowców
-- Fundusz surowcowy — ekspozycja na surowce przez ETF i spółki
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI75', 'Akcje',     20.0),
('UNI75', 'Obligacje',  0.0),
('UNI75', 'Surowce',   70.0),
('UNI75', 'Gotówka',   10.0);

-- UNI25_E Generali Euro
-- Fundusz walutowy EUR — instrumenty dłużne denominowane w EUR
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI25_E', 'Akcje',      0.0),
('UNI25_E', 'Obligacje', 90.0),
('UNI25_E', 'Gotówka',   10.0);

-- UNI30_U Generali Dolar
-- Fundusz walutowy USD — instrumenty dłużne denominowane w USD
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('UNI30_U', 'Akcje',      0.0),
('UNI30_U', 'Obligacje', 90.0),
('UNI30_U', 'Gotówka',   10.0);

-- ============================================================
-- PZU — fundusze akcyjne
-- ============================================================

-- PZU01 PZU Akcji KRAKOWIAK
-- Fundusz akcji polskich — min. 66% akcje GPW, benchmark WIG
-- Typowa alokacja: akcje ~90%, gotówka ~10%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU01', 'Akcje',     90.0),
('PZU01', 'Obligacje',  0.0),
('PZU01', 'Gotówka',   10.0);

-- PZU02 PZU Akcji Polskich
-- Fundusz akcji polskich — min. 66% akcje GPW
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU02', 'Akcje',     90.0),
('PZU02', 'Obligacje',  0.0),
('PZU02', 'Gotówka',   10.0);

-- PZU10 PZU Akcji Małych i Średnich Spółek
-- Fundusz akcji MiŚ — min. 66% akcje małych i średnich spółek GPW
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU10', 'Akcje',     90.0),
('PZU10', 'Obligacje',  0.0),
('PZU10', 'Gotówka',   10.0);

-- PZU69 PZU Akcji Odpowiedzialnego Rozwoju
-- Fundusz akcji ESG — min. 66% akcje spółek spełniających kryteria ESG
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU69', 'Akcje',     90.0),
('PZU69', 'Obligacje',  0.0),
('PZU69', 'Gotówka',   10.0);

-- PZU11 PZU Globalny Akcji Medycznych
-- Fundusz akcji sektorowych — spółki medyczne i farmaceutyczne globalnie
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU11', 'Akcje',     90.0),
('PZU11', 'Obligacje',  0.0),
('PZU11', 'Gotówka',   10.0);

-- ============================================================
-- PZU — fundusze mieszane
-- ============================================================

-- PZU08 PZU Zrównoważony
-- Benchmark 50% WIG + 50% obligacje — akcje 40-60%
-- Typowa alokacja: akcje ~50%, obligacje ~46%, gotówka ~4%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU08', 'Akcje',     50.0),
('PZU08', 'Obligacje', 46.0),
('PZU08', 'Gotówka',    4.0);

-- PZU05 PZU Stabilnego Wzrostu Mazurek
-- Źródło: funduszowe.pl — akcje ~23% (benchmark 30% WIG + 70% obligacje)
-- Typowa alokacja: akcje ~23%, obligacje ~74%, gotówka ~3%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU05', 'Akcje',     23.0),
('PZU05', 'Obligacje', 74.0),
('PZU05', 'Gotówka',    3.0);

-- PZU13 PZU Aktywny Globalny
-- Fundusz mieszany globalny — aktywna alokacja między akcje i obligacje globalne
-- Typowa alokacja: akcje ~50%, obligacje ~45%, gotówka ~5%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU13', 'Akcje',     50.0),
('PZU13', 'Obligacje', 45.0),
('PZU13', 'Gotówka',    5.0);

-- ============================================================
-- PZU — fundusze dłużne
-- ============================================================

-- PZU14 PZU Dłużny Rynków Wschodzących
-- Fundusz obligacji emerging markets — obligacje rządowe i korporacyjne EM
-- Typowa alokacja: obligacje ~92%, gotówka ~8%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU14', 'Akcje',      0.0),
('PZU14', 'Obligacje', 92.0),
('PZU14', 'Gotówka',    8.0);

-- PZU96 PZU Dłużny Korporacyjny
-- Fundusz obligacji korporacyjnych — głównie polskie obligacje korporacyjne
-- Typowa alokacja: obligacje ~93%, gotówka ~7%
INSERT OR REPLACE INTO fund_allocation (fund_code, category, percentage) VALUES
('PZU96', 'Akcje',      0.0),
('PZU96', 'Obligacje', 93.0),
('PZU96', 'Gotówka',    7.0);

-- ============================================================
-- Tabela powiadomień o cenach
-- ============================================================
CREATE TABLE IF NOT EXISTS price_alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL DEFAULT 'default',
    fund_code       TEXT NOT NULL,
    alert_type      TEXT NOT NULL CHECK (alert_type IN ('BELOW', 'ABOVE', 'DRAWBACK')),
    threshold_price REAL,
    drawback_percent REAL,
    email           TEXT NOT NULL,
    is_active       INTEGER DEFAULT 1,
    triggered_at    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (fund_code) REFERENCES funds (code)
);