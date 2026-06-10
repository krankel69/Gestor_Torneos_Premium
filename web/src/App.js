import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [torneos, setTorneos] = useState([
    { id: 'liga', nombre: 'Liga', bd: 'liga_futbol_v2.db' },
    { id: 'mundial', nombre: 'Mundial 2026', bd: 'mundial_2026_v2.db' },
    { id: 'champions', nombre: 'Champions', bd: 'champions_gui_v2.db' },
    { id: 'euro', nombre: 'Eurocopa', bd: 'eurocopa_2024_v2.db' }
  ]);
  
  const [equipos, setEquipos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTorneo, setSelectedTorneo] = useState('liga');

  useEffect(() => {
    setLoading(true);
    const apiUrl = `http://${window.location.hostname}:8000/api/equipos?torneo=${selectedTorneo}`;
    fetch(apiUrl)
      .then(res => res.json())
      .then(data => {
        setEquipos(data);
        setLoading(false);
      })
      .catch(err => {
        console.log(err);
        setLoading(false);
      });
  }, [selectedTorneo]);

  return (
    <div className="App">
      <h1>⚽ Gestor Premium de Torneos - WEB</h1>
      
      <div style={{marginBottom: '20px'}}>
        <label>Selecciona torneo: </label>
        <select value={selectedTorneo} onChange={(e) => setSelectedTorneo(e.target.value)}>
          {torneos.map(t => (
            <option key={t.id} value={t.id}>{t.nombre}</option>
          ))}
        </select>
      </div>

      {loading && <p>Cargando...</p>}
      
      {equipos.length > 0 && (
        <table border="1" cellPadding="10">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Ciudad</th>
              <th>PJ</th>
              <th>Pts</th>
            </tr>
          </thead>
          <tbody>
            {equipos.map(eq => (
              <tr key={eq.id}>
                <td>{eq.id}</td>
                <td>{eq.nombre}</td>
                <td>{eq.ciudad}</td>
                <td>{eq.pj}</td>
                <td>{eq.pts}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;