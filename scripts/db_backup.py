#!/usr/bin/env python
"""
Database Backup Utility for FinSight
This script implements a simulated production backup strategy for SQLite databases.
For PostgreSQL, it would wrap pg_dump.
"""

import os
import sys
import shutil
import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("db_backup")

def backup_sqlite(source_path: str, backup_dir: str):
    if not os.path.exists(source_path):
        logger.error(f"Source database not found at {source_path}")
        sys.exit(1)
        
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    db_name = os.path.basename(source_path)
    backup_path = os.path.join(backup_dir, f"{db_name}.{timestamp}.bak")
    
    try:
        # For SQLite, a simple file copy is often sufficient if WAL mode isn't heavily contested,
        # but in production we'd use the backup API. For this sprint, shutil.copy2 is acceptable.
        import sqlite3
        
        logger.info(f"Initiating safe backup of {source_path} to {backup_path}")
        
        # Connect to source and create a safe backup
        source_conn = sqlite3.connect(source_path)
        backup_conn = sqlite3.connect(backup_path)
        
        with backup_conn:
            source_conn.backup(backup_conn)
            
        backup_conn.close()
        source_conn.close()
        
        # Verify backup size
        source_size = os.path.getsize(source_path)
        backup_size = os.path.getsize(backup_path)
        
        logger.info(f"Backup successful. Size: {backup_size / (1024*1024):.2f} MB")
        
        if backup_size < (source_size * 0.9):
            logger.warning("Backup size is significantly smaller than source. Verify integrity.")
            
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Default to finsight_test.db for the sprint
    src = "finsight_test.db"
    dest = "backups"
    backup_sqlite(src, dest)
