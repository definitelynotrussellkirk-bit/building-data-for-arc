from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = "dcf954423fbb"
WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(grid, color=1):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result = []
    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in ORTHOGONAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(cells)))
    return sorted(result)


def border_sides(cells, height, width):
    sides = set()
    if any(row == 0 for row, _ in cells):
        sides.add("top")
    if any(row == height - 1 for row, _ in cells):
        sides.add("bottom")
    if any(col == 0 for _, col in cells):
        sides.add("left")
    if any(col == width - 1 for _, col in cells):
        sides.add("right")
    return sides


def exactly_one_border_side_rival(grid):
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for part in components(grid):
        if len(border_sides(part, height, width)) == 1:
            for row, col in part:
                output[row][col] = 2
    return output


pairs = canonical_pairs(TASK, root=REPO)
canonical = pairs[0]
assert module.self_check(canonical["input"]) == []
canonical_sides = [
    sorted(border_sides(part, len(canonical["input"]), len(canonical["input"][0])))
    for part in components(canonical["input"])
]
assert any(len(sides) >= 2 for sides in canonical_sides)

rival = exactly_one_border_side_rival(canonical["input"])
assert rival != canonical["output"]
(OUT / "input.json").write_text(json.dumps(canonical["input"], indent=2) + "\n")
(OUT / "rival-output.json").write_text(json.dumps(rival, indent=2) + "\n")

generated = []
scan = []
for band_index, band in enumerate((None, "easy", "medium", "hard")):
    for index in range(16):
        seed = 920_000 + band_index * 10_000 + index
        grid = module.generate(seed, index, difficulty=band)
        errors = module.self_check(grid)
        sides = [
            sorted(border_sides(part, len(grid), len(grid[0])))
            for part in components(grid)
        ]
        generated.append(grid)
        scan.append(
            {
                "difficulty": band,
                "seed": seed,
                "sample_index": index,
                "self_check": errors,
                "component_border_sides": sides,
                "has_multi_side_component": any(len(item) >= 2 for item in sides),
            }
        )
assert len(generated) == 64
assert all(not row["self_check"] for row in scan)
assert not any(row["has_multi_side_component"] for row in scan)
(OUT / "generated-inputs.json").write_text(json.dumps(generated, indent=2) + "\n")
(OUT / "generated-rival-output.json").write_text(
    json.dumps([exactly_one_border_side_rival(grid) for grid in generated], indent=2) + "\n"
)
(OUT / "repro-metadata.json").write_text(
    json.dumps(
        {
            "schema": "arcpuzzles-audit-reproducer-v1",
            "task_id": TASK,
            "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "rule_hash": module.RULE_HASH,
            "canonical_pair_index": 0,
            "canonical_self_check": module.self_check(canonical["input"]),
            "canonical_component_border_sides": canonical_sides,
            "rival": "recolor only components touching exactly one border side",
            "generated_scan": {
                "draws": len(scan),
                "bands": [None, "easy", "medium", "hard"],
                "per_band": 16,
                "multi_side_component_hits": sum(row["has_multi_side_component"] for row in scan),
                "self_check_failures": sum(bool(row["self_check"]) for row in scan),
                "cases": scan,
            },
            "claim": (
                "The canonical/validator domain includes corner-touching blue components, "
                "but the sampler's side roles require exactly one touched side. The rival "
                "therefore disagrees on this accepted canonical input while remaining "
                "answer-equivalent on emitted scenes."
            ),
            "canonical_racket_command": {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply",
                    TASK, "--input", "../checks/audit/dcf954423fbb/input.json",
                    "--out", "../checks/audit/dcf954423fbb/racket.json",
                ],
            },
            "generated_racket_command": {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply",
                    TASK, "--input", "../checks/audit/dcf954423fbb/generated-inputs.json",
                    "--out", "../checks/audit/dcf954423fbb/generated-racket.json",
                ],
            },
        },
        indent=2,
        sort_keys=True,
    )
    + "\n"
)
