from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str
    available: bool


class CatalogError(ValueError):
    """Carte inexistenta sau tranzitie de imprumut invalida."""


class Catalog(Protocol):
    # Numarul instructiunilor SQL ale operatiilor, fara BEGIN/COMMIT/ROLLBACK.
    query_count: int

    def reset_metrics(self) -> None: ...
    def list_books(self) -> list[Book]: ...
    def search_books(self, title: str) -> list[Book]: ...
    def get_book(self, book_id: int) -> Book | None: ...
    def borrow_book(self, book_id: int) -> None: ...
    def return_book(self, book_id: int) -> None: ...
