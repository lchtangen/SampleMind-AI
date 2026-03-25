"""
data/repositories — Repository pattern for database access.

All database operations go through these static-method classes, never through
raw SQLite connections or the legacy data/database.py module.

Exports:
  SampleRepository — CRUD for the `samples` table
  UserRepository   — CRUD for the `users` table
"""

from .sample_repository import SampleRepository
from .user_repository import UserRepository

__all__ = ["SampleRepository", "UserRepository"]
