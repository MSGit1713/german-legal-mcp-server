# 🏛️ German Legal MCP Server

**Version 1.0.0 | Status: ✅ PRODUKTIONSBEREIT**

Ein Model Context Protocol (MCP) Server für deutsche Rechtsprechung - ermöglicht die Durchsuchung juristischer Datenbanken direkt in Claude Desktop.

## 🎯 Features

- **7 vollständig funktionale MCP-Tools** für juristische Recherche
- **Volltext-Suche** mit BM25-Scoring und SQLite FTS5
- **Ähnlichkeitssuche** für verwandte Rechtsfälle
- **Intelligente Suchvorschläge** mit Auto-Vervollständigung
- **Performance-optimiert** mit Caching (<200ms Antwortzeiten)
- **Claude Desktop Integration** - sofort einsatzbereit

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.13+
- Claude Desktop
- SQLite 3.45+ (mit FTS5-Support)

### Installation

1. **Repository klonen:**
```bash
git clone https://github.com/MSGit1713/german-legal-mcp-server.git
cd german-legal-mcp-server
```

2. **Setup ausführen:**
```bash
python scripts/setup.py
```

3. **Claude Desktop konfigurieren:**
   - Konfiguration aus `config/claude_mcp_config.json` in Claude Desktop Config einfügen
   - Claude Desktop neu starten

4. **Testen:**
```bash
python scripts/test_server.py
```

## 🔧 Verfügbare MCP-Tools

| Tool | Beschreibung |
|------|-------------|
| `suche_rechtsprechung` | Hauptsuchfunktion für Rechtsfälle |
| `erweiterte_suche` | Suche mit zusätzlichen Filtern |
| `aehnliche_faelle` | Ähnlichkeits-basierte Fallsuche |
| `fall_details` | Detaillierte Informationen zu einem Fall |
| `suchvorschlaege` | Intelligente Auto-Vervollständigung |
| `datenbank_statistik` | Umfassende Datenbankmetriken |
| `system_status` | Performance-Monitoring |

## 📁 Projektstruktur

```
german_legal_mcp/
├── src/german_legal_mcp/     # Core MCP Server Code
├── tests/                    # Unit & Integration Tests
├── scripts/                  # Entwickler-Tools & Setup
├── config/                   # Konfigurationsdateien
├── docs/                     # Dokumentation
└── data/                     # Datenbankdateien
```

## 🏗️ Architektur

- **Design Pattern**: Modulares MVC-ähnliches Pattern
- **Async Support**: Vollständig async/await implementiert
- **Error Handling**: Umfassende Exception-Behandlung
- **Logging**: Strukturiertes Logging mit Rotation
- **Database**: SQLite mit FTS5 für Volltext-Suche

## 📊 Performance

- **Suchzeit**: ~15ms (Test-DB)
- **Memory**: ~50MB (kleine DB)
- **Cache-Hit-Rate**: 100% bei wiederholten Suchen
- **Startup-Zeit**: ~2 Sekunden

## 🛠️ Entwicklung

### Tests ausführen:
```bash
python scripts/test_runner.py
```

### Diagnose:
```bash
python scripts/simple_diagnose.py
```

### Test-Datenbank erstellen:
```bash
python scripts/create_test_db.py
```

## 📚 Dokumentation

- [Installation & Setup](docs/INSTALL.md)
- [Projekt Status](PROJEKT_STATUS.md)
- [Changelog](CHANGELOG.md)

## 🤝 Beitragen

Das Projekt ist produktionsreif und bereit für Erweiterungen. Vor Änderungen:

1. `python scripts/simple_diagnose.py` ausführen
2. Tests mit `python scripts/test_runner.py` laufen lassen
3. Dokumentation aktualisieren

## 📄 Lizenz

Dieses Projekt ist für juristische Anwendungen entwickelt und respektiert alle anwendbaren Gesetze und Vorschriften.

---

**Professionell entwickelt • Vollständig getestet • Produktionsreif** 🚀