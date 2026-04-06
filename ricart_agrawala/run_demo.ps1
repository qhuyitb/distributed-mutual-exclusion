# Ricart-Agrawala Demo Runner - PowerShell Script
# Usage: .\run_demo.ps1

Write-Host "`n" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Ricart-Agrawala Algorithm - Demo Runner" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "`n"

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python da duoc cai dat: $pythonVersion" -ForegroundColor Green
    Write-Host "`n"
    
    # Change to script directory
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptPath
    
    Write-Host "Chon demo:" -ForegroundColor Yellow
    Write-Host "1. Quick Demo (demo.py)" -ForegroundColor White
    Write-Host "2. Interactive Menu (main.py)" -ForegroundColor White
    Write-Host "3. Example Scenarios (example.py)" -ForegroundColor White
    Write-Host "`n"
    
    $choice = Read-Host "Chon (1-3)"
    
    switch ($choice) {
        "1" {
            Write-Host "`nRunning Quick Demo...`n" -ForegroundColor Cyan
            python demo.py
        }
        "2" {
            Write-Host "`nRunning Interactive Menu...`n" -ForegroundColor Cyan
            python main.py
        }
        "3" {
            Write-Host "`nRunning Example Scenarios...`n" -ForegroundColor Cyan
            python example.py
        }
        default {
            Write-Host "Lua chon khong hop le!" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "[ERROR] Python chua duoc cai dat!" -ForegroundColor Red
    Write-Host "`n"
    Write-Host "Hay cai dat Python:" -ForegroundColor Yellow
    Write-Host "https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "`n"
    Write-Host "Huong dan cai dat:" -ForegroundColor Yellow
    Write-Host "1. Download Python from python.org" -ForegroundColor White
    Write-Host "2. Chay installer va TICK 'Add Python to PATH'" -ForegroundColor White
    Write-Host "3. Restart terminal" -ForegroundColor White
    Write-Host "4. Chay lai script nay" -ForegroundColor White
}
