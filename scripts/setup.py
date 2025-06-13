#!/usr/bin/env python3
"""
🛠️ SETUP SCRIPT
================

Setup-Script für German Legal MCP Server
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_python_version():
    """Prüft Python-Version"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ erforderlich")
        sys.exit(1)
    print(f"OK: Python {sys.version_info.major}.{sys.version_info.minor}")


def create_directories():
    """Erstellt benötigte Verzeichnisse"""
    dirs = ["data", "logs", "backups"]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"OK: Verzeichnis erstellt: {dir_name}")


def install_dependencies():
    """Installiert Dependencies"""
    print("Installing Dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], check=True)
        print("OK: Dependencies installiert")
    except subprocess.CalledProcessError:
        print("ERROR: Fehler beim Installieren der Dependencies")
        sys.exit(1)


def setup_config():
    """Richtet Konfiguration ein"""
    config_src = Path("config/.env.example")
    config_dst = Path(".env")
    
    if not config_dst.exists() and config_src.exists():
        shutil.copy(config_src, config_dst)
        print("OK: Konfigurationsdatei erstellt: .env")
    else:
        print("INFO: Konfigurationsdatei bereits vorhanden")


def find_database():
    """Sucht nach vorhandenen Datenbanken"""
    possible_paths = [
        r"C:\Users\Nerd\AppData\Local\AnthropicClaude\app-0.10.14\ultimate_plus_plus_legal.db",
        "ultimate_plus_plus_legal.db",
        "german_legal.db",
        "data/german_legal.db"
    ]
    
    found_dbs = []
    for path in possible_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            found_dbs.append((path, size))
    
    if found_dbs:
        print("\nGefundene Datenbanken:")
        for path, size in found_dbs:
            size_mb = size / (1024 * 1024)
            print(f"  - {path} ({size_mb:.1f} MB)")
        
        # Größte Datenbank als Standard verwenden
        best_db = max(found_dbs, key=lambda x: x[1])
        
        # In .env eintragen
        env_file = Path(".env")
        if env_file.exists():
            content = env_file.read_text()
            # DB_PATH aktualisieren
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('DB_PATH='):
                    lines[i] = f'DB_PATH={best_db[0]}'
                    break
            
            env_file.write_text('\n'.join(lines))
            print(f"OK: Datenbankpfad konfiguriert: {best_db[0]}")
    else:
        print("WARNING: Keine Datenbank gefunden")
        print("INFO: Bitte laden Sie eine OpenLegalData-Datenbank herunter")


def test_installation():
    """Testet die Installation"""
    print("\nTeste Installation...")
    
    try:
        import german_legal_mcp
        print("OK: Paket importiert")
        
        from german_legal_mcp.config import get_config
        config = get_config()
        print("OK: Konfiguration geladen")
        
        # Datenbank-Test falls vorhanden
        if os.path.exists(config.database.path):
            from german_legal_mcp.database import DatabaseManager
            db = DatabaseManager()
            print("OK: Datenbankverbindung erfolgreich")
        else:
            print("WARNING: Datenbank nicht gefunden (normal bei Erstinstallation)")
            
    except Exception as e:
        print(f"ERROR: Installationstest fehlgeschlagen: {e}")
        return False
    
    return True


def main():
    """Hauptfunktion"""
    print("German Legal MCP Server Setup")
    print("=" * 40)
    
    # Schritte ausführen
    check_python_version()
    create_directories()
    install_dependencies()
    setup_config()
    find_database()
    
    # Test
    if test_installation():
        print("\nOK: Setup erfolgreich abgeschlossen!")
        print("\nNaechste Schritte:")
        print("1. Pruefen Sie die .env Datei")
        print("2. Stellen Sie sicher, dass eine Datenbank verfuegbar ist")
        print("3. Starten Sie den Server: python -m german_legal_mcp.main")
    else:
        print("\nERROR: Setup fehlgeschlagen")
        sys.exit(1)


if __name__ == "__main__":
    main()
