# Etapa 1: implementari functionale si primele masuratori

**Stare: in lucru.** Fundatia persoanei 1 este implementata; variantele si
comparatiile persoanelor 2–4 sunt inca planificate.
Pentru imaginea de ansamblu, vezi [traseul proiectului](README.md).

Scop: aceleasi operatii intr-o referinta simpla, o varianta cu anti-pattern-uri
si una cu pattern-uri; rezultate preliminare verificabile, fara concluzii
prestabilite. Impartirea de mai jos acopera doar codul.

## Persoana 1 — fundatia si referinta simpla (implementate acum)

Fisiere: `pyproject.toml`, `catalog/`, `baseline/`, `tests/test_contract.py`.
Pregateste initial `benchmark/run.py`; dupa predare, persoana 4 preia acest fisier.

- Setup fara dependinte externe pentru nucleu; Flask pentru interfata web.
- Schema SQLite si generator determinist pentru orice volum pozitiv.
- Contract comun pentru listare, cautare, detalii, imprumut si returnare.
- Implementare simpla cu JOIN, fara Repository/Facade/cache.
- Teste de comportament reutilizabile si verificarea referintei.
- Prima executie a benchmark-ului, cu rezultate brute versionate.
- Interfata web comuna in `web/`: cautare, paginare, detalii si operatii de
  imprumut/returnare; teste HTTP in `tests/test_web.py`. Datele demonstrative
  sunt separate de generatorul folosit pentru experimente.

Livrabil: testele trec; ceilalti pot genera aceleasi date si implementa acelasi
contract. Baseline-ul nu este etichetat drept anti-pattern.

## Persoana 2 — anti-pattern-uri si izolarea efectului N+1

Fisiere proprii: `antipattern/`, `tests/test_antipattern.py`.

- Implementeaza `AntiPatternCatalog(database)` conform contractului comun.
- O singura clasa contine SQL, citire si regulile imprumutului: God Object
  intentionat, documentat prin responsabilitatile amestecate.
- La listare: un SELECT pentru carti, apoi cate un SELECT pentru autorul
  fiecarei carti, inclusiv cand autorii se repeta: exact N+1 interogari.
- Adauga `AntiPatternJoinCatalog`: pastreaza structura monolitica, dar
  suprascrie listarea cu JOIN. Este controlul pentru efectul SQL-ului.
- Refoloseste testele comune pentru ambele clase; adauga un test care verifica
  N+1, respectiv 1 interogare la listare.
- Furnizeaza persoanei 4 cele doua fabrici pentru registrul benchmark-ului.

Livrabil: toate operatiile corecte in ambele variante; numarul de interogari
explica diferenta de executie dintre cele doua listari.

## Persoana 3 — Repository si Facade

Fisiere proprii: `pattern/repository.py`, `pattern/service.py`,
`pattern/__init__.py`, `tests/test_patterns.py`.

- Implementeaza `BookRepository`: SQL si mapare la `Book`; listare cu JOIN.
- Implementeaza `LibraryService(database)`: interfata comuna si coordonarea
  operatiilor, fara SQL in serviciu. Rolul Facade trebuie sa fie explicit;
  daca ramane doar un intermediar trivial, acest cost va fi consemnat.
- Mentine regulile de imprumut si returnare prin actualizari conditionate,
  fara o verificare urmata de o actualizare neprotejata.
- Pastreaza conexiunea per operatie, schema si interogarile comparabile cu
  baseline-ul. Nu introduce acum pool, singleton, cache sau indexuri noi.
- Refoloseste testele comune si verifica separat repository-ul cu o baza
  temporara reala. Expune contorul SQL prin serviciu.
- Stabileste cu persoana 4 interfata repository-ului inainte de integrarea cache-ului.

Livrabil: serviciul trece acelasi contract; listarea are o singura interogare.
Comparam cu baseline si cu monolitul cu JOIN pentru costul organizarii.

## Persoana 4 — Proxy cu cache si masuratori comparative

Fisiere proprii: `pattern/cache_proxy.py`, `tests/test_cache.py`,
`benchmark/run.py` (dupa predarea initiala), `benchmark/summarize.py`, `rezultate/`.

- Implementeaza un Proxy cu aceeasi interfata ca `BookRepository`.
  Cache doar pentru detaliile dupa ID; listarea si cautarea sunt delegate.
- Foloseste injectarea repository-ului in serviciu pentru a expune o fabrica
  `CachedLibraryService(database)` compatibila cu benchmark-ul.
- La imprumut/returnare prin serviciu, invalideaza intrarea afectata.
  Nu cache-ui rezultate inexistente in aceasta etapa.
