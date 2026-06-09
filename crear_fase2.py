"""
FASE II - Script de creación automática
Crea: design_system.py, ui_components_v2.py, charts.py
"""

# ════════════════════════════════════════════════════════════════════════════
# 1. DESIGN SYSTEM.PY
# ════════════════════════════════════════════════════════════════════════════

design_system_code = '''"""Design System - Paleta, tipografía, espaciado"""

class Colors:
    PRIMARY = "#1E3A8A"
    PRIMARY_LIGHT = "#3B82F6"
    PRIMARY_DARK = "#1E40AF"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    INFO = "#06B6D4"
    WHITE = "#FFFFFF"
    BLACK = "#000000"
    GRAY_50 = "#F9FAFB"
    GRAY_100 = "#F3F4F6"
    GRAY_200 = "#E5E7EB"
    GRAY_300 = "#D1D5DB"
    GRAY_400 = "#9CA3AF"
    GRAY_500 = "#6B7280"
    GRAY_600 = "#4B5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1F2937"
    GRAY_900 = "#111827"
    DARK_BG = "#0F172A"
    DARK_SURFACE = "#1E293B"
    DARK_TEXT = "#E2E8F0"

class Typography:
    FONT_FAMILY = "Segoe UI, Arial, sans-serif"
    H1_SIZE = 32
    H2_SIZE = 28
    H3_SIZE = 24
    H4_SIZE = 20
    BODY_SIZE = 14
    SMALL_SIZE = 12
    REGULAR = 400
    MEDIUM = 500
    BOLD = 700

class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48

class Border:
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12
    WIDTH_THIN = 1
    WIDTH_NORMAL = 2
    WIDTH_THICK = 4

class Shadows:
    NONE = "0 0 0 rgba(0,0,0,0)"
    SM = "0 1px 2px 0 rgba(0,0,0,0.05)"
    MD = "0 4px 6px -1px rgba(0,0,0,0.1)"
    LG = "0 10px 15px -3px rgba(0,0,0,0.1)"
    XL = "0 20px 25px -5px rgba(0,0,0,0.1)"

class Breakpoints:
    MOBILE = 480
    TABLET = 768
    DESKTOP = 1024
    WIDE = 1280

class Transitions:
    FAST = 150
    NORMAL = 300
    SLOW = 500
'''

# ════════════════════════════════════════════════════════════════════════════
# 2. UI_COMPONENTS_V2.PY
# ════════════════════════════════════════════════════════════════════════════

ui_components_v2_code = '''"""Componentes UI modernos"""

import tkinter as tk
import ttkbootstrap as tb
from design_system import Colors, Typography, Spacing

class Card(tb.Frame):
    def __init__(self, parent, title="", content="", icon="", **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=Colors.WHITE, relief="flat")
        
        if title:
            header = tb.Frame(self, padding=Spacing.MD)
            header.pack(fill="x")
            if icon:
                tb.Label(header, text=icon, font=("Arial", 16)).pack(side="left", padx=5)
            tb.Label(header, text=title, font=(Typography.FONT_FAMILY, Typography.H4_SIZE, "bold")).pack(side="left")
        
        if content:
            body = tb.Frame(self, padding=Spacing.MD)
            body.pack(fill="both", expand=True)
            tb.Label(body, text=content, wraplength=300).pack()

class Alert(tb.Frame):
    def __init__(self, parent, message, alert_type="info", **kwargs):
        super().__init__(parent, **kwargs)
        
        color_map = {
            "success": (Colors.SUCCESS, "[OK]"),
            "warning": (Colors.WARNING, "[!]"),
            "error": (Colors.DANGER, "[ERROR]"),
            "info": (Colors.INFO, "[*]")
        }
        
        color, icon = color_map.get(alert_type, color_map["info"])
        self.config(bg=color, height=2)
        
        frame = tb.Frame(self, padding=Spacing.MD)
        frame.pack(fill="x")
        tb.Label(frame, text=f"{icon} {message}", foreground="white").pack(side="left")

class StatWidget(tb.Frame):
    def __init__(self, parent, label="", value=0, color=Colors.PRIMARY, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=Colors.GRAY_50, relief="flat", padding=Spacing.LG)
        
        tb.Label(self, text=str(value), font=(Typography.FONT_FAMILY, 32, "bold"), 
                foreground=color).pack()
        tb.Label(self, text=label, font=(Typography.FONT_FAMILY, 12), 
                foreground=Colors.GRAY_600).pack()

class Badge(tb.Label):
    def __init__(self, parent, text="", color=Colors.PRIMARY, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self.config(
            background=color,
            foreground="white",
            font=(Typography.FONT_FAMILY, 11, "bold"),
            padding=(Spacing.SM, Spacing.XS)
        )
'''

# ════════════════════════════════════════════════════════════════════════════
# 3. CHARTS.PY
# ════════════════════════════════════════════════════════════════════════════

charts_code = '''"""Gráficos interactivos con matplotlib"""

import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

class ChartWidget(tk.Frame):
    def __init__(self, parent, chart_type="line", **kwargs):
        super().__init__(parent, **kwargs)
        self.chart_type = chart_type
        self.figure = None
        self.canvas = None
    
    def plot_evolution(self, equipos_data, title="Evolucion de Puntos"):
        self.figure = Figure(figsize=(10, 5), dpi=100)
        ax = self.figure.add_subplot(111)
        
        for eq_name, points in equipos_data.items():
            ax.plot(points, marker='o', label=eq_name, linewidth=2)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Jornada")
        ax.set_ylabel("Puntos")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self._render_canvas()
    
    def plot_bars(self, data, title="Goles por Equipo"):
        self.figure = Figure(figsize=(10, 5), dpi=100)
        ax = self.figure.add_subplot(111)
        
        equipos = list(data.keys())
        goles = list(data.values())
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(equipos)))
        
        ax.bar(equipos, goles, color=colors)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel("Goles")
        
        self._render_canvas()
    
    def _render_canvas(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()
'''

# ════════════════════════════════════════════════════════════════════════════
# CREAR ARCHIVOS
# ════════════════════════════════════════════════════════════════════════════

with open("src/design_system.py", "w") as f:
    f.write(design_system_code)

with open("src/ui_components_v2.py", "w") as f:
    f.write(ui_components_v2_code)

with open("src/charts.py", "w") as f:
    f.write(charts_code)

print("[OK] design_system.py creado")
print("[OK] ui_components_v2.py creado")
print("[OK] charts.py creado")
print("\nProximo paso:")
print("  pip install matplotlib")
print("  Luego integrar en app_maestra_futbol.py")
