# Web-App: KI-Barrierefreiheits-Prüfer
# Streamlit-basierte Oberfläche für BITV 2.0 / WCAG 2.1 Prüfungen

import streamlit as st
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Projekt-Root zum Pfad hinzufügen
PROJ_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJ_ROOT))

from scanner.page_scanner import PageScanner
from scanner.wcag_rules import WCAGRuleEngine
from processor.ai_provider import AIProvider
from reporter.html_reporter import HTMLReporter
from reporter.pdf_reporter import PDFReporter
from database.db_manager import DatabaseManager

# --- Seiten-Konfiguration ---
st.set_page_config(
    page_title="KI-Barrierefreiheits-Prüfer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Datenbank initialisieren ---
DB_PATH = os.environ.get("DB_PATH", str(PROJ_ROOT / "data" / "barrierefreiheit.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = DatabaseManager(DB_PATH)

# --- Hilfsfunktionen ---

def ampel_bewertung(score):
    """Ampel-System: Grün/Gelb/Rot basierend auf Konformitäts-Prozentsatz."""
    if score >= 90:
        return "🟢 Konform", "#2e7d32"
    elif score >= 60:
        return "🟡 Teilweise konform", "#f9a825"
    else:
        return "🔴 Nicht konform", "#c62828"


def init_ai_provider():
    """AI-Provider aus Einstellungen initialisieren."""
    settings = db.get_settings()
    provider_type = settings.get("ai_provider", "ollama")
    model = settings.get("ai_model", "llama3")
    api_key = settings.get("claude_api_key", "")
    base_url = settings.get("ollama_url", "http://localhost:11434")
    return AIProvider(provider=provider_type, model=model, api_key=api_key, base_url=base_url)


# --- Sidebar ---
with st.sidebar:
    st.title("🏛️ BF-Prüfer")
    st.caption("BITV 2.0 / WCAG 2.1")
    
    page = st.radio(
        "Navigation",
        ["🏠 Neue Prüfung", "📊 Ergebnisse", "📄 Report erstellen", "📁 Vergangene Prüfungen", "⚙️ Einstellungen"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.caption(f"v1.0.0 | {datetime.now().year}")


# --- Seite: Neue Prüfung ---
if page == "🏠 Neue Prüfung":
    st.header("🏠 Neue Barrierefreiheits-Prüfung")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url_input = st.text_input(
            "URL der zu prüfenden Webseite",
            placeholder="https://www.beispiel-deutschland.de",
            help="Geben Sie die URL der Behörden-Webseite ein"
        )
        
        additional_urls = st.text_area(
            "Weitere URLs (eine pro Zeile, optional)",
            placeholder="https://www.beispiel.de/kontakt\nhttps://www.beispiel.de/formulare",
            height=100
        )
    
    with col2:
        pruefung_name = st.text_input("Prüfungsname", value=f"Prüfung {datetime.now().strftime('%d.%m.%Y')}")
        pruefer_name = st.text_input("Prüfer/in", placeholder="Name eingeben")
        depth = st.selectbox("Prüftiefe", ["Standard (WCAG AA)", "Erweitert (inkl. AAA-Hinweise)", "Schnellcheck"])
        use_ai = st.checkbox("KI-Korrekturvorschläge aktivieren", value=True)
    
    st.divider()
    
    if st.button("🔍 Prüfung starten", type="primary", use_container_width=True):
        if not url_input:
            st.error("Bitte geben Sie eine URL ein.")
        else:
            urls = [url_input.strip()] + [u.strip() for u in additional_urls.strip().split("\n") if u.strip()]
            
            # Prüfung in DB anlegen
            scan_id = db.create_scan(
                name=pruefung_name,
                url=url_input,
                pruefer=pruefer_name,
                depth=depth
            )
            
            progress_container = st.container()
            results_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0, text="Prüfung wird durchgeführt...")
                
                all_violations = []
                total = len(urls)
                
                for i, url in enumerate(urls):
                    try:
                        progress_bar.progress(
                            int((i / total) * 100),
                            text=f"Scanne {url} ({i+1}/{total})..."
                        )
                        
                        scanner = PageScanner(url)
                        scanner.fetch_page()
                        elements = scanner.extract_elements()
                        
                        rule_engine = WCAGRuleEngine(elements, url)
                        violations = rule_engine.run_all_checks()
                        
                        # Seite in DB speichern
                        page_id = db.create_page(
                            scan_id=scan_id,
                            url=url,
                            title=scanner.title or url,
                            status_code=scanner.status_code
                        )
                        
                        # Verstöße speichern
                        for v in violations:
                            violation_id = db.create_violation(
                                page_id=page_id,
                                criterion=v.get("criterion", ""),
                                name=v.get("name", ""),
                                level=v.get("level", ""),
                                severity=v.get("severity", "mittel"),
                                element=v.get("element", ""),
                                description=v.get("description", ""),
                                html_snippet=v.get("html_snippet", "")
                            )
                            
                            # KI-Vorschläge
                            if use_ai:
                                try:
                                    ai = init_ai_provider()
                                    suggestion = ai.suggest_fix(
                                        criterion=v.get("criterion", ""),
                                        element=v.get("element", ""),
                                        html_snippet=v.get("html_snippet", ""),
                                        description=v.get("description", "")
                                    )
                                    db.create_suggestion(
                                        violation_id=violation_id,
                                        suggestion_text=suggestion.get("suggestion", ""),
                                        fix_code=suggestion.get("fix_code", ""),
                                        confidence=suggestion.get("confidence", 0.5)
                                    )
                                except Exception as e:
                                    st.warning(f"KI-Vorschlag fehlgeschlagen: {e}")
                            
                            all_violations.append({**v, "url": url})
                        
                    except Exception as e:
                        st.error(f"Fehler bei {url}: {e}")
                        db.create_page(scan_id=scan_id, url=url, title=url, status_code=0, error=str(e))
                
                progress_bar.progress(100, text="Prüfung abgeschlossen!")
            
            # Ergebnisse anzeigen
            with results_container:
                st.divider()
                st.subheader("📋 Ergebnisse")
                
                total_checks = len(urls)
                pages_with_issues = len(set(v["url"] for v in all_violations))
                
                if not all_violations:
                    st.success("🎉 Keine Verstöße gefunden! Die Seite entspricht den geprüften Kriterien.")
                else:
                    # Zusammenfassung
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Seiten geprüft", total_checks)
                    with col_b:
                        st.metric("Seiten mit Mängeln", pages_with_issues)
                    with col_c:
                        st.metric("Verstöße gesamt", len(all_violations))
                    
                    # Schweregrad-Verteilung
                    schwer = [v for v in all_violations if v.get("severity") == "hoch"]
                    mittel = [v for v in all_violations if v.get("severity") == "mittel"]
                    niedrig = [v for v in all_violations if v.get("severity") == "niedrig"]
                    
                    col_s, col_m, col_n = st.columns(3)
                    with col_s:
                        st.metric("🔴 Hoch", len(schwer))
                    with col_m:
                        st.metric("🟡 Mittel", len(mittel))
                    with col_n:
                        st.metric("🔵 Niedrig", len(niedrig))
                    
                    # Detail-Tabelle
                    st.subheader("Verstöße im Detail")
                    for v in all_violations:
                        severity_emoji = {"hoch": "🔴", "mittel": "🟡", "niedrig": "🔵"}.get(v.get("severity", "mittel"), "⚪")
                        with st.expander(f"{severity_emoji} {v.get('criterion', '')} – {v.get('name', '')} ({v.get('url', '')})"):
                            st.write(f"**Schweregrad:** {v.get('severity', 'mittel')}")
                            st.write(f"**Level:** {v.get('level', 'A')}")
                            st.write(f"**Element:** `{v.get('element', '')}`")
                            st.write(f"**Beschreibung:** {v.get('description', '')}")
                            if v.get("html_snippet"):
                                st.code(v.get("html_snippet", ""), language="html")


# --- Seite: Ergebnisse ---
elif page == "📊 Ergebnisse":
    st.header("📊 Letzte Ergebnisse")
    
    scans = db.get_scans(limit=10)
    
    if not scans:
        st.info("Noch keine Prüfungen durchgeführt.")
    else:
        for scan in scans:
            pages = db.get_pages_for_scan(scan["id"])
            total_violations = sum(db.count_violations_for_page(p["id"]) for p in pages)
            total_pages = len(pages)
            
            # Konformitäts-Score berechnen
            if total_pages > 0:
                score = max(0, 100 - (total_violations * 5))
            else:
                score = 0
            
            label, color = ampel_bewertung(score)
            
            with st.expander(f"{'📊' if total_violations > 0 else '✅'} {scan['name']} – {scan['created_at']} | {label}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Seiten", total_pages)
                col2.metric("Verstöße", total_violations)
                col3.metric("Bewertung", f"{score}%")
                
                if pages:
                    for p in pages:
                        violations = db.get_violations_for_page(p["id"])
                        if violations:
                            st.write(f"📄 [{p['url']}]({p['url']}) – {len(violations)} Verstöße")
                            for v in violations:
                                suggestions = db.get_suggestions_for_violation(v["id"])
                                sev = v.get("severity", "mittel")
                                st.markdown(f"  - **{v['criterion']}** {v['name']} ({sev})")
                                if suggestions:
                                    for s in suggestions:
                                        st.markdown(f"    - 💡 *KI-Vorschlag:* {s['suggestion_text'][:200]}...")
                                        if s.get("fix_code"):
                                            st.code(s["fix_code"], language="html")


# --- Seite: Report erstellen ---
elif page == "📄 Report erstellen":
    st.header("📄 Barrierefreiheits-Report erstellen")
    
    scans = db.get_scans(limit=50)
    
    if not scans:
        st.info("Keine Prüfungen verfügbar. Führen Sie zuerst eine Prüfung durch.")
    else:
        selected_scan = st.selectbox(
            "Prüfung auswählen",
            options=scans,
            format_func=lambda s: f"{s['name']} ({s['created_at']})"
        )
        
        if selected_scan:
            scan_id = selected_scan["id"]
            pages = db.get_pages_for_scan(scan_id)
            all_data = []
            
            for p in pages:
                violations = db.get_violations_for_page(p["id"])
                for v in violations:
                    suggestions = db.get_suggestions_for_violation(v["id"])
                    all_data.append({
                        "page": p,
                        "violation": v,
                        "suggestions": suggestions
                    })
            
            # Vorschau
            total_v = len(all_data)
            score = max(0, 100 - (total_v * 5))
            label, color = ampel_bewertung(score)
            
            st.markdown(f"**Zusammenfassung:** {len(pages)} Seiten, {total_v} Verstöße, Bewertung: {label}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 HTML-Report generieren", use_container_width=True):
                    reporter = HTMLReporter()
                    report_path = reporter.generate(
                        scan=selected_scan,
                        pages=pages,
                        violations_data=all_data,
                        score=score,
                        label=label
                    )
                    st.success(f"Report erstellt: {report_path}")
                    with open(report_path, "r", encoding="utf-8") as f:
                        st.download_button(
                            "⬇️ Herunterladen",
                            f.read(),
                            file_name=f"bf-report-{selected_scan['name']}.html",
                            mime="text/html"
                        )
            
            with col2:
                if st.button("📑 PDF-Report generieren", use_container_width=True):
                    reporter = PDFReporter()
                    try:
                        report_path = reporter.generate(
                            scan=selected_scan,
                            pages=pages,
                            violations_data=all_data,
                            score=score,
                            label=label
                        )
                        st.success(f"PDF erstellt: {report_path}")
                        with open(report_path, "rb") as f:
                            st.download_button(
                                "⬇️ Herunterladen",
                                f.read(),
                                file_name=f"bf-report-{selected_scan['name']}.pdf",
                                mime="application/pdf"
                            )
                    except ImportError:
                        st.error("WeasyPrint nicht installiert. Führen Sie 'pip install weasyprint' aus.")


# --- Seite: Vergangene Prüfungen ---
elif page == "📁 Vergangene Prüfungen":
    st.header("📁 Vergangene Prüfungen")
    
    scans = db.get_scans(limit=100)
    
    if not scans:
        st.info("Noch keine Prüfungen vorhanden.")
    else:
        for scan in scans:
            pages = db.get_pages_for_scan(scan["id"])
            total_v = sum(db.count_violations_for_page(p["id"]) for p in pages)
            score = max(0, 100 - (total_v * 5)) if pages else 0
            label, _ = ampel_bewertung(score)
            
            with st.expander(f"{scan['name']} | {scan['created_at']} | {label}"):
                st.write(f"**URL:** {scan['url']}")
                st.write(f"**Prüfer:** {scan.get('pruefer', '–')}")
                st.write(f"**Seiten:** {len(pages)} | **Verstöße:** {total_v} | **Score:** {score}%")
                
                if st.button("🗑️ Löschen", key=f"del_{scan['id']}"):
                    db.delete_scan(scan["id"])
                    st.rerun()


# --- Seite: Einstellungen ---
elif page == "⚙️ Einstellungen":
    st.header("⚙️ Einstellungen")
    
    settings = db.get_settings()
    
    st.subheader("🤖 KI-Provider")
    
    provider = st.selectbox(
        "KI-Provider",
        ["ollama", "claude"],
        index=0 if settings.get("ai_provider", "ollama") == "ollama" else 1
    )
    
    if provider == "ollama":
        st.caption("Ollama: Lokale KI, keine Daten verlassen Ihren Server. DSGVO-konform.")
        ollama_url = st.text_input("Ollama URL", value=settings.get("ollama_url", "http://localhost:11434"))
        ollama_model = st.text_input("Ollama Modell", value=settings.get("ai_model", "llama3"))
        claude_key = settings.get("claude_api_key", "")
    else:
        st.caption("Claude API: Externe API-Anfrage. Prüfen Sie Ihren Auftragsverarbeitungsvertrag.")
        claude_key = st.text_input("Claude API Key", value=settings.get("claude_api_key", ""), type="password")
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        ollama_model = settings.get("ai_model", "llama3")
    
    st.subheader("📋 Allgemeine Einstellungen")
    report_dir = st.text_input("Report-Verzeichnis", value=settings.get("report_dir", str(PROJ_ROOT / "reports")))
    
    if st.button("💾 Einstellungen speichern", type="primary"):
        db.save_settings({
            "ai_provider": provider,
            "ollama_url": ollama_url,
            "ai_model": ollama_model,
            "claude_api_key": claude_key,
            "report_dir": report_dir
        })
        st.success("Einstellungen gespeichert!")
    
    st.divider()
    st.subheader("⚠️ Warnhinweis")
    st.warning(
        "KI-generierte Vorschläge können halluzinieren (falsche Informationen erzeugen). "
        "Alle KI-Ergebnisse sollten von einer qualifizierten Person überprüft werden, "
        "bevor sie in der Praxis umgesetzt werden."
    )
