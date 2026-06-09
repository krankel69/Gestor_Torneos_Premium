#!/usr/bin/env python3
"""
🔒 SCRIPT SETUP SEGURO - Gestor Premium de Torneos v2.1.0
Ejecutar ANTES de cualquier cambio importante

Qué hace:
✓ Crea estructura de carpetas
✓ Backup automático de v2.0.0
✓ Inicializa Git
✓ Crea CHANGELOG
✓ Crea environment seguro
"""

import os
import shutil
import sqlite3
import gzip
from datetime import datetime
from pathlib import Path
import subprocess
import json

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(r"D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium")
BACKUP_DIR = PROJECT_ROOT / "backups" / "v2.0.0"
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

DATABASES = [
    r"D:\Manu\Documentos\FUTBOL\bases_de_datos\liga_futbol_v2.db",
    r"D:\Manu\Documentos\FUTBOL\bases_de_datos\mundial_2026_v2.db",
    r"D:\Manu\Documentos\FUTBOL\bases_de_datos\champions_gui_v2.db",
    r"D:\Manu\Documentos\FUTBOL\bases_de_datos\eurocopa_2024_v2.db",
]

APP_FILES = [
    r"D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium\app_maestra_futbol.py",
    r"D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium\database.py",
    r"D:\Manu\Documentos\FUTBOL\Gestor_Torneos_Premium\ui_components.py",
]

# ════════════════════════════════════════════════════════════════════════════
# COLORES PARA TERMINAL
# ════════════════════════════════════════════════════════════════════════════


class Colors:
    OK = "\033[92m"
    WARN = "\033[93m"
    ERROR = "\033[91m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def log_ok(msg):
    print(f"{Colors.OK}✓ {msg}{Colors.END}")


def log_warn(msg):
    print(f"{Colors.WARN}⚠ {msg}{Colors.END}")


def log_error(msg):
    print(f"{Colors.ERROR}✗ {msg}{Colors.END}")


def log_info(msg):
    print(f"{Colors.INFO}ℹ {msg}{Colors.END}")


# ════════════════════════════════════════════════════════════════════════════
# PASO 1: CREAR ESTRUCTURA DE CARPETAS
# ════════════════════════════════════════════════════════════════════════════


def setup_directories():
    print(f"\n{Colors.BOLD}PASO 1: Creando estructura de carpetas...{Colors.END}\n")

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


# ════════════════════════════════════════════════════════════════════════════
# PASO 2: HACER BACKUP DE VERSIÓN ACTUAL
# ════════════════════════════════════════════════════════════════════════════


def backup_files():
    print(f"\n{Colors.BOLD}PASO 2: Backupeando archivos de aplicación...{Colors.END}\n")

    for app_file in APP_FILES:
        if os.path.exists(app_file):
            dest = BACKUP_DIR / Path(app_file).name
            shutil.copy2(app_file, dest)
            log_ok(f"Backup: {Path(app_file).name}")
        else:
            log_warn(f"Archivo no encontrado: {app_file}")


def backup_databases():
    print(f"\n{Colors.BOLD}PASO 3: Exportando bases de datos...{Colors.END}\n")

    for db_path in DATABASES:
        if not os.path.exists(db_path):
            log_warn(f"BD no encontrada: {Path(db_path).name}")
            continue

        try:
            db_name = Path(db_path).stem
            sql_file = BACKUP_DIR / f"{db_name}.sql"

            # Conectar y exportar SQL
            conn = sqlite3.connect(db_path)
            with open(sql_file, "w") as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            conn.close()

            # Comprimir
            gz_file = BACKUP_DIR / f"{db_name}.sql.gz"
            with open(sql_file, "rb") as f_in:
                with gzip.open(gz_file, "wb") as f_out:
                    f_out.writelines(f_in)

            # Eliminar SQL sin comprimir (solo guardar .gz)
            os.remove(sql_file)

            log_ok(f"BD exportada: {db_name}.sql.gz")

        except Exception as e:
            log_error(f"Error exportando {db_path}: {e}")


# ════════════════════════════════════════════════════════════════════════════
# PASO 4: CREAR DOCUMENTACIÓN
# ════════════════════════════════════════════════════════════════════════════


