from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

import pandas as pd

from dntl_datos.io import read_latest_dataset, write_layer_dataset


def normalize_text_key(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return text or None


def _to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def normalize_yahoo_prices(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "datetime" in out.columns and "date" not in out.columns:
        out = out.rename(columns={"datetime": "date"})
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce", utc=True).dt.tz_localize(None)
    out = _to_numeric(out, ["open", "high", "low", "close", "adj close", "volume"])
    out = out.rename(columns={"adj close": "adj_close"})
    if "ticker" in out.columns:
        out["ticker"] = out["ticker"].astype("string").str.strip()
    cols = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    return out[[c for c in cols if c in out.columns]].sort_values([c for c in ["ticker", "date"] if c in out.columns])


def normalize_world_bank(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["year"] = pd.to_numeric(out.get("year"), errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out.get("value"), errors="coerce")
    out["observation_date"] = pd.to_datetime(out["year"].astype("string") + "-01-01", errors="coerce")
    out = out.rename(columns={"country_id": "country_code"})
    cols = ["observation_date", "year", "country_code", "country", "indicator_code", "indicator", "value"]
    return out[[c for c in cols if c in out.columns]].sort_values(["country_code", "indicator", "year"])


def normalize_bcrp(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().rename(columns={"name": "period_label"})
    out["value"] = pd.to_numeric(out.get("value"), errors="coerce")
    for column in ["series_code", "series", "period_label"]:
        if column in out.columns:
            out[column] = out[column].astype("string").str.strip()
    cols = ["series_code", "series", "period_label", "value"]
    return out[[c for c in cols if c in out.columns]]


def normalize_musicbrainz(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["artist_key"] = out.get("name", pd.Series(index=out.index, dtype="object")).map(normalize_text_key)
    out["score"] = pd.to_numeric(out.get("score"), errors="coerce")
    cols = [
        "artist_key", "musicbrainz_id", "name", "sort_name", "type", "gender", "country",
        "begin_area", "area", "disambiguation", "score",
    ]
    return out[[c for c in cols if c in out.columns]].drop_duplicates()


def normalize_wikidata(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().rename(columns={
        "itemLabel": "name",
        "occupationLabel": "occupation",
        "genreLabel": "genre",
        "birthDate": "birth_date",
    })
    if "item" in out.columns:
        out["wikidata_id"] = out["item"].astype("string").str.rsplit("/", n=1).str[-1]
    out["artist_key"] = out.get("name", pd.Series(index=out.index, dtype="object")).map(normalize_text_key)
    if "birth_date" in out.columns:
        out["birth_date"] = pd.to_datetime(out["birth_date"], errors="coerce", utc=True).dt.tz_localize(None)
    cols = ["artist_key", "wikidata_id", "name", "occupation", "genre", "birth_date"]
    return out[[c for c in cols if c in out.columns]].drop_duplicates()


def normalize_billboard(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["chart_date"] = pd.to_datetime(out.get("chart_date"), errors="coerce")
    out["artist_key"] = out.get("artist", pd.Series(index=out.index, dtype="object")).map(normalize_text_key)
    out = _to_numeric(out, ["rank", "last_week", "peak_position", "weeks_on_chart"])
    cols = ["chart_date", "chart", "rank", "title", "artist", "artist_key", "last_week", "peak_position", "weeks_on_chart"]
    return out[[c for c in cols if c in out.columns]].drop_duplicates()


SILVER_JOBS: dict[tuple[str, str], Callable[[pd.DataFrame], pd.DataFrame]] = {
    ("yahoo_finance", "prices"): normalize_yahoo_prices,
    ("world_bank", "indicators"): normalize_world_bank,
    ("bcrp", "series"): normalize_bcrp,
    ("musicbrainz", "peru_artists"): normalize_musicbrainz,
    ("wikidata", "peru_musicians"): normalize_wikidata,
    ("billboard_unofficial", "hot-100"): normalize_billboard,
    ("billboard_unofficial", "billboard-200"): normalize_billboard,
    ("billboard_unofficial", "latin-songs"): normalize_billboard,
}


def build_silver(root: str = "data") -> dict[str, int]:
    summary: dict[str, int] = {}
    for (source, dataset), transform in SILVER_JOBS.items():
        raw = read_latest_dataset("raw", source, dataset, root=root, required=False)
        if raw is None:
            continue
        clean = transform(raw)
        write_layer_dataset(clean, "silver", source, dataset, root=root)
        summary[f"{source}/{dataset}"] = len(clean)
    return summary
