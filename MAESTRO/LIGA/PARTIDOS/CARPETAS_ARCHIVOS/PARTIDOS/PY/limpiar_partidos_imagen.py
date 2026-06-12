import csv
from datetime import datetime
import os
import glob

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
                # separar visitante y fecha
                if visitante_fecha.endswith(fecha):
                    visitante = visitante_fecha[:-len(fecha)].strip()
                else:
                    visitante = visitante_fecha.strip()
                partidos.append([local, visitante, fecha])
    return partidos

if __name__ == "__main__":
    archivos = glob.glob("*.csv")
    if not archivos:
        print("⚠️ No se encontraron archivos CSV en la carpeta.")
        input("Presiona Enter para salir...")
        exit()

    fecha = pedir_fecha()
    jornada = input("Número de la jornada: ").strip()

    todos_partidos = []
    for archivo in archivos:
        partidos = procesar_csv(archivo, fecha)
        todos_partidos.extend(partidos)

    if not todos_partidos:
        print("⚠️ No se encontraron partidos válidos en los CSV.")
        input("Presiona Enter para salir...")
        exit()

    # Guardar CSV final
    nombre_salida = f"{jornada}.csv"
    with open(nombre_salida, "w", newline="", encoding="utf-8") as f_out:
        escritor = csv.writer(f_out)
        escritor.writerow(["Equipo Local", " Equipo Visitante", " Fecha"])
        for local, visitante, f in todos_partidos:
            escritor.writerow([local, " " + visitante, " " + f])

    # Eliminar CSV antiguo de esta jornada si existe (ej: j14.csv)
    antiguo = f"j{jornada}.csv"
    if os.path.exists(antiguo):
        os.remove(antiguo)
        print(f"🗑️ Se ha eliminado el CSV antiguo: {antiguo}")

    print(f"\n✅ CSV final de la jornada generado: {nombre_salida}")
    print("📂 Las jornadas anteriores se mantienen intactas.")
    input("Presiona Enter para salir...")
