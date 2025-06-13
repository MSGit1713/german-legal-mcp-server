#!/usr/bin/env python3
"""
MCP SERVER STARTER - Für Claude Desktop Integration
"""
import os
import sys
import asyncio
from pathlib import Path

# Environment für Test setzen
os.environ['DB_PATH'] = r'C:\Users\Nerd\Desktop\german_legal_mcp\data\test_legal.db'
os.environ['LOG_LEVEL'] = 'INFO'

# Pfad für Import setzen
sys.path.insert(0, 'src')

async def main():
    """Startet MCP Server für Claude Desktop"""
    try:
        from german_legal_mcp.main import main as mcp_main
        print("German Legal MCP Server wird gestartet...")
        print("Bereit für Claude Desktop Integration!")
        print("=" * 50)
        await mcp_main()
    except KeyboardInterrupt:
        print("\nServer beendet.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
