@echo off
title Dramix Gateway - Stop All Services
echo ===============================================================================
echo                DRAMIX GATEWAY - STOPPING ALL SERVICES
echo ===============================================================================
echo.

echo Menghentikan process pada port 8090 dan 7401-7407...

powershell -NoProfile -Command ^
    "$ports = @(8090, 7401, 7402, 7403, 7404, 7405, 7406, 7407);" ^
    "$pids = (Get-NetTCPConnection -LocalPort $ports -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique);" ^
    "if ($pids) { foreach ($p in $pids) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; Write-Host ('[STOPPED] PID: ' + $p) } } else { Write-Host '[INFO] Tidak ada service yang sedang berjalan.' }"

echo.
echo ===============================================================================
echo SEMUA SERVICE TELAH DIHENTIKAN!
echo ===============================================================================
echo.
pause
