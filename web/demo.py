"""Date pentru demonstratia vizuala, separate de datele benchmark-ului."""

from contextlib import closing
from pathlib import Path
import sqlite3

from catalog.data import create_database


TITLES = [
    ("Enigma Otiliei", "George Călinescu"),
    ("Mândrie și prejudecată", "Jane Austen"),
    ("Povestea lui Harap-Alb", "Ion Creangă"),
    ("Metamorfoza", "Franz Kafka"),
    ("Pădurea spânzuraților", "Liviu Rebreanu"),
    ("O călătorie spre centrul Pământului", "Jules Verne"),
    ("Amintiri din copilărie", "Ion Creangă"),
    ("Crimă și pedeapsă", "F. M. Dostoievski"),
    ("Baltagul", "Mihail Sadoveanu"),
    ("Portretul lui Dorian Gray", "Oscar Wilde"),
    ("Ion", "Liviu Rebreanu"),
    ("Jane Eyre", "Charlotte Brontë"),
    ("Moara cu noroc", "Ioan Slavici"),
    ("Procesul", "Franz Kafka"),
    ("Douăzeci de mii de leghe sub mări", "Jules Verne"),
    ("Mara", "Ioan Slavici"),
    ("Marile speranțe", "Charles Dickens"),
    ("Moromeții", "Marin Preda"),
    ("Un studiu în roșu", "Arthur Conan Doyle"),
    ("Ultima noapte de dragoste, întâia noapte de război", "Camil Petrescu"),
    ("La răscruce de vânturi", "Emily Brontë"),
    ("O scrisoare pierdută", "I. L. Caragiale"),
    ("Mizerabilii", "Victor Hugo"),
    ("Călătorie în jurul lumii în 80 de zile", "Jules Verne"),
]


def create_demo(path: Path) -> None:
    create_database(path, len(TITLES))
    authors = list(dict.fromkeys(author for _, author in TITLES))
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("DELETE FROM books")
        connection.execute("DELETE FROM authors")
        connection.executemany("INSERT INTO authors VALUES (?, ?)", enumerate(authors, 1))
        connection.executemany(
            "INSERT INTO books VALUES (?, ?, ?, ?)",
            ((i, title, authors.index(author) + 1, int(i % 4 != 0))
             for i, (title, author) in enumerate(TITLES, 1)),
        )
