"""
Automatic backup system for critical data.
"""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from datetime import datetime
import threading


class BackupManager:
    """Manages automatic backups of critical data."""
    
    def __init__(self, backup_dir: str = "data/backups", max_backups: int = 10):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups
        self._running = False
        self._thread = None
    
    def backup_file(self, file_path: str, category: str = "general") -> bool:
        """
        Create a timestamped backup of a file.
        
        Args:
            file_path: Path to file to backup
            category: Category folder for organizing backups
        
        Returns:
            True if backup successful
        """
        try:
            source = Path(file_path)
            if not source.exists():
                return False
            
            # Create category subdirectory
            cat_dir = self.backup_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source.stem}_{timestamp}{source.suffix}"
            backup_path = cat_dir / backup_name
            
            shutil.copy2(source, backup_path)
            
            # Clean old backups
            self._clean_old_backups(cat_dir, source.stem)
            
            return True
        except Exception as e:
            print(f"Backup failed for {file_path}: {e}")
            return False
    
    def _clean_old_backups(self, directory: Path, file_stem: str):
        """Remove old backups, keeping only max_backups most recent."""
        try:
            # Get all backups for this file
            pattern = f"{file_stem}_*"
            backups = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
            
            # Remove oldest if we exceed max
            while len(backups) > self.max_backups:
                oldest = backups.pop(0)
                oldest.unlink()
        except Exception:
            pass
    
    def backup_databases(self):
        """Backup all database files."""
        self.backup_file("data/eve_arbitrage.db", "databases")
        self.backup_file("data/wormholes.db", "databases")
    
    def backup_config(self):
        """Backup configuration files."""
        self.backup_file("config.yaml", "config")
        self.backup_file("data/token.json", "config")
        self.backup_file("data/twitch_config.json", "config")
    
    def start_auto_backup(self, interval_hours: int = 6):
        """Start automatic backup thread."""
        if self._running:
            return
        
        self._running = True
        
        def _backup_loop():
            while self._running:
                try:
                    self.backup_databases()
                    self.backup_config()
                except Exception as e:
                    print(f"Auto-backup error: {e}")
                
                # Sleep for interval (check every minute for stop signal)
                for _ in range(interval_hours * 60):
                    if not self._running:
                        break
                    time.sleep(60)
        
        self._thread = threading.Thread(target=_backup_loop, daemon=True)
        self._thread.start()
    
    def stop_auto_backup(self):
        """Stop automatic backup thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def restore_backup(self, backup_path: str, destination: str) -> bool:
        """
        Restore a backup file.
        
        Args:
            backup_path: Path to backup file
            destination: Where to restore to
        
        Returns:
            True if restore successful
        """
        try:
            backup = Path(backup_path)
            dest = Path(destination)
            
            if not backup.exists():
                return False
            
            # Create backup of current file before restoring
            if dest.exists():
                temp_backup = dest.parent / f"{dest.name}.pre-restore"
                shutil.copy2(dest, temp_backup)
            
            shutil.copy2(backup, dest)
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def list_backups(self, category: str = None) -> list[dict]:
        """List all available backups."""
        backups = []
        
        search_dirs = [self.backup_dir / category] if category else list(self.backup_dir.iterdir())
        
        for dir_path in search_dirs:
            if not dir_path.is_dir():
                continue
            
            for backup_file in dir_path.glob("*"):
                if backup_file.is_file():
                    stat = backup_file.stat()
                    backups.append({
                        "path": str(backup_file),
                        "name": backup_file.name,
                        "category": dir_path.name,
                        "size_bytes": stat.st_size,
                        "created_at": stat.st_mtime,
                        "created_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    })
        
        return sorted(backups, key=lambda b: b["created_at"], reverse=True)


# Global backup manager instance
_backup_manager = None


def get_backup_manager() -> BackupManager:
    """Get or create global backup manager instance."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
