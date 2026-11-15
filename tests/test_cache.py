import unittest

from catalog.contract import Book, CatalogError
from pattern.cache_proxy import CachedLibraryService, CachingBookRepository
from pattern.repository import BookRepository
from tests.test_contract import CatalogContract


class FakeRepository:
    """Repository in memorie: numara apelurile fara SQLite."""

    def __init__(self):
        self.books = {1: Book(1, "Carte 000001", "Autor 0001", True),
                      2: Book(2, "Carte 000002", "Autor 0002", True)}
        self.query_count = 0

    def reset_metrics(self):
        self.query_count = 0

    def list_books(self):
        self.query_count += 1
        return [self.books[key] for key in sorted(self.books)]

    def search_books(self, title):
        self.query_count += 1
        return [book for book in self.list_books() if title.lower() in book.title.lower()]

    def get_book(self, book_id):
        self.query_count += 1
        return self.books.get(book_id)

    def set_available(self, book_id, available):
        self.query_count += 1
        book = self.books.get(book_id)
        if book is None or book.available == available:
            return False
        self.books[book_id] = Book(book.id, book.title, book.author, available)
        return True


class TestCachingRepositoryWithFake(unittest.TestCase):
    def setUp(self):
        self.inner = FakeRepository()
        self.proxy = CachingBookRepository(self.inner)

    def test_first_read_is_miss_then_hits(self):
        for _ in range(5):
            self.assertEqual(self.proxy.get_book(1), self.inner.books[1])
        self.assertEqual((self.proxy.misses, self.proxy.hits), (1, 4))
        self.assertEqual(self.inner.query_count, 1)

    def test_missing_book_is_not_cached(self):
        self.assertIsNone(self.proxy.get_book(99))
        self.assertIsNone(self.proxy.get_book(99))
        self.assertEqual(self.proxy.misses, 2)
        self.assertEqual(len(self.proxy), 0)

    def test_list_and_search_are_delegated(self):
        self.proxy.list_books()
        self.proxy.list_books()
        self.assertEqual(self.inner.query_count, 2)
        self.assertEqual(len(self.proxy), 0)

    def test_write_invalidates_only_affected_entry(self):
        self.proxy.get_book(1)
        self.proxy.get_book(2)
        self.assertTrue(self.proxy.set_available(1, False))
        self.assertEqual(len(self.proxy), 1)
        self.assertFalse(self.proxy.get_book(1).available)
        self.assertEqual(self.proxy.misses, 3)

    def test_reset_metrics_keeps_cache(self):
        self.proxy.get_book(1)
        self.proxy.reset_metrics()
        self.proxy.get_book(1)
        self.assertEqual(self.proxy.query_count, 0)
        self.assertEqual(self.proxy.hits, 1)


class TestCachedLibraryService(CatalogContract, unittest.TestCase):
    factory = CachedLibraryService

    def test_constructor_does_not_execute_sql(self):
        self.assertEqual(CachedLibraryService(self.database).query_count, 0)

    def test_listing_is_one_query(self):
        self.catalog.list_books()
        self.assertEqual(self.catalog.query_count, 1)

    def test_repeated_reads_use_one_query(self):
        books = [self.catalog.get_book(1) for _ in range(100)]
        self.assertEqual(len(set(books)), 1)
        self.assertEqual(self.catalog.query_count, 1)

    def test_read_after_write_hits_database_again(self):
        self.catalog.get_book(1)
        self.catalog.borrow_book(1)
        self.catalog.reset_metrics()
        self.assertFalse(self.catalog.get_book(1).available)
        self.assertEqual(self.catalog.query_count, 1)

    def test_failed_write_keeps_correct_state(self):
        self.catalog.borrow_book(1)
        self.catalog.get_book(1)
        with self.assertRaises(CatalogError):
            self.catalog.borrow_book(1)
        self.assertFalse(self.catalog.get_book(1).available)

    def test_injected_repository_is_wrapped(self):
        inner = BookRepository(self.database)
        service = CachedLibraryService(self.database, repository=inner)
        service.get_book(1)
        service.get_book(1)
        self.assertEqual(inner.query_count, 1)
