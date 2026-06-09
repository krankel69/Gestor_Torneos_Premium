════════════════════════════════════════════════════════════════════════════════
  🌍 MUNDIAL 2026 — SISTEMA DE DESEMPATE FIFA IMPLEMENTADO
════════════════════════════════════════════════════════════════════════════════

CAMBIOS IMPLEMENTADOS
═════════════════════

✅ SCHEMA EXTENDIDA (base de datos)
  · campos tarjetas_amarillas_local/visitante (INTEGER, default 0)
  · campos tarjetas_rojas_local/visitante (INTEGER, default 0)
  · campo ranking_fifa en tabla equipos (INTEGER, default 999)

✅ DESEMPATE H2H FIFA 2026 (nueva lógica)
  Cuando 2+ equipos tienen los mismos puntos en un grupo:
  1. Enfrentamiento directo (H2H) - Puntos
  2. Enfrentamiento directo (H2H) - Diferencia de goles
  3. Enfrentamiento directo (H2H) - Goles a favor
  4. Diferencia general de goles
  5. Goles generales a favor
  6. Conducta deportiva (Fair Play)
     - Tarjeta amarilla: -1 punto
     - Tarjeta roja directa: -4 puntos
     - Tarjeta roja indirecta (segunda amarilla): -3 puntos
  7. Ranking FIFA (si persiste empate)

✅ INTERFAZ USUARIO
  Tab "Grupos y Resultados" → Panel de resultados:
  · Campos de TARJETAS (nuevo):
    - Amarillas Local / Visitante
    - Rojas Local / Visitante
  · Se guardan automáticamente al registrar el marcador

✅ CÁLCULO AUTOMÁTICO
  · Al hacer clic "Refrescar Clasificación" (o registrar resultado):
    1. Recalcula estadísticas (PJ, PG, PE, PP, GF, GC, PTS)
    2. Para mundial: aplica desempate H2H dentro de cada grupo
    3. Ordena equipos en orden definitivo (1º, 2º de cada grupo)
    4. Calcula Fair Play
    5. Aplica Ranking FIFA como último criterio

════════════════════════════════════════════════════════════════════════════════
CÓMO USAR
═════════════════════

1️⃣  CREAR PARTIDO (ya existía)
    - Tab "Equipos y Jugadores" → Importar equipos CSV
    - Asignar a GRUPO (A, B, C, etc.)
    - Crear partidos con fase="Fase de grupos"

2️⃣  REGISTRAR RESULTADO
    - Tab "Grupos y Resultados" → Selector "Selecciona un partido"
    - Entrada goles Local / Visitante
    - ⭐ NUEVO: Entrada de tarjetas
      * Amarillas Local/Visitante (1, 2, 3... según desee)
      * Rojas Local/Visitante (0, 1, 2 etc.)
    - Click "Grabar Resultado" → se guardan marcador + tarjetas
    - ⚠️  Cuadre de goleadores (como antes)

3️⃣  VER CLASIFICACIÓN
    - Tab "Equipos y Judadores" → Tabla "Clasificación"
    - Click "Refrescar Clasificación" → aplica desempate H2H
    - Equipos aparecen en orden (1º grupo A, 2º grupo A, 1º grupo B, etc.)
    - Tabla muestra: Pos, Equipo, PJ, PG, PE, PP, GF, GC, PTS, DG

4️⃣  RANKING FIFA (PRÓXIMA MEJORA)
    - Editar en tabla "Equipos" (campo ranking_fifa)
    - Usado como último criterio en desempate
    - Default: 999 (baja prioridad)
    - Valores reales: 1 (mejor) a ~200 (peor)

════════════════════════════════════════════════════════════════════════════════
CARACTERÍSTICAS PENDIENTES (no críticas)
═════════════════════════════════════════════

⏳ UI para editar ranking FIFA de equipos
⏳ Mostrar "Mejores Terceros" (8 de 12 terceros)
⏳ Mostrar detalles de desempate en clasificación (ej: "1º por H2H")
⏳ Generador automático de Dieciseisavos basado en clasificación

════════════════════════════════════════════════════════════════════════════════
ALGORITMO DE DESEMPATE (método: _desempatar_mundial_h2h)
═════════════════════════════════════════════════════════════════════════════════

def _desempatar_mundial_h2h(grupo_eq, grupo_id, conn):
    1. Agrupar equipos por número de puntos
    2. Para cada grupo con 2+ equipos empatados:
       a. Calcular estadísticas H2H (solo partidos entre los empatados)
       b. Calcular Fair Play (total de tarjetas × factores)
       c. Ordenar por:
          - H2H puntos (desc)
          - H2H diferencia goles (desc)
          - H2H goles a favor (desc)
          - General diferencia goles (desc)
          - General goles a favor (desc)
          - Fair Play (desc)
          - Ranking FIFA (asc)
    3. Devolver orden final: [id_eq1, id_eq2, ...] clasificados

════════════════════════════════════════════════════════════════════════════════
NOTAS TÉCNICAS
═════════════════════════════════════════════════════════════════════════════════

• Schema migration: automático en __init__ de AppMaestra
  Si campos no existen → se crean con ALTER TABLE

• Fair Play calculation:
  - Suma de (amarillas × -1) + (rojas × -4) por equipo y partido
  - Aplicado a TODOS los partidos de su grupo (sin filtro H2H)

• Llamadas clave:
  - self._cargar_grupos() → recalcula + carga tabla
  - self._recalcular_grupos() → recalcula stats + aplica H2H
  - self._desempatar_mundial_h2h() → devuelve orden correcto de un grupo

════════════════════════════════════════════════════════════════════════════════
EJEMPLO PRÁCTICO
═════════════════════════════════════════════════════════════════════════════════

Grupo A: Argentina (3-0 Colombia, 1-1 Canadá), 
         Colombia (0-3 Argentina, 2-1 Canadá),
         Canadá (1-2 Colombia, 1-1 Argentina)

Stats simples:
  Argentina: 3 PJ, 2 PG, 1 PE, 0 PP, 5 GF, 1 GC = 7 PTS
  Colombia:  3 PJ, 1 PG, 0 PE, 2 PP, 5 GF, 5 GC = 3 PTS
  Canadá:    3 PJ, 0 PG, 1 PE, 2 PP, 3 GF, 7 GC = 1 PTS

Resultado: Argentina 1º, Colombia 2º, Canadá 3º (sin desempate)

════════════════════════════════════════════════════════════════════════════════
PRÓXIMAS SESIONES
═════════════════════════════════════════════════════════════════════════════════

1. Prueba el sistema con datos reales de un grupo
2. Si detectas bugs en H2H, avisa con ejemplo específico
3. Se puede añadir UI para editar ranking FIFA de equipos
4. Se puede mostrar visualmente qué criterio resolvió cada desempate
5. Se puede generar automáticamente Dieciseisavos basado en 1º+2º+8 mejores 3ºs

════════════════════════════════════════════════════════════════════════════════
