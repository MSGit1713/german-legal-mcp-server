#!/usr/bin/env python3
"""
🔧 CONFIGURATION MODULE
========================

Zentrale Konfiguration für German Legal MCP Server
Unterstützt Environment Variables und Config Files
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Datenbank-Konfiguration"""
    path: str = "german_legal.db"
    backup_path: Optional[str] = None
    cache_size: int = 10000
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    temp_store: str = "memory"
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Lädt Konfiguration aus Umgebungsvariablen"""
        return cls(
            path=os.getenv('DB_PATH', cls.path),
            backup_path=os.getenv('DB_BACKUP_PATH'),
            cache_size=int(os.getenv('DB_CACHE_SIZE', cls.cache_size)),
            journal_mode=os.getenv('DB_JOURNAL_MODE', cls.journal_mode),
            synchronous=os.getenv('DB_SYNCHRONOUS', cls.synchronous),
            temp_store=os.getenv('DB_TEMP_STORE', cls.temp_store)
        )


@dataclass
class SearchConfig:
    """Such-Konfiguration"""
    max_results: int = 100
    default_results: int = 20
    cache_size: int = 50
    cache_ttl: int = 3600  # Sekunden
    snippet_length: int = 64
    leitsatz_max_length: int = 200
    
    @classmethod
    def from_env(cls) -> 'SearchConfig':
        """Lädt Konfiguration aus Umgebungsvariablen"""
        return cls(
            max_results=int(os.getenv('SEARCH_MAX_RESULTS', cls.max_results)),
            default_results=int(os.getenv('SEARCH_DEFAULT_RESULTS', cls.default_results)),
            cache_size=int(os.getenv('SEARCH_CACHE_SIZE', cls.cache_size)),
            cache_ttl=int(os.getenv('SEARCH_CACHE_TTL', cls.cache_ttl)),
            snippet_length=int(os.getenv('SEARCH_SNIPPET_LENGTH', cls.snippet_length)),
            leitsatz_max_length=int(os.getenv('SEARCH_LEITSATZ_MAX_LENGTH', cls.leitsatz_max_length))
        )


@dataclass
class ServerConfig:
    """Server-Konfiguration"""
    name: str = "german-legal-mcp"
    version: str = "1.0.0"
    log_level: str = "INFO"
    max_concurrent_searches: int = 10
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Lädt Konfiguration aus Umgebungsvariablen"""
        return cls(
            name=os.getenv('SERVER_NAME', cls.name),
            version=os.getenv('SERVER_VERSION', cls.version),
            log_level=os.getenv('LOG_LEVEL', cls.log_level),
            max_concurrent_searches=int(os.getenv('MAX_CONCURRENT_SEARCHES', cls.max_concurrent_searches))
        )


@dataclass
class AppConfig:
    """Haupt-Anwendungskonfiguration"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    # Zusätzliche Pfade
    data_dir: Path = field(default_factory=lambda: Path.home() / "german_legal_data")
    log_dir: Path = field(default_factory=lambda: Path.home() / "german_legal_logs")
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'AppConfig':
        """
        Lädt Konfiguration aus verschiedenen Quellen:
        1. Environment Variables
        2. Config File (falls angegeben)
        3. Defaults
        """
        config = cls()
        
        # Aus Environment Variables laden
        config.database = DatabaseConfig.from_env()
        config.search = SearchConfig.from_env()
        config.server = ServerConfig.from_env()
        
        # Pfade aus Environment
        if data_dir := os.getenv('DATA_DIR'):
            config.data_dir = Path(data_dir)
        if log_dir := os.getenv('LOG_DIR'):
            config.log_dir = Path(log_dir)
        
        # Verzeichnisse erstellen falls sie nicht existieren
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.log_dir.mkdir(parents=True, exist_ok=True)
        
        return config
    
    def setup_logging(self) -> None:
        """Konfiguriert Logging"""
        log_file = self.log_dir / "german_legal_mcp.log"
        
        # Logging-Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Root Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.server.log_level))
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File Handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    def get_database_paths(self) -> Dict[str, str]:
        """Gibt alle möglichen Datenbankpfade zurück"""
        possible_paths = [
            # Absoluter Pfad falls angegeben
            self.database.path,
            
            # Im Data Directory
            str(self.data_dir / "german_legal.db"),
            
            # Bekannte Pfade
            r"C:\Users\Nerd\AppData\Local\AnthropicClaude\app-0.10.14\ultimate_plus_plus_legal.db",
            str(Path.home() / "Desktop/OpenLegalData/ultimate_plus_plus_legal.db"),
            
            # Relative Pfade
            "ultimate_plus_plus_legal.db",
            "german_legal.db",
        ]
        
        # Existierende Pfade finden
        existing_paths = {}
        for path in possible_paths:
            if os.path.exists(path):
                existing_paths[path] = os.path.getsize(path)
        
        return existing_paths


# Globale Konfiguration
config = AppConfig.load()


def get_config() -> AppConfig:
    """Gibt die globale Konfiguration zurück"""
    return config


def find_database() -> Optional[str]:
    """Findet die beste verfügbare Datenbank"""
    existing_dbs = config.get_database_paths()
    
    if not existing_dbs:
        return None
    
    # Größte Datenbank nehmen (vermutlich die vollständigste)
    best_db = max(existing_dbs.items(), key=lambda x: x[1])
    return best_db[0]


# Konstanten für Rechtsgebiete
RECHTSGEBIETE = [
    "Zivilrecht",
    "Arbeitsrecht", 
    "Sozialrecht",
    "Verwaltungsrecht",
    "Steuerrecht",
    "Verfassungsrecht",
    "Strafrecht",
    "Öffentliches Recht"
]

# Gerichtstypen
GERICHTSTYPEN = [
    "Amtsgericht",
    "Landgericht",
    "Oberlandesgericht",
    "Bundesgerichtshof",
    "Arbeitsgericht",
    "Landesarbeitsgericht",
    "Bundesarbeitsgericht",
    "Sozialgericht",
    "Landessozialgericht",
    "Bundessozialgericht",
    "Verwaltungsgericht",
    "Oberverwaltungsgericht",
    "Bundesverwaltungsgericht",
    "Finanzgericht",
    "Bundesfinanzhof",
    "Verfassungsgerichtshof",
    "Bundesverfassungsgericht"
]
