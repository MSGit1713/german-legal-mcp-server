#!/usr/bin/env python3
"""
🖥️ MCP SERVER
==============

Model Context Protocol Server für German Legal MCP
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import CallToolResult, ListToolsResult, Tool, TextContent

from .config import get_config, RECHTSGEBIETE
from .database import DatabaseManager
from .search import LegalSearchEngine
from .models import SearchQuery
from .utils import ValidationHelper, PerformanceHelper
from .server_formatting import ServerFormattingMixin


logger = logging.getLogger(__name__)


class GermanLegalMCPServer(ServerFormattingMixin):
    """German Legal MCP Server"""
    
    def __init__(self):
        self.config = get_config()
        self.server = Server(self.config.server.name)
        self.db_manager = None
        self.search_engine = None
        self._initialized = False
        
        # Performance-Tracking
        self.request_count = 0
        self.error_count = 0
        
        # Setup MCP handlers
        self._setup_handlers()
    
    async def initialize(self):
        """Initialisiert Server und Datenbank"""
        if self._initialized:
            return
        
        logger.info("🚀 Initialisiere German Legal MCP Server...")
        
        try:
            # Konfiguration und Logging
            self.config.setup_logging()
            
            # Datenbankmanager
            self.db_manager = DatabaseManager()
            
            # Datenbank-Gesundheitscheck
            health = await self.db_manager.check_database_health()
            if health["status"] != "healthy":
                logger.error(f"❌ Datenbank nicht bereit: {health['errors']}")
                raise RuntimeError(f"Datenbank-Probleme: {health['errors']}")
            
            logger.info(f"✅ Datenbank OK: {PerformanceHelper.format_number(health['total_cases'])} Fälle")
            
            # Suchmaschine
            self.search_engine = LegalSearchEngine(self.db_manager)
            
            self._initialized = True
            logger.info("✅ Server erfolgreich initialisiert!")
            
        except Exception as e:
            logger.error(f"❌ Initialisierungsfehler: {e}")
            raise
    
    def _setup_handlers(self):
        """Richtet MCP-Handler ein"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Liste aller verfügbaren Tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="suche_rechtsprechung",
                        description="Durchsucht deutsche Gerichtsentscheidungen mit erweiterten Filtern und intelligenter Relevanz-Bewertung",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "suchbegriff": {
                                    "type": "string",
                                    "description": "Suchbegriff (z.B. 'Mietrecht Kündigung', '\"fristlose Kündigung\"', § 543 BGB')"
                                },
                                "rechtsgebiet": {
                                    "type": "string",
                                    "description": "Rechtsgebiet-Filter",
                                    "enum": RECHTSGEBIETE
                                },
                                "gericht": {
                                    "type": "string",
                                    "description": "Gericht-Filter (z.B. 'Bundesgerichtshof', 'Landgericht München')"
                                },
                                "jahr_von": {
                                    "type": "integer",
                                    "description": "Startjahr (z.B. 2020)",
                                    "minimum": 1900,
                                    "maximum": 2030
                                },
                                "jahr_bis": {
                                    "type": "integer",
                                    "description": "Endjahr (z.B. 2023)",
                                    "minimum": 1900,
                                    "maximum": 2030
                                },
                                "anzahl": {
                                    "type": "integer",
                                    "description": "Anzahl Ergebnisse (Standard: 20, Maximum: 100)",
                                    "minimum": 1,
                                    "maximum": 100
                                }
                            },
                            "required": ["suchbegriff"]
                        }
                    ),
                    Tool(
                        name="erweiterte_suche",
                        description="Erweiterte Suche mit zusätzlichen Filtern für präzise Rechtsprechungsrecherche",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "suchbegriff": {
                                    "type": "string",
                                    "description": "Hauptsuchbegriff"
                                },
                                "rechtsgebiet": {
                                    "type": "string",
                                    "enum": RECHTSGEBIETE
                                },
                                "gericht": {"type": "string"},
                                "aktenzeichen": {
                                    "type": "string",
                                    "description": "Aktenzeichen-Filter"
                                },
                                "ecli": {
                                    "type": "string",
                                    "description": "ECLI-Filter"
                                },
                                "instanz": {
                                    "type": "string",
                                    "description": "Instanz-Filter"
                                },
                                "jahr_von": {"type": "integer", "minimum": 1900, "maximum": 2030},
                                "jahr_bis": {"type": "integer", "minimum": 1900, "maximum": 2030},
                                "anzahl": {"type": "integer", "minimum": 1, "maximum": 100}
                            },
                            "required": ["suchbegriff"]
                        }
                    ),
                    Tool(
                        name="aehnliche_faelle",
                        description="Findet ähnliche Rechtsfälle basierend auf einem gegebenen Fall",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "fall_id": {
                                    "type": "integer",
                                    "description": "ID des Referenzfalls"
                                },
                                "anzahl": {
                                    "type": "integer",
                                    "description": "Anzahl ähnlicher Fälle (Standard: 10)",
                                    "minimum": 1,
                                    "maximum": 50
                                }
                            },
                            "required": ["fall_id"]
                        }
                    ),
                    Tool(
                        name="fall_details",
                        description="Lädt detaillierte Informationen zu einem spezifischen Rechtsfall",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "fall_id": {
                                    "type": "integer",
                                    "description": "ID des Falls"
                                }
                            },
                            "required": ["fall_id"]
                        }
                    ),
                    Tool(
                        name="suchvorschlaege",
                        description="Generiert Suchvorschläge basierend auf Eingabe",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "eingabe": {
                                    "type": "string",
                                    "description": "Teilweise Eingabe für Vorschläge"
                                }
                            },
                            "required": ["eingabe"]
                        }
                    ),
                    Tool(
                        name="datenbank_statistik",
                        description="Zeigt umfassende Statistiken der Rechtsprechungsdatenbank",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "detailliert": {
                                    "type": "boolean",
                                    "description": "Detaillierte Statistiken anzeigen",
                                    "default": False
                                }
                            }
                        }
                    ),
                    Tool(
                        name="system_status",
                        description="Zeigt System- und Performance-Status des MCP Servers",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Verarbeitet Tool-Aufrufe"""
            
            if not self._initialized:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="❌ Server nicht initialisiert. Bitte warten Sie auf die Initialisierung."
                    )]
                )
            
            self.request_count += 1
            
            try:
                if name == "suche_rechtsprechung":
                    return await self._handle_search(arguments)
                
                elif name == "erweiterte_suche":
                    return await self._handle_advanced_search(arguments)
                
                elif name == "aehnliche_faelle":
                    return await self._handle_similar_cases(arguments)
                
                elif name == "fall_details":
                    return await self._handle_case_details(arguments)
                
                elif name == "suchvorschlaege":
                    return await self._handle_search_suggestions(arguments)
                
                elif name == "datenbank_statistik":
                    return await self._handle_database_stats(arguments)
                
                elif name == "system_status":
                    return await self._handle_system_status(arguments)
                
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"❌ Unbekanntes Tool: {name}"
                        )]
                    )
            
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Tool-Fehler ({name}): {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"❌ Fehler bei der Ausführung: {str(e)}\n💡 Bitte überprüfen Sie Ihre Eingaben und versuchen Sie es erneut."
                    )]
                )
    
    async def _handle_search(self, arguments: dict) -> CallToolResult:
        """Behandelt Standard-Rechtsprechungssuche"""
        suchbegriff = arguments.get("suchbegriff", "").strip()
        
        if not suchbegriff:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="❌ Bitte geben Sie einen Suchbegriff an."
                )]
            )
        
        query = SearchQuery(
            query=ValidationHelper.sanitize_search_term(suchbegriff),
            rechtsgebiet=arguments.get("rechtsgebiet"),
            gericht=arguments.get("gericht"),
            jahr_von=ValidationHelper.validate_year(arguments.get("jahr_von")),
            jahr_bis=ValidationHelper.validate_year(arguments.get("jahr_bis")),
            limit=ValidationHelper.validate_limit(arguments.get("anzahl", 20))
        )
        
        results = await self.search_engine.search_cases(query)
        
        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Keine Ergebnisse für '{suchbegriff}' gefunden.\n💡 Versuchen Sie allgemeinere Suchbegriffe oder weniger Filter."
                )]
            )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=self._format_search_results(results, suchbegriff)
            )]
        )
    
    async def _handle_advanced_search(self, arguments: dict) -> CallToolResult:
        """Behandelt erweiterte Suche"""
        suchbegriff = arguments.get("suchbegriff", "").strip()
        
        if not suchbegriff:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="❌ Bitte geben Sie einen Suchbegriff an."
                )]
            )
        
        results = await self.search_engine.advanced_search(suchbegriff, arguments)
        
        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Keine Ergebnisse für erweiterte Suche gefunden."
                )]
            )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=self._format_search_results(results, suchbegriff, advanced=True)
            )]
        )
    
    async def _handle_similar_cases(self, arguments: dict) -> CallToolResult:
        """Behandelt Suche nach ähnlichen Fällen"""
        fall_id = arguments.get("fall_id")
        anzahl = ValidationHelper.validate_limit(arguments.get("anzahl", 10), max_val=50)
        
        if not fall_id:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="❌ Bitte geben Sie eine Fall-ID an."
                )]
            )
        
        results = await self.search_engine.search_similar_cases(fall_id, anzahl)
        
        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Keine ähnlichen Fälle für Fall-ID {fall_id} gefunden."
                )]
            )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=self._format_similar_cases(results, fall_id)
            )]
        )
    
    async def _handle_case_details(self, arguments: dict) -> CallToolResult:
        """Behandelt Abfrage von Fall-Details"""
        fall_id = arguments.get("fall_id")
        
        if not fall_id:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="❌ Bitte geben Sie eine Fall-ID an."
                )]
            )
        
        case = await self.db_manager.get_case_by_id(fall_id)
        
        if not case:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Fall mit ID {fall_id} nicht gefunden."
                )]
            )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=self._format_case_details(case)
            )]
        )
    
    async def _handle_search_suggestions(self, arguments: dict) -> CallToolResult:
        """Behandelt Suchvorschläge"""
        eingabe = arguments.get("eingabe", "").strip()
        
        if len(eingabe) < 3:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="💡 Geben Sie mindestens 3 Zeichen ein für Suchvorschläge."
                )]
            )
        
        suggestions = await self.search_engine.get_search_suggestions(eingabe)
        
        if not suggestions:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Keine Suchvorschläge für '{eingabe}' gefunden."
                )]
            )
        
        output = f"💡 **Suchvorschläge für '{eingabe}':**\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            output += f"{i}. {suggestion}\n"
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=output
            )]
        )
    
    async def _handle_database_stats(self, arguments: dict) -> CallToolResult:
        """Behandelt Datenbankstatistiken"""
        detailliert = arguments.get("detailliert", False)
        
        stats = await self.db_manager.get_database_statistics()
        cache_stats = self.search_engine.get_cache_stats()
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=self._format_database_stats(stats, cache_stats, detailliert)
            )]
        )
    
    async def _handle_system_status(self, arguments: dict) -> CallToolResult:
        """Behandelt System-Status"""
        
        # Datenbank-Gesundheit
        health = await self.db_manager.check_database_health()
        cache_stats = self.search_engine.get_cache_stats()
        
        output = "🖥️ **German Legal MCP Server - System Status**\n\n"
        
        # Server-Info
        output += f"**📊 Server-Information:**\n"
        output += f"- Version: {self.config.server.version}\n"
        output += f"- Requests: {PerformanceHelper.format_number(self.request_count)}\n"
        output += f"- Errors: {self.error_count}\n"
        
        if self.request_count > 0:
            error_rate = (self.error_count / self.request_count) * 100
            output += f"- Error Rate: {error_rate:.1f}%\n"
        
        output += "\n"
        
        # Datenbank-Status
        status_emoji = "✅" if health["status"] == "healthy" else "❌"
        output += f"**🗄️ Datenbank-Status:** {status_emoji}\n"
        output += f"- Datei: {self.db_manager.db_path}\n"
        output += f"- Größe: {PerformanceHelper.format_size(health['file_size'])}\n"
        output += f"- Fälle: {PerformanceHelper.format_number(health['total_cases'])}\n"
        output += f"- FTS: {'✅' if health['fts_enabled'] else '❌'}\n"
        
        if health["errors"]:
            output += f"- **Fehler:** {', '.join(health['errors'])}\n"
        
        output += "\n"
        
        # Cache-Status
        output += f"**⚡ Cache-Performance:**\n"
        output += f"- Hit Rate: {cache_stats['hit_rate']}%\n"
        output += f"- Cache Size: {cache_stats['cache_size']}/{cache_stats['max_size']}\n"
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=output
            )]
        )
