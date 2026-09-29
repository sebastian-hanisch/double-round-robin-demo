"""Regler-Grenzen, Presets und Konstanten fuer die Doppelrunden-Liga-Demo.

Nur gerade Teamzahl (kein Freilos-Fall - siehe README "Wo die Annahmen enden"). Kein Zufalls-Seed: alle drei
Politiken (naiv, Farbregel, CP-SAT-Optimum) sind deterministisch fuer eine gegebene Teamzahl.
"""

DEFAULT_N_TEAMS = 8
N_TEAMS_MIN, N_TEAMS_MAX, N_TEAMS_STEP = 4, 30, 2

POLICIES = ["CP-SAT-Optimum", "Farbregel (wie round-robin-demo)", "naiv (Rundenparitaet)"]
DEFAULT_POLICY = "CP-SAT-Optimum"

SWEEP_N_VALUES = list(range(4, 21, 2))
TIMING_N_VALUES = [10, 20, 30, 40, 50]
CP_SAT_TIME_LIMIT_S = 10.0

_BASE = {"n_teams": DEFAULT_N_TEAMS, "policy": DEFAULT_POLICY}
PRESETS = {
    "Kleine Liga, Optimum (6 Teams)": {**_BASE, "n_teams": 6, "policy": "CP-SAT-Optimum"},
    "Farbregel wiederverwendet (8 Teams)": {**_BASE, "n_teams": 8, "policy": "Farbregel (wie round-robin-demo)"},
    "Naive Politik (8 Teams)": {**_BASE, "n_teams": 8, "policy": "naiv (Rundenparitaet)"},
    "Groessere Liga, Optimum bleibt schnell (30 Teams)": {**_BASE, "n_teams": 30, "policy": "CP-SAT-Optimum"},
}
PRESET_HELP = {
    "Kleine Liga, Optimum (6 Teams)": "6 Teams, 10 Runden - das CP-SAT-Optimum erreicht hier genau die theoretische Schranke 2(n-2).",
    "Farbregel wiederverwendet (8 Teams)": "Dieselbe Farbregel wie in round-robin-demo (Stueck 1), hier als Heim/Auswaerts gelesen - erzeugt deutlich mehr Breaks als das Optimum, obwohl sie dort das Farbausgleichs-Ziel erfuellt.",
    "Naive Politik (8 Teams)": "Heim/Auswaerts nur nach Rundenparitaet, ohne Ruecksicht auf die Paarstruktur - die mit Abstand meisten Breaks.",
    "Groessere Liga, Optimum bleibt schnell (30 Teams)": "58 Runden, trotzdem loest CP-SAT das Optimum in Sekundenbruchteilen - die Break-Minimierung ist fuer Ligagroessen dieser Art praktisch beliebig schnell exakt loesbar.",
}
