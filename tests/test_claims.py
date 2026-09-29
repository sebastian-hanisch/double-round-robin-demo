"""Regressionstests gegen die konkreten Zahlen aus README.md - schlaegt an, falls sich die Politiken
oder die Break-Zaehlung unbemerkt aendern."""

import pytest

from drr_evaluation import compare_policies, cp_sat_timing


@pytest.mark.parametrize(
    "n, naive, colour, optimal",
    [
        (8, 34, 22, 18),
        (20, 106, 70, 54),
    ],
)
def test_readme_policy_numbers(n, naive, colour, optimal):
    cmp = compare_policies(n, time_limit_s=10.0)
    assert cmp.naive_breaks == naive
    assert cmp.colour_rule_breaks == colour
    assert cmp.optimal_breaks == optimal
    assert cmp.optimal_is_proven


def test_readme_50_teams_timing_stays_well_within_the_time_limit():
    """Grosszuegige Schwelle (nicht < 10s) - CP-SAT-Laufzeit mit paralleler Suche schwankt spuerbar
    zwischen Laeufen/Maschinen (lokal 4.9s-12.5s beobachtet); der Test soll ein Timeout/Nicht-Optimal
    fangen, nicht eine knappe Sekundenzahl fixieren, siehe project memory zu CI-robusten Zahlen-Asserts."""
    points = cp_sat_timing([50], time_limit_s=30.0)
    assert points[0].is_proven
    assert points[0].seconds < 20.0
