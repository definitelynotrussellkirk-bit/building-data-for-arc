#!/usr/bin/env python3
"""Audit ea45d5e1d11c for canonical-validator and distribution mismatch."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs

TASK_ID = "ea45d5e1d11c"
PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
HERE = PACKET / "checks" / "audit" / TASK_ID
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def object_sides(module, grid: list[list[int]]) -> list[int]:
    bg = module._mode_color(grid)
    sides = []
    for _color, cells in module._components_except_bg(grid, bg):
        r1, c1, r2, c2 = module._bbox(cells)
        sides.append(r2 - r1 + 1)
    return sorted(sides)


def grid_like(value: Any) -> bool:
    return (
        isinstance(value, list) and value and all(isinstance(row, list) and row for row in value)
        and all(all(type(cell) is int for cell in row) for row in value)
    )


def load_racket_output(path: Path) -> tuple[list[list[int]], dict[str, Any]]:
    receipt = json.loads(path.read_text())
    candidates = [receipt.get(k) for k in ("output", "outputs", "results", "cases") if k in receipt]
    for candidate in candidates:
        if grid_like(candidate):
            return candidate, receipt
        if isinstance(candidate, list) and len(candidate) == 1:
            one = candidate[0]
            if grid_like(one):
                return one, receipt
            if isinstance(one, dict):
                for key in ("output", "grid", "result"):
                    if grid_like(one.get(key)):
                        return one[key], receipt
        if isinstance(candidate, dict):
            for key in ("output", "grid", "result"):
                if grid_like(candidate.get(key)):
                    return candidate[key], receipt
    raise ValueError(f"could not locate single output grid in {path}")


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    module = load_generator()
    pairs = canonical_pairs(TASK_ID, root=REPO)
    selected = next(pair for pair in pairs if 9 in object_sides(module, pair["input"]))
    input_grid = selected["input"]
    expected = selected["output"]
    sides = object_sides(module, input_grid)
    validator_errors = module.self_check(input_grid, difficulty=None)
    assert 9 in sides
    assert any("1/3/5/7" in err for err in validator_errors), validator_errors

    sampled_counts: Counter[int] = Counter()
    sampled = 0
    failures: list[dict[str, Any]] = []
    for difficulty in ("easy", None, "hard"):
        for index in range(100):
            try:
                grid = module.generate(99173, index, difficulty=difficulty)
            except Exception as exc:
                failures.append({
                    "difficulty": difficulty,
                    "sample_index": index,
                    "error": f"{type(exc).__name__}: {exc}",
                })
                continue
            sampled += 1
            sampled_counts.update(object_sides(module, grid))
    assert sampled == 300, failures[:3]
    assert sampled_counts[9] == 0

    (HERE / "input.json").write_text(json.dumps(input_grid, indent=2) + "\n")
    evidence: dict[str, Any] = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "finding": "self_check rejects an official canonical 9x9 square and generation omits that demonstrated branch",
        "generator_path": str(GEN_PATH.relative_to(REPO)),
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "canonical_case": {
            "variant": selected["variant"],
            "split": selected["split"],
            "pair_index": selected["pair_index"],
            "input_object_sides": sides,
            "validator_difficulty": None,
            "validator_errors": validator_errors,
            "input": input_grid,
            "expected_output": expected,
        },
        "generator_census": {
            "seed": 99173,
            "sample_indices": [0, 99],
            "difficulties": ["easy", None, "hard"],
            "generated_inputs": sampled,
            "generation_failures": failures,
            "object_side_histogram": {str(k): v for k, v in sorted(sampled_counts.items())},
            "size_9_count": sampled_counts[9],
            "structural_reason": "generate() chooses size_pool [1,3,5] or [1,3,5,7], never 9",
        },
        "belongs_to_documented_task_domain": True,
        "default_generator_emits_size_9": False,
        "public_apply": {
            "cwd": "packet_root",
            "argv": [
                "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                TASK_ID, "--input", f"../checks/audit/{TASK_ID}/input.json",
                "--out", f"../checks/audit/{TASK_ID}/racket.json",
            ],
            "receipt": f"checks/audit/{TASK_ID}/racket.json",
        },
    }

    receipt_path = HERE / "racket.json"
    if receipt_path.exists():
        actual, receipt = load_racket_output(receipt_path)
        evidence["actual_racket_output"] = actual
        evidence["racket_matches_canonical_expected"] = actual == expected
        evidence["racket_receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        for key in ("executed_rule_hash", "catalog_rule_hash", "rule_text_sha256", "generator_sha256", "source_sha256", "input_sha256", "output_sha256"):
            if key in receipt:
                evidence.setdefault("receipt_fields", {})[key] = receipt[key]
        assert actual == expected
    else:
        evidence["status"] = "prepared; run public apply command, then rerun probe"

    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_identity": [selected["variant"], selected["split"], selected["pair_index"]],
        "canonical_object_sides": sides,
        "validator_errors": validator_errors,
        "sampled_generated_inputs": sampled,
        "generated_side_histogram": dict(sorted(sampled_counts.items())),
        "racket_receipt_present": receipt_path.exists(),
        "racket_matches_canonical_expected": evidence.get("racket_matches_canonical_expected"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
