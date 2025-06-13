#!/usr/bin/env python3
"""
🧪 SEARCH TESTS
===============

Tests für LegalSearchEngine
"""

import pytest
from german_legal_mcp.database import DatabaseManager
from german_legal_mcp.search import LegalSearchEngine
from german_legal_mcp.models import SearchQuery


class TestLegalSearchEngine:
    """Tests für LegalSearchEngine"""
    
    @pytest.fixture
    async def search_engine(self, sample_database: DatabaseManager) -> LegalSearchEngine:
        """Search Engine für Tests"""
        return LegalSearchEngine(sample_database)
    
    @pytest.mark.asyncio
    async def test_basic_search(self, search_engine: LegalSearchEngine):
        """Test Basis-Suche"""
        query = SearchQuery(query="Mietrecht", limit=10)
        results = await search_engine.search_cases(query)
        
        assert len(results) >= 1
        assert any("Mietrecht" in r.case.content_clean for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_rechtsgebiet_filter(self, search_engine: LegalSearchEngine):
        """Test Suche mit Rechtsgebiets-Filter"""
        query = SearchQuery(
            query="Urteil", 
            rechtsgebiet="Arbeitsrecht",
            limit=10
        )
        results = await search_engine.search_cases(query)
        
        assert len(results) >= 1
        assert all(r.case.rechtsgebiet == "Arbeitsrecht" for r in results)
    
    @pytest.mark.asyncio 
    async def test_search_with_court_filter(self, search_engine: LegalSearchEngine):
        """Test Suche mit Gerichts-Filter"""
        query = SearchQuery(
            query="Urteil",
            gericht="Bundesgerichtshof", 
            limit=10
        )
        results = await search_engine.search_cases(query)
        
        assert len(results) >= 1
        assert all("Bundesgerichtshof" in r.case.court_name for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_year_filter(self, search_engine: LegalSearchEngine):
        """Test Suche mit Jahres-Filter"""
        query = SearchQuery(
            query="Urteil",
            jahr_von=2023,
            jahr_bis=2023,
            limit=10
        )
        results = await search_engine.search_cases(query)
        
        assert len(results) >= 1
        assert all(r.case.year == 2023 for r in results)
    
    @pytest.mark.asyncio
    async def test_empty_search(self, search_engine: LegalSearchEngine):
        """Test leere Suche"""
        query = SearchQuery(query="", limit=10)
        results = await search_engine.search_cases(query)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_no_results_search(self, search_engine: LegalSearchEngine):
        """Test Suche ohne Ergebnisse"""
        query = SearchQuery(query="xyz123nonexistent", limit=10)
        results = await search_engine.search_cases(query)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_cache(self, search_engine: LegalSearchEngine):
        """Test Such-Cache"""
        query = SearchQuery(query="Urteil", limit=10)
        
        # Erste Suche
        results1 = await search_engine.search_cases(query)
        cache_stats1 = search_engine.get_cache_stats()
        
        # Zweite Suche (sollte aus Cache kommen)
        results2 = await search_engine.search_cases(query)
        cache_stats2 = search_engine.get_cache_stats()
        
        assert len(results1) == len(results2)
        assert cache_stats2["hits"] > cache_stats1["hits"]
    
    @pytest.mark.asyncio
    async def test_similar_cases(self, search_engine: LegalSearchEngine):
        """Test ähnliche Fälle"""
        # Suche ähnliche Fälle zu Fall 1
        results = await search_engine.search_similar_cases(case_id=1, limit=5)
        
        # Sollte andere Fälle finden, aber nicht den ursprünglichen
        assert all(r.case.id != 1 for r in results)
    
    @pytest.mark.asyncio
    async def test_search_suggestions(self, search_engine: LegalSearchEngine):
        """Test Suchvorschläge"""
        suggestions = await search_engine.get_search_suggestions("Bundes")
        
        assert isinstance(suggestions, list)
        # Sollte "Bundesgerichtshof" enthalten
        assert any("Bundesgerichtshof" in s for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_advanced_search(self, search_engine: LegalSearchEngine):
        """Test erweiterte Suche"""
        filters = {
            "rechtsgebiet": "Zivilrecht",
            "aktenzeichen": "ZR",
            "limit": 10
        }
        
        results = await search_engine.advanced_search("Urteil", filters)
        
        assert len(results) >= 1
        assert all(r.case.rechtsgebiet == "Zivilrecht" for r in results)
        assert any("ZR" in r.case.file_number for r in results if r.case.file_number)
    
    @pytest.mark.asyncio
    async def test_query_validation(self, search_engine: LegalSearchEngine):
        """Test Query-Validierung"""
        # Ungültige Query
        invalid_query = SearchQuery(query="test", limit=-1)
        errors = invalid_query.validate()
        
        assert len(errors) > 0
        assert any("Limit" in error for error in errors)
    
    def test_cache_stats(self, search_engine: LegalSearchEngine):
        """Test Cache-Statistiken"""
        stats = search_engine.get_cache_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "cache_size" in stats
        assert "max_size" in stats
    
    def test_clear_cache(self, search_engine: LegalSearchEngine):
        """Test Cache löschen"""
        # Cache mit Dummy-Daten füllen
        search_engine.cache.put("test_key", [])
        
        # Cache löschen
        search_engine.clear_cache()
        
        # Prüfen ob leer
        stats = search_engine.get_cache_stats()
        assert stats["cache_size"] == 0
