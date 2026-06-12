@echo off
cd /d "%~dp0"

:: Ejecuta el script de Python
python generar_jornada.py

:: Mantener la ventana abierta para ver mensajes
pause
