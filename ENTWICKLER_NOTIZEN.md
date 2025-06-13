# 🔧 ENTWICKLER NOTIZEN - German Legal MCP Server

**Technische Dokumentation für kontinuierliche Entwicklung**

## 🏗️ Architektur-Entscheidungen

### **Warum SQLite + FTS5?**
- **Offline-Fähigkeit**: Keine externe DB-Server erforderlich
- **Performance**: FTS5 ist optimiert für Volltext-Suche
- **Einfachheit**: Keine komplexe Setup/Wartung
- **Portabilität**: Single-File-Database, einfach zu deployen
- **BM25-Scoring**: Moderne Relevanz-Bewertung integriert

### **Warum Async/Await?**
- **Zukunftssicherheit**: Skalierbar für Web-Interfaces
- **MCP-Kompatibilität**: Protocol erwartet async Handlers
- **Performance**: Non-blocking IO für große Datenoperationen
- **Testbarkeit**: Bessere Kontrolle über async Tests

### **Warum Typisierte Models?**
- **IDE-Support**: Bessere Auto-Vervollständigung
- **Fehlerprävention**: Compile-time Type Checking
- **Dokumentation**: Code ist selbst-dokumentierend
- **Refactoring**: Sichere Umstrukturierung

## 🔍 Komponenten-Details

### **config.py** - Konfigurationsmanagement
```python
# Zentrale Konfiguration mit Environment-Fallbacks
- AppConfig: Haupt-Konfigurationsklasse
- DatabaseConfig: DB-spezifische Einstellungen  
- SearchConfig: Such-Parameter
- ServerConfig: MCP-Server-Einstellungen

# Wichtige Funktionen:
- get_config(): Singleton-Pattern für globale Config
- find_database(): Intelligente DB-Pfad-Suche
- setup_logging(): Strukturiertes Logging konfigurieren
```

### **models.py** - Datenmodelle
```python
# Typisierte Datenstrukturen mit Pydantic-ähnlicher Validierung
- LegalCase: Hauptdatenmodell für Rechtsfälle
- SearchQuery: Such-Anfrage mit Validierung
- SearchResult: Such-Ergebnis mit Relevanz-Score
- DatabaseStats: Statistik-Datenmodell

# Design-Pattern:
- @dataclass für Performance
- Optional-Types für fehlende Daten
- from_db_row() Factory-Methods
- to_dict() für MCP-Response-Serialisierung
```

### **database.py** - Datenbankschicht
```python
# Async Context Manager Pattern für Connection-Handling
- DatabaseManager: Hauptklasse für DB-Operationen
- get_connection(): Async Context Manager
- Performance-Optimierungen: WAL-Mode, Cache-Size
- Health-Checks: Automatische DB-Validierung

# Wichtige Methods:
- get_cases_by_ids(): Batch-Loading für Performance
- get_database_statistics(): Cached Statistics
- optimize_database(): VACUUM/ANALYZE für Wartung
```

### **search.py** - Suchmaschine
```python
# LRU Cache + FTS5 für optimale Performance
- LegalSearchEngine: Main Search Class
- SearchCache: Custom LRU-Implementation mit TTL
- FTS Query Building: Erweiterte Query-Syntax
- Relevance Scoring: BM25 + Custom Ranking

# Wichtige Features:
- search_cases(): Haupt-Suchfunktion
- search_similar_cases(): Content-basierte Ähnlichkeit
- get_search_suggestions(): Auto-Vervollständigung
- Cache-Management: Automatic Eviction + Statistics
```

### **server.py** - MCP Server
```python
# MCP Protocol Implementation
- GermanLegalMCPServer: Main Server Class
- Tool Definitions: 7 verfügbare MCP-Tools
- Error Handling: Graceful Degradation
- Performance Tracking: Request/Error Counters

# MCP-Tools (alle implementiert):
1. suche_rechtsprechung - Standard-Suche
2. erweiterte_suche - Mit zusätzlichen Filtern
3. aehnliche_faelle - Ähnlichkeits-basiert
4. fall_details - Detaillierte Informationen
5. suchvorschlaege - Auto-Completion
6. datenbank_statistik - DB-Metriken
7. system_status - Server-Monitoring
```

