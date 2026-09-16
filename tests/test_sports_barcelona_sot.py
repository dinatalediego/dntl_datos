import math

import pandas as pd
import pytest

from dntl_datos.sports.barcelona_sot import (
    build_dense_player_match_grid,
    build_window_summary,
    validate_complete_appearance_grid,
    validate_player_match_team_totals,
)


def test_dense_grid_distinguishes_dnp_from_zero_sot_appearance():
    player_matches = pd.DataFrame([
        {"date": "2026-01-01", "player": "A", "shots_on_target": 1, "minutes": 60, "started": True, "appeared": 1},
        {"date": "2026-01-03", "player": "A", "shots_on_target": 2, "minutes": 30, "started": False, "appeared": 1},
    ])
    team_matches = pd.DataFrame([
        {"date": "2026-01-01", "sot": 1},
        {"date": "2026-01-02", "sot": 0},
        {"date": "2026-01-03", "sot": 2},
    ])
    grid = build_dense_player_match_grid(player_matches, team_matches)
    dnp = grid.loc[grid["date"] == pd.Timestamp("2026-01-02")].iloc[0]
    assert dnp["appeared"] == 0
    assert dnp["minutes"] == 0
    assert dnp["shots_on_target"] == 0
    assert dnp["appearance_status"] == "did_not_appear"


def test_team_match_and_appearance_denominators_are_both_exposed():
    player_matches = pd.DataFrame([
        {"date": "2026-01-01", "player": "A", "shots_on_target": 1, "minutes": 60, "venue": "home", "opponent": "X", "started": True, "appeared": 1},
        {"date": "2026-01-03", "player": "A", "shots_on_target": 2, "minutes": 90, "venue": "away", "opponent": "Z", "started": False, "appeared": 1},
    ])
    team_matches = pd.DataFrame([
        {"date": "2026-01-01", "sot": 1},
        {"date": "2026-01-02", "sot": 0},
        {"date": "2026-01-03", "sot": 2},
    ])
    row = build_window_summary(player_matches, windows=(3,), team_matches=team_matches).iloc[0]
    assert row["appearances_last_3"] == 2
    assert row["sot_last_3"] == 3
    assert row["avg_sot_per_team_match_last_3"] == 1
    assert row["avg_sot_per_appearance_last_3"] == 1.5
    assert math.isclose(row["hit_1plus_pct_team_match_last_3"], 100 * 2 / 3)
    assert row["hit_1plus_pct_appearance_last_3"] == 100
    assert row["hit_2plus_pct_team_match_last_3"] == pytest.approx(100 / 3)
    assert row["hit_2plus_pct_appearance_last_3"] == 50
    assert row["median_sot_per_team_match_last_3"] == 1
    assert row["median_sot_per_appearance_last_3"] == 1.5
    assert math.isclose(row["sot_per_90_last_3"], 1.8)


def test_complete_grid_requires_11_starters_and_reconciles():
    rows = []
    for i in range(11):
        rows.append({
            "date": "2026-01-01", "player": f"P{i}", "appeared": 1,
            "started": True, "minutes": 90, "shots_on_target": 1 if i == 0 else 0
        })
    rows.append({
        "date": "2026-01-01", "player": "Sub", "appeared": 1,
        "started": False, "minutes": 10, "shots_on_target": 1
    })
    player_matches = pd.DataFrame(rows)
    team_matches = pd.DataFrame([{"date": "2026-01-01", "sot": 2}])
    check = validate_complete_appearance_grid(player_matches, team_matches)
    assert check["is_reconciled"].all()


def test_reconciliation_raises_on_mismatch():
    player_matches = pd.DataFrame([{"date": "2026-01-01", "player": "A", "shots_on_target": 1}])
    team_matches = pd.DataFrame([{"date": "2026-01-01", "sot": 2}])
    with pytest.raises(ValueError, match="reconciliation failed"):
        validate_player_match_team_totals(player_matches, team_matches)
