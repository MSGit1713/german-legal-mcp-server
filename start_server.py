#!/usr/bin/env python3
"""
START SCRIPT
============

Startet den German Legal MCP Server
"""

import os
import sys
import asyncio
from pathlib import Path


def setup_environment():
    """Richtet Umgebung ein"""
    # Datenbankpfad setzen
    db_path = Path("data/test_legal.db").absolute()
    os.environ['DB_PATH'] = str(db_path)
    
    # Log-Level
    os.environ['LOG_LEVEL'] = 'INFO'
    
    # Weitere Umgebungsvariablen
    os.environ['SEARCH_CACHE_SIZE'] = '50'
    os.environ['DB_CACHE_SIZE'] = '10000'
    
    print(f"DB_PATH = {os.environ['DB_PATH']}")


async def start_server():
    """Startet den MCP Server"""
    print("German Legal MCP Server")
    print("=" * 30)
    print("Starte Server...")
    
    setup_environment()
    
    try:
        # Pfad setzen
        sys.path.insert(0, 'src')
        
        # Main-Modul importieren und starten
        from german_legal_mcp.main import main
        await main()
        
    except KeyboardInterrupt:
        print("\nServer durch Benutzer beendet")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Prüfen ob im richtigen Verzeichnis
    if not Path("src/german_legal_mcp").exists():
        print("ERROR: Bitte im Projekt-Verzeichnis ausführen")
        print("cd C:/Users/Nerd/Desktop/german_legal_mcp")
        sys.exit(1)
    
    asyncio.run(start_server())
