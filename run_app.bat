@echo off
cd /d "%~dp0"
title Intervue.ai Launcher
color 0B

echo ===================================================
echo             LAUNCHING INTERVUE.AI
echo ===================================================
echo.

:: Check for backend virtual environment
if not exist "backend\venv" (
    echo [ERROR] Python virtual environment not found in backend\venv.
    echo Please follow the README to set up the project first.
    pause
    exit /b
)

:: Start Backend in a minimized window
echo [1/3] Starting backend API server (port 8000)...
start "Intervue.ai Backend" /min cmd /c "cd backend && venv\Scripts\activate && uvicorn app.main:app --port 8000"

:: Start Frontend in a minimized window
echo [2/3] Starting frontend Dev server (port 3000)...
start "Intervue.ai Frontend" /min cmd /c "cd frontend && npm run dev"

:: Wait for 3 seconds for servers to initialize
echo [3/3] Waiting for servers to load...
timeout /t 3 /nobreak > nul

:: Open the default web browser
echo Launching your default browser to http://localhost:3000...
start http://localhost:3000

echo.
echo ===================================================
echo SUCCESS! Intervue.ai is running.
echo.
echo - You can keep this window open.
echo - To STOP both servers and exit:
echo   Press any key in this window to shut down the servers.
echo ===================================================
echo.
pause

echo Shutting down servers...
taskkill /FI "WINDOWTITLE eq Intervue.ai Backend*" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq Intervue.ai Frontend*" /F > nul 2>&1
echo Done! Both servers stopped.
timeout /t 2 > nul
exit
