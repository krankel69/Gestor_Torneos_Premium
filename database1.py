# database.py  —  Cerebro de datos universal
# Soporta cualquier esquema: liga (equipos/jugadores/partidos),
# mundial (selecciones + fase en partidos), o mixto bilingue
# (teams/players/matches junto a equipos/jugadores/partidos).

import sqlite3
from collections import defaultdict


class GestorBaseDeDatos:

    # Tablas canonicas -> alternativas aceptadas
    _TABLA_EQUIPOS = ("equipos", "selecciones", "teams")
    _TABLA_JUGADORES = ("jugadores", "players")
    _TABLA_PARTIDOS = ("partidos", "matches")
    _TABLA_GOLEADORES_PARTIDO = ("goleadores_partido", "mundial_goleadores")

    # Columnas canonicas -> alternativas por tabla
    _COLS_EQUIPOS = {
        "id": ("id",),
        "nombre": ("nombre", "name"),
        "ciudad": ("ciudad", "city", "grupo"),
        "pj": ("pj",),
        "pg": ("pg", "wins"),
        "pe": ("pe", "draws"),
        "pp": ("pp", "losses"),
        "gf": ("gf", "goals_for"),
        "gc": ("gc", "goals_against"),
        "pts": ("pts", "points"),
    }
    _COLS_JUGADORES = {
        "id": ("id",),
        "nombre": ("nombre", "name"),
        "equipo_id": ("equipo_id", "seleccion_id", "team_id"),
        "goles_marcados": ("goles_marcados", "goles", "goals"),
    }
    _COLS_PARTIDOS = {
        "id": ("id",),
        "equipo_local_id": ("equipo_local_id", "home_team_id"),
        "equipo_visitante_id": ("equipo_visitante_id", "away_team_id"),
        "goles_local": ("goles_local", "home_score"),
        "goles_visitante": ("goles_visitante", "away_score"),
        "fecha": ("fecha", "date"),
        "jugado": ("jugado",),
        "archivado": ("archivado",),
        "fase": ("fase",),
    }

    # ----------------------------------------------------------------
    def __init__(self, db_path):
        self.db_name = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self._tablas_existentes = self._listar_tablas()
        self._detectar_todo()
        self._crear_tablas_faltantes()
        self._migrar_columnas()
        # Re-detectar tras posibles creaciones
        self._tablas_existentes = self._listar_tablas()
        self._detectar_todo()

    def _detectar_todo(self):
        self._t_equipos = self._detectar_tabla(self._TABLA_EQUIPOS)
        self._t_jugadores = self._detectar_tabla(self._TABLA_JUGADORES)
        self._t_partidos = self._detectar_tabla(self._TABLA_PARTIDOS)
        self._t_goleadores = self._detectar_tabla(self._TABLA_GOLEADORES_PARTIDO)
        self._c_eq = self._mapear_columnas(self._t_equipos, self._COLS_EQUIPOS)
        self._c_jug = self._mapear_columnas(self._t_jugadores, self._COLS_JUGADORES)
        self._c_par = self._mapear_columnas(self._t_partidos, self._COLS_PARTIDOS)

    def _listar_tablas(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {r[0].lower() for r in self.cursor.fetchall()}

    def _detectar_tabla(self, candidatas):
        for t in candidatas:
            if t.lower() in self._tablas_existentes:
                return t
        return candidatas[0]

    def _columnas_de_tabla(self, tabla):
        try:
            self.cursor.execute(f"PRAGMA table_info({tabla})")
            return {r["name"].lower() for r in self.cursor.fetchall()}
        except Exception:
            return set()

    def _mapear_columnas(self, tabla, mapa):
        cols = self._columnas_de_tabla(tabla)
        resultado = {}
        for canon, alts in mapa.items():
            for alt in alts:
                if alt.lower() in cols:
                    resultado[canon] = alt
                    break
            else:
                resultado[canon] = None
        return resultado

    # ----------------------------------------------------------------
    # Creacion y migracion
    # ----------------------------------------------------------------

    def _crear_tablas_faltantes(self):
        if not any(t in self._tablas_existentes for t in self._TABLA_EQUIPOS):
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE, ciudad TEXT DEFAULT '',
                    pj INTEGER DEFAULT 0, pg INTEGER DEFAULT 0,
                    pe INTEGER DEFAULT 0, pp INTEGER DEFAULT 0,
                    gf INTEGER DEFAULT 0, gc INTEGER DEFAULT 0, pts INTEGER DEFAULT 0
                )""")
        if not any(t in self._tablas_existentes for t in self._TABLA_JUGADORES):
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS jugadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL, equipo_id INTEGER,
                    goles_marcados INTEGER DEFAULT 0
                )""")
        if not any(t in self._tablas_existentes for t in self._TABLA_PARTIDOS):
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS partidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipo_local_id INTEGER, equipo_visitante_id INTEGER,
                    goles_local INTEGER DEFAULT -1, goles_visitante INTEGER DEFAULT -1,
                    fecha TEXT, jugado INTEGER DEFAULT 0, archivado INTEGER DEFAULT 0
                )""")
        if not any(t in self._tablas_existentes for t in self._TABLA_GOLEADORES_PARTIDO):
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS goleadores_partido (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partido_id INTEGER, jugador_id INTEGER, goles INTEGER DEFAULT 0
                )""")
        self.conn.commit()

    def _migrar_columnas(self):
        migraciones = [
            (self._t_equipos, "ciudad", "TEXT DEFAULT ''"),
            (self._t_jugadores, "goles_marcados", "INTEGER DEFAULT 0"),
            (self._t_jugadores, "equipo_id", "INTEGER"),
            (self._t_partidos, "jugado", "INTEGER DEFAULT 0"),
            (self._t_partidos, "archivado", "INTEGER DEFAULT 0"),
            (self._t_partidos, "fecha", "TEXT"),
        ]
        for tabla, col, defn in migraciones:
            try:
                self.cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {defn}")
                self.conn.commit()
            except Exception:
                pass
        # Sincronizar flag jugado con convencion -1=pendiente
        try:
            m = self._c_par
            gl = m.get("goles_local") or "goles_local"
            gv = m.get("goles_visitante") or "goles_visitante"
            self.cursor.execute(f"UPDATE {self._t_partidos} SET jugado=1 WHERE {gl}!=-1 AND {gv}!=-1 AND jugado=0")
            self.conn.commit()
        except Exception:
            pass

    # ----------------------------------------------------------------
    # Helpers internos
    # ----------------------------------------------------------------

    def _sel_equipos(self):
        m = self._c_eq
        cols = []
        for c in ("id", "nombre", "ciudad", "pj", "pg", "pe", "pp", "gf", "gc", "pts"):
            real = m.get(c)
            if real:
                cols.append(f"{real} AS {c}" if real != c else real)
            else:
                cols.append(f"0 AS {c}" if c not in ("nombre", "ciudad") else f"'' AS {c}")
        return ", ".join(cols)

    # ----------------------------------------------------------------
    # Equipos
    # ----------------------------------------------------------------

    def close_db(self):
        self.conn.close()

    def obtener_nombres_equipos(self):
        col = self._c_eq.get("nombre") or "nombre"
        self.cursor.execute(f"SELECT {col} AS nombre FROM {self._t_equipos} ORDER BY {col}")
        return [r["nombre"] for r in self.cursor.fetchall()]

    def obtener_equipos(self):
        self.cursor.execute(f"SELECT {self._sel_equipos()} FROM {self._t_equipos} ORDER BY nombre")
        return self.cursor.fetchall()

    def obtener_id_equipo(self, nombre):
        col = self._c_eq.get("nombre") or "nombre"
        self.cursor.execute(f"SELECT id FROM {self._t_equipos} WHERE {col}=?", (nombre,))
        res = self.cursor.fetchone()
        return res["id"] if res else None

    def agregar_equipo(self, nombre, ciudad=""):
        cn = self._c_eq.get("nombre") or "nombre"
        cc = self._c_eq.get("ciudad") or "ciudad"
        try:
            self.cursor.execute(f"INSERT INTO {self._t_equipos} ({cn},{cc}) VALUES (?,?)", (nombre, ciudad))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_equipo_por_nombre(self, nombre):
        col = self._c_eq.get("nombre") or "nombre"
        self.cursor.execute(f"DELETE FROM {self._t_equipos} WHERE {col}=?", (nombre,))
        self.conn.commit()

    def actualizar_clasificacion_manual(self, nombre, pj, pg, pe, pp, gf, gc, pts):
        eid = self.obtener_id_equipo(nombre)
        if not eid:
            return
        m = self._c_eq
        self.cursor.execute(
            f"""
            UPDATE {self._t_equipos}
            SET {m.get('pj','pj')}=?, {m.get('pg','pg')}=?, {m.get('pe','pe')}=?,
                {m.get('pp','pp')}=?, {m.get('gf','gf')}=?, {m.get('gc','gc')}=?,
                {m.get('pts','pts')}=?
            WHERE id=?
        """,
            (pj, pg, pe, pp, gf, gc, pts, eid),
        )
        self.conn.commit()

    # ----------------------------------------------------------------
    # Jugadores
    # ----------------------------------------------------------------

    def obtener_id_jugador(self, nombre):
        col = self._c_jug.get("nombre") or "nombre"
        self.cursor.execute(f"SELECT id FROM {self._t_jugadores} WHERE {col}=?", (nombre,))
        res = self.cursor.fetchone()
        return res["id"] if res else None

    def obtener_jugadores_completo(self):
        t_j = self._t_jugadores
        t_e = self._t_equipos
        m_j = self._c_jug
        m_e = self._c_eq
        jid = m_j.get("id") or "id"
        jnomb = m_j.get("nombre") or "nombre"
        jgol = m_j.get("goles_marcados") or "goles_marcados"
        jeid = m_j.get("equipo_id") or "equipo_id"
        enomb = m_e.get("nombre") or "nombre"
        self.cursor.execute(f"""
            SELECT j.{jid} AS id, j.{jnomb} AS nombre,
                   e.{enomb} AS equipo_nombre,
                   j.{jgol} AS goles_marcados
            FROM {t_j} j
            LEFT JOIN {t_e} e ON j.{jeid} = e.id
            ORDER BY j.{jnomb}
        """)
        return self.cursor.fetchall()

    def obtener_jugadores_por_equipo(self, nombre_equipo):
        eid = self.obtener_id_equipo(nombre_equipo)
        if eid:
            col = self._c_jug.get("equipo_id") or "equipo_id"
            self.cursor.execute(f"SELECT * FROM {self._t_jugadores} WHERE {col}=? ORDER BY nombre", (eid,))
            return self.cursor.fetchall()
        return []

    def agregar_jugador(self, nombre_jugador, nombre_equipo):
        eid = self.obtener_id_equipo(nombre_equipo)
        if eid:
            cn = self._c_jug.get("nombre") or "nombre"
            ce = self._c_jug.get("equipo_id") or "equipo_id"
            self.cursor.execute(f"INSERT INTO {self._t_jugadores} ({cn},{ce}) VALUES (?,?)", (nombre_jugador, eid))
            self.conn.commit()

    def eliminar_jugador_por_nombre(self, nombre):
        col = self._c_jug.get("nombre") or "nombre"
        self.cursor.execute(f"DELETE FROM {self._t_jugadores} WHERE {col}=?", (nombre,))
        self.conn.commit()

    def obtener_goleadores_top(self):
        t_j = self._t_jugadores
        t_e = self._t_equipos
        m_j = self._c_jug
        m_e = self._c_eq
        cg = m_j.get("goles_marcados") or "goles_marcados"
        cjn = m_j.get("nombre") or "nombre"
        cen = m_e.get("nombre") or "nombre"
        cej = m_j.get("equipo_id") or "equipo_id"
        self.cursor.execute(f"""
            SELECT j.{cjn} AS jugador, e.{cen} AS equipo, j.{cg} AS goles
            FROM {t_j} j JOIN {t_e} e ON j.{cej}=e.id
            WHERE j.{cg}>0 ORDER BY j.{cg} DESC
        """)
        return self.cursor.fetchall()

    def recalcular_goleadores_totales(self):
        cg = self._c_jug.get("goles_marcados") or "goles_marcados"
        self.cursor.execute(f"UPDATE {self._t_jugadores} SET {cg}=0")
        self.cursor.execute(f"SELECT jugador_id, SUM(goles) AS total FROM {self._t_goleadores} GROUP BY jugador_id")
        for g in self.cursor.fetchall():
            self.cursor.execute(f"UPDATE {self._t_jugadores} SET {cg}=? WHERE id=?", (g["total"], g["jugador_id"]))
        self.conn.commit()

    def establecer_goles_totales_manual(self, nombre_jugador, nuevo_total):
        jid = self.obtener_id_jugador(nombre_jugador)
        if jid:
            cg = self._c_jug.get("goles_marcados") or "goles_marcados"
            self.cursor.execute(f"UPDATE {self._t_jugadores} SET {cg}=? WHERE id=?", (nuevo_total, jid))
            self.conn.commit()
            return True
        return False

    # ----------------------------------------------------------------
    # Partidos
    # ----------------------------------------------------------------

    def _q_partidos_base(self):
        m = self._c_par
        m_e = self._c_eq
        t = self._t_partidos
        t_e = self._t_equipos
        gl = m.get("goles_local") or "goles_local"
        gv = m.get("goles_visitante") or "goles_visitante"
        cf = m.get("fecha") or "fecha"
        cj = m.get("jugado") or "jugado"
        ca = m.get("archivado") or "archivado"
        cl = m.get("equipo_local_id") or "equipo_local_id"
        cv = m.get("equipo_visitante_id") or "equipo_visitante_id"
        cen = m_e.get("nombre") or "nombre"
        extra = f", p.{m['fase']} AS fase" if m.get("fase") else ""
        return f"""
            SELECT p.id,
                   el.{cen} AS nombre_equipo_local,
                   ev.{cen} AS nombre_equipo_visitante,
                   p.{gl}   AS goles_local,
                   p.{gv}   AS goles_visitante,
                   p.{cf}   AS fecha,
                   p.{cj}   AS jugado,
                   COALESCE(p.{ca},0) AS archivado
                   {extra}
            FROM {t} p
            JOIN {t_e} el ON p.{cl}=el.id
            JOIN {t_e} ev ON p.{cv}=ev.id
        """

    def obtener_partidos_con_equipos(self, fecha_filtro=None, mostrar_archivados=0):
        m = self._c_par
        ca = m.get("archivado") or "archivado"
        cf = m.get("fecha") or "fecha"
        q = self._q_partidos_base() + f" WHERE COALESCE(p.{ca},0)=?"
        params = [mostrar_archivados]
        if fecha_filtro and fecha_filtro not in ("-- Ver Todos los Partidos --", "-- Archivo Histórico --"):
            q += f" AND p.{cf}=?"
            params.append(fecha_filtro)
        q += f" ORDER BY p.{cf} DESC, p.id DESC"
        self.cursor.execute(q, params)
        return self.cursor.fetchall()

    def obtener_jornadas(self, mostrar_archivados=0):
        m = self._c_par
        cf = m.get("fecha") or "fecha"
        ca = m.get("archivado") or "archivado"
        try:
            self.cursor.execute(f"SELECT DISTINCT {cf} AS fecha FROM {self._t_partidos} " f"WHERE COALESCE({ca},0)=? ORDER BY {cf} DESC", (mostrar_archivados,))
            return [r["fecha"] for r in self.cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

    def agregar_partido(self, local, visitante, fecha):
        id_l = self.obtener_id_equipo(local)
        id_v = self.obtener_id_equipo(visitante)
        if id_l and id_v:
            m = self._c_par
            cl = m.get("equipo_local_id") or "equipo_local_id"
            cv = m.get("equipo_visitante_id") or "equipo_visitante_id"
            cf = m.get("fecha") or "fecha"
            self.cursor.execute(f"INSERT INTO {self._t_partidos} ({cl},{cv},{cf},jugado) VALUES (?,?,?,0)", (id_l, id_v, fecha))
            self.conn.commit()
            return True
        return False

    def registrar_resultado_partido(self, partido_id, goles_local, goles_visitante):
        m = self._c_par
        gl = m.get("goles_local") or "goles_local"
        gv = m.get("goles_visitante") or "goles_visitante"
        self.cursor.execute(f"UPDATE {self._t_partidos} SET {gl}=?,{gv}=?,jugado=1 WHERE id=?", (goles_local, goles_visitante, partido_id))
        self.conn.commit()

    def eliminar_partido_por_id(self, partido_id):
        self.cursor.execute(f"DELETE FROM {self._t_partidos} WHERE id=?", (partido_id,))
        self.conn.commit()

    def limpiar_partidos_pendientes(self):
        self.cursor.execute(f"SELECT COUNT(*) FROM {self._t_partidos} WHERE jugado=0")
        n = self.cursor.fetchone()[0]
        self.cursor.execute(f"DELETE FROM {self._t_partidos} WHERE jugado=0")
        self.conn.commit()
        return n

    def toggle_archivo_partido(self, partido_id, estado):
        self.cursor.execute(f"UPDATE {self._t_partidos} SET archivado=? WHERE id=?", (estado, partido_id))
        self.conn.commit()

    # ----------------------------------------------------------------
    # Goleadores por partido
    # ----------------------------------------------------------------

    def obtener_goleadores_por_partido(self, partido_id):
        t_g = self._t_goleadores
        t_j = self._t_jugadores
        cn = self._c_jug.get("nombre") or "nombre"
        self.cursor.execute(
            f"""
            SELECT j.{cn} AS jugador, gp.goles
            FROM {t_g} gp LEFT JOIN {t_j} j ON gp.jugador_id=j.id
            WHERE gp.partido_id=?
        """,
            (partido_id,),
        )
        return self.cursor.fetchall()

    def insertar_goleador(self, partido_id, nombre_jugador, cantidad_goles):
        if nombre_jugador == "(Propia Puerta)":
            return
        jid = self.obtener_id_jugador(nombre_jugador)
        if jid:
            self.cursor.execute(f"INSERT INTO {self._t_goleadores} (partido_id,jugador_id,goles) VALUES (?,?,?)", (partido_id, jid, cantidad_goles))
            self.conn.commit()

    def limpiar_goleadores_de_partido(self, partido_id):
        self.cursor.execute(f"DELETE FROM {self._t_goleadores} WHERE partido_id=?", (partido_id,))
        self.conn.commit()

    # ----------------------------------------------------------------
    # Clasificacion
    # ----------------------------------------------------------------

    def recalcular_y_obtener_clasificacion(self):
        m_e = self._c_eq
        m_p = self._c_par
        t_e = self._t_equipos
        t_p = self._t_partidos
        pj = m_e.get("pj", "pj")
        pg = m_e.get("pg", "pg")
        pe = m_e.get("pe", "pe")
        pp = m_e.get("pp", "pp")
        gf = m_e.get("gf", "gf")
        gc = m_e.get("gc", "gc")
        pts = m_e.get("pts", "pts")
        gl = m_p.get("goles_local") or "goles_local"
        gv = m_p.get("goles_visitante") or "goles_visitante"
        cl = m_p.get("equipo_local_id") or "equipo_local_id"
        cv = m_p.get("equipo_visitante_id") or "equipo_visitante_id"

        self.cursor.execute(f"UPDATE {t_e} SET {pj}=0,{pg}=0,{pe}=0,{pp}=0,{gf}=0,{gc}=0,{pts}=0")
        self.cursor.execute(f"SELECT * FROM {t_p} WHERE jugado=1")
        for p in self.cursor.fetchall():
            g_l, g_v = p[gl], p[gv]
            id_l, id_v = p[cl], p[cv]
            self.cursor.execute(f"UPDATE {t_e} SET {gf}={gf}+?,{gc}={gc}+?,{pj}={pj}+1 WHERE id=?", (g_l, g_v, id_l))
            self.cursor.execute(f"UPDATE {t_e} SET {gf}={gf}+?,{gc}={gc}+?,{pj}={pj}+1 WHERE id=?", (g_v, g_l, id_v))
            if g_l > g_v:
                self.cursor.execute(f"UPDATE {t_e} SET {pg}={pg}+1,{pts}={pts}+3 WHERE id=?", (id_l,))
                self.cursor.execute(f"UPDATE {t_e} SET {pp}={pp}+1 WHERE id=?", (id_v,))
            elif g_v > g_l:
                self.cursor.execute(f"UPDATE {t_e} SET {pp}={pp}+1 WHERE id=?", (id_l,))
                self.cursor.execute(f"UPDATE {t_e} SET {pg}={pg}+1,{pts}={pts}+3 WHERE id=?", (id_v,))
            else:
                self.cursor.execute(f"UPDATE {t_e} SET {pe}={pe}+1,{pts}={pts}+1 WHERE id=?", (id_l,))
                self.cursor.execute(f"UPDATE {t_e} SET {pe}={pe}+1,{pts}={pts}+1 WHERE id=?", (id_v,))
        self.conn.commit()
        return self.obtener_clasificacion_actual()

    def obtener_clasificacion_actual(self):
        m = self._c_eq
        pts_c = m.get("pts", "pts")
        gf_c = m.get("gf", "gf")
        gc_c = m.get("gc", "gc")
        self.cursor.execute(f"""
            SELECT {self._sel_equipos()} FROM {self._t_equipos}
            ORDER BY {pts_c} DESC, ({gf_c}-{gc_c}) DESC, {gf_c} DESC
        """)
        equipos = [dict(r) for r in self.cursor.fetchall()]

        grupos = defaultdict(list)
        for eq in equipos:
            grupos[eq["pts"]].append(eq)

        m_p = self._c_par
        gl = m_p.get("goles_local") or "goles_local"
        gv = m_p.get("goles_visitante") or "goles_visitante"
        cl = m_p.get("equipo_local_id") or "equipo_local_id"
        cv = m_p.get("equipo_visitante_id") or "equipo_visitante_id"

        clasificacion_final = []
        for pts in sorted(grupos.keys(), reverse=True):
            grupo = grupos[pts]
            if len(grupo) == 1:
                clasificacion_final.append(grupo[0])
                continue
            ids = tuple(eq["id"] for eq in grupo)
            mini = {eq["id"]: {"pts_mini": 0, "dif_mini": 0, "orig": eq} for eq in grupo}
            ph = ",".join("?" * len(ids))
            self.cursor.execute(
                f"""
                SELECT {cl} AS equipo_local_id, {cv} AS equipo_visitante_id,
                       {gl} AS goles_local,     {gv} AS goles_visitante
                FROM {self._t_partidos}
                WHERE jugado=1 AND {cl} IN ({ph}) AND {cv} IN ({ph})
            """,
                ids + ids,
            )
            for p in self.cursor.fetchall():
                il, iv = p["equipo_local_id"], p["equipo_visitante_id"]
                g_l, g_v = p["goles_local"], p["goles_visitante"]
                mini[il]["dif_mini"] += g_l - g_v
                mini[iv]["dif_mini"] += g_v - g_l
                if g_l > g_v:
                    mini[il]["pts_mini"] += 3
                elif g_v > g_l:
                    mini[iv]["pts_mini"] += 3
                else:
                    mini[il]["pts_mini"] += 1
                    mini[iv]["pts_mini"] += 1
            for item in sorted(mini.values(), key=lambda x: (x["pts_mini"], x["dif_mini"], x["orig"]["gf"] - x["orig"]["gc"], x["orig"]["gf"]), reverse=True):
                clasificacion_final.append(item["orig"])

        return clasificacion_final
