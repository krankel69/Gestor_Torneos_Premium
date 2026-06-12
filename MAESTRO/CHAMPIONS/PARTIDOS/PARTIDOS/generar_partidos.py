import re

input_file = "partidos.txt"
output_file = "partidos.csv"

fecha = input("Fecha (YYYY-MM-DD): ").strip()
fase = input("Fase: ").strip()
jornada = input("Jornada: ").strip()

with open(input_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

if len(lines) % 2 != 0:
    raise ValueError("Número impar de líneas. Revisa el archivo.")

rows = []

for i in range(0, len(lines), 2):
    local = lines[i]
    visitante = lines[i + 1]
    rows.append(f"{local},{visitante},{fecha},{fase},{jornada}")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("equipo_local,equipo_visitante,fecha,fase,jornada\n")
    for row in rows:
        f.write(row + "\n")

print("CSV generado correctamente:", output_file)
