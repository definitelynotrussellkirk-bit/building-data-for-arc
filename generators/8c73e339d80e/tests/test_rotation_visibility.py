"""Bounded regression: generated pairs must visibly use a rotation code.

The canonical rule still permits symmetric motifs; generation must provide at
least one observable distinction from stamping the base unchanged everywhere.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

from arcpuzzles import Catalog

HOME = Path(__file__).resolve().parents[1]
TASK = "8c73e339d80e"
SPEC = importlib.util.spec_from_file_location("rotation_generator", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def ignore_codes(grid):
    base = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    r0 = min(r for r, _ in base)
    c0 = min(c for _, c in base)
    out = [[0] * len(grid[0]) for _ in grid]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 1:
                for br, bc in base:
                    rr, cc = r + br - r0, c + bc - c0
                    if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                        out[rr][cc] = 8
    return out


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def test_bounded_generated_pairs_refute_ignore_codes():
    witness_path = HOME / "counterexamples/review-5f1b2eb43a971d3a-v0001/retained/checks/audit/8c73e339d80e/input.json"
    historical = json.loads(witness_path.read_text())
    settings = [("medium", 0, i) for i in range(8)]
    settings += [(difficulty, 17, i) for difficulty in ("easy", "hard") for i in range(2)]
    grids = [GEN.generate(seed, index, difficulty=difficulty)
             for difficulty, seed, index in settings]
    result = Catalog(root=HOME.parents[1]).apply(TASK, [historical, *grids], timeout=120)
    outputs = [row["output"] for row in result["results"]]
    rows = []
    for (difficulty, seed, index), grid, output in zip(settings, grids, outputs[1:]):
        rows.append(dict(difficulty=difficulty, seed=seed, sample_index=index,
                         input_sha256=digest(grid), output_sha256=digest(output),
                         self_check=GEN.self_check(grid, difficulty=difficulty),
                         refutes_ignore_codes=(output != ignore_codes(grid))))
    report = dict(task_id=TASK, generator_sha256=hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
                  executed_rule_hash=result["executed_rule_hash"],
                  rule_hash_matches_catalog=result["rule_hash_matches_catalog"],
                  historical_witness=dict(input_sha256=digest(historical),
                      structurally_valid=(GEN.self_check(historical) == []),
                      invisible_rotation=(outputs[0] == ignore_codes(historical))),
                  generated_cases=rows,
                  successes=sum(row["refutes_ignore_codes"] and not row["self_check"] for row in rows),
                  total=len(rows),
                  limits="One pair-level rival only; no full-lesson teaching certificate or broader control audit.")
    if os.environ.get("ROTATION_PROBE_REPORT"):
        Path(os.environ["ROTATION_PROBE_REPORT"]).write_text(json.dumps(report, indent=2) + "\n")
    assert report["rule_hash_matches_catalog"]
    assert report["historical_witness"]["structurally_valid"]
    assert report["historical_witness"]["invisible_rotation"]
    assert all(not row["self_check"] for row in rows), rows
    assert report["successes"] == report["total"], rows
