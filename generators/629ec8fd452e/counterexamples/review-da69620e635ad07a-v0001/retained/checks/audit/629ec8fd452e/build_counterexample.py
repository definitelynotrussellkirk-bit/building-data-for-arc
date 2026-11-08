from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs

TASK = "629ec8fd452e"
path = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_holes_generator", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def rival(grid):
    analysis = module._analysis(grid)
    out = [[0 for _ in row] for row in grid]
    for component in analysis["components"]:
        if component["bbox_interior_missing"] and len(component["cells"]) >= 8:
            for row, col in component["cells"]:
                out[row][col] = component["color"]
    return out


def blank(h, w):
    return [[0] * w for _ in range(h)]


def add(grid, cells, color, top, left):
    for row, col in cells:
        assert grid[top + row][left + col] == 0
        grid[top + row][left + col] = color


grid = blank(10, 14)
add(grid, module._rect_frame(3, 3), 2, 1, 1)
add(grid, module._filled_rect(3, 3), 4, 1, 6)
open_large = tuple(cell for cell in module._rect_frame(4, 4) if cell != (3, 1))
add(grid, open_large, 6, 5, 1)

assert module.self_check(grid) == [], module.self_check(grid)
assert module.strict_canonical_like(grid) == [], module.strict_canonical_like(grid)
true_output = module.rule_true(grid)
rival_output = rival(grid)
assert true_output != rival_output

canon = canonical_pairs(TASK, root=REPO, labeled_only=True)
canonical_matches = sum(rival(pair["input"]) == pair["output"] for pair in canon)

bands = ("easy", "medium", "hard")
generated_total = 0
generated_matches = 0
generation_errors = []
for band in bands:
    for seed in range(30):
        for sample_index in range(8):
            try:
                candidate = module.generate(seed, sample_index, difficulty=band)
            except Exception as exc:
                generation_errors.append({"band": band, "seed": seed, "sample_index": sample_index,
                                          "error": f"{type(exc).__name__}: {exc}"})
                continue
            generated_total += 1
            generated_matches += rival(candidate) == module.rule_true(candidate)

out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps(grid, separators=(",", ":")) + "\n")
(out_dir / "rival.json").write_text(json.dumps(rival_output, separators=(",", ":")) + "\n")
record = {
    "task_id": TASK,
    "finding": "size_threshold_false_hole_shortcut",
    "generator_path": str(path.relative_to(ROOT)),
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "generator_version": module.VERSION,
    "counterexample": {
        "validator_errors": module.self_check(grid),
        "strict_errors": module.strict_canonical_like(grid),
        "input": grid,
        "python_true_output": true_output,
        "rival_output": rival_output,
        "rival_definition": "keep components with a missing strict-bbox interior cell and at least 8 occupied cells",
        "disagreement_cells": [
            [r, c, true_output[r][c], rival_output[r][c]]
            for r in range(len(grid)) for c in range(len(grid[0]))
            if true_output[r][c] != rival_output[r][c]
        ],
    },
    "canonical_check": {"matched": canonical_matches, "total": len(canon)},
    "generated_check": {
        "bands": list(bands),
        "seed_range": [0, 29],
        "sample_index_range": [0, 7],
        "matched": generated_matches,
        "total": generated_total,
        "generation_errors": generation_errors,
    },
    "generator_emits_counterexample_shape": False,
    "reason_not_emitted": "the sampler's only open object is a 3x3 almost-ring with 7 cells",
}
(out_dir / "analysis.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "canonical_matches": [canonical_matches, len(canon)],
    "generated_matches": [generated_matches, generated_total],
    "generation_errors": len(generation_errors),
    "validator_errors": record["counterexample"]["validator_errors"],
    "strict_errors": record["counterexample"]["strict_errors"],
    "disagreement_cells": len(record["counterexample"]["disagreement_cells"]),
    "generator_sha256": record["generator_sha256"],
}, sort_keys=True))
