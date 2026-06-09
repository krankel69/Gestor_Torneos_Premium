"""Graficos interactivos con Plotly (compatible Python 3.14)"""

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
