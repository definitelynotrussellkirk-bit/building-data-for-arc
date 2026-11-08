#!/usr/bin/env python3
"""Audit d3412a5b76a6 for the unique-largest-panel shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "repo"
TASK_ID = "d3412a5b76a6"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
OUT = Path(__file__).with_name("probe.json")
SEED = "audit-d3412a5b76a6-size-shortcut-v1"
PER_BAND = 100
BANDS = ("easy", None, "hard")

sys.path.insert(0, str(REPO / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location("audit_target_d3412a5b76a6", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    starts = [0]
    panels = []
    for divider in dividers + [w]:
        start = starts[-1]
        if start < divider:
            panels.append([row[start:divider] for row in grid])
        starts.append(divider + 1)
    return panels


def occupancy(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value not in {0, 9}}


def render(cells: set[tuple[int, int]], h: int, w: int) -> list[list[int]]:
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        out[r][c] = 8
    return out


def true_rule(grid: list[list[int]]) -> list[list[int]]:
    panels = split_panels(grid)
    masks = [occupancy(panel) for panel in panels]
    for i, mask in enumerate(masks):
        if masks.count(mask) >= 2:
            return render(mask, len(panels[i]), len(panels[i][0]))
    raise ValueError("no repeated occupancy mask")


def rival_largest_panel(grid: list[list[int]]) -> list[list[int]]:
    panels = split_panels(grid)
    masks = [occupancy(panel) for panel in panels]
    index = max(range(len(masks)), key=lambda i: len(masks[i]))
    return render(masks[index], len(panels[index]), len(panels[index][0]))


def canonical_task() -> dict:
    with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise RuntimeError("canonical task not found")


band_rows = {}
all_generated_equal = True
for band in BANDS:
    label = band or "medium"
    records = []
    for sample_index in range(PER_BAND):
        grid = module.generate(SEED, sample_index, difficulty=band)
        panels = split_panels(grid)
        sizes = [len(occupancy(panel)) for panel in panels]
        true = true_rule(grid)
        rival = rival_largest_panel(grid)
        same = true == rival
        all_generated_equal &= same
        records.append({
            "sample_index": sample_index,
            "shape": [len(grid), len(grid[0])],
            "panel_occupancy_sizes": sizes,
            "rival_matches_true_rule": same,
        })
    band_rows[label] = {
        "draws": len(records),
        "panel_size_tuples": {str(key): value for key, value in Counter(tuple(row["panel_occupancy_sizes"]) for row in records).items()},
        "rival_matches": sum(row["rival_matches_true_rule"] for row in records),
        "sample_indices": [0, PER_BAND - 1],
    }

canonical = canonical_task()
canonical_pairs = canonical["train"] + (canonical["test"] if isinstance(canonical["test"], list) else [canonical["test"]])
canonical_results = []
for index, pair in enumerate(canonical_pairs):
    actual = true_rule(pair["input"])
    expected_matches_mirror = actual == pair["output"]
    rival = rival_largest_panel(pair["input"])
    canonical_results.append({
        "pair_index": index,
        "panel_occupancy_sizes": [len(occupancy(panel)) for panel in split_panels(pair["input"])],
        "expected_matches_python_mirror": expected_matches_mirror,
        "rival_matches_expected": rival == pair["output"],
    })

report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": sha256(GENERATOR),
    "rule_hash": "e4864a16bb12",
    "seed": SEED,
    "per_band": PER_BAND,
    "bands": band_rows,
    "claim": "Selecting the panel with the largest occupied-cell count, without comparing masks, is indistinguishable on all sampled generated inputs because repeated panels always have 6 cells and the odd panel always has 5.",
    "all_generated_rival_matches": all_generated_equal,
    "canonical_pairs": canonical_results,
    "canonical_failures_of_rival": sum(not row["rival_matches_expected"] for row in canonical_results),
    "passes": all_generated_equal and all(row["expected_matches_python_mirror"] for row in canonical_results) and any(not row["rival_matches_expected"] for row in canonical_results),
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passes"] else 1)
