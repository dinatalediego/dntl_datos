from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dntl_datos.io import write_layer_dataset


def build_catalog(root: str = "data") -> pd.DataFrame:
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

    catalog = pd.DataFrame(rows)
    if not catalog.empty:
        catalog = catalog.sort_values(["layer", "source", "dataset", "run_date"])
    write_layer_dataset(catalog, "catalog", "system", "datasets", root=root)
    return catalog
