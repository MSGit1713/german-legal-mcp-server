#!/usr/bin/env python3
"""
DIAGNOSE SCRIPT - SIMPLIFIED
=============================

Vereinfachtes Diagnose-Tool für German Legal MCP Server
"""

import os
import sys
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime


def simple_diagnose():
    """Führt einfache System-Diagnose durch"""
    print("German Legal MCP Server - Diagnose")
    print("=" * 50)
    
    # Python-Version
    print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Arbeitsverzeichnis
    print(f"Arbeitsverzeichnis: {os.getcwd()}")
    
    # Paket-Import
    try:
        sys.path.insert(0, 'src')
        import german_legal_mcp
        print(f"OK: Paket importiert v{german_legal_mcp.__version__}")
    except Exception as e:
        print(f"ERROR: Paket-Import fehlgeschlagen: {e}")
        return False
    
    # Konfiguration
    try:
        from german_legal_mcp.config import get_config, find_database
        config = get_config()
        print(f"OK: Konfiguration geladen")
        
        # Datenbankpfad
        db_path = find_database()
        if db_path:
            print(f"OK: Datenbank gefunden: {db_path}")
            diagnose_database_simple(db_path)
        else:
            print(f"ERROR: Keine Datenbank gefunden")
            print(f"   Konfiguriert: {config.database.path}")
            
    except Exception as e:
        print(f"ERROR: Konfigurationsfehler: {e}")
        return False
    
    # MCP-Framework
    try:
        import mcp
        print(f"OK: MCP-Framework verfügbar")
    except ImportError:
        print(f"ERROR: MCP-Framework nicht gefunden")
        return False
    
    # Verzeichnisse
    dirs = ["data", "logs", "config"]
    for dir_name in dirs:
        if Path(dir_name).exists():
            print(f"OK: Verzeichnis vorhanden: {dir_name}")
        else:
            print(f"WARNING: Verzeichnis fehlt: {dir_name}")
    
    return True


def diagnose_database_simple(db_path: str):
    """Einfache Datenbank-Diagnose"""
    print(f"\nDatenbank-Diagnose: {db_path}")
    print("-" * 30)
    
    try:
        # Dateigröße
        size = os.path.getsize(db_path)
        size_mb = size / (1024 * 1024)
        print(f"Dateigröße: {size_mb:.1f} MB")
        
        # SQLite-Verbindung
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabellen
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tabellen: {', '.join(tables)}")
        
        # Cases-Tabelle
        if 'cases' in tables:
            cursor.execute("SELECT COUNT(*) FROM cases")
            count = cursor.fetchone()[0]
            print(f"Fälle in Datenbank: {count:,}")
            
            # Beispiel-Fall
            cursor.execute("SELECT court_name, file_number FROM cases LIMIT 1")
            example = cursor.fetchone()
            if example:
                print(f"Beispiel: {example[0]} - {example[1]}")
        
        # FTS-Status
        if 'cases_fts' in tables:
            try:
                cursor.execute("SELECT COUNT(*) FROM cases_fts")
                fts_count = cursor.fetchone()[0]
                print(f"FTS-Index: {fts_count:,} Einträge")
            except:
                print(f"FTS-Index: ERROR")
        
        conn.close()
        
    except Exception as e:
        print(f"Datenbankfehler: {e}")


def test_search_simple():
    """Testet Suchfunktionalität"""
    print(f"\nSuch-Test")
    print("-" * 20)
    
    try:
        sys.path.insert(0, 'src')
        from german_legal_mcp.database import DatabaseManager
        from german_legal_mcp.search import LegalSearchEngine
        from german_legal_mcp.models import SearchQuery
        
        # Synchrone Version für einfachen Test
        import sqlite3
        from german_legal_mcp.config import find_database
        
        db_path = find_database()
        if not db_path:
            print("ERROR: Keine Datenbank für Test verfügbar")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM cases")
        count = cursor.fetchone()[0]
        print(f"OK: {count} Fälle in Datenbank")
        
        # Einfache Suche testen
        cursor = conn.execute("""
            SELECT court_name, file_number 
            FROM cases 
            WHERE content_clean LIKE '%Urteil%' 
            LIMIT 3
        """)
        results = cursor.fetchall()
        print(f"OK: {len(results)} Testresultate gefunden")
        
        for court, file_num in results:
            print(f"   - {court}: {file_num}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: Such-Test fehlgeschlagen: {e}")


def main():
    """Hauptfunktion"""
    success = simple_diagnose()
    
    if success:
        test_search_simple()
        print(f"\nDiagnose abgeschlossen")
        print(f"Bei Problemen: Überprüfen Sie Datenbank-Pfad und Dependencies")
    else:
        print(f"\nDiagnose fehlgeschlagen - bitte Setup prüfen")


if __name__ == "__main__":
    main()
