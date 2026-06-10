# DIRECTRICES PARA CONTINUAR - PROYECTO GESTOR TORNEOS

**FECHA:** 2026-06-10  
**ESTADO:** 80% completado  
**PROBLEMAS PENDIENTES:** Publicar API en servidor real  

---

## ¿QUÉ FUNCIONA?

✅ **App Desktop** - 100% funcional  
- Ubicación: `D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium\app_maestra_futbol.py`
- Ejecutar: `python app_maestra_futbol.py`
- Funciona: Registra partidos, ve gráficos, exporta PDF

✅ **WEB React Local** - 100% funcional  
- Ubicación: `web/src/App.js`
- Ejecutar: `cd web && npm start`
- Funciona: `http://127.0.0.1:3000` (PC) y `http://192.168.x.x:3000` (iPhone en casa)
- Selector de torneos: FUNCIONA (cambia datos)

✅ **API REST FastAPI** - 100% funcional localmente  
- Ubicación: `src/api_rest/main.py`
- Ejecutar: `python -m uvicorn src.api_rest.main:app --host 0.0.0.0 --reload`
- 18 endpoints CRUD funcionando
- Endpoint clave: `GET http://127.0.0.1:8000/api/equipos?torneo=liga`

✅ **Git** - 12+ commits guardados en GitHub  
- Repo: https://github.com/krankel69/Gestor_Torneos_Premium
- Historial completo

✅ **Vercel WEB** - Publicada pero sin datos  
- URL: https://gestor-torneos-premium.vercel.app
- Problema: Intenta conectar a `127.0.0.1:8000` que NO es accesible desde internet

---

## ¿QUÉ NO FUNCIONA?

❌ **API en servidor real** (PROBLEMA PRINCIPAL)
- Intentó con Railway: Error `metadata-generation-failed` con pydantic en Python 3.14
- Intentó con Render: Mismos errores de compatibilidad
- Causa: Python 3.14 es muy nuevo, librerías no compatibles

❌ **Vercel + API integrada**
- Vercel publica WEB pero WEB no puede conectar a API
- Necesita: API en servidor real con URL pública

---

## ¿QUÉ DEBE HACER LA SIGUIENTE IA?

### OPCIÓN A (RECOMENDADA): Publicar API en Heroku o Render
1. **Cambiar Python version** a 3.11 o 3.12 (no 3.14 - muy nuevo)
2. **Crear/actualizar `requirements.txt`** compatible:
   ```
   fastapi==0.104.0
   uvicorn[standard]==0.24.0
   pydantic==2.4.2
   ```
3. **Crear `Procfile` para Heroku:**
   ```
   web: uvicorn src.api_rest.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Publicar en Heroku o Render** con ese Python version
5. **Obtener URL pública** (ej: `https://gestor-api-xxxxx.herokuapp.com`)
6. **Actualizar WEB** para usar esa URL en lugar de `127.0.0.1:8000`
7. **Redeploy WEB en Vercel**

### OPCIÓN B (MÁS SIMPLE): Usar servicio sin servidor
- Migrar API a Firebase Functions o AWS Lambda
- Usar base de datos en cloud (MongoDB Atlas gratis)
- Vercel WEB + Firebase API = Funcionan juntas

---

## ARCHIVOS CRÍTICOS

```
D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium\
├── app_maestra_futbol.py          ← DESKTOP (FUNCIONA)
├── database.py                      ← Gestor BD
├── requirements.txt                 ← NECESITA ACTUALIZAR
├── src/api_rest/main.py            ← API (FUNCIONA local)
├── src/api_rest/routes/
│   ├── equipos.py                  ← Router equipos
│   ├── partidos.py
│   ├── goleadores.py
│   └── clasificacion.py
├── web/src/App.js                  ← WEB (FUNCIONA local)
├── bases_de_datos/
│   ├── liga_futbol_v2.db           ← BD principal
│   ├── mundial_2026_v2.db
│   ├── champions_gui_v2.db
│   └── eurocopa_2024_v2.db
└── .git/                            ← Historial completo
```

---

## PASOS EXACTOS PARA RESOLVER

### Paso 1: Arreglar Python version
```bash
# En local primero (PC del usuario)
python3.11 -m venv venv  # Crear environment Python 3.11
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.api_rest.main:app --host 0.0.0.0
```

### Paso 2: Crear requirements.txt correcto
```
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.4.2
click==8.1.7
```

### Paso 3: Publicar en Render (más fácil que Heroku ahora)
- Conectar GitHub
- Seleccionar repo `Gestor_Torneos_Premium`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn src.api_rest.main:app --host 0.0.0.0 --port 8000`
- **Importante:** Especificar Python 3.11 en `runtime.txt`: `python-3.11.0`

### Paso 4: Obtener URL de API pública
Ejemplo: `https://gestor-api-xxxxx.onrender.com`

### Paso 5: Actualizar App.js
En `web/src/App.js`, cambiar:
```javascript
// De:
const apiUrl = `http://${window.location.hostname}:8000/api/equipos?torneo=${selectedTorneo}`;

// A:
const apiUrl = `https://gestor-api-xxxxx.onrender.com/api/equipos?torneo=${selectedTorneo}`;
```

### Paso 6: Git commit y Vercel redeploy
```bash
git add .
git commit -m "feat: Use public API from Render"
git push
# Vercel redeploya automático
```

### Paso 7: Testear
- `https://gestor-torneos-premium.vercel.app` (WEB publica)
- Selector de torneos: ¿Funciona?
- iPhone 4G: ¿Ve datos?

---

## ERRORES A EVITAR

❌ No usar Python 3.14 - demasiado nuevo, librerías no compatibles  
❌ No hardcodear IPs - usar `window.location.hostname` o variables de entorno  
❌ No olvidar CORS en API si es necesario  
❌ No subir bases de datos a servidor público (seguridad)  

---

## CÓMO INDICARLE A OTRA IA

**Prompt recomendado:**

"Tengo una app Django/FastAPI que funciona localmente pero necesito publicarla en internet. 
- Desktop funciona ✅
- WEB (React) funciona en `localhost:3000` ✅
- API (FastAPI) funciona en `127.0.0.1:8000` ✅
- Problema: Necesito publicar API en servidor real (Render/Heroku/Railway)
- Intentos previos fallaron por compatibilidad Python 3.14

Ayudame a:
1. Arreglar `requirements.txt` compatible
2. Publicar API en Render
3. Conectar WEB a API pública
4. Hacer que funcione desde internet"

**Información a compartir:**
- Link GitHub: https://github.com/krankel69/Gestor_Torneos_Premium
- Stack: Python 3.14, FastAPI, React, SQLite
- Objetivo: App accesible desde internet (iPhone, desde cualquier lugar)

---

## RESUMEN DEL ESTADO

| Componente | Estado | Acceso |
|-----------|--------|--------|
| Desktop | ✅ 100% | Local PC |
| WEB local | ✅ 100% | 127.0.0.1:3000 |
| API local | ✅ 100% | 127.0.0.1:8000 |
| WEB Vercel | ✅ 100% | vercel.app (sin datos) |
| API público | ❌ 0% | NO EXISTE |
| iPhone local | ✅ 100% | WiFi casa |
| iPhone internet | ❌ 0% | NO FUNCIONA |

**Falta:** Publicar API en servidor real = **2-3 horas máximo**

---

**Hecho con buenas intenciones pero sin éxito final. Disculpas sinceras.**
