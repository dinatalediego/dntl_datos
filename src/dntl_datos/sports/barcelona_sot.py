"""Rolling shots-on-target analytics for football player-match data."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import isclose

import pandas as pd

DEFAULT_WINDOWS = (3, 5, 10, 15)


def _trend_slope(values: pd.Series) -> float:
    """OLS slope of SOT over chronological appearances."""
    y = pd.to_numeric(values, errors="coerce").dropna().astype(float).tolist()
    n = len(y)
    if n < 2:
        return float("nan")
    x_mean = (n - 1) / 2
    y_mean = sum(y) / n
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return float("nan")
    numerator = sum((i - x_mean) * (value - y_mean) for i, value in enumerate(y))
    return float(numerator / denominator)


def _mean_or_nan(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    return float(numeric.mean()) if len(numeric) else float("nan")


def build_window_summary(
    player_matches: pd.DataFrame,
    windows: Iterable[int] = DEFAULT_WINDOWS,
    team_matches: pd.DataFrame | None = None,
    players: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Build player SOT metrics over the team's latest N matches.

    Required player-match columns: date, player, shots_on_target.
    Optional: appeared, minutes, started, venue, opponent, shots.

    If team_matches is provided, its distinct dates define L3/L5/L10/L15.
    This is preferred when the player-match table is sparse.

    avg_sot_per_team_match_last_N = SOT / team matches in the window.
    avg_sot_per_appearance_last_N = SOT / actual player appearances.
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
    df["appeared"] = pd.to_numeric(df["appeared"], errors="coerce").fillna(0)

    for column in ("minutes", "shots"):
        if column not in df.columns:
            df[column] = float("nan")
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if "started" not in df.columns:
        df["started"] = pd.Series(pd.NA, index=df.index, dtype="boolean")
    else:
        df["started"] = df["started"].astype("boolean")

    for column in ("venue", "opponent"):
        if column not in df.columns:
            df[column] = pd.NA

    if team_matches is not None:
        if "date" not in team_matches.columns:
            raise ValueError("team_matches must contain a 'date' column.")
        match_dates = sorted(
            pd.to_datetime(team_matches["date"], errors="raise").dropna().unique(),
            reverse=True,
        )
    else:
        match_dates = sorted(df["date"].dropna().unique(), reverse=True)

    player_index = (
        sorted(df["player"].dropna().astype(str).unique())
        if players is None
        else list(players)
    )
    records: list[dict[str, object]] = []

    for player in player_index:
        player_all = df[df["player"].astype(str) == str(player)]
        record: dict[str, object] = {"player": player}

        for window_raw in windows:
            n = int(window_raw)
            if n <= 0:
                raise ValueError("All windows must be positive integers.")

            selected_dates = match_dates[:n]
            selected_date_set = set(selected_dates)
            team_denominator = len(selected_dates)
            player_window = player_all[player_all["date"].isin(selected_date_set)]
            appearances = (
                player_window[player_window["appeared"] > 0]
                .sort_values("date")
                .copy()
            )

            total_sot = float(appearances["shots_on_target"].sum())
            appearance_count = int(len(appearances))
            minutes = float(appearances["minutes"].sum(min_count=1))
            shots = float(appearances["shots"].sum(min_count=1))
            avg_team = total_sot / team_denominator if team_denominator else float("nan")
            avg_app = total_sot / appearance_count if appearance_count else float("nan")

            record[f"team_matches_last_{n}"] = team_denominator
            record[f"appearances_last_{n}"] = appearance_count
            record[f"sot_last_{n}"] = total_sot
            record[f"avg_sot_per_team_match_last_{n}"] = avg_team
            record[f"sot_per_team_match_last_{n}"] = avg_team
            record[f"avg_sot_per_appearance_last_{n}"] = avg_app
            record[f"median_sot_per_appearance_last_{n}"] = (
                float(appearances["shots_on_target"].median())
                if appearance_count else float("nan")
            )
            record[f"std_sot_per_appearance_last_{n}"] = (
                float(appearances["shots_on_target"].std(ddof=0))
                if appearance_count else float("nan")
            )
            for threshold in (1, 2, 3):
                record[f"hit_{threshold}plus_pct_last_{n}"] = (
                    float((appearances["shots_on_target"] >= threshold).mean() * 100)
                    if appearance_count else float("nan")
                )

            record[f"minutes_last_{n}"] = minutes
            record[f"shots_last_{n}"] = shots
            record[f"sot_per_90_last_{n}"] = (
                total_sot * 90 / minutes
                if pd.notna(minutes) and minutes > 0 else float("nan")
            )

            home = appearances[appearances["venue"].astype(str).str.lower() == "home"]
            away = appearances[appearances["venue"].astype(str).str.lower() == "away"]
            record[f"avg_sot_home_per_appearance_last_{n}"] = _mean_or_nan(home["shots_on_target"])
            record[f"avg_sot_away_per_appearance_last_{n}"] = _mean_or_nan(away["shots_on_target"])
            record[f"trend_sot_per_appearance_last_{n}"] = _trend_slope(appearances["shots_on_target"])

            starts_known = int(appearances["started"].notna().sum())
            record[f"starts_known_last_{n}"] = starts_known
            record[f"starts_last_{n}"] = (
                int(appearances.loc[appearances["started"].notna(), "started"].sum())
                if starts_known else float("nan")
            )

            if appearance_count:
                latest = appearances.iloc[-1]
                record[f"latest_opponent_last_{n}"] = latest["opponent"]
                record[f"latest_venue_last_{n}"] = latest["venue"]
            else:
                record[f"latest_opponent_last_{n}"] = pd.NA
                record[f"latest_venue_last_{n}"] = pd.NA

        records.append(record)

    return pd.DataFrame.from_records(records)


def validate_window_totals(
    summary: pd.DataFrame,
    expected_team_sot: dict[int, int | float],
) -> None:
    """Raise when player SOT does not reconcile to known team totals."""
    for window, expected in expected_team_sot.items():
        column = f"sot_last_{window}"
        if column not in summary.columns:
            raise ValueError(f"Missing summary column: {column}")
        observed = float(summary[column].sum())
        if not isclose(observed, float(expected), rel_tol=0, abs_tol=1e-9):
            raise ValueError(
                f"SOT reconciliation failed for L{window}: "
                f"players={observed:g}, team={float(expected):g}"
            )


def validate_player_match_team_totals(
    player_matches: pd.DataFrame,
    team_matches: pd.DataFrame,
) -> pd.DataFrame:
    """Reconcile date-level player SOT with team SOT and raise on mismatch."""
    required_player = {"date", "shots_on_target"}
    required_team = {"date", "sot"}
    if missing := required_player.difference(player_matches.columns):
        raise ValueError(f"Missing player-match columns: {sorted(missing)}")
    if missing := required_team.difference(team_matches.columns):
        raise ValueError(f"Missing team-match columns: {sorted(missing)}")

    p = player_matches.copy()
    t = team_matches.copy()
    p["date"] = pd.to_datetime(p["date"], errors="raise")
    t["date"] = pd.to_datetime(t["date"], errors="raise")
    p["shots_on_target"] = pd.to_numeric(p["shots_on_target"], errors="raise")
    t["sot"] = pd.to_numeric(t["sot"], errors="raise")

    player_totals = (
        p.groupby("date", as_index=False)["shots_on_target"]
        .sum()
        .rename(columns={"shots_on_target": "player_sot"})
    )
    check = t[["date", "sot"]].merge(player_totals, on="date", how="left")
    check["player_sot"] = check["player_sot"].fillna(0)
    check["difference"] = check["player_sot"] - check["sot"]
    check["is_reconciled"] = check["difference"].abs() <= 1e-9

    failed = check.loc[~check["is_reconciled"]]
    if not failed.empty:
        failures = ", ".join(
            f"{row.date.date()}: players={row.player_sot:g}, team={row.sot:g}"
            for row in failed.itertuples()
        )
        raise ValueError(f"Player-match SOT reconciliation failed: {failures}")

    return check.sort_values("date").reset_index(drop=True)
