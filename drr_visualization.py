"""Plotly-Visualisierungen: Heim/Auswaerts-Gitter mit Break-Markierung (wachsendes Beispiel),
Politik-Vergleichsdiagramm (Hook) und CP-SAT-Timing-Skalierung. Alle Figuren per lock_axes gesperrt
(Touch-Scrolling-Konvention des Portfolios)."""

from __future__ import annotations

import plotly.graph_objects as go

from drr_evaluation import PolicyComparison, TimingPoint
from drr_scheduler import Schedule

HOME_COLOR = "#1f77b4"
AWAY_COLOR = "#d68a2e"
BREAK_COLOR = "#c0392b"
NAIVE_COLOR = "#c0392b"
COLOUR_RULE_COLOR = "#d68a2e"
OPTIMAL_COLOR = "#2ca02c"
BOUND_COLOR = "#8a8f98"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _home_grid(schedule: Schedule):
    n_teams = schedule.n_teams
    n_rounds = len(schedule.rounds)
    status = [[None] * n_rounds for _ in range(n_teams)]
    for r, rnd in enumerate(schedule.rounds):
        for m in rnd.matches:
            status[m.home][r] = True
            status[m.away][r] = False
    return status


def build_home_away_grid(schedule: Schedule, upto_round: int) -> go.Figure:
    """Zeilen = Teams, Spalten = Runden bis upto_round (1-indiziert); Zelle blau = Heim, orange =
    Auswaerts, roter Rahmen = Break (gleicher Status wie die Vorrunde desselben Teams)."""
    status = _home_grid(schedule)
    n_teams = schedule.n_teams
    n_rounds_shown = upto_round

    z = []
    text = []
    for t in range(n_teams):
        row_z = []
        row_text = []
        for r in range(n_rounds_shown):
            row_z.append(1 if status[t][r] else 0)
            row_text.append("Heim" if status[t][r] else "Auswaerts")
        z.append(row_z)
        text.append(row_text)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            text=text,
            hovertemplate="Team %{y}, Runde %{x}: %{text}<extra></extra>",
            colorscale=[[0, AWAY_COLOR], [1, HOME_COLOR]],
            showscale=False,
            xgap=2,
            ygap=2,
        )
    )

    # Break-Markierungen: rotes X auf der zweiten von zwei aufeinanderfolgenden Runden mit gleichem Status
    break_x, break_y = [], []
    for t in range(n_teams):
        for r in range(1, n_rounds_shown):
            if status[t][r] is not None and status[t][r - 1] is not None and status[t][r] == status[t][r - 1]:
                break_x.append(r)
                break_y.append(t)
    if break_x:
        fig.add_trace(
            go.Scatter(
                x=break_x,
                y=break_y,
                mode="markers",
                marker=dict(symbol="x", size=9, color=BREAK_COLOR, line=dict(width=2)),
                name="Break",
                hovertext=["Break" for _ in break_x],
                hoverinfo="text",
            )
        )

    fig.update_xaxes(title="Runde", tickmode="linear", dtick=max(1, n_rounds_shown // 15))
    fig.update_yaxes(title="Team", tickmode="linear", dtick=max(1, n_teams // 15), autorange="reversed")
    fig.update_layout(
        template="plotly_white",
        height=min(120 + n_teams * 22, 700),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=bool(break_x),
        legend=dict(orientation="h", y=-0.15),
    )
    return lock_axes(fig)


def build_policy_comparison_chart(comparisons: list[PolicyComparison]) -> go.Figure:
    ns = [c.n_teams for c in comparisons]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[c.lower_bound for c in comparisons], mode="lines",
                              line=dict(color=BOUND_COLOR, width=2, dash="dot"),
                              name="theoretische Schranke 2(n-2)"))
    fig.add_trace(go.Scatter(x=ns, y=[c.optimal_breaks for c in comparisons], mode="lines+markers",
                              line=dict(color=OPTIMAL_COLOR, width=3), name="CP-SAT-Optimum"))
    fig.add_trace(go.Scatter(x=ns, y=[c.colour_rule_breaks for c in comparisons], mode="lines+markers",
                              line=dict(color=COLOUR_RULE_COLOR, width=3), name="Farbregel"))
    fig.add_trace(go.Scatter(x=ns, y=[c.naive_breaks for c in comparisons], mode="lines+markers",
                              line=dict(color=NAIVE_COLOR, width=3), name="naiv"))
    fig.update_xaxes(title="Teamzahl", fixedrange=True, dtick=2)
    fig.update_yaxes(title="Breaks (Doppelrunde gesamt)", fixedrange=True, rangemode="tozero")
    fig.update_layout(
        template="plotly_white", height=380, margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", y=-0.22),
    )
    return fig


def build_timing_chart(points: list[TimingPoint]) -> go.Figure:
    ns = [p.n_teams for p in points]
    secs = [p.seconds for p in points]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=secs, mode="lines+markers", line=dict(color=OPTIMAL_COLOR, width=3)))
    fig.update_xaxes(title="Teamzahl", fixedrange=True)
    fig.update_yaxes(title="CP-SAT-Loesezeit (Sekunden)", fixedrange=True, rangemode="tozero")
    fig.update_layout(template="plotly_white", height=300, margin=dict(l=10, r=10, t=20, b=10))
    return fig
