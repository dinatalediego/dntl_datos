import pandas as pd

from dntl_datos.io import write_layer_dataset
from dntl_datos.marts import build_market_daily_features, build_peru_artist_master


def test_market_daily_features(tmp_path):
    dates = pd.date_range("2026-01-01", periods=40, freq="D")
    silver = pd.DataFrame({
        "date": dates,
        "ticker": ["SPY"] * len(dates),
        "close": range(100, 140),
        "open": range(99, 139),
        "high": range(101, 141),
        "low": range(98, 138),
        "adj_close": range(100, 140),
        "volume": [1000] * len(dates),
    })
    write_layer_dataset(silver, "silver", "yahoo_finance", "prices", root=str(tmp_path))

    mart = build_market_daily_features(root=str(tmp_path))

    assert mart is not None
    assert {"daily_return", "ma_20", "volatility_30d_ann", "drawdown", "month"}.issubset(mart.columns)
    assert mart["daily_return"].notna().sum() == 39


def test_peru_artist_master_matches_normalized_artist_key(tmp_path):
    mb = pd.DataFrame([{
        "artist_key": "susana baca",
        "musicbrainz_id": "mb-1",
        "name": "Susana Baca",
        "type": "Person",
        "gender": "Female",
        "country": "PE",
        "begin_area": "Lima",
        "area": "Peru",
        "disambiguation": None,
        "score": 100,
    }])
    wd = pd.DataFrame([{
        "artist_key": "susana baca",
        "wikidata_id": "Q123",
        "name": "Susana Baca",
        "occupation": "cantante",
        "genre": "música afroperuana",
        "birth_date": pd.Timestamp("1944-05-24"),
    }])
    write_layer_dataset(mb, "silver", "musicbrainz", "peru_artists", root=str(tmp_path))
    write_layer_dataset(wd, "silver", "wikidata", "peru_musicians", root=str(tmp_path))

    mart = build_peru_artist_master(root=str(tmp_path))

    assert mart is not None
    assert len(mart) == 1
    assert mart.loc[mart.index[0], "match_status"] == "matched"
    assert mart.loc[mart.index[0], "artist_name"] == "Susana Baca"
    assert mart.loc[mart.index[0], "genre"] == "música afroperuana"


def test_peru_artist_master_supports_wikidata_only(tmp_path):
    wd = pd.DataFrame([{
        "artist_key": "chabuca granda",
        "wikidata_id": "Q456",
        "name": "Chabuca Granda",
        "occupation": "compositora",
        "genre": "vals peruano",
        "birth_date": pd.Timestamp("1920-09-03"),
    }])
    write_layer_dataset(wd, "silver", "wikidata", "peru_musicians", root=str(tmp_path))

    mart = build_peru_artist_master(root=str(tmp_path))

    assert mart is not None
    assert len(mart) == 1
    assert mart.loc[mart.index[0], "match_status"] == "wikidata_only"
    assert mart.loc[mart.index[0], "artist_name"] == "Chabuca Granda"
