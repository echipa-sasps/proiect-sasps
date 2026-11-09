# Etapa 1 — Persoana 2: Anti-pattern-uri și izolarea efectului N+1

Acest document descrie implementarea aferentă **Persoanei 2** din [docs/etapa-1.md](etapa-1.md), obiectivele experimentale urmărite, deciziile de proiectare și rezultatele obținute.

---

## 1. Obiectivul experimental

În cadrul Etapei 1, rolul Persoanei 2 este dublu:
1. **Modelarea anti-pattern-urilor *God Object* și *N+1 queries*** într-o clasă monolitică (`AntiPatternCatalog`) care respectă contractul comun [`Catalog`](../catalog/contract.py).
2. **Izolarea strictă a efectului strategiei SQL (`N+1` vs `JOIN`)** printr-o variantă de control (`AntiPatternJoinCatalog`) care păstrează aceeași structură monolitică, dar înlocuiește listarea `N+1` cu o singură interogare cu `JOIN`.

Astfel, comparația dintre `AntiPatternCatalog` și `AntiPatternJoinCatalog` măsoară exclusiv costul interogărilor `N+1`, fără a amesteca acest efect cu cel al reorganizării codului în clase separate (`Repository` / `Facade`).

---

## 2. Fișiere implementate

| Fișier | Rol |
|---|---|
| [`antipattern/__init__.py`](../antipattern/__init__.py) | Expune fabricile `AntiPatternCatalog` și `AntiPatternJoinCatalog` pentru teste și benchmark. |
| [`antipattern/catalog.py`](../antipattern/catalog.py) | Conține implementarea monolitică `AntiPatternCatalog` (God Object + N+1) și clasa de control `AntiPatternJoinCatalog` (God Object + JOIN). |
| [`tests/test_antipattern.py`](../tests/test_antipattern.py) | Suitele de teste `TestAntiPattern` și `TestAntiPatternJoin`, bazate pe mixin-ul comun `CatalogContract`. |
| [`rezultate/antipattern.csv`](../rezultate/antipattern.csv) | Măsurătorile brute (100, 1.000 și 10.000 de cărți, câte 10 repetări) pentru `antipattern` și `antipattern_join`. |

---

## 3. Detalii de implementare

### 3.1. `AntiPatternCatalog` — God Object și interogări N+1

Clasa `AntiPatternCatalog(database: Path)` cumulează intenționat cinci responsabilități distincte în același corp de clasă (anti-pattern-ul **God Object**):
1. **Gestionarea conexiunilor SQLite**: deschiderea și închiderea câte unei conexiuni per operație (`_connection()`).
2. **Instrumentarea metricilor SQL**: interceptarea instrucțiunilor SQL prin `connection.set_trace_callback(self._trace)` și contorizarea lor în `query_count` (excluzând `BEGIN`, `COMMIT`, `ROLLBACK`).
3. **Execuția directă a interogărilor SQL**: interogări `SELECT` și `UPDATE` scrise direct în metodele publice ale catalogului.
4. **Maparea datelor**: conversia tuplurilor returnate de SQLite în obiecte imuabile de domeniu `Book`.
5. **Logica de business pentru împrumut și returnare**: validarea disponibilității cărții și ridicarea excepției `CatalogError` la tranziții invalide sau ID-uri inexistente.

#### Cum este produs efectul N+1 în `list_books()`
La apelul `list_books()`:
1. Se execută o primă interogare pentru preluarea tuturor cărților ordonate după ID:
   ```sql
   SELECT id, title, author_id, available FROM books ORDER BY id
   ```
2. Pentru fiecare dintre cele $N$ cărți returnate, se execută în buclă câte o interogare individuală pentru preluarea numelui autorului (inclusiv atunci când același `author_id` se repetă la mai multe cărți):
   ```sql
   SELECT name FROM authors WHERE id = ?
   ```
- **Total interogări SQL executate**: $1 + N$ (de exemplu, `101` interogări pentru 100 de cărți, `1001` pentru 1.000 de cărți și `10001` pentru 10.000 de cărți).

