from __future__ import annotations

import time
import pandas as pd
import requests

UA = {"User-Agent": "dntl_datos/0.1 (public data research; GitHub: dinatalediego/dntl_datos)"}


def fetch_musicbrainz_peru(query: str = "area:Peru", page_size: int = 100, max_pages: int = 10) -> pd.DataFrame:
    rows: list[dict] = []
    for page in range(max_pages):
        r = requests.get(
            "https://musicbrainz.org/ws/2/artist/",
            params={"query": query, "fmt": "json", "limit": page_size, "offset": page * page_size},
            headers=UA,
            timeout=60,
        )
        r.raise_for_status()
        payload = r.json()
        artists = payload.get("artists", [])
        if not artists:
            break
        for a in artists:
            rows.append({
                "musicbrainz_id": a.get("id"),
                "name": a.get("name"),
                "sort_name": a.get("sort-name"),
                "type": a.get("type"),
                "gender": a.get("gender"),
                "country": a.get("country"),
                "disambiguation": a.get("disambiguation"),
                "score": a.get("score"),
                "begin_area": (a.get("begin-area") or {}).get("name"),
                "area": (a.get("area") or {}).get("name"),
            })
        if len(artists) < page_size:
            break
        time.sleep(1.1)
    return pd.DataFrame(rows)


def fetch_wikidata_peruvian_musicians(limit: int = 1000) -> pd.DataFrame:
    query = f'''SELECT ?item ?itemLabel ?occupationLabel ?genreLabel ?birthDate WHERE {{
      ?item wdt:P31 wd:Q5;
            wdt:P27 wd:Q419.
      ?item wdt:P106 ?occupation.
      VALUES ?occupation {{ wd:Q177220 wd:Q639669 wd:Q36834 wd:Q488205 }}
      OPTIONAL {{ ?item wdt:P136 ?genre. }}
      OPTIONAL {{ ?item wdt:P569 ?birthDate. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }} LIMIT {int(limit)}'''
    r = requests.get(
        "https://query.wikidata.org/sparql",
        params={"query": query, "format": "json"},
        headers=UA,
        timeout=90,
    )
    r.raise_for_status()
    bindings = r.json().get("results", {}).get("bindings", [])
    return pd.DataFrame([{k: v.get("value") for k, v in row.items()} for row in bindings])


def fetch_billboard_chart(chart: str = "hot-100", date: str | None = None) -> pd.DataFrame:
    try:
        import billboard
    except ImportError as exc:
        raise RuntimeError("Instala el extra opcional: pip install -e '.[billboard]'") from exc

    c = billboard.ChartData(chart, date=date)
    return pd.DataFrame([{
        "chart": chart,
        "chart_date": str(c.date),
        "rank": e.rank,
        "title": e.title,
        "artist": e.artist,
        "last_week": e.lastPos,
        "peak_position": e.peakPos,
        "weeks_on_chart": e.weeks,
    } for e in c])
