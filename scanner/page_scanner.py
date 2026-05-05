"""
page_scanner.py – HTML-Parser & Seiten-Scanner
Ruft Webseiten ab, parst HTML, extrahiert Elemente für WCAG-Prüfung.
"""

import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import socket
from typing import Dict, List, Optional, Any


class PageScanner:
    """Scanner für einzelne Webseiten – ruft HTML ab und extrahiert prüfrelevante Elemente."""

    def __init__(self, url: str, timeout: int = 30, user_agent: str = None):
        self.url = url
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "Barrierefreiheits-Pruefer/1.0 (Behoerden-Scanner)"
        )
        self.soup: Optional[BeautifulSoup] = None
        self.html: str = ""
        self.status_code: int = 0
        self.title: str = ""
        self.robots_allowed: bool = True
        self.headers: Dict[str, str] = {}

    def fetch_page(self) -> bool:
        """Ruft die Webseite ab und parst das HTML."""
        # robots.txt prüfen
        self._check_robots()

        if not self.robots_allowed:
            return False

        try:
            response = requests.get(
                self.url,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                verify=True,
                allow_redirects=True
            )
            self.status_code = response.status_code
            self.headers = dict(response.headers)

            if response.status_code == 200:
                self.html = response.text
                self.soup = BeautifulSoup(self.html, "html.parser")

                # Titel extrahieren
                title_tag = self.soup.find("title")
                self.title = title_tag.get_text(strip=True) if title_tag else ""

                return True
            return False

        except requests.RequestException as e:
            raise RuntimeError(f"Fehler beim Abrufen von {self.url}: {e}")

    def _check_robots(self):
        """Prüft robots.txt ob das Scannen erlaubt ist."""
        try:
            parsed = urlparse(self.url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                # Einfache Prüfung – kein Disallow für unseren User-Agent
                for line in response.text.split("\n"):
                    if line.lower().startswith("disallow:"):
                        path = line.split(":", 1)[1].strip()
                        if path == "/" or path == "/*":
                            self.robots_allowed = False
                            return
        except Exception:
            # Bei Fehlern erlauben wir das Scannen
            self.robots_allowed = True

    def extract_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extrahiert alle für WCAG-Prüfung relevanten Elemente."""
        if not self.soup:
            return {}

        return {
            "images": self.check_images(),
            "headings": self.check_headings(),
            "links": self.check_links(),
            "forms": self.check_forms(),
            "lang": self.check_lang(),
            "documents": self.check_documents(),
            "meta": self._check_meta(),
            "tables": self._check_tables(),
            "iframes": self._check_iframes(),
            "page_info": {
                "url": self.url,
                "title": self.title,
                "status_code": self.status_code,
                "content_type": self.headers.get("content-type", ""),
                "html_length": len(self.html)
            }
        }

    def check_images(self) -> List[Dict[str, Any]]:
        """Prüft alle Bilder auf Alt-Attribute."""
        images = []
        for img in self.soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", None)
            role = img.get("role", "")
            aria_hidden = img.get("aria-hidden", "")

            # Decorative Bilder mit aria-hidden="true"
            is_decorative = aria_hidden.lower() == "true" or role == "presentation"

            images.append({
                "src": urljoin(self.url, src),
                "alt": alt,
                "alt_missing": alt is None,
                "alt_empty": alt is not None and alt.strip() == "",
                "is_decorative": is_decorative,
                "html_snippet": str(img)[:500],
                "tag": str(img.name)
            })
        return images

    def check_headings(self) -> List[Dict[str, Any]]:
        """Prüft Überschriftenstruktur."""
        headings = []
        for level in range(1, 7):
            for h in self.soup.find_all(f"h{level}"):
                text = h.get_text(strip=True)
                headings.append({
                    "level": level,
                    "text": text,
                    "empty": len(text) == 0,
                    "html_snippet": str(h)[:300],
                    "id": h.get("id", "")
                })
        return headings

    def check_links(self) -> List[Dict[str, Any]]:
        """Prüft Links auf barrierefreie Linktexte."""
        links = []
        for a in self.soup.find_all("a", href=True):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            title = a.get("title", "")
            aria_label = a.get("aria-label", "")
            target = a.get("target", "")
            has_text = len(text) > 0
            has_title = len(title.strip()) > 0
            has_aria_label = len(aria_label.strip()) > 0

            # Prüfe auf "hier klicken"-Muster
            generic_text = any(
                kw in text.lower()
                for kw in ["hier", "klick", "mehr", "weiter", "hier klicken", "klicken sie"]
            )

            links.append({
                "href": urljoin(self.url, href),
                "text": text,
                "title": title,
                "aria_label": aria_label,
                "target": target,
                "text_missing": not has_text,
                "generic_text": generic_text,
                "accessible": has_text or has_title or has_aria_label,
                "html_snippet": str(a)[:300],
                "is_external": href.startswith("http") and urlparse(href).netloc != urlparse(self.url).netloc
            })
        return links

    def check_contrast(self) -> List[Dict[str, Any]]:
        """Grundlegende Kontrastprüfung – extrahiert Inline-Styles mit Farbangaben."""
        contrast_issues = []
        elements_with_style = self.soup.find_all(style=True)
        for el in elements_with_style:
            style = el.get("style", "")
            if "color" in style.lower() or "background" in style.lower():
                contrast_issues.append({
                    "element": str(el.name),
                    "style": style,
                    "html_snippet": str(el)[:300],
                    "text": el.get_text(strip=True)[:100]
                })
        return contrast_issues

    def check_forms(self) -> List[Dict[str, Any]]:
        """Prüft Formulare auf Labels und barrierefreie Eingabefelder."""
        forms = []
        for form in self.soup.find_all("form"):
            inputs = []
            for inp in form.find_all(["input", "select", "textarea"]):
                input_type = inp.get("type", "text")
                input_id = inp.get("id", "")
                input_name = inp.get("name", "")
                aria_label = inp.get("aria-label", "")
                aria_labelledby = inp.get("aria-labelledby", "")
                placeholder = inp.get("placeholder", "")
                required = inp.get("required", False)

                # Prüfe ob ein Label existiert
                has_label = False
                if input_id:
                    label = form.find("label", attrs={"for": input_id})
                    has_label = label is not None

                # Wrapped Label prüfen
                if not has_label:
                    parent_label = inp.find_parent("label")
                    has_label = parent_label is not None

                inputs.append({
                    "type": input_type,
                    "id": input_id,
                    "name": input_name,
                    "aria_label": aria_label,
                    "aria_labelledby": aria_labelledby,
                    "placeholder": placeholder,
                    "required": required,
                    "has_label": has_label,
                    "accessible": has_label or bool(aria_label) or bool(aria_labelledby),
                    "html_snippet": str(inp)[:300]
                })

            forms.append({
                "action": form.get("action", ""),
                "method": form.get("method", "GET"),
                "inputs": inputs,
                "html_snippet": str(form)[:500]
            })
        return forms

    def check_lang(self) -> Dict[str, Any]:
        """Prüft das lang-Attribut des HTML-Elements."""
        html_tag = self.soup.find("html")
        lang = html_tag.get("lang", "") if html_tag else ""
        return {
            "lang": lang,
            "present": bool(lang),
            "valid": bool(re.match(r"^[a-z]{2}(-[A-Z]{2})?$", lang)) if lang else False
        }

    def check_keyboard_nav(self) -> List[Dict[str, Any]]:
        """Prüft auf Elemente die Tastatur-Navigation erschweren könnten."""
        issues = []
        # Tabindex prüfen
        for el in self.soup.find_all(attrs={"tabindex": True}):
            tabindex = el.get("tabindex", "")
            if tabindex not in ("0", "1", "-1"):
                issues.append({
                    "element": str(el.name),
                    "tabindex": tabindex,
                    "html_snippet": str(el)[:300],
                    "issue": f"Ungültiger tabindex-Wert: {tabindex}"
                })
        return issues

    def check_documents(self) -> List[Dict[str, Any]]:
        """Findet verlinkte Dokumente (PDF, DOC, etc.)."""
        docs = []
        doc_extensions = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
        for a in self.soup.find_all("a", href=True):
            href = a.get("href", "")
            parsed = urlparse(href)
            if any(parsed.path.lower().endswith(ext) for ext in doc_extensions):
                docs.append({
                    "href": urljoin(self.url, href),
                    "text": a.get_text(strip=True),
                    "extension": parsed.path.lower().split(".")[-1],
                    "html_snippet": str(a)[:300]
                })
        return docs

    def _check_meta(self) -> List[Dict[str, Any]]:
        """Prüft Meta-Tags (viewport, charset, description)."""
        meta_info = []
        charset = self.soup.find("meta", attrs={"charset": True})
        viewport = self.soup.find("meta", attrs={"name": "viewport"})
        description = self.soup.find("meta", attrs={"name": "description"})

        meta_info.append({
            "charset": charset.get("charset", "") if charset else "",
            "charset_present": charset is not None,
            "viewport": viewport.get("content", "") if viewport else "",
            "viewport_present": viewport is not None,
            "description": description.get("content", "") if description else "",
            "description_present": description is not None
        })
        return meta_info

    def _check_tables(self) -> List[Dict[str, Any]]:
        """Prüft Tabellen auf Barrierefreiheit (th, caption, scope)."""
        tables = []
        for table in self.soup.find_all("table"):
            has_caption = table.find("caption") is not None
            headers = table.find_all("th")
            has_scope = any(th.get("scope") for th in headers)

            tables.append({
                "has_caption": has_caption,
                "header_count": len(headers),
                "has_scope": has_scope,
                "html_snippet": str(table)[:500]
            })
        return tables

    def _check_iframes(self) -> List[Dict[str, Any]]:
        """Prüft iFrames auf Titel-Attribute."""
        iframes = []
        for iframe in self.soup.find_all("iframe"):
            title = iframe.get("title", "")
            iframes.append({
                "src": iframe.get("src", ""),
                "title": title,
                "title_missing": not bool(title.strip()),
                "html_snippet": str(iframe)[:300]
            })
        return iframes
