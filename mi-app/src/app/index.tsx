import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator } from 'react-native';

export default function App() {
  const [equipos, setEquipos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/equipos')
      .then(res => res.json())
      .then(data => { setEquipos(data); setLoading(false); })
      .catch(err => setLoading(false));
  }, []);

  if (loading) return <View style={styles.center}><ActivityIndicator /></View>;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>⚽ Torneos</Text>
      <FlatList data={equipos} renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.nombre}>{item.nombre}</Text>
          <Text>{item.ciudad} - {item.pts} pts</Text>
        </View>
      )} keyExtractor={item => item.id.toString()} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 50, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center' },
  title: { fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 },
  card: { backgroundColor: '#fff', margin: 10, padding: 15, borderRadius: 8 },
  nombre: { fontSize: 18, fontWeight: 'bold' },
});
