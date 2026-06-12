import sqlite3
import os

db_path = r"D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium\bases_de_datos\mundial_2026_v2.db"

conn = sqlite3.connect(db_path, timeout=10.0)
conn.row_factory = sqlite3.Row

# Obtener equipos agrupados
equipos = {}
for eq in conn.execute("SELECT id, nombre, grupo FROM equipos ORDER BY grupo").fetchall():
    if eq["grupo"]:
        if eq["grupo"] not in equipos:
            equipos[eq["grupo"]] = []
        equipos[eq["grupo"]].append(eq["id"])

print(f"Grupos encontrados: {list(equipos.keys())}")

# Asignar grupo a cada partido basado en equipos
actualizado = 0
for partido in conn.execute("SELECT id, equipo_local_id, equipo_visitante_id, grupo FROM partidos").fetchall():
    if partido["grupo"]:  # Ya tiene grupo
        continue

    # Buscar grupo del equipo local
    for grupo, equipos_grupo in equipos.items():
        if partido["equipo_local_id"] in equipos_grupo:
            conn.execute("UPDATE partidos SET grupo = ? WHERE id = ?", (grupo, partido["id"]))
            actualizado += 1
            break

conn.commit()
conn.close()

print(f"✓ {actualizado} partidos actualizados con su grupo")
