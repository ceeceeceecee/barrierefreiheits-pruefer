"""
html_reporter.py – Generiert professionelle HTML-Reports
Behördengeeignet, druckoptimiert, barrierefrei.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape


class HTMLReporter:
    """Generiert HTML-Reports für Barrierefreiheitsprüfungen."""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.template_dir = template_dir
        self.output_dir = os.environ.get("REPORT_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports"))
        os.makedirs(self.output_dir, exist_ok=True)

        # Jinja2 Umgebung
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate(
        self,
        scan: Dict,
        pages: List[Dict],
        violations_data: List[Dict],
        score: float,
        label: str,
        output_path: str = None
    ) -> str:
        """
        Generiert den HTML-Report.

        Args:
            scan: Scan-Datensatz aus der DB
            pages: Liste der geprüften Seiten
            violations_data: Liste mit {page, violation, suggestions}
            score: Konformitäts-Score (0-100)
            label: Ampel-Label
            output_path: Optionaler Pfad für die Ausgabe

        Returns:
            Pfad zur generierten HTML-Datei
        """
        # Verstöße nach Schweregrad gruppieren
        hoch = [v for v in violations_data if v["violation"].get("severity") == "hoch"]
        mittel = [v for v in violations_data if v["violation"].get("severity") == "mittel"]
        niedrig = [v for v in violations_data if v["violation"].get("severity") == "niedrig"]

        # Verstöße pro Seite
        violations_per_page = {}
        for v in violations_data:
            page_url = v["page"]["url"]
            if page_url not in violations_per_page:
                violations_per_page[page_url] = []
            violations_per_page[page_url].append(v)

        # Verstöße pro WCAG-Kriterium
        violations_per_criterion = {}
        for v in violations_data:
            crit = v["violation"].get("criterion", "unbekannt")
            if crit not in violations_per_criterion:
                violations_per_criterion[crit] = {
                    "name": v["violation"].get("name", ""),
                    "level": v["violation"].get("level", ""),
                    "count": 0,
                    "violations": []
                }
            violations_per_criterion[crit]["count"] += 1
            violations_per_criterion[crit]["violations"].append(v)

        # Template rendern
        template = self.env.get_template("report.html.j2")

        html_content = template.render(
            scan=scan,
            pages=pages,
            violations_data=violations_data,
            score=score,
            label=label,
            hoch=hoch,
            mittel=mittel,
            niedrig=niedrig,
            violations_per_page=violations_per_page,
            violations_per_criterion=violations_per_criterion,
            generated_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
            version="1.0.0"
        )

        # Datei speichern
        if output_path is None:
            safe_name = scan.get("name", "report").replace(" ", "-").replace("/", "-")
            output_path = os.path.join(self.output_dir, f"{safe_name}-{datetime.now().strftime('%Y%m%d-%H%M')}.html")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
