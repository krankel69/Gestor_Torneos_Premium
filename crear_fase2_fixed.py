"""
FASE II - Crear archivos (version corregida para Windows)
"""

from pathlib import Path

# Crear carpeta si no existe
Path("src").mkdir(exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# 1. design_system.py
# ════════════════════════════════════════════════════════════════════════════

design_system_code = '''"""Design System - Paleta, tipografia, espaciado"""

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

class Typography:
    FONT_FAMILY = "Segoe UI, Arial, sans-serif"
    H1_SIZE = 32
    H2_SIZE = 28
    H3_SIZE = 24
    H4_SIZE = 20
    BODY_SIZE = 14
    SMALL_SIZE = 12

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
'''

# ════════════════════════════════════════════════════════════════════════════
# 2. ui_components_v2.py
# ════════════════════════════════════════════════════════════════════════════

ui_components_v2_code = '''"""Componentes UI modernos - Card, Alert, StatWidget, Badge"""

import tkinter as tk
import ttkbootstrap as tb
from design_system import Colors, Spacing, Typography

class Card(tb.Frame):
    """Componente tarjeta moderna."""
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, **kwargs)
        if title:
            tb.Label(self, text=title, font=(Typography.FONT_FAMILY, 14, "bold")).pack(pady=Spacing.MD)

class Alert(tb.Frame):
    """Componente alerta (success, warning, error, info)."""
    def __init__(self, parent, message, alert_type="info", **kwargs):
        super().__init__(parent, **kwargs)
        color_map = {
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "error": Colors.DANGER,
            "info": Colors.INFO
        }
        color = color_map.get(alert_type, Colors.INFO)
        self.config(bg=color)
        tb.Label(self, text=message, foreground="white").pack(pady=Spacing.SM, padx=Spacing.SM)

class StatWidget(tb.Frame):
    """Muestra metrica: numero grande + label."""
    def __init__(self, parent, label="", value=0, color=Colors.PRIMARY, **kwargs):
        super().__init__(parent, **kwargs)
        tb.Label(self, text=str(value), font=(Typography.FONT_FAMILY, 32, "bold"), 
                foreground=color).pack()
        tb.Label(self, text=label, font=(Typography.FONT_FAMILY, 12), 
                foreground=Colors.GRAY_600).pack()

class Badge(tb.Label):
    """Etiqueta pequena con color."""
    def __init__(self, parent, text="", color=Colors.PRIMARY, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self.config(background=color, foreground="white", font=(Typography.FONT_FAMILY, 11, "bold"))
'''

# ════════════════════════════════════════════════════════════════════════════
# 3. charts.py (CON PLOTLY - compatible Python 3.14)
# ════════════════════════════════════════════════════════════════════════════

charts_code = '''"""Graficos interactivos con Plotly (compatible Python 3.14)"""

import plotly.graph_objects as go

class ChartWidget:
    """Widget para graficos con Plotly."""
    
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
    
    def plot_evolution(self, equipos_data, title="Evolucion de Puntos"):
        """Grafico de lineas: evolucion de puntos."""
        fig = go.Figure()
        
        for eq_name, points in equipos_data.items():
            fig.add_trace(go.Scatter(
                y=points,
                mode='lines+markers',
                name=eq_name,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Jornada",
            yaxis_title="Puntos",
            hovermode='x unified',
            template="plotly_white",
            height=500
        )
        
        fig.show()
    
    def plot_bars(self, data, title="Goles por Equipo"):
        """Grafico de barras."""
        equipos = list(data.keys())
        goles = list(data.values())
        
        fig = go.Figure(data=[
            go.Bar(x=equipos, y=goles, marker_color='#1E3A8A')
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="Equipo",
            yaxis_title="Goles",
            template="plotly_white",
            height=500
        )
        
        fig.show()
    
    def plot_top_scorers(self, scorers_dict, title="Top Goleadores"):
        """Grafico de goleadores."""
        jugadores = list(scorers_dict.keys())
        goles = list(scorers_dict.values())
        
        fig = go.Figure(data=[
            go.Bar(y=jugadores, x=goles, orientation='h', marker_color='#10B981')
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="Goles",
            template="plotly_white",
            height=400
        )
        
        fig.show()
'''

# ════════════════════════════════════════════════════════════════════════════
# CREAR ARCHIVOS
# ════════════════════════════════════════════════════════════════════════════

try:
    with open("src/design_system.py", "w", encoding="utf-8") as f:
        f.write(design_system_code)
    print("[OK] src/design_system.py creado")
except Exception as e:
    print(f"[ERROR] design_system.py: {e}")

try:
    with open("src/ui_components_v2.py", "w", encoding="utf-8") as f:
        f.write(ui_components_v2_code)
    print("[OK] src/ui_components_v2.py creado")
except Exception as e:
    print(f"[ERROR] ui_components_v2.py: {e}")

try:
    with open("src/charts.py", "w", encoding="utf-8") as f:
        f.write(charts_code)
    print("[OK] src/charts.py creado (con Plotly)")
except Exception as e:
    print(f"[ERROR] charts.py: {e}")

print("\nProximo paso:")
print("  pip install plotly")
print("  python -m pip install --upgrade plotly")
