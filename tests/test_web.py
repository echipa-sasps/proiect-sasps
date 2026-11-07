from pathlib import Path
import re
import tempfile
import unittest

from baseline.catalog import BaselineCatalog
from web.app import create_app
from web.demo import create_demo


class TestWeb(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "demo.db"
        create_demo(self.database)
        self.app = create_app(self.database)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def token(self):
        response = self.client.get("/")
        return re.search(r'name="csrf_token" value="([^"]+)"',
                         response.get_data(as_text=True)).group(1)

    def test_home_is_paginated_and_assets_are_local(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Enigma Otiliei", html)
        self.assertNotIn("Baltagul", html)
        self.assertIn("1–8", html)
        for asset in ("style.css", "favicon.svg"):
            with self.client.get("/static/" + asset) as response:
                self.assertEqual(response.status_code, 200)
        second = self.client.get("/?page=2").get_data(as_text=True)
        self.assertIn("Baltagul", second)
        self.assertNotIn("Enigma Otiliei", second)

    def test_search_and_filters(self):
        html = self.client.get("/?q=Enigma").get_data(as_text=True)
        self.assertIn("Enigma Otiliei", html)
        self.assertNotIn("Metamorfoza", html)
        html = self.client.get("/?status=borrowed").get_data(as_text=True)
        self.assertIn("Metamorfoza", html)
        self.assertNotIn("Enigma Otiliei", html)

    def test_empty_search_and_invalid_page(self):
        html = self.client.get("/?q=titlu-inexistent").get_data(as_text=True)
        self.assertIn("Nicio carte", html)
        for query in ("page=abc", "page=-1", "page=999999", "status=invalid"):
            self.assertEqual(self.client.get("/?" + query).status_code, 200)

    def test_details_and_missing_book(self):
        html = self.client.get("/carti/1").get_data(as_text=True)
        self.assertIn("George Călinescu", html)
        self.assertEqual(self.client.get("/carti/999").status_code, 404)

    def test_borrow_return_persist_and_keep_detail_view(self):
        token = self.token()
        for action, expected in (("imprumuta", False), ("returneaza", True)):
            response = self.client.post(f"/carti/1/{action}", data={
                "csrf_token": token, "view": "detail",
            })
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.location, "/carti/1")
            self.assertEqual(BaselineCatalog(self.database).get_book(1).available, expected)

    def test_invalid_transition_shows_message(self):
        token = self.token()
        response = self.client.post("/carti/1/returneaza", data={
            "csrf_token": token,
        }, follow_redirects=True)
        self.assertIn("Operația nu a putut fi efectuată", response.get_data(as_text=True))
        self.assertTrue(BaselineCatalog(self.database).get_book(1).available)

    def test_mutations_require_post_and_token(self):
        self.assertEqual(self.client.get("/carti/1/imprumuta").status_code, 405)
        self.assertEqual(self.client.post("/carti/1/imprumuta").status_code, 400)
        self.assertTrue(BaselineCatalog(self.database).get_book(1).available)

    def test_search_query_is_escaped(self):
        html = self.client.get("/", query_string={"q": '<script>alert(1)</script>'}).get_data(as_text=True)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_mutation_keeps_search_filter_and_page(self):
        response = self.client.post("/carti/1/imprumuta", data={
            "csrf_token": self.token(), "q": "Enigma", "status": "available", "page": "2",
        })
        self.assertEqual(response.status_code, 303)
        self.assertIn("q=Enigma", response.location)
        self.assertIn("status=available", response.location)
        self.assertIn("page=2", response.location)

    def test_alternative_factory_uses_same_ui(self):
        calls = []

        def factory(path):
            calls.append(path)
            return BaselineCatalog(path)

        app = create_app(self.database, catalog_factory=factory)
        client = app.test_client()
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(client.get("/carti/1").status_code, 200)
        self.assertEqual(calls, [self.database])
