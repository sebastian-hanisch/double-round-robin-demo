"""Doppelrunden-Liga mit Heim/Auswaerts-Balance (Break-Minimierung) - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stueck der "Turnierplanung"-Linie der "Konzepte"-Reihe: baut auf der Zirkelmethode-Paarung von
Stueck 1 (round-robin-demo) auf, fragt aber nach etwas, das dort nie gemessen wurde - wie oft spielt ein
Team zwei Heim- oder zwei Auswaertsspiele in Folge (ein "Break")? Naechstes Stueck (Traveling Tournament
Problem) baut direkt auf dieser Break-Struktur auf und fuegt Reisedistanz hinzu.

Lauffaehig mit: streamlit run app.py
"""

import streamlit as st

import drr_constants as C
from drr_evaluation import cp_sat_timing, sweep_policies
from drr_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    sync_query_params,
)
from drr_scheduler import colour_rule_home_away, naive_home_away, optimal_home_away
from drr_evaluation import count_breaks
from drr_visualization import build_home_away_grid, build_policy_comparison_chart, build_timing_chart

st.set_page_config(page_title="Doppelrunden-Liga – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _schedule(n_teams, policy):
    if policy == "CP-SAT-Optimum":
        schedule, is_optimal = optimal_home_away(n_teams, time_limit_s=C.CP_SAT_TIME_LIMIT_S)
        return schedule, is_optimal
    if policy == "Farbregel (wie round-robin-demo)":
        return colour_rule_home_away(n_teams), True
    return naive_home_away(n_teams), True


@st.cache_data(show_spinner=False)
def _sweep():
    return sweep_policies(C.SWEEP_N_VALUES, time_limit_s=C.CP_SAT_TIME_LIMIT_S)


@st.cache_data(show_spinner=False)
def _timing():
    return cp_sat_timing(C.TIMING_N_VALUES, time_limit_s=30.0)


st.title("🏆 Doppelrunden-Liga: Heim/Auswärts-Balance (Break-Minimierung)")
st.markdown(
    """
Bei einer **Doppelrunden-Liga** ("Hin- und Rückrunde") spielt jedes Team zweimal gegen jedes andere - einmal
zuhause, einmal auswärts. Die Paarungen allein legen das noch nicht fest: **wer wann zuhause spielt**, ist
eine eigene Entscheidung. Ein **Break** ist, wenn ein Team zwei Heim- oder zwei Auswärtsspiele in Folge
bekommt - Ligen wollen das aus Fairness- und Vermarktungsgründen möglichst selten. Diese Demo vergleicht drei
Heim/Auswärts-Politiken für dieselbe Paarstruktur (Zirkelmethode, wie in Stück 1 dieser Linie).
"""
)
st.caption(
    "Baut auf der Zirkelmethode-Paarung von Stück 1 (round-robin-demo) auf, fragt aber etwas Neues: nicht "
    "die Paarung selbst, sondern die Heim/Auswärts-**Reihenfolge** ist hier die Entscheidung. Das nächste "
    "Stück (Traveling Tournament Problem) baut direkt hierauf auf und fügt Reisedistanz hinzu."
)

with st.expander("Drei Heim/Auswärts-Politiken für dieselbe Paarstruktur", expanded=True):
    st.markdown(
        """
1. **naiv (zuerst genannt = Heim)**: Heim ist, wer in der erzeugten Paarung zuerst genannt wird (Rückrunde
   automatisch vertauscht) - ignoriert komplett, welche Heim- oder Auswärts-Serien daraus entstehen.
2. **Farbregel**: exakt dieselbe Weiß/Schwarz-Regel wie in Stück 1 (round-robin-demo), hier als
   Heim/Auswärts gelesen - dort optimiert sie den Farbausgleich (Differenz höchstens 1), nicht die
   Break-Zahl. Wie gut trifft sie trotzdem das Break-Ziel?
3. **CP-SAT-Optimum**: echte Optimierung - minimiert die Gesamtzahl der Breaks über die ganze Saison exakt,
   kein Heuristik-Kompromiss.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_teams = st.slider(
        "Teamzahl", *bounds("n_teams_slider"), step=C.N_TEAMS_STEP, key="n_teams_slider",
        help="Nur gerade Teamzahl - bei ungerader Zahl wäre ein Freilos-Team nicht sauber Heim/Auswärts-bilanzierbar.",
    )
    policy = st.radio("Heim/Auswärts-Politik", C.POLICIES, key="policy_radio")

sync_query_params(n_teams, policy)

n_teams = int(n_teams)
schedule, is_optimal = _schedule(n_teams, policy)
n_rounds = len(schedule.rounds)
breaks = count_breaks(schedule)

st.markdown("---")
st.markdown("## 🎯 Saisonverlauf: wer spielt wann zuhause?")
st.caption(
    f"{n_teams} Teams, {n_rounds} Runden (Doppelrunde), Politik: **{policy}** - "
    "jede Zelle ein Spiel, rotes Kreuz = Break."
)

round_key = (n_teams, policy)
if "round_slider" not in st.session_state or st.session_state.get("round_owner") != round_key:
    st.session_state["round_slider"] = n_rounds
    st.session_state["round_owner"] = round_key

rcol1, rcol2 = st.columns([5, 1])
with rcol1:
    upto_round = st.slider("Bis Runde", 1, n_rounds, key="round_slider")
with rcol2:
    auto_play = st.button("▶️ Abspielen", width="stretch")

grid_slot = st.empty()


def _render(r):
    grid_slot.plotly_chart(build_home_away_grid(schedule, r), width="stretch", key=f"grid_{n_teams}_{policy}_{r}")


if auto_play:
    import time

    for r in range(1, n_rounds + 1):
        _render(r)
        time.sleep(max(0.02, 4.0 / n_rounds))
    upto_round = n_rounds
else:
    _render(upto_round)

if policy == "CP-SAT-Optimum" and not is_optimal:
    st.warning(
        f"CP-SAT hat innerhalb von {C.CP_SAT_TIME_LIMIT_S:.0f}s keine bewiesene Optimallösung gefunden - "
        "gezeigt wird die beste bisher gefundene (obere Schranke)."
    )
st.caption(
    f"**{breaks} Breaks** insgesamt über die ganze Saison "
    f"(theoretische Schranke: {2 * (n_teams - 2)}, siehe Abschnitt unten)."
)

st.markdown("---")
st.subheader("📐 Wie viel kostet eine schlechte Heim/Auswärts-Politik?")
st.markdown(
    """
Dieselbe Paarstruktur, drei Politiken, über die Teamzahl hinweg gemessen - die theoretische Schranke
(de Werra 1980, für die Einzelrunde bewiesen, hier verdoppelt als Referenzlinie) zeigt, wie viel Luft
grundsätzlich noch nach unten wäre.
"""
)
sweep = _sweep()
st.plotly_chart(build_policy_comparison_chart(sweep), width="stretch", key="policy_comparison")
current = next((c for c in sweep if c.n_teams == n_teams), None)
if current is not None:
    gap_naive = current.naive_breaks - current.optimal_breaks
    gap_colour = current.colour_rule_breaks - current.optimal_breaks
    st.caption(
        f"Bei {n_teams} Teams: naiv braucht {gap_naive} Breaks mehr als das Optimum "
        f"({current.naive_breaks} vs. {current.optimal_breaks}), die Farbregel {gap_colour} mehr "
        f"({current.colour_rule_breaks} vs. {current.optimal_breaks}) - "
        "eine für Farbausgleich gute Regel ist nicht automatisch break-arm."
    )

st.markdown("---")
st.subheader("🔬 Experiment: bleibt das Optimum bei größeren Ligen noch schnell?")
timing = _timing()
st.plotly_chart(build_timing_chart(timing), width="stretch", key="timing_chart")
st.caption(
    f"CP-SAT löst das exakte Optimum für alle gemessenen Ligagrößen (bis {C.TIMING_N_VALUES[-1]} Teams, "
    f"{2 * (C.TIMING_N_VALUES[-1] - 1)} Runden) in unter {max(p.seconds for p in timing):.1f} Sekunden - "
    "die Break-Minimierung ist für Ligagrößen dieser Art praktisch beliebig schnell exakt lösbar, "
    "anders als z. B. das nächste Stück dieser Linie (Traveling Tournament Problem), das echte "
    "Rechenzeit-Grenzen hat."
)

st.markdown("---")

with st.expander("🚧 Wo die Annahmen enden"):
    st.markdown(
        """
- **Nur gerade Teamzahl.** Bei ungerader Zahl hat in jeder Runde ein Team ein Freilos - dessen
  Heim/Auswärts-Bilanz und Break-Zählung wären gesondert zu definieren (in dieser Demo nicht behandelt).
- **Nur Breaks als Ziel.** Reale Ligaplanung hat weitere Ziele (Stadion-Verfügbarkeit, TV-Slots,
  Rivalitäts-Spieltage) - hier bewusst isoliert, um genau dieses eine Kriterium sauber zu zeigen.
- **Die allgemeine theoretische Schranke 2(n-2) wird von dieser Paarstruktur nicht erreicht.** Gemessen
  (CP-SAT, bewiesen optimal für alle gezeigten n): das tatsächliche Optimum für DIESE Paarstruktur
  (Zirkelmethode, mit der Nebenbedingung "jedes Paar einmal je Seite zuhause") liegt konstant bei **3(n-2)**
  Breaks - deutlich über der allgemeinen Schranke. Wahrscheinlicher Grund (nicht separat geprüft): diese Demo verlangt eine **gespiegelte**
  ("mirrored") Doppelrunde, dieselbe Rundenreihenfolge mit vertauschten Rollen. Die gemessene Lücke gilt für
  diese gespiegelte Struktur; ob sie auch bei einer NICHT gespiegelten Doppelrunde auftritt, untersucht diese
  Demo nicht.
- **Reisedistanz fehlt komplett.** Ein Team kann break-frei spielen und trotzdem quer durchs Land pendeln -
  genau diese Lücke schließt das nächste Stück dieser Linie (Traveling Tournament Problem).
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** $n$ Teams (gerade), Doppelrunde = $2(n-1)$ Runden. Eine Paarstruktur $\pi$ (hier: Zirkelmethode,
wie Stück 1) legt fest, wer in welcher Runde gegen wen spielt. Gesucht: eine Heim/Auswärts-Zuweisung
$h_{t,r} \in \{0,1\}$ je Team $t$ und Runde $r$ mit $h_{a,r} + h_{b,r} = 1$ für jedes Spielpaar $(a,b)$ der
Runde $r$, die die Zahl der **Breaks**
$$\sum_t \sum_{r=2}^{2(n-1)} \mathbb{1}[h_{t,r} = h_{t,r-1}]$$
minimiert.

**Untere Schranke** (de Werra 1980): für eine Einzelrunde ($n-1$ Runden, $n$ gerade) sind mindestens $n-2$
Breaks nötig, erreichbar durch eine geeignete kanonische Konstruktion. Für die Doppelrunde als
Referenzlinie verdoppelt ($2(n-2)$) - **nicht** notwendig das tatsächliche Optimum jeder konkreten
Paarstruktur: für die Zirkelmethode-Paarstruktur dieser Demo (mit der Nebenbedingung "jedes Paar einmal je
Seite zuhause") liegt das per CP-SAT bewiesene Optimum bei $3(n-2)$, siehe "Wo die Annahmen enden".

**CP-SAT-Optimum**: `AddBoolVar`-Modell mit einer Break-Indikatorvariable je Team und Runde (Big-M-frei über
`OnlyEnforceIf` auf beiden Ungleichheitsrichtungen), Minimierung der Summe - löst alle gezeigten Ligagrößen
in Sekundenbruchteilen bis Sekunden (`drr_scheduler.optimal_home_away`).

**Farbregel** (identisch zu `rr_scheduler.py`, hier als Heim/Auswärts gelesen): die "$R+i$"-Seite jeder
Paarung ist immer Heim; das fixe Team wechselt nach Rundenindex-Parität.

Implementiert in `drr_scheduler.py` (drei Politiken) und `drr_evaluation.py` (Break-Zählung, Sweeps).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Turnierplanung: 7 Wege zum Turnierplan](https://sebastianhanisch.net/konzepte-turnierplanung.html)."
)
