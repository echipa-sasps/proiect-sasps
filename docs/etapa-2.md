# Etapa 2 — contexte, resurse și comparație între pattern-uri

**Stare: planificată, neimplementată.** Începe după integrarea etapei 1.
Vezi [traseul proiectului](README.md) pentru starea curentă.

Scop: trecem de la „funcționează într-un exemplu favorabil” la „știm în ce
condiții ajută și cât costă”. Păstrăm funcționalitățile catalogului; extindem
experimentele și infrastructura, fără să adăugăm pattern-uri doar pentru număr.

## Experimente de implementat

### 1. Cache în condiții diferite

- Comparație fără cache / Proxy cu cache cu aceeași politică de conexiuni.
- Loturi cu citiri ale aceluiași ID, ID-uri distincte și distribuție mixtă,
  cu aceeași secvență de ID-uri generată determinist pentru ambele variante.
- Cache rece și cache preîncălzit măsurate separat; raportăm dimensiunea lotului,
  hit-uri, miss-uri și capacitatea cache-ului.
- Citiri amestecate cu împrumut/returnare; verificăm disponibilitatea după fiecare
  schimbare și măsurăm costul invalidării. Scrierile invalide sunt numărate separat.
- Dacă adăugăm limită de capacitate, comparăm aceeași politică în toate probele;
  nu schimbăm simultan implementarea și scenariul fără să consemnăm diferența.

Întrebarea: la ce reutilizare merită cache-ul, ce memorie folosește și ce
obligații de corectitudine introduce? Nu numim absența cache-ului anti-pattern.

### 2. Conexiune per operație vs Singleton vs Object Pool

Folosim același Repository, același SQL și cache dezactivat. Componentele de
conexiuni sunt injectate printr-un contract comun de achiziție/eliberare.

- Referință: conexiune deschisă și închisă pentru fiecare operație.
- Singleton: acces la o singură instanță de gestionare cu o conexiune partajată
  și acces sincronizat. Nu este doar o variabilă globală redenumită.
- Object Pool: număr limitat de conexiuni, fiecare folosită exclusiv de un worker
  cât timp este împrumutată; returnare inclusiv după excepții și închidere la final.
- Probe cu 1, 4 și 8 workeri; citiri separat de scenariile cu scrieri.
- Înregistrăm configurarea SQLite, politica tranzacțiilor, timeout-urile,
  dimensiunea pool-ului și sincronizarea. Aceleași setări unde sunt comparabile.
- Configurarea SQLite pentru folosirea conexiunilor între fire trebuie tratată
  explicit; dezactivarea unei verificări de thread nu înlocuiește sincronizarea.

Verificăm întâi corectitudinea: fără conexiuni pierdute sau blocaje la excepții;
două împrumuturi concurente ale aceleiași cărți nu trebuie să reușească ambele
fără o returnare între ele. Măsurăm operații reușite, erori și durata întregului lot.

O îmbunătățire produsă de reutilizarea conexiunilor nu dovedește că mecanismul
Singleton de acces este indispensabil. SQLite poate limita avantajele
concurenței, mai ales la scrieri; lipsa unui câștig al pool-ului este un rezultat
valid. Nu promitem dinainte că pool-ul va scala mai bine.

### 3. Volume mai mari și metrici de cod

- Extindem la 50.000 de cărți după verificarea duratei pilotului; păstrăm și
  volumele mici. Raportăm separat operația, volumul și numărul de workeri.
- Colectăm cu `radon` complexitatea ciclomatică și indicele de mentenabilitate
  pe module/clase comparabile; numărăm și fișierele și liniile de cod.
- Separăm codul implementărilor de UI, generator, teste și benchmark.
- Raportăm dimensiunea și distribuția complexității, fără un scor unic de
  „calitate”. Multe funcții mici nu sunt singure dovada unui design mai bun.

## Reguli pentru măsurători

1. Fixăm versiunile, commit-ul, mediul și configurația înaintea rulării finale.
2. Păstrăm probele brute, media, mediana, abaterea standard și min/max.
   Pentru percentile pe cereri colectăm suficiente observații individuale;
   nu deducem p95 al cererilor din 10 durate ale unor loturi.
3. Separăm inițializarea, încălzirea și operațiile măsurate. Raportăm și costul
   inițializării când comparăm infrastructuri care creează resurse anticipat.
4. Alternăm sau randomizăm reproductibil ordinea variantelor. Nu ștergem probe
   lente fără o regulă explicită și păstrarea datelor originale.
5. Măsurăm timpul fără instrumentarea memoriei. `tracemalloc` reprezintă alocări
   Python; pentru cache preîncălzit raportăm și memoria reținută, nu doar noile
   alocări din citire. Nu o numim memorie totală SQLite/proces.
6. Pentru concurență, contoarele și măsurătorile sunt agregate sigur între
   workeri. Nu reutilizăm neadaptat contorul secvențial sau `tracemalloc` global
   în măsurători individuale simultane.
7. Nu atribuim Repository/Facade efecte ale JOIN, cache-ului sau conexiunilor.

## Împărțire propusă pentru cele 4 persoane

| Persoană | Cod și responsabilitate | Livrabil |
|---|---|---|
| 1 | Extinde harness-ul și formatul datelor: configurații, ordine, metadate și sumarizare | Rulare reproductibilă și verificarea CSV-urilor |
| 2 | Implementează și testează gestionarea conexiunilor per operație, Singleton și Object Pool | Componente injectabile și teste de resurse/concurență |
| 3 | Integrează politicile în Repository; colectează metricile statice și verifică SQL comparabil | Variante de conexiuni echivalente și rezultate radon |
| 4 | Extinde Proxy-ul și scenariile cache; generează grafice din sumarizări | Hit/miss, invalidare și comparații în contexte diferite |

Înainte de lucru, persoanele 1/4 stabilesc formatul rezultatelor, iar 2/3
contractul conexiunilor. Alegerea fișierelor se face la începutul etapei, în
funcție de structura efectiv livrată de colegi în etapa 1.

## Criteriu de încheiere

Testele secvențiale și concurente trec; există rezultate pentru cache și
conexiuni în contexte diferite, metrici statice și grafice produse din CSV.
Pentru fiecare experiment sunt explicite factorul schimbat, corectitudinea,
costurile măsurate și limitele. Rezultatele contradictorii sunt păstrate.

Înainte de etapa 3 înghețăm un commit comun al tuturor variantelor, cu testele
și rezultatele aferente. Acesta va fi punctul de plecare al schimbării controlate.
