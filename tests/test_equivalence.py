"""Toate variantele din benchmark dau aceleasi rezultate pe baze initial identice."""

from pathlib import Path
import tempfile
import unittest

from benchmark.run import VARIANTS
from catalog.contract import CatalogError
from catalog.data import create_database


def scenario(catalog):
    """Secventa fixa de citiri si scrieri; intoarce tot ce s-a observat."""
    observed = [catalog.list_books(), catalog.search_books("00001"), catalog.get_book(7)]
    for operation, book_id in [("borrow", 7), ("borrow", 7), ("borrow", 12),
                               ("return", 7), ("return", 7), ("borrow", 999)]:
        method = catalog.borrow_book if operation == "borrow" else catalog.return_book
        try:
            method(book_id)
            observed.append((operation, book_id, "ok"))
        except CatalogError:
            observed.append((operation, book_id, "error"))
        observed.append(catalog.get_book(book_id))
    observed += [catalog.list_books(), catalog.search_books("")]
    return observed


class TestEquivalence(unittest.TestCase):
    def test_all_variants_match_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            results = {}
            for name, factory in VARIANTS.items():
                database = Path(directory) / f"{name}.db"
                create_database(database, 200)
                results[name] = scenario(factory(database))
                results[name].append(factory(database).list_books())
            for name, observed in results.items():
                with self.subTest(variant=name):
                    self.assertEqual(observed, results["baseline"])
