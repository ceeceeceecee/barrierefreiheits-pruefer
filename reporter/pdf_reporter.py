"""
pdf_reporter.py – Konvertiert HTML-Reports in PDF (WeasyPrint)
"""

import os
from datetime import datetime
from typing import Dict, List, Any


class PDFReporter:
    """Generiert PDF-Reports aus HTML-Vorlagen."""

    def __init__(self):
        self.output_dir = os.environ.get(
            "REPORT_DIR",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
        )
        os.makedirs(self.output_dir, exist_ok=True)

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
        Generiert einen PDF-Report.

        Args:
            scan: Scan-Datensatz
            pages: Geprüfte Seiten
            violations_data: Verstöße mit Vorschlägen
            score: Konformitäts-Score
            label: Ampel-Label
            output_path: Optionaler Ausgabepfad

        Returns:
            Pfad zur generierten PDF-Datei
        """
        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError(
                "WeasyPrint ist nicht installiert. "
                "Installieren Sie es mit: pip install weasyprint"
            )

        # Zuerst HTML generieren
        from reporter.html_reporter import HTMLReporter
        html_reporter = HTMLReporter()
        html_path = html_reporter.generate(
            scan=scan,
            pages=pages,
            violations_data=violations_data,
            score=score,
            label=label
        )

        # HTML zu PDF konvertieren
        if output_path is None:
            safe_name = scan.get("name", "report").replace(" ", "-").replace("/", "-")
            output_path = os.path.join(
                self.output_dir,
                f"{safe_name}-{datetime.now().strftime('%Y%m%d-%H%M')}.pdf"
            )

        HTML(filename=html_path).write_pdf(output_path)
        return output_path
