# Etapa 1 — Persoana 4: Proxy cu cache și măsurători comparative

Partea mea din [etapa 1](etapa-1.md): cache pentru detaliile cărților, testul de
echivalență între toate variantele și benchmark-ul comparativ cu sumarizare.

## Fișiere

| Fișier | Ce conține |
|---|---|
| `pattern/cache_proxy.py` | `CachingBookRepository` (Proxy) și fabrica `CachedLibraryService` |
| `tests/test_cache.py` | Proxy-ul testat cu un repository fals și serviciul testat prin `CatalogContract` |
| `tests/test_equivalence.py` | Aceeași secvență de citiri, împrumuturi și returnări pe toate variantele |
| `benchmark/run.py` | Am adăugat varianta `pattern_cache` în `VARIANTS` |
| `benchmark/summarize.py` | Mediană, medie, abatere standard, min/max pe variantă, scenariu și volum |
| `rezultate/etapa1.csv`, `rezultate/etapa1-sumar.csv` | Probele brute și sumarul pentru toate cele 5 variante |

## Cum funcționează cache-ul

`CachingBookRepository` are aceeași interfață ca `BookRepository` și primește
repository-ul real în constructor. `LibraryService` nu știe dacă lucrează cu
cache sau fără, pentru că persoana 3 a lăsat repository-ul injectabil.

- Doar `get_book` folosește cache-ul. Listarea și căutarea merg direct în bază.
- Cărțile inexistente nu se pun în cache.
- La împrumut sau returnare se scoate din cache doar cartea afectată, chiar dacă
  operația a eșuat, ca următoarea citire să vină din bază.
- `reset_metrics()` resetează contoarele (SQL, hit-uri, miss-uri), nu cache-ul.

Limitări: cache-ul este local instanței. Dacă altă instanță sau alt proces
modifică baza, instanța curentă poate întoarce date vechi. Nu are limită de
dimensiune. Ambele rămân pentru etapa 2.

## Rulare

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -t .
python -m benchmark.run --output rezultate/etapa1.csv
python -m benchmark.summarize rezultate/etapa1.csv --output rezultate/etapa1-sumar.csv
```

## Rezultate (mediana din 10 probe, 10.000 de cărți)

| Scenariu | antipattern | antipattern_join | baseline | pattern | pattern_cache |
|---|---|---|---|---|---|
| `list_books` (ms / SQL) | 66,97 / 10001 | 5,97 / 1 | 6,19 / 1 | 5,94 / 1 | 5,83 / 1 |
| `search_books` (ms / SQL) | 1,60 / 1 | 1,46 / 1 | 1,46 / 1 | 1,54 / 1 | 1,61 / 1 |
| 100 × `get_book(1)` (ms / SQL) | 10,22 / 100 | 8,97 / 100 | 8,33 / 100 | 9,88 / 100 | 0,10 / 1 |

Ce se vede:

- N+1 crește liniar: la listare, 0,72 ms la 100 de cărți, 6,28 ms la 1.000 și
  66,97 ms la 10.000. Cu JOIN, aceeași organizare coboară la aproximativ 6 ms.
- Repository + Facade (`pattern`) nu are un cost vizibil față de baseline sau de
  monolitul cu JOIN. Diferențele sunt de ordinul zgomotului dintre probe.
- Cache-ul reduce lotul de 100 de citiri de la 100 de interogări la una și de la
  aproximativ 9 ms la 0,1 ms. Scenariul îl avantajează: se citește mereu aceeași
  carte. La listare și căutare nu schimbă nimic, pentru că acolo doar deleagă.

Rulat pe un singur laptop (macOS, Python 3.12). Timpii depind de mediu. Pentru
analiza finală, măsurătorile se refac toate pe același calculator.
