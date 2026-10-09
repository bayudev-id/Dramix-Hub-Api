@echo off
title Dramix Gateway - Master Launcher
echo ===============================================================================
echo                DRAMIX GATEWAY - STARTING ALL SERVICES
echo ===============================================================================
echo.

:: Deteksi Python Virtual Environment (Fallback ke sistem python jika .venv belum ada)
set "PYTHON_CMD=python"
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    echo [INFO] Menggunakan Virtual Environment: %~dp0.venv
) else (
    echo [INFO] Menggunakan Python Sistem
)
echo.

echo [1/8] Menjalankan PocketBase (Port 8090)...
start "Dramix [8090] PocketBase" /D "%~dp0pocketbase" cmd /k "pocketbase.exe serve"

timeout /t 2 /nobreak >nul

echo [2/8] Menjalankan CineFlow Hub API (Port 7401)...
start "Dramix [7401] CineFlow Hub" /D "%~dp0services\cineflow_hub_api" cmd /k "%PYTHON_CMD% main.py"

echo [3/8] Menjalankan WeTV API (Port 7402)...
start "Dramix [7402] WeTV API" /D "%~dp0services\wetv_api" cmd /k "%PYTHON_CMD% main.py"

echo [4/8] Menjalankan KissKH API (Port 7403)...
start "Dramix [7403] KissKH API" /D "%~dp0services\kisskh_api" cmd /k "node server.js"

echo [5/8] Menjalankan MovieBox API (Port 7404)...
start "Dramix [7404] MovieBox API" /D "%~dp0services\moviebox_api" cmd /k "%PYTHON_CMD% app.py"

echo [6/8] Menjalankan Viu API (Port 7405)...
start "Dramix [7405] Viu API" /D "%~dp0services\viu_api" cmd /k "%PYTHON_CMD% main.py"

echo [7/8] Menjalankan FreeReels API (Port 7406)...
start "Dramix [7406] FreeReels API" /D "%~dp0services\freereels_api\production" cmd /k "%PYTHON_CMD% run_proxy.py"

echo [8/8] Menjalankan iQIYI API (Port 7407)...
start "Dramix [7407] iQIYI API" /D "%~dp0services\iqiyi_api\production" cmd /k "%PYTHON_CMD% run_server.py"

echo.
echo ===============================================================================
echo SEMUA SERVICE TELAH DIJALANKAN!
echo -------------------------------------------------------------------------------
echo  - PocketBase:    http://127.0.0.1:8090/_/
echo  - Models API:    http://127.0.0.1:8090/api/modelles/models
echo  - CineFlow Hub:  http://127.0.0.1:7401
echo  - WeTV API:      http://127.0.0.1:7402
echo  - KissKH API:    http://127.0.0.1:7403
echo  - MovieBox API:  http://127.0.0.1:7404
echo  - Viu API:       http://127.0.0.1:7405
echo  - FreeReels API: http://127.0.0.1:7406
echo  - iQIYI API:     http://127.0.0.1:7407
echo ===============================================================================
echo.
pause
