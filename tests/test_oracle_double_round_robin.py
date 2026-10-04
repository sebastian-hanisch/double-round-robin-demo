"""Unabhängiges Orakel für die Doppelrunden-Liga: (1) Gültigkeit jedes Spielplans (jedes geordnete Paar genau einmal,
perfektes Matching je Runde) und Break-Zahl über Heim/Auswärts-Zeichenketten statt über die Demo-Zählung;
(2) das CP-SAT-Optimum gegen Brute Force (n = 4, 6) und eine gemischt-ganzzahlige Formulierung mit scipy/HiGHS (n = 8);
(3) die Farbregel auf der Doppelrunde von round-robin-demo selbst (Rückrunde in der ursprünglichen Reihenfolge) erreicht
3(n-2) - die Lücke "Farbregel gegen Optimum" gehört also zur gespiegelten Struktur, nicht zur Regel;
(4) die Break-Kreuze im Heim/Auswärts-Gitter gegen die Zeichenketten."""

import itertools

import numpy as np
import pytest

from drr_scheduler import (
    Match,
    Round,
    Schedule,
    _single_leg_pairs,
    colour_rule_home_away,
    naive_home_away,
    optimal_home_away,
)
from drr_evaluation import count_breaks
from drr_visualization import build_home_away_grid


def home_strings(s):
    strs = [""] * s.n_teams
    for rnd in s.rounds:
        h = {}
        for m in rnd.matches:
            h[m.home], h[m.away] = "H", "A"
        for t in range(s.n_teams):
            strs[t] += h[t]
    return strs


def oracle_breaks(s):
    return sum(1 for x in home_strings(s) for a, b in zip(x, x[1:]) if a == b)


def check_valid(s):
    n = s.n_teams
    assert len(s.rounds) == 2 * (n - 1)
    seen = set()
    for rnd in s.rounds:
        assert sorted(t for m in rnd.matches for t in (m.home, m.away)) == list(range(n))
        for m in rnd.matches:
            assert (m.home, m.away) not in seen
            seen.add((m.home, m.away))
    assert len(seen) == n * (n - 1)


@pytest.mark.parametrize("n", range(4, 23, 2))
def test_schedules_valid_and_break_count_matches_independent_count(n):
    for s in (naive_home_away(n), colour_rule_home_away(n)):
        check_valid(s)
        assert count_breaks(s) == oracle_breaks(s)


def _pair_positions(s):
    pos = {}
    for r, rnd in enumerate(s.rounds):
        for m in rnd.matches:
            pos.setdefault(frozenset((m.home, m.away)), []).append(r)
    return pos


def brute_force_min_breaks(s):
    """Alle Ausrichtungen "wer hat im ersten Treffen Heimrecht" je Paar (zweites Treffen: der andere)."""
    n, n_rounds = s.n_teams, len(s.rounds)
    pos = _pair_positions(s)
    pairs = list(pos)
    best = 10**9
    for bits in itertools.product((0, 1), repeat=len(pairs)):
        home = [[None] * n_rounds for _ in range(n)]
        for p, bit in zip(pairs, bits):
            a, c = sorted(p)
            h, g = (a, c) if bit == 0 else (c, a)
            r1, r2 = pos[p]
            home[h][r1], home[g][r1] = 1, 0
            home[g][r2], home[h][r2] = 1, 0
        best = min(best, sum(home[t][r] == home[t][r - 1] for t in range(n) for r in range(1, n_rounds)))
    return best


