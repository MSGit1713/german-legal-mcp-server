#!/usr/bin/env python3
"""
🗄️ CREATE TEST DATABASE
========================

Erstellt eine Test-Datenbank für German Legal MCP Server
"""

import sqlite3
import os
from pathlib import Path


def create_test_database():
    """Erstellt eine Test-Datenbank mit Beispieldaten"""
    
    db_path = Path("C:/Users/Nerd/Desktop/german_legal_mcp/data/test_legal.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Erstelle Test-Datenbank: {db_path}")
    
    # Datenbank erstellen
    conn = sqlite3.connect(db_path)
    
    # Tabellen erstellen
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
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
        CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts USING fts5(
            content_clean,
            court_name,
            file_number,
            ecli,
            rechtsgebiet,
            content='cases',
            content_rowid='id'
        )
    """)
    
    # Testdaten
    test_cases = [
        (
            1, 'bgh-mietrecht-2022', 'Bundesgerichtshof', 'bgh',
            'Ordentliche Gerichtsbarkeit', 'Zivilrecht', 'Revision',
            'VIII ZR 123/22', '2022-03-15', 'Urteil',
            'ECLI:DE:BGH:2022:150322UVIIIZR123.22.0',
            '<h2>Tenor</h2><p>Die Revision wird zurückgewiesen.</p><p>Mietrecht: Bei fristloser Kündigung wegen Zahlungsverzug muss eine Abmahnung erfolgen.</p>',
            'Tenor: Die Revision wird zurückgewiesen. Mietrecht: Bei fristloser Kündigung wegen Zahlungsverzug muss eine Abmahnung erfolgen.',
            150, 2022, '2022-03-15', '2022-03-15'
        ),
        (
            2, 'bag-arbeitszeit-2023', 'Bundesarbeitsgericht', 'bag',
            'Arbeitsgerichtsbarkeit', 'Arbeitsrecht', 'Revision',
            '5 AZR 456/23', '2023-05-20', 'Urteil',
            'ECLI:DE:BAG:2023:200523U5AZR456.23.0',
            '<h2>Leitsatz</h2><p>Arbeitszeit: Überstunden müssen ausdrücklich angeordnet oder genehmigt werden.</p>',
            'Leitsatz: Arbeitszeit: Überstunden müssen ausdrücklich angeordnet oder genehmigt werden.',
            120, 2023, '2023-05-20', '2023-05-20'
        ),
        (
            3, 'bsg-sozialrecht-2023', 'Bundessozialgericht', 'bsg',
            'Sozialgerichtsbareit', 'Sozialrecht', 'Revision',
            'B 1 KR 789/23', '2023-08-10', 'Urteil',
            'ECLI:DE:BSG:2023:100823UB1KR789.23.0',
            '<p>Krankenversicherung: Behandlungskosten für alternative Heilmethoden sind grundsätzlich nicht erstattungsfähig.</p>',
            'Krankenversicherung: Behandlungskosten für alternative Heilmethoden sind grundsätzlich nicht erstattungsfähig.',
            95, 2023, '2023-08-10', '2023-08-10'
        ),
        (
            4, 'bverwg-verwaltungsrecht-2022', 'Bundesverwaltungsgericht', 'bverwg',
            'Verwaltungsgerichtsbarkeit', 'Verwaltungsrecht', 'Revision',
            '6 C 12.22', '2022-11-25', 'Urteil',
            'ECLI:DE:BVERWG:2022:251122U6C12.22.0',
            '<h2>Tenor</h2><p>Die Revision wird zurückgewiesen.</p><p>Baurecht: Eine Baugenehmigung kann nur erteilt werden, wenn alle baurechtlichen Voraussetzungen erfüllt sind.</p>',
            'Tenor: Die Revision wird zurückgewiesen. Baurecht: Eine Baugenehmigung kann nur erteilt werden, wenn alle baurechtlichen Voraussetzungen erfüllt sind.',
            180, 2022, '2022-11-25', '2022-11-25'
        ),
        (
            5, 'lg-muenchen-zivilrecht-2024', 'Landgericht München I', 'lg-muenchen',
            'Ordentliche Gerichtsbarkeit', 'Zivilrecht', 'Berufung',
            '1 O 1234/24', '2024-01-15', 'Urteil',
            'ECLI:DE:LGM:2024:150124U1O1234.24.0',
            '<p>Kaufrecht: Der Verkäufer haftet für Mängel, die zum Zeitpunkt des Gefahrübergangs bereits vorhanden waren.</p>',
            'Kaufrecht: Der Verkäufer haftet für Mängel, die zum Zeitpunkt des Gefahrübergangs bereits vorhanden waren.',
            110, 2024, '2024-01-15', '2024-01-15'
        )
    ]
    
    # Daten einfügen
    conn.executemany("""
        INSERT OR REPLACE INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, test_cases)
    
    # FTS-Index füllen
    for case in test_cases:
        conn.execute("""
            INSERT OR REPLACE INTO cases_fts VALUES (?, ?, ?, ?, ?)
        """, (case[12], case[2], case[7], case[10], case[5]))
    
    conn.commit()
    conn.close()
    
    print(f"OK: Test-Datenbank erstellt mit {len(test_cases)} Fällen")
    print(f"Pfad: {db_path}")
    
    return str(db_path)


if __name__ == "__main__":
    create_test_database()
