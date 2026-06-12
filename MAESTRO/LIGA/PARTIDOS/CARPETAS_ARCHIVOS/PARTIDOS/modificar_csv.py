import pandas as pd

# Nombre del archivo original
archivo_original = 'goleadores.csv'

# Nombre para el nuevo archivo modificado
archivo_modificado = 'goleadores_modificado.csv'

try:
    # Leer el archivo CSV
    df = pd.read_csv(archivo_original)

    # 1. Eliminar la columna 'Equipo'
    df_modificado = df.drop(columns=['Equipo'])

    # 2. Renombrar la columna 'Nombre' a 'Goleador'
    df_modificado = df_modificado.rename(columns={'Nombre': 'Goleador'})

    # Guardar el resultado en un nuevo archivo CSV sin el índice
    df_modificado.to_csv(archivo_modificado, index=False)

    print(f"¡Éxito! Se ha creado el archivo '{archivo_modificado}' con el formato deseado.")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo '{archivo_original}'.")
    print("Asegúrate de que este script esté en la misma carpeta que tu archivo CSV.")
except KeyError:
    print("Error: El archivo CSV no contiene las columnas esperadas ('Nombre', 'Equipo').")