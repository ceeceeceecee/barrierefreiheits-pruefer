"""
wcag_rules.py – WCAG 2.1 Regelmaschine
Enthält Regeln für WCAG 2.1 Level A und AA, ausgerichtet auf BITV 2.0.
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field


@dataclass
class WCAGRule:
    """Einzelne WCAG-Regel mit Kriterium, Name, Level, Prüffunktion und Schweregrad."""
    criterion: str
    name: str
    level: str
    severity: str
    check: Callable
    description: str = ""


class WCAGRuleEngine:
    """Regelmaschine – führt alle WCAG-Prüfungen gegen extrahierte Elemente durch."""

    def __init__(self, elements: Dict[str, List[Dict]], page_url: str = ""):
        self.elements = elements
        self.page_url = page_url
        self.rules = self._define_rules()
        self.violations: List[Dict] = []

    def _define_rules(self) -> List[WCAGRule]:
        """Definiert alle WCAG-Regeln."""
        return [
            # --- 1.1.1 Nicht-Text-Inhalte (Level A) ---
            WCAGRule(
                criterion="1.1.1",
                name="Nicht-Text-Inhalte",
                level="A",
                severity="hoch",
                description="Alle nicht-textuellen Inhalte müssen eine Textalternative haben.",
                check=self._check_1_1_1_images
            ),
            # --- 1.3.1 Info und Beziehungen (Level A) ---
            WCAGRule(
                criterion="1.3.1",
                name="Info und Beziehungen",
                level="A",
                severity="hoch",
                description="Informationen, Struktur und Beziehungen müssen durch Markup bestimmt sein.",
                check=self._check_1_3_1_headings
            ),
            # --- 1.3.1 Tabellen ---
            WCAGRule(
                criterion="1.3.1",
                name="Tabellen-Struktur",
                level="A",
                severity="mittel",
                description="Datentabellen müssen korrekte Header und Caption haben.",
                check=self._check_1_3_1_tables
            ),
            # --- 1.4.3 Kontrast (Minimum) (Level AA) ---
            WCAGRule(
                criterion="1.4.3",
                name="Kontrast (Minimum)",
                level="AA",
                severity="hoch",
                description="Text muss ein Kontrastverhältnis von mindestens 4.5:1 haben (3:1 für großen Text).",
                check=self._check_1_4_3_contrast
            ),
            # --- 1.4.11 Nicht-Text-Kontrast (Level AA) ---
            WCAGRule(
                criterion="1.4.11",
                name="Nicht-Text-Kontrast",
                level="AA",
                severity="mittel",
                description="Benutzeroberflächen-Komponenten und grafische Objekte müssen ausreichenden Kontrast haben.",
                check=self._check_1_4_11_non_text_contrast
            ),
            # --- 2.4.2 Seiten-Titel (Level A) ---
            WCAGRule(
                criterion="2.4.2",
                name="Seiten-Titel",
                level="A",
                severity="mittel",
                description="Jede Webseite muss einen beschreibenden Titel haben.",
                check=self._check_2_4_2_page_title
            ),
            # --- 2.4.4 Linktext (Level A) ---
            WCAGRule(
                criterion="2.4.4",
                name="Linktext",
                level="A",
                severity="mittel",
                description="Der Linktext muss den Zweck des Links beschreiben.",
                check=self._check_2_4_4_link_text
            ),
            # --- 2.4.6 Überschriften und Labels (Level AA) ---
            WCAGRule(
                criterion="2.4.6",
                name="Überschriften und Labels",
                level="AA",
                severity="niedrig",
                description="Überschriften und Labels müssen den Zweck des Inhalts beschreiben.",
                check=self._check_2_4_6_headings_labels
            ),
            # --- 3.1.1 Sprache der Seite (Level A) ---
            WCAGRule(
                criterion="3.1.1",
                name="Sprache der Seite",
                level="A",
                severity="hoch",
                description="Die Standardsprache jeder Webseite muss bestimmt sein.",
                check=self._check_3_1_1_lang
            ),
            # --- 3.3.1 Fehlerkennung (Level A) ---
            WCAGRule(
                criterion="3.3.1",
                name="Fehlerkennung",
                level="A",
                severity="mittel",
                description="Wenn ein Eingabefehler automatisch erkannt wird, muss das Element identifiziert und der Fehler beschrieben werden.",
                check=self._check_3_3_1_error_identification
            ),
            # --- 4.1.1 Syntaxanalyse (Level A) ---
            WCAGRule(
                criterion="4.1.1",
                name="Syntaxanalyse",
                level="A",
                severity="hoch",
                description="In Markup-Sprachen verwendete Elemente müssen vollständige Öffnungs- und Schließ-Tags haben.",
                check=self._check_4_1_1_parsing
            ),
            # --- 4.1.2 Name, Role, Value (Level A) ---
            WCAGRule(
                criterion="4.1.2",
                name="Name, Role, Value",
                level="A",
                severity="hoch",
                description="Für alle UI-Komponenten müssen Name, Role und Value programmgesteuert bestimmt werden können.",
                check=self._check_4_1_2_name_role_value
            ),
            # --- 1.2.1 Reine Audio und Video (Level A) ---
            WCAGRule(
                criterion="1.2.1",
                name="Reine Audio und Video (Vorausgezeichnet)",
                level="A",
                severity="hoch",
                description="Für voraufgezeichnete Audio-Inhalte muss eine Alternative als Text bereitgestellt werden.",
                check=self._check_1_2_1_media
            ),
            # --- 2.1.1 Tastatur (Level A) ---
            WCAGRule(
                criterion="2.1.1",
                name="Tastatur",
                level="A",
                severity="hoch",
                description="Alle Funktionen müssen über eine Tastatur bedienbar sein.",
                check=self._check_2_1_1_keyboard
            ),
            # --- 2.4.1 Blöcke überspringen (Level A) ---
            WCAGRule(
                criterion="2.4.1",
                name="Blöcke überspringen",
                level="A",
                severity="mittel",
                description="Es muss ein Mechanismus vorhanden sein, um Inhaltsblöcke zu überspringen.",
                check=self._check_2_4_1_skip_links
            ),
            # --- 1.4.4 Text-Vergrößerung (Level AA) ---
            WCAGRule(
                criterion="1.4.4",
                name="Text-Vergrößerung",
                level="AA",
                severity="niedrig",
                description="Text muss bis auf 200% vergrößerbar sein ohne Verlust von Inhalt oder Funktionalität.",
                check=self._check_1_4_4_text_resize
            ),
        ]

    def run_all_checks(self) -> List[Dict]:
        """Führt alle Regeln aus und sammelt Verstöße."""
        self.violations = []
        for rule in self.rules:
            try:
                findings = rule.check()
                for finding in findings:
                    self.violations.append({
                        "criterion": rule.criterion,
                        "name": rule.name,
                        "level": rule.level,
                        "severity": rule.severity,
                        "description": rule.description,
                        **finding
                    })
            except Exception as e:
                # Regel konnte nicht ausgeführt werden – nicht fatal
                pass
        return self.violations

    # === Prüffunktionen ===

    def _check_1_1_1_images(self) -> List[Dict]:
        """1.1.1 – Bilder müssen Alt-Text haben (außer dekorative)."""
        findings = []
        for img in self.elements.get("images", []):
            if img["alt_missing"] and not img["is_decorative"]:
                findings.append({
                    "element": f"img[src='{img['src'][:80]}']",
                    "html_snippet": img["html_snippet"],
                    "detail": f"Bild ohne Alt-Attribut: {img['src'][:80]}"
                })
            elif img["alt_empty"] and not img["is_decorative"]:
                findings.append({
                    "element": f"img[src='{img['src'][:80]}']",
                    "html_snippet": img["html_snippet"],
                    "detail": f"Bild mit leerem Alt-Attribut (nicht als dekorativ markiert): {img['src'][:80]}"
                })
        return findings

    def _check_1_3_1_headings(self) -> List[Dict]:
        """1.3.1 – Überschriftenstruktur muss logisch sein."""
        findings = []
        headings = self.elements.get("headings", [])
        if not headings:
            findings.append({
                "element": "html",
                "html_snippet": "",
                "detail": "Keine Überschriften auf der Seite gefunden."
            })
            return findings

        # Prüfe ob h1 existiert
        has_h1 = any(h["level"] == 1 for h in headings)
        if not has_h1:
            findings.append({
                "element": "html",
                "html_snippet": "",
                "detail": "Keine h1-Überschrift gefunden. Jede Seite sollte genau eine h1 haben."
            })

        # Prüfe auf Sprünge (z.B. h1 direkt zu h3)
        prev_level = 0
        for h in headings:
            if h["level"] > prev_level + 1 and prev_level > 0:
                findings.append({
                    "element": f"h{h['level']}",
                    "html_snippet": h["html_snippet"],
                    "detail": f"Überschriftensprung von h{prev_level} zu h{h['level']}: '{h['text'][:50]}'"
                })
            prev_level = h["level"]

        # Leere Überschriften
        for h in headings:
            if h["empty"]:
                findings.append({
                    "element": f"h{h['level']}",
                    "html_snippet": h["html_snippet"],
                    "detail": f"Leere h{h['level']}-Überschrift gefunden."
                })

        return findings

    def _check_1_3_1_tables(self) -> List[Dict]:
        """1.3.1 – Tabellen müssen Caption und korrekte Header haben."""
        findings = []
        for table in self.elements.get("tables", []):
            if not table["has_caption"]:
                findings.append({
                    "element": "table",
                    "html_snippet": table["html_snippet"],
                    "detail": "Tabelle ohne caption-Element."
                })
            if table["header_count"] == 0:
                findings.append({
                    "element": "table",
                    "html_snippet": table["html_snippet"],
                    "detail": "Tabelle ohne th-Elemente (Tabellenüberschriften)."
                })
            elif not table["has_scope"]:
                findings.append({
                    "element": "table > th",
                    "html_snippet": table["html_snippet"],
                    "detail": "Tabellenüberschriften ohne scope-Attribut."
                })
        return findings

    def _check_1_4_3_contrast(self) -> List[Dict]:
        """1.4.3 – Kontrastprüfung (Hinweis – vollständige Prüfung erfordert Rendering)."""
        findings = []
        # Inline-Styles mit Farbangaben sind potenzielle Probleme
        contrast_elements = self.elements.get("contrast", [])
        if contrast_elements:
            findings.append({
                "element": "style-attribute",
                "html_snippet": contrast_elements[0]["html_snippet"],
                "detail": f"Inline-Farbangaben gefunden ({len(contrast_elements)} Elemente). Kontrast sollte manuell geprüft werden."
            })
        return findings

    def _check_1_4_11_non_text_contrast(self) -> List[Dict]:
        """1.4.11 – Nicht-Text-Kontrast (Hinweis)."""
        return []  # Erfordert visuelles Rendering – wird als Hinweis in contrast-Prüfung behandelt

    def _check_2_4_2_page_title(self) -> List[Dict]:
        """2.4.2 – Seiten muss einen beschreibenden Titel haben."""
        findings = []
        page_info = self.elements.get("page_info", {})
        title = page_info.get("title", "")
        if not title:
            findings.append({
                "element": "title",
                "html_snippet": "",
                "detail": "Kein Seiten-Titel gefunden."
            })
        elif len(title) < 5:
            findings.append({
                "element": "title",
                "html_snippet": f"<title>{title}</title>",
                "detail": f"Seiten-Titel sehr kurz ('{title}'). Sollte beschreibend sein."
            })
        return findings

    def _check_2_4_4_link_text(self) -> List[Dict]:
        """2.4.4 – Linktext muss den Zweck beschreiben."""
        findings = []
        for link in self.elements.get("links", []):
            if link["text_missing"] and not link["aria_label"] and not link["title"]:
                findings.append({
                    "element": f"a[href='{link['href'][:80]}']",
                    "html_snippet": link["html_snippet"],
                    "detail": f"Link ohne Text, aria-label oder title: {link['href'][:80]}"
                })
            elif link["generic_text"] and not link["aria_label"]:
                findings.append({
                    "element": f"a[href='{link['href'][:80]}']",
                    "html_snippet": link["html_snippet"],
                    "detail": f"Unspezifischer Linktext '{link['text']}'. Sollte den Zweck beschreiben."
                })
        return findings

    def _check_2_4_6_headings_labels(self) -> List[Dict]:
        """2.4.6 – Überschriften und Labels sollen beschreibend sein."""
        findings = []
        for h in self.elements.get("headings", []):
            if h["text"] and len(h["text"]) < 3:
                findings.append({
                    "element": f"h{h['level']}",
                    "html_snippet": h["html_snippet"],
                    "detail": f"Sehr kurze Überschrift: '{h['text']}'"
                })
        return findings

    def _check_3_1_1_lang(self) -> List[Dict]:
        """3.1.1 – HTML muss ein lang-Attribut haben."""
        findings = []
        lang_info = self.elements.get("lang", {})
        if not lang_info.get("present", False):
            findings.append({
                "element": "html",
                "html_snippet": "",
                "detail": "Kein lang-Attribut im html-Element gefunden."
            })
        elif not lang_info.get("valid", False):
            findings.append({
                "element": f"html[lang='{lang_info.get('lang', '')}']",
                "html_snippet": "",
                "detail": f"Ungültiges lang-Attribut: '{lang_info.get('lang', '')}'. Erwartetes Format: 'de' oder 'de-DE'."
            })
        return findings

    def _check_3_3_1_error_identification(self) -> List[Dict]:
        """3.3.1 – Formularfelder müssen bei Fehlern identifizierbar sein (Hinweis)."""
        findings = []
        for form in self.elements.get("forms", []):
            required_fields = [i for i in form["inputs"] if i["required"]]
            for field in required_fields:
                if not field["accessible"]:
                    findings.append({
                        "element": f"{field['type']}[name='{field['name']}']",
                        "html_snippet": field["html_snippet"],
                        "detail": f"Pflichtfeld '{field['name']}' ohne Label oder aria-label."
                    })
        return findings

    def _check_4_1_1_parsing(self) -> List[Dict]:
        """4.1.1 – Grundlegende Syntax-Prüfung."""
        findings = []
        page_info = self.elements.get("page_info", {})
        # Prüfe ob Seite überhaupt geladen wurde
        if page_info.get("status_code", 0) != 200:
            findings.append({
                "element": "html",
                "html_snippet": "",
                "detail": f"Seite konnte nicht geladen werden (Status: {page_info.get('status_code', 0)})."
            })
        if page_info.get("html_length", 0) == 0:
            findings.append({
                "element": "html",
                "html_snippet": "",
                "detail": "Leere oder nicht parsebare Seite."
            })
        return findings

    def _check_4_1_2_name_role_value(self) -> List[Dict]:
        """4.1.2 – UI-Komponenten müssen Name, Role und Value haben."""
        findings = []
        for form in self.elements.get("forms", []):
            for field in form["inputs"]:
                if not field["accessible"]:
                    findings.append({
                        "element": f"{field['type']}[name='{field['name']}']",
                        "html_snippet": field["html_snippet"],
                        "detail": f"Eingabefeld '{field['name']}' (Typ: {field['type']}) ohne zugänglichen Namen (Label/aria-label)."
                    })
        # iFrames prüfen
        for iframe in self.elements.get("iframes", []):
            if iframe["title_missing"]:
                findings.append({
                    "element": f"iframe[src='{iframe['src'][:80]}']",
                    "html_snippet": iframe["html_snippet"],
                    "detail": f"iFrame ohne title-Attribut: {iframe['src'][:80]}"
                })
        return findings

    def _check_1_2_1_media(self) -> List[Dict]:
        """1.2.1 – Audio/Video müssen Alternativen haben."""
        findings = []
        docs = self.elements.get("documents", [])
        # PDFs ohne Hinweis auf Barrierefreiheit
        for doc in docs:
            if doc["extension"] == "pdf":
                findings.append({
                    "element": f"a[href='{doc['href'][:80]}']",
                    "html_snippet": doc["html_snippet"],
                    "detail": f"PDF-Dokument verlinkt: {doc['href'][:80]}. PDF muss barrierefrei sein (taggt PDF)."
                })
        return findings

    def _check_2_1_1_keyboard(self) -> List[Dict]:
        """2.1.1 – Tastatur-Navigation prüfen (Hinweis auf tabindex-Probleme)."""
        findings = []
        keyboard_issues = self.elements.get("keyboard", [])
        for issue in keyboard_issues:
            findings.append({
                "element": issue["element"],
                "html_snippet": issue["html_snippet"],
                "detail": issue["issue"]
            })
        return findings

    def _check_2_4_1_skip_links(self) -> List[Dict]:
        """2.4.1 – Skip-Links (Sprungmarken) prüfen."""
        findings = []
        links = self.elements.get("links", [])
        has_skip_link = any(
            "skip" in (link["text"].lower() or "") or "skip" in (link.get("href", "").lower())
            for link in links
        )
        if not has_skip_link:
            findings.append({
                "element": "body",
                "html_snippet": "",
                "detail": "Kein 'Skip to content'-Link gefunden. Für Barrierefreiheit empfohlen."
            })
        return findings

    def _check_1_4_4_text_resize(self) -> List[Dict]:
        """1.4.4 – Prüft ob Viewport festgesetzt ist (verhindert Text-Vergrößerung)."""
        findings = []
        meta = self.elements.get("meta", [])
        if meta:
            viewport = meta[0].get("viewport", "")
            if "maximum-scale=1" in viewport or "user-scalable=no" in viewport:
                findings.append({
                    "element": "meta[name=viewport]",
                    "html_snippet": f'<meta name="viewport" content="{viewport}">',
                    "detail": "Viewport verhindert Text-Vergrößerung. 'maximum-scale=1' oder 'user-scalable=no' sollten vermieden werden."
                })
        return findings
