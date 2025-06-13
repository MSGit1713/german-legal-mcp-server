# 🚀 Installationsanleitung - German Legal MCP Server

## Schnelle Installation

### 1. Voraussetzungen prüfen
```bash
python --version  # Muss 3.8+ sein
```

### 2. Projekt einrichten
```bash
cd C:\Users\Nerd\Desktop\german_legal_mcp
python scripts/setup.py
```

### 3. Konfiguration anpassen
Bearbeiten Sie `.env` und passen Sie den Datenbankpfad an:
```
DB_PATH=C:\Users\Nerd\AppData\Local\AnthropicClaude\app-0.10.14\ultimate_plus_plus_legal.db
```

### 4. Installation testen
```bash
python scripts/diagnose.py
```

### 5. Server starten
```bash
python -m german_legal_mcp.main
```

## Claude Desktop Konfiguration

### MCP Settings hinzufügen
1. Öffnen Sie Claude Desktop
2. Gehen Sie zu Settings > Developer > MCP Servers
3. Fügen Sie hinzu:

```json
{
  "german-legal-mcp": {
    "command": "python",
    "args": ["-m", "german_legal_mcp.main"],
    "cwd": "C:\\Users\\Nerd\\Desktop\\german_legal_mcp",
    "env": {
      "LEGAL_DATA_PATH": "C:\\Users\\Nerd\\AppData\\Local\\AnthropicClaude\\app-0.10.14\\ultimate_plus_plus_legal.db"
    }
  }
}
```

4. Claude Desktop neu starten

## Erste Nutzung

### Einfache Suche testen
```
Suche nach "Mietrecht Kündigung" in der deutschen Rechtsprechung
```

### Erweiterte Suche
```
Finde Arbeitsrecht-Urteile vom Bundesarbeitsgericht aus den letzten 3 Jahren
```

### Ähnliche Fälle
```
Zeige mir ähnliche Fälle zu Fall-ID 12345
```

## Problembehandlung

### Server startet nicht
1. Prüfen Sie Python-Version: `python --version`
2. Prüfen Sie Datenbank-Pfad in `.env`
3. Führen Sie Diagnose aus: `python scripts/diagnose.py`

### Keine Suchergebnisse
1. Prüfen Sie Datenbankverbindung
2. Testen Sie einfache Suche: "Urteil"
3. Prüfen Sie Logs in `logs/german_legal_mcp.log`

### Performance-Probleme
1. Erhöhen Sie Cache-Größe in `.env`:
   ```
   DB_CACHE_SIZE=50000
   SEARCH_CACHE_SIZE=100
   ```
2. Optimieren Sie Datenbank:
   ```bash
   python -c "
   import asyncio
   from german_legal_mcp.database import DatabaseManager
   db = DatabaseManager()
   asyncio.run(db.optimize_database())
   "
   ```

## Entwicklung

### Tests ausführen
```bash
python scripts/test_runner.py
python scripts/test_runner.py --coverage --lint
```

### Code formatieren
```bash
black src/ tests/
isort src/ tests/
```

## Support

- **GitHub Issues**: Für Bugs und Feature-Requests
- **Logs prüfen**: `logs/german_legal_mcp.log`
- **Diagnose**: `python scripts/diagnose.py`
