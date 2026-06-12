import csv
from datetime import datetime
import os
import glob

def pedir_fecha():
    """Pide la fecha validando el formato YYYY-MM-DD"""
    while True:
        fecha = input("Fecha a asignar (formato YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            return fecha
        except ValueError:
            print("❌ Formato incorrecto. Intenta de nuevo (ejemplo: 2025-11-09).")

def procesar_jornada(archivo_entrada, fecha):
    """Convierte jXX.csv → XX.csv con equipos y fecha"""
    num_jornada = archivo_entrada[1:-4]  # extrae número de jornada
    archivo_salida = f"{num_jornada}.csv"

    partidos = []
    with open(archivo_entrada, "r", newline="", encoding="utf-8") as f_in:
        lector = csv.reader(f_in)
        next(lector, None)  # saltar cabecera si existe

        equipos = []
        for fila in lector:
            if not fila:
                continue
            valor = fila[0].strip()
            if valor:
                equipos.append(valor)
                if len(equipos) == 2:
                    partidos.append([equipos[0], equipos[1], fecha])
                    equipos = []

    print(f"\n✅ Jornada {num_jornada} procesada con fecha {fecha}")
    print("📋 Vista previa de todos los partidos:")
    for local, visitante, f in partidos:
        print(f"   - {local}, {visitante}, {f}")

    confirm = input(f"\n¿Quieres guardar en {archivo_salida} y eliminar {archivo_entrada}? (s/n): ").strip().lower()
    if confirm != "s":
        print("❌ Operación cancelada. No se creó ni borró ningún archivo.")
        return

    with open(archivo_salida, "w", newline="", encoding="utf-8") as f_out:
        escritor = csv.writer(f_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        escritor.writerow(["Equipo Local", " Equipo Visitante", " Fecha"])
        for local, visitante, f in partidos:
            escritor.writerow([local, " " + visitante, " " + f])

    os.remove(archivo_entrada)
    print(f"\n📂 Archivo generado: {archivo_salida}")
    print(f"🗑️ Archivo original eliminado: {archivo_entrada}")

if __name__ == "__main__":
    # Detectar automáticamente archivos jXX.csv en la carpeta
    archivos_jornada = glob.glob("j*.csv")
    if not archivos_jornada:
        print("⚠️ No se encontraron archivos jXX.csv en la carpeta.")
        input("Presiona Enter para salir...")
        exit()

    fecha = pedir_fecha()

    for archivo in sorted(archivos_jornada):
        procesar_jornada(archivo, fecha)

    input("\n✅ Todas las jornadas procesadas. Presiona Enter para salir...")
