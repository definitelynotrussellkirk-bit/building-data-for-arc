from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "5ca74a85bc85"
WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
HERE = Path(__file__).resolve().parent
SOURCE = REPO / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audited_5ca74a85bc85", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to import audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def filled_bbox_rival(grid):
    height, width = len(grid), len(grid[0])
    divider = next(c for c in range(width) if all(grid[r][c] == 9 for r in range(height)))
    source = [(r, c, grid[r][c]) for r in range(height) for c in range(width)
              if grid[r][c] not in (0, 9)]
    colors = {value for _, _, value in source}
    if len(colors) != 1:
        raise ValueError("this rival is defined only for monochrome source lessons")
    color = next(iter(colors))
    rows = [r for r, _, _ in source]
    cols = [c for _, c, _ in source]
    out = [row[:] for row in grid]
    for r in range(min(rows), max(rows) + 1):
        for c in range(min(cols), max(cols) + 1):
            destination = 2 * divider - c
            out[r][destination] = color
    return out


def main():
    gen = load_generator()
    inputs = json.loads((HERE / "input.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    racket_outputs = [item["output"] for item in racket["results"]]
    rivals = [filled_bbox_rival(grid) for grid in inputs]
    fits = [rival == official for rival, official in zip(rivals, racket_outputs)]
    observed = [gen.observe_overrides(grid) for grid in inputs]
    validators = [gen.self_check(grid) for grid in inputs]
    report = {
        "schema": "arc-audit-rival-reproduction-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "rule_hash": racket["executed_rule_hash"],
        "production_lesson": {
            "seed": 0,
            "sample_indices": [3, 4, 5, 6],
            "demo_count": 3,
            "query_index": 3,
            "profiles": [row["scene_profile"] for row in observed],
        },
        "validator_results": validators,
        "rival": "mirror one filled monochrome source bounding rectangle rather than each source cell",
        "rival_outputs": rivals,
        "racket_outputs": racket_outputs,
        "fits_each_pair": fits,
        "rival_fits_all_demos": all(fits[:3]),
        "rival_changes_query": not fits[3],
        "limitations": "One exact production lesson; this proves an ambiguity but does not estimate its frequency.",
    }
    (HERE / "bbox_rival_reproduction.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in (
        "generator_sha256", "rule_hash", "fits_each_pair",
        "rival_fits_all_demos", "rival_changes_query")}, indent=2))
    if validators != [[], [], [], []] or fits != [True, True, True, False]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
