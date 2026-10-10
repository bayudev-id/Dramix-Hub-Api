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
"%~dp0pocketbase\pocketbase.exe" migrate up --dir="%~dp0pocketbase\pb_data" --migrationsDir="%~dp0pocketbase\pb_migrations"
start "Dramix [8090] PocketBase" /D "%~dp0pocketbase" cmd /k "pocketbase.exe serve"

timeout /t 2 /nobreak >nul

echo [2/8] Menjalankan CineFlow Hub API (Port 6101)...
start "Dramix [6101] CineFlow Hub" /D "%~dp0services\cineflow_hub_api" cmd /k "%PYTHON_CMD% main.py"

echo [3/8] Menjalankan WeTV API (Port 6102)...
start "Dramix [6102] WeTV API" /D "%~dp0services\wetv_api" cmd /k "%PYTHON_CMD% main.py"

echo [4/8] Menjalankan KissKH API (Port 6103)...
start "Dramix [6103] KissKH API" /D "%~dp0services\kisskh_api" cmd /k "node server.js"

echo [5/8] Menjalankan MovieBox API (Port 6104)...
start "Dramix [6104] MovieBox API" /D "%~dp0services\moviebox_api" cmd /k "%PYTHON_CMD% app.py"

echo [6/8] Menjalankan Viu API (Port 6105)...
start "Dramix [6105] Viu API" /D "%~dp0services\viu_api" cmd /k "%PYTHON_CMD% main.py"

echo [7/8] Menjalankan FreeReels API (Port 6106)...
start "Dramix [6106] FreeReels API" /D "%~dp0services\freereels_api\production" cmd /k "%PYTHON_CMD% run_proxy.py"

echo [8/8] Menjalankan iQIYI API (Port 6107)...
start "Dramix [6107] iQIYI API" /D "%~dp0services\iqiyi_api\production" cmd /k "%PYTHON_CMD% run_server.py"

echo.
echo ===============================================================================
echo SEMUA SERVICE TELAH DIJALANKAN!
echo -------------------------------------------------------------------------------
echo  - PocketBase:    http://127.0.0.1:8090/_/
echo  - Models API:    http://127.0.0.1:8090/api/modelles/models
echo  - CineFlow Hub:  http://127.0.0.1:6101
echo  - WeTV API:      http://127.0.0.1:6102
echo  - KissKH API:    http://127.0.0.1:6103
echo  - MovieBox API:  http://127.0.0.1:6104
echo  - Viu API:       http://127.0.0.1:6105
echo  - FreeReels API: http://127.0.0.1:6106
echo  - iQIYI API:     http://127.0.0.1:6107
echo ===============================================================================
echo.
pause
