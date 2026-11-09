"""Implementare monolitica (God Object) cu interogari N+1 si controlul sau cu JOIN.

Responsabilitati amestecate intentionat in aceeasi clasa (AntiPatternCatalog):
1. Gestionarea ciclului de viata al conexiunii SQLite (deschidere/inchidere per operatie).
2. Instrumentarea si contorizarea instructiunilor SQL executate (query_count).
3. Scrierea si executia directa a interogarilor SQL pentru carti si autori.
4. Maparea randurilor SQL la obiectele de domeniu Book.
5. Validarea si aplicarea regulilor de imprumut si returnare direct peste baza de date.
"""

from contextlib import contextmanager
from pathlib import Path
import sqlite3

from catalog.contract import Book, CatalogError


class AntiPatternCatalog:
    """Monolit God Object care executa N+1 interogari la listarea cartilor."""

    def __init__(self, database: Path):
        self.database = Path(database)
        self.query_count = 0

    def reset_metrics(self) -> None:
        self.query_count = 0

    def _trace(self, statement: str) -> None:
        tokens = statement.strip().split()
        if tokens and tokens[0].upper() not in {"BEGIN", "COMMIT", "ROLLBACK"}:
            self.query_count += 1

    @contextmanager
    def _connection(self):
        # Conexiune per operatie, constanta in toate variantele etapei 1.
        connection = sqlite3.connect(f"{self.database.resolve().as_uri()}?mode=rw", uri=True)
        connection.set_trace_callback(self._trace)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def list_books(self) -> list[Book]:
        # Anti-pattern N+1: 1 SELECT pentru lista de carti + N SELECT-uri pentru autori,
        # inclusiv atunci cand acelasi autor apare la mai multe carti.
        with self._connection() as connection:
            book_rows = connection.execute(
                "SELECT id, title, author_id, available FROM books ORDER BY id"
            ).fetchall()
            books: list[Book] = []
            for book_id, title, author_id, available in book_rows:
                author_row = connection.execute(
                    "SELECT name FROM authors WHERE id = ?",
                    (author_id,),
                ).fetchone()
                author_name = author_row[0] if author_row is not None else ""
                books.append(Book(book_id, title, author_name, bool(available)))
            return books

    def search_books(self, title: str) -> list[Book]:
        # Subsir literal; % si _ nu sunt wildcard-uri. Ignora cazul doar pentru ASCII.
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT b.id, b.title, a.name, b.available "
                "FROM books b JOIN authors a ON a.id = b.author_id "
                "WHERE instr(lower(b.title), lower(?)) > 0 "
                "ORDER BY b.id",
                (title,),
            ).fetchall()
        return [Book(row[0], row[1], row[2], bool(row[3])) for row in rows]

    def get_book(self, book_id: int) -> Book | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT b.id, b.title, a.name, b.available "
                "FROM books b JOIN authors a ON a.id = b.author_id "
                "WHERE b.id = ?",
                (book_id,),
            ).fetchone()
        if row is None:
            return None
        return Book(row[0], row[1], row[2], bool(row[3]))

    def borrow_book(self, book_id: int) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE books SET available = 0 WHERE id = ? AND available = 1",
                (book_id,),
            )
            if cursor.rowcount != 1:
                raise CatalogError("Carte inexistenta sau deja imprumutata")

    def return_book(self, book_id: int) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE books SET available = 1 WHERE id = ? AND available = 0",
                (book_id,),
            )
            if cursor.rowcount != 1:
                raise CatalogError("Carte inexistenta sau deja disponibila")


class AntiPatternJoinCatalog(AntiPatternCatalog):
    """Control experimental monolitic: pastreaza God Object-ul, dar inlocuieste N+1 cu JOIN la listare."""

    def list_books(self) -> list[Book]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT b.id, b.title, a.name, b.available "
                "FROM books b JOIN authors a ON a.id = b.author_id "
                "ORDER BY b.id"
            ).fetchall()
        return [Book(row[0], row[1], row[2], bool(row[3])) for row in rows]
