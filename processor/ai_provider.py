"""
ai_provider.py – KI-Provider für Korrekturvorschläge
Unterstützt Ollama (lokal, DSGVO-konform) und Claude API.
"""

import json
import os
import requests
from typing import Dict, Optional


class AIProvider:
    """Abstraktionsschicht für KI-Anfragen – Ollama (lokal) oder Claude API."""

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3",
        api_key: str = "",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialisiert den KI-Provider.

        Args:
            provider: 'ollama' für lokale KI oder 'claude' für Claude API
            model: Modellname (z.B. 'llama3' oder 'claude-sonnet-4-20250514')
            api_key: API-Key für Claude (nur bei provider='claude' nötig)
            base_url: Basis-URL für Ollama
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

        # Prompts-Verzeichnis
        self.prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

    def _load_prompt(self, name: str) -> str:
        """Lädt einen Prompt aus der prompts/ Datei."""
        path = os.path.join(self.prompts_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""

    def _ask_ollama(self, prompt: str, system: str = "") -> str:
        """Sendet Anfrage an lokale Ollama-Instanz."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 1024
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama-Fehler: {e}")

    def _ask_claude(self, prompt: str, system: str = "") -> str:
        """Sendet Anfrage an Claude API."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("content", [{}])[0].get("text", "")
        except requests.RequestException as e:
            raise RuntimeError(f"Claude API-Fehler: {e}")

    def ask(self, prompt: str, system: str = "") -> str:
        """Sendet Anfrage an den konfigurierten Provider."""
        if self.provider == "ollama":
            return self._ask_ollama(prompt, system)
        elif self.provider == "claude":
            return self._ask_claude(prompt, system)
        else:
            raise ValueError(f"Unbekannter Provider: {self.provider}")

    def suggest_fix(
        self,
        criterion: str,
        element: str,
        html_snippet: str,
        description: str
    ) -> Dict:
        """
        Generiert einen KI-Korrekturvorschlag für einen WCAG-Verstoß.

        Args:
            criterion: WCAG-Kriterium (z.B. '1.1.1')
            element: Betroffenes HTML-Element
            html_snippet: HTML-Ausschnitt
            description: Beschreibung des Verstoßes

        Returns:
            Dict mit 'suggestion', 'fix_code', 'confidence'
        """
        # Prompt zusammenbauen
        fix_prompt = self._load_prompt("fix_suggestion.txt")
        explain_prompt = self._load_prompt("violation_explain.txt")

        user_prompt = f"""WCAG-Kriterium: {criterion}
Element: {element}
HTML: {html_snippet[:500]}
Beschreibung: {description}

{fix_prompt}"""

        system = "Du bist ein Experte für Web-Barrierefreiheit (WCAG 2.1, BITV 2.0). Antworte auf Deutsch. Sei präzise und praktisch."

        try:
            response = self.ask(user_prompt, system)

            # Versuche JSON aus der Antwort zu extrahieren
            json_match = response.find("{")
            if json_match >= 0:
                json_end = response.rfind("}") + 1
                try:
                    result = json.loads(response[json_match:json_end])
                    return {
                        "suggestion": result.get("suggestion", response[:500]),
                        "fix_code": result.get("fix_code", ""),
                        "confidence": min(1.0, max(0.0, float(result.get("confidence", 0.6))))
                    }
                except json.JSONDecodeError:
                    pass

            return {
                "suggestion": response[:500],
                "fix_code": "",
                "confidence": 0.5
            }

        except Exception as e:
            return {
                "suggestion": f"KI-Fehler: {str(e)}",
                "fix_code": "",
                "confidence": 0.0
            }

    def suggest_alt_text(self, image_src: str, surrounding_text: str = "") -> str:
        """Generiert einen Alt-Text für ein Bild."""
        alt_prompt = self._load_prompt("alt_text.txt")
        prompt = f"""Bild-URL: {image_src}
Kontext: {surrounding_text[:300]}

{alt_prompt}"""
        system = "Du bist ein Experte für barrierefreie Webinhalte. Antworte auf Deutsch. Gib nur den Alt-Text zurück, nichts anderes."
        try:
            return self.ask(prompt, system).strip().strip('"')
        except Exception:
            return ""

    def check_available(self) -> bool:
        """Prüft ob der KI-Provider erreichbar ist."""
        try:
            if self.provider == "ollama":
                resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return resp.status_code == 200
            elif self.provider == "claude" and self.api_key:
                return True
            return False
        except Exception:
            return False
