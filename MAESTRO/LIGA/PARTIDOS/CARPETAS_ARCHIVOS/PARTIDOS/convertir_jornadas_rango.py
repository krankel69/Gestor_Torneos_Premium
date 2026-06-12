import os
import csv
import shutil

# Diccionario de nombres de equipos
EQUIPOS = {
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

def procesar_jornada(archivo_jx, modo_extendido):
    if not os.path.exists(archivo_jx):
        print(f"Archivo {archivo_jx} no encontrado, se salta.")
        return None

    equipos = []
    with open(archivo_jx, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                equipos.append(EQUIPOS.get(line, line.upper()))

    if len(equipos) % 2 != 0:
        print(f"Advertencia: número impar de equipos en {archivo_jx}")
        return None

    fecha = None
    while True:
        fecha_input = input(f"Introduce la fecha para {archivo_jx} (YYYY-MM-DD): ")
        try:
            yyyy, mm, dd = map(int, fecha_input.split('-'))
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                fecha = fecha_input
                break
            else:
                print("Fecha inválida. Formato YYYY-MM-DD.")
        except:
            print("Formato incorrecto. Intenta de nuevo.")

    filas = []
    for i in range(0, len(equipos), 2):
        local = equipos[i]
        visitante = equipos[i+1]
        if modo_extendido:
            fecha_partido = input(f"Introduce fecha para {local} vs {visitante} (YYYY-MM-DD) o ENTER para {fecha}: ").strip()
            if fecha_partido:
                filas.append([local, visitante, fecha_partido])
            else:
                filas.append([local, visitante, fecha])
        else:
            filas.append([local, visitante, fecha])

    return filas

def main():
    modo_extendido = input("¿Deseas modo extendido (fecha por partido)? S/N: ").strip().lower() == 's'

    inicio = int(input("Introduce jornada inicial: "))
    fin = int(input("Introduce jornada final: "))

    if not os.path.exists(DESTINO):
        os.makedirs(DESTINO)

    for j in range(inicio, fin + 1):
        archivo_jx = f"j{j}.csv"
        filas = procesar_jornada(archivo_jx, modo_extendido)
        if filas:
            archivo_final = f"{j}.csv"
            with open(archivo_final, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Equipo Local","Equipo Visitante","Fecha"])
                writer.writerows(filas)
            print(f"{archivo_final} generado con éxito.")
            shutil.copy(archivo_final, DESTINO)
            print(f"{archivo_final} copiado a {DESTINO}")
            os.remove(archivo_jx)  # elimina solo el jX.csv procesado

if __name__ == "__main__":
    main()
