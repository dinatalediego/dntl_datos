from __future__ import annotations

import time

import pandas as pd
import requests

UA = {"User-Agent": "dntl_datos/0.1 (public data research; GitHub: dinatalediego/dntl_datos)"}
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), 1.2)
            except ValueError:
                pass
    return min(1.2 * (2 ** attempt), 12.0)


def _get_json(
    url: str,
    *,
    params: dict,
    timeout: int,
    attempts: int = 5,
) -> dict:
    last_error: Exception | None = None

    for attempt in range(attempts):
        response: requests.Response | None = None
        try:
            response = requests.get(url, params=params, headers=UA, timeout=timeout)
            if response.status_code in RETRYABLE_STATUS:
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            retryable = response is None or response.status_code in RETRYABLE_STATUS
            if not retryable or attempt == attempts - 1:
                raise
            time.sleep(_retry_delay(response, attempt))

    raise RuntimeError(f"Public API request failed after retries: {url}") from last_error


def fetch_musicbrainz_peru(query: str = "area:Peru", page_size: int = 100, max_pages: int = 10) -> pd.DataFrame:
    rows: list[dict] = []
    for page in range(max_pages):
        payload = _get_json(
            "https://musicbrainz.org/ws/2/artist/",
            params={"query": query, "fmt": "json", "limit": page_size, "offset": page * page_size},
            timeout=60,
        )
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
        time.sleep(1.2)
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
    payload = _get_json(
        "https://query.wikidata.org/sparql",
        params={"query": query, "format": "json"},
        timeout=90,
    )
    bindings = payload.get("results", {}).get("bindings", [])
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
