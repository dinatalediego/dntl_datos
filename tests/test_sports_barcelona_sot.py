import math

import pandas as pd
import pytest

from dntl_datos.sports.barcelona_sot import (
    build_window_summary,
    validate_player_match_team_totals,
)


def test_team_match_and_appearance_averages_are_distinct():
    player_matches = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "player": "A",
                "shots_on_target": 1,
                "minutes": 60,
                "venue": "home",
                "opponent": "X",
                "started": True,
            },
            {
                "date": "2026-01-03",
                "player": "A",
                "shots_on_target": 2,
                "minutes": 90,
                "venue": "away",
                "opponent": "Z",
                "started": False,
            },
        ]
    )
    team_matches = pd.DataFrame(
        [
            {"date": "2026-01-01", "sot": 1},
            {"date": "2026-01-02", "sot": 0},
            {"date": "2026-01-03", "sot": 2},
        ]
    )

    row = build_window_summary(
        player_matches,
        windows=(3,),
        team_matches=team_matches,
    ).iloc[0]

    assert row["team_matches_last_3"] == 3
    assert row["appearances_last_3"] == 2
    assert row["sot_last_3"] == 3
    assert row["avg_sot_per_team_match_last_3"] == 1
    assert row["avg_sot_per_appearance_last_3"] == 1.5
    assert row["median_sot_per_appearance_last_3"] == 1.5
    assert row["std_sot_per_appearance_last_3"] == 0.5
    assert row["hit_1plus_pct_last_3"] == 100
    assert row["hit_2plus_pct_last_3"] == 50
    assert row["hit_3plus_pct_last_3"] == 0
    assert math.isclose(row["sot_per_90_last_3"], 1.8)
    assert row["avg_sot_home_per_appearance_last_3"] == 1
    assert row["avg_sot_away_per_appearance_last_3"] == 2
    assert row["trend_sot_per_appearance_last_3"] == 1
    assert row["starts_known_last_3"] == 2
    assert row["starts_last_3"] == 1
    assert row["latest_opponent_last_3"] == "Z"


def test_sparse_player_match_sot_can_reconcile_team_volume():
    player_matches = pd.DataFrame(
        [
            {"date": "2026-01-01", "player": "A", "shots_on_target": 2},
            {"date": "2026-01-01", "player": "B", "shots_on_target": 1},
            {"date": "2026-01-02", "player": "A", "shots_on_target": 0},
            {"date": "2026-01-02", "player": "C", "shots_on_target": 4},
        ]
    )
    team_matches = pd.DataFrame(
        [
            {"date": "2026-01-01", "sot": 3},
            {"date": "2026-01-02", "sot": 4},
        ]
    )

    check = validate_player_match_team_totals(player_matches, team_matches)
    assert check["is_reconciled"].all()


def test_reconciliation_raises_on_mismatch():
    player_matches = pd.DataFrame(
        [{"date": "2026-01-01", "player": "A", "shots_on_target": 1}]
    )
    team_matches = pd.DataFrame([{"date": "2026-01-01", "sot": 2}])

    with pytest.raises(ValueError, match="reconciliation failed"):
        validate_player_match_team_totals(player_matches, team_matches)
