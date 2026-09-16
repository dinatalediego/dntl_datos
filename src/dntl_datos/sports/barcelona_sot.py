"""Rolling shots-on-target analytics for football player-match data."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import isclose

import pandas as pd

DEFAULT_WINDOWS = (3, 5, 10, 15)


def _trend_slope(values: pd.Series) -> float:
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


def _mean(values: pd.Series) -> float:
    x = pd.to_numeric(values, errors="coerce").dropna()
    return float(x.mean()) if len(x) else float("nan")


def build_dense_player_match_grid(
    player_matches: pd.DataFrame,
    team_matches: pd.DataFrame,
    players: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a dense team-match x player grid.

    Missing player/date rows become appeared=0, started=0, minutes=0 and SOT=0.
    This makes DNP explicit while downstream appearance metrics still filter
    to appeared > 0.
    """
    required_player = {"date", "player", "shots_on_target"}
    required_team = {"date"}
    if missing := required_player.difference(player_matches.columns):
        raise ValueError(f"Missing player-match columns: {sorted(missing)}")
    if missing := required_team.difference(team_matches.columns):
        raise ValueError(f"Missing team-match columns: {sorted(missing)}")

    p = player_matches.copy()
    t = team_matches.copy()
    p["date"] = pd.to_datetime(p["date"], errors="raise")
    t["date"] = pd.to_datetime(t["date"], errors="raise")

    if players is None:
        players = sorted(p["player"].dropna().astype(str).unique())

    base = (
        t[["date"]].drop_duplicates()
        .assign(_k=1)
        .merge(pd.DataFrame({"player": list(players), "_k": 1}), on="_k")
        .drop(columns="_k")
    )
    out = base.merge(p, on=["date", "player"], how="left", suffixes=("", "_src"))

    out["appeared"] = pd.to_numeric(out.get("appeared"), errors="coerce").fillna(0).astype(int)
    out["started"] = out.get("started", False)
    out["started"] = out["started"].fillna(False).astype(bool)
    out["minutes"] = pd.to_numeric(out.get("minutes"), errors="coerce").fillna(0)
    out["shots_on_target"] = pd.to_numeric(out["shots_on_target"], errors="coerce").fillna(0)
    out["appearance_status"] = out["appeared"].map({1: "appeared", 0: "did_not_appear"})
    return out.sort_values(["date", "player"]).reset_index(drop=True)


