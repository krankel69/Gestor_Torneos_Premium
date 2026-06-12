import { useEffect, useState } from 'react';

const API_BASE_URL = 'https://gestor-torneos-premium-2.onrender.com';

const COLORES = {
  primario: '#10B981',
  secundario: '#1F2937',
  gris: '#F3F4F6',
  grisOscuro: '#6B7280',
  blanco: '#FFFFFF',
  naranja: '#F97316',
  rojo: '#EF4444',
  verde: '#10B981',
  azul: '#3B82F6'
};

const estilos = {
  contenedor: {
    minHeight: '100vh',
    backgroundColor: COLORES.gris,
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    padding: '0',
    margin: '0'
  },
  header: {
    background: `linear-gradient(135deg, ${COLORES.primario} 0%, ${COLORES.azul} 100%)`,
    color: COLORES.blanco,
    padding: '20px',
    textAlign: 'center',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    position: 'sticky',
    top: 0,
    zIndex: 100
  },
  titulo: {
    margin: '0',
    fontSize: '28px',
    fontWeight: '700',
    letterSpacing: '-0.5px'
  },
  main: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px'
  },
  seccion: {
    marginBottom: '30px'
  },
  selectorTorneo: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '30px',
    padding: '15px',
    backgroundColor: COLORES.blanco,
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  label: {
    fontSize: '14px',
    fontWeight: '600',
    color: COLORES.secundario
  },
  select: {
    padding: '8px 12px',
    borderRadius: '8px',
    border: `2px solid ${COLORES.primario}`,
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    backgroundColor: COLORES.blanco,
    color: COLORES.secundario,
    transition: 'all 0.2s'
  },
  tarjeta: {
    backgroundColor: COLORES.blanco,
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    marginBottom: '20px'
  },
  subtitulo: {
    fontSize: '20px',
    fontWeight: '700',
    color: COLORES.secundario,
    marginBottom: '15px',
    marginTop: '0'
  },
  formulario: {
    display: 'flex',
    gap: '10px',
    flexWrap: 'wrap',
    alignItems: 'center'
  },
  input: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: `2px solid #E5E7EB`,
    fontSize: '14px',
    fontFamily: 'inherit',
    transition: 'all 0.2s',
    flex: '1',
    minWidth: '150px'
  },
  inputFocus: {
    outline: 'none',
    borderColor: COLORES.primario,
    boxShadow: `0 0 0 3px ${COLORES.primario}20`
  },
  boton: {
    padding: '10px 20px',
    borderRadius: '8px',
    border: 'none',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '6px'
  },
  botonPrimario: {
    backgroundColor: COLORES.primario,
    color: COLORES.blanco
  },
  botonDanger: {
    backgroundColor: COLORES.rojo,
    color: COLORES.blanco,
    padding: '6px 12px',
    fontSize: '12px'
  },
  tabla: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px'
  },
  tableHeader: {
    backgroundColor: COLORES.secundario,
    color: COLORES.blanco,
    padding: '12px',
    textAlign: 'left',
    fontWeight: '600',
    fontSize: '13px'
  },
  tableRow: {
    borderBottom: `1px solid #E5E7EB`
  },
  tableRowAlternate: {
    backgroundColor: '#F9FAFB'
  },
  tableCell: {
    padding: '12px',
    textAlign: 'left'
  },
  tableCellNumero: {
    textAlign: 'center',
    fontWeight: '500'
  },
  mensajeError: {
    backgroundColor: '#FEE2E2',
    color: '#991B1B',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '20px',
    border: `1px solid #FECACA`,
    fontSize: '14px'
  },
  mensajeVacio: {
    textAlign: 'center',
    color: COLORES.grisOscuro,
    padding: '40px 20px',
    fontSize: '14px'
  },
  cargando: {
    textAlign: 'center',
    color: COLORES.grisOscuro,
    padding: '20px'
  },
  pie: {
    textAlign: 'center',
    fontSize: '12px',
    color: COLORES.grisOscuro,
    padding: '20px',
    marginTop: '40px',
    borderTop: `1px solid #E5E7EB`
  }
};

