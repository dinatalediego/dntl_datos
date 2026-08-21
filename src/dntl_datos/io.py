from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd


def write_dataset(df: pd.DataFrame, source: str, dataset: str, root: str = "data") -> Path:
    run_date = datetime.now(timezone.utc).date().isoformat()
    out_dir = Path(root) / "raw" / source / dataset / f"run_date={run_date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "data.parquet"
    df.to_parquet(out, index=False)

    manifest = {
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
