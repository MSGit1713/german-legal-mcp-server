#!/usr/bin/env python3
"""
🧪 TEST CONFIGURATION
=====================

Test-Konfiguration für German Legal MCP
"""

import pytest
import asyncio
import tempfile
import sqlite3
from pathlib import Path
from typing import Generator

from german_legal_mcp.config import AppConfig
from german_legal_mcp.database import DatabaseManager
from german_legal_mcp.models import LegalCase


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Temporäre Testdatenbank"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture 
def test_config(temp_db_path: str) -> AppConfig:
    """Test-Konfiguration"""
    config = AppConfig()
    config.database.path = temp_db_path
    config.search.cache_size = 5  # Kleiner Cache für Tests
    config.server.log_level = "DEBUG"
    return config


@pytest.fixture
async def sample_database(temp_db_path: str) -> DatabaseManager:
    """Erstellt eine Beispiel-Datenbank für Tests"""
    
    # Datenbank mit Testdaten erstellen
    conn = sqlite3.connect(temp_db_path)
    
    # Tabellen erstellen
    conn.execute("""
        CREATE TABLE cases (
            id INTEGER PRIMARY KEY,
            slug TEXT,
            court_name TEXT,
            court_slug TEXT,
            jurisdiction TEXT,
            rechtsgebiet TEXT,
            level_of_appeal TEXT,
            file_number TEXT,
            date TEXT,
            type TEXT,
            ecli TEXT,
            content_raw TEXT,
            content_clean TEXT,
            content_length INTEGER,
            year INTEGER,
            created_date TEXT,
            updated_date TEXT
        )
    """)
    
    # FTS-Tabelle
    conn.execute("""
        CREATE VIRTUAL TABLE cases_fts USING fts5(
            content_clean,
            court_name,
            file_number,
            ecli,
            rechtsgebiet,
            content='cases',
            content_rowid='id'
        )
    """)
    
    # Testdaten einfügen
    test_cases = [
        (
            1, 'test-case-1', 'Bundesgerichtshof', 'bgh', 
            'Ordentliche Gerichtsbarkeit', 'Zivilrecht', 'Revision',
            'VIII ZR 123/20', '2022-03-15', 'Urteil',
            'ECLI:DE:BGH:2022:150322UVIIIZR123.20.0',
            '<h2>Tenor</h2><p>Die Revision wird zurückgewiesen.</p><p>Inhalt über Mietrecht und Kündigung.</p>',
            'Tenor: Die Revision wird zurückgewiesen. Inhalt über Mietrecht und Kündigung.',
            150, 2022, '2022-03-15', '2022-03-15'
        ),
        (
            2, 'test-case-2', 'Landesarbeitsgericht München', 'lag-muenchen',
            'Arbeitsgerichtsbarkeit', 'Arbeitsrecht', 'Berufung', 
            '4 Sa 456/21', '2023-01-20', 'Urteil',
            'ECLI:DE:LAGM:2023:200123U4SA456.21.0',
            '<h2>Leitsatz</h2><p>Arbeitszeit und Überstunden müssen korrekt abgerechnet werden.</p>',
            'Leitsatz: Arbeitszeit und Überstunden müssen korrekt abgerechnet werden.',
            120, 2023, '2023-01-20', '2023-01-20'
        ),
        (
            3, 'test-case-3', 'Amtsgericht Berlin', 'ag-berlin',
            'Ordentliche Gerichtsbarkeit', 'Zivilrecht', 'Erste Instanz',
            '12 C 789/22', '2023-06-10', 'Urteil', 
            'ECLI:DE:AGB:2023:100623U12C789.22.0',
            '<p>Urteil zu Nachbarschaftsrecht und Lärmbelästigung.</p>',
            'Urteil zu Nachbarschaftsrecht und Lärmbelästigung.',
            80, 2023, '2023-06-10', '2023-06-10'
        )
    ]
    
    conn.executemany("""
        INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, test_cases)
    
    # FTS-Index füllen
    for case in test_cases:
        conn.execute("""
            INSERT INTO cases_fts VALUES (?, ?, ?, ?, ?)
        """, (case[12], case[2], case[7], case[10], case[5]))  # content_clean, court_name, file_number, ecli, rechtsgebiet
    
    conn.commit()
    conn.close()
    
    # DatabaseManager erstellen
    db_manager = DatabaseManager(temp_db_path)
    return db_manager


@pytest.fixture
def sample_legal_case() -> LegalCase:
    """Beispiel-Rechtsfall für Tests"""
    return LegalCase(
        id=1,
        slug='test-case-1',
        court_name='Bundesgerichtshof',
        court_slug='bgh',
        jurisdiction='Ordentliche Gerichtsbarkeit',
        rechtsgebiet='Zivilrecht',
        level_of_appeal='Revision',
        file_number='VIII ZR 123/20',
        date='2022-03-15',
        type='Urteil',
        ecli='ECLI:DE:BGH:2022:150322UVIIIZR123.20.0',
        content_raw='<h2>Tenor</h2><p>Die Revision wird zurückgewiesen.</p>',
        content_clean='Tenor: Die Revision wird zurückgewiesen.',
        content_length=150,
        year=2022,
        created_date='2022-03-15',
        updated_date='2022-03-15'
    )


# Pytest-asyncio Konfiguration
pytest_plugins = ('pytest_asyncio',)
