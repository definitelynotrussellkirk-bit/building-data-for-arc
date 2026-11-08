"""Read-only target audit; writes evidence only beside this file."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "f7ebaf709467"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def wall_blind_parity(grid):
    """Deliberately wrong rival: ignore connectivity while preserving all occupied cells."""
    result = [row[:] for row in grid]
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
    for sr, sc, color in seeds:
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0 and (abs(r - sr) + abs(c - sc)) % 2 == 0:
                    result[r][c] = color
    return result


def changes(actual, other):
    return [{"row": r, "col": c, "actual": value, "other": other[r][c]}
            for r, row in enumerate(actual) for c, value in enumerate(row) if value != other[r][c]]


def observe(grid):
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_seeds": len(seeds),
            "seed_colors": sorted({v for r, c, v in seeds}),
            "wall_cells": sum(row.count(5) for row in grid)}


def main():
    source = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_halo_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    pairs = canonical_pairs(TASK, root=REPO)
    records = []
    for i, pair in enumerate(pairs):
        rival = wall_blind_parity(pair["input"])
        records.append({"index": i, "split": pair["split"], "pair_index": pair["pair_index"],
                        "observed": observe(pair["input"]), "self_check": gen.self_check(pair["input"]),
                        "wall_blind_rival_fits_canonical": rival == pair["output"],
                        "wall_blind_rival_differences": len(changes(pair["output"], rival))})
    controls = {"grid_h": 20, "grid_w": 24, "n_seeds": 6}
    grid = gen.generate(0, 0, difficulty="easy", **controls)
    normal = gen.generate(0, 0, difficulty="easy")
    unknown = gen.generate(0, 0, difficulty="easy", unknown_axis="sentinel")
    write("input.json", grid)
    write("inputs.json", {"inputs": [grid, *[pair["input"] for pair in pairs]]})
    write("canonical-pairs.json", pairs)
    write("canonical-input.json", pairs[0]["input"])
    write("canonical-stored-output.json", pairs[0]["output"])
    write("rival-output.json", wall_blind_parity(grid))
    write("canonical-rival-output.json", wall_blind_parity(pairs[0]["input"]))
    selected = None
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            selected = row
            break
    program = selected["program_solution"]
    (HERE / "canonical-program.rkt").write_text(program)
    report = {
        "schema": "task-source-bound-audit-v1", "task_id": TASK,
        "generator_sha256": sha(source.read_bytes()),
        "canonical_program_sha256": sha(program.encode()),
        "canonical_rule_hash": sha(" ".join(program.split()).encode())[:12],
        "canonical_ledger_sha256": sha((REPO / "shared/data/canonical/puzzles.jsonl").read_bytes()),
        "canonical_cases": records,
        "override_case": {"seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": controls,
                          "declared_valid": {k:gen.AXES[k] for k in controls},
                          "observed": observe(grid), "self_check": gen.self_check(grid),
                          "identical_to_no_overrides": grid == normal,
                          "unknown_axis_accepted_and_identical": unknown == normal},
        "finding_status": "reproduced_python_findings_pending_public_racket_execution",
        "rival_note": "Supplementary comparator only: canonical fit is measured, not assumed.",
    }
    write("probe-results.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
