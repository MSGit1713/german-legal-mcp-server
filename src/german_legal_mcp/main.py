#!/usr/bin/env python3
"""
🚀 MAIN ENTRY POINT
===================

Haupteinstiegspunkt für German Legal MCP Server
"""

import asyncio
import logging
import sys
from pathlib import Path

from mcp.server.stdio import stdio_server

from german_legal_mcp import GermanLegalMCPServer
from german_legal_mcp.config import get_config


async def main():
    """Startet den German Legal MCP Server"""
    
    # Konfiguration laden
    config = get_config()
    config.setup_logging()
    
    logger = logging.getLogger("german_legal_mcp.main")
    logger.info("🚀 Starte German Legal MCP Server...")
    
    try:
        # Server erstellen und initialisieren
        server_instance = GermanLegalMCPServer()
        await server_instance.initialize()
        
        # MCP Server über stdio starten
        async with stdio_server() as (read_stream, write_stream):
            from mcp.server.models import InitializationOptions
            from mcp.server import NotificationOptions
            
            await server_instance.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=config.server.name,
                    server_version=config.server.version,
                    capabilities=server_instance.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    
    except KeyboardInterrupt:
        logger.info("👋 Server durch Benutzer beendet")
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
