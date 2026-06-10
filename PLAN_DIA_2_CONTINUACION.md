# 📋 PLAN DE CONTINUACIÓN - DÍA 2

**Objetivo:** Hacer que WEB funcione completamente + Publicar en Vercel  
**Duración estimada:** 4 horas  
**Dificultad:** Media  

---

## ✅ CHECKLIST PREVIO

Antes de empezar, verifica:

- [ ] App Desktop abre sin errores
- [ ] Git tiene 10+ commits
- [ ] Carpeta `web/` existe con archivos
- [ ] Archivo `src/api_rest/routes/equipos.py` fue modificado
- [ ] Archivo `web/src/App.js` tiene fetch con `?torneo=`

---

## 🔥 FASE 1: DEBUGGEAR WEB (60 minutos)

### Paso 1.1: Verificar que API devuelve datos (10 min)

**Terminal:**
```powershell
cd D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium
python -m uvicorn src.api_rest.main:app --reload
```

**En otra terminal, testea:**
```powershell
# Liga (debe funcionar)
curl "http://127.0.0.1:8000/api/equipos?torneo=liga"

# Mundial (¿funciona?)
curl "http://127.0.0.1:8000/api/equipos?torneo=mundial"

# Champions (¿funciona?)
curl "http://127.0.0.1:8000/api/equipos?torneo=champions"
```

**¿Qué deberías ver?**
```json
[
  {"id": 1, "nombre": "ALAVES", "ciudad": "VITORIA", ...},
  {"id": 2, "nombre": "ATH.BILBAO", "ciudad": "BILBAO", ...},
  ...
]
```

**Si funciona:** ✅ Continúa a Paso 1.2  
**Si FALLA:** ❌ Revisar errores en terminal de API

---

### Paso 1.2: Verificar que WEB envía parámetro (10 min)

**Abre navegador: http://localhost:3000**

1. Presiona **F12** (DevTools)
2. Haz click en pestaña **Network**
3. En la WEB, haz click en selector "Mondial 2026"
4. En DevTools, busca request a `api/equipos`
5. Haz click en ese request
6. Mira la URL completa

**¿Qué deberías ver?**
```
http://127.0.0.1:8000/api/equipos?torneo=mundial
```

**Si ves eso:** ✅ Está bien  
**Si ves `?torneo=mondial` o `?torneo=undefined`:** ❌ Problema en App.js

---

### Paso 1.3: Revisar App.js si no funciona (20 min)

Abre: `web/src/App.js`

Busca la función `useEffect` que hace fetch:

```javascript
useEffect(() => {
  fetch(`http://127.0.0.1:8000/api/equipos?torneo=${selectedTorneo}`)
    .then(res => res.json())
    .then(data => {
      setEquipos(data);
      setLoading(false);
    })
    .catch(err => {
      console.log(err);
      setLoading(false);
    });
}, [selectedTorneo]);
```

**Problemas comunes:**

1. **La URL no tiene `?torneo=`:**
   - Reemplaza por la versión con parámetro (arriba)

2. **`selectedTorneo` es undefined:**
   - Verifica que existe: `const [selectedTorneo, setSelectedTorneo] = useState('liga');`

3. **No actualiza cuando cambias selector:**
   - Verifica que la función de cambio es: 
   ```javascript
   onChange={(e) => setSelectedTorneo(e.target.value)}
   ```

---

### Paso 1.4: Testear nuevamente (10 min)

1. Guarda cambios en App.js (Ctrl+S)
2. En navegador, presiona F5 (refresh)
3. Cambia selector a "Mondial 2026"
4. ¿Cambian los equipos?

**Si funciona:** ✅ Continúa a FASE 2  
**Si no:** ❌ Revisa console del navegador (F12 → Console) para errores

---

## 🎯 FASE 2: TESTEAR TODOS LOS TORNEOS (60 minutos)

### Paso 2.1: Probar cada torneo (30 min)

**Selector "Liga"**
- [ ] ¿Ves 17 equipos?
- [ ] ¿Empiezan con ALAVES, ATH.BILBAO, etc.?

**Selector "Mondial 2026"**
- [ ] ¿Ves equipos distintos?
- [ ] ¿Cambian respecto a Liga?

**Selector "Champions"**
- [ ] ¿Ves equipos distintos?

**Selector "Eurocopa"**
- [ ] ¿Ves equipos distintos?

---

### Paso 2.2: Hacer screenshot de cada uno (15 min)

1. Selector = "Liga" → Screenshot
2. Selector = "Mondial 2026" → Screenshot
3. Selector = "Champions" → Screenshot
4. Selector = "Eurocopa" → Screenshot

**Guarda en carpeta:** `screenshots/`

---

### Paso 2.3: Git commit (15 min)

```powershell
cd D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium
git add .
git commit -m "fix: WEB tournament selector fully functional - all torneos working"
git log --oneline
```

Deberías ver 11+ commits.

---

## 🌐 FASE 3: PUBLICAR EN VERCEL (30 minutos)

### Paso 3.1: Crear cuenta en Vercel (10 min)

1. Ve a: **https://vercel.com**
2. Click en **Sign Up** (arriba a la derecha)
3. Click en **Continue with GitHub** (o email)
4. Sigue pasos de registro

✅ Tienes cuenta creada

---

### Paso 3.2: Conectar carpeta `web/` (10 min)

1. En Vercel, click en **Add New → Project**
2. Click en **Import Git Repository**
3. Busca tu repo (Gestor_Torneos_Premium)
4. Click en **Import**
5. Vercel auto-detecta que es React
6. Click en **Deploy**

**Espera 2-3 minutos...**

✅ Tu WEB está en internet con URL como: `https://gestor-torneos-xxxxx.vercel.app`

