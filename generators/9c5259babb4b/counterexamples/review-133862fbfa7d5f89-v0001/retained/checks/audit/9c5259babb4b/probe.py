#!/usr/bin/env python3
"""Scoped audit: asymmetric 8-connected, non-4-connected support hole."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TASK = "9c5259babb4b"
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
path = ROOT / f"repo/generators/{TASK}/generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def objects(grid, bg, diagonal=True):
    cells = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x != bg}
    result = []
    while cells:
        start = min(cells)
        component = {start}
        queue = [start]
        cells.remove(start)
        for r, c in queue:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    p = r + dr, c + dc
                    if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1) and p in cells and grid[p[0]][p[1]] == grid[r][c]:
                        component.add(p)
                        queue.append(p)
                        cells.remove(p)
        result.append(component)
    return result


def label(cells):
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    h = {(r0 + r1 - r, c) for r, c in cells} == cells
    v = {(r, c0 + c1 - c) for r, c in cells} == cells
    return 1 if h else 3 if v else 6


def connected4(cells):
    seen = {min(cells)}
    queue = list(seen)
    for r, c in queue:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = r + dr, c + dc
            if p in cells and p not in seen:
                seen.add(p)
                queue.append(p)
    return seen == cells


def solve(grid, shortcut=False):
    counts = {x: sum(row.count(x) for row in grid) for x in set(sum(grid, [])) if x != 0}
    bg = max(counts, key=lambda x: (counts[x], -x)) if counts else 0
    output = [[bg] * len(grid[0]) for row in grid]
    for cells in objects(grid, bg):
        if len(cells) == 1:
            continue
        # Shortcut: non-4-connected objects are assumed symmetric. A vertical
        # symmetry case uses the ordinary precedence rule; otherwise blue is
        # returned without any top-bottom reflection test.
        if shortcut and not connected4(cells):
            c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
            vertical = {(r, c0 + c1 - c) for r, c in cells} == cells
            color = label(cells) if vertical else 1
        else:
            color = label(cells)
        for r, c in cells:
            output[r][c] = color
    return output


canonical = None
with (ROOT / "repo/shared/data/canonical/puzzles.jsonl").open() as f:
    for line in f:
        row = json.loads(line)
        if row.get("task_id") == TASK and row.get("content_hash") == TASK:
            canonical = row
            break
assert canonical is not None
canonical_pairs = canonical["train"] + canonical["test"]
canonical_results = []
for index, pair in enumerate(canonical_pairs):
    correct = solve(pair["input"])
    rival = solve(pair["input"], shortcut=True)
    assert correct == pair["output"] == rival
    canonical_results.append({"index": index, "reference_equals_stored": True, "rival_equals_stored": True})

samples = []
for index in range(8):
    samples.append((1000, index, {}, gen.generate(1000, index)))
for index, profile in enumerate(gen.GENERAL_PROFILES):
    overrides = {"scene_profile": profile}
    samples.append((501, index, overrides, gen.generate(501, index, **overrides)))
generated_results = []
for seed, index, overrides, grid in samples:
    analysis = gen._analysis(grid)
    assert gen.self_check(grid) == []
    assert solve(grid) == gen.rule_mirror(grid) == solve(grid, shortcut=True)
    generated_results.append({"seed": seed, "sample_index": index, "difficulty": None, "overrides": overrides,
                              "observed_profile": analysis["scene_profile"], "input": grid,
                              "reference_output": solve(grid), "rival_output": solve(grid, shortcut=True),
                              "non4connected_retained_labels": [label(o) for o in objects(grid, analysis["facts"]["background"]) if len(o) > 1 and not connected4(o)],
                              "self_check": [], "rival_equals_reference": True})

# Handbuilt class_balanced scene. Duplicate symmetric shapes are intentional;
# current domain requires class counts, not distinct shapes.
witness = [[8] * 18 for _ in range(18)]
hshape = {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)}
vshape = {(c, r) for r, c in hshape}
ashape = {(0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3)}
for r0, c0, shape in ((1, 1, hshape), (1, 7, hshape), (7, 1, vshape), (7, 7, vshape), (12, 12, ashape)):
    for r, c in shape:
        witness[r0 + r][c0 + c] = 2
for r, c in ((0, 17), (17, 0), (17, 7)):
    witness[r][c] = 2
assert label(ashape) == 6 and not connected4(ashape)
assert gen.self_check(witness) == []
assert gen.observe_overrides(witness) == {"scene_profile": "class_balanced"}
expected, rival = solve(witness), solve(witness, shortcut=True)
assert expected == gen.rule_mirror(witness) and expected != rival

rule = canonical["program_solution"]
evidence = {
    "task_id": TASK, "finding": "asymmetric_non4connected_support_hole",
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "canonical_rule_raw_sha256": hashlib.sha256(rule.encode()).hexdigest(),
    "canonical_rule_normalized_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
    "canonical_content_hash": canonical["content_hash"], "canonical_source": canonical["source"],
    "canonical_results": canonical_results, "generated_results": generated_results,
    "witness": {"construction": "handbuilt; not a generate() return", "seed": None, "sample_index": None,
                "overrides": None, "input": witness, "self_check": [], "domain_accepted": True,
                "observed_profile": "class_balanced", "reference_output": expected, "rival_output": rival,
                "different_cells": [[r, c] for r in range(18) for c in range(18) if expected[r][c] != rival[r][c]],
                "asymmetric_normalized_cells": sorted(map(list, ashape)), "asymmetric_connected4": False},
    "racket_input_indices": {"generated": list(range(len(samples))), "witness": len(samples)},
}
(OUT / "input.json").write_text(json.dumps([grid for _, _, _, grid in samples] + [witness]) + "\n")
(OUT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"canonical_pairs_fit": len(canonical_results), "generated_scenes_fit": len(samples),
                  "witness_self_check": [], "witness_difference_cells": len(evidence["witness"]["different_cells"])}))
