# app_maestra_futbol.py  —  Gestor Premium de Torneos v2
# Requiere: database.py, ttkbootstrap, reportlab (opcional)
# Compatible con BDs migradas al esquema canónico (_v2.db)
# ──────────────────────────────────────────────────────────

import sqlite3
import os
import sys
import csv
import json
import traceback
import io
import unicodedata
from datetime import datetime
from collections import Counter

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from database import GestorBaseDeDatos

def _normalizar_nombre(s):
    """Quita acentos y caracteres especiales para comparación fuzzy.
    Cubre: acentos latinos, ø/Ø, æ/Æ, ł/Ł, ð, etc."""
    # Reemplazos 1-a-1 para caracteres que NFKD no descompone
    _EXTRAS = str.maketrans(
        "øØæÆłŁðþ",
        "oOaAlLdt"
    )
    s = str(s).translate(_EXTRAS)
    # ß → ss no cabe en maketrans 1-a-1; lo hacemos aparte
    s = s.replace("ß", "ss").replace("œ", "oe").replace("Œ", "OE")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").upper().strip()

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ──────────────────────────────────────────────────────────
# ESQUEMA CANÓNICO (para crear nuevas BDs)
# ──────────────────────────────────────────────────────────
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS torneo_info (
    id        INTEGER PRIMARY KEY,
    nombre    TEXT NOT NULL,
    tipo      TEXT NOT NULL CHECK(tipo IN ('liga','copa','mundial','euro')),
    temporada TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    ciudad TEXT DEFAULT '',
    grupo  TEXT DEFAULT NULL,
    pj INTEGER DEFAULT 0, pg INTEGER DEFAULT 0,
    pe INTEGER DEFAULT 0, pp INTEGER DEFAULT 0,
    gf INTEGER DEFAULT 0, gc INTEGER DEFAULT 0, pts INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS jugadores (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT NOT NULL,
    equipo_id      INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    goles_marcados INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS partidos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_local_id     INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    equipo_visitante_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    goles_local         INTEGER DEFAULT -1,
    goles_visitante     INTEGER DEFAULT -1,
    penaltis_local      INTEGER DEFAULT -1,
    penaltis_visitante  INTEGER DEFAULT -1,
    fecha               TEXT DEFAULT '',
    estadio             TEXT DEFAULT '',
    fase                TEXT DEFAULT NULL,
    jornada             TEXT DEFAULT NULL,
    jugado              INTEGER DEFAULT 0,
    archivado           INTEGER DEFAULT 0
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
"""

TIPOS_TORNEO = ["liga", "copa", "mundial", "euro"]

# ── CARPETA CENTRALIZADA DE BASES DE DATOS ──────────────────
# Cambia esta ruta si quieres un directorio diferente.
# None = subcarpeta "bases_de_datos" junto al script (por defecto)
CARPETA_BBDD_OVERRIDE = None
# Descomenta y edita para usar una ruta fija:
# CARPETA_BBDD_OVERRIDE = r"D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium\bases_de_datos"
# ─────────────────────────────────────────────────────────────

def _carpeta_bbdd():
    if CARPETA_BBDD_OVERRIDE:
        os.makedirs(CARPETA_BBDD_OVERRIDE, exist_ok=True)
        return CARPETA_BBDD_OVERRIDE
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bases_de_datos")
    os.makedirs(ruta, exist_ok=True)
    return ruta
FASES_ELIMINATORIAS = {
    "mundial": ["Fase de grupos", "Dieciseisavos de final", "Octavos de final",
                "Cuartos de final", "Semifinal", "Tercer Puesto", "Final"],
    "euro":    ["Fase de grupos", "Octavos de final", "Cuartos de final",
                "Semifinal", "Tercer Puesto", "Final"],
    "copa":    ["Fase de liga", "Playoffs", "Octavos de final",
                "Cuartos de final", "Semifinal", "Final"],
    "liga":    [],
}

def fases_para_tipo(tipo):
    return FASES_ELIMINATORIAS.get(tipo, FASES_ELIMINATORIAS["copa"])

# ──────────────────────────────────────────────────────────
# HELPERS DE BD
# ──────────────────────────────────────────────────────────

def crear_bd_nueva(ruta, nombre, tipo, temporada=""):
    conn = sqlite3.connect(ruta)
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO torneo_info (nombre,tipo,temporada) VALUES (?,?,?)",
        (nombre, tipo, temporada)
    )
    conn.commit()
    conn.close()


def leer_torneo_info(db_path):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        r = conn.execute("SELECT * FROM torneo_info LIMIT 1").fetchone()
        conn.close()
        return dict(r) if r else None
    except Exception:
        return None


def _conn(db_path):
    c = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    return c


# ──────────────────────────────────────────────────────────
# VENTANA DE GOLEADORES (popup reutilizable)
# ──────────────────────────────────────────────────────────
class VentanaGoleadores(tk.Toplevel):
    def __init__(self, parent, db_path, partido_id, callback=None):
        super().__init__(parent)
        self.db_path = db_path
        self.partido_id = partido_id
        self.callback = callback
        self.title("Goleadores del Partido")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._cargar()

    def _build(self):
        f = tb.Frame(self, padding=15)
        f.pack(fill=BOTH, expand=True)
        tb.Label(f, text="Goleadores registrados", font="-weight bold").pack(anchor=W)
        self.tree = tb.Treeview(f, columns=("jugador","goles"), show="headings", height=8)
        self.tree.heading("jugador", text="Jugador")
        self.tree.heading("goles", text="Goles")
        self.tree.column("goles", width=60, anchor="center")
        self.tree.pack(fill=X, pady=5)
        tb.Button(f, text="🗑 Limpiar todos los goleadores",
                  bootstyle="danger-outline", command=self._limpiar).pack(fill=X, pady=5)
        tb.Button(f, text="Cerrar", command=self.destroy).pack(fill=X)

    def _cargar(self):
        self.tree.delete(*self.tree.get_children())
        conn = _conn(self.db_path)
        rows = conn.execute("""
            SELECT j.nombre, gp.goles
            FROM goleadores_partido gp
            JOIN jugadores j ON gp.jugador_id = j.id
            WHERE gp.partido_id = ?
            ORDER BY gp.goles DESC, j.nombre
        """, (self.partido_id,)).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(r["nombre"], r["goles"]))
        if hasattr(self, "lbl_vacio"):
            self.lbl_vacio.pack_forget()
        if not rows:
            self.lbl_vacio = tb.Label(self.tree.master,
                text="Este partido no tiene goleadores registrados.",
                foreground="#aaaaaa", font="-size 9")
            self.lbl_vacio.pack(anchor=W, pady=2)

    def _limpiar(self):
        if messagebox.askyesno("Confirmar", "¿Borrar todos los goleadores de este partido?"):
            conn = _conn(self.db_path)
            conn.execute("DELETE FROM goleadores_partido WHERE partido_id=?", (self.partido_id,))
            conn.commit(); conn.close()
            self._cargar()
            if self.callback:
                self.callback()


# ──────────────────────────────────────────────────────────
# APLICACIÓN PRINCIPAL
# ──────────────────────────────────────────────────────────
class AppMaestra(tk.Frame):
    """Frame principal que vive dentro del root tb.Window ya creado."""

    def __init__(self, root, db_path, torneo_info):
        super().__init__(root)
        self.pack(fill=BOTH, expand=True)
        self._root = root
        self.db_path = db_path
        
        # Actualizar schema para mundial 2026: tarjetas, ranking FIFA y grupo
        try:
            conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
            conn.execute("PRAGMA journal_mode = WAL")
            p_cols = {col[1] for col in conn.execute("PRAGMA table_info(partidos)").fetchall()}
            if "tarjetas_amarillas_local" not in p_cols:
                for col in ["tarjetas_amarillas_local","tarjetas_amarillas_visitante",
                            "tarjetas_rojas_local","tarjetas_rojas_visitante"]:
                    conn.execute(f"ALTER TABLE partidos ADD COLUMN {col} INTEGER DEFAULT 0")
            if "grupo" not in p_cols:
                conn.execute("ALTER TABLE partidos ADD COLUMN grupo TEXT DEFAULT NULL")
            e_cols = {col[1] for col in conn.execute("PRAGMA table_info(equipos)").fetchall()}
            if "ranking_fifa" not in e_cols:
                conn.execute("ALTER TABLE equipos ADD COLUMN ranking_fifa INTEGER DEFAULT 999")
            conn.commit(); conn.close()
        except: pass
        
        self.torneo_info = torneo_info
        # Forzar tipo correcto basado en nombre de archivo
        if "champions" in db_path.lower():
            self.tipo = "champions"
        else:
            self.tipo = torneo_info.get("tipo", "liga")
        self.db = GestorBaseDeDatos(db_path)
        self._mostrar_archivados = tk.IntVar(value=0)

        nombre = torneo_info.get("nombre", "Torneo")
        temp   = torneo_info.get("temporada", "")
        root.title(f"⚽ {nombre}" + (f"  —  {temp}" if temp else ""))
        root.geometry("1300x820")
        root.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        self._crear_ui()
        self._refresh_all()

    # ──────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE UI
    # ──────────────────────────────────────────────────────

    def _crear_ui(self):
        barra = tb.Frame(self, padding=(10, 5))
        barra.pack(fill=X)
        nombre = self.torneo_info.get("nombre","")
        tipo   = self.tipo.upper()
        temp   = self.torneo_info.get("temporada","")
        tb.Label(barra, text=f"🏆 {nombre}", font="-size 14 -weight bold").pack(side=LEFT)
        tb.Label(barra, text=f"[{tipo}]  {temp}", foreground="#888888").pack(side=LEFT, padx=10)
        tb.Button(barra, text="🔄 Refrescar Todo", bootstyle="secondary-outline",
                  command=self._refresh_all).pack(side=RIGHT, padx=5)
        tb.Button(barra, text="🏆 Cambiar Torneo", bootstyle="info-outline",
                  command=self._cambiar_torneo).pack(side=RIGHT, padx=5)
        tb.Button(barra, text="✖ Salir", bootstyle="danger-outline",
                  command=self._al_cerrar).pack(side=RIGHT, padx=5)

        nb = tb.Notebook(self)
        nb.pack(fill=BOTH, expand=True, padx=10, pady=(0,10))

        if self.tipo == "liga":
            t_cls = tb.Frame(nb); nb.add(t_cls, text="📊 Clasificación")
            t_jug = tb.Frame(nb); nb.add(t_jug, text="🏃 Jugadores")
            t_par = tb.Frame(nb); nb.add(t_par, text="⚽ Partidos")
            t_gol = tb.Frame(nb); nb.add(t_gol, text="🥅 Goleadores")
            t_exp = tb.Frame(nb); nb.add(t_exp, text="📄 Exportar")
            self._ui_clasificacion(t_cls)
            self._ui_jugadores(t_jug)
            self._ui_partidos(t_par)
            self._ui_goleadores_tab(t_gol)
            self._ui_exportar(t_exp)
        elif self.tipo == "champions":
            # UI específico para Champions League (Liguilla, Playoff, Eliminatorias)
            t_lig = tb.Frame(nb); nb.add(t_lig, text="📋 Liguilla")
            t_pla = tb.Frame(nb); nb.add(t_pla, text="🔥 Playoff")
            t_eli = tb.Frame(nb); nb.add(t_eli, text="🏆 Eliminatorias")
            t_gol = tb.Frame(nb); nb.add(t_gol, text="🥅 Goleadores")
            t_equ = tb.Frame(nb); nb.add(t_equ, text="👥 Equipos y Jugadores")
            t_exp = tb.Frame(nb); nb.add(t_exp, text="📄 Exportar")
            self._ui_liguilla(t_lig)
            self._ui_playoff(t_pla)
            self._ui_eliminatorias_champions(t_eli)
            self._ui_goleadores_tab(t_gol)
            self._ui_equipos_jugadores_copa(t_equ)
            self._ui_exportar(t_exp)
        else:
            tab1_txt = "📋 Grupos y Resultados" if self.tipo in ("mundial","euro") else "📋 Equipos y Resultados"
            t_grp = tb.Frame(nb); nb.add(t_grp, text=tab1_txt)
            t_eli = tb.Frame(nb); nb.add(t_eli, text="🏆 Eliminatorias")
            t_gol = tb.Frame(nb); nb.add(t_gol, text="🥅 Goleadores")
            t_equ = tb.Frame(nb); nb.add(t_equ, text="👥 Equipos y Jugadores")
            t_exp = tb.Frame(nb); nb.add(t_exp, text="📄 Exportar")
            self._ui_grupos(t_grp)
            self._ui_eliminatorias(t_eli)
            self._ui_goleadores_tab(t_gol)
            self._ui_equipos_jugadores_copa(t_equ)
            self._ui_exportar(t_exp)

    # ──────────────────────────────────────────────────────
    # TAB: CLASIFICACIÓN (modo liga)
    # ──────────────────────────────────────────────────────

    def _ui_clasificacion(self, parent):
        frm_izq = tb.Frame(parent, padding=10, width=280)
        frm_izq.pack_propagate(False)
        frm_izq.pack(side=LEFT, fill=Y)
        frm_der = tb.Frame(parent, padding=10)
        frm_der.pack(side=RIGHT, fill=BOTH, expand=True)

        # Panel izquierdo: controles
        tb.Label(frm_izq, text="Nombre del Equipo:").pack(anchor=W)
        self.entry_eq_nombre = tb.Entry(frm_izq); self.entry_eq_nombre.pack(fill=X)
        tb.Label(frm_izq, text="Ciudad:").pack(anchor=W, pady=(8,0))
        self.entry_eq_ciudad = tb.Entry(frm_izq); self.entry_eq_ciudad.pack(fill=X)
        tb.Button(frm_izq, text="➕ Añadir Equipo", bootstyle=SUCCESS,
                  command=self._on_aniadir_equipo).pack(fill=X, pady=(10,3))
        tb.Button(frm_izq, text="🗑 Eliminar Equipo Seleccionado", bootstyle="danger-outline",
                  command=self._on_eliminar_equipo).pack(fill=X, pady=3)
        tb.Button(frm_izq, text="📁 Importar Equipos (CSV)", bootstyle=INFO,
                  command=self._on_cargar_equipos_csv).pack(fill=X, pady=3)

        tk.Frame(frm_izq, height=1, bg="#cccccc").pack(fill=X, pady=15)
        tb.Button(frm_izq, text="🔢 Recalcular Clasificación", bootstyle="warning",
                  command=self._on_recalcular_clasificacion).pack(fill=X, pady=3)
        tb.Button(frm_izq, text="✏️ Editar Estadísticas Manual", bootstyle="warning-outline",
                  command=self._on_guardar_clasificacion_manual).pack(fill=X, pady=3)
        tb.Button(frm_izq, text="🔄 Nueva Temporada", bootstyle="secondary-outline",
                  command=self._on_nueva_temporada).pack(fill=X, pady=3)

        tk.Frame(frm_izq, height=1, bg="#cccccc").pack(fill=X, pady=15)
        tb.Label(frm_izq, text="Historial de Simulacros:").pack(anchor=W)
        tb.Button(frm_izq, text="📋 Ver Historial Simulacros", bootstyle="info-outline",
                  command=self._on_simulacro_historial).pack(fill=X, pady=3)

        # Panel derecho: tabla clasificación
        tb.Label(frm_der, text="Tabla de Posiciones", font="-size 13 -weight bold").pack(pady=5, anchor=W)
        cols_c = ("pos","nombre","ciudad","pj","pg","pe","pp","gf","gc","dif","pts")
        self.tree_clas = tb.Treeview(frm_der, columns=cols_c, show="headings", height=22, bootstyle="primary")
        headers = {"pos":"#","nombre":"Equipo","ciudad":"Ciudad","pj":"PJ","pg":"PG","pe":"PE",
                   "pp":"PP","gf":"GF","gc":"GC","dif":"DIF","pts":"PTS"}
        anchos  = {"pos":35,"nombre":160,"ciudad":130,"pj":40,"pg":40,"pe":40,
                   "pp":40,"gf":40,"gc":40,"dif":50,"pts":50}
        for c in cols_c:
            self.tree_clas.heading(c, text=headers[c])
            self.tree_clas.column(c, width=anchos[c], anchor="center" if c != "nombre" else "w")
        sb = tb.Scrollbar(frm_der, orient=VERTICAL, command=self.tree_clas.yview)
        self.tree_clas.configure(yscrollcommand=sb.set)
        self.tree_clas.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

    # ──────────────────────────────────────────────────────
    # TAB: JUGADORES (modo liga)
    # ──────────────────────────────────────────────────────

    def _ui_jugadores(self, parent):
        frm_ctrl = tb.Frame(parent, padding=10, width=280)
        frm_ctrl.pack_propagate(False)
        frm_ctrl.pack(side=LEFT, fill=Y)
        frm_tbl  = tb.Frame(parent, padding=10)
        frm_tbl.pack(side=RIGHT, fill=BOTH, expand=True)

        tb.Label(frm_ctrl, text="Nombre del Jugador:").pack(anchor=W)
        self.entry_jug_nombre = tb.Entry(frm_ctrl); self.entry_jug_nombre.pack(fill=X)
        tb.Label(frm_ctrl, text="Equipo:").pack(anchor=W, pady=(8,0))
        self.combo_jug_equipo = tb.Combobox(frm_ctrl, state="readonly")
        self.combo_jug_equipo.pack(fill=X)
        tb.Button(frm_ctrl, text="➕ Añadir Jugador", bootstyle=SUCCESS,
                  command=self._on_aniadir_jugador).pack(fill=X, pady=(10,3))
        tb.Button(frm_ctrl, text="🗑 Eliminar Jugador", bootstyle="danger-outline",
                  command=self._on_eliminar_jugador).pack(fill=X, pady=3)
        tb.Button(frm_ctrl, text="📁 Importar Jugadores (carpeta CSV)", bootstyle=INFO,
                  command=self._on_cargar_jugadores_carpeta).pack(fill=X, pady=3)
        tb.Button(frm_ctrl, text="🧹 Limpiar Duplicados", bootstyle="warning-outline",
                  command=self._on_limpiar_duplicados_jugadores).pack(fill=X, pady=3)
        tb.Button(frm_ctrl, text="⚠️ Borrar TODOS los Jugadores", bootstyle="danger",
                  command=self._on_borrar_todos_jugadores).pack(fill=X, pady=3)

        tk.Frame(frm_ctrl, height=1, bg="#cccccc").pack(fill=X, pady=15)
        tb.Label(frm_ctrl, text="Editar goles totales (doble-clic en tabla):",
                 font="-size 9", foreground="#888").pack(anchor=W)

        tb.Label(frm_tbl, text="Lista Global de Jugadores", font="-size 13 -weight bold").pack(pady=5, anchor=W)
        cols_j = ("id","nombre","equipo","goles")
        self.tree_jugadores = tb.Treeview(frm_tbl, columns=cols_j, show="headings", height=22)
        self.tree_jugadores.heading("id", text="ID"); self.tree_jugadores.column("id", width=50, anchor="center")
        self.tree_jugadores.heading("nombre", text="Jugador"); self.tree_jugadores.column("nombre", width=200)
        self.tree_jugadores.heading("equipo", text="Equipo"); self.tree_jugadores.column("equipo", width=160)
        self.tree_jugadores.heading("goles", text="Goles"); self.tree_jugadores.column("goles", width=60, anchor="center")
        sb = tb.Scrollbar(frm_tbl, orient=VERTICAL, command=self.tree_jugadores.yview)
        self.tree_jugadores.configure(yscrollcommand=sb.set)
        self.tree_jugadores.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        self.tree_jugadores.bind("<Double-1>", self._on_editar_goles_totales_manual)

    # ──────────────────────────────────────────────────────
    # TAB: PARTIDOS (modo liga)
    # ──────────────────────────────────────────────────────

    def _ui_partidos(self, parent):
        frm_top = tb.Frame(parent, padding=5)
        frm_top.pack(fill=X)
        frm_ctrl = tb.Frame(parent, padding=10, width=280)
        frm_ctrl.pack_propagate(False)
        frm_ctrl.pack(side=LEFT, fill=Y)
        frm_tbl  = tb.Frame(parent, padding=10)
        frm_tbl.pack(side=RIGHT, fill=BOTH, expand=True)

        # Filtro jornada
        tb.Label(frm_top, text="Jornada/Fecha:").pack(side=LEFT)
        self.combo_jornada = tb.Combobox(frm_top, state="readonly", width=20)
        self.combo_jornada.pack(side=LEFT, padx=5)
        self.combo_jornada.bind("<<ComboboxSelected>>", self._on_jornada_filtrada)
        tb.Checkbutton(frm_top, text="Ver Archivo Histórico",
                       variable=self._mostrar_archivados,
                       command=self._on_toggle_historico).pack(side=LEFT, padx=10)

        # Panel control
        tb.Label(frm_ctrl, text="Nuevo Partido:").pack(anchor=W)
        tb.Label(frm_ctrl, text="Local:").pack(anchor=W)
        self.combo_p_local = tb.Combobox(frm_ctrl, state="readonly")
        self.combo_p_local.pack(fill=X)
        tb.Label(frm_ctrl, text="Visitante:").pack(anchor=W, pady=(5,0))
        self.combo_p_visit = tb.Combobox(frm_ctrl, state="readonly")
        self.combo_p_visit.pack(fill=X)
        tb.Label(frm_ctrl, text="Fecha (YYYY-MM-DD):").pack(anchor=W, pady=(5,0))
        self.entry_p_fecha = tb.Entry(frm_ctrl)
        self.entry_p_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_p_fecha.pack(fill=X)
        tb.Button(frm_ctrl, text="📅 Programar Partido", bootstyle=SUCCESS,
                  command=self._on_crear_partido).pack(fill=X, pady=(8,3))
        tb.Button(frm_ctrl, text="📁 Importar Jornada (CSV)", bootstyle=INFO,
                  command=self._on_cargar_jornada_csv).pack(fill=X, pady=3)

        tk.Frame(frm_ctrl, height=1, bg="#cccccc").pack(fill=X, pady=10)
        tb.Label(frm_ctrl, text="Resultado:").pack(anchor=W)
        frm_goles = tb.Frame(frm_ctrl)
        frm_goles.pack(fill=X)
        tb.Label(frm_goles, text="L:").pack(side=LEFT)
        self.entry_gl = tb.Entry(frm_goles, width=5); self.entry_gl.pack(side=LEFT, padx=2)
        tb.Label(frm_goles, text="V:").pack(side=LEFT)
        self.entry_gv = tb.Entry(frm_goles, width=5); self.entry_gv.pack(side=LEFT, padx=2)
        tb.Button(frm_ctrl, text="✅ Registrar Resultado", bootstyle=SUCCESS,
                  command=self._on_registrar_resultado).pack(fill=X, pady=(5,3))
        tb.Button(frm_ctrl, text="✏️ Editar Partido / Goles", bootstyle="warning-outline",
                  command=self._abrir_editar_partido).pack(fill=X, pady=3)

        tk.Frame(frm_ctrl, height=1, bg="#cccccc").pack(fill=X, pady=10)
        tb.Button(frm_ctrl, text="📦 Archivar Partido", bootstyle="secondary-outline",
                  command=self._on_toggle_archivo_partido).pack(fill=X, pady=3)
        tb.Button(frm_ctrl, text="🗑 Eliminar Partido", bootstyle="danger-outline",
                  command=self._on_eliminar_partido).pack(fill=X, pady=3)

        # Panel tabla
        tb.Label(frm_tbl, text="Partidos (doble-clic → ver goleadores)",
                 font="-size 11").pack(pady=2, anchor=W)
        cols_p = ("id","fecha","local","visitante","res","jugado")
        self.tree_partidos = tb.Treeview(frm_tbl, columns=cols_p, show="headings", height=12)
        self.tree_partidos.heading("id", text="ID"); self.tree_partidos.column("id", width=40, anchor="center")
        self.tree_partidos.heading("fecha", text="Fecha"); self.tree_partidos.column("fecha", width=90, anchor="center")
        self.tree_partidos.heading("local", text="Local"); self.tree_partidos.column("local", width=150)
        self.tree_partidos.heading("visitante", text="Visitante"); self.tree_partidos.column("visitante", width=150)
        self.tree_partidos.heading("res", text="Res."); self.tree_partidos.column("res", width=60, anchor="center")
        self.tree_partidos.heading("jugado", text="Estado"); self.tree_partidos.column("jugado", width=70, anchor="center")
        sb = tb.Scrollbar(frm_tbl, orient=VERTICAL, command=self.tree_partidos.yview)
        self.tree_partidos.configure(yscrollcommand=sb.set)
        self.tree_partidos.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        self.tree_partidos.bind("<Double-1>", self._on_partido_doble_clic)

        tb.Label(frm_tbl, text="Goleadores del partido seleccionado:", font="-weight bold").pack(pady=5, anchor=W)
        self.tree_gol_partido = tb.Treeview(frm_tbl, columns=("jugador","goles"), show="headings", height=5)
        self.tree_gol_partido.heading("jugador", text="Jugador")
        self.tree_gol_partido.heading("goles", text="Goles")
        self.tree_gol_partido.column("goles", width=60, anchor="center")
        self.tree_gol_partido.pack(fill=X)
        self.lbl_sin_goles = tb.Label(frm_tbl,
            text="(sin goleadores registrados para este partido)",
            foreground="#aaaaaa", font="-size 9")
        self.lbl_sin_goles.pack(anchor=W)

        # ── Añadir goleador al partido seleccionado ──────────
        frm_add_gol = tb.LabelFrame(frm_tbl, text=" Añadir Goleador al Partido ")
        frm_add_gol.pack(fill=X, pady=(8,0))
        frm_ag1 = tb.Frame(frm_add_gol, padding=(5,4))
        frm_ag1.pack(fill=X)
        tb.Label(frm_ag1, text="Jugador:").pack(side=LEFT)
        self.combo_gol_jugador = tb.Combobox(frm_ag1, state="readonly", width=22)
        self.combo_gol_jugador.pack(side=LEFT, padx=5)
        tb.Label(frm_ag1, text="Goles:").pack(side=LEFT, padx=(8,3))
        self.spin_gol_cantidad = tb.Spinbox(frm_ag1, from_=1, to=10, width=5)
        self.spin_gol_cantidad.pack(side=LEFT); self.spin_gol_cantidad.set(1)
        tb.Button(frm_ag1, text="⚽ Añadir", bootstyle="info",
                  command=self._on_aniadir_goleador_partido).pack(side=LEFT, padx=8)
        tb.Button(frm_ag1, text="🗑 Limpiar goleadores", bootstyle="danger-outline",
                  command=self._on_limpiar_goleadores_partido).pack(side=LEFT)

        self.tree_partidos.bind("<<TreeviewSelect>>", self._on_partido_seleccionado_ver_goleadores)

    # ──────────────────────────────────────────────────────
    # TAB: GOLEADORES
    # ──────────────────────────────────────────────────────

    def _ui_goleadores_tab(self, parent):
        frm_ctrl = tb.Frame(parent, padding=10, width=260)
        frm_ctrl.pack_propagate(False)
        frm_ctrl.pack(side=LEFT, fill=Y)
        frm_tbl  = tb.Frame(parent, padding=10)
        frm_tbl.pack(side=RIGHT, fill=BOTH, expand=True)

        tb.Button(frm_ctrl, text="🔄 Recalcular desde partidos", bootstyle="warning",
                  command=self._on_recalcular_goleadores).pack(fill=X, pady=5)
        tb.Button(frm_ctrl, text="📁 Importar goleadores (CSV)", bootstyle=INFO,
                  command=self._on_importar_goleadores_csv).pack(fill=X, pady=5)

        tb.Label(frm_tbl, text="Máximos Goleadores", font="-size 13 -weight bold").pack(pady=5, anchor=W)
        cols_g = ("pos","jugador","equipo","goles")
        self.tree_goleadores = tb.Treeview(frm_tbl, columns=cols_g, show="headings", height=24)
        self.tree_goleadores.heading("pos",    text="#");        self.tree_goleadores.column("pos",    width=40,  anchor="center")
        self.tree_goleadores.heading("jugador",text="Jugador");  self.tree_goleadores.column("jugador",width=200)
        self.tree_goleadores.heading("equipo", text="Equipo");   self.tree_goleadores.column("equipo", width=160)
        self.tree_goleadores.heading("goles",  text="Goles");    self.tree_goleadores.column("goles",  width=60,  anchor="center")
        sb = tb.Scrollbar(frm_tbl, orient=VERTICAL, command=self.tree_goleadores.yview)
        self.tree_goleadores.configure(yscrollcommand=sb.set)
        self.tree_goleadores.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

    # ──────────────────────────────────────────────────────
    # TAB: GRUPOS Y RESULTADOS (modo copa/mundial/euro)
    # ──────────────────────────────────────────────────────

    def _ui_grupos(self, parent):
        """Tab mejorado con selector visual de grupos y dashboard."""
        # Panel superior: selector de grupos
        frm_selector = tb.LabelFrame(parent, text=" Seleccionar Grupo/División ")
        frm_selector.pack(fill=X, padx=10, pady=(10,5))
        
        self.grupo_seleccionado = tk.StringVar(value="A")
        frm_botones = tb.Frame(frm_selector)
        frm_botones.pack(fill=X, padx=5, pady=5)
        
        # Generar botones según tipo
        if self.tipo == "mundial":
            grupos = ["A","B","C","D","E","F","G","H","I","J","K","L"]
        elif self.tipo == "copa":
            grupos = ["A","B","C","D","E","F","G","H"]  # Champions
        else:
            grupos = ["Jornada 1", "Jornada 2", "Jornada 3", "Jornada 4"]  # Liga
        
        for grp in grupos:
            def _on_grupo(g=grp):
                self.grupo_seleccionado.set(g)
                self._cargar_grupo_seleccionado()
            tb.Button(frm_botones, text=grp, width=6,
                      command=_on_grupo).pack(side=LEFT, padx=2, pady=2)
        
        # Panel principal: dos columnas
        frm_main = tb.Frame(parent)
        frm_main.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Columna izquierda: partidos + goleadores
        frm_izq = tb.Frame(frm_main)
        frm_izq.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,5))
        
        # Tabla de partidos
        tb.Label(frm_izq, text="📅 Partidos del Grupo", 
                 font="-size 11 -weight bold", bootstyle="inverse-primary").pack(fill=X, pady=(0,5))
        cols_part = ("fecha","local","visitante","resultado","estadio")
        self.tree_partidos_grupo = tb.Treeview(frm_izq, columns=cols_part, show="headings", height=8)
        self.tree_partidos_grupo.heading("fecha", text="Fecha")
        self.tree_partidos_grupo.heading("local", text="Local")
        self.tree_partidos_grupo.heading("visitante", text="Visitante")
        self.tree_partidos_grupo.heading("resultado", text="Res.")
        self.tree_partidos_grupo.heading("estadio", text="Estadio")
        for c in cols_part:
            self.tree_partidos_grupo.column(c, width=100 if c=="local" else 80)
        sb1 = tb.Scrollbar(frm_izq, orient=VERTICAL, command=self.tree_partidos_grupo.yview)
        self.tree_partidos_grupo.configure(yscrollcommand=sb1.set)
        self.tree_partidos_grupo.pack(side=LEFT, fill=BOTH, expand=True)
        sb1.pack(side=RIGHT, fill=Y)
        
        # Tabla de posiciones
        tb.Label(frm_izq, text="🏆 Posiciones", 
                 font="-size 11 -weight bold", bootstyle="inverse-success").pack(fill=X, pady=(10,5))
        cols_pos = ("pos","equipo","pj","pg","pe","pp","gf","gc","pts")
        self.tree_posiciones_grupo = tb.Treeview(frm_izq, columns=cols_pos, show="headings", height=6)
        self.tree_posiciones_grupo.heading("pos", text="Pos")
        self.tree_posiciones_grupo.heading("equipo", text="Equipo")
        self.tree_posiciones_grupo.heading("pj", text="PJ")
        self.tree_posiciones_grupo.heading("pg", text="PG")
        self.tree_posiciones_grupo.heading("pe", text="PE")
        self.tree_posiciones_grupo.heading("pp", text="PP")
        self.tree_posiciones_grupo.heading("gf", text="GF")
        self.tree_posiciones_grupo.heading("gc", text="GC")
        self.tree_posiciones_grupo.heading("pts", text="PTS")
        for c in ["pos","pj","pg","pe","pp","gf","gc","pts"]:
            self.tree_posiciones_grupo.column(c, width=35, anchor="center")
        self.tree_posiciones_grupo.column("equipo", width=150)
        sb2 = tb.Scrollbar(frm_izq, orient=VERTICAL, command=self.tree_posiciones_grupo.yview)
        self.tree_posiciones_grupo.configure(yscrollcommand=sb2.set)
        self.tree_posiciones_grupo.pack(side=LEFT, fill=BOTH, expand=True)
        sb2.pack(side=RIGHT, fill=Y)
        
        # Columna derecha: panel de control
        frm_der = tb.LabelFrame(frm_main, text=" Panel de Resultados ")
        frm_der.pack(side=RIGHT, fill=BOTH, padx=0)
        frm_der.pack_propagate(False)
        frm_der.configure(width=500)
        
        # Selector de partido
        tb.Label(frm_der, text="Partido:", font="-weight bold").grid(row=0, column=0, sticky=W, pady=5)
        self.combo_partido_mundial = tb.Combobox(frm_der, width=45, state="readonly")
        self.combo_partido_mundial.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.combo_partido_mundial.bind("<<ComboboxSelected>>", self._on_seleccion_partido_mundial)
        
        # Goles
        tk.Frame(frm_der, height=1, bg="#ccc").grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
        tb.Label(frm_der, text="Goles Local:", font="-weight bold").grid(row=2, column=0, sticky=W, pady=3)
        self.entry_mundial_gl = tb.Entry(frm_der, width=8); self.entry_mundial_gl.grid(row=2, column=1, sticky=W)
        tb.Label(frm_der, text="Goles Visit.:", font="-weight bold").grid(row=3, column=0, sticky=W, pady=3)
        self.entry_mundial_gv = tb.Entry(frm_der, width=8); self.entry_mundial_gv.grid(row=3, column=1, sticky=W)
        
        # Goleador
        tk.Frame(frm_der, height=1, bg="#ccc").grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        tb.Label(frm_der, text="Equipo:", font="-weight bold").grid(row=5, column=0, sticky=W, pady=3)
        self.combo_eq_mundial = tb.Combobox(frm_der, width=43, state="readonly")
        self.combo_eq_mundial.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5, pady=3)
        self.combo_eq_mundial.bind("<<ComboboxSelected>>", self._on_eq_mundial_cambiado)
        
        tb.Label(frm_der, text="Jugador:", font="-weight bold").grid(row=6, column=0, sticky=W, pady=3)
        self.combo_jug_mundial = tb.Combobox(frm_der, width=43, state="readonly")
        self.combo_jug_mundial.grid(row=6, column=1, columnspan=2, sticky="ew", padx=5, pady=3)
        
        tb.Label(frm_der, text="Goles:", font="-weight bold").grid(row=7, column=0, sticky=W, pady=3)
        self.spin_goles_mundial = tb.Spinbox(frm_der, from_=1, to=10, width=8)
        self.spin_goles_mundial.grid(row=7, column=1, sticky=W)
        self.spin_goles_mundial.set(1)
        
        # Botones de acción
        tk.Frame(frm_der, height=1, bg="#ccc").grid(row=8, column=0, columnspan=3, sticky="ew", pady=10)
        tb.Button(frm_der, text="✅ Grabar Marcador", bootstyle=SUCCESS,
                  command=self._grabar_resultado_mundial).grid(row=9, column=0, columnspan=3, sticky="ew", pady=5)
        tb.Button(frm_der, text="⚽ Añadir Goleador", bootstyle="info",
                  command=self._grabar_gol_mundial).grid(row=10, column=0, columnspan=3, sticky="ew", pady=3)
        tb.Button(frm_der, text="🔄 Refrescar", bootstyle="info-outline",
                  command=self._cargar_grupo_seleccionado).grid(row=11, column=0, columnspan=3, sticky="ew", pady=3)
        
        # Goleadores globales
        frm_gol = tb.LabelFrame(frm_der, text=" ⚽ Top Goleadores ")
        frm_gol.grid(row=12, column=0, columnspan=3, sticky="ew", pady=(10,0))
        self.tree_gol_mundial = tb.Treeview(frm_gol, columns=("jugador","goles"), 
                                             show="headings", height=8, bootstyle="success")
        self.tree_gol_mundial.heading("jugador", text="Jugador")
        self.tree_gol_mundial.heading("goles", text="Goles")
        self.tree_gol_mundial.column("goles", width=50, anchor="center")
        sb3 = tb.Scrollbar(frm_gol, orient=VERTICAL, command=self.tree_gol_mundial.yview)
        self.tree_gol_mundial.configure(yscrollcommand=sb3.set)
        self.tree_gol_mundial.pack(side=LEFT, fill=BOTH, expand=True)
        sb3.pack(side=RIGHT, fill=Y)
        
        # Cargar datos iniciales
        self._cargar_grupo_seleccionado()

    # ──────────────────────────────────────────────────────
    # TAB: CHAMPIONS LEAGUE - LIGUILLA
    # ──────────────────────────────────────────────────────

    def _ui_liguilla(self, parent):
        """Tabla única de 36 equipos en Champions League."""
        frm_top = tb.Frame(parent, padding=10)
        frm_top.pack(fill=X)
        
        tb.Label(frm_top, text="⚽ LIGUILLA CHAMPIONS - 36 EQUIPOS",
                 font="-size 13 -weight bold", bootstyle="inverse-info").pack(pady=5)
        tb.Label(frm_top, text="Clasificación única | 1-8: Octavos directo | 9-24: Playoff | 25-36: Eliminados",
                 font="-size 10", foreground="#666").pack(pady=3)
        
        # Tabla de clasificación
        cols = ("pos","equipo","pj","pg","pe","pp","gf","gc","dif","pts")
        self.tree_liguilla = tb.Treeview(parent, columns=cols, show="headings", height=20)
        self.tree_liguilla.heading("pos",text="Pos"); self.tree_liguilla.column("pos",width=35,anchor="c")
        self.tree_liguilla.heading("equipo",text="Equipo"); self.tree_liguilla.column("equipo",width=200)
        for c in ["pj","pg","pe","pp","gf","gc","dif","pts"]:
            self.tree_liguilla.heading(c, text=c.upper())
            self.tree_liguilla.column(c, width=45, anchor="center")
        
        # Colores por zona
        self.tree_liguilla.tag_configure("octavos", background="#90EE90")
        self.tree_liguilla.tag_configure("playoff", background="#FFFFE0")
        self.tree_liguilla.tag_configure("eliminado", background="#FFB6C1")
        
        sb = tb.Scrollbar(parent, orient=VERTICAL, command=self.tree_liguilla.yview)
        self.tree_liguilla.configure(yscrollcommand=sb.set)
        self.tree_liguilla.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        sb.pack(side=RIGHT, fill=Y)
        
        self._cargar_liguilla()
    
    def _cargar_liguilla(self):
        """Carga tabla de liguilla con 36 equipos."""
        if not hasattr(self, "tree_liguilla"): return
        self._recalcular_grupos()
        self.tree_liguilla.delete(*self.tree_liguilla.get_children())
        
        conn = _conn(self.db_path)
        rows = conn.execute("""
            SELECT nombre, pj, pg, pe, pp, gf, gc, pts
            FROM equipos
            ORDER BY pts DESC, (gf-gc) DESC, gf DESC
        """).fetchall()
        conn.close()
        
        for pos, r in enumerate(rows, 1):
            dif = r["gf"] - r["gc"]
            if pos <= 8:
                tag = ("octavos",)
            elif pos <= 24:
                tag = ("playoff",)
            else:
                tag = ("eliminado",)
            
            self.tree_liguilla.insert("", "end", values=(
                pos, r["nombre"], r["pj"], r["pg"], r["pe"], r["pp"],
                r["gf"], r["gc"], dif, r["pts"]
            ), tags=tag)

    # ──────────────────────────────────────────────────────
    # TAB: CHAMPIONS LEAGUE - PLAYOFF
    # ──────────────────────────────────────────────────────

    def _ui_playoff(self, parent):
        """Playoff de 16 equipos (posiciones 9-24 de liguilla)."""
        frm_top = tb.Frame(parent, padding=10)
        frm_top.pack(fill=X)
        
        tb.Label(frm_top, text="🔥 PLAYOFF CHAMPIONS - IDA Y VUELTA",
                 font="-size 13 -weight bold", bootstyle="inverse-warning").pack(pady=5)
        tb.Label(frm_top, text="16 equipos (posiciones 9-24) → 8 ganadores a Octavos",
                 font="-size 10", foreground="#666").pack(pady=3)
        
        frm_btn = tb.Frame(frm_top)
        frm_btn.pack(fill=X, pady=10)
        tb.Button(frm_btn, text="🎲 Generar Playoff Automático",
                  bootstyle="warning", command=self._generar_playoff).pack(side=LEFT, padx=5)
        tb.Button(frm_btn, text="🔄 Cargar Playoff",
                  bootstyle="info-outline", command=self._cargar_playoff).pack(side=LEFT, padx=5)
        
        # Tabla de partidos del playoff
        cols = ("tipo","local","visitante","ida","vuelta","agregado","ganador")
        self.tree_playoff = tb.Treeview(parent, columns=cols, show="headings", height=18)
        self.tree_playoff.heading("tipo",text="Cruce"); self.tree_playoff.column("tipo",width=60,anchor="c")
        self.tree_playoff.heading("local",text="Local"); self.tree_playoff.column("local",width=120)
        self.tree_playoff.heading("visitante",text="Visitante"); self.tree_playoff.column("visitante",width=120)
        self.tree_playoff.heading("ida",text="IDA"); self.tree_playoff.column("ida",width=50,anchor="c")
        self.tree_playoff.heading("vuelta",text="VUELTA"); self.tree_playoff.column("vuelta",width=50,anchor="c")
        self.tree_playoff.heading("agregado",text="Agregado"); self.tree_playoff.column("agregado",width=60,anchor="c")
        self.tree_playoff.heading("ganador",text="Ganador"); self.tree_playoff.column("ganador",width=100)
        
        sb = tb.Scrollbar(parent, orient=VERTICAL, command=self.tree_playoff.yview)
        self.tree_playoff.configure(yscrollcommand=sb.set)
        self.tree_playoff.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        sb.pack(side=RIGHT, fill=Y)
        
        self._cargar_playoff()
    
    def _generar_playoff(self):
        """Genera automáticamente emparejamientos del playoff."""
        messagebox.showinfo("Próxima", "Función de generación de playoff en desarrollo")
    
    def _cargar_playoff(self):
        """Carga tabla del playoff."""
        if not hasattr(self, "tree_playoff"): return
        self.tree_playoff.delete(*self.tree_playoff.get_children())
        # TODO: Cargar partidos de playoff de la BD

    # ──────────────────────────────────────────────────────
    # TAB: CHAMPIONS LEAGUE - ELIMINATORIAS
    # ──────────────────────────────────────────────────────

    def _ui_eliminatorias_champions(self, parent):
        """Octavos, Cuartos, Semis, Final con ida y vuelta."""
        frm_top = tb.Frame(parent, padding=10)
        frm_top.pack(fill=X)
        
        tb.Label(frm_top, text="🏆 ELIMINATORIAS CHAMPIONS - IDA Y VUELTA",
                 font="-size 13 -weight bold", bootstyle="inverse-success").pack(pady=5)
        
        # Selector de fase
        frm_sel = tb.Frame(frm_top)
        frm_sel.pack(fill=X, pady=10)
        tb.Label(frm_sel, text="Fase:").pack(side=LEFT, padx=5)
        
        self.var_fase_eli = tk.StringVar(value="Octavos")
        for fase in ["Octavos", "Cuartos", "Semifinal", "Final"]:
            tb.Button(frm_sel, text=fase, width=15,
                      command=lambda f=fase: self._cargar_fase_eliminatoria(f)).pack(side=LEFT, padx=2)
        
        # Tabla de eliminatorias
        cols = ("tipo","local","visitante","ida","vuelta","agregado","ganador")
        self.tree_eliminatorias = tb.Treeview(parent, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree_eliminatorias.heading(c, text=c.upper())
            self.tree_eliminatorias.column(c, width=80 if c=="agregado" else 100, anchor="c")
        
        sb = tb.Scrollbar(parent, orient=VERTICAL, command=self.tree_eliminatorias.yview)
        self.tree_eliminatorias.configure(yscrollcommand=sb.set)
        self.tree_eliminatorias.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        sb.pack(side=RIGHT, fill=Y)
        
        self._cargar_fase_eliminatoria("Octavos")
    
    def _cargar_fase_eliminatoria(self, fase):
        """Carga partidos de una fase eliminatoria."""
        if not hasattr(self, "tree_eliminatorias"): return
        self.tree_eliminatorias.delete(*self.tree_eliminatorias.get_children())
        # TODO: Cargar partidos de eliminatorias de la BD

    def _ui_eliminatorias(self, parent):
        frm_izq = tb.Frame(parent, padding=10, width=320)
        frm_izq.pack_propagate(False)
        frm_izq.pack(side=LEFT, fill=Y)
        frm_der = tb.Frame(parent, padding=10)
        frm_der.pack(side=RIGHT, fill=BOTH, expand=True)

        # Clasificados
        lbl_top = "🏆 Clasificados"
        if self.tipo == "mundial":
            lbl_top += " (1º, 2º y 8 mejores 3ºs)"
        tb.Label(frm_izq, text=lbl_top, font="-size 11 -weight bold",
                 bootstyle="inverse-info").pack(fill=X, pady=(0,5))
        self.tree_clasificados = tb.Treeview(frm_izq,
            columns=("grupo","pos","pais","pts"), show="headings", height=10, bootstyle="info")
        for c,t,w in [("grupo","Grp",35),("pos","Pos",35),("pais","Equipo",130),("pts","Pts",40)]:
            self.tree_clasificados.heading(c, text=t)
            self.tree_clasificados.column(c, width=w, anchor="center" if c!="pais" else "w")
        self.tree_clasificados.pack(fill=X)
        tb.Button(frm_izq, text="🔄 Refrescar Clasificados",
                  bootstyle="info-outline", command=self._cargar_eliminatorias).pack(fill=X, pady=6)

        # Goleadores en eliminatorias
        tb.Label(frm_izq, text="⚽ Máximos Goleadores",
                 font="-size 11 -weight bold", bootstyle="inverse-success").pack(fill=X, pady=(10,5))
        self.tree_elim_goles = tb.Treeview(frm_izq, columns=("jugador","goles"),
                                            show="headings", height=10, bootstyle="success")
        self.tree_elim_goles.heading("jugador", text="Jugador")
        self.tree_elim_goles.heading("goles",   text="Goles")
        self.tree_elim_goles.column("goles", width=50, anchor="center")
        self.tree_elim_goles.pack(fill=BOTH, expand=True)

        # Generador de cruces
        frm_cruces = tb.LabelFrame(frm_der, text=" Generador de Cruces ")
        frm_cruces.pack(fill=X, pady=(0,10), ipadx=5, ipady=5)

        tb.Label(frm_cruces, text="Fase:").grid(row=0,column=0,padx=5,pady=4,sticky=W)
        self.combo_fase_elim = tb.Combobox(frm_cruces, values=fases_para_tipo(self.tipo),
                                            state="readonly", width=22)
        self.combo_fase_elim.grid(row=0,column=1,padx=5,pady=4)
        fases = fases_para_tipo(self.tipo)
        self.combo_fase_elim.set(fases[1] if len(fases) > 1 else (fases[0] if fases else ""))

        tb.Label(frm_cruces, text="Local:").grid(row=0,column=2,padx=5,pady=4,sticky=W)
        self.combo_elim_local = tb.Combobox(frm_cruces, state="readonly", width=20)
        self.combo_elim_local.grid(row=0,column=3,padx=5,pady=4)

        tb.Label(frm_cruces, text="Visitante:").grid(row=0,column=4,padx=5,pady=4,sticky=W)
        self.combo_elim_vis = tb.Combobox(frm_cruces, state="readonly", width=20)
        self.combo_elim_vis.grid(row=0,column=5,padx=5,pady=4)

        tb.Label(frm_cruces, text="Fecha:").grid(row=1,column=0,padx=5,pady=4,sticky=W)
        self.entry_elim_fecha = tb.Entry(frm_cruces, width=14)
        self.entry_elim_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_elim_fecha.grid(row=1,column=1,padx=5,pady=4)
        tb.Label(frm_cruces, text="Estadio:").grid(row=1,column=2,padx=5,pady=4,sticky=W)
        self.entry_elim_estadio = tb.Entry(frm_cruces, width=18)
        self.entry_elim_estadio.grid(row=1,column=3,padx=5,pady=4)
        tb.Button(frm_cruces, text="⚔️ Generar Cruce", bootstyle=SUCCESS,
                  command=self._crear_cruce_eliminatoria).grid(row=1,column=4,columnspan=2,
                  sticky="ew",padx=5,pady=4)

        # Cuadro del torneo
        tb.Label(frm_der, text="🏆 Cuadro del Torneo",
                 font="-size 12 -weight bold", bootstyle="inverse-primary").pack(fill=X, pady=(0,5))
        cols_cuadro = ("fase","fecha","partido","resultado")
        self.tree_cuadro = tb.Treeview(frm_der, columns=cols_cuadro,
                                        show="headings", height=18, bootstyle="primary")
        for c,t,w in [("fase","Fase",145),("fecha","Fecha",90),("partido","Enfrentamiento",260),("resultado","Res.",65)]:
            self.tree_cuadro.heading(c, text=t)
            self.tree_cuadro.column(c, width=w, anchor="center" if c!="partido" else "w")
        self.tree_cuadro.tag_configure("r16",        background="#98FB98")
        self.tree_cuadro.tag_configure("octavos",    background="#006400", foreground="white")
        self.tree_cuadro.tag_configure("cuartos",    background="#ADD8E6")
        self.tree_cuadro.tag_configure("semis",      background="#F5DEB3")
        self.tree_cuadro.tag_configure("final",      background="#DC143C", foreground="white",
                                        font=("Segoe UI",10,"bold"))
        self.tree_cuadro.tag_configure("campeon",    background="#32CD32", foreground="black",
                                        font=("Segoe UI",13,"bold"))
        self.tree_cuadro.pack(fill=BOTH, expand=True)

    # ──────────────────────────────────────────────────────
    # TAB: EQUIPOS Y JUGADORES (modo copa)
    # ──────────────────────────────────────────────────────

    def _ui_equipos_jugadores_copa(self, parent):
        nb2 = tb.Notebook(parent)
        nb2.pack(fill=BOTH, expand=True)
        t_eq  = tb.Frame(nb2); nb2.add(t_eq,  text="Equipos / Selecciones")
        t_jug = tb.Frame(nb2); nb2.add(t_jug, text="Jugadores")
        self._ui_clasificacion(t_eq)   # reutilizamos el panel de equipos
        self._ui_jugadores(t_jug)

    # ──────────────────────────────────────────────────────
    # TAB: EXPORTAR
    # ──────────────────────────────────────────────────────

    def _ui_exportar(self, parent):
        frm = tb.Frame(parent, padding=30)
        frm.pack(anchor="n", pady=20)
        tb.Label(frm, text="Generador de Informes", font="-size 14 -weight bold").grid(
            row=0, column=0, columnspan=2, pady=(0,20))
        tb.Label(frm, text="Contenido:").grid(row=1, column=0, sticky=W, padx=10, pady=8)
        self.combo_exp_tipo = tb.Combobox(frm, state="readonly", width=32,
            values=["Tabla de Posiciones","Lista de Goleadores","Resultados (partidos jugados)"])
        self.combo_exp_tipo.grid(row=1, column=1, padx=10, pady=8)
        self.combo_exp_tipo.set("Tabla de Posiciones")
        tb.Label(frm, text="Formato:").grid(row=2, column=0, sticky=W, padx=10, pady=8)
        fmts = ["TXT","CSV","JSON"]
        if HAS_PDF:
            fmts.append("PDF")
        self.combo_exp_fmt = tb.Combobox(frm, state="readonly", width=32, values=fmts)
        self.combo_exp_fmt.grid(row=2, column=1, padx=10, pady=8)
        self.combo_exp_fmt.set("TXT")
        tb.Button(frm, text="💾 Generar y Guardar", bootstyle=SUCCESS,
                  command=self._on_exportar, width=35).grid(row=3, column=0, columnspan=2, pady=25)

    # ──────────────────────────────────────────────────────
    # REFRESH
    # ──────────────────────────────────────────────────────

    def _refresh_all(self):
        if self.tipo == "liga":
            self._refresh_clasificacion()
            self._refresh_jugadores()
            self._refresh_partidos()
            self._refresh_goleadores()
            self._refresh_combos_liga()
        else:
            self._refresh_equipos_copa()  # Cargar tabla de equipos para Copa/Mundial
            self._cargar_grupos()
            self._cargar_eliminatorias()
            self._refresh_goleadores()
            self._cargar_partidos_mundiales()
            self._refresh_combos_mundial()
    
    def _refresh_equipos_copa(self):
        """Carga los equipos en la tabla para Copa/Mundial."""
        if not hasattr(self, "tree_clas"): return
        self.tree_clas.delete(*self.tree_clas.get_children())
        
        conn = _conn(self.db_path)
        equipos = conn.execute(
            "SELECT id, nombre, ciudad FROM equipos ORDER BY nombre"
        ).fetchall()
        conn.close()
        
        for i, row in enumerate(equipos, 1):
            eq = dict(row)
            self.tree_clas.insert("", "end", values=(
                i, eq["nombre"], eq.get("ciudad", ""), "", "", "", "", "", "", "", ""
            ))

    def _refresh_combos_liga(self):
        nombres = self.db.obtener_nombres_equipos()
        for cb in (self.combo_jug_equipo, self.combo_p_local, self.combo_p_visit):
            cb["values"] = nombres

    def _refresh_combos_mundial(self):
        nombres = self.db.obtener_nombres_equipos()
        if hasattr(self, "combo_eq_mundial"):
            self.combo_eq_mundial["values"] = nombres
        if hasattr(self, "combo_elim_local"):
            self.combo_elim_local["values"] = nombres
            self.combo_elim_vis["values"]   = nombres

    def _refresh_clasificacion(self):
        if not hasattr(self, "tree_clas"): return
        self.tree_clas.delete(*self.tree_clas.get_children())
        clas = self.db.recalcular_y_obtener_clasificacion()
        for i, _eq in enumerate(clas, 1):
            eq = dict(_eq)
            dif = eq.get("gf",0) - eq.get("gc",0)
            self.tree_clas.insert("","end", values=(
                i, eq.get("nombre",""), eq.get("ciudad",""),
                eq.get("pj",0), eq.get("pg",0), eq.get("pe",0), eq.get("pp",0),
                eq.get("gf",0), eq.get("gc",0),
                f"+{dif}" if dif > 0 else str(dif),
                eq.get("pts",0)
            ))

    def _refresh_jugadores(self):
        if not hasattr(self, "tree_jugadores"): return
        self.tree_jugadores.delete(*self.tree_jugadores.get_children())
        for _j in self.db.obtener_jugadores_completo():
            j = dict(_j)
            self.tree_jugadores.insert("","end",
                values=(j["id"], j["nombre"], j.get("equipo_nombre",""), j.get("goles_marcados",0)))

    def _refresh_partidos(self):
        if not hasattr(self, "tree_partidos"): return
        jornadas = self.db.obtener_jornadas(self._mostrar_archivados.get())
        opciones = ["-- Ver Todos los Partidos --"] + jornadas + ["-- Archivo Histórico --"]
        sel_actual = self.combo_jornada.get()
        self.combo_jornada["values"] = opciones
        if sel_actual not in opciones:
            self.combo_jornada.set(opciones[0])
        self._on_jornada_filtrada()

    def _refresh_goleadores(self):
        if not hasattr(self, "tree_goleadores"): return
        self.tree_goleadores.delete(*self.tree_goleadores.get_children())
        for i, g in enumerate(self.db.obtener_goleadores_top(), 1):
            self.tree_goleadores.insert("","end",
                values=(i, g["jugador"], g["equipo"], g["goles"]))

    # ──────────────────────────────────────────────────────
    # EVENTOS LIGA
    # ──────────────────────────────────────────────────────

    def _on_aniadir_equipo(self):
        nombre = self.entry_eq_nombre.get().strip()
        ciudad = self.entry_eq_ciudad.get().strip()
        if nombre:
            ok = self.db.agregar_equipo(nombre, ciudad)
            if ok:
                self.entry_eq_nombre.delete(0,"end")
                self.entry_eq_ciudad.delete(0,"end")
                messagebox.showinfo("Éxito", f"Equipo '{nombre}' registrado.")
                self._refresh_all()
            else:
                messagebox.showerror("Error", "El equipo ya existe.")
        else:
            messagebox.showwarning("Aviso", "Introduce el nombre del equipo.")

    def _on_eliminar_equipo(self):
        item = self.tree_clas.selection() if hasattr(self,"tree_clas") else None
        if not item:
            messagebox.showwarning("Aviso", "Selecciona un equipo en la tabla.")
            return
        nombre = self.tree_clas.item(item,"values")[1]
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{nombre}'?\nSe borrarán sus jugadores y partidos."):
            self.db.eliminar_equipo_por_nombre(nombre)
            self._refresh_all()

    def _on_cargar_equipos_csv(self):
        ruta = filedialog.askopenfilename(title="CSV de Equipos", filetypes=[("CSV","*.csv")])
        if not ruta: return
        try:
            with open(ruta, encoding="utf-8") as f:
                for row in csv.reader(f):
                    if row:
                        self.db.agregar_equipo(row[0].strip(), row[1].strip() if len(row)>1 else "")
            messagebox.showinfo("Éxito", "Equipos importados.")
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_aniadir_jugador(self):
        nombre = self.entry_jug_nombre.get().strip()
        equipo = self.combo_jug_equipo.get()
        if nombre and equipo:
            self.db.agregar_jugador(nombre, equipo)
            self.entry_jug_nombre.delete(0,"end")
            messagebox.showinfo("Éxito", f"Jugador '{nombre}' añadido.")
            self._refresh_jugadores()
        else:
            messagebox.showwarning("Aviso", "Introduce nombre y selecciona equipo.")

    def _on_eliminar_jugador(self):
        item = self.tree_jugadores.selection() if hasattr(self,"tree_jugadores") else None
        if not item: messagebox.showwarning("Aviso","Selecciona un jugador."); return
        nombre = self.tree_jugadores.item(item,"values")[1]
        if messagebox.askyesno("Confirmar", f"¿Eliminar jugador '{nombre}'?"):
            self.db.eliminar_jugador_por_nombre(nombre)
            self._refresh_jugadores()

    def _on_cargar_jugadores_carpeta(self):
        carpeta = filedialog.askdirectory(title="Carpeta con CSVs de jugadores")
        if not carpeta: return
        contador = 0
        try:
            for arch in os.listdir(carpeta):
                if arch.lower().endswith(".csv"):
                    equipo = os.path.splitext(arch)[0]
                    with open(os.path.join(carpeta, arch), encoding="utf-8") as f:
                        for row in csv.reader(f):
                            if row:
                                self.db.agregar_jugador(row[0].strip(), equipo)
                                contador += 1
            messagebox.showinfo("Éxito", f"{contador} jugadores cargados.")
            self._refresh_jugadores()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_limpiar_duplicados_jugadores(self):
        """Elimina jugadores duplicados, manteniendo solo uno de cada (nombre, equipo)."""
        if not messagebox.askyesno("Confirmar",
            "¿Limpiar duplicados?\nSe mantendrá un jugador de cada (nombre, equipo) única.\n"
            "¡Esto es irreversible!"):
            return
        try:
            conn = _conn(self.db_path)
            # Encontrar duplicados
            duplicados = conn.execute("""
                SELECT nombre, equipo_id, COUNT(*) as cnt
                FROM jugadores
                GROUP BY nombre, equipo_id
                HAVING cnt > 1
            """).fetchall()
            
            eliminados = 0
            for dup in duplicados:
                nombre, eq_id, cnt = dup["nombre"], dup["equipo_id"], dup["cnt"]
                # Mantener el primero (menor ID), eliminar el resto
                ids_a_borrar = conn.execute("""
                    SELECT id FROM jugadores
                    WHERE nombre=? AND equipo_id=?
                    ORDER BY id ASC
                    LIMIT ? OFFSET 1
                """, (nombre, eq_id, cnt-1)).fetchall()
                for row in ids_a_borrar:
                    conn.execute("DELETE FROM jugadores WHERE id=?", (row["id"],))
                    eliminados += 1
            
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", f"Se eliminaron {eliminados} jugadores duplicados.")
            self._refresh_jugadores()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo limpiar: {e}")

    def _on_borrar_todos_jugadores(self):
        """Borra TODOS los jugadores del torneo actual."""
        if not messagebox.askyesno("⚠️ ATENCIÓN",
            "¿BORRAR TODOS los jugadores de este torneo?\n"
            "¡Esta acción es IRREVERSIBLE!\n\n"
            "Haz clic en OK solo si estás seguro."):
            return
        if not messagebox.askyesno("Confirmación Final",
            "¿ESTÁS SEGURO?\nSe borrarán todos los jugadores permanentemente."):
            return
        
        try:
            conn = _conn(self.db_path)
            resultado = conn.execute("DELETE FROM jugadores").rowcount
            conn.commit(); conn.close()
            messagebox.showinfo("Completado", f"Se eliminaron {resultado} jugadores.")
            self._refresh_jugadores()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo borrar: {e}")

    def _on_crear_partido(self):
        local    = self.combo_p_local.get()
        visitante = self.combo_p_visit.get()
        fecha    = self.entry_p_fecha.get().strip()
        if not local or not visitante or not fecha:
            messagebox.showwarning("Aviso","Rellena todos los campos."); return
        if local == visitante:
            messagebox.showerror("Error","Un equipo no puede jugar contra sí mismo."); return
        if self.db.agregar_partido(local, visitante, fecha):
            messagebox.showinfo("Éxito","Partido programado.")
            self._refresh_partidos()
        else:
            messagebox.showerror("Error","Verifica los nombres de los equipos.")

    def _on_cargar_jornada_csv(self):
        if messagebox.askyesno("Limpiar pendientes",
                               "¿Eliminar partidos pendientes antes de importar?"):
            n = self.db.limpiar_partidos_pendientes()
            messagebox.showinfo("OK", f"{n} partidos pendientes eliminados.")
        ruta = filedialog.askopenfilename(title="CSV de Jornada", filetypes=[("CSV","*.csv")])
        if not ruta: return
        try:
            with open(ruta, encoding="utf-8") as f:
                for row in csv.reader(f):
                    if len(row) >= 3:
                        self.db.agregar_partido(row[0].strip(), row[1].strip(), row[2].strip())
            messagebox.showinfo("Éxito","Jornada importada.")
            self._refresh_partidos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_registrar_resultado(self):
        item = self.tree_partidos.selection() if hasattr(self,"tree_partidos") else None
        if not item: messagebox.showwarning("Aviso","Selecciona un partido."); return
        pid = int(self.tree_partidos.item(item,"values")[0])
        try:
            gl = int(self.entry_gl.get())
            gv = int(self.entry_gv.get())
        except ValueError:
            messagebox.showerror("Error","Introduce números válidos."); return
        self.db.registrar_resultado_partido(pid, gl, gv)
        self.entry_gl.delete(0,"end"); self.entry_gv.delete(0,"end")
        self._refresh_all()

    def _on_partido_doble_clic(self, event):
        item = self.tree_partidos.identify_row(event.y) if hasattr(self,"tree_partidos") else None
        if not item: return
        pid = int(self.tree_partidos.item(item,"values")[0])
        VentanaGoleadores(self, self.db_path, pid, callback=self._refresh_goleadores)

    def _on_partido_seleccionado_ver_goleadores(self, event=None):
        if not hasattr(self,"tree_partidos"): return
        item = self.tree_partidos.selection()
        if not item: return
        vals = self.tree_partidos.item(item,"values")
        pid  = int(vals[0])
        local_nom    = vals[2]
        visitante_nom= vals[3]

        # Actualizar combo de jugadores: los del local + visitante de ese partido
        jugadores = []
        for eq in (local_nom, visitante_nom):
            for j in self.db.obtener_jugadores_por_equipo(eq):
                jugadores.append(j["nombre"] if "nombre" in j.keys() else j[0])
        if hasattr(self,"combo_gol_jugador"):
            self.combo_gol_jugador["values"] = sorted(jugadores)
            if jugadores: self.combo_gol_jugador.set(jugadores[0])

        # Mostrar goleadores registrados
        self.tree_gol_partido.delete(*self.tree_gol_partido.get_children())
        goles = self.db.obtener_goleadores_por_partido(pid)
        for g in goles:
            self.tree_gol_partido.insert("","end", values=(g["jugador"], g["goles"]))
        if hasattr(self, "lbl_sin_goles"):
            if goles:
                self.lbl_sin_goles.pack_forget()
            else:
                self.lbl_sin_goles.pack(anchor=W)

    def _on_aniadir_goleador_partido(self):
        item = self.tree_partidos.selection() if hasattr(self,"tree_partidos") else None
        if not item:
            messagebox.showwarning("Aviso","Selecciona primero un partido en la tabla."); return
        vals = self.tree_partidos.item(item,"values")
        pid  = int(vals[0])
        res  = vals[4]   # "2–0" o "–"
        if res == "–":
            messagebox.showwarning("Aviso","Registra el resultado del partido antes de añadir goleadores."); return

        jugador = self.combo_gol_jugador.get() if hasattr(self,"combo_gol_jugador") else ""
        if not jugador:
            messagebox.showwarning("Aviso","Selecciona un jugador."); return
        try:
            goles = int(self.spin_gol_cantidad.get())
        except ValueError:
            goles = 1

        # Validar que no se supere el marcador del equipo
        try:
            gl_str, gv_str = res.replace("–","-").split("-")
            gl_max, gv_max = int(gl_str.strip()), int(gv_str.strip())
        except Exception:
            gl_max = gv_max = 99

        jid = self.db.obtener_id_jugador(jugador)
        if not jid:
            messagebox.showerror("Error","Jugador no encontrado en la BD."); return

        conn = _conn(self.db_path)
        p = conn.execute("SELECT equipo_local_id, equipo_visitante_id FROM partidos WHERE id=?",
                         (pid,)).fetchone()
        if not p:
            conn.close(); return

        j_row = conn.execute("SELECT equipo_id FROM jugadores WHERE id=?", (jid,)).fetchone()
        if not j_row:
            conn.close(); return
        es_local = j_row["equipo_id"] == p["equipo_local_id"]
        permitidos = gl_max if es_local else gv_max

        ya = conn.execute("""
            SELECT COALESCE(SUM(gp.goles),0) FROM goleadores_partido gp
            JOIN jugadores j ON gp.jugador_id=j.id
            WHERE gp.partido_id=? AND j.equipo_id=?
        """, (pid, j_row["equipo_id"])).fetchone()[0]

        if ya + goles > permitidos:
            conn.close()
            messagebox.showerror("Límite superado",
                f"El equipo marcó {permitidos} gol(es). Ya asignados: {ya}. "
                f"Solo puedes añadir {max(0, permitidos-ya)} más."); return

        conn.execute("INSERT INTO goleadores_partido (partido_id,jugador_id,goles) VALUES (?,?,?)",
                     (pid, jid, goles))
        conn.execute("UPDATE jugadores SET goles_marcados=goles_marcados+? WHERE id=?", (goles, jid))
        conn.commit(); conn.close()

        self.spin_gol_cantidad.set(1)
        self._on_partido_seleccionado_ver_goleadores()
        self._refresh_goleadores()

    def _on_limpiar_goleadores_partido(self):
        item = self.tree_partidos.selection() if hasattr(self,"tree_partidos") else None
        if not item: return
        pid = int(self.tree_partidos.item(item,"values")[0])
        if not messagebox.askyesno("Confirmar","¿Borrar todos los goleadores de este partido?"): return
        # Restar los goles a los jugadores antes de borrar
        conn = _conn(self.db_path)
        filas = conn.execute("SELECT jugador_id, goles FROM goleadores_partido WHERE partido_id=?",
                              (pid,)).fetchall()
        for f in filas:
            conn.execute("UPDATE jugadores SET goles_marcados=MAX(0,goles_marcados-?) WHERE id=?",
                         (f["goles"], f["jugador_id"]))
        conn.execute("DELETE FROM goleadores_partido WHERE partido_id=?", (pid,))
        conn.commit(); conn.close()
        self._on_partido_seleccionado_ver_goleadores()
        self._refresh_goleadores()

    def _on_toggle_archivo_partido(self):
        item = self.tree_partidos.selection() if hasattr(self,"tree_partidos") else None
        if not item: return
        vals = self.tree_partidos.item(item,"values")
        pid = int(vals[0])
        estado_actual = 1 if vals[5] == "📦 Archivado" else 0
        self.db.toggle_archivo_partido(pid, 1 - estado_actual)
        self._refresh_partidos()

    def _on_toggle_historico(self):
        val = self._mostrar_archivados.get()
        self._mostrar_archivados.set(1 - val)
        self._refresh_partidos()

    def _on_eliminar_partido(self):
        item = self.tree_partidos.selection() if hasattr(self,"tree_partidos") else None
        if not item: return
        pid = int(self.tree_partidos.item(item,"values")[0])
        if messagebox.askyesno("Confirmar","¿Eliminar este partido?"):
            self.db.eliminar_partido_por_id(pid)
            self._refresh_partidos()

    def _on_jornada_filtrada(self, event=None):
        if not hasattr(self,"tree_partidos"): return
        jornada = self.combo_jornada.get()
        arch    = self._mostrar_archivados.get()
        if jornada == "-- Archivo Histórico --":
            arch = 1; jornada = None
        elif jornada == "-- Ver Todos los Partidos --":
            jornada = None
        partidos = self.db.obtener_partidos_con_equipos(
            fecha_filtro=jornada, mostrar_archivados=arch
        )
        self.tree_partidos.delete(*self.tree_partidos.get_children())
        for p in partidos:
            gl = p["goles_local"]; gv = p["goles_visitante"]
            res = f"{gl}–{gv}" if (gl is not None and gl != -1) else "–"
            estado = "📦 Archivado" if p["archivado"] else ("✅ Jugado" if p["jugado"] else "⏳ Pendiente")
            self.tree_partidos.insert("","end", values=(
                p["id"], p["fecha"], p["nombre_equipo_local"],
                p["nombre_equipo_visitante"], res, estado
            ))

    def _on_recalcular_clasificacion(self):
        self._refresh_clasificacion()
        messagebox.showinfo("Hecho","Clasificación recalculada.")

    def _on_guardar_clasificacion_manual(self):
        item = self.tree_clas.selection() if hasattr(self,"tree_clas") else None
        if not item: messagebox.showwarning("Aviso","Selecciona un equipo."); return
        vals = self.tree_clas.item(item,"values")
        nombre = vals[1]
        try:
            pj,pg,pe,pp,gf,gc,pts = [int(vals[i]) for i in (3,4,5,6,7,8,10)]
        except Exception:
            messagebox.showerror("Error","No se pudieron leer las estadísticas."); return
        nv = {}
        for k,v in zip(("PJ","PG","PE","PP","GF","GC","PTS"),(pj,pg,pe,pp,gf,gc,pts)):
            r = simpledialog.askinteger(k, f"Valor de {k} para {nombre}:", initialvalue=v)
            if r is None: return
            nv[k] = r
        self.db.actualizar_clasificacion_manual(nombre, nv["PJ"],nv["PG"],nv["PE"],
                                                 nv["PP"],nv["GF"],nv["GC"],nv["PTS"])
        self._refresh_clasificacion()

    def _on_editar_goles_totales_manual(self, event):
        item = self.tree_jugadores.identify_row(event.y) if hasattr(self,"tree_jugadores") else None
        if not item: return
        vals = self.tree_jugadores.item(item,"values")
        nombre = vals[1]
        actual = int(vals[3])
        nuevo = simpledialog.askinteger("Goles totales",
            f"Nuevo total de goles para {nombre}:", initialvalue=actual)
        if nuevo is not None:
            self.db.establecer_goles_totales_manual(nombre, nuevo)
            self._refresh_jugadores()
            self._refresh_goleadores()

    def _on_recalcular_goleadores(self):
        self.db.recalcular_goleadores_totales()
        self._refresh_goleadores()
        messagebox.showinfo("Hecho","Goleadores recalculados desde partidos.")

    def _on_importar_goleadores_csv(self):
        """Acepta dos formatos de CSV:
          · 2 columnas:  jugador, goles
          · 3 columnas:  jugador, equipo, goles
          Las filas con texto en la columna de goles (cabeceras) se saltan solas.
        """
        ruta = filedialog.askopenfilename(title="CSV de Goleadores", filetypes=[("CSV","*.csv")])
        if not ruta: return
        importados = 0
        saltados   = 0
        errores    = []
        try:
            # Construir índice normalizado de jugadores de la BD
            conn_idx = _conn(self.db_path)
            cg = self.db._c_jug.get("goles_marcados") or "goles_marcados"
            filas_jug = conn_idx.execute("SELECT id, nombre FROM jugadores").fetchall()
            # {nombre_normalizado: id_real}
            indice = {_normalizar_nombre(f["nombre"]): f["id"] for f in filas_jug}
            conn_idx.close()

            with open(ruta, encoding="utf-8-sig") as f:   # utf-8-sig tolera BOM de Excel
                for n, row in enumerate(csv.reader(f), 1):
                    if not row: continue
                    jugador = row[0].strip()
                    if not jugador: continue

                    # Detectar formato: 2 cols (jugador,goles) o 3 cols (jugador,equipo,goles)
                    if len(row) >= 3:
                        goles_str = row[2].strip()
                    elif len(row) == 2:
                        goles_str = row[1].strip()
                    else:
                        continue

                    try:
                        goles = int(goles_str)
                    except ValueError:
                        saltados += 1   # cabecera o fila inválida
                        continue

                    # Buscar por nombre normalizado (sin acentos, sin distinción may/min)
                    jid = indice.get(_normalizar_nombre(jugador))
                    if jid:
                        conn_up = _conn(self.db_path)
                        conn_up.execute(f"UPDATE jugadores SET {cg}=? WHERE id=?", (goles, jid))
                        conn_up.commit(); conn_up.close()
                        importados += 1
                    else:
                        errores.append(f"Fila {n}: '{jugador}'")

            msg = f"✅ {importados} goleadores importados."
            if saltados: msg += f"\n⚠️  {saltados} fila(s) saltadas (cabecera o no numérico)."
            if errores:
                msg += f"\n❌ {len(errores)} no encontrado(s):\n" + "\n".join(errores[:8])
                if len(errores) > 8:
                    msg += f"\n  ... y {len(errores)-8} más."
            messagebox.showinfo("Importación completada", msg)
            self._refresh_goleadores()
        except Exception as e:
            messagebox.showerror("Error al leer el CSV", str(e))

    def _on_nueva_temporada(self):
        if not messagebox.askyesno("Nueva Temporada",
                "Esto borrará TODOS los resultados y estadísticas.\n¿Continuar?"):
            return
        conn = _conn(self.db_path)
        conn.execute("DELETE FROM partidos")
        conn.execute("DELETE FROM goleadores_partido")
        conn.execute("UPDATE equipos SET pj=0,pg=0,pe=0,pp=0,gf=0,gc=0,pts=0")
        conn.execute("UPDATE jugadores SET goles_marcados=0")
        conn.commit(); conn.close()
        self._refresh_all()
        messagebox.showinfo("Nueva Temporada","Se ha iniciado una temporada nueva.")

    def _on_simulacro_historial(self):
        conn = _conn(self.db_path)
        if "historial_simulacros" not in {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}:
            conn.execute("CREATE TABLE historial_simulacros (id INTEGER PRIMARY KEY, fecha TEXT, json TEXT)")
            conn.commit()
        snap = {"fecha": datetime.now().isoformat(),
                "clasificacion": [dict(r) for r in conn.execute("SELECT * FROM equipos").fetchall()]}
        conn.execute("INSERT INTO historial_simulacros (fecha,json) VALUES (?,?)",
                     (snap["fecha"], json.dumps(snap, ensure_ascii=False)))
        conn.commit()
        rows = conn.execute("SELECT id,fecha FROM historial_simulacros ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        ventana = tk.Toplevel(self._root)
        ventana.title("Historial de Simulacros")
        ventana.geometry("460x300")
        ventana.transient(self._root); ventana.grab_set()
        tree_h = tb.Treeview(ventana, columns=("id","fecha"), show="headings", height=12)
        tree_h.heading("id", text="ID"); tree_h.column("id", width=60, anchor="center")
        tree_h.heading("fecha", text="Fecha y Hora"); tree_h.column("fecha", width=340)
        tree_h.pack(fill=BOTH, expand=True, padx=10, pady=10)
        for r in rows:
            tree_h.insert("","end", values=(r[0], r[1]))
        messagebox.showinfo("Simulacro","Estado actual guardado en historial.")

    # ──────────────────────────────────────────────────────
    # EVENTOS MUNDO / COPA
    # ──────────────────────────────────────────────────────

    def _cargar_grupo_seleccionado(self):
        """Carga partidos y posiciones del grupo seleccionado en dashboard."""
        if not hasattr(self, "grupo_seleccionado"): return
        
        # Recalcular puntos ANTES de cargar
        self._recalcular_grupos()
        
        grupo = self.grupo_seleccionado.get()
        conn = _conn(self.db_path)
        
        try:
            # Limpiar tablas
            if hasattr(self, "tree_partidos_grupo"):
                self.tree_partidos_grupo.delete(*self.tree_partidos_grupo.get_children())
            if hasattr(self, "tree_posiciones_grupo"):
                self.tree_posiciones_grupo.delete(*self.tree_posiciones_grupo.get_children())
            
            # Cargar partidos del grupo
            if "Jornada" in grupo:  # Liga
                where = f"p.jornada = '{grupo}'"
            else:  # Mundial/Copa
                where = f"p.grupo = '{grupo}'"
            
            partidos = conn.execute(f"""
                SELECT p.id, p.fecha, el.nombre AS local, ev.nombre AS visitante,
                       p.goles_local, p.goles_visitante, p.estadio
                FROM partidos p
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                WHERE {where}
                ORDER BY p.fecha ASC
            """).fetchall()
            
            for p in partidos:
                gl, gv = p["goles_local"], p["goles_visitante"]
                res = f"{gl}–{gv}" if gl != -1 else "–"
                if hasattr(self, "tree_partidos_grupo"):
                    self.tree_partidos_grupo.insert("", "end", values=(
                        p["fecha"], p["local"], p["visitante"], res, p["estadio"] or ""
                    ))
            
            # Cargar posiciones del grupo
            if "Jornada" in grupo:  # Liga: mostrar clasificación general
                rows = conn.execute("""
                    SELECT nombre, pj, pg, pe, pp, gf, gc, pts
                    FROM equipos
                    ORDER BY pts DESC, (gf-gc) DESC, gf DESC
                """).fetchall()
            else:  # Mundial/Copa: solo del grupo seleccionado
                rows = conn.execute("""
                    SELECT nombre, pj, pg, pe, pp, gf, gc, pts
                    FROM equipos
                    WHERE grupo = ?
                    ORDER BY pts DESC, (gf-gc) DESC, gf DESC
                """, (grupo,)).fetchall()
            
            for pos, r in enumerate(rows, 1):
                if hasattr(self, "tree_posiciones_grupo"):
                    # Color según posición (para mundial)
                    tag = ()
                    if self.tipo == "mundial":
                        if pos <= 2:
                            tag = ("clasificado",)
                        elif pos > 2:
                            tag = ("eliminado",)
                    self.tree_posiciones_grupo.insert("", "end", values=(
                        pos, r["nombre"], r["pj"], r["pg"], r["pe"], r["pp"],
                        r["gf"], r["gc"], r["pts"]
                    ), tags=tag)
            
            # Configurar colores
            if self.tipo == "mundial" and hasattr(self, "tree_posiciones_grupo"):
                self.tree_posiciones_grupo.tag_configure("clasificado", background="#90EE90")
                self.tree_posiciones_grupo.tag_configure("eliminado", background="#FFB6C6")
            
            # Actualizar combo de partidos
            opciones = []
            for p in partidos:
                gl, gv = p["goles_local"], p["goles_visitante"]
                res = f"{gl}–{gv}" if gl != -1 else "–"
                opciones.append(f"{p['id']} - {p['local']} vs {p['visitante']} [{res}]")
            
            if hasattr(self, "combo_partido_mundial"):
                self.combo_partido_mundial["values"] = opciones
            
            # Cargar goleadores
            self._refresh_goleadores_mundial()
        
        except Exception as e:
            print(f"Error cargando grupo: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def _cargar_grupos(self):
        if not hasattr(self, "tree_grupos"): return
        self._recalcular_grupos()
        self.tree_grupos.delete(*self.tree_grupos.get_children())

        # Configurar colores para copa
        if self.tipo == "copa":
            self.tree_grupos.tag_configure("octavos",   background="#006400", foreground="white")
            self.tree_grupos.tag_configure("playoff",   background="#90EE90", foreground="black")
            self.tree_grupos.tag_configure("eliminados",background="#DC143C", foreground="white")

        conn = _conn(self.db_path)
        tiene_grupos = conn.execute(
            "SELECT COUNT(*) FROM equipos WHERE grupo IS NOT NULL AND grupo != ''"
        ).fetchone()[0] > 0
        if tiene_grupos:
            rows = conn.execute("""
                SELECT COALESCE(grupo,'') AS grupo, nombre, pj, pg, pe, pp, gf, gc, pts
                FROM equipos
                ORDER BY grupo ASC, pts DESC, (gf-gc) DESC, gf DESC
            """).fetchall()
        else:
            rows = conn.execute("""
                SELECT '' AS grupo, nombre, pj, pg, pe, pp, gf, gc, pts
                FROM equipos
                ORDER BY pts DESC, (gf-gc) DESC, gf DESC
            """).fetchall()
        conn.close()

        for pos, r in enumerate(rows, 1):
            if self.tipo == "copa":
                if pos <= 8:                tag = ("octavos",)
                elif 9 <= pos <= 24:        tag = ("playoff",)
                else:                       tag = ("eliminados",)
            else:
                tag = ()
            self.tree_grupos.insert("","end", values=(
                r["grupo"], r["nombre"], r["pj"], r["pg"],
                r["pe"], r["pp"], r["gf"], r["gc"], r["pts"]
            ), tags=tag)
        self._refresh_goleadores_mundial()

    def _desempatar_mundial_h2h(self, grupo_eq, grupo_id, conn):
        """Aplica lógica FIFA 2026: DG → GF → Fair Play → Ranking FIFA (H2H simplificado)"""
        def calc_fair_play(eq_id):
            try:
                r = conn.execute("""
                    SELECT SUM(COALESCE(tarjetas_rojas_local,0)*2 + COALESCE(tarjetas_amarillas_local,0)) AS pts_loc,
                           SUM(COALESCE(tarjetas_rojas_visitante,0)*2 + COALESCE(tarjetas_amarillas_visitante,0)) AS pts_vis
                    FROM partidos WHERE grupo=? AND (equipo_local_id=? OR equipo_visitante_id=?)
                """, (grupo_id, eq_id, eq_id)).fetchone()
                pts_loc = r["pts_loc"] or 0 if r else 0
                pts_vis = r["pts_vis"] or 0 if r else 0
                return pts_loc + pts_vis
            except:
                return 0
        
        # Agrupar por puntos
        pts_map = {}
        for eq_id, data in grupo_eq.items():
            p = data["pts"]
            if p not in pts_map: pts_map[p] = []
            pts_map[p].append(eq_id)
        
        # Desempatar dentro de cada grupo de puntos iguales
        resultado_final = []
        for pts in sorted(pts_map.keys(), reverse=True):
            eqs = pts_map[pts]
            if len(eqs) == 1:
                resultado_final.append(eqs[0])
            else:
                # Aplicar desempate: DG → GF → Fair Play → FIFA Ranking
                eqs_sort = sorted(eqs, key=lambda e: (
                    -(grupo_eq[e]["gf"] - grupo_eq[e]["gc"]),  # DG (desc)
                    -grupo_eq[e]["gf"],  # GF (desc)
                    -calc_fair_play(e),  # Fair Play (menos tarjetas = mejor)
                    grupo_eq[e].get("ranking_fifa", 999)  # FIFA Ranking (asc)
                ))
                resultado_final.extend(eqs_sort)
        return resultado_final

    def _recalcular_grupos(self):
        """Recalcula estadísticas con manejo seguro de conexiones."""
        try:
            conn = _conn(self.db_path)
            conn.execute("UPDATE equipos SET pj=0,pg=0,pe=0,pp=0,gf=0,gc=0,pts=0")
            
            # Determinar filtro según tipo
            if self.tipo == "copa":
                where = "jugado=1 AND fase LIKE 'Liga%' AND goles_local!=-1 AND goles_visitante!=-1"
            elif self.tipo in ("mundial","euro"):
                where = "jugado=1 AND fase='Fase de grupos' AND goles_local!=-1 AND goles_visitante!=-1"
            else:
                where = "jugado=1 AND goles_local!=-1 AND goles_visitante!=-1"
            
            # Obtener partidos
            try:
                partidos = conn.execute(
                    f"SELECT equipo_local_id, equipo_visitante_id, goles_local, goles_visitante, grupo FROM partidos WHERE {where}"
                ).fetchall()
            except:
                # Si grupo no existe aún, hacer sin ella
                partidos = conn.execute(
                    f"SELECT equipo_local_id, equipo_visitante_id, goles_local, goles_visitante FROM partidos WHERE {where}"
                ).fetchall()
            
            # Procesar cada partido
            for p in partidos:
                l = p["equipo_local_id"]
                v = p["equipo_visitante_id"]
                gl = p["goles_local"]
                gv = p["goles_visitante"]
                
                conn.execute("UPDATE equipos SET pj=pj+1,gf=gf+?,gc=gc+? WHERE id=?", (gl,gv,l))
                conn.execute("UPDATE equipos SET pj=pj+1,gf=gf+?,gc=gc+? WHERE id=?", (gv,gl,v))
                
                if gl > gv:
                    conn.execute("UPDATE equipos SET pg=pg+1,pts=pts+3 WHERE id=?",(l,))
                    conn.execute("UPDATE equipos SET pp=pp+1 WHERE id=?",(v,))
                elif gv > gl:
                    conn.execute("UPDATE equipos SET pp=pp+1 WHERE id=?",(l,))
                    conn.execute("UPDATE equipos SET pg=pg+1,pts=pts+3 WHERE id=?",(v,))
                else:
                    conn.execute("UPDATE equipos SET pe=pe+1,pts=pts+1 WHERE id=?",(l,))
                    conn.execute("UPDATE equipos SET pe=pe+1,pts=pts+1 WHERE id=?",(v,))
            
            conn.commit()
            
            # Para mundial: aplicar desempate H2H por grupo
            if self.tipo == "mundial":
                try:
                    grupos = conn.execute(
                        "SELECT DISTINCT grupo FROM partidos WHERE grupo IS NOT NULL"
                    ).fetchall()
                    for gid in grupos:
                        grupo_id = gid["grupo"] if isinstance(gid, dict) else gid[0]
                        eq_grupo = {}
                        for r in conn.execute(
                            "SELECT id, nombre, pj, pg, pe, pp, gf, gc, pts, ranking_fifa FROM equipos WHERE grupo=?", 
                            (grupo_id,)):
                            eq_grupo[r["id"]] = dict(r) if hasattr(r, 'keys') else {
                                'id': r[0], 'nombre': r[1], 'pj': r[2], 'pg': r[3], 'pe': r[4], 'pp': r[5],
                                'gf': r[6], 'gc': r[7], 'pts': r[8], 'ranking_fifa': r[9]
                            }
                        if eq_grupo:
                            self._desempatar_mundial_h2h(eq_grupo, grupo_id, conn)
                except Exception as e:
                    print(f"Nota: desempate H2H skipped: {e}")
            
            conn.commit()
        except Exception as e:
            print(f"Error recalculando grupos: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def _refresh_goleadores_mundial(self):
        if not hasattr(self,"tree_gol_mundial"): return
        self.tree_gol_mundial.delete(*self.tree_gol_mundial.get_children())
        for g in self.db.obtener_goleadores_top():
            self.tree_gol_mundial.insert("","end", values=(g["jugador"], g["goles"]))

    def _cargar_partidos_mundiales(self):
        if not hasattr(self,"tree_mundial_partidos"): return
        self.tree_mundial_partidos.delete(*self.tree_mundial_partidos.get_children())
        conn = _conn(self.db_path)

        # Actualizar combo de filtro de fases (para copa)
        if hasattr(self,"combo_filtro_fase_cal"):
            fases_db = [r[0] for r in conn.execute(
                "SELECT DISTINCT fase FROM partidos WHERE fase IS NOT NULL ORDER BY fase"
            ).fetchall()]
            self.combo_filtro_fase_cal["values"] = [""] + fases_db

        fase_filtro = getattr(self, "combo_filtro_fase_cal", None)
        fase_sel = fase_filtro.get() if fase_filtro else ""

        where = "1=1"
        params = []
        if fase_sel:
            where = "p.fase=?"; params = [fase_sel]

        rows = conn.execute(f"""
            SELECT p.id, p.fecha,
                   el.nombre AS loc, ev.nombre AS vis,
                   p.goles_local, p.goles_visitante,
                   p.penaltis_local, p.penaltis_visitante,
                   COALESCE(p.estadio,'') AS estadio,
                   COALESCE(p.fase,'') AS fase
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            WHERE {where}
            ORDER BY p.fecha ASC, p.id ASC
        """, params).fetchall()
        conn.close()

        opciones = []
        for r in rows:
            gl, gv = r["goles_local"], r["goles_visitante"]
            if gl != -1 and gl is not None:
                res = f"{gl}–{gv}"
                # Añadir penaltis si los hubo
                pl, pv = r["penaltis_local"], r["penaltis_visitante"]
                if pl not in (-1, None): res += f" ({pl}–{pv}p)"
            else:
                res = "–"
            partido_txt = f"{r['loc']} vs {r['vis']}"
            self.tree_mundial_partidos.insert("","end",
                values=(r["id"], r["fecha"], partido_txt, res, r["estadio"], r["fase"]))
            # CAMBIO: Mostrar TODOS los partidos en el combo, no solo pendientes
            # Así puedes seguir editando/agregando goleadores a partidos ya jugados
            opciones.append(f"{r['id']} - {partido_txt} ({r['fase']}) [{res}]")
        if hasattr(self,"combo_partido_mundial"):
            self.combo_partido_mundial["values"] = opciones

    def _on_seleccion_partido_mundial(self, event=None):
        txt = self.combo_partido_mundial.get()
        if not txt: return
        pid_str = txt.split(" - ")[0]
        try:
            pid = int(pid_str)
        except ValueError: return
        conn = _conn(self.db_path)
        try:
            p = conn.execute("""
                SELECT equipo_local_id, equipo_visitante_id, goles_local, goles_visitante,
                       tarjetas_amarillas_local, tarjetas_amarillas_visitante,
                       tarjetas_rojas_local, tarjetas_rojas_visitante
                FROM partidos WHERE id=?""",
                (pid,)).fetchone()
            if not p: return
            
            # Pre-llenar goles
            if hasattr(self, "entry_mundial_gl"):
                self.entry_mundial_gl.delete(0, "end")
                if p["goles_local"] != -1:
                    self.entry_mundial_gl.insert(0, str(p["goles_local"]))
            if hasattr(self, "entry_mundial_gv"):
                self.entry_mundial_gv.delete(0, "end")
                if p["goles_visitante"] != -1:
                    self.entry_mundial_gv.insert(0, str(p["goles_visitante"]))
            
            # Pre-llenar tarjetas (mundial)
            if self.tipo == "mundial" and hasattr(self, "spin_am_l"):
                self.spin_am_l.delete(0, "end"); self.spin_am_l.set(p["tarjetas_amarillas_local"] or 0)
                self.spin_am_v.delete(0, "end"); self.spin_am_v.set(p["tarjetas_amarillas_visitante"] or 0)
                self.spin_ro_l.delete(0, "end"); self.spin_ro_l.set(p["tarjetas_rojas_local"] or 0)
                self.spin_ro_v.delete(0, "end"); self.spin_ro_v.set(p["tarjetas_rojas_visitante"] or 0)
            
            # Cargar equipos y jugadores
            n_loc = conn.execute("SELECT nombre FROM equipos WHERE id=?",(p["equipo_local_id"],)).fetchone()
            n_vis = conn.execute("SELECT nombre FROM equipos WHERE id=?",(p["equipo_visitante_id"],)).fetchone()
            equipos = []
            if n_loc: equipos.append(n_loc["nombre"])
            if n_vis: equipos.append(n_vis["nombre"])
            self.combo_eq_mundial["values"] = equipos
            if equipos: self.combo_eq_mundial.set(equipos[0])
            self._on_eq_mundial_cambiado()
        finally:
            try:
                conn.close()
            except:
                pass

    def _on_eq_mundial_cambiado(self, event=None):
        eq = self.combo_eq_mundial.get()
        if not eq: return
        jugadores = [j["nombre"] for j in self.db.obtener_jugadores_por_equipo(eq)]
        self.combo_jug_mundial["values"] = jugadores
        if jugadores: self.combo_jug_mundial.set(jugadores[0])

    def _on_doble_clic_calendario(self, event):
        item = self.tree_mundial_partidos.identify_row(event.y)
        if not item: return
        pid = int(self.tree_mundial_partidos.item(item,"values")[0])
        VentanaGoleadores(self, self.db_path, pid, callback=self._refresh_goleadores_mundial)

    def _grabar_resultado_mundial(self):
        txt = self.combo_partido_mundial.get() if hasattr(self,"combo_partido_mundial") else ""
        if not txt:
            messagebox.showwarning("Aviso","Selecciona un partido primero."); return
        pid = int(txt.split(" - ")[0])
        gl_s = self.entry_mundial_gl.get().strip()
        gv_s = self.entry_mundial_gv.get().strip()
        if not gl_s and not gv_s:
            conn = _conn(self.db_path)
            conn.execute("UPDATE partidos SET goles_local=-1,goles_visitante=-1,jugado=0 WHERE id=?", (pid,))
            conn.commit(); conn.close()
            self._cargar_grupos(); self._cargar_partidos_mundiales()
            messagebox.showinfo("OK","Resultado borrado.")
            return
        try:
            gl, gv = int(gl_s), int(gv_s)
            if gl < 0 or gv < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error","Introduce números válidos (≥ 0)."); return

        # Validar coherencia con goleadores ya registrados
        conn = _conn(self.db_path)
        a_loc = conn.execute("""
            SELECT COALESCE(SUM(gp.goles),0) FROM goleadores_partido gp
            JOIN jugadores j ON gp.jugador_id=j.id
            JOIN partidos p ON gp.partido_id=p.id
            WHERE gp.partido_id=? AND j.equipo_id=p.equipo_local_id
        """, (pid,)).fetchone()[0]
        a_vis = conn.execute("""
            SELECT COALESCE(SUM(gp.goles),0) FROM goleadores_partido gp
            JOIN jugadores j ON gp.jugador_id=j.id
            JOIN partidos p ON gp.partido_id=p.id
            WHERE gp.partido_id=? AND j.equipo_id=p.equipo_visitante_id
        """, (pid,)).fetchone()[0]
        if a_loc > gl or a_vis > gv:
            conn.close()
            messagebox.showerror("Cuadre",
                f"Ya hay {a_loc} goles locales y {a_vis} visitantes registrados.\n"
                "Edita los goleadores antes de bajar el marcador."); return
        conn.execute("UPDATE partidos SET goles_local=?,goles_visitante=?,jugado=1 WHERE id=?",
                     (gl, gv, pid))
        
        # Guardar tarjetas (mundial) y penaltis (copa)
        if self.tipo == "mundial" and hasattr(self,"spin_am_l"):
            try:
                am_l = int(self.spin_am_l.get())
                am_v = int(self.spin_am_v.get())
                ro_l = int(self.spin_ro_l.get())
                ro_v = int(self.spin_ro_v.get())
                conn.execute(
                    "UPDATE partidos SET tarjetas_amarillas_local=?,tarjetas_amarillas_visitante=?,"
                    "tarjetas_rojas_local=?,tarjetas_rojas_visitante=? WHERE id=?",
                    (am_l, am_v, ro_l, ro_v, pid))
                for spin in (self.spin_am_l, self.spin_am_v, self.spin_ro_l, self.spin_ro_v):
                    spin.delete(0,"end"); spin.set(0)
            except ValueError:
                pass
        
        if self.tipo == "copa" and hasattr(self,"entry_pen_local"):
            try:
                pl = int(self.entry_pen_local.get().strip())
                pv = int(self.entry_pen_visit.get().strip())
                conn.execute("UPDATE partidos SET penaltis_local=?,penaltis_visitante=? WHERE id=?",
                             (pl, pv, pid))
                self.entry_pen_local.delete(0,"end")
                self.entry_pen_visit.delete(0,"end")
            except ValueError:
                pass
        conn.commit(); conn.close()
        self.entry_mundial_gl.delete(0,"end"); self.entry_mundial_gv.delete(0,"end")
        self._cargar_grupos(); self._cargar_partidos_mundiales()
        faltan_l = gl - a_loc; faltan_v = gv - a_vis
        msg = "Marcador guardado."
        if faltan_l > 0 or faltan_v > 0:
            msg += f"\n⚠️  Falta asignar {faltan_l} gol(es) local y {faltan_v} visitante."
        else:
            msg += "\n✅ Goleadores cuadrados."
        messagebox.showinfo("Marcador", msg)

    def _grabar_gol_mundial(self):
        txt = self.combo_partido_mundial.get() if hasattr(self,"combo_partido_mundial") else ""
        if not txt:
            messagebox.showwarning("Aviso","Selecciona un partido primero."); return
        pid   = int(txt.split(" - ")[0])
        jugador = self.combo_jug_mundial.get()
        equipo  = self.combo_eq_mundial.get()
        if not jugador:
            messagebox.showwarning("Aviso","Selecciona un jugador."); return
        try:
            goles = int(self.spin_goles_mundial.get())
        except ValueError:
            goles = 1
        
        conn = None
        try:
            conn = _conn(self.db_path)
            p = conn.execute("""
                SELECT equipo_local_id, equipo_visitante_id, goles_local, goles_visitante
                FROM partidos WHERE id=?""", (pid,)).fetchone()
            if not p:
                messagebox.showerror("Error","Partido no encontrado."); return
            if p["goles_local"] == -1:
                messagebox.showerror("Bloqueo","Graba el marcador antes de asignar goleadores."); return

            eid = self.db.obtener_id_equipo(equipo)
            es_local = eid == p["equipo_local_id"]
            permitidos = p["goles_local"] if es_local else p["goles_visitante"]
            ya = conn.execute("""
                SELECT COALESCE(SUM(gp.goles),0) FROM goleadores_partido gp
                JOIN jugadores j ON gp.jugador_id=j.id
                WHERE gp.partido_id=? AND j.equipo_id=?
            """, (pid, eid)).fetchone()[0]
            if ya + goles > permitidos:
                messagebox.showerror("Límite",
                    f"{equipo} marcó {permitidos} goles total.\n"
                    f"Ya asignados: {ya}. Solo puedes añadir {permitidos-ya} más."); return
            jid = self.db.obtener_id_jugador(jugador)
            if not jid:
                messagebox.showerror("Error","Jugador no encontrado."); return
            conn.execute("INSERT INTO goleadores_partido (partido_id,jugador_id,goles) VALUES (?,?,?)",
                         (pid, jid, goles))
            conn.execute("UPDATE jugadores SET goles_marcados=goles_marcados+? WHERE id=?", (goles,jid))
            conn.commit()
            
            self.spin_goles_mundial.set(1)
            self.combo_jug_mundial.set("")
            self._refresh_goleadores_mundial()
            faltan = permitidos - ya - goles
            msg = f"⚽ {goles} gol(es) de {jugador}."
            if faltan > 0:
                msg += f"\n⚠️  Faltan {faltan} gol(es) de {equipo}."
            else:
                msg += "\n✅ ¡Goleadores cuadrados!"
            messagebox.showinfo("Éxito", msg)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo grabar: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    def _cargar_eliminatorias(self):
        if not hasattr(self,"tree_clasificados"): return
        self.tree_clasificados.delete(*self.tree_clasificados.get_children())
        conn = _conn(self.db_path)
        rows = conn.execute("""
            SELECT COALESCE(grupo,'?') AS grupo, nombre, pts, gf, gc
            FROM equipos
            ORDER BY grupo ASC, pts DESC, (gf-gc) DESC, gf DESC
        """).fetchall()
        grupos_vistos, clasificados, terceros = {}, [], []
        for r in rows:
            grp = r["grupo"]
            grupos_vistos[grp] = grupos_vistos.get(grp, 0) + 1
            pos = grupos_vistos[grp]
            if pos <= 2:
                clasificados.append((grp, f"{pos}º", r["nombre"], r["pts"]))
            elif pos == 3:
                terceros.append({"grupo":grp,"pais":r["nombre"],"pts":r["pts"],
                                  "dif":r["gf"]-r["gc"],"gf":r["gf"]})
        if self.tipo == "mundial":
            terceros.sort(key=lambda x:(x["pts"],x["dif"],x["gf"]), reverse=True)
            mejores = [t["pais"] for t in terceros[:8]]
            for t in terceros[:8]:
                clasificados.append((t["grupo"],"3º",t["pais"],t["pts"]))
        else:
            mejores = []
        nombres_clas = [c[2] for c in clasificados]
        if hasattr(self,"combo_elim_local"):
            self.combo_elim_local["values"] = sorted(nombres_clas)
            self.combo_elim_vis["values"]   = sorted(nombres_clas)
        for c in clasificados:
            self.tree_clasificados.insert("","end", values=c)
        # Cuadro del torneo — fases dinámicas según tipo
        fases_grupo = {"Fase de grupos", "Fase de liga"}
        self.tree_cuadro.delete(*self.tree_cuadro.get_children())
        todas_fases = fases_para_tipo(self.tipo)
        fase_orden  = {f: i for i,f in enumerate(todas_fases)}
        elim_rows = conn.execute("""
            SELECT p.id, p.fase, p.fecha, el.nombre AS loc, ev.nombre AS vis,
                   p.goles_local AS gl, p.goles_visitante AS gv
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            WHERE p.fase IS NOT NULL AND p.fase != ''
            ORDER BY p.fase, p.fecha
        """).fetchall()
        conn.close()
        campeon = None
        for r in sorted(elim_rows, key=lambda x: fase_orden.get(x["fase"],99)):
            if r["fase"] in fases_grupo:
                continue
            res = f"{r['gl']}–{r['gv']}" if (r["gl"] is not None and r["gl"] != -1) else "–"
            fase = r["fase"]
            tag = ""
            if "Playoffs" in fase or "Dieciseis" in fase: tag="r16"
            elif "Octavos" in fase: tag="octavos"
            elif "Cuartos" in fase: tag="cuartos"
            elif "Semi"    in fase: tag="semis"
            elif "Final"   in fase: tag="final"
            self.tree_cuadro.insert("","end",
                values=(fase, r["fecha"], f"{r['loc']} vs {r['vis']}", res), tags=(tag,))
            if fase == "Final" and r["gl"] is not None and r["gl"] != -1:
                campeon = r["loc"] if r["gl"]>r["gv"] else (
                    r["vis"] if r["gv"]>r["gl"] else f"{r['loc']} o {r['vis']} (pen.)")
        if campeon:
            self.tree_cuadro.insert("","end",
                values=("🏆 CAMPEÓN","⭐⭐⭐",f"¡{campeon.upper()}!","⭐⭐⭐"),
                tags=("campeon",))
        # Goleadores en eliminatorias
        if hasattr(self,"tree_elim_goles"):
            self.tree_elim_goles.delete(*self.tree_elim_goles.get_children())
            for g in self.db.obtener_goleadores_top():
                self.tree_elim_goles.insert("","end", values=(g["jugador"],g["goles"]))

    def _crear_cruce_eliminatoria(self):
        fase    = self.combo_fase_elim.get()
        local   = self.combo_elim_local.get()
        visit   = self.combo_elim_vis.get()
        fecha   = self.entry_elim_fecha.get().strip()
        estadio = self.entry_elim_estadio.get().strip()
        if not all([fase, local, visit, fecha]):
            messagebox.showwarning("Aviso","Rellena fase, equipos y fecha."); return
        if local == visit:
            messagebox.showwarning("Aviso","El local y visitante no pueden ser el mismo."); return
        id_l = self.db.obtener_id_equipo(local)
        id_v = self.db.obtener_id_equipo(visit)
        if not id_l or not id_v:
            messagebox.showerror("Error","Equipo no encontrado."); return
        conn = _conn(self.db_path)
        conn.execute("""
            INSERT INTO partidos (equipo_local_id,equipo_visitante_id,fecha,estadio,fase)
            VALUES (?,?,?,?,?)
        """, (id_l, id_v, fecha, estadio, fase))
        conn.commit(); conn.close()
        self._cargar_eliminatorias()
        self._cargar_partidos_mundiales()
        messagebox.showinfo("Cruce creado",
            f"{fase}: {local} vs {visit} → partido programado.\n"
            "Puedes grabar el resultado desde la pestaña de Grupos.")

    # ──────────────────────────────────────────────────────
    # EDITAR PARTIDO (ventana flotante)
    # ──────────────────────────────────────────────────────

    def _abrir_editar_partido(self):
        """Abre ventana para editar resultado y goleadores de un partido."""
        # Detectar partido seleccionado según modo
        pid = None
        if self.tipo == "liga" and hasattr(self,"tree_partidos"):
            item = self.tree_partidos.selection()
            if item:
                pid = int(self.tree_partidos.item(item,"values")[0])
        elif hasattr(self,"combo_partido_mundial"):
            txt = self.combo_partido_mundial.get()
            if txt:
                try: pid = int(txt.split(" - ")[0])
                except: pass
        if not pid:
            messagebox.showwarning("Aviso","Selecciona un partido primero."); return

        conn = _conn(self.db_path)
        p = conn.execute("""
            SELECT p.*, el.nombre AS loc_nom, ev.nombre AS vis_nom
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            WHERE p.id=?
        """, (pid,)).fetchone()
        conn.close()
        if not p: return

        win = tk.Toplevel(self._root)
        win.title(f"Editar — {p['loc_nom']} vs {p['vis_nom']}")
        win.geometry("500x420"); win.resizable(False,False)
        win.transient(self._root); win.grab_set()
        frm = tb.Frame(win, padding=20); frm.pack(fill=BOTH, expand=True)

        tb.Label(frm, text=f"{p['loc_nom']}  vs  {p['vis_nom']}",
                 font="-size 13 -weight bold").grid(row=0,column=0,columnspan=4,pady=(0,15))
        tb.Label(frm,text="Goles Local:").grid(row=1,column=0,sticky=W,pady=5)
        e_gl = tb.Entry(frm, width=8); e_gl.grid(row=1,column=1,padx=5)
        tb.Label(frm,text="Goles Visitante:").grid(row=1,column=2,sticky=W,pady=5)
        e_gv = tb.Entry(frm, width=8); e_gv.grid(row=1,column=3,padx=5)
        gl_act = p["goles_local"];  gv_act = p["goles_visitante"]
        if gl_act != -1: e_gl.insert(0, str(gl_act))
        if gv_act != -1: e_gv.insert(0, str(gv_act))

        tb.Label(frm,text="Fecha:").grid(row=2,column=0,sticky=W,pady=5)
        e_fecha = tb.Entry(frm, width=15); e_fecha.grid(row=2,column=1,padx=5)
        e_fecha.insert(0, p["fecha"] or "")

        # Goleadores actuales
        tb.Label(frm, text="Goleadores registrados:", font="-weight bold").grid(
            row=3,column=0,columnspan=4,pady=(15,5),sticky=W)
        tree_gp = tb.Treeview(frm, columns=("jug","goles"), show="headings", height=5)
        tree_gp.heading("jug",text="Jugador"); tree_gp.heading("goles",text="Goles")
        tree_gp.column("goles",width=60,anchor="center")
        tree_gp.grid(row=4,column=0,columnspan=4,sticky="ew")

        def _recargar_goles():
            tree_gp.delete(*tree_gp.get_children())
            c2 = _conn(self.db_path)
            for g in c2.execute("""
                SELECT j.nombre, gp.goles FROM goleadores_partido gp
                JOIN jugadores j ON gp.jugador_id=j.id
                WHERE gp.partido_id=?""", (pid,)).fetchall():
                tree_gp.insert("","end",values=(g["nombre"],g["goles"]))
            c2.close()
        _recargar_goles()

        def _limpiar_goles():
            if messagebox.askyesno("Confirmar","¿Borrar todos los goleadores de este partido?"):
                c2 = _conn(self.db_path)
                c2.execute("DELETE FROM goleadores_partido WHERE partido_id=?", (pid,))
                c2.commit(); c2.close()
                _recargar_goles()
        tb.Button(frm,text="🗑 Limpiar goleadores", bootstyle="danger-outline",
                  command=_limpiar_goles).grid(row=5,column=0,columnspan=2,sticky="ew",pady=8)

        def _guardar():
            try:
                gl = int(e_gl.get()); gv = int(e_gv.get())
            except ValueError:
                messagebox.showerror("Error","Goles deben ser números."); return
            c2 = _conn(self.db_path)
            c2.execute("UPDATE partidos SET goles_local=?,goles_visitante=?,jugado=1,fecha=? WHERE id=?",
                       (gl, gv, e_fecha.get().strip(), pid))
            c2.commit(); c2.close()
            self._refresh_all()
            win.destroy()
        tb.Button(frm,text="💾 Guardar Cambios", bootstyle=SUCCESS,
                  command=_guardar).grid(row=5,column=2,columnspan=2,sticky="ew",pady=8)

    # ──────────────────────────────────────────────────────
    # EXPORTAR
    # ──────────────────────────────────────────────────────

    def _on_exportar(self):
        tipo_exp = self.combo_exp_tipo.get()
        fmt      = self.combo_exp_fmt.get()
        ext_map  = {"TXT":".txt","CSV":".csv","JSON":".json","PDF":".pdf"}
        ext = ext_map.get(fmt, ".txt")
        ruta = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(fmt, f"*{ext}")],
            initialfile=f"informe_{datetime.now().strftime('%Y%m%d_%H%M')}{ext}"
        )
        if not ruta: return
        try:
            if tipo_exp == "Tabla de Posiciones":
                datos = self.db.recalcular_y_obtener_clasificacion()
                cabecera = ["Pos","Equipo","Ciudad","PJ","PG","PE","PP","GF","GC","DIF","PTS"]
                filas = [(i+1, d["nombre"], d.get("ciudad","") if isinstance(d,dict) else (d["ciudad"] or ""), d["pj"],d["pg"],d["pe"],
                          d["pp"],d["gf"],d["gc"],d["gf"]-d["gc"],d["pts"])
                         for i,d in enumerate(datos)]
            elif tipo_exp == "Lista de Goleadores":
                datos = self.db.obtener_goleadores_top()
                cabecera = ["Pos","Jugador","Equipo","Goles"]
                filas = [(i+1,d["jugador"],d["equipo"],d["goles"]) for i,d in enumerate(datos)]
            else:
                datos = self.db.obtener_partidos_con_equipos()
                cabecera = ["ID","Fecha","Local","Visitante","Resultado"]
                filas = [(d["id"],d["fecha"],d["nombre_equipo_local"],
                          d["nombre_equipo_visitante"],
                          f"{d['goles_local']}–{d['goles_visitante']}" if d["jugado"] else "–")
                         for d in datos]

            if fmt == "CSV":
                with open(ruta,"w",newline="",encoding="utf-8") as f:
                    w = csv.writer(f); w.writerow(cabecera); w.writerows(filas)
            elif fmt == "JSON":
                with open(ruta,"w",encoding="utf-8") as f:
                    json.dump([dict(zip(cabecera,r)) for r in filas], f,
                              ensure_ascii=False, indent=2)
            elif fmt == "PDF" and HAS_PDF:
                self._exportar_pdf(ruta, tipo_exp, cabecera, filas)
            else:
                with open(ruta,"w",encoding="utf-8") as f:
                    f.write(f"{tipo_exp}  —  {self.torneo_info.get('nombre','')}\n")
                    f.write("="*60 + "\n")
                    f.write("  ".join(f"{h:>8}" for h in cabecera) + "\n")
                    f.write("-"*60 + "\n")
                    for row in filas:
                        f.write("  ".join(f"{str(v):>8}" for v in row) + "\n")
            messagebox.showinfo("Exportado", f"Archivo guardado en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e))

    def _exportar_pdf(self, ruta, titulo, cabecera, filas):
        doc = SimpleDocTemplate(ruta, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"<b>{titulo}</b>", styles["Title"]),
            Paragraph(self.torneo_info.get("nombre",""), styles["Normal"]),
            Spacer(1, 12),
        ]
        tabla_data = [cabecera] + [[str(v) for v in f] for f in filas]
        t = Table(tabla_data)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#003366")),
            ("TEXTCOLOR",(0,0),(-1,0),  colors.white),
            ("FONTNAME",(0,0),(-1,0),   "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f0f0f0")]),
            ("GRID",(0,0),(-1,-1),       0.5, colors.grey),
            ("ALIGN",(0,0),(-1,-1),      "CENTER"),
        ]))
        story.append(t)
        doc.build(story)

    # ──────────────────────────────────────────────────────
    # GENERADORES COPA/CHAMPIONS
    # ──────────────────────────────────────────────────────

    def _on_generar_liga_completa(self):
        import random as _rnd
        equipos = self.db.obtener_nombres_equipos()
        if len(equipos) != 36:
            messagebox.showerror("Error",
                f"Se necesitan exactamente 36 equipos para la Liga.\nTienes {len(equipos)}."); return
        if not messagebox.askyesno("Confirmar",
                "¿Borrar partidos de liga previos y generar 8 jornadas (144 partidos)?"):
            return
        conn = _conn(self.db_path)
        conn.execute("DELETE FROM partidos WHERE fase LIKE 'Liga%'")
        conn.commit(); conn.close()
        equipos = list(equipos)
        _rnd.shuffle(equipos)
        conn = _conn(self.db_path)
        for jor in range(1, 9):
            jornada_lbl = f"Jornada {jor}"
            for i in range(18):
                local    = equipos[i]
                visitante= equipos[35 - i]
                if jor % 2 == 0:
                    local, visitante = visitante, local
                id_l = conn.execute("SELECT id FROM equipos WHERE nombre=?", (local,)).fetchone()["id"]
                id_v = conn.execute("SELECT id FROM equipos WHERE nombre=?", (visitante,)).fetchone()["id"]
                conn.execute(
                    "INSERT INTO partidos (equipo_local_id,equipo_visitante_id,fase,jornada,fecha,goles_local,goles_visitante) VALUES (?,?,?,?,?,?,?)",
                    (id_l, id_v, "Liga Regular", jornada_lbl, "2026", -1, -1)
                )
            equipos = [equipos[0]] + [equipos[-1]] + equipos[1:-1]
        conn.commit(); conn.close()
        self._refresh_all()
        messagebox.showinfo("Éxito","Se han generado las 8 jornadas de la Liga Regular (144 partidos).")

    def _obtener_ganadores_de_fase(self, fase):
        """Calcula el ganador de cada eliminatoria (ida+vuelta) de una fase."""
        conn = _conn(self.db_path)
        partidos = conn.execute("""
            SELECT el.nombre AS loc, ev.nombre AS vis,
                   p.goles_local AS gl, p.goles_visitante AS gv,
                   p.penaltis_local AS pl, p.penaltis_visitante AS pv
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id=el.id
            JOIN equipos ev ON p.equipo_visitante_id=ev.id
            WHERE p.fase=? AND p.goles_local!=-1
        """, (fase,)).fetchall()
        conn.close()
        eliminatorias = {}
        for p in partidos:
            par = tuple(sorted([p["loc"], p["vis"]]))
            if par not in eliminatorias:
                eliminatorias[par] = {par[0]:0, par[1]:0, "pen":{par[0]:-1, par[1]:-1}}
            eliminatorias[par][p["loc"]] += p["gl"]
            eliminatorias[par][p["vis"]] += p["gv"]
            if p["pl"] not in (-1, None):
                eliminatorias[par]["pen"][p["loc"]] = p["pl"]
                eliminatorias[par]["pen"][p["vis"]] = p["pv"]
        ganadores = []
        for par, d in eliminatorias.items():
            e1, e2 = par
            if d[e1] > d[e2]:         ganadores.append(e1)
            elif d[e2] > d[e1]:       ganadores.append(e2)
            elif d["pen"][e1] > d["pen"][e2]: ganadores.append(e1)
            else:                     ganadores.append(e2)
        return sorted(ganadores)

    def _on_generar_octavos_automatico(self):
        """Genera octavos cruzando los 8 primeros de liga con los 8 ganadores del playoff."""
        clasificacion = self._obtener_clasificacion_copa()
        if len(clasificacion) < 24:
            messagebox.showerror("Error","Necesitas al menos 24 equipos con estadísticas."); return
        ganadores_playoff = self._obtener_ganadores_de_fase("Playoffs")
        if len(ganadores_playoff) < 8:
            messagebox.showwarning("Atención",
                f"Faltan resultados de Playoffs. Solo hay {len(ganadores_playoff)} ganadores."); return
        top8 = [eq["nombre"] for eq in clasificacion[:8]]
        # Cruce: 1er vs ganador 16º, 2º vs 15º, etc. (confrontación inversa)
        conn = _conn(self.db_path)
        conn.execute("DELETE FROM partidos WHERE fase='Octavos de final'")
        for i in range(8):
            cabeza  = top8[i]
            rival   = ganadores_playoff[7 - i]
            id_c = conn.execute("SELECT id FROM equipos WHERE nombre=?",(cabeza,)).fetchone()["id"]
            id_r = conn.execute("SELECT id FROM equipos WHERE nombre=?",(rival,)).fetchone()["id"]
            conn.execute("INSERT INTO partidos (equipo_local_id,equipo_visitante_id,fase,jornada,fecha,goles_local,goles_visitante) VALUES (?,?,'Octavos de final','Ida','DD/MM/AAAA',-1,-1)", (id_r, id_c))
            conn.execute("INSERT INTO partidos (equipo_local_id,equipo_visitante_id,fase,jornada,fecha,goles_local,goles_visitante) VALUES (?,?,'Octavos de final','Vuelta','DD/MM/AAAA',-1,-1)", (id_c, id_r))
        conn.commit(); conn.close()
        self._refresh_all()
        messagebox.showinfo("Octavos generados","Se han creado los 16 partidos de Octavos de Final.")

    def _obtener_clasificacion_copa(self):
        self._recalcular_grupos()
        conn = _conn(self.db_path)
        rows = conn.execute("""
            SELECT nombre, pts, pj, gf, gc FROM equipos
            ORDER BY pts DESC, (gf-gc) DESC, gf DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _on_sorteo_manual(self):
        win = tk.Toplevel(self._root)
        win.title("Sorteo / Emparejamiento Manual"); win.grab_set()
        win.geometry("620x480")
        tb.Label(win, text="Fase y emparejamientos", font="-size 12 -weight bold").pack(pady=10)
        frm_top = tb.Frame(win); frm_top.pack(pady=5)
        tb.Label(frm_top, text="Fase:").pack(side=LEFT, padx=5)
        FASES_SORTEO = ["Playoffs","Octavos de final","Cuartos de final","Semifinal","Final"]
        fase_var = tk.StringVar(value="Cuartos de final")
        cb_fase = tb.Combobox(frm_top, textvariable=fase_var, values=FASES_SORTEO, state="readonly", width=22)
        cb_fase.pack(side=LEFT)
        frm_cruces = tb.Frame(win); frm_cruces.pack(fill=BOTH, expand=True, pady=10)
        self._combos_sorteo = []

        def _actualizar(*_):
            for w in frm_cruces.winfo_children(): w.destroy()
            self._combos_sorteo.clear()
            fase = fase_var.get()
            mapa = {"Playoffs":8,"Octavos de final":8,"Cuartos de final":4,"Semifinal":2,"Final":1}
            n = mapa.get(fase, 4)
            fase_previa = {"Playoffs":"","Octavos de final":"Playoffs",
                           "Cuartos de final":"Octavos de final",
                           "Semifinal":"Cuartos de final","Final":"Semifinal"}.get(fase,"")
            if fase_previa:
                gan = self._obtener_ganadores_de_fase(fase_previa)
                equipos_disp = gan if len(gan) == n*2 else self.db.obtener_nombres_equipos()
            else:
                equipos_disp = self.db.obtener_nombres_equipos()
            for i in range(n):
                f = tb.Frame(frm_cruces); f.pack(pady=4)
                tb.Label(f, text=f"Cruce {i+1}:", width=10).pack(side=LEFT)
                cb1 = tb.Combobox(f, values=sorted(equipos_disp), width=22, state="readonly")
                cb1.pack(side=LEFT, padx=4)
                tb.Label(f, text="vs").pack(side=LEFT)
                cb2 = tb.Combobox(f, values=sorted(equipos_disp), width=22, state="readonly")
                cb2.pack(side=LEFT, padx=4)
                self._combos_sorteo.append((cb1, cb2))

        cb_fase.bind("<<ComboboxSelected>>", _actualizar)
        _actualizar()

        def _guardar():
            fase = fase_var.get()
            ida_vuelta = fase not in ("Final",)
            conn = _conn(self.db_path)
            n = 0
            for cb1, cb2 in self._combos_sorteo:
                e1, e2 = cb1.get().strip(), cb2.get().strip()
                if not e1 or not e2: continue
                id1 = conn.execute("SELECT id FROM equipos WHERE nombre=?",(e1,)).fetchone()
                id2 = conn.execute("SELECT id FROM equipos WHERE nombre=?",(e2,)).fetchone()
                if not id1 or not id2: continue
                conn.execute("INSERT INTO partidos (equipo_local_id,equipo_visitante_id,fase,jornada,fecha,goles_local,goles_visitante) VALUES (?,?,?,?,?,-1,-1)",
                             (id1["id"],id2["id"],fase,"Ida" if ida_vuelta else "Único","DD/MM/AAAA"))
                n += 1
                if ida_vuelta:
                    conn.execute("INSERT INTO partidos (equipo_local_id,equipo_visitante_id,fase,jornada,fecha,goles_local,goles_visitante) VALUES (?,?,?,?,?,-1,-1)",
                                 (id2["id"],id1["id"],fase,"Vuelta","DD/MM/AAAA"))
                    n += 1
            conn.commit(); conn.close()
            if n:
                self._refresh_all(); win.destroy()
                messagebox.showinfo("Éxito",f"{n} partidos de {fase} generados.")
            else:
                messagebox.showwarning("Aviso","No se rellenó ningún emparejamiento.")

        tb.Button(win, text="🚀 Generar Partidos", bootstyle=SUCCESS, command=_guardar).pack(pady=15)

    # ──────────────────────────────────────────────────────
    # CIERRE
    # ──────────────────────────────────────────────────────

    def _cambiar_torneo(self):
        """Vuelve al selector de torneos sin cerrar la app."""
        # Limpiar AppMaestra actual
        self.destroy()
        
        # Mostrar dashboard principal nuevamente en el root
        root = self._root
        root.withdraw()  # Ocultar mientras se prepara
        
        # Limpiar cualquier widget existente
        for widget in root.winfo_children():
            widget.destroy()
        
        # Variable para almacenar el torneo seleccionado
        torneo_seleccionado = [None]
        
        def _on_torneo_seleccionado(torneo):
            """Callback cuando se selecciona un torneo."""
            torneo_seleccionado[0] = torneo
            root.quit()  # Salir del loop
        
        # Mostrar dashboard principal
        dashboard = DashboardPrincipal(root, None, _on_torneo_seleccionado)
        root.deiconify()  # Mostrar ventana
        root.mainloop()
        
        if torneo_seleccionado[0]:
            torneo = torneo_seleccionado[0]
            carpeta = _carpeta_bbdd()
            db_path = os.path.join(str(carpeta), torneo["archivo"])
            
            # Crear BD si no existe
            if not os.path.exists(db_path):
                crear_bd_nueva(db_path, torneo["nombre"], torneo["tipo"])
            
            torneo_info = leer_torneo_info(db_path)
            if not torneo_info:
                conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
                conn.execute("PRAGMA journal_mode = WAL")
                conn.executescript(SCHEMA)
                conn.execute("INSERT OR IGNORE INTO torneo_info (nombre,tipo,temporada) VALUES (?,?,?)",
                             (torneo["nombre"], torneo["tipo"], ""))
                conn.commit(); conn.close()
                torneo_info = leer_torneo_info(db_path)
            
            # Cargar nuevo torneo
            AppMaestra(root, db_path, torneo_info)

    def _al_cerrar(self):
        try: self.db.close_db()
        except: pass
        self._root.destroy()




# ──────────────────────────────────────────────────────────
# DASHBOARD PRINCIPAL - SELECTOR DE TORNEOS
# ──────────────────────────────────────────────────────────

class DashboardPrincipal(tk.Frame):
    """Panel principal para seleccionar y gestionar torneos."""
    
    def __init__(self, root, db_path, callback_torneo_seleccionado):
        super().__init__(root)
        self.pack(fill=BOTH, expand=True)
        self._root = root
        self.db_path = db_path
        self.callback = callback_torneo_seleccionado
        
        # Encabezado
        frm_header = tb.Frame(self, bootstyle="info")
        frm_header.pack(fill=X, padx=20, pady=20)
        tb.Label(frm_header, text="🏆 GESTOR PREMIUM DE TORNEOS 2026",
                 font="-size 20 -weight bold", bootstyle="inverse-info").pack(pady=10)
        tb.Label(frm_header, text="Selecciona el torneo que deseas gestionar",
                 font="-size 12", foreground="#555").pack()
        
        # Área central: selector de torneos
        frm_main = tb.Frame(self)
        frm_main.pack(fill=BOTH, expand=True, padx=40, pady=40)
        
        # Definir torneos disponibles
        self.torneos = [
            {"nombre": "⚽ LIGA", "tipo": "liga", "archivo": "liga_futbol_v2.db"},
            {"nombre": "🏅 CHAMPIONS LEAGUE", "tipo": "champions", "archivo": "champions_gui_v2.db"},
            {"nombre": "🌍 MUNDIAL 2026", "tipo": "mundial", "archivo": "mundial_2026_v2.db"},
            {"nombre": "🇪🇺 EUROCOPA 2024", "tipo": "euro", "archivo": "eurocopa_2024_v2.db"},
        ]
        
        # Grid de botones de torneos
        for i, torneo in enumerate(self.torneos):
            frm_torneo = tb.LabelFrame(frm_main, text=" " + torneo["nombre"] + " ")
            frm_torneo.grid(row=i//2, column=i%2, padx=15, pady=15, sticky="ew")
            frm_main.columnconfigure(i%2, weight=1)
            
            # Estado del torneo
            estado = self._obtener_estado_torneo(torneo)
            tb.Label(frm_torneo, text=estado, font="-size 10", 
                     foreground="#666", justify="left").pack(pady=(10,10), padx=10)
            
            # Botón seleccionar
            tb.Button(frm_torneo, text=f"Abrir {torneo['nombre'].split()[1]}", 
                      bootstyle=SUCCESS, width=30,
                      command=lambda t=torneo: self._seleccionar_torneo(t)).pack(padx=10, pady=10)
        
        # Footer
        frm_footer = tb.Frame(self)
        frm_footer.pack(fill=X, padx=20, pady=20)
        tb.Label(frm_footer, text="v2.0 - 2026 | Sistema flexible para Liga, Champions, Mundial, Eurocopa",
                 font="-size 9", foreground="#999").pack()
    
    def _obtener_estado_torneo(self, torneo):
        """Obtiene el estado del torneo desde la BD."""
        try:
            carpeta = _carpeta_bbdd()
            archivo = os.path.join(str(carpeta), torneo["archivo"])
            
            if not os.path.exists(archivo):
                return "📊 Estado: No iniciado\n⚙️ Acción: Crear nueva BD"
            
            info = leer_torneo_info(archivo)
            if not info:
                return "📊 Estado: BD vacía\n⚙️ Acción: Importar equipos"
            
            # Información básica
            conn = sqlite3.connect(archivo, timeout=10.0)
            try:
                num_equipos = conn.execute(
                    "SELECT COUNT(*) FROM equipos"
                ).fetchone()[0]
                num_partidos = conn.execute(
                    "SELECT COUNT(*) FROM partidos"
                ).fetchone()[0]
            finally:
                conn.close()
            
            return f"📊 Equipos: {num_equipos}\n📅 Partidos: {num_partidos}\n✓ Listo para usar"
        except Exception as e:
            return f"📊 Estado: Error\n⚙️ Acción: Verificar BD"
    
    def _seleccionar_torneo(self, torneo):
        """Callback cuando se selecciona un torneo."""
        self.callback(torneo)
        self.destroy()

# ──────────────────────────────────────────────────────────
# LOBBY
# ──────────────────────────────────────────────────────────

def abrir_lobby(root):
    """Muestra el lobby como Toplevel sobre el root ya creado.
    Devuelve la ruta de la BD elegida, o None si se cancela."""
    carpeta_dbs = _carpeta_bbdd()

    db_elegida = [None]

    lobby = tk.Toplevel(root)
    lobby.title("Gestor Universal de Torneos")
    lobby.resizable(False, False)
    lobby.geometry("520x340")
    lobby.grab_set()
    lobby.focus_force()
    # Centrar
    lobby.update_idletasks()
    sw = lobby.winfo_screenwidth(); sh = lobby.winfo_screenheight()
    lobby.geometry(f"520x340+{(sw-520)//2}+{(sh-340)//2}")

    tb.Label(lobby, text="⚽ Gestor Premium de Torneos",
             font="-size 16 -weight bold").pack(pady=(30,5))
    tb.Label(lobby, text="Selecciona o crea el torneo que quieres gestionar",
             font="-size 10", foreground="#666666").pack(pady=(0,25))

    card = tb.Frame(lobby, padding=10)
    card.pack(fill=X, padx=50)

    def _cargar():
        ruta = filedialog.askopenfilename(
            parent=lobby, title="Abrir base de datos",
            initialdir=carpeta_dbs,
            filetypes=[("Base de Datos SQLite","*.db")]
        )
        if ruta:
            db_elegida[0] = ruta
            lobby.destroy()

    def _crear():
        win = tk.Toplevel(lobby)
        win.title("Nuevo Torneo"); win.resizable(False,False); win.grab_set()
        win.geometry("360x260")
        frm = tb.Frame(win, padding=20); frm.pack(fill=BOTH, expand=True)
        tb.Label(frm, text="Nombre del torneo:").pack(anchor=W)
        e_nom = tb.Entry(frm); e_nom.pack(fill=X, pady=3)
        tb.Label(frm, text="Tipo:").pack(anchor=W, pady=(10,0))
        cb_tipo = tb.Combobox(frm, values=TIPOS_TORNEO, state="readonly")
        cb_tipo.pack(fill=X, pady=3); cb_tipo.set("liga")
        tb.Label(frm, text="Temporada (ej: 2025-26):").pack(anchor=W, pady=(10,0))
        e_temp = tb.Entry(frm); e_temp.pack(fill=X, pady=3)

        def _ok():
            nom  = e_nom.get().strip()
            tipo = cb_tipo.get()
            temp = e_temp.get().strip()
            if not nom:
                messagebox.showwarning("Aviso","Introduce el nombre del torneo.",parent=win)
                return
            nombre_arch = nom.replace(" ","_") + ".db"
            ruta = os.path.join(carpeta_dbs, nombre_arch)
            crear_bd_nueva(ruta, nom, tipo, temp)
            db_elegida[0] = ruta
            win.destroy()
            lobby.destroy()

        tb.Button(frm, text="✨ Crear", bootstyle=SUCCESS, command=_ok).pack(fill=X, pady=(15,0))

    def _salir():
        lobby.destroy()

    tb.Button(card, text="📂  Cargar Torneo Existente", bootstyle="primary",
              width=38, command=_cargar).pack(pady=6)
    tb.Button(card, text="✨  Crear Torneo Nuevo", bootstyle="success-outline",
              width=38, command=_crear).pack(pady=6)
    tb.Button(card, text="✖  Salir", bootstyle="secondary-outline",
              width=38, command=_salir).pack(pady=6)

    root.wait_window(lobby)
    return db_elegida[0]


# ──────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Captura de errores a fichero de log
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log_errores.txt")
    try:
        _log = open(log_path, "w", encoding="utf-8")
        class _Tee:
            def __init__(self, f, s): self._f=f; self._s=s
            def write(self,m): self._f.write(m); self._f.flush(); self._s.write(m)
            def flush(self): self._f.flush()
        sys.stdout = _Tee(_log, sys.__stdout__)
        sys.stderr = _Tee(_log, sys.__stderr__)
    except Exception:
        pass

    print(f"Iniciando Gestor Premium de Torneos — {datetime.now()}")

    # UN SOLO root durante toda la sesión
    root = tb.Window(themename="cosmo")
    root.geometry("1200x700")
    root.title("🏆 Gestor Premium de Torneos")
    
    # Variable para almacenar el torneo seleccionado
    torneo_seleccionado = [None]
    
    def _on_torneo_seleccionado(torneo):
        """Callback cuando se selecciona un torneo."""
        torneo_seleccionado[0] = torneo
        root.quit()  # Sale del loop de selección
    
    # Mostrar dashboard principal
    try:
        dashboard = DashboardPrincipal(root, None, _on_torneo_seleccionado)
        root.mainloop()
        
        if not torneo_seleccionado[0]:
            root.destroy()
            sys.exit(0)
        
        torneo = torneo_seleccionado[0]
        carpeta = _carpeta_bbdd()
        db_path = os.path.join(str(carpeta), torneo["archivo"])
        
        # Crear BD si no existe
        if not os.path.exists(db_path):
            crear_bd_nueva(db_path, torneo["nombre"], torneo["tipo"])
        
        torneo_info = leer_torneo_info(db_path)
        if not torneo_info:
            conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(SCHEMA)
            conn.execute("INSERT OR IGNORE INTO torneo_info (nombre,tipo,temporada) VALUES (?,?,?)",
                         (torneo["nombre"], torneo["tipo"], ""))
            conn.commit(); conn.close()
            torneo_info = leer_torneo_info(db_path)
        
        # Limpiar y cargar el torneo seleccionado
        for widget in root.winfo_children():
            widget.destroy()
        
        AppMaestra(root, db_path, torneo_info)
        root.deiconify()
        root.mainloop()
        
    except Exception as e:
        err = traceback.format_exc()
        print("ERROR CRÍTICO:", err)
        try:
            messagebox.showerror("Error Crítico", f"La app falló:\n{e}\n\nVer log: {log_path}")
        except:
            pass
        finally:
            root.destroy()
            sys.exit(1)
