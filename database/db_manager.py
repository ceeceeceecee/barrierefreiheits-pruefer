"""
db_manager.py – Datenbank-Zugriff für den Barrierefreiheits-Prüfer
SQLite-basiert, DSGVO-konform (lokale Daten).
"""

import sqlite3
import os
from typing import Dict, List, Optional, Any
from datetime import datetime


class DatabaseManager:
    """CRUD-Operationen für alle Tabellen des Barrierefreiheits-Prüfers."""

    def __init__(self, db_path: str = "data/barrierefreiheit.db"):
        """
        Initialisiert die Datenbank-Verbindung.

        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Lädt das Schema und erstellt Tabellen falls nötig."""
        schema_path = os.path.join(
            os.path.dirname(__file__), "schema.sql"
        )
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                self.conn.executescript(f.read())
            self.conn.commit()

    # === Scans ===

    def create_scan(self, name: str, url: str, pruefer: str = "", depth: str = "Standard (WCAG AA)") -> int:
        """Erstellt einen neuen Scan-Eintrag."""
        cursor = self.conn.execute(
            "INSERT INTO scans (name, url, pruefer, depth, status) VALUES (?, ?, ?, ?, 'laufend')",
            (name, url, pruefer, depth)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_scans(self, limit: int = 50) -> List[Dict]:
        """Gibt die letzten Scans zurück."""
        cursor = self.conn.execute(
            "SELECT * FROM scans ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_scan(self, scan_id: int) -> Optional[Dict]:
        """Gibt einen einzelnen Scan zurück."""
        cursor = self.conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_scan(self, scan_id: int):
        """Löscht einen Scan und alle zugehörigen Daten."""
        self.conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
        self.conn.commit()

    def update_scan_status(self, scan_id: int, status: str):
        """Aktualisiert den Status eines Scans."""
        self.conn.execute(
            "UPDATE scans SET status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
            (status, scan_id)
        )
        self.conn.commit()

    # === Pages ===

    def create_page(
        self, scan_id: int, url: str, title: str = "",
        status_code: int = 0, error: str = ""
    ) -> int:
        """Erstellt einen neuen Seiten-Eintrag."""
        cursor = self.conn.execute(
            "INSERT INTO pages (scan_id, url, title, status_code, error) VALUES (?, ?, ?, ?, ?)",
            (scan_id, url, title, status_code, error)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_pages_for_scan(self, scan_id: int) -> List[Dict]:
        """Gibt alle Seiten eines Scans zurück."""
        cursor = self.conn.execute(
            "SELECT * FROM pages WHERE scan_id = ? ORDER BY id", (scan_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # === Violations ===

    def create_violation(
        self, page_id: int, criterion: str, name: str,
        level: str = "A", severity: str = "mittel",
        element: str = "", description: str = "", html_snippet: str = ""
    ) -> int:
        """Erstellt einen neuen Verstoß-Eintrag."""
        cursor = self.conn.execute(
            """INSERT INTO violations
               (page_id, criterion, name, level, severity, element, description, html_snippet)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (page_id, criterion, name, level, severity, element, description, html_snippet)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_violations_for_page(self, page_id: int) -> List[Dict]:
        """Gibt alle Verstöße einer Seite zurück."""
        cursor = self.conn.execute(
            "SELECT * FROM violations WHERE page_id = ? ORDER BY severity DESC, criterion",
            (page_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def count_violations_for_page(self, page_id: int) -> int:
        """Zählt Verstöße für eine Seite."""
        cursor = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM violations WHERE page_id = ?", (page_id,)
        )
        return cursor.fetchone()["cnt"]

    # === Suggestions ===

    def create_suggestion(
        self, violation_id: int, suggestion_text: str = "",
        fix_code: str = "", confidence: float = 0.5
    ) -> int:
        """Erstellt einen KI-Korrekturvorschlag."""
        cursor = self.conn.execute(
            """INSERT INTO suggestions
               (violation_id, suggestion_text, fix_code, confidence)
               VALUES (?, ?, ?, ?)""",
            (violation_id, suggestion_text, fix_code, confidence)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_suggestions_for_violation(self, violation_id: int) -> List[Dict]:
        """Gibt alle Vorschläge für einen Verstoß zurück."""
        cursor = self.conn.execute(
            "SELECT * FROM suggestions WHERE violation_id = ?", (violation_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # === Reports ===

    def create_report(self, scan_id: int, format: str, file_path: str) -> int:
        """Erstellt einen Report-Eintrag."""
        cursor = self.conn.execute(
            "INSERT INTO reports (scan_id, format, file_path) VALUES (?, ?, ?)",
            (scan_id, format, file_path)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_reports_for_scan(self, scan_id: int) -> List[Dict]:
        """Gibt alle Reports für einen Scan zurück."""
        cursor = self.conn.execute(
            "SELECT * FROM reports WHERE scan_id = ? ORDER BY created_at DESC", (scan_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # === Settings ===

    def get_settings(self) -> Dict[str, str]:
        """Gibt alle Einstellungen als Dict zurück."""
        cursor = self.conn.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in cursor.fetchall()}

    def save_settings(self, settings: Dict[str, str]):
        """Speichert Einstellungen (upsert)."""
        for key, value in settings.items():
            self.conn.execute(
                """INSERT INTO settings (key, value, updated_at)
                   VALUES (?, ?, datetime('now', 'localtime'))
                   ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now', 'localtime')""",
                (key, value, value)
            )
        self.conn.commit()

    def close(self):
        """Schließt die Datenbankverbindung."""
        self.conn.close()
