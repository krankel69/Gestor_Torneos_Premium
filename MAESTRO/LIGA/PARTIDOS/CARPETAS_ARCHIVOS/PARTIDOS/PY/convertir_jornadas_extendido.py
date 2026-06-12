import os
import csv
import shutil

# Diccionario de mapeo de nombres
MAPEO_EQUIPOS = {
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

def procesar_jornada(num_jornada, carpeta_destino):
    archivo_entrada = f"j{num_jornada}.csv"
    archivo_salida = f"{num_jornada}.csv"

    if not os.path.exists(archivo_entrada):
        print(f"⚠️ No existe el archivo {archivo_entrada}, se omite.")
        return

    with open(archivo_entrada, "r", encoding="utf-8") as f:
        equipos = [line.strip() for line in f if line.strip()]

    partidos = []
    for i in range(0, len(equipos), 2):
        local = MAPEO_EQUIPOS.get(equipos[i], equipos[i].upper())
        visitante = MAPEO_EQUIPOS.get(equipos[i+1], equipos[i+1].upper())
        fecha = input(f"📅 Introduce la fecha (YYYY-MM-DD) para {local} vs {visitante}: ")
        partidos.append([local, visitante, fecha])

    # Guardar CSV convertido
    with open(archivo_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Equipo Local", "Equipo Visitante", "Fecha"])
        writer.writerows(partidos)

    print(f"✅ Jornada {num_jornada} procesada → {archivo_salida}")

    # Copiar también a la carpeta de destino
    destino = os.path.join(carpeta_destino, archivo_salida)
    shutil.copy(archivo_salida, destino)
    print(f"📂 Copiado también a: {destino}")

    # Eliminar el archivo original
    os.remove(archivo_entrada)
    print(f"🗑️ Eliminado: {archivo_entrada}")

def main():
    inicio = int(input("👉 Introduce la jornada inicial (ej: 14): "))
    fin = int(input("👉 Introduce la jornada final (ej: 16): "))

    carpeta_destino = r"C:\Users\Admin\Documents\FUTBOL - copia\partidos"
    os.makedirs(carpeta_destino, exist_ok=True)

    for j in range(inicio, fin + 1):
        procesar_jornada(j, carpeta_destino)

    print("🎉 Conversión completada.")

if __name__ == "__main__":
    main()
