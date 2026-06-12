import csv
import os

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
    from datetime import datetime
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
                if celda:  # ignorar celdas vacías
                    equipos.append(renombrar_equipos.get(celda, celda))
    return equipos

def generar_partidos(equipos):
    if len(equipos) % 2 != 0:
        print("⚠️ Número impar de equipos. Se ignorará el último equipo.")
        equipos = equipos[:-1]
    partidos = []
    for i in range(0, len(equipos), 2):
        partidos.append((equipos[i], equipos[i+1]))
    return partidos

if __name__ == "__main__":
    jornada = input("Número de la jornada: ").strip()
    fecha = pedir_fecha()
    archivo_entrada = f"j{jornada}.csv"

    if not os.path.exists(archivo_entrada):
        print(f"⚠️ No se encontró el archivo {archivo_entrada}.")
        input("Presiona Enter para salir...")
        exit()

    equipos = leer_jornada_csv(archivo_entrada)
    partidos = generar_partidos(equipos)

    nombre_salida = f"{jornada}.csv"
    with open(nombre_salida, "w", newline="", encoding="utf-8") as f_out:
        escritor = csv.writer(f_out)
        escritor.writerow(["Equipo Local", "Equipo Visitante", "Fecha"])
        for local, visitante in partidos:
            escritor.writerow([local, visitante, fecha])

    # eliminar antiguo jX.csv
    if os.path.exists(archivo_entrada):
        os.remove(archivo_entrada)
        print(f"🗑️ Se ha eliminado el CSV antiguo: {archivo_entrada}")

    print(f"\n✅ CSV final de la jornada generado: {nombre_salida}")
    input("Presiona Enter para salir...")
