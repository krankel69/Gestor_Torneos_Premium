import csv
from datetime import datetime
import os

def pedir_fecha():
    while True:
        fecha = input("Fecha de la jornada (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            return fecha
        except ValueError:
            print("❌ Formato incorrecto. Intenta de nuevo (ej: 2025-10-25).")

def procesar_csv(archivo, fecha):
    partidos = []
    with open(archivo, "r", newline="", encoding="utf-8") as f_in:
        lector = csv.reader(f_in, delimiter='\t')
        next(lector, None)  # saltar cabecera si existe

        for fila in lector:
            # eliminar celdas vacías y que contengan "Imagen"
            fila = [x.strip() for x in fila if x.strip() and "Imagen" not in x]
            if len(fila) >= 2:
                local = fila[0]
                visitante_fecha = fila[-1]  # última columna
                if visitante_fecha.endswith(fecha):
                    visitante = visitante_fecha[:-len(fecha)].strip()
                else:
                    visitante = visitante_fecha.strip()
                partidos.append([local, visitante, fecha])
    return partidos

if __name__ == "__main__":
    jornada = input("Número de la jornada: ").strip()
    archivo_csv = f"j{jornada}.csv"

    if not os.path.exists(archivo_csv):
        print(f"⚠️ No se encontró el archivo {archivo_csv}.")
        input("Presiona Enter para salir...")
        exit()

    fecha = pedir_fecha()
    partidos = procesar_csv(archivo_csv, fecha)

    if not partidos:
        print("⚠️ No se encontraron partidos válidos en el CSV.")
        input("Presiona Enter para salir...")
        exit()

    # Guardar CSV final
    nombre_salida = f"{jornada}.csv"
    with open(nombre_salida, "w", newline="", encoding="utf-8") as f_out:
        escritor = csv.writer(f_out)
        escritor.writerow(["Equipo Local", "Equipo Visitante", "Fecha"])
        for local, visitante, f in partidos:
            escritor.writerow([local, visitante, f])

    # Eliminar CSV antiguo
    if os.path.exists(archivo_csv):
        os.remove(archivo_csv)
        print(f"🗑️ Se ha eliminado el CSV antiguo: {archivo_csv}")

    print(f"\n✅ CSV final de la jornada generado: {nombre_salida}")
    input("Presiona Enter para salir...")
