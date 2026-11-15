"""Implementari bazate pe pattern-uri de proiectare: Repository, Facade si Proxy."""

from pattern.repository import BookRepository, Repository
from pattern.service import LibraryService
from pattern.cache_proxy import CachedLibraryService, CachingBookRepository

__all__ = [
    "BookRepository", "CachedLibraryService", "CachingBookRepository",
    "LibraryService", "Repository",
]
