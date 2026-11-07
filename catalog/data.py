"""Generator determinist. Nu suprascrie implicit o baza existenta."""

import argparse
from contextlib import closing
from pathlib import Path
import sqlite3


def create_database(path: Path, books: int, *, overwrite: bool = False) -> None:
    if books < 1:
        raise ValueError("Numarul de carti trebuie sa fie pozitiv")
    path = Path(path)
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Baza exista deja: {path}")
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    authors = max(1, min(100, books // 10))
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author_id INTEGER NOT NULL REFERENCES authors(id),
                available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0, 1))
            );
        """)
        connection.executemany(
            "INSERT INTO authors VALUES (?, ?)",
            ((i, f"Autor {i:04d}") for i in range(1, authors + 1)),
        )
        connection.executemany(
            "INSERT INTO books VALUES (?, ?, ?, 1)",
            ((i, f"Carte {i:06d}", (i - 1) % authors + 1)
             for i in range(1, books + 1)),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--books", type=int, default=1000)
    parser.add_argument("--path", type=Path, default=Path("date/catalog.db"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    create_database(args.path, args.books, overwrite=args.overwrite)
    print(f"Creat: {args.path}, {args.books} carti")


if __name__ == "__main__":
    main()
