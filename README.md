# Doppelrunden-Liga: Heim/Auswärts-Balance (Break-Minimierung)

Viertes Stück der **Turnierplanung**-Linie der "Konzepte"-Reihe von [sebastianhanisch.net](https://sebastianhanisch.net).
Interaktive Demo: `streamlit run app.py`.

**[→ Demo live ausprobieren](https://sebastianhanisch-double-round-robin-demo.streamlit.app/)**

## Ergebnis in Kürze

Dieselbe Zirkelmethode-Paarstruktur wie in Stück 1 (`round-robin-demo`), aber jetzt geht es um eine andere
Entscheidung: **wer wann zuhause spielt**. Drei Heim/Auswärts-Politiken im Vergleich, alle drei erfüllen die
Grundregel der Doppelrunde (jedes Team empfängt jeden Gegner genau einmal zuhause, reist genau einmal zu ihm):

- **naiv** (wer zuerst in der Paarung genannt wird, ist zuhause): bei 8 Teams 34 Breaks, bei 20 Teams 106.
- **Farbregel** (identischer Mechanismus wie `round-robin-demo`, dort für Farbausgleich optimiert, hier als
  Heim/Auswärts gelesen): 22 bzw. 70 Breaks - besser als naiv, aber **22-30 % mehr** als das Optimum -
  auf dieser gespiegelten Doppelrunde (Rückrunde in derselben gezeigten Reihenfolge). Legt man die Rückrunde wie in
  `round-robin-demo` in die ursprüngliche Reihenfolge, erreicht dieselbe Regel für $n=4\dots22$ ebenfalls $3(n-2)$
  (`tests/test_oracle_double_round_robin.py`): die Lücke gehört zur Struktur, nicht allein zur Regel.
- **CP-SAT-Optimum**: 18 bzw. 54 Breaks - bewiesen optimal, für alle gemessenen Teamzahlen (4-20, gerade)
  gilt exakt **3(n-2)** Breaks.

Die allgemeine theoretische Schranke für Break-Minimierung (de Werra 1980: mindestens $n-2$ Breaks für eine
Einzelrunde) liegt bei $2(n-2)$ für die Doppelrunde - diese konkrete Zirkelmethode-Paarstruktur erreicht sie
nicht; das gemessene Optimum liegt konstant 50 % darüber (siehe "Wo die Annahmen enden").

CP-SAT bleibt dabei über den gesamten gemessenen Bereich schnell: 50 Teams (98 Runden) lösen sich bewiesen
optimal in wenigen Sekunden, deutlich innerhalb der gesetzten 30-Sekunden-Grenze (parallele SAT-Suche - die
genaue Laufzeit schwankt spürbar zwischen Läufen/Maschinen, siehe `tests/test_claims.py`).

## Was die Demo zeigt

1. **Wachsendes Beispiel**: Saisonverlauf Runde für Runde, Heim/Auswärts-Gitter je Team, Breaks als rotes
   Kreuz markiert - Politik per Regler umschaltbar (naiv / Farbregel / CP-SAT-Optimum), live neu berechnet.
2. **📐 Wie viel kostet eine schlechte Politik?**: Sweep über die Teamzahl, alle drei Politiken plus die
   theoretische Schranke als Referenzlinie.
3. **🔬 Experiment**: CP-SAT-Rechenzeit-Skalierung bis 50 Teams - die exakte Optimierung ist für Ligagrößen
   dieser Art praktisch beliebig schnell.
4. **🚧 Wo die Annahmen enden**: nur gerade Teamzahl, nur Breaks als Ziel, die gemessene 3(n-2)-Lücke zur
   allgemeinen Schranke, keine Reisedistanz (kommt im nächsten Stück).

## Was diese Demo nicht kann (und wohin das nächste Stück geht)

Ein Team ohne Breaks kann trotzdem eine schlecht geplante Saison haben - wenn es zwischen zwei
Auswärtsspielen quer durchs Land reisen muss, obwohl ein anderer Gegner viel näher gewesen wäre. Breaks
allein sagen nichts über die **Reisedistanz**. Das nächste Stück dieser Linie (**Traveling Tournament
Problem**) baut direkt auf dieser Doppelrunden-Struktur auf und fügt genau das hinzu: Distanzminimierung
unter denselben Heim/Auswärts-Nebenbedingungen - ein berühmtes, echtes NP-schweres Problem der OR-Literatur.

## Modell und Verfahren

- **Paarstruktur**: identische Zirkelmethode wie `round-robin-demo` (`drr_scheduler.py`, Port ohne
  Cross-Repo-Import) - ein Team fix, die restlichen $n-1$ rotieren mit Schrittweite $\lceil n/2 \rceil$
  modulo $n-1$. Doppelrunde: Hinrunde plus Rückrunde mit vertauschten Rollen, letzte zwei Runden der
  Hinrunde vertauscht (FIDE-Trick wie Stück 1, hier gegen den Runden-Übergang; die Rückrunde läuft hier in der gezeigten Reihenfolge, in Stück 1 in der ursprünglichen).
- **Politiken** (`drr_scheduler.py`):
  - *naiv*: Heim ist, wer in der erzeugten Paarung zuerst genannt wird - erfüllt die Grundregel automatisch
    durch die Konstruktion, nicht durch Nachdenken über Serien.
  - *Farbregel*: wörtlicher Port von `rr_scheduler.py`s Weiß/Schwarz-Regel (die "$R+i$"-Seite ist immer
    Heim, das fixe Team wechselt nach Rundenindex-Parität).
  - *CP-SAT-Optimum*: Boolesches Modell mit einer Heim-Variable je Team und Runde, einer
    Break-Indikatorvariable je Team und Rundenübergang (über `OnlyEnforceIf` auf beide
    Ungleichheitsrichtungen, ohne Big-M) und der Nebenbedingung, dass jedes Paar genau einmal je Seite
    zuhause spielt. Minimiert die Summe der Break-Indikatoren.
- **Break-Zählung** (`drr_evaluation.py`): ein Break = zwei aufeinanderfolgende Runden mit demselben
  Heim/Auswärts-Status für ein Team; Runde 1 zählt nie als Break.
- **Quellen**: de Werra, D. (1980). "Geography, games and graphs." *Discrete Applied Mathematics* 2(4),
  327-337 (Ursprung der $n-2$-Schranke für die Einzelrunde). Goossens, D. & Spieksma, F. (2011). "Breaks,
  cuts, and patterns." *Operations Research Letters* 39(6), 428-432 - verallgemeinert den Break-Begriff auf
  nicht aufeinanderfolgende Runden (weiterführende Literatur zu Breaks und Heim-Auswärts-Mustern, nicht Beleg
  einer Aussage dieser Demo); die gemessene Mehrkosten-Lücke dieser Demo (3(n-2) statt 2(n-2)) gilt für die
  **gespiegelte** ("mirrored") Struktur - für nicht gespiegelte Doppelrunden macht die Demo keine Aussage. Terminologie "mirrored double
  round-robin tournament" zusätzlich aus Suzuka et al. (2021, "Solving Large Break Minimization Problems in
  a Mirrored Double Round-robin Tournament Using Quantum Annealing").

## Verifikation

- **Strukturell** (`tests/test_scheduler.py`): für alle drei Politiken und $n=4\dots12$ - Rundenzahl
  $2(n-1)$, jede Runde ein perfektes Matching, jedes Paar trifft genau zweimal (einmal je Seite zuhause),
  jedes Team genau $n-1$ Heimspiele.
- **Politik-Vergleich** (`tests/test_evaluation.py`): CP-SAT-Optimum ist nie schlechter als Farbregel oder
  naiv, für $n=4\dots14$ exakt $3(n-2)$ Breaks (Regressionstest gegen die gemessene Formel).
- **Orakel** (`tests/test_oracle_double_round_robin.py`): Spielplan-Gültigkeit und Break-Zahl über Heim/Auswärts-Zeichenketten, CP-SAT-Optimum gegen Brute Force ($n=4,6$) und eine MILP-Formulierung mit scipy ($n=8$), Farbregel auf der Doppelrunde von Stück 1, Break-Kreuze im Gitter.
- **Oberfläche** (`tests/test_app.py`): alle Presets, alle drei Politiken bei minimaler/maximaler Teamzahl,
  Runden-Regler-Reset bei Teamzahl-Wechsel.

## Dateistruktur

```
app.py                 Streamlit-Oberfläche
drr_constants.py        Regler-Grenzen, Presets
drr_scheduler.py         Paarstruktur + drei Heim/Auswärts-Politiken (naiv, Farbregel, CP-SAT)
drr_evaluation.py        Break-Zählung, Politik-Vergleich, Timing-Sweep
drr_presets.py           Permalink-Muster
drr_visualization.py     Plotly-Grafiken (Heim/Auswärts-Gitter, Vergleich, Timing)
tests/                   pytest-Suite
```

## Lokal starten

```bash
python -m venv venv
venv\Scripts\activate  # Windows; unter Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Turnierplanung: 7 Wege zum Turnierplan](https://sebastianhanisch.net/konzepte-turnierplanung.html).