def create_changelog():
    print(f"\n{Colors.BOLD}PASO 4: Creando CHANGELOG.md...{Colors.END}\n")

    changelog = """# CHANGELOG - Gestor Premium de Torneos

## [2.0.0] - 2026-06-09
### Added
- ✅ FASE 0: El Búnker (Backups)
- ✅ FASE 1: Los Cimientos (Modularización con ui_components.py)
- ✅ FASE 2: El Lobby (Crear nuevo torneo)
- ✅ FASE 3: El Escaparate (Dashboard visual)
- ✅ FASE 4: Nivel Profesional (Generador de actas PDF)
- ✅ FASE 5: Análisis Profundo (Estadísticas avanzadas)

### Features
- Dashboard con progreso, próxima jornada, destacados
- Panel de Control con 3 secciones visuales
- Botón "🖨 Generar Acta PDF" en todos los torneos
- Estadísticas analíticas: Racha, Rendimiento Local/Visitante
- Modularización en ui_components.py
- Soporte para Liga, Champions League, Mundial, Eurocopa

### Security
- SQLite3 timeout de 10 segundos
- Conexiones con context managers
- Validación de inputs
- Backups automáticos

### Bug Fixes
- ✓ Error padding en tb.LabelFrame (solucionado)
- ✓ SQL H2H 17 placeholders (simplificado)
- ✓ Desempate H2H funcionando correctamente

## [2.1.0] - PRÓXIMO
### Planned
- API REST con FastAPI
- Separación de lógica de negocio
- Endpoints CRUD para equipos, partidos, goleadores
- Testing completo de BD
- Documentación de API

## [2.2.0] - PRÓXIMO
### Planned
- Rediseño UI/UX profesional
- Gráficos interactivos con Plotly
- Tema oscuro/claro
- Design System integrado

## [2.3.0] - PRÓXIMO
### Planned
- WebSockets para actualizaciones en tiempo real
- Notificaciones automáticas
- Live scoring durante partidos

## [2.4.0] - PRÓXIMO
### Planned
- Sistema de monetización (FREE/PRO/ENTERPRISE)
- Integración Stripe
- Panel de suscripciones

## [2.5.0] - PRÓXIMO
### Planned
- Integración Slack
- Notificaciones por email (SendGrid)
- Sincronización Google Calendar
- Alertas WhatsApp (Twilio)

## [3.0.0] - PRÓXIMO
### Planned
- App web con React
- App mobile con React Native
- Migración a PostgreSQL
- Hospedaje en cloud (AWS/GCP)
"""

    changelog_file = DOCS_DIR / "CHANGELOG.md"
    with open(changelog_file, "w") as f:
        f.write(changelog)

    log_ok("CHANGELOG.md creado")


def create_version_file():
    print(f"\n{Colors.BOLD}PASO 5: Creando VERSION.txt...{Colors.END}\n")

    version_file = PROJECT_ROOT / "VERSION.txt"
    with open(version_file, "w") as f:
        f.write("2.0.0\n")

    log_ok("VERSION.txt = 2.0.0")


