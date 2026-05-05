-- =====================================================
-- Schema für KI-Barrierefreiheits-Prüfer
-- Tabellen: scans, pages, violations, suggestions, reports, settings
-- =====================================================

-- Prüfungen (Scans)
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- Name der Prüfung
    url TEXT NOT NULL,                     -- Haupt-URL
    pruefer TEXT DEFAULT '',               -- Name der Prüferin/des Prüfers
    depth TEXT DEFAULT 'Standard (WCAG AA)', -- Prüftiefe
    status TEXT DEFAULT 'abgeschlossen',   -- Status: gestartet, laufend, abgeschlossen, fehlgeschlagen
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- Geprüfte Seiten
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    url TEXT NOT NULL,                     -- URL der Seite
    title TEXT DEFAULT '',                 -- Seitentitel
    status_code INTEGER DEFAULT 0,         -- HTTP-Statuscode
    error TEXT DEFAULT '',                 -- Fehlermeldung (falls vorhanden)
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

-- WCAG-Verstöße
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id INTEGER NOT NULL,
    criterion TEXT NOT NULL,               -- WCAG-Kriterium (z.B. '1.1.1')
    name TEXT NOT NULL,                    -- Name des Kriteriums
    level TEXT DEFAULT 'A',                -- Konformitätslevel (A, AA, AAA)
    severity TEXT DEFAULT 'mittel',        -- Schweregrad: hoch, mittel, niedrig
    element TEXT DEFAULT '',               -- Betroffenes HTML-Element
    description TEXT DEFAULT '',           -- Beschreibung des Verstoßes
    html_snippet TEXT DEFAULT '',          -- HTML-Ausschnitt
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
);

-- KI-Korrekturvorschläge
CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id INTEGER NOT NULL,
    suggestion_text TEXT DEFAULT '',       -- Textvorschlag der KI
    fix_code TEXT DEFAULT '',              -- HTML-Korrekturcode
    confidence REAL DEFAULT 0.5,           -- Konfidenz (0.0 - 1.0)
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (violation_id) REFERENCES violations(id) ON DELETE CASCADE
);

-- Generierte Reports
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    format TEXT NOT NULL,                  -- 'html' oder 'pdf'
    file_path TEXT NOT NULL,               -- Pfad zur Report-Datei
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

-- Einstellungen (Schlüssel-Wert)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- Standard-Einstellungen einfügen
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('ai_provider', 'ollama'),
    ('ai_model', 'llama3'),
    ('ollama_url', 'http://localhost:11434'),
    ('claude_api_key', ''),
    ('report_dir', './reports');

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_pages_scan ON pages(scan_id);
CREATE INDEX IF NOT EXISTS idx_violations_page ON violations(page_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_violation ON suggestions(violation_id);
CREATE INDEX IF NOT EXISTS idx_reports_scan ON reports(scan_id);
