import csv
import os
import shutil
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

DESTINO = r"C:\Users\Admin\Documents\FUTBOL - copia\partidos"

def pedir_rango():
    while True:
        try:
            ini = int(input("Primera jornada a procesar (ej: 10): ").strip())
            fin = int(input("Última jornada a procesar (ej: 14): ").strip())
            if ini <= fin:
                return ini, fin
            print("❌ La jornada inicial debe ser menor o igual que la final.")
        except ValueError:
            print("❌ Debes introducir números válidos.")

def pedir_fecha(jornada):
    while True:
        fecha = input(f"Fecha para la jornada {jornada} (YYYY-MM-DD): ").strip()
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
        print(f"⚠️ Número impar de equipos ({len(equipos)}). Se ignorará el último equipo.")
        equipos = equipos[:-1]
    return [(equipos[i], equipos[i+1]) for i in range(0, len(equipos), 2)]

def confirmar_partidos(jornada, partidos):
    print(f"\nPartidos generados para la jornada {jornada}:")
    print("="*40)
    for local, visitante in partidos:
        print(f"{local} vs {visitante}")
    print("="*40)
    while True:
        resp = input("¿Deseas continuar con estos partidos? (S/N): ").strip().upper()
        if resp in ("S", "N"):
            return resp == "S"
        print("❌ Respuesta inválida. Escribe 'S' para sí o 'N' para no.")

def preguntar_sobrescribir(nombre_salida):
    if os.path.exists(nombre_salida):
        while True:
            resp = input(f"⚠️ El archivo '{nombre_salida}' ya existe. ¿Deseas sobrescribirlo? (S/N): ").strip().upper()
            if resp in ("S", "N"):
                return resp == "S"
            print("❌ Respuesta inválida. Escribe 'S' o 'N'.")
    return True

def procesar_jornada(jornada):
    archivo = f"j{jornada}.csv"
    if not os.path.exists(archivo):
        print(f"⚠️ No se encontró el archivo {archivo}, se salta esta jornada.")
        return

    fecha = pedir_fecha(jornada)
    equipos = leer_jornada_csv(archivo)
    partidos = generar_partidos(equipos)

    if not confirmar_partidos(jornada, partidos):
        print(f"⚠️ Jornada {jornada} cancelada por el usuario.")
        return

    nombre_salida = f"{jornada}.csv"

    if not preguntar_sobrescribir(nombre_salida):
        print(f"⚠️ Jornada {jornada} cancelada (no sobrescrita).")
        return

    with open(nombre_salida, "w", newline="", encoding="utf-8") as f_out:
        escritor = csv.writer(f_out)
        escritor.writerow(["Equipo Local", "Equipo Visitante", "Fecha"])
        for local, visitante in partidos:
            escritor.writerow([local, visitante, fecha])

    # Copiar al destino
    os.makedirs(DESTINO, exist_ok=True)
    shutil.copy2(nombre_salida, DESTINO)

    # Eliminar el archivo jX.csv original
    os.remove(archivo)

    print(f"✅ Jornada {jornada} procesada: '{nombre_salida}' creado y copiado a '{DESTINO}' (se eliminó '{archivo}')")

def procesar_rango():
    ini, fin = pedir_rango()
    for j in range(ini, fin + 1):
        procesar_jornada(j)

if __name__ == "__main__":
    print("=== Procesar VARIAS jornadas (de jX.csv a jY.csv) ===")
    procesar_rango()
    input("Presiona Enter para salir...")
