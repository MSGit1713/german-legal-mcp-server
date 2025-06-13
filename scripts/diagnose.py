#!/usr/bin/env python3
"""
🔧 DIAGNOSE SCRIPT
==================

Diagnose-Tool für German Legal MCP Server
"""

import os
import sys
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime


async def diagnose_system():
    """Führt System-Diagnose durch"""
    print("German Legal MCP Server - Diagnose")
    print("=" * 50)
    
    # Python-Version
    print(f"Python: {sys.version}")
    
    # Arbeitsverzeichnis
    print(f"Arbeitsverzeichnis: {os.getcwd()}")
    
    # Paket-Import
    try:
        import german_legal_mcp
        print(f"OK: Paket gefunden: v{german_legal_mcp.__version__}")
    except ImportError as e:
        print(f"ERROR: Paket-Import fehlgeschlagen: {e}")
        return
    
    # Konfiguration
    try:
        from german_legal_mcp.config import get_config, find_database
        config = get_config()
        print(f"OK: Konfiguration geladen")
        
        # Datenbankpfad
        db_path = find_database()
        if db_path:
            print(f"OK: Datenbank gefunden: {db_path}")
            await diagnose_database(db_path)
        else:
            print(f"ERROR: Keine Datenbank gefunden")
            print(f"   Konfigurierter Pfad: {config.database.path}")
            
    except Exception as e:
        print(f"ERROR: Konfigurationsfehler: {e}")
        return
    
    # MCP-Dependencies
    try:
        import mcp
        print(f"OK: MCP-Framework verfügbar")
    except ImportError:
        print(f"ERROR: MCP-Framework nicht gefunden")
    
    # Verzeichnisse
    dirs = ["data", "logs", "config"]
    for dir_name in dirs:
        if Path(dir_name).exists():
            print(f"OK: Verzeichnis: {dir_name}")
        else:
            print(f"WARNING: Verzeichnis fehlt: {dir_name}")


async def diagnose_database(db_path: str):
    """Diagnose der Datenbank"""
    print(f"\n📊 Datenbank-Diagnose: {db_path}")
    print("-" * 30)
    
    try:
        # Dateigröße
        size = os.path.getsize(db_path)
        size_mb = size / (1024 * 1024)
        print(f"📏 Dateigröße: {size_mb:.1f} MB")
        
        # SQLite-Verbindung
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabellen
        cursor.execute("""
            SELECT name, type FROM sqlite_master 
            WHERE type IN ('table', 'view')
            ORDER BY name
        """)
        tables = cursor.fetchall()
        print(f"📋 Tabellen ({len(tables)}):")
        for name, type_name in tables:
            # Zeilen zählen
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
                count = cursor.fetchone()[0]
                print(f"   - {name} ({type_name}): {count:,} Einträge")
            except:
                print(f"   - {name} ({type_name}): Fehler beim Zählen")
        
        # Cases-Tabelle spezifisch
        if any(name == 'cases' for name, _ in tables):
            print(f"\n⚖️ Cases-Tabelle Details:")
            
            # Jahre
            cursor.execute("""
                SELECT year, COUNT(*) 
                FROM cases 
                WHERE year IS NOT NULL 
                GROUP BY year 
                ORDER BY year DESC 
                LIMIT 5
            """)
            years = cursor.fetchall()
            print(f"   Aktuelle Jahre:")
            for year, count in years:
                print(f"     {year}: {count:,}")
            
            # Rechtsgebiete
            cursor.execute("""
                SELECT rechtsgebiet, COUNT(*) 
                FROM cases 
                WHERE rechtsgebiet IS NOT NULL 
                GROUP BY rechtsgebiet 
                ORDER BY COUNT(*) DESC 
                LIMIT 5
            """)
            areas = cursor.fetchall()
            print(f"   Top Rechtsgebiete:")
            for area, count in areas:
                print(f"     {area}: {count:,}")
        
        # FTS-Status
        if any(name == 'cases_fts' for name, _ in tables):
            try:
                cursor.execute("SELECT COUNT(*) FROM cases_fts")
                fts_count = cursor.fetchone()[0]
                print(f"✅ FTS-Index: {fts_count:,} Einträge")
            except:
                print(f"❌ FTS-Index: Fehler")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Datenbankfehler: {e}")


async def test_search_functionality():
    """Testet Suchfunktionalität"""
    print(f"\n🔍 Such-Test")
    print("-" * 20)
    
    try:
        from german_legal_mcp.database import DatabaseManager
        from german_legal_mcp.search import LegalSearchEngine
        from german_legal_mcp.models import SearchQuery
        
        # Datenbank
        db_manager = DatabaseManager()
        search_engine = LegalSearchEngine(db_manager)
        
        # Einfache Suche
        query = SearchQuery(query="Urteil", limit=3)
        results = await search_engine.search_cases(query)
        
        print(f"✅ Suche erfolgreich: {len(results)} Ergebnisse")
        
        if results:
            case = results[0].case
            print(f"   Beispiel: {case.court_name} - {case.file_number}")
        
        # Cache-Test
        cache_stats = search_engine.get_cache_stats()
        print(f"✅ Cache funktioniert: {cache_stats['cache_size']} Einträge")
        
    except Exception as e:
        print(f"❌ Such-Test fehlgeschlagen: {e}")


async def test_mcp_server():
    """Testet MCP Server"""
    print(f"\n🖥️ MCP Server Test")
    print("-" * 20)
    
    try:
        from german_legal_mcp.server import GermanLegalMCPServer
        
        # Server erstellen
        server = GermanLegalMCPServer()
        print(f"✅ Server erstellt")
        
        # Initialisierung (ohne tatsächlichen Start)
        await server.initialize()
        print(f"✅ Server initialisiert")
        
        # Request-Counter prüfen
        print(f"📊 Requests: {server.request_count}")
        print(f"📊 Errors: {server.error_count}")
        
    except Exception as e:
        print(f"❌ MCP Server Test fehlgeschlagen: {e}")


def generate_report():
    """Erstellt Diagnose-Report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"diagnose_report_{timestamp}.txt"
    
    print(f"\n📄 Report wird erstellt: {report_file}")
    
    # TODO: Report-Generierung implementieren
    # Hier könnten alle Diagnose-Daten in eine Datei geschrieben werden


async def main():
    """Hauptfunktion"""
    await diagnose_system()
    await test_search_functionality()
    await test_mcp_server()
    
    print(f"\n🎯 Diagnose abgeschlossen")
    print(f"💡 Bei Problemen: Überprüfen Sie Datenbank-Pfad und Dependencies")


if __name__ == "__main__":
    asyncio.run(main())
