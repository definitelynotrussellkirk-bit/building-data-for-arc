"""Find a generated lesson exposing an undeclared T4 shape-conditioned shortcut."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
GEN_PATH = REPO / "generators/7f31c4f794b2/generator.py"

spec = importlib.util.spec_from_file_location("audit_target_7f31", GEN_PATH)
g = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(g)

T4 = frozenset(g._SHAPE_VARIANTS["T4"])


def is_t4(obj):
    return g._shape_key(obj["cells"]) in T4


def candidate_skip_border_t4(grid):
    out = [row[:] for row in grid]
    for obj in g._components(grid):
        if obj["sides"] and not is_t4(obj):
            for r, c in obj["cells"]:
                out[r][c] = 7
    return out


def descriptors(grid):
    result = []
    for obj in g._components(grid):
        names = [name for name, variants in g._SHAPE_VARIANTS.items() if g._shape_key(obj["cells"]) in variants]
        result.append({
            "color": obj["color"],
            "size": len(obj["cells"]),
            "shape": names[0] if names else "unknown",
            "sides": sorted(obj["sides"]),
            "cells": [list(cell) for cell in obj["cells"]],
        })
    return result


# Verify the rival fits every canonical labeled pair, not just the training examples.
canonical = None
for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
    record = json.loads(line)
    if record.get("task_id") == "7f31c4f794b2":
        canonical = record
        break
assert canonical is not None
canonical_checks = []
for split in ("train", "test"):
    for index, pair in enumerate(canonical[split]):
        match = candidate_skip_border_t4(pair["input"]) == pair["output"]
        canonical_checks.append({"split": split, "index": index, "matches": match})
assert all(item["matches"] for item in canonical_checks), canonical_checks

found = None
for difficulty in ("easy", "medium", "hard"):
    for seed in range(5000):
        grids = [g.generate(seed, sample_index, difficulty=difficulty) for sample_index in range(4)]
        intended = [g.rule_mirror(grid) for grid in grids]
        rival = [candidate_skip_border_t4(grid) for grid in grids]
        demo_fit = [rival[i] == intended[i] for i in range(3)]
        query_diff = rival[3] != intended[3]
        demo_has_interior_t4 = any(
            is_t4(obj) and not obj["sides"]
            for grid in grids[:3]
            for obj in g._components(grid)
        )
        if all(demo_fit) and query_diff and demo_has_interior_t4:
            found = {
                "difficulty": difficulty,
                "seed": seed,
                "sample_indices": [0, 1, 2, 3],
                "inputs": grids,
                "mirror_outputs": intended,
                "rival_outputs": rival,
                "component_descriptors": [descriptors(grid) for grid in grids],
                "demo_fit": demo_fit,
                "query_differs": query_diff,
                "demo_has_interior_t4": demo_has_interior_t4,
            }
            break
    if found is not None:
        break
assert found is not None

lesson = {
    "train": [
        {"input": found["inputs"][i], "output": found["mirror_outputs"][i]}
        for i in range(3)
    ],
    "test": [{"input": found["inputs"][3]}],
}
(HERE / "generated_lesson.json").write_text(json.dumps(lesson, indent=2) + "\n")
(HERE / "all_inputs.json").write_text(json.dumps({"inputs": found["inputs"]}, indent=2) + "\n")
(HERE / "rival_outputs.json").write_text(json.dumps({"outputs": found["rival_outputs"]}, indent=2) + "\n")
report = {
    "schema": "7f31c4f794b2-shape-shortcut-search-v1",
    "rival": "recolor border-touching components except T tetrominoes",
    "canonical_checks": canonical_checks,
    "canonical_all_match": all(item["matches"] for item in canonical_checks),
    **{key: value for key, value in found.items() if key not in {"inputs", "mirror_outputs", "rival_outputs"}},
}
(HERE / "search_report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "difficulty": found["difficulty"],
    "seed": found["seed"],
    "canonical_pairs_matched": len(canonical_checks),
    "demo_fit": found["demo_fit"],
    "query_differs": found["query_differs"],
    "demo_has_interior_t4": found["demo_has_interior_t4"],
}, indent=2))