### **utils.py** - Hilfsfunktionen
```python
# Spezialisierte Utility-Classes
- HTMLProcessor: HTML-Parsing für Rechtsdokumente
- FTSQueryBuilder: Erweiterte FTS5-Query-Syntax
- DateParser: Deutsche Datumsformate
- TextProcessor: Legal-Text-Verarbeitung
- ValidationHelper: Input-Validierung
- PerformanceHelper: Metriken und Formatierung

# Design-Pattern: Static Methods für Utility-Functions
```

## 💾 Datenstrukturen

### **SQLite Schema (aktuell):**
```sql
-- Haupt-Tabelle
CREATE TABLE cases (
    id INTEGER PRIMARY KEY,           -- OpenLegalData ID
    slug TEXT UNIQUE,                 -- URL-Slug
    court_name TEXT,                  -- Gerichtsname
    court_slug TEXT,                  -- Gericht-Slug
    jurisdiction TEXT,                -- Gerichtsbarkeit (raw)
    rechtsgebiet TEXT,                -- Mapped Rechtsgebiet
    level_of_appeal TEXT,             -- Instanz
    file_number TEXT,                 -- Aktenzeichen
    date TEXT,                        -- Urteilsdatum (ISO)
    type TEXT,                        -- Urteilstyp
    ecli TEXT,                        -- ECLI-Nummer
    content_raw TEXT,                 -- Original HTML
    content_clean TEXT,               -- Bereinigter Text
    content_length INTEGER,           -- Text-Länge
    year INTEGER,                     -- Extrahiertes Jahr
    created_date TEXT,                -- Import-Datum
    updated_date TEXT                 -- Update-Datum
);

-- FTS5 Virtual Table
CREATE VIRTUAL TABLE cases_fts USING fts5(
    content_clean,                    -- Volltext-Index
    court_name,                       -- Gericht suchbar
    file_number,                      -- Aktenzeichen suchbar
    ecli,                            -- ECLI suchbar
    rechtsgebiet,                    -- Rechtsgebiet suchbar
    content='cases',                 -- Verknüpfung zu cases
    content_rowid='id'               -- Row-ID Mapping
);
```

### **Performance-Indizes:**
```sql
-- Wichtig für Filter-Performance
CREATE INDEX idx_court ON cases(court_name);
CREATE INDEX idx_jurisdiction ON cases(jurisdiction);
CREATE INDEX idx_rechtsgebiet ON cases(rechtsgebiet);
CREATE INDEX idx_year ON cases(year);
CREATE INDEX idx_type ON cases(type);
```

## 🔄 Datenfluss

### **Typische Such-Anfrage:**
```
1. MCP-Request → server.py
2. Input-Validierung → models.SearchQuery
3. Cache-Check → search.SearchCache
4. FTS-Query-Building → utils.FTSQueryBuilder
5. DB-Query → database.DatabaseManager
6. Result-Processing → models.SearchResult
7. Response-Formatierung → server_formatting.py
8. Cache-Update → search.SearchCache
9. MCP-Response → Claude Desktop
```

### **Datenbank-Import-Flow:**
```
1. JSONL-File → scripts/create_test_db.py
2. JSON-Parsing → _process_case()
3. HTML-Cleaning → utils.HTMLProcessor
4. Batch-Insert → database._insert_batch()
5. FTS-Index-Build → SQLite FTS5
6. Validation → Health-Check
```

## ⚡ Performance-Optimierungen

### **SQLite-Tuning:**
```python
# In database.py - get_connection()
conn.execute("PRAGMA journal_mode=WAL")      # Write-Ahead Logging
conn.execute("PRAGMA synchronous=NORMAL")     # Balanced Safety/Speed
conn.execute("PRAGMA cache_size=10000")       # 10MB Cache
conn.execute("PRAGMA temp_store=memory")      # Memory-based Temp
```