export default function App() {
  const [equipos, setEquipos] = useState([]);
  const [partidos, setPartidos] = useState([]);
  const [selectedTorneo, setSelectedTorneo] = useState('liga');
  const [nuevoNombre, setNuevoNombre] = useState('');
  const [nuevaCiudad, setNuevaCiudad] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingEquipos, setLoadingEquipos] = useState(true);
  const [error, setError] = useState('');

  const torneos = [
    { value: 'liga', label: '🏆 Liga' },
    { value: 'mundial', label: '🌍 Mundial 2026' },
    { value: 'champions', label: '👑 Champions' },
    { value: 'euro', label: '🇪🇺 Eurocopa' }
  ];

  useEffect(() => {
    cargarEquipos();
    
    // Polling: Actualizar equipos cada 5 segundos
    const intervalo = setInterval(() => {
      cargarEquipos();
    }, 5000);
    
    return () => clearInterval(intervalo);
  }, [selectedTorneo]);

  useEffect(() => {
    cargarPartidos();
    
    const intervalo = setInterval(() => {
      cargarPartidos();
    }, 5000);
    
    return () => clearInterval(intervalo);
  }, [selectedTorneo]);

  const cargarEquipos = async () => {
    setLoadingEquipos(true);
    setError('');
    try {
      const params = new URLSearchParams({ torneo: selectedTorneo });
      const response = await fetch(`${API_BASE_URL}/api/equipos?${params}`);
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setEquipos(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error cargando equipos:', err);
      setError(`Error al cargar equipos: ${err.message}`);
      setEquipos([]);
    } finally {
      setLoadingEquipos(false);
    }
  };

  const cargarPartidos = async () => {
    try {
      const response = await fetch(`/data/partidos_${selectedTorneo}.json`);
      if (response.ok) {
        const data = await response.json();
        setPartidos(Array.isArray(data) ? data : []);
      } else {
        setPartidos([]);
      }
    } catch (error) {
      console.log('Partidos no disponibles');
      setPartidos([]);
    }
  };

  const agregarEquipo = async (e) => {
    e.preventDefault();
    
    if (!nuevoNombre.trim()) {
      setError('Por favor ingresa un nombre de equipo');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/equipos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nombre: nuevoNombre.trim(),
          ciudad: nuevaCiudad.trim(),
          grupo: selectedTorneo
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Error ${response.status}`);
      }

      const result = await response.json();
      
      setNuevoNombre('');
      setNuevaCiudad('');
      await cargarEquipos();
      setError('');
      alert(`✅ ${result.message}`);
    } catch (err) {
      console.error('Error agregando equipo:', err);
      setError(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const eliminarEquipo = async (equipoId, equipoNombre) => {
    if (!window.confirm(`¿Estás seguro de que quieres eliminar a ${equipoNombre}?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/equipos/${equipoId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Error ${response.status}`);
      }

      const result = await response.json();
      await cargarEquipos();
      alert(`✅ ${result.message}`);
    } catch (err) {
      console.error('Error eliminando equipo:', err);
      setError(`❌ Error al eliminar: ${err.message}`);
    }
  };

  return (
    <div style={estilos.contenedor}>
      <header style={estilos.header}>
        <h1 style={estilos.titulo}>⚽ Gestor Premium de Torneos</h1>
        <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>Gestiona tus equipos desde cualquier lugar</p>
      </header>

      <main style={estilos.main}>
        {/* Selector de Torneo */}
        <div style={estilos.selectorTorneo}>
          <label style={estilos.label}>Torneo:</label>
          <select 
            value={selectedTorneo}
            onChange={(e) => setSelectedTorneo(e.target.value)}
            style={estilos.select}
          >
            {torneos.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* Mensaje de Error */}
        {error && <div style={estilos.mensajeError}>{error}</div>}

        {/* Formulario Agregar Equipo */}
        <div style={estilos.tarjeta}>
          <h2 style={estilos.subtitulo}>➕ Agregar Equipo</h2>
          <form onSubmit={agregarEquipo} style={estilos.formulario}>
            <input 
              type="text" 
              placeholder="Nombre del equipo" 
              value={nuevoNombre}
              onChange={(e) => setNuevoNombre(e.target.value)}
              style={estilos.input}
              disabled={loading}
            />
            <input 
              type="text" 
              placeholder="Ciudad" 
              value={nuevaCiudad}
              onChange={(e) => setNuevaCiudad(e.target.value)}
              style={estilos.input}
              disabled={loading}
            />
            <button 
              type="submit" 
              disabled={loading || !nuevoNombre.trim()}
              style={{
                ...estilos.boton,
                ...estilos.botonPrimario,
                opacity: (loading || !nuevoNombre.trim()) ? 0.6 : 1,
                cursor: (loading || !nuevoNombre.trim()) ? 'not-allowed' : 'pointer'
              }}
              onMouseOver={(e) => {
                if (!loading && nuevoNombre.trim()) {
                  e.target.style.backgroundColor = '#059669';
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 4px 6px rgba(16,185,129,0.3)';
                }
              }}
              onMouseOut={(e) => {
                e.target.style.backgroundColor = COLORES.primario;
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              {loading ? '⏳ Agregando...' : '➕ Agregar'}
            </button>
          </form>
        </div>

        {/* Lista de Equipos */}
        <div style={estilos.tarjeta}>
          <h2 style={estilos.subtitulo}>🏆 Equipos ({selectedTorneo})</h2>
          
          {loadingEquipos ? (
            <div style={estilos.cargando}>⏳ Cargando equipos...</div>
          ) : equipos.length === 0 ? (
            <div style={estilos.mensajeVacio}>
              📭 No hay equipos registrados. ¡Agrega el primero!
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={estilos.tabla}>
                <thead>
                  <tr style={{ backgroundColor: COLORES.secundario }}>
                    <th style={estilos.tableHeader}>ID</th>
                    <th style={estilos.tableHeader}>Nombre</th>
                    <th style={estilos.tableHeader}>Ciudad</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>PJ</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>PG</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>PE</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>PP</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>GF</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>GC</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>PTS</th>
                    <th style={estilos.tableHeader}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {equipos.map((eq, idx) => (
                    <tr 
                      key={eq.id} 
                      style={{
                        ...estilos.tableRow,
                        ...(idx % 2 === 1 ? estilos.tableRowAlternate : {})
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.backgroundColor = '#F0FDF4';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.backgroundColor = idx % 2 === 1 ? '#F9FAFB' : 'transparent';
                      }}
                    >
                      <td style={estilos.tableCell}>{eq.id}</td>
                      <td style={{...estilos.tableCell, fontWeight: '600', color: COLORES.primario}}>{eq.nombre}</td>
                      <td style={estilos.tableCell}>{eq.ciudad || '-'}</td>
                      <td style={{...estilos.tableCell, ...estilos.tableCellNumero}}>{eq.pj || 0}</td>
                      <td style={{...estilos.tableCell, ...estilos.tableCellNumero, color: COLORES.verde}}>{eq.pg || 0}</td>
                      <td style={{...estilos.tableCell, ...estilos.tableCellNumero}}>{eq.pe || 0}</td>
                      <td style={{...estilos.tableCell, ...estilos.tableCellNumero}}>{eq.pp || 0}</td>
                      <td style={{...estilos.tableCell, ...estilos.tableCellNumero, color: COLORES.verde}}>{eq.gf || 0}</td>
                      <td style={{...estilos.tableCell, ...estilos.tableCellNumero, color: COLORES.rojo}}>{eq.gc || 0}</td>
                      <td style={{...estilos.tableCell, ...estilos.tableCellNumero, fontWeight: '700'}}>{eq.pts || 0}</td>
                      <td style={estilos.tableCell}>
                        <button
                          onClick={() => eliminarEquipo(eq.id, eq.nombre)}
                          style={estilos.botonDanger}
                          onMouseOver={(e) => {
                            e.target.style.backgroundColor = '#DC2626';
                            e.target.style.transform = 'scale(1.05)';
                          }}
                          onMouseOut={(e) => {
                            e.target.style.backgroundColor = COLORES.rojo;
                            e.target.style.transform = 'scale(1)';
                          }}
                        >
                          🗑️ Eliminar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        {/* Lista de Partidos */}
        <div style={estilos.tarjeta}>
          <h2 style={estilos.subtitulo}>⚽ Partidos ({selectedTorneo})</h2>
          
          {!partidos || partidos.length === 0 ? (
            <div style={estilos.mensajeVacio}>
              📭 No hay partidos registrados.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={estilos.tabla}>
                <thead>
                  <tr style={{ backgroundColor: COLORES.secundario }}>
                    <th style={estilos.tableHeader}>Fecha</th>
                    <th style={estilos.tableHeader}>Local</th>
                    <th style={estilos.tableHeader}>Visitante</th>
                    <th style={{...estilos.tableHeader, textAlign: 'center'}}>Resultado</th>
                  </tr>
                </thead>
                <tbody>
                  {partidos.map((p, idx) => (
                    <tr key={idx} style={{...estilos.tableRow, ...(idx % 2 === 1 ? estilos.tableRowAlternate : {})}}>
                      <td style={estilos.tableCell}>{new Date(p.fecha).toLocaleDateString()}</td>
                      <td style={estilos.tableCell}>{p.equipo_local_id || p.local || '-'}</td>
                      <td style={estilos.tableCell}>{p.equipo_visitante_id || p.visitante || '-'}</td>
                      <td style={{...estilos.tableCell, textAlign: 'center', fontWeight: '600'}}>
                        {p.goles_local !== -1 ? `${p.goles_local}–${p.goles_visitante}` : '–'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <footer style={estilos.pie}>
          <p>🚀 <strong>Gestor Premium de Torneos</strong> v2.0 | Diseñado para móvil y desktop</p>
          <p>🔗 API: {API_BASE_URL} | Última actualización: {new Date().toLocaleTimeString()}</p>
        </footer>
      </main>
    </div>
  );
}
