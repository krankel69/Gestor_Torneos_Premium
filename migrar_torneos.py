"""
migrar_torneos.py  —  Migración única al esquema canónico
=========================================================
Lee cada BD antigua y vuelca los datos en una BD nueva con
el esquema unificado. Las BDs originales NO se modifican.

Uso:
    python migrar_torneos.py

Se abrirá un selector por cada BD origen. Al final se
guarda cada torneo migrado en la misma carpeta con el
sufijo _v2.db
"""
import sqlite3
import os
import sys
from tkinter import filedialog, messagebox, Tk

# ────────────────────────────────────────────────────────────────────
# ESQUEMA CANÓNICO
# ────────────────────────────────────────────────────────────────────
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS torneo_info (
    id          INTEGER PRIMARY KEY,
    nombre      TEXT    NOT NULL,
    tipo        TEXT    NOT NULL CHECK(tipo IN ('liga','copa','mundial','euro')),
    temporada   TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS equipos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT    NOT NULL UNIQUE,
    ciudad  TEXT    DEFAULT '',
    grupo   TEXT    DEFAULT NULL,
    pj      INTEGER DEFAULT 0,
    pg      INTEGER DEFAULT 0,
    pe      INTEGER DEFAULT 0,
    pp      INTEGER DEFAULT 0,
    gf      INTEGER DEFAULT 0,
    gc      INTEGER DEFAULT 0,
    pts     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS jugadores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL,
    equipo_id       INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    goles_marcados  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS partidos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_local_id     INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    equipo_visitante_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    goles_local         INTEGER DEFAULT -1,
    goles_visitante     INTEGER DEFAULT -1,
    penaltis_local      INTEGER DEFAULT -1,
    penaltis_visitante  INTEGER DEFAULT -1,
    fecha               TEXT    DEFAULT '',
    estadio             TEXT    DEFAULT '',
    fase                TEXT    DEFAULT NULL,
    jornada             TEXT    DEFAULT NULL,
    jugado              INTEGER DEFAULT 0,
    archivado           INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS goleadores_partido (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    partido_id  INTEGER REFERENCES partidos(id)  ON DELETE CASCADE,
    jugador_id  INTEGER REFERENCES jugadores(id) ON DELETE CASCADE,
    goles       INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS clasificados (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id   INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    fase        TEXT,
    resultado   TEXT    DEFAULT NULL
);
"""

# ────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────

def crear_bd_nueva(ruta):
    conn = sqlite3.connect(ruta)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.row_factory = sqlite3.Row
    return conn

def tablas(conn):
    return {r[0].lower() for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

def columnas(conn, tabla):
    return {r["name"].lower() for r in conn.execute(
        f"PRAGMA table_info({tabla})").fetchall()}

def detectar_tipo(conn, ruta):
    t = tablas(conn)
    nombre = os.path.basename(ruta).lower()
    if "selecciones" in t:
        return "mundial"
    if any(p in nombre for p in ("euro","eurocopa")):
        return "euro"
    if any(p in nombre for p in ("champions","ucl","copa")):
        return "copa"
    return "liga"

def nombre_torneo(ruta):
    return os.path.basename(ruta).replace(".db","").replace("_"," ").title()

# ────────────────────────────────────────────────────────────────────
# MIGRACIÓN DE EQUIPOS
# ────────────────────────────────────────────────────────────────────

def migrar_equipos(src, dst, tipo):
    """
    Detecta la tabla de equipos (equipos / equipo / selecciones / teams)
    y la vuelca al esquema canónico.
    Devuelve dict {id_viejo: id_nuevo}.
    """
    t = tablas(src)
    # Elegir la candidata con más filas (evita tablas residuales vacías)
    _candidatas = [x for x in ("equipos","equipo","selecciones","teams") if x in t]
    tabla = None
    _max_filas = -1
    for _c in _candidatas:
        _n = src.execute(f"SELECT COUNT(*) FROM {_c}").fetchone()[0]
        if _n > _max_filas:
            _max_filas = _n
            tabla = _c
    if not tabla:
        print("  [!] No se encontró tabla de equipos")
        return {}

    cols = columnas(src, tabla)
    col_nombre = next((c for c in ("nombre","name") if c in cols), None)
    col_ciudad  = next((c for c in ("ciudad","city") if c in cols), None)
    col_grupo   = "grupo" if "grupo" in cols else None

    filas = src.execute(f"SELECT * FROM {tabla}").fetchall()
    mapa = {}
    for f in filas:
        nombre  = f[col_nombre] if col_nombre else "?"
        ciudad  = f[col_ciudad] if col_ciudad else ""
        grupo   = f[col_grupo]  if col_grupo  else None
        pj = f["pj"] if "pj" in cols else 0
        pg = f["pg"] if "pg" in cols else (f["wins"]   if "wins"   in cols else 0)
        pe = f["pe"] if "pe" in cols else (f["draws"]  if "draws"  in cols else 0)
        pp = f["pp"] if "pp" in cols else (f["losses"] if "losses" in cols else 0)
        gf = f["gf"] if "gf" in cols else (f["goals_for"]     if "goals_for"     in cols else 0)
        gc = f["gc"] if "gc" in cols else (f["goals_against"]  if "goals_against" in cols else 0)
        pts= f["pts"]if "pts"in cols else (f["points"] if "points" in cols else 0)

        cur = dst.execute(
            "INSERT INTO equipos (nombre,ciudad,grupo,pj,pg,pe,pp,gf,gc,pts) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (nombre, ciudad or "", grupo, pj, pg, pe, pp, gf, gc, pts)
        )
        mapa[f["id"]] = cur.lastrowid

    dst.commit()
    print(f"  Equipos migrados: {len(mapa)}")
    return mapa

# ────────────────────────────────────────────────────────────────────
# MIGRACIÓN DE JUGADORES
# ────────────────────────────────────────────────────────────────────

def migrar_jugadores(src, dst, mapa_equipos):
    t = tablas(src)
    _candidatas_j = [x for x in ("jugadores","players") if x in t]
    tabla = None
    _max_j = -1
    for _c in _candidatas_j:
        _n = src.execute(f"SELECT COUNT(*) FROM {_c}").fetchone()[0]
        if _n > _max_j:
            _max_j = _n
            tabla = _c
    if not tabla:
        print("  [!] No se encontró tabla de jugadores")
        return {}

    cols = columnas(src, tabla)
    col_nombre  = next((c for c in ("nombre","name") if c in cols), None)
    # Detectar la FK real: elegir la columna con más valores no-NULL
    _fk_candidatas = [c for c in ("equipo_id","seleccion_id","team_id") if c in cols]
    col_equipo = None
    for _c in _fk_candidatas:
        _n = src.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {_c} IS NOT NULL AND {_c} != 0").fetchone()[0]
        if _n > 0:
            col_equipo = _c
            break
    if col_equipo is None and _fk_candidatas:
        col_equipo = _fk_candidatas[0]
    col_goles   = next((c for c in ("goles_marcados","goles","goals") if c in cols), None)

    filas = src.execute(f"SELECT * FROM {tabla}").fetchall()
    mapa = {}
    for f in filas:
        nombre   = f[col_nombre]  if col_nombre  else "?"
        equipo_v = f[col_equipo]  if col_equipo  else None
        goles    = f[col_goles]   if col_goles   else 0
        equipo_n = mapa_equipos.get(equipo_v)

        cur = dst.execute(
            "INSERT INTO jugadores (nombre, equipo_id, goles_marcados) VALUES (?,?,?)",
            (nombre, equipo_n, goles or 0)
        )
        mapa[f["id"]] = cur.lastrowid

    dst.commit()
    print(f"  Jugadores migrados: {len(mapa)}")
    return mapa

# ────────────────────────────────────────────────────────────────────
# MIGRACIÓN DE PARTIDOS
# ────────────────────────────────────────────────────────────────────

def migrar_partidos(src, dst, mapa_equipos):
    t = tablas(src)
    # Elegir la candidata con más filas
    _candidatas_p = [x for x in ("partidos","matches") if x in t]
    tabla = None
    _max_p = -1
    for _c in _candidatas_p:
        _n = src.execute(f"SELECT COUNT(*) FROM {_c}").fetchone()[0]
        if _n > _max_p:
            _max_p = _n
            tabla = _c
    if not tabla:
        print("  [!] No se encontró tabla de partidos")
        return {}

    cols = columnas(src, tabla)
    col_loc  = next((c for c in ("equipo_local_id","home_team_id") if c in cols), None)
    col_vis  = next((c for c in ("equipo_visitante_id","away_team_id") if c in cols), None)
    col_gl   = next((c for c in ("goles_local","home_score") if c in cols), None)
    col_gv   = next((c for c in ("goles_visitante","away_score") if c in cols), None)
    col_fecha= next((c for c in ("fecha","date") if c in cols), None)

    filas = src.execute(f"SELECT * FROM {tabla}").fetchall()
    mapa = {}
    for f in filas:
        loc_v = f[col_loc] if col_loc else None
        vis_v = f[col_vis] if col_vis else None
        loc_n = mapa_equipos.get(loc_v)
        vis_n = mapa_equipos.get(vis_v)
        if not loc_n or not vis_n:
            continue

        gl  = f[col_gl]  if col_gl  else -1
        gv  = f[col_gv]  if col_gv  else -1
        if gl is None: gl = -1
        if gv is None: gv = -1

        fecha   = f[col_fecha] if col_fecha else ""
        estadio = f["estadio"] if "estadio" in cols else ""
        fase    = f["fase"]    if "fase"    in cols else None
        jornada = f["jornada"] if "jornada" in cols else None
        pl  = f["penaltis_local"]     if "penaltis_local"     in cols else -1
        pv  = f["penaltis_visitante"] if "penaltis_visitante" in cols else -1
        jugado   = 1 if (gl != -1 and gv != -1) else (f["jugado"] if "jugado" in cols else 0)
        archivado= f["archivado"] if "archivado" in cols else 0

        cur = dst.execute(
            "INSERT INTO partidos "
            "(equipo_local_id,equipo_visitante_id,goles_local,goles_visitante,"
            "penaltis_local,penaltis_visitante,fecha,estadio,"
            "fase,jornada,jugado,archivado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (loc_n, vis_n, gl, gv, pl or -1, pv or -1,
             fecha or "", estadio or "",
             fase, jornada, jugado, archivado or 0)
        )
        mapa[f["id"]] = cur.lastrowid

    dst.commit()
    print(f"  Partidos migrados: {len(mapa)}")
    return mapa

# ────────────────────────────────────────────────────────────────────
# MIGRACIÓN DE GOLEADORES
# ────────────────────────────────────────────────────────────────────

def migrar_goleadores(src, dst, mapa_partidos, mapa_jugadores):
    t = tablas(src)
    tabla = next((x for x in
        ("goleadores_partido","mundial_goleadores","goleadores") if x in t), None)
    if not tabla:
        print("  [!] No se encontró tabla de goleadores")
        return

    cols = columnas(src, tabla)
    filas = src.execute(f"SELECT * FROM {tabla}").fetchall()
    n = 0
    for f in filas:
        pid_v = f["partido_id"]  if "partido_id"  in cols else None
        jid_v = f["jugador_id"]  if "jugador_id"  in cols else None
        goles = f["goles"]       if "goles"       in cols else 0
        pid_n = mapa_partidos.get(pid_v)
        jid_n = mapa_jugadores.get(jid_v)
        if pid_n and jid_n:
            dst.execute(
                "INSERT INTO goleadores_partido (partido_id,jugador_id,goles) VALUES (?,?,?)",
                (pid_n, jid_n, goles or 0)
            )
            n += 1

    dst.commit()
    print(f"  Goleadores migrados: {n}")

# ────────────────────────────────────────────────────────────────────
# MIGRACIÓN DE CLASIFICADOS
# ────────────────────────────────────────────────────────────────────

def migrar_clasificados(src, dst, mapa_equipos):
    t = tablas(src)
    if "clasificados" not in t:
        return
    cols = columnas(src, "clasificados")
    filas = src.execute("SELECT * FROM clasificados").fetchall()
    n = 0
    for f in filas:
        equipo_col = next((c for c in ("equipo_id","equipo") if c in cols), None)
        if not equipo_col:
            continue
        if equipo_col == "equipo_id":
            eid_n = mapa_equipos.get(f["equipo_id"])
        else:
            # es nombre de equipo, buscar id nuevo
            eid_n = dst.execute(
                "SELECT id FROM equipos WHERE nombre=?", (f["equipo"],)
            ).fetchone()
            eid_n = eid_n[0] if eid_n else None

        if eid_n:
            fase = f["fase"] if "fase" in cols else None
            dst.execute(
                "INSERT INTO clasificados (equipo_id, fase) VALUES (?,?)",
                (eid_n, fase)
            )
            n += 1

    dst.commit()
    if n:
        print(f"  Clasificados migrados: {n}")

# ────────────────────────────────────────────────────────────────────
# MIGRACIÓN COMPLETA DE UNA BD
# ────────────────────────────────────────────────────────────────────

def migrar_bd(ruta_origen):
    nombre = nombre_torneo(ruta_origen)
    base   = os.path.splitext(ruta_origen)[0]
    ruta_destino = base + "_v2.db"

    if os.path.exists(ruta_destino):
        os.remove(ruta_destino)

    src = sqlite3.connect(ruta_origen)
    src.row_factory = sqlite3.Row
    dst = crear_bd_nueva(ruta_destino)

    tipo = detectar_tipo(src, ruta_origen)
    temporada = ""  # se puede editar después desde la app

    dst.execute(
        "INSERT INTO torneo_info (nombre, tipo, temporada) VALUES (?,?,?)",
        (nombre, tipo, temporada)
    )
    dst.commit()

    print(f"\n{'─'*50}")
    print(f"  Migrando: {nombre}  [{tipo}]")
    print(f"  Origen:   {ruta_origen}")
    print(f"  Destino:  {ruta_destino}")
    print(f"{'─'*50}")

    mapa_eq  = migrar_equipos(src, dst, tipo)
    mapa_jug = migrar_jugadores(src, dst, mapa_eq)
    mapa_par = migrar_partidos(src, dst, mapa_eq)
    migrar_goleadores(src, dst, mapa_par, mapa_jug)
    migrar_clasificados(src, dst, mapa_eq)

    src.close()
    dst.close()
    print(f"  [OK] {ruta_destino}")
    return ruta_destino

# ────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Tk()
    root.withdraw()

    print("Selecciona las BDs a migrar (puedes seleccionar varias con Ctrl+clic)")
    rutas = filedialog.askopenfilenames(
        title="Selecciona las bases de datos a migrar",
        filetypes=[("SQLite", "*.db")],
        parent=root
    )
    root.destroy()

    if not rutas:
        print("Cancelado.")
        sys.exit()

    migradas = []
    errores  = []

    for ruta in rutas:
        try:
            dest = migrar_bd(ruta)
            migradas.append(dest)
        except Exception as e:
            import traceback
            print(f"\n[ERROR] {ruta}: {e}")
            traceback.print_exc()
            errores.append(ruta)

    print(f"\n{'='*50}")
    print(f"Migración completada.")
    print(f"  OK:    {len(migradas)} archivos")
    if errores:
        print(f"  Error: {len(errores)} archivos")
        for e in errores:
            print(f"    - {e}")
    print(f"\nArchivos nuevos:")
    for m in migradas:
        print(f"  {m}")
    print(f"\nPuedes abrir los _v2.db con la app maestra.")
