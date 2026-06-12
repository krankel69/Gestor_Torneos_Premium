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

def pedir_jornada():
    while True:
        j = input("Número de jornada a procesar (ej: 14 para j14.csv): ").strip()
        if j.isdigit():
            archivo = f"j{j}.csv"
            if os.path.exists(archivo):
                return j, archivo
            else:
                print(f"⚠️ No se encontró el archivo '{archivo}' en la carpeta.")
        else:
            print("❌ Debes introducir un número válido.")

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
    partidos = []
    for i in range(0, len(equipos), 2):
        partidos.append((equipos[i], equipos[i+1]))
    return partidos

def confirmar_partidos(partidos):
    print("\nPartidos generados para esta jornada:")
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

def procesar_jornada():
    jornada_num, archivo = pedir_jornada()
    fecha = pedir_fecha(jornada_num)
    equipos = leer_jornada_csv(archivo)
    partidos = generar_partidos(equipos)

    if not confirmar_partidos(partidos):
        print("⚠️ Operación cancelada por el usuario.")
        return

    nombre_salida = f"{jornada_num}.csv"

    if not preguntar_sobrescribir(nombre_salida):
        print("⚠️ Operación cancelada por el usuario.")
        return

    with open(nombre_salida, "w", newline="", encoding="utf-8") as f_out:
        escritor = csv.writer(f_out)
        escritor.writerow(["Equipo Local", "Equipo Visitante", "Fecha"])
        for local, visitante in partidos:
            escritor.writerow([local, visitante, fecha])

    os.remove(archivo)
    print(f"✅ Procesada jornada {jornada_num}: '{archivo}' → '{nombre_salida}' y eliminado '{archivo}'")

if __name__ == "__main__":
    print("=== Procesar UNA jornada jX.csv con fecha individual ===")
    procesar_jornada()
    input("Presiona Enter para salir...")
