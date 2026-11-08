#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "c5a96370d612"
ROOT = Path.cwd()
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def exact_runs(grid):
    runs = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            color = row[c]
            start = c
            while c < len(row) and row[c] == color:
                c += 1
            runs.append({
                "row": r,
                "start": start,
                "end": c - 1,
                "length": c - start,
                "color": color,
                "right_cell": row[c] if c < len(row) else None,
            })
    return runs


def main() -> int:
    cases = {}
    for texture in ("length_3_run", "dominoes_touching"):
        grid = GEN.generate(20261019, 0, texture=texture)
        runs = exact_runs(grid)
        cases[texture] = {
            "input": grid,
            "self_check": GEN.self_check(grid),
            "runs": runs,
            "violates_exact_length_2": any(run["length"] != 2 for run in runs),
            "violates_right_zero": any(run["right_cell"] not in (0, None) for run in runs),
        }
    # The negative-texture comments and invariants say both cases are malformed,
    # but the current self_check accepts them.
    assert cases["length_3_run"]["self_check"] == []
    assert cases["length_3_run"]["violates_exact_length_2"]
    assert cases["dominoes_touching"]["self_check"] == []
    assert cases["dominoes_touching"]["violates_right_zero"]

    override_pairs = {}
    for axis, a, b in (
        ("palette_kind", "warm", "cool"),
        ("palette_size", 1, 9),
        ("n_distinct_colors", 1, 9),
    ):
        ga = GEN.generate(123456, 7, **{axis: a})
        gb = GEN.generate(123456, 7, **{axis: b})
        override_pairs[axis] = {
            "a": a,
            "b": b,
            "identical_outputs": ga == gb,
            "output": ga if ga == gb else None,
        }
    result = {
        "schema": "audit-c5a96370d612-v1",
        "task_id": TASK_ID,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": SOURCE_SHA256,
        "finding": (
            "self_check accepts the generator's own malformed length-3 and "
            "touching-domino negative textures; several advertised override "
            "axes are also observationally inert for a fixed seed/sample"
        ),
        "cases": cases,
        "override_pairs": override_pairs,
    }
    out = Path("../checks/audit/c5a96370d612/probe-result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "reproduced",
        "out": str(out),
        "source_sha256": SOURCE_SHA256,
        "accepted_bad_textures": [
            name for name, case in cases.items() if case["self_check"] == []
        ],
        "inert_override_axes": [
            name for name, case in override_pairs.items() if case["identical_outputs"]
        ],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
