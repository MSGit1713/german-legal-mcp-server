#!/usr/bin/env python3
"""
🏛️ GERMAN LEGAL MCP
===================

German Legal MCP Server Package
"""

__version__ = "1.0.0"
__author__ = "Claude & User"
__description__ = "MCP Server für deutsche Rechtsprechung"

from .config import get_config, AppConfig
from .database import DatabaseManager
from .search import LegalSearchEngine
from .server import GermanLegalMCPServer
from .models import (
    LegalCase, SearchQuery, SearchResult, 
    DatabaseStats, Rechtsgebiet, Gerichtstyp
)

__all__ = [
    "get_config",
    "AppConfig", 
    "DatabaseManager",
    "LegalSearchEngine",
    "GermanLegalMCPServer",
    "LegalCase",
    "SearchQuery", 
    "SearchResult",
    "DatabaseStats",
    "Rechtsgebiet",
    "Gerichtstyp"
]
