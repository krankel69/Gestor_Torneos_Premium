import { useEffect, useState } from 'react';
import { db } from './firebase';
import { collection, onSnapshot, addDoc } from 'firebase/firestore';

export default function App() {
  const [equipos, setEquipos] = useState([]);
  const [selectedTorneo, setSelectedTorneo] = useState('liga');
  const [nuevoNombre, setNuevoNombre] = useState('');
  const [nuevaCiudad, setNuevaCiudad] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'equipos'), (snapshot) => {
      const data = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setEquipos(data);
    });
    return unsubscribe;
  }, []);

  const agregarEquipo = async (e) => {
    e.preventDefault();
    if (!nuevoNombre.trim()) return alert('Nombre requerido');
    
    setLoading(true);
    try {
      await addDoc(collection(db, 'equipos'), {
        nombre: nuevoNombre,
        ciudad: nuevaCiudad
      });
      setNuevoNombre('');
      setNuevaCiudad('');
      alert('Equipo agregado!');
    } catch (error) {
      alert('Error: ' + error.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>⚽ Gestor Premium de Torneos - WEB</h1>
      
      <p>Selecciona torneo: 
        <select value={selectedTorneo} onChange={(e) => setSelectedTorneo(e.target.value)}>
          <option>Liga</option>
          <option>Mondial 2026</option>
          <option>Champions</option>
          <option>Eurocopa</option>
        </select>
      </p>

      <h2>Agregar Equipo</h2>
      <form onSubmit={agregarEquipo}>
        <input 
          type="text" 
          placeholder="Nombre del equipo" 
          value={nuevoNombre}
          onChange={(e) => setNuevoNombre(e.target.value)}
        />
        <input 
          type="text" 
          placeholder="Ciudad" 
          value={nuevaCiudad}
          onChange={(e) => setNuevaCiudad(e.target.value)}
        />
        <button type="submit" disabled={loading}>{loading ? 'Agregando...' : 'Agregar'}</button>
      </form>

      <h2>Equipos</h2>
      <table border="1" style={{ width: '100%', marginTop: '20px' }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Ciudad</th>
          </tr>
        </thead>
        <tbody>
          {equipos.map((eq) => (
            <tr key={eq.id}>
              <td>{eq.id}</td>
              <td>{eq.nombre}</td>
              <td>{eq.ciudad}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}