#!/usr/bin/env python3
"""Reproduce a validator-accepted plus-with-tail shortcut for eb46daa8881c."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
TASK = "eb46daa8881c"
GENERATOR = REPO / "generators" / TASK / "generator.py"
EXPECTED_SHA256 = "fb16f7f5f7e35c5b1aa7da30a12d192794c7075f8ac3416df5b570ed193e1671"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local_rule(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            if value not in (0, 8) and all(grid[r + dr][c + dc] == value for dr, dc in CARDINAL):
                out[r][c] = 8
    return out


def clean_diagonal_plus_rival(grid):
    """Shortcut: require the four diagonal neighbors of a plus center to be 0."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    diagonals = ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            is_plus = value not in (0, 8) and all(
                grid[r + dr][c + dc] == value for dr, dc in CARDINAL
            )
            clean_diagonals = all(grid[r + dr][c + dc] == 0 for dr, dc in diagonals)
            if is_plus and clean_diagonals:
                out[r][c] = 8
    return out

def canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row.get("train", []) + row.get("test", [])
    raise AssertionError("canonical task missing")


def main() -> int:
    module = load_module()
    source_sha = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    assert source_sha == EXPECTED_SHA256, (source_sha, EXPECTED_SHA256)

    canonical = canonical_pairs()
    canonical_fit = [clean_diagonal_plus_rival(pair["input"]) == pair["output"] for pair in canonical]
    assert canonical_fit and all(canonical_fit)

    generated_checked = 0
    generated_disagreements = []
    for band in ("easy", "medium", "hard"):
        for seed in range(200):
            grid = module.generate(seed, 0, difficulty=band)
            generated_checked += 1
            if clean_diagonal_plus_rival(grid) != local_rule(grid):
                generated_disagreements.append({"band": band, "seed": seed})
    assert not generated_disagreements, generated_disagreements[:5]

    input_payload = json.loads((HERE / "input.json").read_text())
    counterexample = input_payload["input"]
    validator_errors = module.self_check(counterexample, difficulty="easy", meta={})
    assert validator_errors == [], validator_errors

    racket = json.loads((HERE / "racket.json").read_text())
    if isinstance(racket, dict) and racket.get("results"):
        racket_output = racket["results"][0]["output"]
    elif isinstance(racket, dict) and "output" in racket:
        racket_output = racket["output"]
    elif isinstance(racket, dict) and "outputs" in racket:
        racket_output = racket["outputs"][0]
    else:
        racket_output = racket
    expected = local_rule(counterexample)
    rival = clean_diagonal_plus_rival(counterexample)
    assert racket_output == expected, (racket_output, expected)
    assert rival != racket_output

    controls = (
        [("palette_kind", v) for v in ("default", "warm", "cool", "varied")]
        + [("texture", v) for v in ("default", "warm", "cool", "varied")]
        + [("palette_size", v) for v in (1, 8)]
        + [("n_distinct_colors", v) for v in (1, 8)]
    )
    variant_hashes = []
    for key, value in controls:
        grid = module.generate(12345, 7, difficulty="medium", **{key: value})
        digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
        variant_hashes.append({"key": key, "value": value, "grid_sha256": digest})
    assert len({row["grid_sha256"] for row in variant_hashes}) == 1

    report = {
        "schema": "audit-reproducer-v1",
        "task_id": TASK,
        "generator_sha256": source_sha,
        "status": "reproduced",
        "finding": "clean-diagonal shortcut fits all canonical/default data but fails a validator-accepted local plus with a diagonal distractor",
        "rival": "recolor a plus center only when all four diagonal neighbors are background",
        "canonical_pairs_fit": sum(canonical_fit),
        "canonical_pairs_total": len(canonical_fit),
        "generated_samples_checked": generated_checked,
        "generated_sample_recipe": "difficulty in easy,medium,hard; seed 0..199; sample_index 0",
        "generated_rival_disagreements": generated_disagreements,
        "counterexample": {
            "input_path": "checks/audit/eb46daa8881c/input.json",
            "validator_difficulty": "easy",
            "validator_errors": validator_errors,
            "racket_output_path": "checks/audit/eb46daa8881c/racket.json",
            "racket_output": racket_output,
            "rival_output": rival,
        },
        "inert_control_variants": variant_hashes,
        "unique_inert_control_outputs": len({row["grid_sha256"] for row in variant_hashes}),
        "domain_note": (
            "The counterexample satisfies the canonical written local-neighborhood rule and passes self_check, "
            "but its diagonal distractor is outside the generator's documented pure-separated-plus default distribution. "
            "It is therefore a validator-accepted/domain-coverage shortcut, not a claim that defaults already emit it."
        ),
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
