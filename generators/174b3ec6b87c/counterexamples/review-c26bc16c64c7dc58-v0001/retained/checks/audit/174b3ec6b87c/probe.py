"""Bounded findings-only audit; public generator and canonical-data helpers."""
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path

TASK = "174b3ec6b87c"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks/audit" / TASK
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def count_windows(grid):
    return sum(1 for r in range(len(grid) - 1) for c in range(len(grid[0]) - 1)
               if [[grid[r][c], grid[r][c+1]], [grid[r+1][c], grid[r+1][c+1]]]
               in ([[3, 0], [0, 3]], [[0, 3], [3, 0]]))


def loose_corner_rival(grid):
    """Paint a zero with perpendicular adjacent green cells; omit opposite-zero guard."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            for dr in (-1, 1):
                for dc in (-1, 1):
                    if (0 <= r+dr < h and 0 <= c+dc < w
                            and grid[r+dr][c] == 3 and grid[r][c+dc] == 3):
                        out[r][c] = 7
    return out


pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
              "rival_matches": loose_corner_rival(p["input"]) == p["output"],
              "input_sha256": digest(json.dumps(p["input"], separators=(",", ":")).encode())}
             for p in pairs]
override_rows = []
inputs = []
for index in range(20):
    controls = {"grid_h": 7, "grid_w": 7, "n_pairs": 5}
    grid = generator.generate(123, index, difficulty=None, **controls)
    override_rows.append({"seed": 123, "sample_index": index, "difficulty": None,
                          "overrides": controls, "requested_pairs": 5,
                          "actual_pairs": count_windows(grid), "nonbackground_cells": sum(v == 3 for row in grid for v in row),
                          "self_check": generator.self_check(grid, difficulty="easy", meta=controls)})
    if index == 0:
        inputs.append(grid)
default_rows = []
default_inputs = []
for band in ("easy", "medium", "hard"):
    for index in range(20):
        grid = generator.generate(123, index, difficulty=band)
        default_inputs.append(grid)
        default_rows.append({"seed": 123, "sample_index": index, "difficulty": band,
                             "public_apply_index": 3 + len(default_rows),
                             "actual_pairs": count_windows(grid),
                             "self_check": generator.self_check(grid, difficulty=band),
                             "loose_rival_prediction": loose_corner_rival(grid)})
blocked_corner = [[3, 3], [0, 3]]
inputs.append(blocked_corner)
no_pair = [[3, 0], [0, 0]]
inputs.append(no_pair)
inputs.extend(default_inputs)
axis_rejections = []
for controls in ({"grid_h": 4}, {"grid_h": 18}, {"grid_w": 4}, {"grid_w": 18},
                 {"n_pairs": 1}, {"n_pairs": 10}):
    try:
        generator.generate(123, 0, **controls)
        error = None
    except ValueError as exc:
        error = str(exc)
    axis_rejections.append({"seed": 123, "sample_index": 0, "difficulty": None,
                            "overrides": controls, "error": error})
row = next(json.loads(line) for line in canonical_path(ROOT).open()
           if json.loads(line).get("task_id") == TASK)
summary = {"task_id": TASK, "generator_sha256": digest(SOURCE.read_bytes()),
           "canonical_ledger_sha256": digest(canonical_path(ROOT).read_bytes()),
           "canonical_program_sha256": digest(row["program_solution"].encode()),
           "canonical_usable_labelled_pairs": canonical,
           "override_probe": override_rows, "default_probe": default_rows,
           "advertised_axis_endpoint_probes": axis_rejections,
           "input_cases": [
               {"index": 0, "kind": "generated_override_underfill", "seed": 123, "sample_index": 0,
                "difficulty": None, "overrides": {"grid_h": 7, "grid_w": 7, "n_pairs": 5}},
               {"index": 1, "kind": "validator_accepted_opposite_corner_blocked", "generated": False,
                "self_check": generator.self_check(blocked_corner), "rival_output": loose_corner_rival(blocked_corner)},
               {"index": 2, "kind": "validator_accepted_no_diagonal_pair", "generated": False,
                "self_check": generator.self_check(no_pair)}]}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
(OUT / "probe.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({"canonical_pairs": len(pairs), "rival_fits": sum(x["rival_matches"] for x in canonical),
                  "override_underfills": sum(x["actual_pairs"] != 5 for x in override_rows),
                  "override_denominator": len(override_rows),
                  "default_count": len(default_rows),
                  "default_self_check_failures": sum(bool(x["self_check"]) for x in default_rows)}))
