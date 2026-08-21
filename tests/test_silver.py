import pandas as pd

from dntl_datos.silver import normalize_text_key, normalize_world_bank, normalize_yahoo_prices


def test_normalize_text_key_removes_accents_and_punctuation():
    assert normalize_text_key("José Quiñones & Los Ñandú") == "jose quinones los nandu"


def test_normalize_yahoo_prices_contract():
    raw = pd.DataFrame({
        "date": ["2026-08-20", "2026-08-21"],
        "ticker": ["SPY", "SPY"],
        "Open": [1, 2],
        "Close": [2, 3],
        "Adj Close": [2, 3],
        "Volume": [100, 200],
    }).rename(columns=str.lower)
    clean = normalize_yahoo_prices(raw)

    assert list(clean["ticker"]) == ["SPY", "SPY"]
    assert "adj_close" in clean.columns
    assert pd.api.types.is_datetime64_any_dtype(clean["date"])


def test_normalize_world_bank_contract():
    raw = pd.DataFrame([{
        "country_id": "PER",
        "country": "Peru",
        "year": "2025",
        "indicator_code": "NY.GDP.MKTP.CD",
        "indicator": "gdp_current_usd",
        "value": "10.5",
    }])
    clean = normalize_world_bank(raw)

    assert clean.loc[0, "country_code"] == "PER"
    assert clean.loc[0, "year"] == 2025
    assert clean.loc[0, "value"] == 10.5
