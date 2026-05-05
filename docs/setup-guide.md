# Setup-Guide – KI-Barrierefreiheits-Prüfer

## Voraussetzungen

- Python 3.10 oder neuer
- pip (Python-Paketmanager)
- Git
- Optional: Docker & Docker Compose
- Optional: Ollama (für lokale KI)

## Option 1: Docker (empfohlen)

### 1. Repository klonen
```bash
git clone https://github.com/ceeceeceecee/barrierefreiheits-pruefer.git
cd barrierefreiheits-pruefer
```

### 2. Umgebungsvariablen konfigurieren
```bash
cp .env.example .env
# .env nach Bedarf anpassen
```

### 3. Docker Compose starten
```bash
docker-compose up -d
```

### 4. Ollama Modell herunterladen (einmalig)
```bash
docker-compose exec ollama ollama pull llama3
```

### 5. Anwendung aufrufen
Öffnen Sie im Browser: `http://localhost:8501`

## Option 2: Manuelle Installation

### 1. Repository klonen
```bash
git clone https://github.com/ceeceeceecee/barrierefreiheits-pruefer.git
cd barrierefreiheits-pruefer
```

### 2. Virtuelle Umgebung erstellen
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# oder: venv\Scripts\activate  # Windows
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 4. Ollama installieren (optional, für KI-Features)
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Modell herunterladen
ollama pull llama3
```

### 5. Anwendung starten
```bash
streamlit run app.py
```

### 6. Im Browser öffnen
`http://localhost:8501`

## Claude API (alternative KI)

Wenn Sie Claude statt Ollama verwenden möchten:

1. API-Key bei Anthropic erstellen: https://console.anthropic.com/
2. In der App unter Einstellungen → Claude als Provider wählen
3. API-Key eingeben

**Hinweis:** Claude ist ein externer Dienst. Für DSGVO-Konformität in Behörden wird Ollama empfohlen.

## PDF-Reports

Für PDF-Export wird WeasyPrint benötigt:

### Linux (Debian/Ubuntu)
```bash
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2
pip install weasyprint
```

### macOS
```bash
brew install pango cairo gdk-pixbuf
pip install weasyprint
```

## Konfiguration

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|-------------|
| `DB_PATH` | `./data/barrierefreiheit.db` | SQLite-Datenbankpfad |
| `REPORT_DIR` | `./reports` | Verzeichnis für generierte Reports |
| `AI_PROVIDER` | `ollama` | KI-Provider (ollama/claude) |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama Server-URL |
| `OLLAMA_MODEL` | `llama3` | Ollama Modellname |

## Erste Schritte

1. Öffnen Sie die App im Browser
2. Geben Sie eine URL ein (z.B. Ihre Behörden-Webseite)
3. Klicken Sie auf "Prüfung starten"
4. Sehen Sie sich die Ergebnisse an
5. Erstellen Sie einen HTML- oder PDF-Report

## Häufige Probleme

### Ollama nicht erreichbar
- Prüfen Sie ob Ollama läuft: `curl http://localhost:11434/api/tags`
- Prüfen Sie die URL in den Einstellungen

### Keine KI-Vorschläge
- Ollama: Modell herunterladen mit `ollama pull llama3`
- Claude: API-Key prüfen

### PDF-Fehler
- WeasyPrint installieren (siehe oben)
- Alternativ: HTML-Report verwenden

## Reverse Proxy (Nginx)

Für Produktivbetrieb hinter Nginx:

```nginx
server {
    listen 443 ssl;
    server_name barrierefreiheit.example.de;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```
