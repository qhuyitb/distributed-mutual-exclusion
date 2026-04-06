@echo off
REM Ricart-Agrawala Demo Installer
REM Download and install Python if not present

echo.
echo ============================================================
echo     Ricart-Agrawala Algorithm - Environment Setup
echo ============================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python da duoc cai dat
    echo.
    python --version
    echo.
    echo Chay demo...
    cd /d "%~dp0"
    python demo.py
    pause
) else (
    echo [ERROR] Python chua duoc cai dat
    echo.
    echo Hay cai dat Python tu: https://www.python.org/downloads/
    echo.
    echo Sau khi cai dat, chay lai script nay.
    pause
)
