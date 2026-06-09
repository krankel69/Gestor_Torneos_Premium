"""
reparar_utility.py
Ejecutar como Administrador (NO necesita importar ttkbootstrap):
    python reparar_utility.py
"""
import sys
from pathlib import Path

# Localizar utility.py sin importar ttkbootstrap
candidates = [
    Path(r"C:\Users\Administrador\AppData\Local\Programs\Python\Python314\Lib\site-packages\ttkbootstrap\utility.py"),
]
# Buscar automaticamente si la ruta no existe
for c in list(candidates):
    if not c.exists():
        import glob
        found = glob.glob(r"C:\Users\**\ttkbootstrap\utility.py", recursive=True)
        candidates = [Path(f) for f in found]
        break

utility_path = next((p for p in candidates if p.exists()), None)
if not utility_path:
    print("ERROR: No se encontro utility.py")
    sys.exit(1)

print(f"Reparando: {utility_path}")

# Leer el archivo roto
text = utility_path.read_text(encoding="utf-8")

# Mostrar las lineas problemáticas
lines = text.splitlines()
for i, line in enumerate(lines[95:110], start=96):
    print(f"  {i}: {repr(line)}")

print()

# La funcion correcta completa
OLD_BROKEN = None
NEW_FUNC = '''\
def get_image_name(image):
    """Extract and return the tcl/tk image name from a PhotoImage object."""
    if hasattr(image, '_PhotoImage__photo'):
        name = image._PhotoImage__photo.name
        if name:
            return name
    import re as _re
    m = _re.search(r'pyimage\\d+', str(image))
    if m:
        return m.group(0)
    return f"img_{id(image)}"
'''

# Buscar la función get_image_name entera (puede estar rota)
import re
pattern = re.compile(
    r'^def get_image_name\(image\):.*?(?=\ndef |\nclass |\Z)',
    re.MULTILINE | re.DOTALL
)
match = pattern.search(text)
if match:
    print(f"Funcion encontrada en posicion {match.start()}-{match.end()}")
    print(f"Contenido actual:\n{match.group()}\n")
    text = text[:match.start()] + NEW_FUNC + text[match.end():]
    utility_path.write_text(text, encoding="utf-8")
    print("Reparado OK")
else:
    print("ERROR: No se encontro la funcion get_image_name")
    sys.exit(1)

# Verificar sintaxis
import py_compile
try:
    py_compile.compile(str(utility_path), doraise=True)
    print("Sintaxis OK - utility.py reparado correctamente")
except py_compile.PyCompileError as e:
    print(f"ERROR de sintaxis: {e}")
    # Restaurar backup si existe
    bak = utility_path.with_suffix(".py.bak314")
    if bak.exists():
        import shutil
        shutil.copy2(bak, utility_path)
        print("Backup restaurado desde .bak314")
    sys.exit(1)
