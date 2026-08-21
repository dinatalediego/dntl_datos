from __future__ import annotations

import pandas as pd

from dntl_datos.io import read_latest_dataset, write_layer_dataset


def build_market_daily_features(root: str = "data") -> pd.DataFrame | None:
    df = read_latest_dataset("silver", "yahoo_finance", "prices", root=root, required=False)
    if df is None or df.empty or not {"ticker", "date", "close"}.issubset(df.columns):
        return None

    out = df.sort_values(["ticker", "date"]).copy()
    grouped_close = out.groupby("ticker", sort=False)["close"]
    out["daily_return"] = grouped_close.pct_change()
    out["ma_20"] = grouped_close.transform(lambda s: s.rolling(20, min_periods=5).mean())
    out["ma_60"] = grouped_close.transform(lambda s: s.rolling(60, min_periods=20).mean())
    out["volatility_30d_ann"] = out.groupby("ticker", sort=False)["daily_return"].transform(
        lambda s: s.rolling(30, min_periods=10).std() * (252 ** 0.5)
    )
    out["drawdown"] = out["close"] / grouped_close.cummax() - 1.0
    out["year"] = out["date"].dt.year.astype("Int64")
    out["month"] = out["date"].dt.to_period("M").astype("string")
    write_layer_dataset(out, "marts", "public", "market_daily_features", root=root)
    return out


def build_macro_country_year(root: str = "data") -> pd.DataFrame | None:
    df = read_latest_dataset("silver", "world_bank", "indicators", root=root, required=False)
    if df is None or df.empty:
        return None

    out = (
        df.pivot_table(
            index=["year", "country_code", "country"],
            columns="indicator",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(columns=None)
        .sort_values(["country_code", "year"])
    )
    write_layer_dataset(out, "marts", "public", "macro_country_year", root=root)
    return out


def _first_non_null(series: pd.Series):
    values = series.dropna()
    return values.iloc[0] if not values.empty else None


def _join_unique(series: pd.Series) -> str | None:
    values = sorted({str(v).strip() for v in series.dropna() if str(v).strip()})
    return " | ".join(values) if values else None


def build_peru_artist_master(root: str = "data") -> pd.DataFrame | None:
    mb = read_latest_dataset("silver", "musicbrainz", "peru_artists", root=root, required=False)
    wd = read_latest_dataset("silver", "wikidata", "peru_musicians", root=root, required=False)
    if (mb is None or mb.empty) and (wd is None or wd.empty):
        return None

    mb_cols = [
        "artist_key", "musicbrainz_id", "musicbrainz_name", "artist_type", "gender", "country",
        "begin_area", "area", "disambiguation", "musicbrainz_score",
    ]
    wd_cols = ["artist_key", "wikidata_id", "wikidata_name", "occupation", "genre", "birth_date"]

    if mb is not None and not mb.empty:
        mb = mb[mb["artist_key"].notna()].copy()
        mb = mb.sort_values("score", ascending=False, na_position="last").drop_duplicates("artist_key")
        mb = mb.rename(columns={
            "name": "musicbrainz_name",
            "type": "artist_type",
            "score": "musicbrainz_score",
        })
        for column in mb_cols:
            if column not in mb.columns:
                mb[column] = pd.NA
        mb = mb[mb_cols]
    else:
        mb = pd.DataFrame(columns=mb_cols)

    if wd is not None and not wd.empty:
        wd = wd[wd["artist_key"].notna()].copy()
        wd = (
            wd.groupby("artist_key", dropna=False)
            .agg(
                wikidata_id=("wikidata_id", _first_non_null),
                wikidata_name=("name", _first_non_null),
                occupation=("occupation", _join_unique),
                genre=("genre", _join_unique),
                birth_date=("birth_date", _first_non_null),
            )
            .reset_index()
        )
        for column in wd_cols:
            if column not in wd.columns:
                wd[column] = pd.NA
        wd = wd[wd_cols]
    else:
        wd = pd.DataFrame(columns=wd_cols)

    out = mb.merge(wd, on="artist_key", how="outer", indicator="match_status")
    out["artist_name"] = out["musicbrainz_name"].combine_first(out["wikidata_name"])
    out["match_status"] = out["match_status"].map({
        "both": "matched",
        "left_only": "musicbrainz_only",
        "right_only": "wikidata_only",
    }).astype("string")

    ordered = [
        "artist_key", "artist_name", "match_status", "musicbrainz_id", "wikidata_id",
        "artist_type", "gender", "country", "begin_area", "area", "occupation", "genre",
        "birth_date", "musicbrainz_score", "disambiguation",
    ]
    out = out[[c for c in ordered if c in out.columns]].sort_values("artist_name", na_position="last")
    write_layer_dataset(out, "marts", "public", "peru_artist_master", root=root)
    return out


def build_billboard_artist_snapshot(root: str = "data") -> pd.DataFrame | None:
    frames: list[pd.DataFrame] = []
    for dataset in ["hot-100", "billboard-200", "latin-songs"]:
        df = read_latest_dataset("silver", "billboard_unofficial", dataset, root=root, required=False)
        if df is not None and not df.empty:
            frames.append(df)
    if not frames:
        return None

    out = pd.concat(frames, ignore_index=True)
    out["chart_points"] = (101 - out["rank"]).clip(lower=0)
    artist_master = read_latest_dataset("marts", "public", "peru_artist_master", root=root, required=False)
    if artist_master is not None and not artist_master.empty:
        lookup = artist_master[["artist_key", "artist_name", "match_status"]].drop_duplicates("artist_key")
        out = out.merge(lookup, on="artist_key", how="left")
        out["is_peruvian_catalog_match"] = out["artist_name"].notna()
    else:
        out["is_peruvian_catalog_match"] = False

    write_layer_dataset(out, "marts", "public", "billboard_artist_snapshot", root=root)
    return out


def build_marts(root: str = "data") -> dict[str, int]:
    builders = {
        "market_daily_features": build_market_daily_features,
        "macro_country_year": build_macro_country_year,
        "peru_artist_master": build_peru_artist_master,
        "billboard_artist_snapshot": build_billboard_artist_snapshot,
    }
    summary: dict[str, int] = {}
    for name, builder in builders.items():
        result = builder(root=root)
        if result is not None:
            summary[name] = len(result)
    return summary
