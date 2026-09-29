"""Strukturelle Korrektheit der Paarstruktur und aller drei Heim/Auswaerts-Politiken."""

import pytest

from drr_scheduler import (
    colour_rule_home_away,
    naive_home_away,
    optimal_home_away,
    round_count,
)

POLICIES = {
    "naive": lambda n: naive_home_away(n),
    "colour": lambda n: colour_rule_home_away(n),
    "optimal": lambda n: optimal_home_away(n, time_limit_s=8.0)[0],
}


@pytest.mark.parametrize("n", [4, 6, 8, 10, 12])
@pytest.mark.parametrize("policy_name", list(POLICIES))
def test_round_count_and_match_count(n, policy_name):
    schedule = POLICIES[policy_name](n)
    assert len(schedule.rounds) == round_count(n) == 2 * (n - 1)
    for rnd in schedule.rounds:
        assert len(rnd.matches) == n // 2


@pytest.mark.parametrize("n", [4, 6, 8, 10, 12])
@pytest.mark.parametrize("policy_name", list(POLICIES))
def test_no_team_plays_itself_or_twice_in_a_round(n, policy_name):
    schedule = POLICIES[policy_name](n)
    for rnd in schedule.rounds:
        seen = set()
        for m in rnd.matches:
            assert m.home != m.away
            assert m.home not in seen
            assert m.away not in seen
            seen.add(m.home)
            seen.add(m.away)
        assert seen == set(range(n))


@pytest.mark.parametrize("n", [4, 6, 8, 10, 12])
@pytest.mark.parametrize("policy_name", list(POLICIES))
def test_every_pair_meets_exactly_once_at_each_home(n, policy_name):
    """Grundregel der Doppelrunde: jedes Team empfaengt jeden Gegner genau einmal zuhause und
    reist genau einmal zu ihm - fuer ALLE drei Politiken, nicht nur fuer die optimierte."""
    schedule = POLICIES[policy_name](n)
    pair_homes = {}
    for rnd in schedule.rounds:
        for m in rnd.matches:
            key = frozenset((m.home, m.away))
            pair_homes.setdefault(key, []).append(m.home)
    assert len(pair_homes) == n * (n - 1) // 2
    for key, homes in pair_homes.items():
        assert len(homes) == 2
        assert homes[0] != homes[1]


@pytest.mark.parametrize("n", [4, 6, 8, 10, 12])
@pytest.mark.parametrize("policy_name", list(POLICIES))
def test_each_team_home_exactly_n_minus_one_times(n, policy_name):
    schedule = POLICIES[policy_name](n)
    home_count = {t: 0 for t in range(n)}
    for rnd in schedule.rounds:
        for m in rnd.matches:
            home_count[m.home] += 1
    assert all(c == n - 1 for c in home_count.values())


@pytest.mark.parametrize("n", [3, 5, 7])
def test_odd_n_rejected(n):
    with pytest.raises(ValueError):
        naive_home_away(n)


def test_n_below_minimum_rejected():
    with pytest.raises(ValueError):
        naive_home_away(2)
