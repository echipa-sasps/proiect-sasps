# SASPS – Catalog de bibliotecă

# Studiu comparativ: pattern-uri de acces la date vs anti-pattern-uri

## Descriere

Proiectul compară efectul pattern-urilor de proiectare și al anti-pattern-urilor asupra **performanței**, **scalabilității**, **consumului de resurse** și **mentenabilității** unei aplicații care lucrează cu o bază de date.

Aplicația este un catalog simplu de bibliotecă: cărți, autori și împrumuturi, stocate în SQLite. Aceleași funcționalități sunt implementate de două ori:

- **varianta anti-pattern** – cod scris „direct”, așa cum apare des în proiecte reale;
- **varianta cu pattern-uri** – același comportament, organizat cu pattern-uri de proiectare.

Ambele variante rulează pe aceleași date și sunt măsurate cu aceleași teste, deci diferențele vin doar din proiectare.

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
