from pathlib import Path
import tempfile
import unittest

from catalog.contract import Book, CatalogError
from catalog.data import create_database
from pattern.repository import BookRepository
from pattern.service import LibraryService
from tests.test_contract import CatalogContract


class TestLibraryService(CatalogContract, unittest.TestCase):
    """Verifica faptul ca Facade + Repository respecta contractul comun."""

    factory = LibraryService

    def test_constructor_does_not_execute_sql(self):
        fresh = LibraryService(self.database)
        self.assertEqual(fresh.query_count, 0)

    def test_listing_is_one_query(self):
        books = self.catalog.list_books()
        self.assertEqual(len(books), 100)
        self.assertEqual(self.catalog.query_count, 1)

    def test_service_accepts_injected_repository(self):
        custom_repo = BookRepository(self.database)
        service = LibraryService(self.database, repository=custom_repo)
        self.assertIs(service.repository, custom_repo)
        book = service.get_book(1)
        self.assertEqual(book, Book(1, "Carte 000001", "Autor 0001", True))
        self.assertEqual(service.query_count, 1)
        self.assertEqual(custom_repo.query_count, 1)


class TestBookRepository(unittest.TestCase):
    """Verifica separat BookRepository pe o baza temporara reala."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "repo_test.db"
        create_database(self.database, 25)
        self.repo = BookRepository(self.database)

    def test_constructor_does_not_execute_sql(self):
        fresh = BookRepository(self.database)
        self.assertEqual(fresh.query_count, 0)

    def test_list_search_and_get_with_single_queries(self):
        books = self.repo.list_books()
        self.assertEqual(len(books), 25)
        self.assertEqual(self.repo.query_count, 1)
        self.assertEqual(books[0], Book(1, "Carte 000001", "Autor 0001", True))

        self.repo.reset_metrics()
        found = self.repo.search_books("000005")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, 5)
        self.assertEqual(self.repo.query_count, 1)

        self.repo.reset_metrics()
        detail = self.repo.get_book(5)
        self.assertEqual(detail, found[0])
        self.assertIsNone(self.repo.get_book(999))
        self.assertEqual(self.repo.query_count, 2)

    def test_conditional_set_available(self):
        # Imprumut reusit (available: 1 -> 0)
        self.assertTrue(self.repo.set_available(1, False))
        self.assertFalse(self.repo.get_book(1).available)
        # Al doilea imprumut esueaza conditionat fara a modifica starea
        self.assertFalse(self.repo.set_available(1, False))
        # Returnare reusita (available: 0 -> 1)
        self.assertTrue(self.repo.set_available(1, True))
        self.assertTrue(self.repo.get_book(1).available)
        # A doua returnare esueaza conditionat
        self.assertFalse(self.repo.set_available(1, True))
        # ID inexistent esueaza conditionat
        self.assertFalse(self.repo.set_available(999, False))
        self.assertFalse(self.repo.set_available(999, True))
