from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from dntl_datos.catalog import build_catalog
from dntl_datos.connectors.macro import fetch_bcrp, fetch_world_bank
from dntl_datos.connectors.markets import fetch_yahoo_prices
from dntl_datos.connectors.music import (
    fetch_billboard_chart,
    fetch_musicbrainz_peru,
    fetch_wikidata_peruvian_musicians,
)
from dntl_datos.io import write_dataset
from dntl_datos.marts import build_marts
from dntl_datos.silver import build_silver


def ingest(config_path: str = "config/sources.yaml") -> dict[str, int]:
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    summary: dict[str, int] = {}

    y = cfg["markets"]["yahoo_finance"]
    if y.get("enabled"):
        df = fetch_yahoo_prices(y["tickers"], y["period"], y["interval"])
        write_dataset(df, "yahoo_finance", "prices")
        summary["yahoo_finance/prices"] = len(df)

    wb = cfg["macro"]["world_bank"]
    if wb.get("enabled"):
        df = fetch_world_bank(wb["countries"], wb["indicators"])
        write_dataset(df, "world_bank", "indicators")
        summary["world_bank/indicators"] = len(df)

    b = cfg["macro"]["bcrp"]
    if b.get("enabled"):
        df = fetch_bcrp(b["series"], b["start_year"])
        write_dataset(df, "bcrp", "series")
        summary["bcrp/series"] = len(df)

    mb = cfg["music"]["musicbrainz_peru"]
    if mb.get("enabled"):
        df = fetch_musicbrainz_peru(mb["query"], mb["page_size"], mb["max_pages"])
        write_dataset(df, "musicbrainz", "peru_artists")
        summary["musicbrainz/peru_artists"] = len(df)

    wd = cfg["music"]["wikidata_peru"]
    if wd.get("enabled"):
        df = fetch_wikidata_peruvian_musicians(wd["limit"])
        write_dataset(df, "wikidata", "peru_musicians")
        summary["wikidata/peru_musicians"] = len(df)

    bb = cfg["music"]["billboard"]
    if bb.get("enabled"):
        for chart in bb["charts"]:
            df = fetch_billboard_chart(chart)
            write_dataset(df, "billboard_unofficial", chart)
            summary[f"billboard_unofficial/{chart}"] = len(df)

    return summary


def run(config_path: str = "config/sources.yaml", stage: str = "all") -> dict[str, dict[str, int] | int]:
    result: dict[str, dict[str, int] | int] = {}

    if stage in {"raw", "all"}:
        result["raw"] = ingest(config_path)
    if stage in {"silver", "all"}:
        result["silver"] = build_silver()
    if stage in {"marts", "all"}:
        result["marts"] = build_marts()
    if stage in {"catalog", "all"}:
        result["catalog"] = len(build_catalog())

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Public batch data hub")
    parser.add_argument("--config", default="config/sources.yaml")
    parser.add_argument(
        "--stage",
        choices=["raw", "silver", "marts", "catalog", "all"],
        default="all",
        help="Pipeline stage to execute. 'all' runs raw -> silver -> marts -> catalog.",
    )
    args = parser.parse_args()
    result = run(args.config, args.stage)
    print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