def build_window_summary(
    player_matches: pd.DataFrame,
    windows: Iterable[int] = DEFAULT_WINDOWS,
    team_matches: pd.DataFrame | None = None,
    players: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Build volume, efficiency and hit-rate metrics over team-match windows.

    Two denominators are always kept separate:
    - per team match: all N matches, including DNP as zero contribution;
    - per appearance: only matches where appeared > 0.
    """
    required = {"date", "player", "shots_on_target"}
    if missing := required.difference(player_matches.columns):
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = player_matches.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["shots_on_target"] = pd.to_numeric(df["shots_on_target"], errors="raise")
    if "appeared" not in df.columns:
        df["appeared"] = 1
    df["appeared"] = pd.to_numeric(df["appeared"], errors="coerce").fillna(0)
    if "minutes" not in df.columns:
        df["minutes"] = float("nan")
    df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce")
    if "started" not in df.columns:
        df["started"] = False
    df["started"] = df["started"].fillna(False).astype(bool)
    for col in ("venue", "opponent"):
        if col not in df.columns:
            df[col] = pd.NA

    if team_matches is not None:
        match_dates = sorted(pd.to_datetime(team_matches["date"], errors="raise").dropna().unique(), reverse=True)
    else:
        match_dates = sorted(df["date"].dropna().unique(), reverse=True)

    player_index = sorted(df["player"].dropna().astype(str).unique()) if players is None else list(players)
    records: list[dict[str, object]] = []

    for player in player_index:
        player_all = df[df["player"].astype(str) == str(player)]
        record: dict[str, object] = {"player": player}
        for n_raw in windows:
            n = int(n_raw)
            if n <= 0:
                raise ValueError("All windows must be positive integers.")
            selected = match_dates[:n]
            selected_set = set(selected)
            team_n = len(selected)
            observed = player_all[player_all["date"].isin(selected_set)].sort_values("date")
            apps = observed[observed["appeared"] > 0].copy()

            # Team-match vector: missing/DNP dates are explicit zero contribution.
            sot_by_date = observed.groupby("date")["shots_on_target"].sum()
            team_values = pd.Series([float(sot_by_date.get(d, 0.0)) for d in sorted(selected)])
            app_values = apps["shots_on_target"].astype(float)
            total = float(app_values.sum())
            app_n = len(apps)
            minutes = float(apps["minutes"].sum(min_count=1))

            record[f"team_matches_last_{n}"] = team_n
            record[f"appearances_last_{n}"] = app_n
            record[f"appearance_pct_last_{n}"] = 100 * app_n / team_n if team_n else float("nan")
            record[f"starts_last_{n}"] = int(apps["started"].sum())
            record[f"start_pct_of_appearances_last_{n}"] = 100 * apps["started"].mean() if app_n else float("nan")
            record[f"minutes_last_{n}"] = minutes
            record[f"sot_last_{n}"] = total
            record[f"avg_sot_per_team_match_last_{n}"] = total / team_n if team_n else float("nan")
            record[f"sot_per_team_match_last_{n}"] = record[f"avg_sot_per_team_match_last_{n}"]
            record[f"avg_sot_per_appearance_last_{n}"] = total / app_n if app_n else float("nan")
            record[f"median_sot_per_team_match_last_{n}"] = float(team_values.median()) if team_n else float("nan")
            record[f"median_sot_per_appearance_last_{n}"] = float(app_values.median()) if app_n else float("nan")
            record[f"std_sot_per_team_match_last_{n}"] = float(team_values.std(ddof=0)) if team_n else float("nan")
            record[f"std_sot_per_appearance_last_{n}"] = float(app_values.std(ddof=0)) if app_n else float("nan")

            for threshold in (1, 2, 3):
                team_hit = 100 * (team_values >= threshold).mean() if team_n else float("nan")
                app_hit = 100 * (app_values >= threshold).mean() if app_n else float("nan")
                record[f"hit_{threshold}plus_pct_team_match_last_{n}"] = team_hit
                record[f"hit_{threshold}plus_pct_appearance_last_{n}"] = app_hit
                record[f"hit_{threshold}plus_pct_last_{n}"] = app_hit

            record[f"sot_per_90_last_{n}"] = total * 90 / minutes if pd.notna(minutes) and minutes > 0 else float("nan")
            home = apps[apps["venue"].astype(str).str.lower() == "home"]["shots_on_target"]
            away = apps[apps["venue"].astype(str).str.lower() == "away"]["shots_on_target"]
            record[f"avg_sot_home_per_appearance_last_{n}"] = _mean(home)
            record[f"avg_sot_away_per_appearance_last_{n}"] = _mean(away)
            record[f"trend_sot_per_team_match_last_{n}"] = _trend_slope(team_values)
            record[f"trend_sot_per_appearance_last_{n}"] = _trend_slope(app_values)

            if app_n:
                latest = apps.iloc[-1]
                record[f"latest_opponent_last_{n}"] = latest["opponent"]
                record[f"latest_venue_last_{n}"] = latest["venue"]
            else:
                record[f"latest_opponent_last_{n}"] = pd.NA
                record[f"latest_venue_last_{n}"] = pd.NA
        records.append(record)

    return pd.DataFrame.from_records(records)


def validate_player_match_team_totals(player_matches: pd.DataFrame, team_matches: pd.DataFrame) -> pd.DataFrame:
    """Reconcile date-level player SOT with team SOT and raise on mismatch."""
    p = player_matches.copy()
    t = team_matches.copy()
    for frame in (p, t):
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    p["shots_on_target"] = pd.to_numeric(p["shots_on_target"], errors="raise")
    t["sot"] = pd.to_numeric(t["sot"], errors="raise")
    player_totals = p.groupby("date", as_index=False)["shots_on_target"].sum().rename(columns={"shots_on_target": "player_sot"})
    check = t[["date", "sot"]].merge(player_totals, on="date", how="left")
    check["player_sot"] = check["player_sot"].fillna(0)
    check["difference"] = check["player_sot"] - check["sot"]
    check["is_reconciled"] = check["difference"].abs() <= 1e-9
    failed = check.loc[~check["is_reconciled"]]
    if not failed.empty:
        failures = ", ".join(f"{r.date.date()}: players={r.player_sot:g}, team={r.sot:g}" for r in failed.itertuples())
        raise ValueError(f"Player-match SOT reconciliation failed: {failures}")
    return check.sort_values("date").reset_index(drop=True)


def validate_complete_appearance_grid(player_matches: pd.DataFrame, team_matches: pd.DataFrame) -> pd.DataFrame:
    """Validate uniqueness, coverage, 11 starters per match and SOT reconciliation."""
    required = {"date", "player", "appeared", "started", "minutes", "shots_on_target"}
    if missing := required.difference(player_matches.columns):
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    p = player_matches.copy()
    p["date"] = pd.to_datetime(p["date"], errors="raise")
    t = team_matches.copy()
    t["date"] = pd.to_datetime(t["date"], errors="raise")

    if p.duplicated(["date", "player"]).any():
        raise ValueError("Duplicate date x player rows found.")
    if set(t["date"]) != set(p["date"]):
        raise ValueError("Appearance grid dates do not exactly match team-match dates.")
    if (pd.to_numeric(p["appeared"], errors="raise") != 1).any():
        raise ValueError("Appearance table must contain only appeared=1 rows.")
    starts = p.groupby("date")["started"].sum()
    bad_starts = starts[starts != 11]
    if not bad_starts.empty:
        raise ValueError(f"Expected 11 starters per match; got {bad_starts.to_dict()}")
    minutes = pd.to_numeric(p["minutes"], errors="raise")
    if ((minutes <= 0) | (minutes > 120)).any():
        raise ValueError("Appearance minutes must be within 1..120.")
    return validate_player_match_team_totals(p, t)


def validate_window_totals(summary: pd.DataFrame, expected_team_sot: dict[int, int | float]) -> None:
    for window, expected in expected_team_sot.items():
        column = f"sot_last_{window}"
        if column not in summary.columns:
            raise ValueError(f"Missing summary column: {column}")
        observed = float(summary[column].sum())
        if not isclose(observed, float(expected), rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"SOT reconciliation failed for L{window}: players={observed:g}, team={float(expected):g}")
