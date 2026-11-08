#!/usr/bin/env python3
"""One bounded source-pinned witness against bounding-box-area ranking."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
SOURCE = REPO / "generators" / "996fc37f49d9" / "generator.py"
OUT = Path(__file__).with_name("witness.json")
EXPECTED_SHA = "8ca3ae432da24852b9302c1509d02a3b0f2af966cb8fa4a597a5fc7172463745"
PROBE_SEED_HEX = "3af73402da8c456b9bf681afa7839cdb61b436a7710d5f5065741c5725ebad96"

sys.path.insert(0, str(REPO / "shared" / "runtime"))

actual_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if actual_sha != EXPECTED_SHA:
    raise SystemExit(f"source hash mismatch: {actual_sha}")

spec = importlib.util.spec_from_file_location("ticket_target_996fc37f49d9", SOURCE)
if spec is None or spec.loader is None:
    raise SystemExit("could not load pinned generator")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

seed = int(PROBE_SEED_HEX, 16)
sample_index = 0  # (seed + 0) % 12 == 10, a declared diagnostic slot.
grid = mod.generate(seed, sample_index)
errors = mod.self_check(grid)
if errors:
    raise SystemExit("generated scene is not lawful: " + "; ".join(errors))

components = mod._components(grid)
area_output = mod.rule_mirror(grid)
bbox_output = mod._competitor_bounding_box(grid)
if bbox_output is None or bbox_output == area_output:
    raise SystemExit("pinned diagnostic draw did not refute bounding-box ranking")

component_rows = []
for cells in sorted(components, key=lambda cells: min(cells)):
    component_rows.append({
        "top_left": list(min(cells)),
        "occupied_area": len(cells),
        "bounding_box_area": mod._box_area(cells),
        "input_colour": grid[cells[0][0]][cells[0][1]],
    })

diffs = [
    {"row": r, "col": c, "area_rank": area_output[r][c], "bbox_rank": bbox_output[r][c]}
    for r in range(len(grid))
    for c in range(len(grid[0]))
    if area_output[r][c] != bbox_output[r][c]
]
report = {
    "ticket_id": "ticket-784a645d1ea82afd",
    "task_id": mod.TASK_ID,
    "source_sha256": actual_sha,
    "rule_hash": mod.RULE_HASH,
    "probe_seed_hex": PROBE_SEED_HEX,
    "seed_integer": seed,
    "sample_index": sample_index,
    "shortcut": "rank connected components by bounding-box area instead of occupied-cell area",
    "lawful": True,
    "self_check_errors": errors,
    "components_in_scan_order": component_rows,
    "input": grid,
    "expected_area_rank_output": area_output,
    "shortcut_bbox_rank_output": bbox_output,
    "different_cells": diffs,
    "conclusion": "The lawful pinned draw reverses occupied-area and bounding-box-area order, so the shortcut disagrees with the task rule.",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"PASS source={actual_sha} components={len(components)} differing_cells={len(diffs)}")
print("areas/boxes:", [(row["occupied_area"], row["bounding_box_area"]) for row in component_rows])
print(OUT)
