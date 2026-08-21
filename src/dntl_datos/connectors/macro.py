from __future__ import annotations

from datetime import datetime
import pandas as pd
import requests

UA = {"User-Agent": "dntl_datos/0.1 (public data research)"}


def fetch_world_bank(countries: list[str], indicators: dict[str, str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    country_expr = ";".join(countries)
    for code, label in indicators.items():
        url = f"https://api.worldbank.org/v2/country/{country_expr}/indicator/{code}"
        r = requests.get(url, params={"format": "json", "per_page": 20000}, headers=UA, timeout=60)
        r.raise_for_status()
        payload = r.json()
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 and payload[1] else []
        for row in rows:
            frames.append(pd.DataFrame([{
                "country_id": row.get("countryiso3code"),
                "country": (row.get("country") or {}).get("value"),
                "year": row.get("date"),
                "indicator_code": code,
                "indicator": label,
                "value": row.get("value"),
            }]))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fetch_bcrp(series: dict[str, str], start_year: int = 2015, end_year: int | None = None) -> pd.DataFrame:
    end_year = end_year or datetime.now().year
    frames: list[pd.DataFrame] = []
    for code, label in series.items():
        url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{code}/json/{start_year}-1/{end_year}-12"
        r = requests.get(url, headers=UA, timeout=60)
        r.raise_for_status()
        payload = r.json()
        periods = payload.get("periods", [])
        df = pd.DataFrame(periods)
        if df.empty:
            continue
        value_col = "values" if "values" in df.columns else None
        if value_col:
            df["value"] = df[value_col].apply(lambda x: x[0] if isinstance(x, list) and x else None)
        df["series_code"] = code
        df["series"] = label
        frames.append(df[[c for c in ["name", "value", "series_code", "series"] if c in df.columns]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
