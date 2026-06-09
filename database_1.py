# database.py  —  Gestor de datos universal v2
# Esquema canónico: una sola estructura para todos los torneos.
# Sin detección dinámica, sin mapeos. SQL limpio y directo.

import sqlite3
import os
from collections import defaultdict


class GestorBaseDeDatos:

    def __init__(self, db_path):
        self.db_name = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._crear_tablas()
        self._cargar_info()

    # ----------------------------------------------------------------
    # Esquema
    # ----------------------------------------------------------------

    def _crear_tablas(self):
        self.conn.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS torneo_info (
            id        INTEGER PRIMARY KEY,
            nombre    TEXT NOT NULL,
            tipo      TEXT NOT NULL DEFAULT 'liga',
            temporada TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS equipos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT NOT NULL UNIQUE,
            ciudad  TEXT DEFAULT '',
            grupo   TEXT DEFAULT NULL,
            pj      INTEGER DEFAULT 0, pg INTEGER DEFAULT 0,
            pe      INTEGER DEFAULT 0, pp INTEGER DEFAULT 0,
            gf      INTEGER DEFAULT 0, gc INTEGER DEFAULT 0,
            pts     INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS jugadores (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT NOT NULL,
            equipo_id      INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            goles_marcados INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS partidos (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            local_id           INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            visitante_id       INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            goles_local        INTEGER DEFAULT -1,
            goles_visitante    INTEGER DEFAULT -1,
            penaltis_local     INTEGER DEFAULT -1,
            penaltis_visitante INTEGER DEFAULT -1,
            fecha              TEXT DEFAULT '',
            estadio            TEXT DEFAULT '',
            fase               TEXT DEFAULT NULL,
            jornada            TEXT DEFAULT NULL,
            jugado             INTEGER DEFAULT 0,
            archivado          INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS goleadores_partido (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            partido_id INTEGER REFERENCES partidos(id)  ON DELETE CASCADE,
            jugador_id INTEGER REFERENCES jugadores(id) ON DELETE CASCADE,
            goles      INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS clasificados (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            fase      TEXT,
            resultado TEXT DEFAULT NULL
        );
        """)
        self.conn.commit()

    def _cargar_info(self):
        """Lee la fila de torneo_info para saber tipo y nombre."""
        row = self.cursor.execute(
            "SELECT nombre, tipo, temporada FROM torneo_info LIMIT 1"
        ).fetchone()
        if row:
            self.torneo_nombre   = row["nombre"]
            self.tipo_torneo     = row["tipo"]
            self.torneo_temporada = row["temporada"]
        else:
            # BD nueva sin info todavia
            self.torneo_nombre    = os.path.basename(self.db_name).replace(".db","")
            self.tipo_torneo      = "liga"
            self.torneo_temporada = ""

    # ----------------------------------------------------------------
    # Torneo info
    # ----------------------------------------------------------------

    def guardar_info_torneo(self, nombre, tipo, temporada=""):
        self.cursor.execute("DELETE FROM torneo_info")
        self.cursor.execute(
            "INSERT INTO torneo_info (nombre, tipo, temporada) VALUES (?,?,?)",
            (nombre, tipo, temporada)
        )
        self.conn.commit()
        self._cargar_info()

    def close_db(self):
        self.conn.close()

    # ----------------------------------------------------------------
    # Equipos
    # ----------------------------------------------------------------

    def obtener_equipos(self):
        return self.cursor.execute(
            "SELECT * FROM equipos ORDER BY pts DESC, (gf-gc) DESC, gf DESC"
        ).fetchall()

    def obtener_nombres_equipos(self):
        return [r["nombre"] for r in self.cursor.execute(
            "SELECT nombre FROM equipos ORDER BY nombre"
        ).fetchall()]

    def obtener_id_equipo(self, nombre):
        r = self.cursor.execute(
            "SELECT id FROM equipos WHERE nombre=?", (nombre,)
        ).fetchone()
        return r["id"] if r else None

    def agregar_equipo(self, nombre, ciudad="", grupo=None):
        try:
            self.cursor.execute(
                "INSERT INTO equipos (nombre, ciudad, grupo) VALUES (?,?,?)",
                (nombre, ciudad, grupo)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_equipo_por_nombre(self, nombre):
        self.cursor.execute("DELETE FROM equipos WHERE nombre=?", (nombre,))
        self.conn.commit()

    def actualizar_clasificacion_manual(self, nombre, pj, pg, pe, pp, gf, gc, pts):
        eid = self.obtener_id_equipo(nombre)
        if eid:
            self.cursor.execute(
                "UPDATE equipos SET pj=?,pg=?,pe=?,pp=?,gf=?,gc=?,pts=? WHERE id=?",
                (pj, pg, pe, pp, gf, gc, pts, eid)
            )
            self.conn.commit()

    # ----------------------------------------------------------------
    # Jugadores
    # ----------------------------------------------------------------

    def obtener_id_jugador(self, nombre):
        r = self.cursor.execute(
            "SELECT id FROM jugadores WHERE nombre=?", (nombre,)
        ).fetchone()
        return r["id"] if r else None

    def obtener_jugadores_completo(self):
        return self.cursor.execute("""
            SELECT j.id, j.nombre, e.nombre AS equipo_nombre, j.goles_marcados
            FROM jugadores j
            LEFT JOIN equipos e ON j.equipo_id = e.id
            ORDER BY j.nombre
        """).fetchall()

    def obtener_jugadores_por_equipo(self, nombre_equipo):
        eid = self.obtener_id_equipo(nombre_equipo)
        if eid:
            return self.cursor.execute(
                "SELECT * FROM jugadores WHERE equipo_id=? ORDER BY nombre", (eid,)
            ).fetchall()
        return []

    def agregar_jugador(self, nombre_jugador, nombre_equipo):
        eid = self.obtener_id_equipo(nombre_equipo)
        if eid:
            self.cursor.execute(
                "INSERT INTO jugadores (nombre, equipo_id) VALUES (?,?)",
                (nombre_jugador, eid)
            )
            self.conn.commit()

    def eliminar_jugador_por_nombre(self, nombre):
        self.cursor.execute("DELETE FROM jugadores WHERE nombre=?", (nombre,))
        self.conn.commit()

    def obtener_goleadores_top(self):
        return self.cursor.execute("""
            SELECT j.nombre AS jugador, e.nombre AS equipo, j.goles_marcados AS goles
            FROM jugadores j
            JOIN equipos e ON j.equipo_id = e.id
            WHERE j.goles_marcados > 0
            ORDER BY j.goles_marcados DESC
        """).fetchall()

    def recalcular_goleadores_totales(self):
        self.cursor.execute("UPDATE jugadores SET goles_marcados = 0")
        for g in self.cursor.execute(
            "SELECT jugador_id, SUM(goles) AS total FROM goleadores_partido GROUP BY jugador_id"
        ).fetchall():
            self.cursor.execute(
                "UPDATE jugadores SET goles_marcados=? WHERE id=?",
                (g["total"], g["jugador_id"])
            )
        self.conn.commit()

    def establecer_goles_totales_manual(self, nombre_jugador, nuevo_total):
        jid = self.obtener_id_jugador(nombre_jugador)
        if jid:
            self.cursor.execute(
                "UPDATE jugadores SET goles_marcados=? WHERE id=?", (nuevo_total, jid)
            )
            self.conn.commit()
            return True
        return False

    # ----------------------------------------------------------------
    # Partidos
    # ----------------------------------------------------------------

    def obtener_partidos_con_equipos(self, fecha_filtro=None, mostrar_archivados=0,
                                      fase_filtro=None):
        q = """
            SELECT p.id,
                   el.nombre AS nombre_equipo_local,
                   ev.nombre AS nombre_equipo_visitante,
                   p.goles_local, p.goles_visitante,
                   p.penaltis_local, p.penaltis_visitante,
                   p.fecha, p.estadio, p.fase, p.jornada,
                   p.jugado, p.archivado
            FROM partidos p
            JOIN equipos el ON p.local_id    = el.id
            JOIN equipos ev ON p.visitante_id = ev.id
            WHERE p.archivado = ?
        """
        params = [mostrar_archivados]

        if fecha_filtro and fecha_filtro not in (
            "-- Ver Todos los Partidos --", "-- Archivo Histórico --"
        ):
            q += " AND p.fecha = ?"
            params.append(fecha_filtro)

        if fase_filtro:
            q += " AND p.fase = ?"
            params.append(fase_filtro)

        q += " ORDER BY p.fecha DESC, p.id DESC"
        return self.cursor.execute(q, params).fetchall()

    def obtener_jornadas(self, mostrar_archivados=0):
        try:
            return [r["fecha"] for r in self.cursor.execute(
                "SELECT DISTINCT fecha FROM partidos WHERE archivado=? ORDER BY fecha DESC",
                (mostrar_archivados,)
            ).fetchall()]
        except sqlite3.OperationalError:
            return []

    def obtener_fases(self):
        return [r["fase"] for r in self.cursor.execute(
            "SELECT DISTINCT fase FROM partidos WHERE fase IS NOT NULL ORDER BY fase"
        ).fetchall()]

    def agregar_partido(self, local, visitante, fecha, fase=None, jornada=None, estadio=""):
        id_l = self.obtener_id_equipo(local)
        id_v = self.obtener_id_equipo(visitante)
        if id_l and id_v:
            self.cursor.execute(
                "INSERT INTO partidos (local_id, visitante_id, fecha, fase, jornada, estadio) "
                "VALUES (?,?,?,?,?,?)",
                (id_l, id_v, fecha, fase, jornada, estadio)
            )
            self.conn.commit()
            return True
        return False

    def registrar_resultado_partido(self, partido_id, goles_local, goles_visitante,
                                     penaltis_local=-1, penaltis_visitante=-1):
        self.cursor.execute(
            "UPDATE partidos SET goles_local=?, goles_visitante=?, "
            "penaltis_local=?, penaltis_visitante=?, jugado=1 WHERE id=?",
            (goles_local, goles_visitante, penaltis_local, penaltis_visitante, partido_id)
        )
        self.conn.commit()

    def eliminar_partido_por_id(self, partido_id):
        self.cursor.execute("DELETE FROM partidos WHERE id=?", (partido_id,))
        self.conn.commit()

    def limpiar_partidos_pendientes(self):
        n = self.cursor.execute(
            "SELECT COUNT(*) FROM partidos WHERE jugado=0"
        ).fetchone()[0]
        self.cursor.execute("DELETE FROM partidos WHERE jugado=0")
        self.conn.commit()
        return n

    def toggle_archivo_partido(self, partido_id, estado):
        self.cursor.execute(
            "UPDATE partidos SET archivado=? WHERE id=?", (estado, partido_id)
        )
        self.conn.commit()

    # ----------------------------------------------------------------
    # Goleadores por partido
    # ----------------------------------------------------------------

    def obtener_goleadores_por_partido(self, partido_id):
        return self.cursor.execute("""
            SELECT j.nombre AS jugador, gp.goles
            FROM goleadores_partido gp
            LEFT JOIN jugadores j ON gp.jugador_id = j.id
            WHERE gp.partido_id = ?
        """, (partido_id,)).fetchall()

    def insertar_goleador(self, partido_id, nombre_jugador, cantidad_goles):
        if nombre_jugador == "(Propia Puerta)":
            return
        jid = self.obtener_id_jugador(nombre_jugador)
        if jid:
            self.cursor.execute(
                "INSERT INTO goleadores_partido (partido_id, jugador_id, goles) VALUES (?,?,?)",
                (partido_id, jid, cantidad_goles)
            )
            self.conn.commit()

    def limpiar_goleadores_de_partido(self, partido_id):
        self.cursor.execute(
            "DELETE FROM goleadores_partido WHERE partido_id=?", (partido_id,)
        )
        self.conn.commit()

    # ----------------------------------------------------------------
    # Clasificados (eliminatorias)
    # ----------------------------------------------------------------

    def registrar_clasificado(self, nombre_equipo, fase, resultado=None):
        eid = self.obtener_id_equipo(nombre_equipo)
        if eid:
            self.cursor.execute(
                "INSERT INTO clasificados (equipo_id, fase, resultado) VALUES (?,?,?)",
                (eid, fase, resultado)
            )
            self.conn.commit()

    def obtener_clasificados_por_fase(self, fase):
        return self.cursor.execute("""
            SELECT e.nombre, c.resultado
            FROM clasificados c
            JOIN equipos e ON c.equipo_id = e.id
            WHERE c.fase = ?
            ORDER BY e.nombre
        """, (fase,)).fetchall()

    # ----------------------------------------------------------------
    # Clasificación
    # ----------------------------------------------------------------

    def recalcular_y_obtener_clasificacion(self, solo_fase=None):
        """
        solo_fase: si se pasa (ej. 'Fase de grupos'), solo cuenta
        partidos de esa fase. Util para mundiales/copas.
        """
        self.cursor.execute(
            "UPDATE equipos SET pj=0,pg=0,pe=0,pp=0,gf=0,gc=0,pts=0"
        )
        if solo_fase:
            partidos = self.cursor.execute(
                "SELECT * FROM partidos WHERE jugado=1 AND fase=?", (solo_fase,)
            ).fetchall()
        else:
            partidos = self.cursor.execute(
                "SELECT * FROM partidos WHERE jugado=1"
            ).fetchall()

        for p in partidos:
            gl, gv = p["goles_local"], p["goles_visitante"]
            id_l, id_v = p["local_id"], p["visitante_id"]
            self.cursor.execute(
                "UPDATE equipos SET gf=gf+?,gc=gc+?,pj=pj+1 WHERE id=?", (gl,gv,id_l)
            )
            self.cursor.execute(
                "UPDATE equipos SET gf=gf+?,gc=gc+?,pj=pj+1 WHERE id=?", (gv,gl,id_v)
            )
            if gl > gv:
                self.cursor.execute(
                    "UPDATE equipos SET pg=pg+1,pts=pts+3 WHERE id=?", (id_l,)
                )
                self.cursor.execute(
                    "UPDATE equipos SET pp=pp+1 WHERE id=?", (id_v,)
                )
            elif gv > gl:
                self.cursor.execute(
                    "UPDATE equipos SET pp=pp+1 WHERE id=?", (id_l,)
                )
                self.cursor.execute(
                    "UPDATE equipos SET pg=pg+1,pts=pts+3 WHERE id=?", (id_v,)
                )
            else:
                self.cursor.execute(
                    "UPDATE equipos SET pe=pe+1,pts=pts+1 WHERE id=?", (id_l,)
                )
                self.cursor.execute(
                    "UPDATE equipos SET pe=pe+1,pts=pts+1 WHERE id=?", (id_v,)
                )
        self.conn.commit()
        return self.obtener_clasificacion_actual()

    def obtener_clasificacion_actual(self):
        equipos = [dict(r) for r in self.cursor.execute("""
            SELECT id, nombre, grupo, pj, pg, pe, pp, gf, gc, pts
            FROM equipos
            ORDER BY pts DESC, (gf-gc) DESC, gf DESC
        """).fetchall()]

        grupos = defaultdict(list)
        for eq in equipos:
            grupos[eq["pts"]].append(eq)

        clasificacion_final = []
        for pts in sorted(grupos.keys(), reverse=True):
            grupo = grupos[pts]
            if len(grupo) == 1:
                clasificacion_final.append(grupo[0])
                continue

            ids = tuple(eq["id"] for eq in grupo)
            ph  = ",".join("?"*len(ids))
            mini = {eq["id"]: {"pts_mini":0,"dif_mini":0,"orig":eq} for eq in grupo}

            for p in self.cursor.execute(f"""
                SELECT local_id, visitante_id, goles_local, goles_visitante
                FROM partidos
                WHERE jugado=1
                AND local_id IN ({ph}) AND visitante_id IN ({ph})
            """, ids+ids).fetchall():
                il, iv = p["local_id"], p["visitante_id"]
                gl, gv = p["goles_local"], p["goles_visitante"]
                mini[il]["dif_mini"] += gl-gv
                mini[iv]["dif_mini"] += gv-gl
                if gl > gv:   mini[il]["pts_mini"] += 3
                elif gv > gl: mini[iv]["pts_mini"] += 3
                else:
                    mini[il]["pts_mini"] += 1
                    mini[iv]["pts_mini"] += 1

            for item in sorted(mini.values(),
                key=lambda x: (x["pts_mini"], x["dif_mini"],
                               x["orig"]["gf"]-x["orig"]["gc"],
                               x["orig"]["gf"]),
                reverse=True):
                clasificacion_final.append(item["orig"])

        return clasificacion_final
