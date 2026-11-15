import unittest

from antipattern.catalog import AntiPatternCatalog, AntiPatternJoinCatalog
from tests.test_contract import CatalogContract


class TestAntiPattern(CatalogContract, unittest.TestCase):
    factory = AntiPatternCatalog

    def test_constructor_does_not_execute_sql(self):
        fresh = AntiPatternCatalog(self.database)
        self.assertEqual(fresh.query_count, 0)

    def test_listing_is_n_plus_one_queries(self):
        books = self.catalog.list_books()
        self.assertEqual(len(books), 100)
        # 1 interogare pentru lista de carti + 100 de interogari pentru autori (chiar daca autorii se repeta)
        self.assertEqual(self.catalog.query_count, 101)


class TestAntiPatternJoin(CatalogContract, unittest.TestCase):
    factory = AntiPatternJoinCatalog

    def test_constructor_does_not_execute_sql(self):
        fresh = AntiPatternJoinCatalog(self.database)
        self.assertEqual(fresh.query_count, 0)

    def test_listing_is_one_query_and_matches_n_plus_one(self):
        books = self.catalog.list_books()
        self.assertEqual(len(books), 100)
        self.assertEqual(self.catalog.query_count, 1)
        self.assertEqual(books, AntiPatternCatalog(self.database).list_books())
