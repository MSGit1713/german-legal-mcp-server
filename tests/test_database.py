#!/usr/bin/env python3
"""
🧪 DATABASE TESTS
=================

Tests für DatabaseManager
"""

import pytest
from german_legal_mcp.database import DatabaseManager
from german_legal_mcp.models import LegalCase


class TestDatabaseManager:
    """Tests für DatabaseManager"""
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, sample_database: DatabaseManager):
        """Test Datenbank-Gesundheitscheck"""
        health = await sample_database.check_database_health()
        
        assert health["status"] == "healthy"
        assert health["file_exists"] is True
        assert health["total_cases"] == 3
        assert health["fts_enabled"] is True
        assert len(health["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_case_by_id(self, sample_database: DatabaseManager):
        """Test Fall-Abfrage nach ID"""
        case = await sample_database.get_case_by_id(1)
        
        assert case is not None
        assert case.id == 1
        assert case.court_name == "Bundesgerichtshof"
        assert case.rechtsgebiet == "Zivilrecht"
        assert case.file_number == "VIII ZR 123/20"
    
    @pytest.mark.asyncio
    async def test_get_case_by_slug(self, sample_database: DatabaseManager):
        """Test Fall-Abfrage nach Slug"""
        case = await sample_database.get_case_by_slug("test-case-2")
        
        assert case is not None
        assert case.id == 2
        assert case.court_name == "Landesarbeitsgericht München"
        assert case.rechtsgebiet == "Arbeitsrecht"
    
    @pytest.mark.asyncio
    async def test_get_cases_by_ids(self, sample_database: DatabaseManager):
        """Test Multiple Fall-Abfrage"""
        cases = await sample_database.get_cases_by_ids([1, 3])
        
        assert len(cases) == 2
        assert cases[0].id in [1, 3]
        assert cases[1].id in [1, 3]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_case(self, sample_database: DatabaseManager):
        """Test nicht-existierenden Fall"""
        case = await sample_database.get_case_by_id(999)
        assert case is None
    
    @pytest.mark.asyncio
    async def test_database_statistics(self, sample_database: DatabaseManager):
        """Test Datenbankstatistiken"""
        stats = await sample_database.get_database_statistics()
        
        assert stats.total_cases == 3
        assert "Zivilrecht" in stats.rechtsgebiete
        assert "Arbeitsrecht" in stats.rechtsgebiete
        assert stats.rechtsgebiete["Zivilrecht"] == 2
        assert stats.rechtsgebiete["Arbeitsrecht"] == 1
    
    @pytest.mark.asyncio
    async def test_get_table_info(self, sample_database: DatabaseManager):
        """Test Tabelleninformationen"""
        table_info = await sample_database.get_table_info()
        
        assert "cases" in table_info
        assert "cases_fts" in table_info
        assert table_info["cases"]["row_count"] == 3
        assert table_info["cases_fts"]["type"] == "fts"
    
    @pytest.mark.asyncio
    async def test_optimize_database(self, sample_database: DatabaseManager):
        """Test Datenbankoptimierung"""
        result = await sample_database.optimize_database()
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "operations" in result
        assert "errors" in result
