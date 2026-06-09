#!/usr/bin/env python3
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
