@echo off
title Convertir Jornadas a CSV
color 0A

REM --- Guardar la carpeta actual ---
set "CARPETA_ACTUAL=%~dp0"

REM --- Cambiar a la carpeta del script ---
cd /d "%CARPETA_ACTUAL%"

REM --- Ejecutar el script con Python ---
python "convertir_jornadas_rango.py"

echo.
echo Proceso finalizado. Pulsa cualquier tecla para cerrar.
pause >nul
