"""Shared dependency overrides for routers."""
from app.core.database import get_db

__all__ = ["get_db"]

