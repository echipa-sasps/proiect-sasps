"""Proxy cu cache peste Repository.

Pastreaza in memorie doar detaliile dupa ID. Listarea si cautarea sunt delegate.
Cache-ul este local instantei: modificarile facute prin alte instante sau direct
in baza nu sunt vazute (limitare asumata in etapa 1).
"""

from pathlib import Path

from catalog.contract import Book
from pattern.repository import BookRepository, Repository
from pattern.service import LibraryService


class CachingBookRepository:
    """Aceeasi interfata ca BookRepository, cu cache pentru get_book."""

    def __init__(self, repository: Repository):
        self._repository = repository
        self._cache: dict[int, Book] = {}
        self.hits = 0
        self.misses = 0

    @property
    def query_count(self) -> int:
        return self._repository.query_count

    def reset_metrics(self) -> None:
        # Reseteaza doar contoarele, nu si cache-ul.
        self._repository.reset_metrics()
        self.hits = 0
        self.misses = 0

    def list_books(self) -> list[Book]:
        return self._repository.list_books()

    def search_books(self, title: str) -> list[Book]:
        return self._repository.search_books(title)

    def get_book(self, book_id: int) -> Book | None:
        book = self._cache.get(book_id)
        if book is not None:
            self.hits += 1
            return book
        self.misses += 1
        book = self._repository.get_book(book_id)
        # Rezultatele inexistente nu se pastreaza.
        if book is not None:
            self._cache[book_id] = book
        return book

    def set_available(self, book_id: int, available: bool) -> bool:
        changed = self._repository.set_available(book_id, available)
        self._cache.pop(book_id, None)
        return changed

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


class CachedLibraryService(LibraryService):
    """Fabrica pentru benchmark: LibraryService cu Proxy-ul de cache injectat."""

    def __init__(self, database: Path, *, repository: Repository | None = None):
        inner = repository if repository is not None else BookRepository(Path(database))
        super().__init__(database, repository=CachingBookRepository(inner))
