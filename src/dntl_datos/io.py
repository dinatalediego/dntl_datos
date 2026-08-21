from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd


def _run_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def write_layer_dataset(
    df: pd.DataFrame,
    layer: str,
    source: str,
    dataset: str,
    root: str = "data",
) -> Path:
    run_date = _run_date()
    out_dir = Path(root) / layer / source / dataset / f"run_date={run_date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "data.parquet"
    df.to_parquet(out, index=False)

    manifest = {
        "layer": layer,
        "source": source,
        "dataset": dataset,
        "run_date": run_date,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "file": str(out),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def write_dataset(df: pd.DataFrame, source: str, dataset: str, root: str = "data") -> Path:
    """Backward-compatible writer for the immutable raw/bronze layer."""
    return write_layer_dataset(df, "raw", source, dataset, root=root)


def latest_dataset_path(layer: str, source: str, dataset: str, root: str = "data") -> Path | None:
    base = Path(root) / layer / source / dataset
    candidates = sorted(base.glob("run_date=*/data.parquet"), reverse=True)
    return candidates[0] if candidates else None


def read_latest_dataset(
    layer: str,
    source: str,
    dataset: str,
    root: str = "data",
    required: bool = True,
) -> pd.DataFrame | None:
    path = latest_dataset_path(layer, source, dataset, root=root)
    if path is None:
        if required:
            raise FileNotFoundError(f"No dataset found: {layer}/{source}/{dataset}")
        return None
    return pd.read_parquet(path)
