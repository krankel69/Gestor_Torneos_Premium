import os
import csv
import shutil
from datetime import datetime

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

def pedir_fecha(mensaje):
    """Pide una fecha y valida el formato YYYY-MM-DD"""
    while True:
        fecha = input(mensaje).strip()
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            return fecha
        except ValueError:
            print("⚠️ Formato inválido. Usa YYYY-MM-DD (ejemplo: 2025-10-25)")

def mostrar_resumen(partidos):
    print("\n📋 Resumen de la jornada:")
    for local, visitante, fecha in partidos:
        print(f"{local} vs {visitante} → {fecha}")
    print("-" * 40)

def procesar_jornada(num_jornada, carpeta_destino, modo_extendido):
    archivo_entrada = f"j{num_jornada}.csv"
    archivo_salida = f"{num_jornada}.csv"

    if not os.path.exists(archivo_entrada):
        print(f"⚠️ No existe el archivo {archivo_entrada}, se omite.")
        return

    with open(archivo_entrada, "r", encoding="utf-8") as f:
        equipos = [line.strip() for line in f if line.strip()]

    while True:
        partidos = []

        if modo_extendido:
            # Fecha distinta por partido
            for i in range(0, len(equipos), 2):
                local = MAPEO_EQUIPOS.get(equipos[i], equipos[i].upper())
                visitante = MAPEO_EQUIPOS.get(equipos[i+1], equipos[i+1].upper())
                fecha = pedir_fecha(f"📅 Fecha (YYYY-MM-DD) para {local} vs {visitante}: ")
                partidos.append([local, visitante, fecha])
        else:
            # Una sola fecha para toda la jornada
            fecha = pedir_fecha(f"📅 Fecha (YYYY-MM-DD) para la jornada {num_jornada}: ")
            for i in range(0, len(equipos), 2):
                local = MAPEO_EQUIPOS.get(equipos[i], equipos[i].upper())
                visitante = MAPEO_EQUIPOS.get(equipos[i+1], equipos[i+1].upper())
                partidos.append([local, visitante, fecha])

        mostrar_resumen(partidos)
        confirmar = input("✅ Confirmar jornada? (S/N): ").strip().upper()
        if confirmar == "S":
            break
        else:
            print("🔁 Reingresa las fechas para esta jornada.\n")

    # Guardar CSV
    with open(archivo_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Equipo Local", "Equipo Visitante", "Fecha"])
        writer.writerows(partidos)

    print(f"✅ Jornada {num_jornada} procesada → {archivo_salida}")

    # Copiar también al destino
    destino = os.path.join(carpeta_destino, archivo_salida)
    shutil.copy(archivo_salida, destino)
    print(f"📂 Copiado también a: {destino}")

    # Borrar original
    os.remove(archivo_entrada)
    print(f"🗑️ Eliminado: {archivo_entrada}\n")

def main():
    print("🏟️  Conversor de Jornadas de Fútbol\n")
    inicio = int(input("👉 Jornada inicial (ej: 14): "))
    fin = int(input("👉 Jornada final (ej: 16): "))
    modo = input("👉 Modo (R = rápido / E = extendido): ").strip().upper()

    modo_extendido = (modo == "E")

    carpeta_destino = r"C:\Users\Admin\Documents\FUTBOL - copia\partidos"
    os.makedirs(carpeta_destino, exist_ok=True)

    for j in range(inicio, fin + 1):
        procesar_jornada(j, carpeta_destino, modo_extendido)

    print("🎉 Conversión completada.")

if __name__ == "__main__":
    main()
