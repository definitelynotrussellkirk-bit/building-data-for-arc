from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "b650a355848c"
EXPECTED_GENERATOR_SHA256 = "c1d66f3bfe7b9c25b35c37745ddf4e3630ad89c071704126847ed5028e9c9a29"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
OUT = ROOT.parent / "checks/tickets/ticket-a0f8f09b9f0a9a2e"
START = time.perf_counter()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def write_json(name: str, value) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


actual_source_sha = sha256_bytes(GENERATOR_PATH.read_bytes())
assert actual_source_sha == EXPECTED_GENERATOR_SHA256
spec = importlib.util.spec_from_file_location("ticket_b650_generator", GENERATOR_PATH)
assert spec and spec.loader
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

grid = g.generate(0, 1)
assert g.self_check(grid) == []

components = g._components(grid)
shapes = []
markers = []
for cells in components:
    r, c = next(iter(cells))
    value = grid[r][c]
    if value == 6:
        rs = [row for row, _ in cells]
        cs = [col for _, col in cells]
        shapes.append(
            {
                "cells": sorted([list(cell) for cell in cells]),
                "bbox": [min(rs), max(rs), min(cs), max(cs)],
            }
        )
    elif len(cells) == 1:
        markers.append({"row": r, "col": c, "color": value})

assert len(shapes) == len(markers) == 3

def bbox_distance(marker, bbox) -> int:
    r1, r2, c1, c2 = bbox
    mr, mc = marker["row"], marker["col"]
    dr = 0 if r1 <= mr <= r2 else min(abs(mr - r1), abs(mr - r2))
    dc = 0 if c1 <= mc <= c2 else min(abs(mc - c1), abs(mc - c2))
    return dr + dc

matrix = [
    [bbox_distance(marker, shape["bbox"]) for marker in markers]
    for shape in shapes
]
permutations = []
for permutation in itertools.permutations(range(len(markers))):
    cost = sum(matrix[shape_index][marker_index] for shape_index, marker_index in enumerate(permutation))
    permutations.append({"marker_indices": list(permutation), "total_distance": cost})
minimum = min(row["total_distance"] for row in permutations)
optimal = [row for row in permutations if row["total_distance"] == minimum]
assert optimal == [{"marker_indices": [0, 1, 2], "total_distance": 11}]


def one_to_one_output(permutation: list[int]) -> list[list[int]]:
    infos = []
    for shape_index, shape in enumerate(shapes):
        r1, r2, c1, c2 = shape["bbox"]
        infos.append(
            {
                **shape,
                "r1": r1,
                "r2": r2,
                "c1": c1,
                "c2": c2,
                "color": markers[permutation[shape_index]]["color"],
            }
        )
    vertical = len(grid) > len(grid[0])
    infos.sort(key=(lambda info: info["r1"]) if vertical else (lambda info: info["c1"]))
    out_h = len(infos) * 4 if vertical else 4
    out_w = 4 if vertical else len(infos) * 4
    output = [[0 for _ in range(out_w)] for _ in range(out_h)]
    for index, info in enumerate(infos):
        base_r = index * 4 if vertical else 0
        base_c = 0 if vertical else index * 4
        for row, col in info["cells"]:
            output[base_r + row - info["r1"]][base_c + col - info["c1"]] = info["color"]
    return output

rival_output = one_to_one_output(optimal[0]["marker_indices"])

sources = set()
with canonical_path(ROOT).open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
            sources.add(row["program_solution"])
assert len(sources) == 1
source = sources.pop()
assert source.startswith("(rule! ") and source.endswith(")")
callable_source = source[len("(rule! ") : -1]
literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
with RacketBridge(max_calls_before_restart=32) as bridge:
    selected_output = normalize_grid(bridge.eval_text(f"({callable_source} '{literal})"))

assert selected_output != rival_output
selected_colors = sorted({value for row in selected_output for value in row if value})
rival_colors = sorted({value for row in rival_output for value in row if value})
assert selected_colors == [3]
assert rival_colors == [1, 3, 9]

retained = ROOT / "generators" / TASK_ID / "counterexamples/review-77585fe0f3de648e-v0001"
assert grid == json.loads((retained / "input.json").read_text())
retained_racket = json.loads((retained / "racket.json").read_text())
assert selected_output == retained_racket["results"][0]["output"]
assert rival_output == json.loads((retained / "rival.json").read_text())

write_json("input.json", grid)
write_json("selected-output.json", selected_output)
write_json("one-to-one-rival-output.json", rival_output)
report = {
    "schema": "arcpuzzles-supplementary-adversarial-witness-v1",
    "ticket_id": "ticket-a0f8f09b9f0a9a2e",
    "task_id": TASK_ID,
    "status": "reproduced_existing_unresolved_finding",
    "shortcut_or_rival": "equal shape/marker counts imply a one-to-one minimum-total-distance pairing",
    "generator_sha256": actual_source_sha,
    "rule_hash": "2cb975ac778f",
    "seed": 0,
    "sample_index": 1,
    "difficulty": None,
    "self_check": [],
    "distance_matrix_shape_by_marker": matrix,
    "one_to_one_optimum": optimal[0],
    "selected_output_nonzero_colors": selected_colors,
    "rival_output_nonzero_colors": rival_colors,
    "selected_differs_from_rival": True,
    "exactly_matches_retained_witness": True,
    "input_sha256": sha256_bytes(stable_bytes(grid)),
    "selected_output_sha256": sha256_bytes(stable_bytes(selected_output)),
    "rival_output_sha256": sha256_bytes(stable_bytes(rival_output)),
    "elapsed_seconds": round(time.perf_counter() - START, 6),
    "limit": "single source-bound witness; no fresh census",
}
write_json("report.json", report)
print(json.dumps(report, indent=2, sort_keys=True))
