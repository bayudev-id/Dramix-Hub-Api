@echo off
title Dramix Gateway - Stop All Services
echo ===============================================================================
echo                DRAMIX GATEWAY - STOPPING ALL SERVICES
echo ===============================================================================
echo.

echo Menghentikan process pada port 8090 dan 6101-6107...

powershell -NoProfile -Command ^
    "$ports = @(8090, 6101, 6102, 6103, 6104, 6105, 6106, 6107);" ^
    "$pids = (Get-NetTCPConnection -LocalPort $ports -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique);" ^
    "if ($pids) { foreach ($p in $pids) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; Write-Host ('[STOPPED] PID: ' + $p) } } else { Write-Host '[INFO] Tidak ada service yang sedang berjalan.' }"

echo.
echo ===============================================================================
echo SEMUA SERVICE TELAH DIHENTIKAN!
echo ===============================================================================
echo.
pause
