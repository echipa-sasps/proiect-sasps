# SASPS – Catalog de bibliotecă

## Starea implementării — etapa 1

### Nucleul și experimentele

Planul concret pentru cele 4 persoane, contractul comun și criteriile primului
milestone sunt în [docs/etapa-1.md](docs/etapa-1.md).

Implementat acum (persoana 1): generator determinist SQLite, contract comun,
variantă simplă de referință în `baseline/`, teste reutilizabile și benchmark.
Implementările cu anti-pattern-uri și pattern-uri urmează conform planului.
Secțiunile de mai jos descriu propunerea generală, nu funcționalități deja livrate;
ipotezele despre avantaje vor fi verificate experimental.

Rulare din rădăcina repo-ului cu Python 3.10+. Nucleul și benchmark-ul nu
necesită pachete externe; interfața web și testele ei necesită Flask:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m catalog.data --books 1000 --path date/catalog.db
python -m unittest tests.test_contract -v
python -m benchmark.run --sizes 100 1000 10000 --repeats 10
```

### Interfața web locală

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m web
```

Deschide **http://127.0.0.1:5000** în browser. Oprești serverul cu `Ctrl+C`.
La prima pornire se creează `date/demo.db`, cu 24 de cărți și autori pentru
demonstrație. Modificările de disponibilitate se păstrează între porniri.
Datele demonstrative sunt separate de datele sintetice din benchmark.

Interfața include căutare după titlu, filtre de disponibilitate, pagini de câte
8 cărți, fișa cărții și operații de împrumut/returnare. Folosește momentan
baseline-ul. Alte implementări se pot injecta în `web.app.create_app` prin
`catalog_factory`, fără schimbarea paginilor HTML.

Pentru o bază deja generată sau un alt port:

```bash
python -m web --database date/catalog.db --port 5001
```

Testarea completă, după instalarea Flask:

```bash
python -m unittest discover -v
```

# Studiu comparativ: pattern-uri de acces la date vs anti-pattern-uri

Această secțiune păstrează propunerea inițială a proiectului. Planul actualizat
și delimitarea experimentelor sunt în [docs](docs/README.md); tabelele de mai
jos nu reprezintă rezultate experimentale sau implementări deja disponibile.

## Descriere

Proiectul compară efectul pattern-urilor de proiectare și al anti-pattern-urilor asupra **performanței**, **scalabilității**, **consumului de resurse** și **mentenabilității** unei aplicații care lucrează cu o bază de date.

Aplicația este un catalog simplu de bibliotecă: cărți, autori și împrumuturi, stocate în SQLite. Aceleași funcționalități sunt implementate de două ori:

- **varianta anti-pattern** – probleme deliberate, precum N+1 și responsabilități amestecate;
- **varianta cu pattern-uri** – același comportament, organizat cu pattern-uri de proiectare.

Variantele vor rula pe aceleași date și vor respecta același contract.
O referință simplă (`baseline`) și controale intermediare vor separa efectele
SQL-ului, cache-ului și organizării codului; simpla folosire a acelorași teste
nu izolează toate aceste contribuții.

## Obiective

- Prezentarea originii și evoluției pattern-urilor de proiectare (GoF, Fowler – *Patterns of Enterprise Application Architecture*).
- Măsurarea impactului pattern-urilor asupra timpului de răspuns, memoriei și numărului de interogări.
- Observarea comportamentului la creșterea volumului de date (scalabilitate).
- Compararea pattern-urilor între ele, nu doar cu anti-pattern-urile.
- Evaluarea mentenabilității prin metrici de cod și prin efortul de a adăuga o funcționalitate nouă.

## Funcționalități

1. Listarea cărților împreună cu autorul fiecăreia.
2. Căutarea cărților după titlu.
3. Afișarea detaliilor unei cărți (citită des – candidat pentru cache).
4. Împrumutarea și returnarea unei cărți.

## Anti-pattern-uri analizate

| Anti-pattern | Ce face | Efect așteptat |
|---|---|---|
| **N+1 queries** | o interogare pentru lista de cărți, apoi câte o interogare pentru autorul fiecărei cărți | timpul crește liniar cu numărul de cărți |
| **Conexiune per cerere** | deschide și închide o conexiune la fiecare operație | timp pierdut la deschiderea conexiunilor |
| **Fără cache** | citește din baza de date aceeași carte la fiecare cerere | interogări repetate inutil |
| **God Object** | o singură clasă `Biblioteca` conține SQL, logică și afișare | cod greu de modificat și de testat |

## Pattern-uri analizate

