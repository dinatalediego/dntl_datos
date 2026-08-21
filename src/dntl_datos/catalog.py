from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from dntl_datos.io import write_layer_dataset


def _runtime_catalog(root: str) -> pd.DataFrame:
    rows: list[dict] = []
    root_path = Path(root)

    for manifest_path in root_path.glob("**/manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("layer") == "catalog":
            continue
        columns = manifest.get("columns") or []
        rows.append({
            "layer": manifest.get("layer", "raw"),
            "source": manifest.get("source"),
            "dataset": manifest.get("dataset"),
            "run_date": manifest.get("run_date"),
            "rows": manifest.get("rows"),
            "column_count": len(columns),
            "columns": " | ".join(map(str, columns)),
            "generated_at_utc": manifest.get("generated_at_utc"),
            "file": manifest.get("file"),
        })

    runtime = pd.DataFrame(rows)
    if runtime.empty:
        return pd.DataFrame(columns=["layer", "source", "dataset"])
    runtime = runtime.sort_values("run_date").drop_duplicates(
        ["layer", "source", "dataset"], keep="last"
    )
    return runtime


def _registry_catalog(registry_path: str) -> pd.DataFrame:
    path = Path(registry_path)
    if not path.exists():
        return pd.DataFrame(columns=["layer", "source", "dataset"])
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    registry = pd.DataFrame(payload.get("datasets", []))
    for column in ["keys", "consumers"]:
        if column in registry.columns:
            registry[column] = registry[column].apply(
                lambda value: " | ".join(map(str, value)) if isinstance(value, list) else value
            )
    return registry


def build_catalog(root: str = "data", registry_path: str = "config/catalog.yaml") -> pd.DataFrame:
    runtime = _runtime_catalog(root)
    registry = _registry_catalog(registry_path)

    if registry.empty:
        catalog = runtime
    elif runtime.empty:
        catalog = registry.copy()
    else:
        catalog = registry.merge(runtime, on=["layer", "source", "dataset"], how="outer")

    if "run_date" in catalog.columns:
        catalog["status"] = catalog["run_date"].notna().map({True: "materialized", False: "registered"})
    else:
        catalog["status"] = "registered"

    if not catalog.empty:
        catalog = catalog.sort_values(["layer", "source", "dataset"])
    write_layer_dataset(catalog, "catalog", "system", "datasets", root=root)
    return catalog
