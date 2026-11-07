"""Referinta simpla, fara Repository/Facade/cache si fara N+1 intentionat."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3

from catalog.contract import Book, CatalogError


class BaselineCatalog:
    def __init__(self, database: Path):
        self.database = Path(database)
        self.query_count = 0

    def reset_metrics(self) -> None:
        self.query_count = 0

    def _trace(self, statement: str) -> None:
        if statement.strip().split()[0].upper() not in {"BEGIN", "COMMIT", "ROLLBACK"}:
            self.query_count += 1

    @contextmanager
    def _connection(self):
        # Conexiune per operatie, constanta in comparatiile etapei 1.
        connection = sqlite3.connect(f"{self.database.resolve().as_uri()}?mode=rw", uri=True)
        connection.set_trace_callback(self._trace)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _read(self, condition: str = "", parameters: tuple = ()) -> list[Book]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT b.id, b.title, a.name, b.available "
                "FROM books b JOIN authors a ON a.id = b.author_id "
                + condition + " ORDER BY b.id", parameters,
            ).fetchall()
        return [Book(row[0], row[1], row[2], bool(row[3])) for row in rows]

    def list_books(self) -> list[Book]:
        return self._read()

    def search_books(self, title: str) -> list[Book]:
        # Subsir literal; % si _ nu sunt wildcard-uri. Ignora cazul doar pentru ASCII.
        return self._read("WHERE instr(lower(b.title), lower(?)) > 0", (title,))

    def get_book(self, book_id: int) -> Book | None:
        books = self._read("WHERE b.id = ?", (book_id,))
        return books[0] if books else None

    def _set_available(self, book_id: int, available: bool) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE books SET available = ? WHERE id = ? AND available = ?",
                (int(available), book_id, int(not available)),
            )
            if cursor.rowcount != 1:
                raise CatalogError("Carte inexistenta sau stare incompatibila")

    def borrow_book(self, book_id: int) -> None:
        self._set_available(book_id, False)

    def return_book(self, book_id: int) -> None:
        self._set_available(book_id, True)
