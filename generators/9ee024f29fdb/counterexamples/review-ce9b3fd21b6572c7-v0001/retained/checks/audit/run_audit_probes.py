#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repo"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "shared" / "runtime"))


def load(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical(task_id: str):
    for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def border_marker_rival(grid):
    """Wrong: noisy border markers define erased rows/cols; clean grids use period 4."""
    h, w = len(grid), len(grid[0])
    lattice_has_noise = any(
        grid[r][c] != 0
        for r in range(h)
        for c in range(w)
        if r % 4 == 0 or c % 4 == 0
    )
    if lattice_has_noise:
        erased_rows = {0} | {r for r in range(h) if grid[r][0] != 0}
        erased_cols = {0} | {c for c in range(w) if grid[0][c] != 0}
    else:
        erased_rows = {r for r in range(h) if r % 4 == 0}
        erased_cols = {c for c in range(w) if c % 4 == 0}
    return [
        [0 if r in erased_rows or c in erased_cols or v == 8 else 2
         for c, v in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def first_parity_only_rival(grid):
    """Wrong: grow halos only from centers matching the first center's parity."""
    points = [
        (r, c, v)
        for r, row in enumerate(grid)
        for c, v in enumerate(row)
        if v != 0
    ]
    parity = (points[0][0] + points[0][1]) % 2
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c, _v in points:
        if (r + c) % 2 != parity:
            continue
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 8
    return out


def audit_9ee():
    task_id = "9ee024f29fdb"
    g, path = load(task_id)
    generated = []
    matches = 0
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for i in range(50):
            sample_index = band_index * 50 + i
            grid = g.generate(900_000 + sample_index, sample_index, difficulty=band)
            truth = g._rule_mirror(grid)
            rival = border_marker_rival(grid)
            matches += rival == truth
            generated.append({"band": band, "sample_index": sample_index, "matches": rival == truth})

    row = canonical(task_id)
    canonical_pairs = row["train"] + row["test"]
    canonical_matches = sum(border_marker_rival(p["input"]) == p["output"] for p in canonical_pairs)

    grid = [[0 for _ in range(9)] for _ in range(9)]
    grid[1][1] = 8
    for r, c in ((0, 1), (4, 1), (8, 1), (1, 0), (1, 4), (1, 8)):
        grid[r][c] = 1
    truth = g._rule_mirror(grid)
    rival = border_marker_rival(grid)
    payload = {
        "schema": "audit-probe-v1",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rival": "If lattice noise exists, infer erased rows from nonzero cells in the first column and erased columns from nonzero cells in the first row; otherwise use the fixed period-4 lattice.",
        "generated_probe": {"draws": len(generated), "matches": matches, "mismatches": len(generated)-matches},
        "canonical_probe": {"pairs": len(canonical_pairs), "matches": canonical_matches},
        "counterexample": {
            "input": grid,
            "self_check": g.self_check(grid),
            "python_truth": truth,
            "rival_output": rival,
            "disagrees": truth != rival,
            "explanation": "All periodic rows/columns contain noise, but the noise is away from the top-row/left-column marker positions used by generated noisy samples."
        },
    }
    d = OUT / task_id
    (d / "pre_apply.json").write_text(json.dumps(payload, indent=2) + "\n")
    (d / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
    return payload


def audit_7a():
    task_id = "7a6e065e8273"
    g, path = load(task_id)
    matches = 0
    draws = 0
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for i in range(50):
            sample_index = band_index * 50 + i
            grid = g.generate(700_000 + sample_index, sample_index, difficulty=band)
            truth = g._fixed_cyan_halos(grid)
            rival = first_parity_only_rival(grid)
            matches += rival == truth
            draws += 1

    row = canonical(task_id)
    test_pairs = [row["test"]] if isinstance(row.get("test"), dict) else list(row.get("test", []))
    canonical_pairs = [p for p in list(row["train"]) + test_pairs if isinstance(p, dict)]
    canonical_matches = sum(first_parity_only_rival(p["input"]) == p["output"] for p in canonical_pairs)

    grid = [[0 for _ in range(6)] for _ in range(6)]
    grid[1][1] = 5  # even checkerboard parity, first in row-major order
    grid[3][2] = 5  # odd parity; lawful and non-adjacent, but never generated
    truth = g._fixed_cyan_halos(grid)
    rival = first_parity_only_rival(grid)
    payload = {
        "schema": "audit-probe-v1",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rival": "Paint halos only for centers on the checkerboard parity of the first row-major center.",
        "generated_probe": {"draws": draws, "matches": matches, "mismatches": draws-matches},
        "canonical_probe": {"pairs": len(canonical_pairs), "matches": canonical_matches},
        "counterexample": {
            "input": grid,
            "self_check": g.self_check(grid),
            "python_truth": truth,
            "rival_output": rival,
            "disagrees": truth != rival,
            "center_parities": [0, 1],
            "explanation": "The validator accepts mixed-parity non-adjacent interior centers, but the sampler always chooses all centers from one parity."
        },
    }
    d = OUT / task_id
    (d / "pre_apply.json").write_text(json.dumps(payload, indent=2) + "\n")
    (d / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
    return payload


if __name__ == "__main__":
    reports = [audit_9ee(), audit_7a()]
    print(json.dumps({r["task_id"]: {"generated_probe": r["generated_probe"], "canonical_probe": r["canonical_probe"], "counterexample": {"self_check": r["counterexample"]["self_check"], "disagrees": r["counterexample"]["disagrees"]}} for r in reports}, indent=2))
