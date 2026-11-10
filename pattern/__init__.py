"""Implementari bazate pe pattern-uri de proiectare: Repository si Facade."""

from pattern.repository import BookRepository, Repository
from pattern.service import LibraryService

__all__ = ["BookRepository", "LibraryService", "Repository"]
