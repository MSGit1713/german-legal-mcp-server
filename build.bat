@echo off
REM German Legal MCP Server - Build Script

IF "%1"=="setup" (
    echo Setting up German Legal MCP Server...
    python scripts/setup.py
    GOTO end
)

IF "%1"=="test" (
    echo Running tests...
    python scripts/test_runner.py
    GOTO end
)

IF "%1"=="test-full" (
    echo Running full test suite...
    python scripts/test_runner.py --coverage --lint
    GOTO end
)

IF "%1"=="diagnose" (
    echo Running diagnostics...
    python scripts/diagnose.py
    GOTO end
)

IF "%1"=="start" (
    echo Starting server...
    python -m german_legal_mcp.main
    GOTO end
)

IF "%1"=="format" (
    echo Formatting code...
    black src/ tests/
    isort src/ tests/
    GOTO end
)

IF "%1"=="clean" (
    echo Cleaning build artifacts...
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul
    rmdir /s /q *.egg-info 2>nul
    rmdir /s /q __pycache__ 2>nul
    rmdir /s /q .pytest_cache 2>nul
    rmdir /s /q htmlcov 2>nul
    echo Cleaned!
    GOTO end
)

echo German Legal MCP Server - Build Commands
echo.
echo Available commands:
echo   setup      - Initial setup
echo   test       - Run tests
echo   test-full  - Run tests with coverage and linting
echo   diagnose   - Run diagnostics
echo   start      - Start server
echo   format     - Format code
echo   clean      - Clean build artifacts
echo.
echo Usage: build.bat [command]

:end
