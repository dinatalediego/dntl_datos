from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_yahoo_prices(tickers: list[str], period: str = "5y", interval: str = "1d") -> pd.DataFrame:
    raw = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
    )
    if raw.empty:
        return pd.DataFrame()

    if len(tickers) == 1:
        df = raw.reset_index()
        df["ticker"] = tickers[0]
        return df.rename(columns=str.lower)

    frames: list[pd.DataFrame] = []
    for ticker in tickers:
        if ticker not in raw.columns.get_level_values(0):
            continue
        tmp = raw[ticker].dropna(how="all").reset_index()
        tmp["ticker"] = ticker
        frames.append(tmp.rename(columns=str.lower))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
