from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = "9c3781759581"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def bbox_crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if not cells:
        return []
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def columns_only_crop(grid):
    cols = [c for row in grid for c, value in enumerate(row) if value == 9]
    if not cols:
        return []
    c0, c1 = min(cols), max(cols)
    return [row[c0:c1 + 1] for row in grid]


canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical_rows = []
for index, pair in enumerate(canonical):
    truth = pair["output"]
    bbox = bbox_crop(pair["input"])
    rival = columns_only_crop(pair["input"])
    canonical_rows.append({
        "index": index,
        "split": pair.get("split"),
        "input": pair["input"],
        "authority_output": truth,
        "bbox_oracle_output": bbox,
        "columns_only_output": rival,
        "bbox_matches": bbox == truth,
        "columns_only_matches": rival == truth,
        "authority_shape": [len(truth), len(truth[0])],
        "columns_only_shape": [len(rival), len(rival[0])],
    })

bands = ("easy", "medium", "hard")
grids = []
metadata = []
for band in bands:
    for index in range(100):
        grid = GEN.generate(20261012, index, difficulty=band)
        grids.append(grid)
        div_cols = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
        metadata.append({
            "band": band,
            "sample_index": index,
            "shape": [len(grid), len(grid[0])],
            "divider_columns": div_cols,
            "self_check": GEN.self_check(grid, difficulty=band),
        })
catalog = Catalog(ROOT)
results = []
rule_hash_matches_catalog = True
for start in range(0, len(grids), 64):
    receipt = catalog.apply(TASK, grids[start:start + 64], reference="canonical", timeout=900)
    rule_hash_matches_catalog = rule_hash_matches_catalog and receipt["rule_hash_matches_catalog"]
    results.extend(receipt["results"])
assert rule_hash_matches_catalog
assert len(results) == len(grids)
rows = []
for grid, meta, item in zip(grids, metadata, results):
    authority = item["output"]
    bbox = bbox_crop(grid)
    rival = columns_only_crop(grid)
    rows.append({
        **meta,
        "valid_output": item["valid_output"],
        "error": item["error"],
        "bbox_matches": authority == bbox,
        "columns_only_matches": authority == rival,
        "full_height_bbox": len(authority) == len(grid),
    })

summary = {
    "draws": len(rows),
    "valid_outputs": sum(row["valid_output"] and row["error"] is None for row in rows),
    "self_check_passes": sum(row["self_check"] == [] for row in rows),
    "bbox_oracle_matches": sum(row["bbox_matches"] for row in rows),
    "columns_only_rival_matches": sum(row["columns_only_matches"] for row in rows),
    "full_height_authority_outputs": sum(row["full_height_bbox"] for row in rows),
    "unique_inputs": len({json.dumps(grid, separators=(",", ":")) for grid in grids}),
    "per_band": {
        band: {
            "draws": sum(row["band"] == band for row in rows),
            "columns_only_matches": sum(row["band"] == band and row["columns_only_matches"] for row in rows),
        }
        for band in bands
    },
}
first = 0
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "source_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash_matches_catalog": rule_hash_matches_catalog,
    "finding": (
        "Generator makes every 9 marker part of a full-height divider column, "
        "so the wrong rule 'crop only between leftmost/rightmost 9 columns' "
        "matches every sampled authority label. Canonical inputs use two sparse "
        "9 markers and require cropping both rows and columns."
    ),
    "canonical": canonical_rows,
    "generated_census": summary,
    "generated_example": {
        "metadata": metadata[first],
        "input": grids[first],
        "authority_output": results[first]["output"],
        "columns_only_output": columns_only_crop(grids[first]),
    },
}
path = Path(__file__).with_name("column_crop_shortcut.json")
path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
print(path)
