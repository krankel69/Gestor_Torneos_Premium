# 📱 MANUAL DE USO - GESTOR TORNEOS PREMIUM

**¿Cómo usar el proyecto cuando cierres el PC e iPhone?**

---

## 🏠 ESCENARIO 1: En tu casa (WiFi)

### **En tu PC:**

Abre PowerShell:

```powershell
cd D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium

# Opción A: Abrir TODO automático
iniciar.bat

# O manualmente - Terminal 1:
python app_maestra_futbol.py

# Terminal 2:
python -m uvicorn src.api_rest.main:app --host 0.0.0.0 --reload

# Terminal 3:
cd web && npm start
```

### **En iPhone (misma WiFi):**

Abre Safari:

```
http://192.168.1.206:3000
```

(Reemplaza 206 por tu IP si cambió)

¿Qué funciona?
- ✅ WEB con equipos
- ✅ Selector de torneos
- ✅ Desktop en tu PC
- ✅ Sin necesidad de internet

---

## 🌍 ESCENARIO 2: Fuera de casa (4G/WiFi pública)

### **En tu PC:**

PC **DEBE ESTAR APAGADO** (no necesita estar encendido).

### **En iPhone:**

Abre Safari:

```
https://krankel69.github.io/Gestor_Torneos_Premium/
```

¿Qué funciona?
- ✅ WEB con equipos (desde GitHub Pages)
- ✅ Selector de torneos
- ✅ **PERO:** Datos están desactualizados (los de última vez que sincronizaste)

**IMPORTANTE:** Los datos son ESTÁTICOS (no se actualizan en tiempo real)

---

## 🔄 ESCENARIO 3: Actualizar datos desde fuera de casa

Si quieres que los datos se actualicen cuando estés fuera:

### **Paso 1: Actualizar en Desktop (en casa)**

1. Abre Desktop en tu PC
2. Registra partidos, jugadores, etc.
3. Datos se guardan en BD local

### **Paso 2: Sincronizar a GitHub**

```powershell
git add .
git commit -m "Update: New matches added"
git push
```

### **Paso 3: Trigger GitHub Pages rebuild**

En GitHub.com:
1. Ve a tu repo
2. Go to Actions
3. Espera a que se reconstruya automáticamente (~1 min)

### **Paso 4: Recargar en iPhone**

En Safari, presiona F5 (refresh):

```
https://krankel69.github.io/Gestor_Torneos_Premium/
```

¡Los datos nuevos están disponibles!

---

## 📊 ¿QUÉ ES CADA PARTE?

| Componente | Ubicación | Cuándo lo usas | Estado |
|-----------|-----------|----------------|--------|
| **Desktop** | Tu PC | Registrar partidos en casa | Siempre disponible |
| **API Render** | Internet (pública) | Backend, datos | Siempre activo |
| **WEB GitHub Pages** | Internet (pública) | Ver datos desde cualquier lado | Datos estáticos |
| **WEB Local** | Tu WiFi (192.168.x.x:3000) | Ver datos en tiempo real en casa | Requiere PC encendido |

---

## 🎯 CASOS DE USO REALES

### **Caso 1: Quiero ver datos en casa**

1. PC encendida ✅
2. Ejecutar: `iniciar.bat`
3. iPhone: `http://192.168.1.206:3000`
4. ✅ FUNCIONA en tiempo real

### **Caso 2: Quiero ver datos fuera de casa**

1. iPhone abierto
2. Ir a: `https://krankel69.github.io/Gestor_Torneos_Premium/`
3. ✅ FUNCIONA (datos última sincronización)

### **Caso 3: Quiero actualizar datos desde fuera de casa**

1. PC apagada ❌
2. **Usar Desktop cuando llegues a casa**
3. Luego sincronizar a GitHub

### **Caso 4: PC encendida pero WiFi no funciona**

1. iPhone en 4G
2. Ir a: `https://krankel69.github.io/Gestor_Torneos_Premium/`
3. ✅ FUNCIONA (datos estáticos)

---

## ⚙️ MANTENIMIENTO

### **Cada semana:**
```powershell
git add .
git commit -m "Weekly sync"
git push
```

### **Si cambias datos:**
```powershell
# En PC
git add .
git commit -m "Updated tournaments"
git push
# Espera 1 min a que GitHub Pages se reconstruya
# Refresca iPhone
```

### **Si algo falla localmente:**
```powershell
git status  # Ver cambios
git log --oneline  # Ver historial
git checkout abc123  # Volver a versión anterior
```

---

## 🔐 SEGURIDAD

- ✅ Datos guardados en GitHub (backup automático)
- ✅ API pública pero solo GET (lectura)
- ✅ Bases de datos NO en GitHub (privadas en tu PC)
- ⚠️ GitHub Pages es público (cualquiera ve WEB)

---

## 🚀 RESUMEN RÁPIDO

**¿Cerraste PC e iPhone?**

```
Mañana cuando abras:

1. CASA + WiFi:
   → Ejecuta: iniciar.bat
   → iPhone: http://192.168.1.206:3000
   → ✅ Todo en tiempo real

2. FUERA DE CASA:
   → iPhone: https://krankel69.github.io/Gestor_Torneos_Premium/
   → ✅ Datos últimas actualización

3. QUIERES ACTUALIZAR DATOS:
   → PC en casa: Desktop + git push
   → Espera 1 min
   → iPhone: F5 (refresh)
   → ✅ Datos nuevos disponibles
```

---

## 🆘 TROUBLESHOOTING

**"404 en GitHub Pages"**
→ Espera 2 minutos a que se reconstruya

**"No ve datos en GitHub Pages"**
→ Hizo git push? Datos en GitHub?

**"En casa dice error de conexión"**
→ ¿API Render está activa? Chequea: https://gestor-torneos-premium-2.onrender.com/api/equipos?torneo=liga

**"IP en casa cambió"**
→ Ejecuta `ipconfig` en PC
→ Actualiza URL en iPhone

---

## 📞 LÍNEA DE TIEMPO

```
DÍA 1:
├─ Abres Desktop
├─ Registras partidos
├─ Cierras PC

DÍA 2 (EN CASA):
├─ Ejecutas iniciar.bat
├─ iPhone en WiFi
├─ Ves datos en tiempo real

DÍA 3 (FUERA DE CASA):
├─ iPhone sin WiFi (4G)
├─ Abres GitHub Pages
├─ Ves datos (estáticos)

DÍA 4 (EN CASA NUEVAMENTE):
├─ Actualizas partidos en Desktop
├─ git push
├─ iPhone refresh
├─ ✅ Datos nuevos
```

---

**¡Tu proyecto está COMPLETO y FUNCIONAL!** 🎉

Úsalo, disfrútalo, y mantén GitHub actualizado.

Cualquier pregunta: revisa este manual o GitHub history.