def milp_min_breaks(s):
    from scipy.optimize import Bounds, LinearConstraint, milp

    n, n_rounds = s.n_teams, len(s.rounds)
    H = lambda t, r: t * n_rounds + r
    B = lambda t, r: n * n_rounds + t * (n_rounds - 1) + (r - 1)
    n_vars = n * n_rounds + n * (n_rounds - 1)
    rows, lo = [], []

    def add(coeffs, lower, upper=None):
        v = np.zeros(n_vars)
        for k, c in coeffs.items():
            v[k] += c
        rows.append((v, lower, np.inf if upper is None else upper))

    for r, rnd in enumerate(s.rounds):
        for m in rnd.matches:
            add({H(m.home, r): 1, H(m.away, r): 1}, 1, 1)
    for p, (r1, r2) in _pair_positions(s).items():
        add({H(min(p), r1): 1, H(min(p), r2): 1}, 1, 1)
    for t in range(n):
        for r in range(1, n_rounds):
            add({B(t, r): 1, H(t, r): -1, H(t, r - 1): -1}, -1)       # beide Heim -> Break
            add({B(t, r): 1, H(t, r): 1, H(t, r - 1): 1}, 1)          # beide Auswärts -> Break
    c = np.zeros(n_vars)
    c[n * n_rounds:] = 1
    res = milp(c, constraints=LinearConstraint(np.array([x[0] for x in rows]), [x[1] for x in rows], [x[2] for x in rows]),
               integrality=np.ones(n_vars), bounds=Bounds(0, 1))
    assert res.status == 0
    return round(res.fun)


@pytest.mark.parametrize("n", [4, 6])
def test_cp_sat_optimum_equals_brute_force(n):
    s, proven = optimal_home_away(n, time_limit_s=8.0)
    check_valid(s)
    assert proven
    assert count_breaks(s) == oracle_breaks(s) == brute_force_min_breaks(s) == 3 * (n - 2)


def test_cp_sat_optimum_equals_independent_milp_for_8_teams():
    pytest.importorskip("scipy.optimize")
    s, proven = optimal_home_away(8, time_limit_s=8.0)
    check_valid(s)
    assert proven
    assert oracle_breaks(s) == milp_min_breaks(naive_home_away(8)) == 18


def colour_rule_double_round(n, second_leg_original_order):
    """Farbregel laut round-robin-demo, selbst hingeschrieben: "R+i"-Seite Heim, Fixteam in gerader Runde (0-indiziert)
    auswärts, Rundenindex vor der Umsortierung; Hinrunde mit vertauschten letzten zwei Runden, Rückrunde in der
    ursprünglichen Reihenfolge (oder, wie in dieser Demo, in der gezeigten Reihenfolge) mit vertauschten Rollen."""
    raw = _single_leg_pairs(n)
    fixed = n - 1

    def one_round(i, mirrored):
        out = []
        for j, (a, b) in enumerate(raw[i]):
            if j == 0:
                home, away = (a, fixed) if i % 2 == 0 else (fixed, a)   # gerade Runde: Fixteam auswärts
            else:
                home, away = b, a
            out.append(Match(away, home) if mirrored else Match(home, away))
        return Round(tuple(out))

    order = list(range(len(raw)))
    order[-1], order[-2] = order[-2], order[-1]
    second = list(range(len(raw))) if second_leg_original_order else order
    rounds = [one_round(i, False) for i in order] + [one_round(i, True) for i in second]
    return Schedule(n, tuple(rounds))


@pytest.mark.parametrize("n", range(4, 23, 2))
def test_colour_rule_reaches_the_optimum_on_the_native_double_round(n):
    s = colour_rule_double_round(n, True)
    check_valid(s)
    assert oracle_breaks(s) == 3 * (n - 2)


@pytest.mark.parametrize("n", range(4, 23, 2))
def test_colour_rule_of_the_demo_equals_the_rule_of_round_robin_demo_on_the_mirrored_structure(n):
    s = colour_rule_double_round(n, False)
    check_valid(s)
    assert oracle_breaks(s) == oracle_breaks(colour_rule_home_away(n))


@pytest.mark.parametrize("n", [4, 6, 8])
def test_grid_markers_match_independent_break_positions(n):
    for s in (naive_home_away(n), colour_rule_home_away(n)):
        strs = home_strings(s)
        n_rounds = len(s.rounds)
        for upto in range(1, n_rounds + 1):
            fig = build_home_away_grid(s, upto)
            expected = {(r + 1, t + 1) for t in range(n) for r in range(1, upto) if strs[t][r] == strs[t][r - 1]}
            got = set(zip(fig.data[1].x, fig.data[1].y)) if len(fig.data) > 1 else set()
            assert got == expected
            for t in range(n):
                assert [int(v) for v in fig.data[0].z[t]] == [1 if ch == "H" else 0 for ch in strs[t][:upto]]
