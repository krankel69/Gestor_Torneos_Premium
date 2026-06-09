# ui_components.py - Componentes gráficos reutilizables
# Versión: 1.1 | Fusión: Autocompletado + VentanaGoleadores + Diálogos nuevos
# Requiere: tkinter, ttkbootstrap

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox


# ════════════════════════════════════════════════════════════════════════════════
# AUTOCOMPLETE COMBOBOX
# ════════════════════════════════════════════════════════════════════════════════

class AutocompleteCombobox(tb.Combobox):
    """Combobox con autocompletado mientras escribes."""
    
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


# ════════════════════════════════════════════════════════════════════════════════
# VENTANA GOLEADORES - Versión mejorada
# ════════════════════════════════════════════════════════════════════════════════

class VentanaGoleadores(tb.Toplevel):
    """Ventana para asignar goleadores con validación estricta de suma."""
    
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
            # Creamos tantas filas como goles máximos
            for i in range(self.goles_local):
                frm_gol = tb.Frame(col_local)
                frm_gol.pack(fill=X, pady=2)
                cb = AutocompleteCombobox(frm_gol, values=self.jugadores_local, width=22)
                cb.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
                # Selector numérico de goles
                sp = tb.Spinbox(frm_gol, from_=0, to=self.goles_local, width=5)
                sp.set(0)
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
        tb.Button(frm_btn, text="✅ Guardar Goleadores", command=self._guardar, bootstyle=SUCCESS).pack(side=RIGHT)
        tb.Button(frm_btn, text="❌ Cancelar", command=self.destroy, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)

    def _guardar(self):
        """Guarda goleadores con validación estricta."""
        goles_asignados_local = 0
        goles_asignados_visitante = 0
        datos_a_guardar = []

        # 1. Validación Local
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
            messagebox.showerror("Error de Suma", 
                f"En {self.local_name} has asignado {goles_asignados_local} goles, pero marcaron {self.goles_local}.\nLa suma debe coincidir.", 
                parent=self)
            return

        # 2. Validación Visitante
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
            messagebox.showerror("Error de Suma", 
                f"En {self.visitante_name} has asignado {goles_asignados_visitante} goles, pero marcaron {self.goles_visitante}.\nLa suma debe coincidir.", 
                parent=self)
            return

        # 3. Guardar en BD
        self.db.limpiar_goleadores_de_partido(self.partido_id)
        for p_id, jugador, cant in datos_a_guardar:
            if jugador != "(Propia Puerta)":
                self.db.insertar_goleador(p_id, jugador, cant)

        messagebox.showinfo("Éxito", "Goleadores guardados correctamente.", parent=self)
        self.destroy()


# ════════════════════════════════════════════════════════════════════════════════
# DIÁLOGO CREAR NUEVO TORNEO
# ════════════════════════════════════════════════════════════════════════════════

class DialogoCrearTorneo(tk.Toplevel):
    """Diálogo para crear un nuevo torneo."""
    
    def __init__(self, parent, on_crear=None):
        super().__init__(parent)
        self.title("Crear Nuevo Torneo")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.on_crear = on_crear
        self.resultado = None
        
        frm = tb.Frame(self, padding=20)
        frm.pack(fill=BOTH, expand=True)
        
        # Nombre
        tb.Label(frm, text="Nombre del Torneo:", font="-size 11").pack(anchor=W, pady=(10,5))
        self.entry_nombre = tb.Entry(frm, width=40)
        self.entry_nombre.pack(fill=X, pady=(0,15))
        self.entry_nombre.focus()
        
        # Tipo
        tb.Label(frm, text="Tipo de Torneo:", font="-size 11").pack(anchor=W, pady=(10,5))
        self.var_tipo = tk.StringVar(value="liga")
        
        for tipo_val, tipo_txt in [("liga", "Liga"), ("copa", "Copa"), 
                                     ("mundial", "Mundial"), ("euro", "Eurocopa")]:
            tb.Radiobutton(frm, text=tipo_txt, variable=self.var_tipo, 
                          value=tipo_val).pack(anchor=W, pady=3)
        
        # Botones
        frm_botones = tb.Frame(frm)
        frm_botones.pack(fill=X, pady=(20,0))
        
        tb.Button(frm_botones, text="✅ Crear", bootstyle="success",
                  command=self._crear).pack(side=LEFT, padx=5)
        tb.Button(frm_botones, text="❌ Cancelar", bootstyle="danger-outline",
                  command=self.destroy).pack(side=LEFT, padx=5)
    
    def _crear(self):
        """Valida y crea el torneo."""
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Aviso", "Ingresa un nombre para el torneo")
            return
        
        self.resultado = {
            "nombre": nombre,
            "tipo": self.var_tipo.get()
        }
        
        if self.on_crear:
            self.on_crear(self.resultado)
        self.destroy()


# ════════════════════════════════════════════════════════════════════════════════
# DIÁLOGO EDITOR DE RESULTADO
# ════════════════════════════════════════════════════════════════════════════════

class DialogoEditarResultado(tk.Toplevel):
    """Diálogo para editar resultado de un partido."""
    
    def __init__(self, parent, fecha="", goles_local=0, goles_visitante=0, on_guardar=None):
        super().__init__(parent)
        self.title("Editar Resultado")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.on_guardar = on_guardar
        
        frm = tb.Frame(self, padding=20)
        frm.pack(fill=BOTH, expand=True)
        
        # Fecha
        tb.Label(frm, text="Fecha (YYYY-MM-DD):", font="-size 10").pack(anchor=W, pady=(10,5))
        self.entry_fecha = tb.Entry(frm)
        self.entry_fecha.insert(0, fecha)
        self.entry_fecha.pack(fill=X, pady=(0,15))
        
        # Goles
        frm_goles = tb.Frame(frm)
        frm_goles.pack(fill=X, pady=15)
        
        tb.Label(frm_goles, text="Goles Local:").pack(side=LEFT, padx=5)
        self.spin_local = tb.Spinbox(frm_goles, from_=0, to=10, width=5)
        self.spin_local.set(goles_local)
        self.spin_local.pack(side=LEFT, padx=5)
        
        tb.Label(frm_goles, text="Goles Visitante:").pack(side=LEFT, padx=5)
        self.spin_visitante = tb.Spinbox(frm_goles, from_=0, to=10, width=5)
        self.spin_visitante.set(goles_visitante)
        self.spin_visitante.pack(side=LEFT, padx=5)
        
        # Botones
        frm_botones = tb.Frame(frm)
        frm_botones.pack(fill=X, pady=(20,0))
        
        tb.Button(frm_botones, text="💾 Guardar", bootstyle="success",
                  command=self._guardar).pack(side=LEFT, padx=5)
        tb.Button(frm_botones, text="❌ Cancelar", bootstyle="danger-outline",
                  command=self.destroy).pack(side=LEFT, padx=5)
    
    def _guardar(self):
        """Guarda los cambios."""
        try:
            goles_local = int(self.spin_local.get())
            goles_visitante = int(self.spin_visitante.get())
        except:
            messagebox.showerror("Error", "Goles deben ser números")
            return
        
        resultado = {
            "fecha": self.entry_fecha.get().strip(),
            "goles_local": goles_local,
            "goles_visitante": goles_visitante
        }
        
        if self.on_guardar:
            self.on_guardar(resultado)
        self.destroy()


# ════════════════════════════════════════════════════════════════════════════════
