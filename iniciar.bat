@echo off
cd D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium

REM Terminal 1: App Desktop
start cmd /k "python app_maestra_futbol.py"

REM Terminal 2: API REST
start cmd /k "cd src && python -m uvicorn api_rest.main:app --reload"

REM Terminal 3: WEB
start cmd /k "cd web && npm start"

echo.
echo Esperando 10 segundos...
timeout /t 10

REM Abre WEB en navegador
start http://localhost:3000

echo.
echo [OK] Todo abierto. Ve a http://localhost:3000 en navegador