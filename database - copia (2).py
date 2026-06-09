import sqlite3


class GestorBaseDeDatos:
    # Obligamos a que se le pase la ruta exacta de la base de datos al iniciar
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.crear_tablas()

    def crear_tablas(self):
        # Tablas base (compatibles con nodriza.db)
        # equipos: nodriza.db no tiene columna 'ciudad', se añade si falta
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                ciudad TEXT,
                pj INTEGER DEFAULT 0,
                pg INTEGER DEFAULT 0,
                pe INTEGER DEFAULT 0,
                pp INTEGER DEFAULT 0,
                gf INTEGER DEFAULT 0,
                gc INTEGER DEFAULT 0,
                pts INTEGER DEFAULT 0
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS jugadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                equipo_id INTEGER,
                FOREIGN KEY (equipo_id) REFERENCES equipos (id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS partidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipo_local_id INTEGER,
                equipo_visitante_id INTEGER,
                goles_local INTEGER DEFAULT -1,
                goles_visitante INTEGER DEFAULT -1,
                fecha TEXT,
                FOREIGN KEY (equipo_local_id) REFERENCES equipos (id) ON DELETE CASCADE,
                FOREIGN KEY (equipo_visitante_id) REFERENCES equipos (id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goleadores_partido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partido_id INTEGER,
                jugador_id INTEGER,
                goles INTEGER DEFAULT 0,
                FOREIGN KEY (partido_id) REFERENCES partidos (id) ON DELETE CASCADE,
                FOREIGN KEY (jugador_id) REFERENCES jugadores (id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goleadores_totales (
                jugador_id INTEGER PRIMARY KEY,
                goles INTEGER DEFAULT 0,
                FOREIGN KEY (jugador_id) REFERENCES jugadores (id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

        # Migraciones: añadir columnas opcionales si la BD existente no las tiene
        self._migrar_columnas()

    def _migrar_columnas(self):
        """Añade columnas que pueden faltar en nodriza.db sin romper datos existentes."""
        migraciones = [
            ("equipos", "ciudad", "TEXT DEFAULT ''"),
            ("partidos", "jugado", "INTEGER DEFAULT 0"),
            ("partidos", "archivado", "INTEGER DEFAULT 0"),
        ]
        for tabla, columna, definicion in migraciones:
            try:
                self.cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")
                self.conn.commit()
            except Exception:
                pass  # La columna ya existe

        # Sincronizar jugado con goles_local (nodriza.db usa -1 para pendiente)
        self.cursor.execute("""
            UPDATE partidos SET jugado = 1
            WHERE goles_local != -1 AND goles_visitante != -1 AND jugado = 0
        """)
        self.conn.commit()

    def close_db(self):
        self.conn.close()

    def obtener_id_equipo(self, nombre):
        self.cursor.execute("SELECT id FROM equipos WHERE nombre = ?", (nombre,))
        res = self.cursor.fetchone()
        return res["id"] if res else None

    def obtener_id_jugador(self, nombre):
        self.cursor.execute("SELECT id FROM jugadores WHERE nombre = ?", (nombre,))
        res = self.cursor.fetchone()
        return res["id"] if res else None

    def obtener_nombres_equipos(self):
        self.cursor.execute("SELECT nombre FROM equipos ORDER BY nombre")
        return [row["nombre"] for row in self.cursor.fetchall()]

    def obtener_equipos(self):
        self.cursor.execute("SELECT * FROM equipos ORDER BY nombre")
        return self.cursor.fetchall()

    def obtener_jugadores_completo(self):
        query = """
            SELECT j.id, j.nombre, e.nombre as equipo_nombre,
                   COALESCE(gt.goles, 0) AS goles_marcados
            FROM jugadores j
            LEFT JOIN equipos e ON j.equipo_id = e.id
            LEFT JOIN goleadores_totales gt ON gt.jugador_id = j.id
            ORDER BY j.nombre
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def obtener_jugadores_por_equipo(self, nombre_equipo):
        equipo_id = self.obtener_id_equipo(nombre_equipo)
        if equipo_id:
            self.cursor.execute("SELECT * FROM jugadores WHERE equipo_id = ? ORDER BY nombre", (equipo_id,))
            return self.cursor.fetchall()
        return []

    def obtener_partidos_con_equipos(self, fecha_filtro=None, mostrar_archivados=0):
        base_query = """
            SELECT p.id, el.nombre as nombre_equipo_local, ev.nombre as nombre_equipo_visitante,
                   p.goles_local, p.goles_visitante, p.fecha, p.jugado, p.archivado
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            WHERE p.archivado = ?
        """
        params = [mostrar_archivados]
        if fecha_filtro and fecha_filtro != "-- Ver Todos los Partidos --" and fecha_filtro != "-- Archivo Histórico --":
            base_query += " AND p.fecha = ?"
            params.append(fecha_filtro)
        base_query += " ORDER BY p.fecha DESC, p.id DESC"
        self.cursor.execute(base_query, params)
        return self.cursor.fetchall()

    def obtener_goleadores_por_partido(self, partido_id):
        query = """
            SELECT j.nombre as jugador, gp.goles 
            FROM goleadores_partido gp
            LEFT JOIN jugadores j ON gp.jugador_id = j.id
            WHERE gp.partido_id = ?
        """
        self.cursor.execute(query, (partido_id,))
        return self.cursor.fetchall()

    def obtener_goleadores_top(self):
        query = """
            SELECT j.nombre as jugador, e.nombre as equipo,
                   COALESCE(gt.goles, 0) AS goles
            FROM jugadores j
            JOIN equipos e ON j.equipo_id = e.id
            LEFT JOIN goleadores_totales gt ON gt.jugador_id = j.id
            WHERE COALESCE(gt.goles, 0) > 0
            ORDER BY COALESCE(gt.goles, 0) DESC
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def obtener_jornadas(self, mostrar_archivados=0):
        try:
            self.cursor.execute("SELECT DISTINCT fecha FROM partidos WHERE archivado = ? ORDER BY fecha DESC", (mostrar_archivados,))
            return [row["fecha"] for row in self.cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

    def recalcular_y_obtener_clasificacion(self):
        self.cursor.execute("UPDATE equipos SET pj=0, pg=0, pe=0, pp=0, gf=0, gc=0, pts=0")
        self.cursor.execute("SELECT * FROM partidos WHERE jugado = 1")
        partidos = self.cursor.fetchall()
        for p in partidos:
            gl, gv = p["goles_local"], p["goles_visitante"]
            self.cursor.execute("UPDATE equipos SET gf = gf + ?, gc = gc + ?, pj = pj + 1 WHERE id = ?", (gl, gv, p["equipo_local_id"]))
            self.cursor.execute("UPDATE equipos SET gf = gf + ?, gc = gc + ?, pj = pj + 1 WHERE id = ?", (gv, gl, p["equipo_visitante_id"]))
            if gl > gv:
                self.cursor.execute("UPDATE equipos SET pg = pg + 1, pts = pts + 3 WHERE id = ?", (p["equipo_local_id"],))
                self.cursor.execute("UPDATE equipos SET pp = pp + 1 WHERE id = ?", (p["equipo_visitante_id"],))
            elif gv > gl:
                self.cursor.execute("UPDATE equipos SET pp = pp + 1 WHERE id = ?", (p["equipo_local_id"],))
                self.cursor.execute("UPDATE equipos SET pg = pg + 1, pts = pts + 3 WHERE id = ?", (p["equipo_visitante_id"],))
            else:
                self.cursor.execute("UPDATE equipos SET pe = pe + 1, pts = pts + 1 WHERE id = ?", (p["equipo_local_id"],))
                self.cursor.execute("UPDATE equipos SET pe = pe + 1, pts = pts + 1 WHERE id = ?", (p["equipo_visitante_id"],))
        self.conn.commit()
        return self.obtener_clasificacion_actual()

    def obtener_clasificacion_actual(self):
        from collections import defaultdict

        self.cursor.execute("SELECT id, nombre, pj, pg, pe, pp, gf, gc, pts FROM equipos ORDER BY pts DESC, (gf - gc) DESC, gf DESC")
        equipos_filas = self.cursor.fetchall()
        equipos = [dict(row) for row in equipos_filas]

        grupos_puntos = defaultdict(list)
        for eq in equipos:
            grupos_puntos[eq["pts"]].append(eq)

        clasificacion_final = []

        for pts in sorted(grupos_puntos.keys(), reverse=True):
            grupo = grupos_puntos[pts]

            if len(grupo) == 1:
                clasificacion_final.append(grupo[0])
            else:
                ids_empatados = tuple(eq["id"] for eq in grupo)
                mini_liga = {eq["id"]: {"pts_mini": 0, "dif_mini": 0, "equipo_original": eq} for eq in grupo}
                placeholders = ",".join("?" * len(ids_empatados))
                query = f"""
                    SELECT equipo_local_id, equipo_visitante_id, goles_local, goles_visitante
                    FROM partidos
                    WHERE jugado = 1
                    AND equipo_local_id IN ({placeholders})
                    AND equipo_visitante_id IN ({placeholders})
                """
                self.cursor.execute(query, ids_empatados + ids_empatados)
                partidos_directos = self.cursor.fetchall()

                for p in partidos_directos:
                    id_loc = p["equipo_local_id"]
                    id_vis = p["equipo_visitante_id"]
                    gl = p["goles_local"]
                    gv = p["goles_visitante"]

                    mini_liga[id_loc]["dif_mini"] += gl - gv
                    mini_liga[id_vis]["dif_mini"] += gv - gl

                    if gl > gv:
                        mini_liga[id_loc]["pts_mini"] += 3
                    elif gv > gl:
                        mini_liga[id_vis]["pts_mini"] += 3
                    else:
                        mini_liga[id_loc]["pts_mini"] += 1
                        mini_liga[id_vis]["pts_mini"] += 1

                grupo_ordenado = sorted(
                    mini_liga.values(),
                    key=lambda x: (
                        x["pts_mini"],
                        x["dif_mini"],
                        (x["equipo_original"]["gf"] - x["equipo_original"]["gc"]),
                        x["equipo_original"]["gf"],
                    ),
                    reverse=True,
                )

                for item in grupo_ordenado:
                    clasificacion_final.append(item["equipo_original"])

        return clasificacion_final

    def actualizar_clasificacion_manual(self, equipo_nombre, pj, pg, pe, pp, gf, gc, pts):
        equipo_id = self.obtener_id_equipo(equipo_nombre)
        if equipo_id:
            self.cursor.execute("UPDATE equipos SET pj=?, pg=?, pe=?, pp=?, gf=?, gc=?, pts=? WHERE id=?", (pj, pg, pe, pp, gf, gc, pts, equipo_id))
            self.conn.commit()

    def agregar_equipo(self, nombre, ciudad):
        try:
            self.cursor.execute("INSERT INTO equipos (nombre, ciudad) VALUES (?, ?)", (nombre, ciudad))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_equipo_por_nombre(self, nombre):
        self.cursor.execute("DELETE FROM equipos WHERE nombre = ?", (nombre,))
        self.conn.commit()

    def agregar_jugador(self, nombre_jugador, nombre_equipo):
        equipo_id = self.obtener_id_equipo(nombre_equipo)
        if equipo_id:
            self.cursor.execute("INSERT INTO jugadores (nombre, equipo_id) VALUES (?, ?)", (nombre_jugador, equipo_id))
            self.conn.commit()

    def agregar_partido(self, local_nombre, visitante_nombre, fecha):
        id_local = self.obtener_id_equipo(local_nombre)
        id_visit = self.obtener_id_equipo(visitante_nombre)
        if id_local and id_visit:
            self.cursor.execute("INSERT INTO partidos (equipo_local_id, equipo_visitante_id, fecha, jugado) VALUES (?, ?, ?, 0)", (id_local, id_visit, fecha))
            self.conn.commit()
            return True
        return False

    def registrar_resultado_partido(self, partido_id, goles_local, goles_visitante):
        self.cursor.execute("UPDATE partidos SET goles_local = ?, goles_visitante = ?, jugado = 1 WHERE id = ?", (goles_local, goles_visitante, partido_id))
        self.conn.commit()

    def insertar_goleador(self, partido_id, nombre_jugador, cantidad_goles):
        if nombre_jugador == "(Propia Puerta)":
            return
        jugador_id = self.obtener_id_jugador(nombre_jugador)
        if jugador_id:
            self.cursor.execute("INSERT INTO goleadores_partido (partido_id, jugador_id, goles) VALUES (?, ?, ?)", (partido_id, jugador_id, cantidad_goles))
            # Actualizar también el acumulado en goleadores_totales
            self.cursor.execute(
                """
                INSERT INTO goleadores_totales (jugador_id, goles) VALUES (?, ?)
                ON CONFLICT(jugador_id) DO UPDATE SET goles = goles + excluded.goles
            """,
                (jugador_id, cantidad_goles),
            )
            self.conn.commit()

    def limpiar_partidos_pendientes(self):
        self.cursor.execute("SELECT COUNT(*) FROM partidos WHERE jugado = 0")
        pendientes = self.cursor.fetchone()[0]
        self.cursor.execute("DELETE FROM partidos WHERE jugado = 0")
        self.conn.commit()
        return pendientes

    def limpiar_goleadores_de_partido(self, partido_id):
        self.cursor.execute("DELETE FROM goleadores_partido WHERE partido_id = ?", (partido_id,))
        self.conn.commit()

    def recalcular_goleadores_totales(self):
        # Recalcula desde goleadores_partido y guarda en goleadores_totales (esquema nodriza.db)
        self.cursor.execute("DELETE FROM goleadores_totales")
        self.cursor.execute("""
            INSERT INTO goleadores_totales (jugador_id, goles)
            SELECT jugador_id, SUM(goles)
            FROM goleadores_partido
            GROUP BY jugador_id
        """)
        self.conn.commit()

    def eliminar_jugador_por_nombre(self, nombre):
        self.cursor.execute("DELETE FROM jugadores WHERE nombre = ?", (nombre,))
        self.conn.commit()

    def eliminar_partido_por_id(self, partido_id):
        self.cursor.execute("DELETE FROM partidos WHERE id = ?", (partido_id,))
        self.conn.commit()

    def establecer_goles_totales_manual(self, nombre_jugador, nuevo_total):
        jugador_id = self.obtener_id_jugador(nombre_jugador)
        if jugador_id:
            self.cursor.execute(
                """
                INSERT INTO goleadores_totales (jugador_id, goles) VALUES (?, ?)
                ON CONFLICT(jugador_id) DO UPDATE SET goles = excluded.goles
            """,
                (jugador_id, nuevo_total),
            )
            self.conn.commit()
            return True
        return False

    def toggle_archivo_partido(self, partido_id, archivo_estado):
        self.cursor.execute("UPDATE partidos SET archivado = ? WHERE id = ?", (archivo_estado, partido_id))
        self.conn.commit()