### **FTS5-Optimierungen:**
```python
# Query-Building für bessere Relevanz
- Phrase-Suche mit Anführungszeichen
- Prefix-Suche mit Stern (*)
- OR-Verknüpfung für bessere Recall
- BM25-Scoring für moderne Relevanz
```

### **Cache-Strategy:**
```python
# LRU Cache mit TTL für Such-Performance
- Max 50 Entries (konfigurierbar)
- 1-Stunden TTL (konfigurierbar)
- Automatic Eviction bei Memory-Druck
- Hit-Rate Tracking für Monitoring
```

## 🧪 Test-Strategy

### **Test-Pyramide:**
```
🔺 Unit Tests (80%)
   - Jede Utility-Function
   - Model-Validierung
   - Einzelne DB-Operationen
   
🔺 Integration Tests (15%)
   - Search-Engine End-to-End
   - Database-Operationen
   - MCP-Tool-Funktionalität
   
🔺 System Tests (5%)
   - Vollständiger Server-Start
   - Performance-Benchmarks
   - Memory-Leak-Detection
```

### **Test-Datenbank:**
```python
# Definierte Test-Cases für reproduzierbare Tests
- 5 verschiedene Rechtsgebiete
- Verschiedene Gerichte (BGH, BAG, BSG, BVerwG, LG)
- Verschiedene Jahre (2022-2024)
- Verschiedene Content-Längen
- Unicode-Test-Cases
```

## 🚨 Kritische Abhängigkeiten

### **Breaking Changes vermeiden:**
- **MCP-Tool-Interface**: Niemals Parameter entfernen
- **Database-Schema**: Nur additive Änderungen
- **Config-Format**: Backwards-kompatible Updates
- **Response-Format**: Strukturelle Kompatibilität

### **Externe Dependencies:**
- **mcp>=1.0.0**: Core Framework (breaking changes möglich)
- **sqlite3**: Standard Library (stabil)
- **Python 3.8+**: Minimum Version (async/await support)

## 🔧 Debug-Strategien

### **Logging-Pattern:**
```python
# Strukturiertes Logging mit Context
logger = logging.getLogger(__name__)
logger.info(f"🔍 Suche: '{query}' | Filter: {filters}")
logger.error(f"❌ DB-Fehler: {error}", extra={"query": query})
```

### **Performance-Debugging:**
```python
# @PerformanceHelper.measure_time Decorator
# Für alle zeitkritischen Operationen
# Automatisches Logging von Ausführungszeiten
```

### **Diagnose-Tools:**
```bash
# Für Problemdiagnose in neuen Chats
python scripts/simple_diagnose.py    # System-Status
python scripts/test_server.py        # Funktionalitäts-Test
python scripts/test_runner.py        # Vollständige Test-Suite
```

---

## 💡 **Hinweise für neue Entwicklungszyklen:**

### **Code-Review-Checklist:**
- [ ] Type-Hints vollständig?
- [ ] Error-Handling implementiert?
- [ ] Logging hinzugefügt?
- [ ] Tests geschrieben?
- [ ] Dokumentation aktualisiert?
- [ ] Backwards-kompatibel?

### **Performance-Checklist:**
- [ ] Async/Await verwendet?
- [ ] DB-Queries optimiert?
- [ ] Caching berücksichtigt?
- [ ] Memory-Leaks vermieden?
- [ ] Load-Testing durchgeführt?

### **Architektur-Prinzipien:**
1. **Separation of Concerns**: Jedes Modul hat eine klare Verantwortung
2. **Dependency Injection**: Konfiguration von außen injizieren
3. **Error Isolation**: Fehler nicht propagieren lassen
4. **Performance First**: Immer an Skalierung denken
5. **Test-Driven**: Tests vor/während Implementierung

---

**🎯 Diese Notizen werden bei jeder größeren Änderung aktualisiert, um das Architektur-Wissen zu bewahren.**
