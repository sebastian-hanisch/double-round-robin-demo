"""Kennzahlen: Break-Zaehlung je Politik, Vergleichs-Sweep ueber n, CP-SAT-Timing-Skalierung."""

from __future__ import annotations

import time
from dataclasses import dataclass

from drr_scheduler import Schedule, colour_rule_home_away, naive_home_away, optimal_home_away


def count_breaks(schedule: Schedule) -> int:
    """Ein Break = zwei aufeinanderfolgende Runden mit demselben Heim/Auswaerts-Status fuer ein Team
    (Runde 1 zaehlt nie als Break - es gibt keine Vorrunde, mit der sie verglichen werden koennte)."""
    last: dict[int, bool | None] = {t: None for t in range(schedule.n_teams)}
    breaks = 0
    for rnd in schedule.rounds:
        status: dict[int, bool] = {}
        for m in rnd.matches:
            status[m.home] = True
            status[m.away] = False
        for t in range(schedule.n_teams):
            if last[t] is not None and last[t] == status[t]:
                breaks += 1
            last[t] = status[t]
    return breaks


def lower_bound_breaks(n_teams: int) -> int:
    """Theoretische untere Schranke fuer die Doppelrunde (2x Einzelrunden-Minimum n-2, de Werra 1980) -
    als REFERENZLINIE gezeigt, das tatsaechliche CP-SAT-Minimum wird separat gemessen und kann je nach
    n leicht darueber liegen (nicht jede Paarstruktur erreicht die Schranke, siehe README)."""
    return 2 * (n_teams - 2)


@dataclass(frozen=True)
class PolicyComparison:
    n_teams: int
    naive_breaks: int
    colour_rule_breaks: int
    optimal_breaks: int
    optimal_is_proven: bool
    lower_bound: int


def compare_policies(n_teams: int, time_limit_s: float = 10.0) -> PolicyComparison:
    naive = count_breaks(naive_home_away(n_teams))
    colour = count_breaks(colour_rule_home_away(n_teams))
    opt_schedule, is_optimal = optimal_home_away(n_teams, time_limit_s=time_limit_s)
    opt = count_breaks(opt_schedule)
    return PolicyComparison(
        n_teams=n_teams,
        naive_breaks=naive,
        colour_rule_breaks=colour,
        optimal_breaks=opt,
        optimal_is_proven=is_optimal,
        lower_bound=lower_bound_breaks(n_teams),
    )


def sweep_policies(n_values: list[int], time_limit_s: float = 10.0) -> list[PolicyComparison]:
    return [compare_policies(n, time_limit_s=time_limit_s) for n in n_values]


@dataclass(frozen=True)
class TimingPoint:
    n_teams: int
    seconds: float
    is_proven: bool


def cp_sat_timing(n_values: list[int], time_limit_s: float = 30.0) -> list[TimingPoint]:
    points = []
    for n in n_values:
        t0 = time.perf_counter()
        _schedule, is_optimal = optimal_home_away(n, time_limit_s=time_limit_s)
        dt = time.perf_counter() - t0
        points.append(TimingPoint(n_teams=n, seconds=dt, is_proven=is_optimal))
    return points
