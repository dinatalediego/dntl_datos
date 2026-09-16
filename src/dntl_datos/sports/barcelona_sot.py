"""Rolling shots-on-target windows for football player-match data."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

DEFAULT_WINDOWS = (3, 5, 10, 15)


def build_window_summary(
    player_matches: pd.DataFrame,
    windows: Iterable[int] = DEFAULT_WINDOWS,
) -> pd.DataFrame:
    """Build team-match rolling SOT windows by player.

    Expected grain: one row per team match x player.
    Required columns:
      - date
      - player
      - shots_on_target

    Optional:
      - appeared (1/0). If absent, every supplied player-match row is treated
        as an appearance for appearance counts.

    Windows are defined by the team's latest N distinct match dates, not by
    each player's latest N appearances.
    """
    required = {"date", "player", "shots_on_target"}
    missing = required.difference(player_matches.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = player_matches.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["shots_on_target"] = pd.to_numeric(df["shots_on_target"], errors="raise")

    if "appeared" not in df.columns:
        df["appeared"] = 1
    df["appeared"] = pd.to_numeric(df["appeared"], errors="raise").fillna(0)

    match_dates = sorted(df["date"].dropna().unique(), reverse=True)
    players = pd.Index(sorted(df["player"].dropna().unique()), name="player")

    result = pd.DataFrame(index=players)

    for n in windows:
        n = int(n)
        if n <= 0:
            raise ValueError("All windows must be positive integers.")

        selected_dates = set(match_dates[:n])
        window = df[df["date"].isin(selected_dates)]

        grouped = window.groupby("player", dropna=False).agg(
            shots_on_target=("shots_on_target", "sum"),
            appearances=("appeared", "sum"),
        )

        result[f"sot_last_{n}"] = grouped["shots_on_target"].reindex(players).fillna(0)
        result[f"appearances_last_{n}"] = grouped["appearances"].reindex(players).fillna(0)
        denominator = min(n, len(match_dates))
        result[f"sot_per_team_match_last_{n}"] = (
            result[f"sot_last_{n}"] / denominator if denominator else 0
        )

    return result.reset_index()


def validate_window_totals(
    summary: pd.DataFrame,
    expected_team_sot: dict[int, int],
) -> None:
    """Raise when player SOT does not reconcile to known team totals."""
    for window, expected in expected_team_sot.items():
        column = f"sot_last_{window}"
        if column not in summary.columns:
            raise ValueError(f"Missing summary column: {column}")
        observed = float(summary[column].sum())
        if observed != float(expected):
            raise ValueError(
                f"SOT reconciliation failed for L{window}: "
                f"players={observed:g}, team={expected:g}"
            )