---

### Paso 3.3: Copiar URL pública (5 min)

1. Vercel muestra tu URL
2. Cópiala
3. Guárdala en un archivo `WEB_URL.txt`

```
Vercel URL: https://gestor-torneos-xxxxx.vercel.app
```

---

### Paso 3.4: Testear desde navegador (5 min)

1. Abre tu URL de Vercel en navegador
2. ¿Ves la WEB?
3. ¿Puedes cambiar de torneo?
4. ¿Funciona igual que en localhost?

**IMPORTANTE:** Probablemente NO funcione porque la API sigue siendo `http://127.0.0.1:8000/` que NO es accesible desde Vercel.

**Solución:** Necesitarías publicar API también en servidor (Heroku, Railway, etc.) - eso es FASE 4 (opcional).

---

## 📱 FASE 4: TESTEAR DESDE iPhone (30 minutos)

### Paso 4.1: Obtener tu IP local (5 min)

**PowerShell:**
```powershell
ipconfig
```

Busca línea: `IPv4 Address: 192.168.x.x`

Anota tu IP, ejemplo: `192.168.1.100`

---

### Paso 4.2: Testear WEB en iPhone (15 min)

1. iPhone y PC **deben estar en MISMA WiFi**
2. En iPhone, abre Safari
3. Ve a: `http://192.168.1.100:3000` (usa TU IP)
4. ¿Ves la WEB?
5. Cambia de torneo - ¿Funciona?

**Si funciona:** ✅ ÉXITO  
**Si no funciona:** ❌ Probablemente firewall o IP incorrecta

---

### Paso 4.3: Testear Vercel en iPhone (10 min)

1. En iPhone, abre Safari
2. Ve a tu URL de Vercel: `https://gestor-torneos-xxxxx.vercel.app`
3. ¿Ves la WEB?
4. Cambias de torneo - ¿Qué pasa?

**Resultado esperado:** Se abre pero probablemente dice "Failed to fetch" porque API no es accesible desde Vercel.

---

## ✅ CHECKLIST FINAL

- [ ] API devuelve datos con parámetro `?torneo=`
- [ ] WEB selector funciona en localhost:3000
- [ ] Puedes cambiar entre 4 torneos
- [ ] Cada torneo muestra equipos distintos
- [ ] Git commit con cambios guardado
- [ ] Cuenta Vercel creada
- [ ] WEB publicada en Vercel
- [ ] Testea desde iPhone con IP local
- [ ] Testea desde iPhone con URL de Vercel

---

## 🎯 RESULTADO ESPERADO AL FINAL

✅ **Desktop:** Funciona 100% localmente  
✅ **WEB:** Funciona 100% con 4 torneos  
✅ **WEB URL:** Accesible desde iPhone en misma red  
✅ **Vercel:** Publicada en internet  
❌ **API pública:** No (opcional para FASE 4)  
❌ **Mobile:** No (opcional para FASE 5)  

---

## 🚀 SI TODO FUNCIONA

**Congratulations! 🎉**

Tienes un producto funcional:
- Desktop para gestionar torneos
- WEB accesible desde cualquier navegador
- Múltiples torneos funcionando
- Publicado en internet

---

## 💡 NOTAS IMPORTANTES

1. **Vercel publican la WEB estática**, no el backend (API)
2. **iPhone en misma red:** Usa `http://192.168.x.x:3000` (No HTTPS)
3. **Si API falla en Vercel:** Es normal, necesitarías publicar API también
4. **Desktop siempre funciona:** Es independiente de todo

---

## 🆘 SI ALGO FALLA

**Recomendado:**
1. Consulta README_PROYECTO_COMPLETO.md (sección Troubleshooting)
2. Revisa Git history: `git log --oneline`
3. Vuelve a versión anterior si es necesario: `git checkout abc1234`

---

**¡Buena suerte! Estás cerca de terminar.** 🚀
