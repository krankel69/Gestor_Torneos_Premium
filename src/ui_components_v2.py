"""Componentes UI modernos - Card, Alert, StatWidget, Badge"""

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
        color_map = {"success": Colors.SUCCESS, "warning": Colors.WARNING, "error": Colors.DANGER, "info": Colors.INFO}
        color = color_map.get(alert_type, Colors.INFO)
        self.config(bg=color)
        tb.Label(self, text=message, foreground="white").pack(pady=Spacing.SM, padx=Spacing.SM)


class StatWidget(tb.Frame):
    """Muestra metrica: numero grande + label."""

    def __init__(self, parent, label="", value=0, color=Colors.PRIMARY, **kwargs):
        super().__init__(parent, **kwargs)
        tb.Label(self, text=str(value), font=(Typography.FONT_FAMILY, 32, "bold"), foreground=color).pack()
        tb.Label(self, text=label, font=(Typography.FONT_FAMILY, 12), foreground=Colors.GRAY_600).pack()


class Badge(tb.Label):
    """Etiqueta pequena con color."""

    def __init__(self, parent, text="", color=Colors.PRIMARY, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self.config(background=color, foreground="white", font=(Typography.FONT_FAMILY, 11, "bold"))