#### Celelalte operații din contract
- `search_books(title)`: caută după subșir literal, fără wildcard-uri (`%` și `_` sunt tratate literal prin `instr(lower(b.title), lower(?)) > 0`), ignorând cazul pentru caracterele ASCII și returnând cărțile în ordine crescătoare după `id`.
- `get_book(book_id)`: preia detaliile unei cărți după ID sau returnează `None` dacă ID-ul nu există.
- `borrow_book(book_id)` și `return_book(book_id)`: execută actualizări condiționate (`UPDATE books SET available = 0/1 WHERE id = ? AND available = 1/0`) și ridică `CatalogError` dacă `cursor.rowcount != 1`.

### 3.2. `AntiPatternJoinCatalog` — Controlul experimental pentru SQL

Clasa `AntiPatternJoinCatalog` moștenește `AntiPatternCatalog` și păstrează neschimbată întreaga structură monolitică (aceeași clasă, aceeași politică de conexiuni și aceleași metode pentru căutare, detalii, împrumut și returnare), dar suprascrie **exclusiv** metoda `list_books()`:

```sql
SELECT b.id, b.title, a.name, b.available
FROM books b JOIN authors a ON a.id = b.author_id
ORDER BY b.id
```

Astfel, la listare se execută **exact 1 interogare SQL** în loc de $N+1$.

---

## 4. Verificare și teste (`tests/test_antipattern.py`)

Ambele clase sunt testate prin moștenirea mixin-ului `CatalogContract` din `tests/test_contract.py`, la care se adaugă teste specifice:
- **`TestAntiPattern`**:
  - Verifică toate cerințele funcționale ale contractului (ordonare, autori, căutare literală și protecție SQL injection, carte inexistentă, ciclu împrumut/returnare, resetare metrici).
  - `test_constructor_does_not_execute_sql`: confirmă că instanțierea nu execută interogări SQL (`query_count == 0`).
  - `test_listing_is_n_plus_one_queries`: confirmă că pe baza de test cu 100 de cărți, `list_books()` execută exact `101` interogări SQL.
- **`TestAntiPatternJoin`**:
  - Verifică toate cerințele din `CatalogContract`.
  - `test_constructor_does_not_execute_sql`: confirmă `query_count == 0` la inițializare.
  - `test_listing_is_one_query_and_matches_n_plus_one`: confirmă că `list_books()` execută exact `1` interogare SQL și returnează o listă de obiecte `Book` identică cu cea produsă de `AntiPatternCatalog`.

Rulare teste:
```powershell
python -m unittest tests.test_antipattern -v
```

---

## 5. Rezultate experimentale (`rezultate/antipattern.csv`)

Măsurătorile au fost generate cu:
```powershell
python -m benchmark.run --variants antipattern antipattern_join --output rezultate/antipattern.csv
```

### Comparație la listare (`list_books` — media pe 10 repetări)

| Volum ($N$ cărți) | Variantă | Interogări SQL (`sql_queries`) | Timp mediu (`elapsed_ms`) | Vârf alocări Python (`peak_python_kib`) |
|---|---|---|---|---|
| **100** | `antipattern` (N+1) | `101` | ~5.76 ms | ~33.1 KiB |
| **100** | `antipattern_join` (JOIN) | `1` | ~0.73 ms | 22.875 KiB |
| **1.000** | `antipattern` (N+1) | `1001` | ~51.70 ms | 259.809 KiB |
| **1.000** | `antipattern_join` (JOIN) | `1` | ~2.31 ms | 241.314 KiB |
| **10.000** | `antipattern` (N+1) | `10001` | ~510.25 ms | 3139.592 KiB |
| **10.000** | `antipattern_join` (JOIN) | `1` | ~18.19 ms | 3124.832 KiB |

### Constatări principale
- **Degradare liniară cu numărul de interogări**: în `AntiPatternCatalog`, timpul de listare crește de la ~5.76 ms (100 cărți) la ~51.70 ms (1.000 cărți) și ~510.25 ms (10.000 cărți).
- **Izolarea cauzei**: în `AntiPatternJoinCatalog`, păstrând exact aceeași clasă monolitică și aceeași conexiune per operație, înlocuirea celor $N+1$ interogări cu un singur `JOIN` reduce timpul de listare la 10.000 de cărți de la ~510 ms la ~18.2 ms (de ~28× mai rapid).
- **Control pe celelalte scenarii**: pentru `search_books` (1 interogare) și `get_book_repeated` (100 de interogări), ambele variante au număr identic de interogări și performanță similară.
