@echo off
cd /d "%~dp0"

:: Ejecuta el script Python
python generar_jornada_csv.py

:: Mantener la ventana abierta
pause
