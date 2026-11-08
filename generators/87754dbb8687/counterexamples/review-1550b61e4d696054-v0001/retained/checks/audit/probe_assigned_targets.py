#!/usr/bin/env python3
"""Reproduce the two immutable adversarial-audit assignments.

This tool deliberately uses only generator.py plus public packet data.  Racket
labels are obtained separately with the supported ``arcpuzzles apply`` command
and merged into the final evidence records by ``finalize_audits.py``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PACKET_ROOT = Path(__file__).resolve().parents[2]
REPO = PACKET_ROOT / "repo"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
OUT_ROOT = PACKET_ROOT / "checks/audit"

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "shared/runtime"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_rule_source(task_id: str) -> str:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id and row.get("program_solution"):
                return str(row["program_solution"])
    raise RuntimeError(f"{task_id}: no canonical program_solution")


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def equality_matrix(grid: list[list[int]]) -> list[list[int]]:
    top = grid[0][1:]
    left = [row[0] for row in grid[1:]]
    return [[left_value if left_value == top_value else 0 for top_value in top]
            for left_value in left]


def main() -> None:
    assignment = json.loads((PACKET_ROOT / "AUDIT_ASSIGNMENT.json").read_text())
    expected_hashes = {item["task_id"]: item["generator_sha256"] for item in assignment["targets"]}

    # Audit A1: an advertised/validator-accepted no_bar sample crashes the rule,
    # because the Racket program immediately takes first/second of an empty list.
    task_id = "849c171da23c"
    gen, source_path = load_generator(task_id)
    seed = 751221139501474214
    sample_index = 0
    difficulty = "easy"
    overrides = {"texture": "no_bar"}
    grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
    out_dir = OUT_ROOT / task_id
    source_hash = sha256_file(source_path)
    assert source_hash == expected_hashes[task_id], (source_hash, expected_hashes[task_id])
    validator = gen.self_check(grid, difficulty=difficulty, meta=None)
    assert validator == [], validator
    assert not any(cell == 5 for row in grid for cell in row)
    context = {
        "schema": "arcpuzzles-audit-reproducer-v1",
        "task_id": task_id,
        "finding_id": "A1",
        "classification": "reproduced authority crash on advertised domain member",
        "generator_sha256": source_hash,
        "canonical_rule_hash": normalized_rule_hash(canonical_rule_source(task_id)),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "documented_domain_basis": "texture=no_bar is listed in DEGENERATE_TEXTURES and AXES.texture.valid",
        "validator_result": validator,
        "input": grid,
        "predicted_failure": "canonical rule takes first/second of empty color-5 coordinate list",
        "apply_command": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
            task_id, "--input", f"../checks/audit/{task_id}/input.json",
            "--out", f"../checks/audit/{task_id}/racket.json",
        ],
        "apply_cwd": "packet_root",
    }
    write_json(out_dir / "input.json", grid)
    write_json(out_dir / "context.json", context)

    # Audit A2: n_shared=0 is advertised, but the override is ignored and the
    # generator forcibly creates at least one shared header color.
    task_id = "87754dbb8687"
    gen, source_path = load_generator(task_id)
    seed = 1
    sample_index = 0
    difficulty = None
    overrides = {"n_shared": 0}
    grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
    out_dir = OUT_ROOT / task_id
    source_hash = sha256_file(source_path)
    assert source_hash == expected_hashes[task_id], (source_hash, expected_hashes[task_id])
    validator = gen.self_check(grid, difficulty=difficulty, meta=None)
    assert validator == [], validator
    top = grid[0][1:]
    left = [row[0] for row in grid[1:]]
    shared = sorted(set(top) & set(left))
    assert shared, "the ignored override reproducer unexpectedly has no shared colors"
    actual_by_rule = equality_matrix(grid)
    requested_zero_shared_rival = [[0 for _ in top] for _ in left]
    context = {
        "schema": "arcpuzzles-audit-reproducer-v1",
        "task_id": task_id,
        "finding_id": "A2",
        "classification": "reproduced ignored exact override",
        "generator_sha256": source_hash,
        "canonical_rule_hash": normalized_rule_hash(canonical_rule_source(task_id)),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "documented_domain_basis": "AXES.n_shared.valid advertises 0..6",
        "validator_result": validator,
        "input": grid,
        "top_header": top,
        "left_header": left,
        "observed_shared_colors": shared,
        "expected_observation_for_exact_override": {"n_shared": 0, "shared_colors": []},
        "rival_output_if_override_were_honored": requested_zero_shared_rival,
        "independent_rule_output": actual_by_rule,
        "apply_command": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
            task_id, "--input", f"../checks/audit/{task_id}/input.json",
            "--out", f"../checks/audit/{task_id}/racket.json",
        ],
        "apply_cwd": "packet_root",
    }
    write_json(out_dir / "input.json", grid)
    write_json(out_dir / "rival-output.json", requested_zero_shared_rival)
    write_json(out_dir / "context.json", context)


if __name__ == "__main__":
    main()
