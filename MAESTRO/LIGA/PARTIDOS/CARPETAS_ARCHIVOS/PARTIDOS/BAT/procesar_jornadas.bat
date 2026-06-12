@echo off
cd /d "%~dp0"

:: Ejecuta el script Python
python procesar_todas_jornadas.py

:: Mantener la ventana abierta
pause
