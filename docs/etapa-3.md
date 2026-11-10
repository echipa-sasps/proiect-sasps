# Etapa 3 — extensibilitate, efort și reproducerea rezultatelor

**Stare: planificată, neimplementată.** Se bazează pe variantele stabilizate în
etapele 1 și 2. Vezi [traseul proiectului](README.md).

Scop: completăm măsurătorile de execuție cu dovezi despre costul schimbării.
Nu deducem efortul din numărul de clase și nu comparăm productivitatea colegilor
care au implementat inițial sarcini diferite.

## Experiment comun: căutare după autor

Pornim pentru fiecare variantă din același commit înghețat, în branch-uri
separate. Înainte de cronometrare stabilim aceeași cerință și aceleași teste:

- Adăugăm `search_by_author(name)` în contract și în toate variantele.
- Căutarea este după subsir literal al numelui, cu aceleași reguli ASCII ca
  la căutarea după titlu, și returnează `Book` în ordine crescătoare după ID.
- Șirul gol returnează toate cărțile; lipsa potrivirilor returnează o listă goală.
- Disponibilitatea trebuie să fie actuală după împrumut și returnare.
- În prima parte măsurăm numai modificarea nucleului și testele sale.
  Adăugarea selectorului titlu/autor în UI este o sarcină comună separată,
  ca să nu atribuim costul frontend-ului unei variante de acces la date.
- Nu introducem simultan indexuri, refactorizări generale sau alte funcții.

Comparația principală este monolitul cu JOIN vs Repository + Facade, pentru
a reduce influența N+1. Extindem și varianta cu cache, observând dacă delegarea
este suficientă sau apar modificări suplimentare. N+1 rămâne un caz distinct,
nu baza unei concluzii generale despre mentenabilitate.

## Cum măsurăm efortul

Pentru fiecare implementare completăm un jurnal cu:

| Câmp | Ce înregistrăm |
|---|---|
| Identitate | Variantă, autorul modificării, commit inițial și final |
| Timp | Minute active, separat pentru înțelegere, implementare și depanare/teste |
| Întreruperi | Pauze excluse și utilizarea instrumentelor de asistență |
| Suprafața schimbării | Fișiere modificate, linii adăugate/șterse; producție separat de teste |
| Corectitudine | Teste de acceptanță trecute, regresii observate și corectate |
| Observații | Dificultăți concrete și presupuneri despre structura existentă |

Folosim `git diff --stat` și `git diff --numstat` între commit-urile notate,
inspectăm și diff-ul efectiv. Mai puține linii nu înseamnă automat mai puțin
efort, iar mai multe teste adăugate nu sunt automat un cost negativ.

Pentru a limita efectele experienței, schimbarea este făcută de aceiași
evaluatori pe ambele variante principale, pornind din branch-uri independente.
Un evaluator începe cu monolitul, altul cu varianta cu pattern-uri. Păstrăm
rezultatele individuale și ordinea, nu doar o medie comună. Dacă timpul echipei
permite o singură execuție per variantă, o raportăm ca studiu exploratoriu cu
acest factor de confuzie, fără concluzie cauzală despre efort.

## Împărțire propusă pentru cele 4 persoane

| Persoană | Responsabilitate de cod | Livrabil |
|---|---|---|
| 1 | Fixează cerința și testele de acceptanță; adaugă după experiment căutarea după autor în UI | Contract extins și interfață comună actualizată |
| 2 | Evaluator A: implementează schimbarea întâi în monolitul cu JOIN, apoi în Repository/Facade, în branch-uri independente | Două diff-uri, jurnale și teste trecute |
| 3 | Evaluator B: implementează independent în ordinea inversă, fără a copia soluțiile evaluatorului A | Două diff-uri, jurnale și teste trecute |
| 4 | Verifică acceptanța, colectează metricile schimbării și adaptează varianta cu cache după experiment | Datele comparației și teste de delegare/coerență cache |

Se integrează o singură soluție aleasă pentru fiecare variantă după evaluare;
nu se combină implementările independente înaintea măsurării. Ceilalți colegi
nu modifică branch-urile experimentelor în timpul cronometrării.

## Reproducere și livrare finală

1. Un coleg rulează dintr-un checkout curat instalarea, testele, generatorul,
   benchmark-urile și sumarizarea, conform instrucțiunilor versionate.
2. Separăm rezultatele de dinaintea și de după extensie; nu suprascriem pilotul.
3. Livrăm CSV-uri brute, sumarizări, grafice, metrici statice, jurnale și commit-uri.
4. Verificăm că fiecare constatare are un experiment și că unitățile, mediul,
   variația probelor și limitările sunt documentate.
5. Menținem interfața utilizabilă pentru demonstrarea tuturor funcționalităților;
   performanța accesului la date continuă să fie măsurată separat de browser.

## Ce putem susține la final

| Dimensiune | Dovezi din cod și experimente |
|---|---|
| Performanță și resurse | Durate, SQL, alocări Python, inițializare și variația probelor |
| Scalabilitate în mediul testat | Curbe după volum, workeri, operații reușite și erori |
| Mentenabilitate | Metrici statice, responsabilități și observații din modificarea reală |
| Extensibilitate și efort | Aceeași cerință, teste, diff-uri și timpi activi cu limitele protocolului |
| Costuri și contexte | Cazuri în care un pattern ajută, nu schimbă relevant rezultatul sau costă mai mult |

Acestea sunt dovezile care vor susține articolul. Nu promitem un clasament
universal al pattern-urilor; formulăm concluzii pentru aplicația, încărcările
și procesul de dezvoltare efectiv observate.
