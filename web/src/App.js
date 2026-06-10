import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [equipos, setEquipos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/equipos')
      .then(res => res.json())
      .then(data => {
        setEquipos(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="App">
      <h1>⚽ Gestor Premium de Torneos - WEB</h1>
      
      {loading && <p>Cargando...</p>}
      {error && <p style={{color: 'red'}}>Error: {error}</p>}
      
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