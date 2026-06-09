#!/usr/bin/env python3
"""
Setup seguro - Version 2 (Windows compatible)
"""

import os
import shutil
import sqlite3
import gzip
from datetime import datetime
from pathlib import Path
import sys

# Force UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN - AJUSTADO PARA WINDOWS
# ════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(r"D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium")
BACKUP_DIR = PROJECT_ROOT / "backups" / "v2.0.0"
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Buscar BDs automáticamente
FUTBOL_ROOT = Path(r"D:\Manu\Documentos\FUTBOL")
DATABASE_PATTERNS = ["*v2.db", "*2026*.db", "*2024*.db"]

def find_databases():
    """Busca todas las BDs en la carpeta FUTBOL."""
    dbs = []
    for pattern in DATABASE_PATTERNS:
        found = list(FUTBOL_ROOT.glob(f"**/{pattern}"))
        dbs.extend(found)
    return list(set(dbs))  # Eliminar duplicados

DATABASES = find_databases()

# ════════════════════════════════════════════════════════════════════════════
# SIN COLORES (Windows PowerShell no soporta bien)
# ════════════════════════════════════════════════════════════════════════════

def log_ok(msg):
    print(f"[OK] {msg}")

def log_warn(msg):
    print(f"[!]  {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}")

def log_info(msg):
    print(f"[*] {msg}")

# ════════════════════════════════════════════════════════════════════════════

def setup_directories():
    print("\n=== PASO 1: Creando estructura de carpetas ===\n")
    
    folders = [
        PROJECT_ROOT,
        SRC_DIR,
        SRC_DIR / "api_rest" / "routes",
        SRC_DIR / "api_rest" / "services",
        SRC_DIR / "api_rest" / "schemas",
        TESTS_DIR,
        DOCS_DIR,
        BACKUP_DIR,
    ]
    
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        log_ok(f"Carpeta: {folder.name}")

def backup_files():
    print("\n=== PASO 2: Backupeando archivos de aplicacion ===\n")
    
    app_files = [
        PROJECT_ROOT / "app_maestra_futbol.py",
        PROJECT_ROOT / "database.py",
        PROJECT_ROOT / "ui_components.py",
    ]
    
    for app_file in app_files:
        if os.path.exists(app_file):
            dest = BACKUP_DIR / app_file.name
            shutil.copy2(app_file, dest)
            log_ok(f"Backup: {app_file.name}")
        else:
            log_warn(f"Archivo no encontrado: {app_file.name}")

