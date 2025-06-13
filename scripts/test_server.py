#!/usr/bin/env python3
"""
TEST MCP SERVER
===============

Testet den MCP Server ohne stdio
"""

import sys
import asyncio
import os
from pathlib import Path


async def test_mcp_server():
    """Testet MCP Server Funktionalität"""
    print("German Legal MCP Server - Test")
    print("=" * 40)
    
    # Environment setzen
    os.environ['DB_PATH'] = r'C:\Users\Nerd\Desktop\german_legal_mcp\data\test_legal.db'
    
    try:
        sys.path.insert(0, 'src')
        from german_legal_mcp.server import GermanLegalMCPServer
        
        # Server erstellen
        print("Erstelle Server...")
        server = GermanLegalMCPServer()
        
        # Initialisieren
        print("Initialisiere Server...")
        await server.initialize()
        print("OK: Server initialisiert")
        
        # Test-Suchanfrage simulieren
        print("\nTeste Suchfunktionalität...")
        
        # Direkte Suche testen
        from german_legal_mcp.models import SearchQuery
        query = SearchQuery(query="Mietrecht", limit=3)
        results = await server.search_engine.search_cases(query)
        
        print(f"OK: {len(results)} Suchergebnisse gefunden")
        
        for i, result in enumerate(results, 1):
            case = result.case
            print(f"  {i}. {case.court_name}: {case.file_number}")
            print(f"     Relevanz: {result.relevance_score:.2f}")
        
        # Statistiken testen
        print("\nTeste Statistiken...")
        stats = await server.db_manager.get_database_statistics()
        print(f"OK: {stats.total_cases} Fälle in Statistik")
        
        # Cache-Statistiken
        cache_stats = server.search_engine.get_cache_stats()
        print(f"Cache: {cache_stats['cache_size']} Einträge")
        
        print("\nOK: Alle Tests erfolgreich!")
        return True
        
    except Exception as e:
        print(f"ERROR: Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
