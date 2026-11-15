from pathlib import Path
import tempfile
import unittest

from baseline.catalog import BaselineCatalog
from catalog.contract import Book, CatalogError
from catalog.data import create_database


class CatalogContract:
    """Mixin reutilizabil: fiecare coleg defineste factory in propria clasa TestCase."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "catalog.db"
        create_database(self.database, 100)
        self.catalog = self.factory(self.database)

    def test_list_includes_author_and_order(self):
        books = self.catalog.list_books()
        self.assertEqual(len(books), 100)
        self.assertEqual([book.id for book in books], list(range(1, 101)))
        self.assertEqual(books[0], Book(1, "Carte 000001", "Autor 0001", True))
        self.assertEqual(books[10].author, "Autor 0001")

    def test_search_literal_and_case(self):
        self.assertEqual(self.catalog.search_books("cArTe 000001"), [self.catalog.get_book(1)])
        self.assertEqual(self.catalog.search_books("%"), [])
        self.assertEqual(self.catalog.search_books("_"), [])
        self.assertEqual(self.catalog.search_books("' OR 1=1 --"), [])
        self.assertEqual(self.catalog.search_books(""), self.catalog.list_books())

    def test_missing_book(self):
        self.assertIsNone(self.catalog.get_book(999))
        for operation in (self.catalog.borrow_book, self.catalog.return_book):
            with self.assertRaises(CatalogError):
                operation(999)

    def test_borrow_return_and_fresh_reads(self):
        self.assertTrue(self.catalog.get_book(1).available)
        self.catalog.borrow_book(1)
        self.assertFalse(self.catalog.get_book(1).available)
        self.assertFalse(self.catalog.list_books()[0].available)
        self.assertFalse(self.catalog.search_books("000001")[0].available)
        with self.assertRaises(CatalogError):
            self.catalog.borrow_book(1)
        self.catalog.return_book(1)
        self.assertTrue(self.catalog.get_book(1).available)
        with self.assertRaises(CatalogError):
            self.catalog.return_book(1)

    def test_metrics_reset(self):
        self.catalog.list_books()
        self.assertGreater(self.catalog.query_count, 0)
        self.catalog.reset_metrics()
        self.assertEqual(self.catalog.query_count, 0)


class TestBaseline(CatalogContract, unittest.TestCase):
    factory = BaselineCatalog

    def test_listing_is_one_query(self):
        self.catalog.list_books()
        self.assertEqual(self.catalog.query_count, 1)

    def test_generator_protects_existing_database(self):
        with self.assertRaises(FileExistsError):
            create_database(self.database, 10)
        self.assertEqual(len(self.catalog.list_books()), 100)

    def test_generator_is_reproducible(self):
        other = Path(self.directory.name) / "other.db"
        create_database(other, 100)
        self.assertEqual(self.catalog.list_books(), BaselineCatalog(other).list_books())
