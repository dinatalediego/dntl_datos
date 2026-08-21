from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from dntl_datos.io import read_latest_dataset

APP_VERSION = "0.2.0"
DATA_ROOT = os.getenv("DNTL_DATA_ROOT", "data")

DEMO_SUMMARY = {
    "market_rows": 9402,
    "macro_rows": 330,
    "artist_rows": 1424,
    "catalog_rows": 14,
    "sources": ["Yahoo Finance", "World Bank", "BCRP", "MusicBrainz", "Wikidata"],
}

app = FastAPI(
    title="DNTL Datos Explorer API",
    version=APP_VERSION,
    description="Read-only API over DNTL Datos marts for the responsive web/PWA explorer.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _read(source: str, dataset: str) -> pd.DataFrame | None:
    return read_latest_dataset("marts", source, dataset, root=DATA_ROOT, required=False)


def _records(df: pd.DataFrame, columns: list[str] | None = None) -> list[dict[str, Any]]:
    if columns:
        df = df[[c for c in columns if c in df.columns]]
    clean = df.copy()
    clean = clean.where(pd.notnull(clean), None)
    for col in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[col]):
            clean[col] = clean[col].astype("string")
    return clean.to_dict(orient="records")


def _data_mode(*frames: pd.DataFrame | None) -> str:
    return "live" if any(frame is not None and not frame.empty for frame in frames) else "demo"


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "dntl-datos-explorer",
        "version": APP_VERSION,
        "data_root": str(Path(DATA_ROOT)),
    }


@app.get("/api/summary")
def summary() -> dict[str, Any]:
    market = _read("public", "market_daily_features")
    macro = _read("public", "macro_country_year")
    artists = _read("public", "peru_artist_master")
    catalog = read_latest_dataset("catalog", "system", "datasets", root=DATA_ROOT, required=False)

    if _data_mode(market, macro, artists, catalog) == "demo":
        return {"data_mode": "demo", **DEMO_SUMMARY}

    return {
        "data_mode": "live",
        "market_rows": int(len(market)) if market is not None else 0,
        "macro_rows": int(len(macro)) if macro is not None else 0,
        "artist_rows": int(len(artists)) if artists is not None else 0,
        "catalog_rows": int(len(catalog)) if catalog is not None else 0,
        "sources": DEMO_SUMMARY["sources"],
    }


@app.get("/api/markets")
def markets(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    df = _read("public", "market_daily_features")
    if df is None or df.empty:
        return {
            "data_mode": "demo",
            "items": [
                {"ticker": ticker, "date": None, "close": None, "daily_return": None, "volatility_30d_ann": None, "drawdown": None}
                for ticker in ["SPY", "QQQ", "EEM", "^GSPC", "^IXIC", "BTC-USD", "PEN=X"]
            ],
        }

    latest = (
        df.sort_values(["ticker", "date"])
        .groupby("ticker", as_index=False)
        .tail(1)
        .sort_values("ticker")
        .head(limit)
    )
    columns = ["ticker", "date", "close", "daily_return", "volatility_30d_ann", "drawdown"]
    return {"data_mode": "live", "items": _records(latest, columns)}


@app.get("/api/macro")
def macro(country: str = "PER", years: int = Query(default=12, ge=1, le=50)) -> dict[str, Any]:
    df = _read("public", "macro_country_year")
    if df is None or df.empty:
        return {"data_mode": "demo", "country": country.upper(), "items": []}

    code = country.upper()
    filtered = df[df["country_code"].astype("string").str.upper() == code].sort_values("year").tail(years)
    return {"data_mode": "live", "country": code, "items": _records(filtered)}


@app.get("/api/artists")
def artists(q: str = "", limit: int = Query(default=40, ge=1, le=100)) -> dict[str, Any]:
    df = _read("public", "peru_artist_master")
    if df is None or df.empty:
        demo = [
            {"artist_name": name, "match_status": "demo", "genre": None, "occupation": None}
            for name in ["Gian Marco", "Eva Ayllón", "Susana Baca", "Daniela Darcourt", "Grupo 5", "Renata Flores"]
        ]
        return {"data_mode": "demo", "items": demo[:limit]}

    filtered = df.copy()
    if q.strip():
        needle = q.strip().lower()
        text = (
            filtered.get("artist_name", pd.Series("", index=filtered.index)).fillna("").astype(str)
            + " "
            + filtered.get("genre", pd.Series("", index=filtered.index)).fillna("").astype(str)
            + " "
            + filtered.get("occupation", pd.Series("", index=filtered.index)).fillna("").astype(str)
        ).str.lower()
        filtered = filtered[text.str.contains(needle, regex=False)]

    if "musicbrainz_score" in filtered.columns:
        filtered = filtered.sort_values("musicbrainz_score", ascending=False, na_position="last")
    columns = ["artist_name", "match_status", "genre", "occupation", "country", "begin_area", "musicbrainz_score"]
    return {"data_mode": "live", "items": _records(filtered.head(limit), columns)}


@app.get("/api/ask")
def ask(q: str = Query(min_length=2, max_length=280)) -> dict[str, Any]:
    question = q.strip()
    lowered = question.lower()

    if any(token in lowered for token in ["artista", "música", "musica", "music", "género", "genero"]):
        df = _read("public", "peru_artist_master")
        count = int(len(df)) if df is not None else DEMO_SUMMARY["artist_rows"]
        matched = 0
        if df is not None and "match_status" in df.columns:
            matched = int((df["match_status"] == "matched").sum())
        detail = f"; {matched:,} están reconciliados entre fuentes" if matched else ""
        answer = f"El catálogo actual contiene {count:,} identidades de artistas peruanos{detail}."
        sources = ["MusicBrainz", "Wikidata"]
        route = "music"
    elif any(token in lowered for token in ["mercado", "spy", "qqq", "bitcoin", "btc", "dólar", "dolar", "pen"]):
        df = _read("public", "market_daily_features")
        count = int(len(df)) if df is not None else DEMO_SUMMARY["market_rows"]
        tickers = int(df["ticker"].nunique()) if df is not None and "ticker" in df.columns else 7
        answer = f"El mart de mercados contiene {count:,} observaciones para {tickers} instrumentos, con retorno, medias móviles, volatilidad y drawdown."
        sources = ["Yahoo Finance / yfinance"]
        route = "markets"
    elif any(token in lowered for token in ["econom", "macro", "pbi", "inflación", "inflacion", "desempleo", "world bank", "bcrp"]):
        df = _read("public", "macro_country_year")
        count = int(len(df)) if df is not None else DEMO_SUMMARY["macro_rows"]
        countries = int(df["country_code"].nunique()) if df is not None and "country_code" in df.columns else 5
        answer = f"El panel macro tiene {count:,} filas país-año para {countries} países y combina indicadores del World Bank con series peruanas del BCRP."
        sources = ["World Bank", "BCRP"]
        route = "macro"
    else:
        answer = "Puedo explorar tres dominios ahora: música peruana, mercados y economía. Prueba preguntando por artistas, volatilidad, inflación o PBI."
        sources = DEMO_SUMMARY["sources"]
        route = "home"

    return {
        "question": question,
        "answer": answer,
        "route": route,
        "sources": sources,
        "data_mode": "live" if Path(DATA_ROOT).exists() else "demo",
    }


def main() -> None:
    import uvicorn

    uvicorn.run("dntl_datos.web_api:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
