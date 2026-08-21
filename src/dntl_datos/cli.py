from __future__ import annotations

import argparse
from pathlib import Path
import yaml

from dntl_datos.io import write_dataset
from dntl_datos.connectors.markets import fetch_yahoo_prices
from dntl_datos.connectors.macro import fetch_world_bank, fetch_bcrp
from dntl_datos.connectors.music import fetch_musicbrainz_peru, fetch_wikidata_peruvian_musicians, fetch_billboard_chart


def run(config_path: str = "config/sources.yaml") -> None:
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

    y = cfg["markets"]["yahoo_finance"]
    if y.get("enabled"):
        write_dataset(fetch_yahoo_prices(y["tickers"], y["period"], y["interval"]), "yahoo_finance", "prices")

    wb = cfg["macro"]["world_bank"]
    if wb.get("enabled"):
        write_dataset(fetch_world_bank(wb["countries"], wb["indicators"]), "world_bank", "indicators")

    b = cfg["macro"]["bcrp"]
    if b.get("enabled"):
        write_dataset(fetch_bcrp(b["series"], b["start_year"]), "bcrp", "series")

    mb = cfg["music"]["musicbrainz_peru"]
    if mb.get("enabled"):
        write_dataset(fetch_musicbrainz_peru(mb["query"], mb["page_size"], mb["max_pages"]), "musicbrainz", "peru_artists")

    wd = cfg["music"]["wikidata_peru"]
    if wd.get("enabled"):
        write_dataset(fetch_wikidata_peruvian_musicians(wd["limit"]), "wikidata", "peru_musicians")

    bb = cfg["music"]["billboard"]
    if bb.get("enabled"):
        for chart in bb["charts"]:
            write_dataset(fetch_billboard_chart(chart), "billboard_unofficial", chart)


def main() -> None:
    parser = argparse.ArgumentParser(description="Public batch data hub")
    parser.add_argument("--config", default="config/sources.yaml")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
