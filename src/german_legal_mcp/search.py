#!/usr/bin/env python3
"""
🔍 SEARCH MODULE
================

Erweiterte Suchfunktionen für German Legal MCP Server
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from .config import get_config
from .models import SearchQuery, SearchResult, LegalCase
from .database import DatabaseManager
from .utils import FTSQueryBuilder, HTMLProcessor, TextProcessor, ValidationHelper


logger = logging.getLogger(__name__)


class SearchCache:
    """LRU-Cache für Suchergebnisse"""
    
    def __init__(self, max_size: int = 50, ttl: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[List[SearchResult]]:
        """Lädt Ergebnis aus Cache"""
        if key in self.cache:
            # TTL prüfen
            if datetime.now() - self.access_times[key] < timedelta(seconds=self.ttl):
                self.access_times[key] = datetime.now()
                self.hits += 1
                return self.cache[key]
            else:
                # Abgelaufen
                del self.cache[key]
                del self.access_times[key]
        
        self.misses += 1
        return None
    
    def put(self, key: str, value: List[SearchResult]) -> None:
        """Speichert Ergebnis im Cache"""
        # LRU-Eviction falls Cache voll
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = datetime.now()
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache-Statistiken"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 1),
            "cache_size": len(self.cache),
            "max_size": self.max_size
        }
    
    def clear(self) -> None:
        """Leert Cache"""
        self.cache.clear()
        self.access_times.clear()


class LegalSearchEngine:
    """Erweiterte Suchmaschine für Rechtsprechung"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = get_config()
        self.cache = SearchCache(
            max_size=self.config.search.cache_size,
            ttl=self.config.search.cache_ttl
        )
        
    async def search_cases(self, query: SearchQuery) -> List[SearchResult]:
        """Hauptsuchfunktion für Rechtsfälle"""
        
        # Validierung
        validation_errors = query.validate()
        if validation_errors:
            logger.warning(f"🚫 Validierungsfehler: {validation_errors}")
            return []
        
        # Cache prüfen
        cache_key = query.to_cache_key()
        cached_results = self.cache.get(cache_key)
        if cached_results is not None:
            logger.debug(f"✅ Cache-Hit für: {query.query[:50]}")
            return cached_results
        
        logger.info(f"🔍 Suche: '{query.query}' | Filter: {query.rechtsgebiet}, {query.gericht}, {query.jahr_von}-{query.jahr_bis}")
        
        try:
            results = await self._execute_search(query)
            
            # In Cache speichern
            self.cache.put(cache_key, results)
            
            logger.info(f"✅ {len(results)} Ergebnisse gefunden")
            return results
            
        except Exception as e:
            logger.error(f"❌ Suchfehler: {e}")
            return []
    
    async def _execute_search(self, query: SearchQuery) -> List[SearchResult]:
        """Führt die eigentliche Datenbanksuche aus"""
        
        # FTS-Query erstellen
        fts_query = FTSQueryBuilder.build_fts_query(query.query)
        search_terms = FTSQueryBuilder.extract_search_terms(query.query)
        
        async with self.db_manager.get_connection() as conn:
            # SQL mit Filtern aufbauen
            sql_parts = ["""
                SELECT c.*, 
                       bm25(cases_fts) as relevance_score,
                       snippet(cases_fts, 0, '<mark>', '</mark>', '...', ?) as snippet
                FROM cases_fts 
                JOIN cases c ON cases_fts.rowid = c.id
                WHERE cases_fts MATCH ?
            """]
            
            params = [self.config.search.snippet_length, fts_query]
            
            # Filter hinzufügen
            if query.rechtsgebiet:
                sql_parts.append("AND c.rechtsgebiet LIKE ?")
                params.append(f"%{query.rechtsgebiet}%")
            
            if query.gericht:
                sql_parts.append("AND (c.court_name LIKE ? OR c.jurisdiction LIKE ?)")
                params.extend([f"%{query.gericht}%", f"%{query.gericht}%"])
            
            if query.jahr_von:
                sql_parts.append("AND c.year >= ?")
                params.append(query.jahr_von)
            
            if query.jahr_bis:
                sql_parts.append("AND c.year <= ?")
                params.append(query.jahr_bis)
            
            # Sortierung und Limit
            sql_parts.append("ORDER BY relevance_score ASC, c.year DESC, c.date DESC")
            sql_parts.append("LIMIT ?")
            params.append(query.limit)
            
            sql = " ".join(sql_parts)
            
            cursor = conn.execute(sql, params)
            results = []
            
            for row in cursor.fetchall():
                # LegalCase erstellen
                case = LegalCase.from_db_row(row)
                
                # Leitsatz extrahieren
                if case.content_raw:
                    case.leitsatz = HTMLProcessor.extract_leitsatz(
                        case.content_raw,
                        self.config.search.leitsatz_max_length
                    )
                
                # SearchResult erstellen
                search_result = SearchResult(
                    case=case,
                    relevance_score=float(row[-2]),  # relevance_score
                    snippet=row[-1] or "",  # snippet
                    highlighted_terms=search_terms
                )
                
                results.append(search_result)
            
            return results
    
    async def search_similar_cases(self, case_id: int, limit: int = 10) -> List[SearchResult]:
        """Findet ähnliche Fälle basierend auf einem gegebenen Fall"""
        
        # Ursprungsfall laden
        case = await self.db_manager.get_case_by_id(case_id)
        if not case:
            return []
        
        # Suchbegriffe aus dem Fall extrahieren
        search_terms = []
        
        # Aktenzeichen-Teile
        if case.file_number:
            parts = case.file_number.split()
            search_terms.extend([part for part in parts if len(part) > 2])
        
        # Gericht
        if case.court_name:
            search_terms.append(case.court_name.split()[0])  # Ersten Teil des Gerichtsnamens
        
        # Rechtsgebiet
        if case.rechtsgebiet:
            search_terms.append(case.rechtsgebiet)
        
        # Content-basierte Begriffe (aus Leitsatz)
        if case.leitsatz:
            content_terms = TextProcessor.extract_citations(case.leitsatz)
            search_terms.extend(content_terms[:3])  # Maximal 3 Zitate
        
        if not search_terms:
            return []
        
        # Suche mit kombinierten Begriffen
        query_str = " ".join(search_terms[:5])  # Maximal 5 Begriffe
        query = SearchQuery(
            query=query_str,
            rechtsgebiet=case.rechtsgebiet,
            limit=limit + 1  # +1 weil ursprünglicher Fall entfernt wird
        )
        
        results = await self.search_cases(query)
        
        # Ursprungsfall aus Ergebnissen entfernen
        filtered_results = [r for r in results if r.case.id != case_id]
        
        return filtered_results[:limit]
    
    async def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Generiert Suchvorschläge basierend auf häufigen Begriffen"""
        
        if len(partial_query) < 3:
            return []
        
        suggestions = []
        
        try:
            async with self.db_manager.get_connection() as conn:
                # Häufige Begriffe in Aktenzeichen
                cursor = conn.execute("""
                    SELECT DISTINCT file_number
                    FROM cases 
                    WHERE file_number LIKE ? 
                    AND file_number IS NOT NULL
                    ORDER BY year DESC
                    LIMIT 10
                """, (f"%{partial_query}%",))
                
                for row in cursor.fetchall():
                    if row["file_number"]:
                        suggestions.append(row["file_number"])
                
                # Häufige Gerichte
                cursor = conn.execute("""
                    SELECT DISTINCT court_name, COUNT(*) as count
                    FROM cases 
                    WHERE court_name LIKE ? 
                    AND court_name IS NOT NULL
                    GROUP BY court_name
                    ORDER BY count DESC
                    LIMIT 5
                """, (f"%{partial_query}%",))
                
                for row in cursor.fetchall():
                    if row["court_name"]:
                        suggestions.append(row["court_name"])
        
        except Exception as e:
            logger.error(f"❌ Fehler bei Suchvorschlägen: {e}")
        
        # Duplikate entfernen und sortieren
        unique_suggestions = list(set(suggestions))
        unique_suggestions.sort(key=len)  # Kürzere zuerst
        
        return unique_suggestions[:10]
    
    async def advanced_search(self, 
                            query: str,
                            filters: Dict[str, Any]) -> List[SearchResult]:
        """Erweiterte Suche mit komplexen Filtern"""
        
        # Basis-Query erstellen
        search_query = SearchQuery(
            query=ValidationHelper.sanitize_search_term(query),
            rechtsgebiet=filters.get("rechtsgebiet"),
            gericht=filters.get("gericht"),
            jahr_von=ValidationHelper.validate_year(filters.get("jahr_von")),
            jahr_bis=ValidationHelper.validate_year(filters.get("jahr_bis")),
            limit=ValidationHelper.validate_limit(filters.get("limit", 20))
        )
        
        # Zusätzliche Filter verarbeiten
        additional_filters = {}
        
        if filters.get("aktenzeichen"):
            additional_filters["file_number"] = filters["aktenzeichen"]
        
        if filters.get("ecli"):
            additional_filters["ecli"] = filters["ecli"]
        
        if filters.get("instanz"):
            additional_filters["level_of_appeal"] = filters["instanz"]
        
        # Erweiterte Suche ausführen
        return await self._execute_advanced_search(search_query, additional_filters)
    
    async def _execute_advanced_search(self, 
                                     query: SearchQuery, 
                                     additional_filters: Dict[str, str]) -> List[SearchResult]:
        """Führt erweiterte Suche mit zusätzlichen Filtern aus"""
        
        fts_query = FTSQueryBuilder.build_fts_query(query.query)
        search_terms = FTSQueryBuilder.extract_search_terms(query.query)
        
        async with self.db_manager.get_connection() as conn:
            sql_parts = ["""
                SELECT c.*, 
                       bm25(cases_fts) as relevance_score,
                       snippet(cases_fts, 0, '<mark>', '</mark>', '...', ?) as snippet
                FROM cases_fts 
                JOIN cases c ON cases_fts.rowid = c.id
                WHERE cases_fts MATCH ?
            """]
            
            params = [self.config.search.snippet_length, fts_query]
            
            # Standard-Filter
            if query.rechtsgebiet:
                sql_parts.append("AND c.rechtsgebiet LIKE ?")
                params.append(f"%{query.rechtsgebiet}%")
            
            if query.gericht:
                sql_parts.append("AND c.court_name LIKE ?")
                params.append(f"%{query.gericht}%")
            
            if query.jahr_von:
                sql_parts.append("AND c.year >= ?")
                params.append(query.jahr_von)
            
            if query.jahr_bis:
                sql_parts.append("AND c.year <= ?")
                params.append(query.jahr_bis)
            
            # Zusätzliche Filter
            for field, value in additional_filters.items():
                sql_parts.append(f"AND c.{field} LIKE ?")
                params.append(f"%{value}%")
            
            sql_parts.append("ORDER BY relevance_score ASC, c.year DESC")
            sql_parts.append("LIMIT ?")
            params.append(query.limit)
            
            sql = " ".join(sql_parts)
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                case = LegalCase.from_db_row(row)
                
                if case.content_raw:
                    case.leitsatz = HTMLProcessor.extract_leitsatz(
                        case.content_raw,
                        self.config.search.leitsatz_max_length
                    )
                
                search_result = SearchResult(
                    case=case,
                    relevance_score=float(row[-2]),
                    snippet=row[-1] or "",
                    highlighted_terms=search_terms
                )
                
                results.append(search_result)
            
            return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück"""
        return self.cache.get_stats()
    
    def clear_cache(self) -> None:
        """Leert den Such-Cache"""
        self.cache.clear()
        logger.info("🗑️ Such-Cache geleert")
