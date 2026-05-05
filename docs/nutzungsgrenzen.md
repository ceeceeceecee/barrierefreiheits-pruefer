# Nutzungsgrenzen – KI-Barrierefreiheits-Prüfer

## ⚠️ Wichtiger Hinweis

Dieses Tool dient als **Unterstützung** bei der Barrierefreiheitsprüfung. Es ersetzt **keine** manuelle Prüfung durch zertifizierte Auditoren und kann **keine** rechtssichere Konformitätserklärung ersetzen.

## Was das Tool kann

- Automatische Überprüfung von HTML-Code gegen definierte WCAG-Regeln
- Erkennung fehlender Alt-Texte, ungültiger Überschriftenstrukturen, etc.
- KI-gestützte Korrekturvorschläge
- Generierung von Prüfberichten

## Was das Tool NICHT kann

### Automatische Vollprüfung
- Farbkontraste können nur bedingt geprüft werden (erfordert visuelles Rendering)
- Tastaturnavigierbarkeit kann nicht vollständig getestet werden
- Screenreader-Kompatibilität wird nicht getestet
- Dynamische Inhalte (JavaScript) werden nicht vollständig erfasst

### Rechtssichere Zertifizierung
- Kein Ersatz für BITV-Test-Zertifizierung
- Keine rechtsverbindliche Konformitätserklärung
- Keine Garantie für WCAG-Konformität

## KI-Halluzinationen

### Was sind Halluzinationen?
KI-Modelle können plausible aber falsche Informationen erzeugen. Dies wird als "Halluzination" bezeichnet.

### Im Kontext dieses Tools:
- Alt-Text-Vorschläge können falsche Bildbeschreibungen enthalten
- HTML-Korrekturvorschläge können syntaktisch falsch sein
- Erklärungen können ungenau oder irreführend sein
- Konfidenz-Werte sind Schätzungen, keine Garantien

### So minimieren Sie das Risiko:
1. **Jeden** KI-Vorschlag manuell überprüfen
2. Korrigierten HTML-Code im Browser testen
3. Alt-Texte mit dem tatsächlichen Bild vergleichen
4. Bei Zweifel Fachexperten hinzuziehen

## Technische Grenzen

### JavaScript-Rendering
- Das Tool analysiert das initiale HTML
- JavaScript-generierte Inhalte werden nicht erfasst
- Single-Page-Applications (SPA) können nur teilweise geprüft werden

### Authentifizierung
- Geschützte Bereiche können nicht geprüft werden
- Login-geschützte Formulare sind nicht erreichbar

### Performance
- Große Webseiten (>100 Seiten) können lange dauern
- KI-Anfragen verlangsamen die Prüfung erheblich

### Browser-Kompatibilität
- Prüfung erfolgt mit einem festen User-Agent
- Browser-spezifische Barrierefreiheitsprobleme können übersehen werden

## Empfohlener Workflow

1. **Automatische Prüfung** mit diesem Tool durchführen
2. **KI-Vorschläge** sichten und manuell überprüfen
3. **Manuelle Prüfung** durchführen:
   - Tastatur-Navigation testen
   - Mit Screenreader testen (NVDA, VoiceOver)
   - Farbkontrast manuell prüfen
4. **Experten-Review** durch zertifizierten Auditor
5. **Konformitätserklärung** erstellen (nach erfolgreicher Prüfung)

## Haftungsausschluss

Der Autor übernimmt keine Haftung für:
- Fehler in den Prüfergebnissen
- Unvollständige oder falsche KI-Vorschläge
- Schäden die durch Nutzung des Tools entstehen
- Nicht erkannte Barrierefreiheitsprobleme

Die Nutzung erfolgt auf eigene Verantwortung. Für rechtssichere Barrierefreiheitsprüfungen wenden Sie sich an zertifizierte Auditoren.