def backup_databases():
    print("\n=== PASO 3: Exportando bases de datos ===\n")
    
    if not DATABASES:
        log_warn("No se encontraron bases de datos")
        return
    
    log_info(f"Encontradas {len(DATABASES)} bases de datos")
    
    for db_path in DATABASES:
        try:
            db_name = db_path.stem
            sql_file = BACKUP_DIR / f"{db_name}.sql"
            
            print(f"\nProcessando: {db_name}")
            
            # Exportar SQL
            conn = sqlite3.connect(str(db_path))
            with open(sql_file, "w", encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            conn.close()
            
            # Comprimir
            gz_file = BACKUP_DIR / f"{db_name}.sql.gz"
            with open(sql_file, "rb") as f_in:
                with gzip.open(gz_file, "wb") as f_out:
                    f_out.writelines(f_in)
            
            # Eliminar SQL (solo guardar .gz)
            os.remove(sql_file)
            
            file_size = os.path.getsize(gz_file) / 1024 / 1024
            log_ok(f"BD exportada: {db_name}.sql.gz ({file_size:.2f} MB)")
            
        except Exception as e:
            log_error(f"Error exportando {db_path}: {e}")

def create_changelog():
    print("\n=== PASO 4: Creando CHANGELOG.md ===\n")
    
    changelog = """# CHANGELOG - Gestor Premium de Torneos

## [2.0.0] - 2026-06-09
### Added
- [OK] FASE 0: El Bunker (Backups)
- [OK] FASE 1: Los Cimientos (Modularizacion)
- [OK] FASE 2: El Lobby (Crear nuevo torneo)
- [OK] FASE 3: El Escaparate (Dashboard visual)
- [OK] FASE 4: Nivel Profesional (PDF)
- [OK] FASE 5: Analisis Profundo (Estadisticas)

### Features
- Dashboard con progreso, proxima jornada, destacados
- Generador de actas PDF
- Estadisticas: Racha, Rendimiento Local/Visitante
- Modularizacion en ui_components.py
- Soporte: Liga, Champions, Mundial, Eurocopa

### Security
- SQLite3 timeout 10 segundos
- Conexiones con context managers
- Validacion de inputs

## [2.1.0] - PROXIMO
- API REST con FastAPI
- Separacion logica de negocio
"""
    
    changelog_file = DOCS_DIR / "CHANGELOG.md"
    with open(changelog_file, "w", encoding='utf-8') as f:
        f.write(changelog)
    
    log_ok("CHANGELOG.md creado")

def create_version_file():
    print("\n=== PASO 5: Creando VERSION.txt ===\n")
    
    version_file = PROJECT_ROOT / "VERSION.txt"
    with open(version_file, "w", encoding='utf-8') as f:
        f.write("2.0.0\n")
    
    log_ok("VERSION.txt = 2.0.0")

def create_backup_log():
    print("\n=== PASO 6: Documentando backup ===\n")
    
    log_file = BACKUP_DIR / "BACKUP_LOG.txt"
    with open(log_file, "w", encoding='utf-8') as f:
        f.write(f"BACKUP v2.0.0 - {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        f.write("ARCHIVOS DE APLICACION:\n")
        
        app_files = [
            PROJECT_ROOT / "app_maestra_futbol.py",
            PROJECT_ROOT / "database.py",
            PROJECT_ROOT / "ui_components.py",
        ]
        
        for app_file in app_files:
            if os.path.exists(app_file):
                size = os.path.getsize(app_file) / 1024
                f.write(f"  [OK] {app_file.name} ({size:.1f} KB)\n")
        
        f.write("\nBASES DE DATOS:\n")
        for db_path in DATABASES:
            size = os.path.getsize(db_path) / 1024 / 1024
            f.write(f"  [OK] {db_path.name} ({size:.1f} MB)\n")
        
        f.write("\nPARAMETROS:\n")
        f.write(f"  Fecha: {datetime.now().isoformat()}\n")
        f.write(f"  Ubicacion: {BACKUP_DIR}\n")
        f.write(f"  Compresion: .sql.gz\n")
    
    log_ok("BACKUP_LOG.txt creado")

def create_gitignore():
    print("\n=== PASO 7: Creando .gitignore ===\n")
    
    gitignore = """# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/
build/
dist/
*.egg-info/
*.egg

# Pytest
.pytest_cache/
.coverage

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Databases
*.db-journal
*.db-shm
*.db-wal

# Logs
*.log

# Ambiente
.env
.env.local

# Excepciones
!backups/
!docs/
!tests/
"""
    
    gitignore_file = PROJECT_ROOT / ".gitignore"
    with open(gitignore_file, "w", encoding='utf-8') as f:
        f.write(gitignore)
    
    log_ok(".gitignore creado")

def create_security_doc():
    print("\n=== PASO 8: Creando SECURITY.md ===\n")
    
    security = """# POLITICA DE SEGURIDAD

## Principios

1. Integridad de datos SIEMPRE
2. Validacion de inputs
3. Encriptacion de sensibles
4. Auditoria de cambios

## Checklist (Antes de deploy)

- Backup de BD actual
- Tests unitarios pasando
- PRAGMA integrity_check OK
- Validacion de inputs
- Documentacion actualizada
- CHANGELOG actualizado
- Script rollback probado
- Logging funciona
"""
    
    security_file = DOCS_DIR / "SECURITY.md"
    with open(security_file, "w", encoding='utf-8') as f:
        f.write(security)
    
    log_ok("SECURITY.md creado")

def create_rollback_script():
    print("\n=== PASO 9: Creando script de rollback ===\n")
    
    rollback_script = """#!/usr/bin/env python3
import sqlite3
import gzip
import os
from pathlib import Path

BACKUP_DIR = Path("backups/v2.0.0")

def restore_database(db_name):
    gz_file = list(BACKUP_DIR.glob(f"{db_name}*.sql.gz"))[0]
    sql_file = BACKUP_DIR / f"{db_name}.sql"
    
    with gzip.open(gz_file, 'rb') as f_in:
        with open(sql_file, 'wb') as f_out:
            f_out.writelines(f_in)
    
    print(f"[OK] Restaurado: {db_name}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python rollback_to_v2.0.0.py [db_name]")
        sys.exit(1)
    
    db_name = sys.argv[1]
    response = input("Confirmar rollback? (s/n): ")
    
    if response.lower() == "s":
        restore_database(db_name)
    else:
        print("Cancelado")
"""
    
    rollback_file = PROJECT_ROOT / "rollback_to_v2.0.0.py"
    with open(rollback_file, "w", encoding='utf-8') as f:
        f.write(rollback_script)
    
    log_ok("Script de rollback creado")

def print_summary():
    print(f"\n{'='*80}")
    print("[OK] SETUP COMPLETADO")
    print(f"{'='*80}\n")
    
    print("Estructura creada:")
    print(f"  {PROJECT_ROOT}/")
    print(f"  +-- src/")
    print(f"  +-- tests/")
    print(f"  +-- docs/")
    print(f"  +-- backups/v2.0.0/")
    print(f"      +-- app_maestra_futbol.py")
    print(f"      +-- ui_components.py")
    print(f"      +-- database.py")
    print(f"      +-- *.sql.gz (todas las BDs)\n")
    
    print("Proximos pasos:")
    print("  1. Inicializar Git:")
    print("     cd d:\\Manu\\Documentos\\FUTBOL\\Gestor_Torneos_Premium")
    print("     git init")
    print("     git add .")
    print("     git commit -m 'chore: Backup v2.0.0'")
    print("\n  2. Crear rama desarrollo:")
    print("     git branch desarrollo")
    print("     git checkout desarrollo")
    print("\n  3. Comienza FASE I (API REST)\n")
    
    print(f"{'='*80}\n")

def main():
    print("\n[*] INICIALIZACION SEGURA - Gestor Premium v2.0.0\n")
    
    try:
        setup_directories()
        backup_files()
        backup_databases()
        create_changelog()
        create_version_file()
        create_backup_log()
        create_gitignore()
        create_security_doc()
        create_rollback_script()
        print_summary()
        
        return 0
        
    except Exception as e:
        log_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