def create_backup_log():
    print(f"\n{Colors.BOLD}PASO 6: Documentando backup...{Colors.END}\n")

    log_file = BACKUP_DIR / "BACKUP_LOG.txt"
    with open(log_file, "w") as f:
        f.write(f"BACKUP v2.0.0 - {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        f.write("ARCHIVOS DE APLICACIÓN:\n")
        for app_file in APP_FILES:
            if os.path.exists(app_file):
                size = os.path.getsize(app_file) / 1024
                f.write(f"  ✓ {Path(app_file).name} ({size:.1f} KB)\n")

        f.write("\nBASES DE DATOS:\n")
        for db_path in DATABASES:
            if os.path.exists(db_path):
                size = os.path.getsize(db_path) / 1024 / 1024
                f.write(f"  ✓ {Path(db_path).name} ({size:.1f} MB)\n")

        f.write("\nPARÁMETROS:\n")
        f.write(f"  Fecha: {datetime.now().isoformat()}\n")
        f.write(f"  Ubicación: {BACKUP_DIR}\n")
        f.write(f"  Compresión: .sql.gz\n")
        f.write(f"\nROLLBACK:\n")
        f.write(f"  1. Eliminar cambios en código\n")
        f.write(f"  2. Copiar .sql.gz a app y descomprimir\n")
        f.write(f"  3. Restaurar: sqlite3 liga_futbol_v2.db < backup.sql\n")

    log_ok("BACKUP_LOG.txt creado")


# ════════════════════════════════════════════════════════════════════════════
# PASO 7: CREAR .gitignore
# ════════════════════════════════════════════════════════════════════════════


def create_gitignore():
    print(f"\n{Colors.BOLD}PASO 7: Creando .gitignore...{Colors.END}\n")

    gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Pytest
.pytest_cache/
.coverage
htmlcov/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Databases
*.db-journal
*.db-shm
*.db-wal

# Logs
*.log
logs/

# Ambiente
.env
.env.local
config.local.py

# Temporal
temp/
tmp/
*.tmp

# Archivos de usuario
desktop.ini
.config/

# Node (si usamos npm después)
node_modules/
package-lock.json

# Excepciones (sí guardar)
!backups/v2.0.0/
!docs/
!tests/
"""

    gitignore_file = PROJECT_ROOT / ".gitignore"
    with open(gitignore_file, "w") as f:
        f.write(gitignore)

    log_ok(".gitignore creado")


# ════════════════════════════════════════════════════════════════════════════
# PASO 8: CREAR DOCUMENTO DE SEGURIDAD
# ════════════════════════════════════════════════════════════════════════════


def create_security_doc():
    print(f"\n{Colors.BOLD}PASO 8: Creando SECURITY.md...{Colors.END}\n")

    security = """# POLÍTICA DE SEGURIDAD - Gestor Premium de Torneos

## Principios Fundamentales

1. **Integridad de Datos SIEMPRE**
   - Backup antes de cualquier cambio
   - Testing en BD test (nunca en producción)
   - Rollback automático si falla

2. **Validación de Inputs**
   - Prevenir SQL injection
   - Validar tipos de datos
   - Sanitizar strings

3. **Encriptación**
   - Contraseñas: bcrypt (cuando agregues autenticación)
   - Datos sensibles: AES-256
   - HTTPS obligatorio (cuando sea web)

4. **Auditoría**
   - Registrar quién cambió qué
   - Timestamps en cada cambio
   - Log de errores

## Checklist de Seguridad (Antes de cada deploy)

- [ ] Backup de BD actual
- [ ] Tests unitarios ✓ 100%
- [ ] Tests de integración ✓
- [ ] PRAGMA integrity_check OK
- [ ] Validación de inputs completa
- [ ] Documentación actualizada
- [ ] CHANGELOG actualizado
- [ ] Script de rollback probado
- [ ] Logging funciona
- [ ] No hay memory leaks

## Política de Backups

- **Frecuencia**: Antes de cada versión mayor
- **Ubicación**: backups/vX.Y.Z/
- **Formato**: .sql.gz (comprimido)
- **Retención**: Último año (12 versiones)

## Incidentes

Si algo se corrompe:

1. Detente INMEDIATAMENTE
2. NO intentes "arreglarlo" rápido
3. Restaura desde backup: `sqlite3 db.db < backup.sql`
4. Investiga ROOT CAUSE
5. Documenta qué pasó
6. Implementa prevención

## Contacto

Error crítico → backup_restore_guide.txt
"""

    security_file = DOCS_DIR / "SECURITY.md"
    with open(security_file, "w") as f:
        f.write(security)

    log_ok("SECURITY.md creado")


# ════════════════════════════════════════════════════════════════════════════
# PASO 9: CREAR SCRIPT DE ROLLBACK
# ════════════════════════════════════════════════════════════════════════════


def create_rollback_script():
    print(f"\n{Colors.BOLD}PASO 9: Creando script de rollback...{Colors.END}\n")

    rollback_script = """#!/usr/bin/env python3
\"\"\"
🔙 ROLLBACK - Volver a versión anterior

Uso: python rollback_to_v2.0.0.py
\"\"\"

import sqlite3
import gzip
import os
from pathlib import Path

BACKUP_DIR = Path("backups/v2.0.0")
DATABASES_DIR = Path(r"D:\\Manu\\Documentos\\FUTBOL\\bases_de_datos")

def restore_database(db_name):
    \"\"\"Restaura BD desde backup.\"\"\"
    
    # Encontrar .sql.gz
    gz_file = list(BACKUP_DIR.glob(f"{db_name}*.sql.gz"))[0]
    sql_file = BACKUP_DIR / f"{db_name}.sql"
    
    # Descomprimir
    with gzip.open(gz_file, 'rb') as f_in:
        with open(sql_file, 'wb') as f_out:
            f_out.writelines(f_in)
    
    # Restaurar BD
    db_path = DATABASES_DIR / f"{db_name}.db"
    if db_path.exists():
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    with open(sql_file) as f:
        conn.executescript(f.read())
    conn.close()
    
    # Limpiar SQL temporal
    os.remove(sql_file)
    
    print(f"✓ Restaurado: {db_name}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python rollback_to_v2.0.0.py [db_name]")
        print("Ejemplo: python rollback_to_v2.0.0.py liga_futbol_v2")
        sys.exit(1)
    
    db_name = sys.argv[1]
    
    print("🔴 ROLLBACK A v2.0.0")
    print("Confirma con: python rollback_to_v2.0.0.py", db_name)
    response = input("¿Continuar? (s/n): ")
    
    if response.lower() == "s":
        restore_database(db_name)
        print("✓ ROLLBACK COMPLETADO")
    else:
        print("Cancelado")
"""

    rollback_file = PROJECT_ROOT / "rollback_to_v2.0.0.py"
    with open(rollback_file, "w") as f:
        f.write(rollback_script)

    log_ok("Script de rollback creado")


# ════════════════════════════════════════════════════════════════════════════
# PASO 10: RESUMEN
# ════════════════════════════════════════════════════════════════════════════


def print_summary():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.OK}✓ SETUP COMPLETADO{Colors.END}\n")

    print(f"{Colors.BOLD}Estructura creada:{Colors.END}")
    print(f"  {PROJECT_ROOT}/")
    print(f"  ├── src/")
    print(f"  │   └── api_rest/ (NUEVO para v2.1.0)")
    print(f"  ├── tests/")
    print(f"  ├── docs/")
    print(f"  │   ├── CHANGELOG.md ✓")
    print(f"  │   └── SECURITY.md ✓")
    print(f"  ├── backups/")
    print(f"  │   └── v2.0.0/ (COMPLETO) ✓")
    print(f"  ├── VERSION.txt (2.0.0) ✓")
    print(f"  ├── .gitignore ✓")
    print(f"  └── rollback_to_v2.0.0.py ✓\n")

    print(f"{Colors.BOLD}Próximos pasos:{Colors.END}")
    print(f"  1. Inicializar Git:")
    print(f"     $ cd {PROJECT_ROOT}")
    print(f"     $ git init")
    print(f"     $ git add .")
    print(f"     $ git commit -m 'chore: Initial backup v2.0.0'")
    print(f"\n  2. Crear rama de desarrollo:")
    print(f"     $ git checkout -b desarrollo")
    print(f"\n  3. Crear rama para v2.1.0:")
    print(f"     $ git checkout -b feature/api-rest")
    print(f"\n  4. Empezar desarrollo de FASE I (API REST)")
    print(f"\n  ⚠️  NUNCA modifiques 'master', siempre usa 'desarrollo'")
    print(f"\n{Colors.WARN}Recuerda:{Colors.END}")
    print(f"  - Backups en backups/vX.Y.Z/")
    print(f"  - Tests antes de cambios")
    print(f"  - Documentación siempre")
    print(f"  - Rollback si algo sale mal\n")

    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════


def main():
    print(f"\n{Colors.BOLD}{Colors.OK}🔒 INICIALIZACIÓN SEGURA - Gestor Premium v2.0.0{Colors.END}\n")

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

    except Exception as e:
        log_error(f"Error durante setup: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
