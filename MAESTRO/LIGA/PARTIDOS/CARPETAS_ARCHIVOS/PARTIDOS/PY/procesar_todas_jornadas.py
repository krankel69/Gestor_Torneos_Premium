import csv
import os
from datetime import datetime

# Diccionario de renombrado de equipos
renombrar_equipos = {
    "Deportivo Alavés": "ALAVES",
    "Elche CF": "ELCHE",
    "Athletic Club": "ATH.BILBAO",
    "RCD Mallorca": "MALLORCA",
    "Girona FC": "GIRONA",
    "Valencia CF": "VALENCIA",
    "Real Madrid": "REAL MADRID",
    "Villarreal CF": "VILLARREAL",
    "RC Celta": "CELTA",
    "Atlético de Madrid": "ATL.MADRID",
    "Sevilla FC": "SEVILLA",
    "FC Barcelona": "BARCELONA",
    "RCD Espanyol de Barcelona": "ESPANYOL",
    "Real Betis": "BETIS",
    "CA Osasuna": "OSASUNA",
    "Getafe CF": "GETAFE",
    "Real Oviedo": "OVIEDO",
    "Levante UD": "LEVANTE",
    "Real Sociedad": "REAL SOCIEDAD",
    "Rayo Vallecano": "RAYO VALLECANO"
}

def pedir_fecha():
    while True:
        fecha = input("Fecha de la jornada (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            return fecha
        except ValueError:
            print("❌ Formato incorrecto. Intenta de nuevo (ej: 2025-11-09).")

def leer_jornada_csv(archivo):
    equipos = []
    with open(archivo, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for fila in reader:
            for celda in fila:
                celda = celda.strip()
                if celda:
                    equipos.append(renombrar_equipos.get(celda, celda))
    return equipos

def generar_partidos(equipos):
    if len(equipos) % 2 != 0:
        print(f"⚠️ Número impar de equipos en {len(equipos)}. Se ignorará el último equipo.")
        equipos = equipos[:-1]
    partidos = []
    for i in range(0, len(equipos), 2):
        partidos.append((equipos[i], equipos[i+1]))
    return partidos

def procesar_jornadas(fecha):
    archivos = [f for f in os.listdir() if f.lower().startswith("j") and f.lower().endswith(".csv")]
    if not archivos:
        print("⚠️ No se encontraron archivos 'jX.csv' en la carpeta.")
        return

    for archivo in sorted(archivos):
        jornada_num = ''.join(filter(str.isdigit, archivo))
        if not jornada_num:
            continue

        equipos = leer_jornada_csv(archivo)
        partidos = generar_partidos(equipos)

        nombre_salida = f"{jornada_num}.csv"
        with open(nombre_salida, "w", newline="", encoding="utf-8") as f_out:
            escritor = csv.writer(f_out)
            escritor.writerow(["Equipo Local", "Equipo Visitante", "Fecha"])
            for local, visitante in partidos:
                escritor.writerow([local, visitante, fecha])

        os.remove(archivo)
        print(f"✅ Procesado {archivo} → {nombre_salida} y eliminado {archivo}")

if __name__ == "__main__":
    print("=== Procesar todas las jornadas 'jX.csv' ===")
    fecha = pedir_fecha()
    procesar_jornadas(fecha)
    print("\n🎉 Todas las jornadas procesadas.")
    input("Presiona Enter para salir...")
