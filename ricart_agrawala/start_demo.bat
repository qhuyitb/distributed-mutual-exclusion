@echo off
REM Start Ricart-Agrawala Demo with Network Communication
REM Mở 4 terminals: 1 coordinator + 3 nodes

echo.
echo ============================================================
echo   Ricart-Agrawala Demo - Multi-Process with Network
echo ============================================================
echo.
echo Dang khoi dong Coordinator va 3 Nodes...
echo.

REM Get the current directory
set SCRIPT_DIR=%~dp0

REM Start Coordinator
echo [1/4] Starting Coordinator...
start "Coordinator" cmd /k "cd /d %SCRIPT_DIR% && python coordinator.py"

REM Wait for coordinator to start
timeout /t 2 /nobreak

REM Start 3 nodes
echo [2/4] Starting Node 0...
start "Node 0" cmd /k "cd /d %SCRIPT_DIR% && python node_process.py 0 3"

echo [3/4] Starting Node 1...
start "Node 1" cmd /k "cd /d %SCRIPT_DIR% && python node_process.py 1 3"

echo [4/4] Starting Node 2...
start "Node 2" cmd /k "cd /d %SCRIPT_DIR% && python node_process.py 2 3"

echo.
echo ============================================================
echo 4 terminals da duoc mo:
echo - 1 Coordinator (port 5000)
echo - 3 Nodes (ports 6000, 6001, 6002)
echo.
echo Tren moi Node terminal, type:
echo   request    = Request vao Critical Section
echo   quit       = Thoat node
echo ============================================================
echo.

pause