- Testeaza hit/miss, numarul de interogari si citirea corecta dupa modificare.
  In etapa 1, scrierile trec prin aceeasi instanta; modificarile externe si
  invalidarea intre instante sunt limitari documentate.
- Adauga fabricile colegilor in `VARIANTS`, executa testele tuturor variantelor,
  apoi benchmark-ul la 100, 1.000, 10.000 de carti, cate 10 repetari.
- Adauga sumarizare CSV: mediana, medie, abatere standard si min/max pe scenariu
  si volum; pastreaza probele brute. Un grafic simplu este optional in etapa 1.

Livrabil: rezultate pentru toate variantele si test de echivalenta directa
pe baze initial identice, inclusiv o secventa de imprumut/returnare.
Poate incepe cu sumarizarea si un repository fals pentru testele Proxy-ului
inainte sa primeasca implementarea persoanei 3.

## Contract comun: nu se schimba independent

Sursa: `catalog/contract.py`. Fiecare fabrica primeste un `pathlib.Path` spre o
baza existenta; constructorul nu executa SQL si nu incarca anticipat carti.

- `Book(id, title, author, available)` este un obiect imuabil.
- Listele sunt ordonate crescator dupa ID; fiecare carte are un singur autor.
- Cautarea este dupa subsir literal, fara wildcard-uri, ignorand cazul ASCII;
  sirul gol returneaza toate cartile. Nu promitem normalizare Unicode.
- `get_book` intoarce `None` daca ID-ul lipseste.
- Imprumutul unei carti indisponibile si returnarea uneia disponibile produc
  `CatalogError`; acelasi tip de eroare pentru ID inexistent la scriere.
- Starea este persistata in SQLite; fiecare test foloseste o baza proprie.
- `query_count` numara instructiunile SQL executate, exceptand tranzactiile;
  `reset_metrics()` reseteaza doar contorul, nu cache-ul.
- Conexiunile sunt inchise dupa operatie in toate variantele etapei 1.

Pentru a reutiliza testele:

```python
import unittest
from tests.test_contract import CatalogContract
from antipattern.catalog import AntiPatternCatalog

class TestAntiPattern(CatalogContract, unittest.TestCase):
    factory = AntiPatternCatalog
```

## Experimente si ce pot demonstra

| Comparatie | Factor urmarit |
|---|---|
| AntiPatternCatalog vs AntiPatternJoinCatalog | N+1 vs JOIN, pastrand organizarea |
| Baseline vs LibraryService | Costul structurii Repository/Facade cu SQL comparabil |
| AntiPatternJoinCatalog vs LibraryService | Monolit vs separarea responsabilitatilor |
| LibraryService vs CachedLibraryService | Efectul cache-ului pe aceleasi citiri |

Benchmark-ul initial masoara listarea completa, cautarea unui subsir fix si un
lot de 100 citiri ale aceleiasi carti. Fiecare proba incepe cu un adaptor nou:
pentru cache, lotul include primul miss si apoi hit-uri; nu este un test exclusiv
de cache deja incalzit. Incalzirea prealabila foloseste alta instanta.
Interogarile raportate apartin intregului lot/operatie.

Timpul se masoara fara `tracemalloc`; memoria intr-o executie separata a aceluiasi
scenariu. `peak_python_kib` este varful alocarilor Python in operatia masurata,
inclusiv rezultatul retinut; nu este memoria totala a procesului sau SQLite.
Datele sunt generate in afara masuratorilor. Ordinea variantelor este fixa in
acest pilot; rezultatele de timing sunt preliminare si dependente de mediu.
Nu se masoara inca performanta scrierilor sau concurenta.

## Integrare si incheierea etapei

1. Persoana 1 publica fundatia comuna.
2. Persoanele 2 si 3 implementeaza independent; persoana 4 pregateste cache-ul
   si sumarizarea, apoi integreaza interfata stabilita cu persoana 3.
3. Fiecare foloseste un branch propriu si ruleaza testele inainte de integrare.
   Persoana 4 inregistreaza fabricile intr-un singur loc, evitand conflictele.
4. Etapa este incheiata cand toate variantele trec contractul, echivalenta este
   verificata si exista CSV-uri comparative reproductibile. Baseline-ul singur
   constituie doar rezultatul initial al persoanei 1.

Singleton/Object Pool, 50.000 de carti, concurenta si metricile radon sunt
planificate in [etapa 2](etapa-2.md). Experimentul controlat de extensibilitate
si efort este separat in [etapa 3](etapa-3.md). Nu sunt necesare pentru primul
milestone; etapa 1 singura nu demonstreaza reducerea efortului de dezvoltare.
