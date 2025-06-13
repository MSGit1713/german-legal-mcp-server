#!/usr/bin/env python3
"""
🗄️ DATABASE MODULE
==================

Datenbankverbindung und -operationen für German Legal MCP Server
"""

import sqlite3
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from .config import get_config, find_database
from .models import LegalCase, DatabaseStats
from .utils import HTMLProcessor, PerformanceHelper


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Verwaltet Datenbankverbindungen und -operationen"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = get_config()
        self.db_path = db_path or find_database()
        self.connection_pool = {}
        self._stats_cache = None
        self._stats_cache_time = None
        
        if not self.db_path:
            raise ValueError("Keine Datenbank gefunden. Bitte Pfad in Konfiguration angeben.")
        
        logger.info(f"🗄️ Verwende Datenbank: {self.db_path}")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[sqlite3.Connection, None]:
        """Async Context Manager für Datenbankverbindungen"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Performance-Optimierungen
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute(f"PRAGMA cache_size={self.config.database.cache_size}")
            conn.execute("PRAGMA temp_store=memory")
            
            yield conn
            
        except Exception as e:
            logger.error(f"❌ Datenbankfehler: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Prüft Datenbankzustand"""
        health_info = {
            "status": "unknown",
            "file_exists": False,
            "file_size": 0,
            "tables": [],
            "total_cases": 0,
            "fts_enabled": False,
            "errors": []
        }
        
        try:
            # Datei-Existenz
            db_file = Path(self.db_path)
            health_info["file_exists"] = db_file.exists()
            
            if health_info["file_exists"]:
                health_info["file_size"] = db_file.stat().st_size
                
                async with self.get_connection() as conn:
                    # Tabellen prüfen
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' 
                        ORDER BY name
                    """)
                    health_info["tables"] = [row["name"] for row in cursor.fetchall()]
                    
                    # Cases-Tabelle prüfen
                    if "cases" in health_info["tables"]:
                        cursor = conn.execute("SELECT COUNT(*) as count FROM cases")
                        health_info["total_cases"] = cursor.fetchone()["count"]
                    
                    # FTS prüfen
                    if "cases_fts" in health_info["tables"]:
                        try:
                            cursor = conn.execute("SELECT COUNT(*) FROM cases_fts")
                            health_info["fts_enabled"] = True
                        except sqlite3.OperationalError:
                            health_info["fts_enabled"] = False
                            health_info["errors"].append("FTS-Index nicht verfügbar")
                    
                    health_info["status"] = "healthy"
            else:
                health_info["status"] = "missing"
                health_info["errors"].append(f"Datenbankdatei nicht gefunden: {self.db_path}")
                
        except Exception as e:
            health_info["status"] = "error"
            health_info["errors"].append(str(e))
        
        return health_info
    
    async def get_table_info(self) -> Dict[str, Dict[str, Any]]:
        """Gibt Informationen über alle Tabellen zurück"""
        table_info = {}
        
        try:
            async with self.get_connection() as conn:
                # Alle Tabellen
                cursor = conn.execute("""
                    SELECT name, sql FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                
                for row in cursor.fetchall():
                    table_name = row["name"]
                    
                    # Zeilen zählen
                    try:
                        count_cursor = conn.execute(f"SELECT COUNT(*) as count FROM [{table_name}]")
                        row_count = count_cursor.fetchone()["count"]
                    except:
                        row_count = 0
                    
                    table_info[table_name] = {
                        "sql": row["sql"],
                        "row_count": row_count,
                        "type": "fts" if "fts" in table_name else "regular"
                    }
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Tabelleninfo: {e}")
        
        return table_info
    
    @PerformanceHelper.measure_time
    async def get_cases_by_ids(self, case_ids: List[int]) -> List[LegalCase]:
        """Lädt Fälle anhand ihrer IDs"""
        if not case_ids:
            return []
        
        cases = []
        
        try:
            async with self.get_connection() as conn:
                placeholders = ",".join("?" * len(case_ids))
                cursor = conn.execute(f"""
                    SELECT * FROM cases 
                    WHERE id IN ({placeholders})
                    ORDER BY year DESC, date DESC
                """, case_ids)
                
                for row in cursor.fetchall():
                    case = LegalCase.from_db_row(row)
                    # Leitsatz extrahieren
                    if case.content_raw:
                        case.leitsatz = HTMLProcessor.extract_leitsatz(
                            case.content_raw, 
                            self.config.search.leitsatz_max_length
                        )
                    cases.append(case)
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Fälle: {e}")
        
        return cases
    
    async def get_case_by_id(self, case_id: int) -> Optional[LegalCase]:
        """Lädt einen einzelnen Fall"""
        cases = await self.get_cases_by_ids([case_id])
        return cases[0] if cases else None
    
    async def get_case_by_slug(self, slug: str) -> Optional[LegalCase]:
        """Lädt Fall anhand des Slugs"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM cases WHERE slug = ?", (slug,))
                row = cursor.fetchone()
                
                if row:
                    case = LegalCase.from_db_row(row)
                    if case.content_raw:
                        case.leitsatz = HTMLProcessor.extract_leitsatz(
                            case.content_raw,
                            self.config.search.leitsatz_max_length
                        )
                    return case
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Falls {slug}: {e}")
        
        return None
    
    async def get_database_statistics(self, force_refresh: bool = False) -> DatabaseStats:
        """Erstellt umfassende Datenbankstatistiken"""
        
        # Cache prüfen (5 Minuten)
        if (not force_refresh and self._stats_cache and self._stats_cache_time and 
            (datetime.now() - self._stats_cache_time).seconds < 300):
            return self._stats_cache
        
        logger.info("📊 Erstelle Datenbankstatistiken...")
        
        try:
            async with self.get_connection() as conn:
                stats = DatabaseStats(total_cases=0)
                
                # Gesamtzahl
                cursor = conn.execute("SELECT COUNT(*) as count FROM cases")
                stats.total_cases = cursor.fetchone()["count"]
                
                if stats.total_cases == 0:
                    return stats
                
                # Rechtsgebiete
                cursor = conn.execute("""
                    SELECT rechtsgebiet, COUNT(*) as count 
                    FROM cases 
                    WHERE rechtsgebiet IS NOT NULL AND rechtsgebiet != ''
                    GROUP BY rechtsgebiet 
                    ORDER BY count DESC
                    LIMIT 15
                """)
                stats.rechtsgebiete = {row["rechtsgebiet"]: row["count"] for row in cursor.fetchall()}
                
                # Top Gerichte
                cursor = conn.execute("""
                    SELECT court_name, COUNT(*) as count 
                    FROM cases 
                    WHERE court_name IS NOT NULL AND court_name != ''
                    GROUP BY court_name 
                    ORDER BY count DESC
                    LIMIT 15
                """)
                stats.top_courts = {row["court_name"]: row["count"] for row in cursor.fetchall()}
                
                # Jahre
                cursor = conn.execute("""
                    SELECT year, COUNT(*) as count 
                    FROM cases 
                    WHERE year IS NOT NULL AND year >= 2000
                    GROUP BY year 
                    ORDER BY year DESC
                    LIMIT 15
                """)
                stats.years = {row["year"]: row["count"] for row in cursor.fetchall()}
                
                # Content-Statistiken
                cursor = conn.execute("""
                    SELECT 
                        AVG(CASE WHEN content_length > 0 THEN content_length END) as avg_length,
                        MIN(CASE WHEN content_length > 0 THEN content_length END) as min_length,
                        MAX(content_length) as max_length,
                        COUNT(CASE WHEN content_length > 100 THEN 1 END) as substantial_content
                    FROM cases
                """)
                content_row = cursor.fetchone()
                stats.content_stats = {
                    "durchschnittliche_laenge": int(content_row["avg_length"]) if content_row["avg_length"] else 0,
                    "minimale_laenge": content_row["min_length"] or 0,
                    "maximale_laenge": content_row["max_length"] or 0,
                    "mit_inhalt": content_row["substantial_content"] or 0
                }
                
                # Datenqualität
                cursor = conn.execute("""
                    SELECT 
                        COUNT(CASE WHEN ecli IS NOT NULL AND ecli != '' THEN 1 END) as with_ecli,
                        COUNT(CASE WHEN date IS NOT NULL AND date != '' THEN 1 END) as with_date,
                        COUNT(CASE WHEN file_number IS NOT NULL AND file_number != '' THEN 1 END) as with_file_number
                    FROM cases
                """)
                quality_row = cursor.fetchone()
                total = stats.total_cases
                stats.data_quality = {
                    "mit_ecli": f"{quality_row['with_ecli']} ({quality_row['with_ecli']/total*100:.1f}%)" if total > 0 else "0",
                    "mit_datum": f"{quality_row['with_date']} ({quality_row['with_date']/total*100:.1f}%)" if total > 0 else "0",
                    "mit_aktenzeichen": f"{quality_row['with_file_number']} ({quality_row['with_file_number']/total*100:.1f}%)" if total > 0 else "0"
                }
                
                # Cache aktualisieren
                self._stats_cache = stats
                self._stats_cache_time = datetime.now()
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Statistik-Erstellung: {e}")
            return DatabaseStats(total_cases=0)
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Optimiert die Datenbank"""
        optimization_results = {
            "success": False,
            "operations": [],
            "errors": []
        }
        
        try:
            async with self.get_connection() as conn:
                # ANALYZE für bessere Query-Planung
                try:
                    conn.execute("ANALYZE")
                    optimization_results["operations"].append("ANALYZE ausgeführt")
                except Exception as e:
                    optimization_results["errors"].append(f"ANALYZE fehlgeschlagen: {e}")
                
                # VACUUM für Speicheroptimierung (nur wenn nötig)
                try:
                    cursor = conn.execute("PRAGMA page_count")
                    page_count = cursor.fetchone()[0]
                    cursor = conn.execute("PRAGMA freelist_count")
                    freelist_count = cursor.fetchone()[0]
                    
                    if freelist_count > page_count * 0.1:  # > 10% freie Seiten
                        conn.execute("VACUUM")
                        optimization_results["operations"].append("VACUUM ausgeführt")
                except Exception as e:
                    optimization_results["errors"].append(f"VACUUM fehlgeschlagen: {e}")
                
                # FTS-Index optimieren
                try:
                    conn.execute("INSERT INTO cases_fts(cases_fts) VALUES('optimize')")
                    optimization_results["operations"].append("FTS-Index optimiert")
                except Exception as e:
                    optimization_results["errors"].append(f"FTS-Optimierung fehlgeschlagen: {e}")
                
                optimization_results["success"] = len(optimization_results["errors"]) == 0
                
        except Exception as e:
            optimization_results["errors"].append(f"Allgemeiner Fehler: {e}")
        
        return optimization_results
