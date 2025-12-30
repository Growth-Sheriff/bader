"""
BADER Core Module
Lisans yönetimi, veritabanı adaptörü ve otomatik güncelleme
"""

from .license_manager import LicenseManager, LicenseInfo, LicenseError
from .database_adapter import DatabaseAdapter, SQLiteBackend, APIBackend, HybridBackend, DatabaseError
from .auto_updater import AutoUpdater, UpdateInfo, UpdateError

__all__ = [
    # License
    "LicenseManager",
    "LicenseInfo", 
    "LicenseError",
    
    # Database
    "DatabaseAdapter",
    "SQLiteBackend",
    "APIBackend",
    "HybridBackend",
    "DatabaseError",
    
    # Updater
    "AutoUpdater",
    "UpdateInfo",
    "UpdateError"
]

__version__ = "1.0.0"
