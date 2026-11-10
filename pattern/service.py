"""Pattern-ul Facade (LibraryService) peste nivelul Repository.

Rolul Facade in aceasta arhitectura:
- Ofera clientilor (UI, teste, benchmark) interfata unica Catalog, ascunzand
  implementarea accesului la date (BookRepository sau un Proxy cu cache).
- Coordoneaza operatiile de domeniu (imprumut si returnare) si transforma
  rezultatul actualizarilor conditionate din repository in exceptii de domeniu
  (CatalogError), fara a contine instructiuni SQL.
- Permite injectarea unui Repository alternativ (ex. Proxy-ul cu cache al
  Persoanei 4) fara modificarea codului client.

Observatie metodologica (etapa 1):
In absenta cache-ului sau a mai multor surse de date, serviciul deleaga citirile
direct catre un singur repository; costul acestei separari (indirestie suplimentara
si numar de clase) este masurat explicit fata de BaselineCatalog si AntiPatternJoinCatalog.
"""

from pathlib import Path

from catalog.contract import Book, CatalogError
from pattern.repository import BookRepository, Repository


class LibraryService:
    """Facade care coordoneaza operatiile catalogului fara a contine SQL."""

    def __init__(self, database: Path, *, repository: Repository | None = None):
        self.database = Path(database)
        self.repository: Repository = (
            repository if repository is not None else BookRepository(self.database)
        )

    @property
    def query_count(self) -> int:
        return self.repository.query_count

    def reset_metrics(self) -> None:
        self.repository.reset_metrics()

    def list_books(self) -> list[Book]:
        return self.repository.list_books()

    def search_books(self, title: str) -> list[Book]:
        return self.repository.search_books(title)

    def get_book(self, book_id: int) -> Book | None:
        return self.repository.get_book(book_id)

    def borrow_book(self, book_id: int) -> None:
        if not self.repository.set_available(book_id, False):
            raise CatalogError("Carte inexistenta sau deja imprumutata")

    def return_book(self, book_id: int) -> None:
        if not self.repository.set_available(book_id, True):
            raise CatalogError("Carte inexistenta sau deja disponibila")
