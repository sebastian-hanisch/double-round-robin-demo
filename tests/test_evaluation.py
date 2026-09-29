"""Break-Zaehlung, Politik-Vergleich und die zentrale Behauptung dieses Stuecks: die optimierte Politik
schlaegt Farbregel und naive Politik immer, gemessen ueber mehrere Teamzahlen."""

import pytest

from drr_evaluation import compare_policies, count_breaks, lower_bound_breaks, sweep_policies
from drr_scheduler import Match, Round, Schedule


def _hand_built_schedule():
    """2 Teams-Paar ueber 4 Runden mit einem bekannten Break-Muster: Team 0 Heim, Heim, Auswaerts,
    Auswaerts -> genau 1 Break (Runde 1->2)."""
    rounds = [
        Round(matches=(Match(home=0, away=1),)),
        Round(matches=(Match(home=0, away=1),)),
        Round(matches=(Match(home=1, away=0),)),
        Round(matches=(Match(home=1, away=0),)),
    ]
    return Schedule(n_teams=2, rounds=tuple(rounds))


def test_count_breaks_hand_built():
    schedule = _hand_built_schedule()
    # Team 0: Heim,Heim,Auswaerts,Auswaerts; Team 1 exakt gespiegelt (immer Gegenstatus) -> je ein
    # Break bei Uebergang 1->2 und 3->4 fuer BEIDE Teams = 4 Breaks insgesamt (count_breaks summiert
    # ueber alle Teams, nicht nur eines).
    assert count_breaks(schedule) == 4


def test_count_breaks_no_breaks_when_always_alternating():
    rounds = [
        Round(matches=(Match(home=0, away=1),)),
        Round(matches=(Match(home=1, away=0),)),
        Round(matches=(Match(home=0, away=1),)),
    ]
    schedule = Schedule(n_teams=2, rounds=tuple(rounds))
    assert count_breaks(schedule) == 0


@pytest.mark.parametrize("n", [4, 6, 8, 10, 12])
def test_optimal_is_never_worse_than_colour_rule_or_naive(n):
    cmp = compare_policies(n, time_limit_s=8.0)
    assert cmp.optimal_breaks <= cmp.colour_rule_breaks
    assert cmp.optimal_breaks <= cmp.naive_breaks
    assert cmp.optimal_is_proven


@pytest.mark.parametrize("n", [4, 6, 8, 10, 12, 14])
def test_optimal_matches_measured_3n_minus_6_formula(n):
    """Empirisch gemessene, fuer die Zirkelmethode-Paarstruktur dieser Demo durchgehend bewiesene
    Formel (siehe README): 3(n-2). Regressionstest gegen genau diese Zahl."""
    cmp = compare_policies(n, time_limit_s=8.0)
    assert cmp.optimal_breaks == 3 * (n - 2)
    assert cmp.optimal_is_proven


def test_lower_bound_formula():
    assert lower_bound_breaks(4) == 4
    assert lower_bound_breaks(8) == 12
    assert lower_bound_breaks(20) == 36


def test_sweep_policies_returns_one_entry_per_n():
    results = sweep_policies([4, 6, 8], time_limit_s=8.0)
    assert [c.n_teams for c in results] == [4, 6, 8]
