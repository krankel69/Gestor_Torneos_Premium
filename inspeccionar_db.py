"""
inspeccionar_db.py
Ejecutar: python inspeccionar_db.py
Muestra el esquema exacto de todas las tablas de la BD elegida.
"""
import sqlite3
from tkinter import filedialog, Tk

root = Tk()
root.withdraw()
ruta = filedialog.askopenfilename(
    title="Selecciona la BD a inspeccionar",
    filetypes=[("SQLite", "*.db")]
)
root.destroy()

if not ruta:
    print("Cancelado.")
    exit()

print(f"\nBD: {ruta}\n{'='*60}")
conn = sqlite3.connect(ruta)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tablas = [r[0] for r in cur.fetchall()]

for tabla in tablas:
    cur.execute(f"PRAGMA table_info({tabla})")
    cols = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) FROM {tabla}")
    n = cur.fetchone()[0]
    print(f"\nTabla: {tabla}  ({n} filas)")
    for col in cols:
        print(f"  {col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else ''} {'PK' if col[5] else ''}")

conn.close()
