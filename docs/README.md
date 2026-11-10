# Traseul proiectului și starea curentă

Acesta este punctul de intrare pentru planificare. Etapele descriu munca de cod
și dovezile produse de ea; redactarea articolului nu este repartizată aici.
Sunt milestone-uri interne propuse, fără termene oficiale presupuse.

## Unde suntem acum

| Componentă | Stare în repo | Ce înseamnă |
|---|---|---|
| Contract, generator, baseline | Implementate | Avem o referință funcțională și date reproductibile |
| Interfață Flask | Implementată pe baseline | Putem demonstra funcțiile catalogului |
| Teste de contract și HTTP | Implementate | Verificăm referința și interfața |
| Benchmark și `rezultate/baseline.csv` | Implementate, cu probe inițiale | Avem măsurători doar pentru referință |
| God Object + N+1 și controlul cu JOIN | Planificate pentru persoana 2 | Nu există încă rezultate comparative |
| Repository + Facade | Planificate pentru persoana 3 | Nu am evaluat încă contribuția organizării |
| Proxy cu cache și integrarea comparațiilor | Planificate pentru persoana 4 | Nu am măsurat încă beneficiile sau costurile cache-ului |

„Baseline” înseamnă o soluție simplă de referință, fără pattern-uri aplicate
explicit. Nu înseamnă cod intenționat defectuos. Varianta cu anti-pattern-uri
este un experiment separat. Numărul de clase, singur, nu dovedește God Object;
trebuie explicate responsabilitățile amestecate și dificultățile observate.

## Cele trei etape

| Etapă | Întrebarea principală | Livrabil de cod și date |
|---|---|---|
| [1 — Primele comparații](etapa-1.md) | Funcționează la fel? Ce se schimbă în execuție când eliminăm N+1, separăm codul sau introducem cache? | Variante echivalente, teste comune, CSV comparativ la 100 / 1.000 / 10.000 de cărți |
| [2 — Evaluare în contexte diferite](etapa-2.md) | În ce condiții apar beneficii, costuri sau limite? Cum se compară Singleton și Object Pool? | Scenarii extinse, măsurători robuste, metrici statice, comparație a conexiunilor |
| [3 — Costul schimbării și reproducerea finală](etapa-3.md) | Cât ajută organizarea la adăugarea aceleiași funcționalități? Putem reproduce constatările? | Extensie controlată, jurnal de efort, diff-uri, teste și pachet final de rezultate |

Nu trebuie implementate etapele 2 și 3 înainte ca variantele din etapa 1 să
treacă aceleași teste. Planurile lor pot fi ajustate după rezultatele pilotului;
schimbările se consemnează înainte de măsurătorile finale.

## Ce demonstrăm prin etapa 1

Etapa 1 produce dovezi pentru ipoteze restrânse, nu verdictul „pattern-urile
sunt mai bune”. La încheierea etapei, pentru fiecare comparație păstrăm
rezultatele inclusiv când diferența este mică sau direcția este neașteptată.

| Experiment | Ce ținem comparabil | Ce observăm | Ce putem susține |
|---|---|---|---|
| Monolit N+1 vs același monolit cu JOIN | Date, comportament și organizare | N+1 vs 1 interogare; timp și alocări Python | Efectul schimbării strategiei SQL în acest scenariu |
| Baseline / monolit cu JOIN vs Repository + Facade | Date, operații, JOIN și conexiune per operație | Timp, alocări și structură | Costul execuției și diferența de organizare a ansamblului implementat |
| Repository + Facade fără cache vs cu Proxy | Aceeași implementare de dedesubt și aceleași ID-uri citite | SQL și timp pentru 100 de citiri ale aceleiași cărți | Efectul cache-ului într-un scenariu cu reutilizare mare |
| Toate variantele | Aceleași reguli și date inițiale | Rezultate și stări după operații | Echivalența comportamentelor acoperite de teste |

În pilot, cache-ul începe gol la fiecare probă: lotul include un miss inițial
și citirile următoare. Nu este măsurarea unei singure cereri cu cache cald.
Acesta este un scenariu favorabil cache-ului; etapa 2 adaugă contexte mai puțin
favorabile. Dacă implementarea respectă planul, numărul SQL așteptat pentru
lot este 100 fără cache și 1 cu cache; acestea sunt așteptări de verificat.

Separarea Repository/Facade este evaluată împreună în acest experiment.
Nu atribuim separat un câștig fiecăruia fără o comparație suplimentară care
izolează acel factor. Un JOIN bun nu este dovada beneficiului Repository.

## Ce nu putem afirma încă

- Datele baseline nu compară pattern-uri: acum avem doar punctul de referință.
- Interfața arată funcționalitatea, dar aspectul ei nu dovedește eficiența codului.
- Etapa 1 nu demonstrează scalarea la utilizatori simultani sau performanța scrierilor.
- Mai puține interogări nu garantează o accelerare de aceeași proporție.
- Mai multe clase sau un indice static mai bun nu dovedesc automat mentenabilitate.
- Fără experimentul de schimbare nu putem cuantifica reducerea efortului de dezvoltare.
- Rezultatele locale Python/SQLite nu se generalizează automat la alte sisteme.

## Când bifăm o etapă ca terminată

1. **Etapa 1:** toate variantele trec contractul, există echivalență directă și
   CSV-uri comparative, plus sumarizare cu variația probelor.
2. **Etapa 2:** există experimente pentru contexte diferite, corectitudine sub
   concurență și rezultate cu metadate de mediu; sunt consemnate și limitele.
3. **Etapa 3:** aceeași schimbare este realizată și măsurată pe variante, iar
   un coleg reproduce testele și experimentele din instrucțiuni curate.

Contribuția finală se exprimă prin relația **problemă → soluție → experiment →
rezultat → cost și limită**. De exemplu: citiri repetate → Proxy cu cache →
scenarii cu diferite reutilizări → timpi și SQL măsurate → memorie și invalidare.
Aceste dovezi vor alimenta ulterior capitolele articolului.
