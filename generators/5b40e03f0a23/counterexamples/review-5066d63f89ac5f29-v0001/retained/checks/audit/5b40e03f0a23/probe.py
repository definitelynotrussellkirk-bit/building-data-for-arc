#!/usr/bin/env python3
"""Independent audit probe for 5b40e03f0a23; does not modify the target."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
GEN_PATH = REPO / "generators" / "5b40e03f0a23" / "generator.py"
RACKET_PATH = ROOT / "checks" / "audit" / "5b40e03f0a23" / "racket.json"
OUT_PATH = ROOT / "checks" / "audit" / "5b40e03f0a23" / "probe.json"

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs  # noqa: E402

spec = importlib.util.spec_from_file_location("audit_generator_5b40e03f0a23", GEN_PATH)
assert spec is not None and spec.loader is not None
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def one_pass(grid: list[list[int]]) -> list[list[int]]:
    """Fill each initially almost-complete green 2x2, simultaneously, once."""
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            values = [grid[rr][cc] for rr, cc in cells]
            if values.count(3) == 3 and values.count(0) == 1:
                rr, cc = cells[values.index(0)]
                out[rr][cc] = 3
    return out


def fixpoint(grid: list[list[int]]) -> list[list[int]]:
    current = copy.deepcopy(grid)
    for _ in range(len(grid) * len(grid[0]) + 1):
        nxt = one_pass(current)
        if nxt == current:
            return current
        current = nxt
    raise RuntimeError("closure did not converge")


def differing_cells(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    return [
        [r, c]
        for r, (row_a, row_b) in enumerate(zip(a, b))
        for c, (va, vb) in enumerate(zip(row_a, row_b))
        if va != vb
    ]


racket = json.loads(RACKET_PATH.read_text())
witness = racket["results"][0]["input"]
authority_output = racket["results"][0]["output"]
witness_one_pass = one_pass(witness)
witness_fixpoint = fixpoint(witness)

canonical = canonical_pairs("5b40e03f0a23", root=REPO)
canonical_rows = []
for pair in canonical:
    one = one_pass(pair["input"])
    fixed = fixpoint(pair["input"])
    canonical_rows.append(
        {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "one_pass_matches": one == pair["output"],
            "fixpoint_matches": fixed == pair["output"],
        }
    )

generated = {}
for band in ("easy", "medium", "hard"):
    rows = []
    for seed in range(20):
        for sample_index in range(10):
            grid = generator.generate(seed, sample_index, difficulty=band)
            rows.append(
                {
                    "self_check_clean": generator.self_check(grid) == [],
                    "one_pass_equals_fixpoint": one_pass(grid) == fixpoint(grid),
                }
            )
    generated[band] = {
        "samples": len(rows),
        "self_check_clean": sum(row["self_check_clean"] for row in rows),
        "one_pass_equals_fixpoint": sum(row["one_pass_equals_fixpoint"] for row in rows),
    }

report = {
    "schema": "5b40e03f0a23-audit-probe-v1",
    "task_id": "5b40e03f0a23",
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash": racket["executed_rule_hash"],
    "witness": {
        "input": witness,
        "validator_errors": generator.self_check(witness),
        "documented_separation_invariant_satisfied": False,
        "one_pass_output": witness_one_pass,
        "fixpoint_output": witness_fixpoint,
        "racket_output": authority_output,
        "fixpoint_matches_racket": witness_fixpoint == authority_output,
        "one_pass_matches_racket": witness_one_pass == authority_output,
        "differing_cells_one_pass_vs_racket": differing_cells(witness_one_pass, authority_output),
    },
    "canonical": {
        "pairs": len(canonical_rows),
        "one_pass_matches": sum(row["one_pass_matches"] for row in canonical_rows),
        "fixpoint_matches": sum(row["fixpoint_matches"] for row in canonical_rows),
        "rows": canonical_rows,
    },
    "generated": generated,
    "finding": (
        "The validator accepts a cascading witness outside the documented separated-window "
        "domain. A simultaneous one-pass shortcut matches every canonical pair and all 600 "
        "sampled generated inputs, but disagrees with the fixpoint Racket authority on the witness."
    ),
}
OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
