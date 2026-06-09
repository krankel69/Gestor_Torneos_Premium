"""
parche_ttkbootstrap.py  —  Fix COMPLETO para Python 3.14
Ejecutar UNA SOLA VEZ como Administrador:
    python parche_ttkbootstrap.py
"""

import sys, shutil, textwrap
from pathlib import Path

try:
    import ttkbootstrap

    pkg_dir = Path(ttkbootstrap.__file__).parent
except ImportError:
    print("ERROR: ttkbootstrap no instalado.")
    sys.exit(1)

style_path = pkg_dir / "style.py"
utility_path = pkg_dir / "utility.py"

print(f"Parcheando: {pkg_dir}")

# ── RESTAURAR BACKUPS SI EXISTEN ─────────────────────────────────────
for p in [style_path, utility_path]:
    bak = p.with_suffix(".py.bak314")
    if bak.exists():
        shutil.copy2(bak, p)
        print(f"  Restaurado desde backup: {p.name}")
    else:
        shutil.copy2(p, bak)
        print(f"  Backup creado: {bak.name}")

# ── PARCHE 1: utility.py ─────────────────────────────────────────────
u = utility_path.read_text(encoding="utf-8")

old_func = '''\
def get_image_name(image):
    """Extract and return the tcl/tk image name from a PhotoImage 
    object.
    
    Parameters:

        image (ImageTk.PhotoImage):
            A photoimage object.

    Returns:

        str:
            The tcl/tk name of the photoimage object.
    """
    return image._PhotoImage__photo.name'''

new_func = '''\
def get_image_name(image):
    """Extract and return the tcl/tk image name from a PhotoImage
    object. Patched for Python 3.14 compatibility.
    """
    # Python <= 3.13
    if hasattr(image, '_PhotoImage__photo'):
        name = image._PhotoImage__photo.name
        if name:
            return name
    # Python 3.14+: extraer nombre desde repr del objeto
    import re as _re
    m = _re.search(r'pyimage\\d+', str(image))
    if m:
        return m.group(0)
    # Ultimo recurso
    return f"img_{id(image)}"'''

if old_func in u:
    u = u.replace(old_func, new_func)
    utility_path.write_text(u, encoding="utf-8")
    print("  utility.py: get_image_name parcheado OK")
else:
    # Buscar solo la linea del return como fallback
    if "    return image._PhotoImage__photo.name" in u:
        u = u.replace(
            "    return image._PhotoImage__photo.name",
            textwrap.dedent("""\
                    # Python <= 3.13
                    if hasattr(image, '_PhotoImage__photo'):
                        name = image._PhotoImage__photo.name
                        if name:
                            return name
                    # Python 3.14+
                    import re as _re
                    m = _re.search(r'pyimage\\d+', str(image))
                    if m:
                        return m.group(0)
                    return f"img_{id(image)}" """),
        )
        utility_path.write_text(u, encoding="utf-8")
        print("  utility.py: return parcheado OK (fallback)")
    else:
        print("  utility.py: patron no encontrado, omitiendo")

# Verificar sintaxis
import py_compile, tempfile, os

try:
    py_compile.compile(str(utility_path), doraise=True)
    print("  utility.py: sintaxis OK")
except py_compile.PyCompileError as e:
    print(f"  utility.py: ERROR de sintaxis -> {e}")
    print("  Restaurando backup...")
    shutil.copy2(utility_path.with_suffix(".py.bak314"), utility_path)
    print("  Backup restaurado. Abortando.")
    sys.exit(1)

# ── PARCHE 2: style.py — monkey-patch global ─────────────────────────
s = style_path.read_text(encoding="utf-8")

MARKER = "# [PARCHE_PY314]"
if MARKER in s:
    print("  style.py: parche ya aplicado anteriormente.")
else:
    patch = """\

# [PARCHE_PY314] Fix Python 3.14: element_create falla con imagenes
# Parcheamos ttk.Style.element_create globalmente para capturar el
# error y usar fallback nativo. Cubre todos los widgets de una vez.
import tkinter.ttk as _ttk_mod
_orig_ec = _ttk_mod.Style.element_create

def _safe_element_create(self, elementname, etype, *args, **kwargs):
    if etype != "image":
        return _orig_ec(self, elementname, etype, *args, **kwargs)
    try:
        return _orig_ec(self, elementname, etype, *args, **kwargs)
    except Exception:
        for _fb in ("clam", "alt", "default"):
            try:
                return _orig_ec(self, elementname, "from", _fb)
            except Exception:
                continue

_ttk_mod.Style.element_create = _safe_element_create
# [FIN_PARCHE_PY314]

"""

    # Insertar justo antes de la primera clase del modulo
    insert_at = s.find("\nclass StyleBuilderTTK:")
    if insert_at == -1:
        insert_at = s.find("\nclass ")
    if insert_at != -1:
        s = s[:insert_at] + patch + s[insert_at:]
        style_path.write_text(s, encoding="utf-8")
        print("  style.py: monkey-patch inyectado OK")
    else:
        print("  style.py: no se encontro punto de insercion")

# Verificar sintaxis
try:
    py_compile.compile(str(style_path), doraise=True)
    print("  style.py: sintaxis OK")
except py_compile.PyCompileError as e:
    print(f"  style.py: ERROR de sintaxis -> {e}")
    shutil.copy2(style_path.with_suffix(".py.bak314"), style_path)
    print("  Backup restaurado.")
    sys.exit(1)

print()
print("[OK] Parche completado con exito.")
print("     Ejecuta la app normalmente.")
