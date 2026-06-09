# ui_components.py
# Componentes gráficos reutilizables: AutocompleteCombobox y VentanaGoleadores.
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox


class AutocompleteCombobox(tb.Combobox):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.set_completion_list(self.cget("values"))
        self.bind("<KeyRelease>", self._on_keyrelease)
        self.bind("<FocusIn>", self._on_focus_in)

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(list(set(completion_list)))
        self["values"] = self._completion_list

    def _on_focus_in(self, event):
        self["values"] = self._completion_list

    def _on_keyrelease(self, event):
        value = self.get()
        if not value:
            self["values"] = self._completion_list
            return
        hits = [item for item in self._completion_list if item.lower().startswith(value.lower())]
        self["values"] = hits


class VentanaGoleadores(tb.Toplevel):
    def __init__(self, parent, partido_id, local_name, visitante_name, goles_local, goles_visitante, db):
        super().__init__(parent)
        self.partido_id = partido_id
        self.local_name = local_name
        self.visitante_name = visitante_name
        self.goles_local = int(goles_local)
        self.goles_visitante = int(goles_visitante)
        self.db = db
        self.title(f"Asignar Goleadores: {local_name} vs {visitante_name}")
        self.resizable(False, False)

        self.jugadores_local = [j["nombre"] for j in self.db.obtener_jugadores_por_equipo(local_name)]
        self.jugadores_visit = [j["nombre"] for j in self.db.obtener_jugadores_por_equipo(visitante_name)]

        self.jugadores_local.insert(0, "(Propia Puerta)")
        self.jugadores_visit.insert(0, "(Propia Puerta)")

        # Listas para rastrear los selectores de jugador y cantidad
        self.filas_local = []
        self.filas_visitante = []

        self._crear_widgets()
        self.transient(parent)
        self.grab_set()
        self.focus_force()

    def _crear_widgets(self):
        frm_top = tb.Frame(self, padding=10)
        frm_top.pack(fill=BOTH, expand=True)

        # --- COLUMNA EQUIPO LOCAL ---
        col_local = tb.Frame(frm_top)
        col_local.pack(side=LEFT, fill=Y, expand=True, padx=10)
        if self.goles_local > 0:
            tb.Label(col_local, text=f"Goles de {self.local_name} (Total: {self.goles_local})", font="-weight bold").pack(anchor=W, pady=5)
            # Creamos tantas filas como goles máximos (por si marcan 3 jugadores distintos)
            for i in range(self.goles_local):
                frm_gol = tb.Frame(col_local)
                frm_gol.pack(fill=X, pady=2)
                cb = AutocompleteCombobox(frm_gol, values=self.jugadores_local, width=22)
                cb.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
                # Selector numérico de goles
                sp = tb.Spinbox(frm_gol, from_=0, to=self.goles_local, width=5)
                sp.set(0)  # Por defecto en 0 para obligar a asignarlos conscientemente
                sp.pack(side=RIGHT)
                self.filas_local.append((cb, sp))

        # --- COLUMNA EQUIPO VISITANTE ---
        col_visit = tb.Frame(frm_top)
        col_visit.pack(side=RIGHT, fill=Y, expand=True, padx=10)
        if self.goles_visitante > 0:
            tb.Label(col_visit, text=f"Goles de {self.visitante_name} (Total: {self.goles_visitante})", font="-weight bold").pack(anchor=W, pady=5)
            for i in range(self.goles_visitante):
                frm_gol = tb.Frame(col_visit)
                frm_gol.pack(fill=X, pady=2)
                cb = AutocompleteCombobox(frm_gol, values=self.jugadores_visit, width=22)
                cb.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
                # Selector numérico de goles
                sp = tb.Spinbox(frm_gol, from_=0, to=self.goles_visitante, width=5)
                sp.set(0)
                sp.pack(side=RIGHT)
                self.filas_visitante.append((cb, sp))

        frm_btn = tb.Frame(self, padding=10)
        frm_btn.pack(fill=X, side=BOTTOM)
        tb.Button(frm_btn, text="Guardar Goleadores", command=self._guardar, bootstyle=SUCCESS).pack(side=RIGHT)
        tb.Button(frm_btn, text="Cancelar", command=self.destroy, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)

    def _guardar(self):
        goles_asignados_local = 0
        goles_asignados_visitante = 0
        datos_a_guardar = []

        # 1. Validación Estricta Local
        for cb, sp in self.filas_local:
            jugador = cb.get().strip()
            try:
                cant = int(sp.get())
            except ValueError:
                cant = 0

            if jugador and cant > 0:
                goles_asignados_local += cant
                datos_a_guardar.append((self.partido_id, jugador, cant))

        if self.goles_local > 0 and goles_asignados_local != self.goles_local:
            messagebox.showerror("Error de Suma", f"En {self.local_name} has asignado {goles_asignados_local} goles, pero marcaron {self.goles_local}. La suma debe coincidir.", parent=self)
            return

        # 2. Validación Estricta Visitante
        for cb, sp in self.filas_visitante:
            jugador = cb.get().strip()
            try:
                cant = int(sp.get())
            except ValueError:
                cant = 0

            if jugador and cant > 0:
                goles_asignados_visitante += cant
                datos_a_guardar.append((self.partido_id, jugador, cant))

        if self.goles_visitante > 0 and goles_asignados_visitante != self.goles_visitante:
            messagebox.showerror("Error de Suma", f"En {self.visitante_name} has asignado {goles_asignados_visitante} goles, pero marcaron {self.goles_visitante}. La suma debe coincidir.", parent=self)
            return

        # 3. Guardado en Base de Datos
        self.db.limpiar_goleadores_de_partido(self.partido_id)
        for p_id, jugador, cant in datos_a_guardar:
            if jugador != "(Propia Puerta)":
                self.db.insertar_goleador(p_id, jugador, cant)

        self.destroy()


# ===================================================================
# ENTORNO GRÁFICO MAESTRO (TTKBOOTSTRAP PROFESIONAL)
# ===================================================================

