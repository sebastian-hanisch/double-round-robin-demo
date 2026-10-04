"""Circle-Method-Paarungsplan (wie round-robin-demo, hier 0-indiziert und ohne Farbe) plus drei
Heim/Auswärts-Politiken für die Doppelrunde: naiv (Paritätsregel), Farbregel (identischer Mechanismus wie
round-robin-demo, hier als Heim/Auswärts gelesen statt Weiß/Schwarz) und CP-SAT-Optimum (echte
Break-Minimierung). Nur gerade Teamzahl (kein Freilos-Fall - Heim/Auswärts-Bilanz wäre für ein
Freilos-Team nicht sauber definierbar, siehe README "Wo die Annahmen enden").

Konstruktion (identisch zu rr_scheduler.py): ein Team ist fix, die restlichen n-1 (ungerade) tragen
Labels 0..m-1. Rundenindex R läuft mit Schrittweite (m+1)//2 durch alle Labels modulo m. Je Runde
spielt das fixe Team gegen Label R, für i=1..(m-1)//2 wird Label (R-i) gegen Label (R+i) gepaart.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ortools.sat.python import cp_model

NUM_SEARCH_WORKERS = min(8, os.cpu_count() or 1)  # NIE hart auf eine Zahl setzen - siehe project memory


@dataclass(frozen=True)
class Match:
    home: int
    away: int


@dataclass(frozen=True)
class Round:
    matches: tuple[Match, ...]


@dataclass(frozen=True)
class Schedule:
    n_teams: int
    rounds: tuple[Round, ...]


def _single_leg_pairs(n_teams: int) -> list[list[tuple[int, int]]]:
    """n_teams-1 Runden, je Runde eine Liste (a, b)-Paare (0-indiziert); b ist immer die "R+i"-Seite
    (Sonderfall: die Paarung mit dem fixen Team hat kein R+i, wird separat behandelt)."""
    if n_teams < 4 or n_teams % 2 != 0:
        raise ValueError("n_teams muss gerade und mindestens 4 sein")
    fixed = n_teams - 1
    m = n_teams - 1
    step = (m + 1) // 2
    rounds: list[list[tuple[int, int]]] = []
    r_pos = 0
    for _round_index in range(m):
        pairs = [(r_pos, fixed)]
        for i in range(1, (m - 1) // 2 + 1):
            a = (r_pos - i) % m
            b = (r_pos + i) % m
            pairs.append((a, b))
        rounds.append(pairs)
        r_pos = (r_pos + step) % m
    return rounds


def _colour_rule_home(n_teams: int, raw_rounds: list[list[tuple[int, int]]]) -> list[dict[int, bool]]:
    """Farbregel von rr_scheduler.py: die "R+i"-Seite (zweiter Eintrag jedes Paars, ausser beim Fixteam) ist
    immer Heim; das Fixteam wechselt nach der Parität des Rundenindex. Hier wird der Index der übergebenen
    Rundenliste benutzt (colour_rule_home_away übergibt die gezeigte, bereits umsortierte Reihenfolge) und das
    Fixteam hat in geraden Runden Heimrecht - gegenüber rr_scheduler.py (Fixteam gerade = Schwarz, Index vor der
    Umsortierung) ist das ein Spiegelbild beim Fixteam. Auf der gespiegelten Doppelrunde dieser Demo ergibt
    beides dieselbe Break-Zahl (tests/test_oracle_double_round_robin.py)."""
    fixed = n_teams - 1
    home_by_round: list[dict[int, bool]] = []
    for round_index, pairs in enumerate(raw_rounds):
        status: dict[int, bool] = {}
        for idx, (a, b) in enumerate(pairs):
            if idx == 0:
                # Fixteam-Paarung: (r_pos, fixed); Heimrecht nach Rundenindex-Paritaet wie im Original
                if round_index % 2 == 0:
                    status[a] = False
                    status[fixed] = True
                else:
                    status[a] = True
                    status[fixed] = False
            else:
                status[b] = True
                status[a] = False
        home_by_round.append(status)
    return home_by_round


def _apply_last_two_swap(raw_rounds: list) -> tuple[list, list[int]]:
    order = list(range(len(raw_rounds)))
    if len(order) >= 2:
        order[-1], order[-2] = order[-2], order[-1]
    return [raw_rounds[i] for i in order], order


def build_schedule(n_teams: int) -> Schedule:
    """Nur die Paarstruktur (Doppelrunde, Ruckrunde mit vertauschten Rollen), OHNE Heim/Auswaerts -
    die wird von einer der drei *_home_away-Funktionen separat aufgesetzt."""
    raw = _single_leg_pairs(n_teams)
    leg1, _order = _apply_last_two_swap(raw)
    leg2 = [[(b, a) for (a, b) in rnd] for rnd in leg1]
    rounds = []
    for rnd in leg1 + leg2:
        rounds.append(rnd)
    # Match.home/away hier nur Platzhalter (a=home) - echte Politik setzt spaeter um
    return Schedule(
        n_teams=n_teams,
        rounds=tuple(Round(matches=tuple(Match(home=a, away=b) for a, b in rnd)) for rnd in rounds),
    )


def _pair_rounds(n_teams: int) -> tuple[list[list[tuple[int, int]]], list[list[tuple[int, int]]], list[int]]:
    raw = _single_leg_pairs(n_teams)
    leg1, order = _apply_last_two_swap(raw)
    leg2 = [[(b, a) for (a, b) in rnd] for rnd in leg1]
    return raw, leg1 + leg2, order


def naive_home_away(n_teams: int) -> Schedule:
    """Naive, in der Praxis reale Politik einfacher Fixture-Generatoren: Heim ist schlicht, wer in der
    erzeugten Paarung zuerst genannt wird - Hinrunde a gegen b -> a zuhause, Ruckrunde (automatisch
    vertauscht) -> b zuhause. Erfuellt die Grundregel "jedes Paar einmal je Seite zuhause" automatisch
    (durch die Konstruktion, nicht durch Nachdenken ueber Streaks) - ignoriert aber komplett, ob daraus
    lange Heim- oder Auswaerts-Serien entstehen."""
    _raw, all_rounds, _order = _pair_rounds(n_teams)
    rounds = []
    for pairs in all_rounds:
        matches = [Match(home=a, away=b) for (a, b) in pairs]
        rounds.append(Round(matches=tuple(matches)))
    return Schedule(n_teams=n_teams, rounds=tuple(rounds))


def colour_rule_home_away(n_teams: int) -> Schedule:
    """round-robin-demos Farbregel woertlich als Heim/Auswaerts gelesen (Ruckrunde: Rollen komplett
    vertauscht, wie im Original die Farben)."""
    raw, order = _apply_last_two_swap(_single_leg_pairs(n_teams))
    home_leg1 = _colour_rule_home(n_teams, [_single_leg_pairs(n_teams)[i] for i in order])
    rounds = []
    for pairs, status in zip(raw, home_leg1):
        matches = [Match(home=a, away=b) if status[a] else Match(home=b, away=a) for (a, b) in pairs]
        rounds.append(Round(matches=tuple(matches)))
    for pairs, status in zip(raw, home_leg1):
        # Ruckrunde: dieselbe Paarung mit vertauschten Rollen, Heimrecht komplett gespiegelt
        matches = [Match(home=b, away=a) if status[a] else Match(home=a, away=b) for (a, b) in pairs]
        rounds.append(Round(matches=tuple(matches)))
    return Schedule(n_teams=n_teams, rounds=tuple(rounds))


def optimal_home_away(
    n_teams: int, time_limit_s: float = 10.0, num_search_workers: int = NUM_SEARCH_WORKERS
) -> tuple[Schedule, bool]:
    """CP-SAT: exaktes Minimum an Breaks fuer die gegebene Doppelrunden-Paarstruktur.
    Liefert (Schedule, ist_bewiesen_optimal)."""
    _raw, all_rounds, _order = _pair_rounds(n_teams)
    n_rounds = len(all_rounds)
    teams = list(range(n_teams))

    model = cp_model.CpModel()
    home = {(t, r): model.NewBoolVar(f"h_{t}_{r}") for t in teams for r in range(n_rounds)}
    pair_rounds: dict[frozenset, list[int]] = {}
    for r, pairs in enumerate(all_rounds):
        for (a, b) in pairs:
            model.Add(home[a, r] + home[b, r] == 1)
            pair_rounds.setdefault(frozenset((a, b)), []).append(r)

    # Jedes Paar trifft in der Doppelrunde zweimal - genau einmal muss Team a (und damit Team b im
    # jeweils anderen Spiel) zuhause sein, sonst waere die Grundregel der Doppelrunde verletzt (ein
    # Team koennte sonst denselben Gegner zweimal zuhause empfangen und nie zu ihm reisen).
    for pair, rs in pair_rounds.items():
        assert len(rs) == 2, f"Paar {pair} trifft {len(rs)}x statt 2x"
        a, _b = tuple(pair)
        r1, r2 = rs
        model.Add(home[a, r1] + home[a, r2] == 1)

    breaks = []
    for t in teams:
        for r in range(1, n_rounds):
            bv = model.NewBoolVar(f"brk_{t}_{r}")
            model.Add(home[t, r] - home[t, r - 1] == 0).OnlyEnforceIf(bv)
            model.Add(home[t, r] - home[t, r - 1] != 0).OnlyEnforceIf(bv.Not())
            breaks.append(bv)
    model.Minimize(sum(breaks))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_search_workers
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT fand keine Lösung (status={status})")

    rounds = []
    for r, pairs in enumerate(all_rounds):
        matches = []
        for (a, b) in pairs:
            a_home = solver.Value(home[a, r]) == 1
            matches.append(Match(home=a, away=b) if a_home else Match(home=b, away=a))
        rounds.append(Round(matches=tuple(matches)))
    return Schedule(n_teams=n_teams, rounds=tuple(rounds)), status == cp_model.OPTIMAL


def round_count(n_teams: int) -> int:
    return 2 * (n_teams - 1)