| Pattern | Sursă | Unde e folosit | Rezolvă anti-pattern-ul |
|---|---|---|---|
| **Repository** | Fowler (PoEAA) | `CarteRepository`, `AutorRepository` – tot SQL-ul stă aici, cu `JOIN` în loc de N+1 | N+1, God Object |
| **Object Pool** | creațional | un număr fix de conexiuni refolosite | Conexiune per cerere |
| **Singleton** | GoF, creațional | o singură conexiune partajată (comparată cu Object Pool) | Conexiune per cerere |
| **Proxy (cache)** | GoF, structural | `CarteRepositoryCuCache` are aceeași interfață ca repository-ul, dar ține rezultatele în memorie | Fără cache |
| **Facade** | GoF, structural | `ServiciuBiblioteca` oferă operațiile de mai sus, ascunzând repository-urile și pool-ul | God Object |

## Comparații între pattern-uri

- **Singleton vs Object Pool** – Singleton e mai simplu, dar o singură conexiune devine punct de blocaj când apar mai multe fire de execuție. Object Pool e mai complex, dar scalează mai bine.
- **Proxy cu cache vs fără cache** – cache-ul reduce mult timpul la citiri repetate, dar consumă memorie și poate întoarce date vechi după o modificare.
- **Repository vs God Object** – Repository adaugă clase, dar fiecare are o singură responsabilitate și poate fi testată separat.

Lucrarea discută și când un pattern **nu** merită folosit (de exemplu, cache pe date care se schimbă des sau pool pentru o aplicație cu un singur utilizator).

## Metodologie de evaluare

Toate măsurătorile se fac pe 100, 1.000, 10.000 și 50.000 de cărți, generate automat. Fiecare test se repetă de 10 ori și se raportează media.

| Criteriu | Metrică | Unealtă |
|---|---|---|
| Performanță | timp de răspuns (ms) | `time.perf_counter` |
| Optimizarea resurselor | memorie maximă (KB), număr de interogări SQL | `tracemalloc`, contor de interogări |
| Scalabilitate | evoluția timpului la creșterea datelor; rulare cu 1, 4 și 8 fire de execuție | script de benchmark |
| Mentenabilitate | complexitate ciclomatică, indice de mentenabilitate, linii pe clasă | `radon` |
| Extensibilitate | fișiere și linii modificate pentru a adăuga „căutare după autor” | `git diff --stat` |
| Corectitudine | ambele variante dau aceleași rezultate | `pytest` |

Rezultatele se salvează în `rezultate/rezultate.csv`, iar graficele în `rezultate/grafice/`.

## Structura proiectului

```
catalog-biblioteca/
├── date/
│   └── genereaza_date.py        # creează baza SQLite cu N cărți
├── antipattern/
│   └── biblioteca.py            # God Object + N+1 + conexiune per cerere
├── pattern/
│   ├── conexiuni.py             # Singleton și Object Pool
│   ├── repository.py            # CarteRepository, AutorRepository
│   ├── cache_proxy.py           # CarteRepositoryCuCache
│   └── serviciu.py              # ServiciuBiblioteca (Facade)
├── benchmark/
│   ├── ruleaza_benchmark.py     # măsoară timp, memorie, interogări
│   └── grafice.py               # desenează graficele din CSV
├── tests/
│   └── test_echivalenta.py      # verifică rezultate identice
├── rezultate/
└── README.md
```

## Tehnologii

- **Python 3.10+** și **SQLite** (inclus în Python, nu necesită instalare)
- **pytest** – teste automate
- **radon** – metrici de mentenabilitate
- **matplotlib** – grafice
- **Git și GitHub** – versionare

## Rulare

```bash
pip install pytest radon matplotlib
python date/genereaza_date.py --carti 10000
pytest
python benchmark/ruleaza_benchmark.py
python benchmark/grafice.py
radon cc antipattern pattern -s -a
radon mi antipattern pattern -s
```

## Legătura cu structura lucrării

| Capitol | Ce conține din proiect |
|---|---|
| 1. Introducere | de ce accesul la date este o sursă frecventă de probleme de performanță |
| 2. Metodologie | tabelul de criterii, volumele de date, uneltele de măsurare |
| 3. Analiza pattern-urilor | istoric GoF și PoEAA, clasificare (creaționale, structurale, de arhitectură), pattern-urile alese |
| 4. Eficiență și optimizare | timp, memorie, interogări, scalabilitate pentru fiecare pattern |
| 5. Studiu comparativ | Singleton vs Object Pool, cache vs fără cache, Repository vs God Object |
| 6. Impactul anti-pattern-urilor | rezultatele variantei anti-pattern și cauzele lor |
| 7. Concluzii | când merită fiecare pattern și când nu |
| 8. Bibliografie | Gamma et al. (1994), Fowler (2002), Brown et al. – *AntiPatterns* (1998) |
