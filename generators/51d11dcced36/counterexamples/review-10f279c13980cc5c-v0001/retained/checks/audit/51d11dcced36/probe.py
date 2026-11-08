#!/usr/bin/env python3
"""Audit 51d11dcced36 for color-role shortcuts in the selected generator."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "repo"
TASK_ID = "51d11dcced36"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
OUT = Path(__file__).with_name("probe.json")
SEED = "audit-51d11dcced36-color-role-v1"
PER_BAND = 100
BANDS = ("easy", None, "hard")

sys.path.insert(0, str(REPO / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location("audit_target_51d11dcced36", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    out: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out.setdefault(value, []).append((r, c))
    return out


def true_rule(grid: list[list[int]]) -> list[list[int]]:
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in by_color(grid).items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                result[r][c] = color
    return result


def rival_ignore_colors_2_and_3(grid: list[list[int]]) -> list[list[int]]:
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in by_color(grid).items():
        if color in {2, 3} or len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                result[r][c] = color
    return result


def canonical_task() -> dict:
    with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise RuntimeError("canonical task not found")


band_rows = {}
all_generated_equal = True
all_color_counts = Counter()
for band in BANDS:
    label = band or "medium"
    rows = []
    for sample_index in range(PER_BAND):
        grid = module.generate(SEED, sample_index, difficulty=band)
        counts = Counter(v for row in grid for v in row if v)
        exact_2_or_3 = {str(color): counts[color] for color in (2, 3)}
        same = true_rule(grid) == rival_ignore_colors_2_and_3(grid)
        all_generated_equal &= same
        all_color_counts.update({f"color_{color}_count_{counts[color]}": 1 for color in (2, 3)})
        rows.append({
            "sample_index": sample_index,
            "shape": [len(grid), len(grid[0])],
            "color_2_count": counts[2],
            "color_3_count": counts[3],
            "rival_matches_true_rule": same,
        })
    band_rows[label] = {
        "draws": len(rows),
        "color_2_count_histogram": dict(Counter(row["color_2_count"] for row in rows)),
        "color_3_count_histogram": dict(Counter(row["color_3_count"] for row in rows)),
        "rival_matches": sum(row["rival_matches_true_rule"] for row in rows),
        "sample_indices": [0, PER_BAND - 1],
    }

canonical = canonical_task()
canonical_pairs = canonical["train"] + (canonical["test"] if isinstance(canonical["test"], list) else [canonical["test"]])
canonical_results = []
for index, pair in enumerate(canonical_pairs):
    actual = true_rule(pair["input"])
    expected_matches_mirror = actual == pair["output"]
    rival = rival_ignore_colors_2_and_3(pair["input"])
    canonical_results.append({
        "pair_index": index,
        "expected_matches_python_mirror": expected_matches_mirror,
        "rival_matches_expected": rival == pair["output"],
        "colors_2_and_3_counts": {
            "2": sum(v == 2 for row in pair["input"] for v in row),
            "3": sum(v == 3 for row in pair["input"] for v in row),
        },
    })

report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": sha256(GENERATOR),
    "rule_hash": "54af2954d411",
    "seed": SEED,
    "per_band": PER_BAND,
    "bands": band_rows,
    "claim": "A rival that applies the rectangle rule to every exact-two color except colors 2 and 3 is indistinguishable on all sampled generated inputs.",
    "all_generated_rival_matches": all_generated_equal,
    "canonical_pairs": canonical_results,
    "canonical_failures_of_rival": sum(not row["rival_matches_expected"] for row in canonical_results),
    "passes": all_generated_equal and all(row["expected_matches_python_mirror"] for row in canonical_results) and any(not row["rival_matches_expected"] for row in canonical_results),
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passes"] else 1)
