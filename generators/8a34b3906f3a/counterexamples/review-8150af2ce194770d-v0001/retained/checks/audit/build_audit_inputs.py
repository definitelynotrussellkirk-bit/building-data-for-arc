#!/usr/bin/env python3
"""Build reproducible audit inputs and source-bound distribution measurements."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
OUT = PACKET / "checks" / "audit"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def components(grid: list[list[int]], color: int | None = None) -> int:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    total = 0
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0 or (color is not None and value != color) or (r, c) in seen:
                continue
            total += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    nv = grid[nr][nc]
                    if nv == 0 or (color is not None and nv != color):
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
    return total


def canonical_row(task_id: str) -> dict[str, Any]:
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main() -> None:
    # Audit 0fce75f9162a: an advertised degenerate is not rejected, and an exact
    # n_blobs override is silently ignored in the easy band.
    task = "0fce75f9162a"
    mod, source = load_generator(task)
    shared_cols = mod.generate(5, 0, difficulty="medium", texture="blobs_share_cols")
    base_easy = mod.generate(17, 0, difficulty="easy")
    one_blob_override = mod.generate(17, 0, difficulty="easy", n_blobs=1)
    # Illustrative rival: move the whole foreground by the global top offset.
    top = min(r for r, row in enumerate(shared_cols) for v in row if v != 0)
    global_shift = [[0 for _ in row] for row in shared_cols]
    for r, row in enumerate(shared_cols):
        for c, value in enumerate(row):
            if value:
                global_shift[r - top][c] = value
    write_json(OUT / task / "input.json", shared_cols)
    write_json(
        OUT / task / "probe.json",
        {
            "schema": "arcpuzzles-audit-probe-v1",
            "task_id": task,
            "generator_sha256": sha256(source),
            "seed": 5,
            "sample_index": 0,
            "difficulty": "medium",
            "overrides": {"texture": "blobs_share_cols"},
            "input": shared_cols,
            "self_check": mod.self_check(shared_cols, difficulty="medium"),
            "documented_domain": "advertised degenerate override; intentionally violates the disjoint-column invariant and should be rejected by self_check",
            "rival_name": "global_foreground_shift_to_top",
            "rival_output": global_shift,
            "override_probe": {
                "seed": 17,
                "sample_index": 0,
                "difficulty": "easy",
                "overrides": {"n_blobs": 1},
                "baseline_equals_override": base_easy == one_blob_override,
                "override_component_count": components(one_blob_override),
                "self_check": mod.self_check(one_blob_override, difficulty="easy"),
            },
        },
    )

    # Audit 8a34b3906f3a: the generated domain removes the canonical center
    # marker/palette and collapses the sparse rotational pattern into one connected
    # color-2 motif. Keep a concrete generated sample and a 600-sample census.
    task = "8a34b3906f3a"
    mod, source = load_generator(task)
    sample = mod.generate(12345, 0, difficulty="easy")
    write_json(OUT / task / "input.json", sample)
    row = canonical_row(task)
    canonical_inputs = [pair["input"] for pair in row["train"] + row["test"]]
    canonical_stats = [
        {
            "pair_index": i,
            "palette": sorted({v for rr in grid for v in rr}),
            "center": grid[len(grid) // 2][len(grid[0]) // 2],
            "color2_components": components(grid, 2),
        }
        for i, grid in enumerate(canonical_inputs)
    ]
    counts: dict[str, dict[str, int]] = {}
    for difficulty in ("easy", "medium", "hard"):
        band = {
            "draws": 200,
            "self_check_pass": 0,
            "center_is_9": 0,
            "canonical_palette_0_2_9": 0,
            "color2_is_one_component": 0,
        }
        for sample_index in range(200):
            grid = mod.generate(12345, sample_index, difficulty=difficulty)
            palette = {v for rr in grid for v in rr}
            band["self_check_pass"] += int(not mod.self_check(grid, difficulty=difficulty))
            band["center_is_9"] += int(grid[len(grid) // 2][len(grid[0]) // 2] == 9)
            band["canonical_palette_0_2_9"] += int(palette == {0, 2, 9})
            band["color2_is_one_component"] += int(components(grid, 2) == 1)
        counts[difficulty] = band
    write_json(
        OUT / task / "probe.json",
        {
            "schema": "arcpuzzles-audit-probe-v1",
            "task_id": task,
            "generator_sha256": sha256(source),
            "seed": 12345,
            "sample_index": 0,
            "difficulty": "easy",
            "overrides": {},
            "input": sample,
            "self_check": mod.self_check(sample, difficulty="easy"),
            "documented_domain": "ordinary generated easy sample",
            "rival_name": "rotate_only_when_a_center_9_marker_is_present",
            "rival_output": sample,
            "sample_profile": {
                "palette": sorted({v for rr in sample for v in rr}),
                "center": sample[len(sample) // 2][len(sample[0]) // 2],
                "color2_components": components(sample, 2),
            },
            "canonical_profile": canonical_stats,
            "distribution_census": {
                "seed": 12345,
                "sample_indices": [0, 199],
                "draws_per_band": 200,
                "counts": counts,
            },
        },
    )


if __name__ == "__main__":
    main()
