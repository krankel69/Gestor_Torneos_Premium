import { useEffect, useState } from 'react';

const API_BASE_URL = 'https://gestor-torneos-premium-2.onrender.com';

export default function App() {
  const [equipos, setEquipos] = useState([]);
  const [selectedTorneo, setSelectedTorneo] = useState('liga');
  const [nuevoNombre, setNuevoNombre] = useState('');
  const [nuevaCiudad, setNuevaCiudad] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingEquipos, setLoadingEquipos] = useState(true);
  const [error, setError] = useState('');

  // Cargar equipos al montar el componente
  useEffect(() => {
    cargarEquipos();
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
      
      // Limpiar campos
      setNuevoNombre('');
      setNuevaCiudad('');
      
      // Recargar equipos
      await cargarEquipos();
      
      setError(''); // Limpiar errores
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
      
      // Recargar equipos
      await cargarEquipos();
      alert(`✅ ${result.message}`);
    } catch (err) {
      console.error('Error eliminando equipo:', err);
      setError(`❌ Error al eliminar: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>⚽ Gestor Premium de Torneos - WEB</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="torneo">Selecciona torneo: </label>
        <select 
          id="torneo"
          value={selectedTorneo} 
          onChange={(e) => setSelectedTorneo(e.target.value)}
          style={{ padding: '8px', fontSize: '14px' }}
        >
          <option value="liga">Liga</option>
          <option value="mundial">Mondial 2026</option>
          <option value="champions">Champions</option>
          <option value="euro">Eurocopa</option>
        </select>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: '#fee', 
          color: '#c33', 
          padding: '10px', 
          marginBottom: '20px', 
          borderRadius: '4px',
          border: '1px solid #fcc'
        }}>
          {error}
        </div>
      )}

      <h2>Agregar Equipo</h2>
      <form onSubmit={agregarEquipo} style={{ marginBottom: '30px' }}>
        <input 
          type="text" 
          placeholder="Nombre del equipo" 
          value={nuevoNombre}
          onChange={(e) => setNuevoNombre(e.target.value)}
          style={{ padding: '8px', marginRight: '10px', width: '200px' }}
          disabled={loading}
        />
        <input 
          type="text" 
          placeholder="Ciudad" 
          value={nuevaCiudad}
          onChange={(e) => setNuevaCiudad(e.target.value)}
          style={{ padding: '8px', marginRight: '10px', width: '150px' }}
          disabled={loading}
        />
        <button 
          type="submit" 
          disabled={loading || !nuevoNombre.trim()}
          style={{
            padding: '8px 16px',
            cursor: loading ? 'not-allowed' : 'pointer',
            backgroundColor: loading ? '#ccc' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '14px'
          }}
        >
          {loading ? '⏳ Agregando...' : '➕ Agregar'}
        </button>
      </form>

      <h2>Equipos ({selectedTorneo})</h2>
      {loadingEquipos ? (
        <p>⏳ Cargando equipos...</p>
      ) : equipos.length === 0 ? (
        <p style={{ color: '#666' }}>No hay equipos registrados</p>
      ) : (
        <table border="1" style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
          marginTop: '20px'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>ID</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Nombre</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Ciudad</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>PJ</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>PG</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>PE</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>PP</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>GF</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>GC</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>PTS</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {equipos.map((eq) => (
              <tr key={eq.id} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={{ padding: '12px' }}>{eq.id}</td>
                <td style={{ padding: '12px', fontWeight: 'bold' }}>{eq.nombre}</td>
                <td style={{ padding: '12px' }}>{eq.ciudad || '-'}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>{eq.pj || 0}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>{eq.pg || 0}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>{eq.pe || 0}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>{eq.pp || 0}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>{eq.gf || 0}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>{eq.gc || 0}</td>
                <td style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold' }}>{eq.pts || 0}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <button
                    onClick={() => eliminarEquipo(eq.id, eq.nombre)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#f44336',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    ❌ Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '4px', fontSize: '12px', color: '#666' }}>
        <p>🔗 API: {API_BASE_URL}</p>
        <p>📱 Ultima actualización: {new Date().toLocaleTimeString()}</p>
      </div>
    </div>
  );
}
