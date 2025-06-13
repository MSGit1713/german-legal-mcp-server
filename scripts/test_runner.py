#!/usr/bin/env python3
"""
🧪 TEST RUNNER
==============

Test-Runner für German Legal MCP Server
"""

import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Führt alle Tests aus"""
    print("🧪 German Legal MCP Server - Test Suite")
    print("=" * 50)
    
    # Basis-Tests
    print("📋 Führe Unit Tests aus...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short",
        "-m", "not slow"
    ])
    
    if result.returncode != 0:
        print("❌ Unit Tests fehlgeschlagen")
        return False
    
    print("✅ Unit Tests erfolgreich")
    
    # Integration Tests (falls vorhanden)
    if Path("tests/integration").exists():
        print("\n📋 Führe Integration Tests aus...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/integration/", 
            "-v",
            "--tb=short"
        ])
        
        if result.returncode != 0:
            print("❌ Integration Tests fehlgeschlagen")
            return False
        
        print("✅ Integration Tests erfolgreich")
    
    return True


def run_coverage():
    """Führt Coverage-Tests aus"""
    print("\n📊 Führe Coverage-Analyse aus...")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=src/german_legal_mcp",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=80"
    ])
    
    if result.returncode == 0:
        print("✅ Coverage-Ziel erreicht")
        print("📄 HTML-Report: htmlcov/index.html")
    else:
        print("⚠️ Coverage unter Zielwert")
    
    return result.returncode == 0


def run_linting():
    """Führt Code-Linting aus"""
    print("\n🔍 Führe Code-Linting aus...")
    
    # Black
    print("  Black (Formatierung)...")
    result = subprocess.run([
        sys.executable, "-m", "black", 
        "--check", 
        "src/", "tests/"
    ])
    
    if result.returncode != 0:
        print("  ❌ Black-Formatierung fehlgeschlagen")
        print("  💡 Führe aus: black src/ tests/")
        return False
    
    # isort
    print("  isort (Import-Sortierung)...")
    result = subprocess.run([
        sys.executable, "-m", "isort", 
        "--check-only", 
        "src/", "tests/"
    ])
    
    if result.returncode != 0:
        print("  ❌ isort-Prüfung fehlgeschlagen")
        print("  💡 Führe aus: isort src/ tests/")
        return False
    
    # mypy (falls verfügbar)
    try:
        print("  mypy (Type-Checking)...")
        result = subprocess.run([
            sys.executable, "-m", "mypy", 
            "src/german_legal_mcp/"
        ])
        
        if result.returncode != 0:
            print("  ⚠️ Type-Checking-Warnungen vorhanden")
        else:
            print("  ✅ Type-Checking erfolgreich")
    except:
        print("  ℹ️ mypy nicht verfügbar")
    
    print("✅ Linting abgeschlossen")
    return True


def main():
    """Hauptfunktion"""
    success = True
    
    # Tests
    if not run_tests():
        success = False
    
    # Coverage (optional)
    if "--coverage" in sys.argv:
        if not run_coverage():
            print("⚠️ Coverage-Test nicht bestanden")
    
    # Linting (optional)
    if "--lint" in sys.argv:
        if not run_linting():
            success = False
    
    # Ergebnis
    if success:
        print("\n🎉 Alle Tests erfolgreich!")
        return 0
    else:
        print("\n❌ Einige Tests fehlgeschlagen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
