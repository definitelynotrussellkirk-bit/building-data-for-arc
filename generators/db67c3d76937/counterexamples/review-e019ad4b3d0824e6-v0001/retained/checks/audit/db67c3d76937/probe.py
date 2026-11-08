"""Source-bound findings-only audit; run through the public review wrapper."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "db67c3d76937"
HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def coordinates(grid):
    by = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                by.setdefault(color, []).append((r, c))
    return by


def paint_selected(grid, by, selected):
    output = [row[:] for row in grid]
    hits = {}
    for color in selected:
        (r1, c1), (r2, c2) = by[color]
        if r1 == r2:
            points = [(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)]
        else:
            points = [(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)]
        for point in points:
            hits.setdefault(point, []).append(color)
    for (r, c), colors in hits.items():
        output[r][c] = 9 if len(colors) > 1 else colors[0]
    return output


def one_pair_per_orientation(grid):
    """Connect the first encountered horizontal and vertical pair only."""
    by = coordinates(grid)
    selected = []
    seen = set()
    for color, points in by.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        orientation = "horizontal" if r1 == r2 else "vertical" if c1 == c2 else None
        if orientation is not None and orientation not in seen:
            selected.append(color)
            seen.add(orientation)
    return paint_selected(grid, by, selected)


def two_lowest_colors(grid):
    """The prior retained audit's count-limited shortcut, independently rebuilt."""
    by = coordinates(grid)
    return paint_selected(grid, by, sorted(by)[:2])


def prepare():
    root = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK, root=root)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    with canonical_path(root).open() as stream:
        row = next(json.loads(line) for line in stream if json.loads(line).get("task_id") == TASK)
    rules = row["program_solution"]
    cases = []
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = module.generate(17, index, difficulty=band)
            cases.append({
                "kind": "generated", "seed": 17, "sample_index": index,
                "difficulty": band, "overrides": {}, "input": grid,
                "self_check": module.self_check(grid, difficulty=band),
                "nonzero_color_count": len(coordinates(grid)),
            })
    for pair in canonical:
        cases.append({"kind": "canonical", **pair,
                      "self_check": module.self_check(pair["input"]),
                      "nonzero_color_count": len(coordinates(pair["input"]))})
    for index, case in enumerate(cases):
        case["apply_index"] = index
        case["rival_outputs"] = {
            "one_pair_per_orientation": one_pair_per_orientation(case["input"]),
            "two_lowest_colors": two_lowest_colors(case["input"]),
        }
    report = {
        "task_id": TASK,
        "source_path": str(source.relative_to(root)),
        "source_sha256": source_sha,
        "canonical_program_sha256": digest(rules),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sampling": {"seed": 17, "sample_indices_inclusive": [0, 11],
                     "bands": ["easy", "medium", "hard"], "per_band": 12},
        "cases": cases,
    }
    (HERE / "probe-inputs.json").write_text(json.dumps(report, indent=2) + "\n")
    (HERE / "inputs.json").write_text(json.dumps({"inputs": [c["input"] for c in cases]}) + "\n")
    print(json.dumps({"source_sha256": source_sha, "canonical_program_sha256": digest(rules),
                      "generated_inputs": 36, "canonical_inputs": len(canonical),
                      "generated_unique_inputs": len({json.dumps(c["input"]) for c in cases if c["kind"] == "generated"}),
                      "canonical_domain_rejections": sum(bool(c["self_check"]) for c in cases if c["kind"] == "canonical")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare"])
    parser.parse_args()
    prepare()
