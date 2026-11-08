#!/usr/bin/env python3
"""Source-bound shortcut audit for generator 95315dd52287.

This script does not import or modify the audited generator.  It compares a
fixed-orientation rival against authoritative Racket outputs already captured by
``arcpuzzles apply`` and against the three canonical labelled pairs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RACKET_PATH = HERE / "racket.json"
CANONICAL_PATH = HERE / "canonical_pairs.json"
COUNTEREXAMPLE_RACKET_PATH = HERE / "counterexample_racket.json"
OUT_PATH = HERE / "observation.json"
FIXED_SHAPE = ((0, 0), (0, 1), (1, 1))


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fixed_orientation_rival(grid: list[list[int]]) -> list[list[int]]:
    """Move row-major blob values into one memorized L orientation at the anchor.

    Unlike the canonical crop-and-translate rule, this intentionally ignores the
    input blob's geometry.  It therefore fits this generator's one-shape support
    but not canonical examples with another L orientation.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    blob = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 8)]
    if len(anchors) != 1 or len(blob) != 3:
        raise ValueError(f"rival expects one anchor and three blob cells; got {len(anchors)=}, {len(blob)=}")
    anchor_r, anchor_c = anchors[0]
    values = [value for _, _, value in sorted(blob)]
    out = [[0 for _ in range(width)] for _ in range(height)]
    for (dr, dc), value in zip(FIXED_SHAPE, values, strict=True):
        rr, cc = anchor_r + dr, anchor_c + dc
        if not (0 <= rr < height and 0 <= cc < width):
            raise ValueError("fixed-orientation rival would place outside the grid")
        out[rr][cc] = value
    return out


def first_difference(a: list[list[int]], b: list[list[int]]) -> dict[str, Any] | None:
    for r, (row_a, row_b) in enumerate(zip(a, b, strict=True)):
        for c, (value_a, value_b) in enumerate(zip(row_a, row_b, strict=True)):
            if value_a != value_b:
                return {"row": r, "col": c, "rival": value_a, "reference": value_b}
    return None


def main() -> None:
    racket = json.loads(RACKET_PATH.read_text())
    canonical = json.loads(CANONICAL_PATH.read_text())
    counterexample_racket = json.loads(COUNTEREXAMPLE_RACKET_PATH.read_text())

    generated_cases: list[dict[str, Any]] = []
    generated_matches = 0
    for result in racket["results"]:
        rival = fixed_orientation_rival(result["input"])
        matches = rival == result["output"]
        generated_matches += int(matches)
        generated_cases.append(
            {
                "index": result["index"],
                "input_sha256": result["input_sha256"],
                "authoritative_output_sha256": result["output_sha256"],
                "rival_output_sha256": stable_sha256(rival),
                "valid_output": result["valid_output"],
                "matches_authoritative_output": matches,
            }
        )

    canonical_cases: list[dict[str, Any]] = []
    canonical_matches = 0
    for case in canonical:
        rival = fixed_orientation_rival(case["input"])
        matches = rival == case["output"]
        canonical_matches += int(matches)
        canonical_cases.append(
            {
                "split": case["split"],
                "index": case["index"],
                "input_sha256": stable_sha256(case["input"]),
                "reference_output_sha256": stable_sha256(case["output"]),
                "rival_output_sha256": stable_sha256(rival),
                "matches_reference_output": matches,
                "first_difference": first_difference(rival, case["output"]),
                "self_check": case["self_check"],
                "input": case["input"] if not matches else None,
                "reference_output": case["output"] if not matches else None,
                "rival_output": rival if not matches else None,
            }
        )

    failing_canonical = [case for case in canonical_cases if not case["matches_reference_output"]]
    witness = failing_canonical[0] if failing_canonical else None
    observation = {
        "schema": "review-audit-shortcut-observation-v1",
        "task_id": racket["task_id"],
        "generator_sha256": racket["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "catalog_rule_hash": racket["catalog_rule_hash"],
        "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "rival": {
            "name": "fixed_orientation_row_major_L",
            "description": (
                "Ignore the source blob geometry; read its three values in row-major order and paste "
                "them at the anchor on fixed offsets (0,0),(0,1),(1,1)."
            ),
            "fixed_shape": [list(cell) for cell in FIXED_SHAPE],
        },
        "generated_probe": {
            "sample_count": len(generated_cases),
            "difficulty_counts": {"easy": 20, "medium": 20, "hard": 20},
            "authoritative_outputs_valid": sum(bool(case["valid_output"]) for case in generated_cases),
            "rival_matches": generated_matches,
            "rival_match_fraction": generated_matches / len(generated_cases),
            "cases": generated_cases,
        },
        "canonical_probe": {
            "pair_count": len(canonical_cases),
            "rival_matches": canonical_matches,
            "rival_match_fraction": canonical_matches / len(canonical_cases),
            "cases": canonical_cases,
        },
        "counterexample": {
            **(witness or {}),
            "authoritative_racket_output": counterexample_racket["results"][0]["output"],
            "authoritative_racket_output_sha256": counterexample_racket["results"][0]["output_sha256"],
            "authoritative_racket_valid_output": counterexample_racket["results"][0]["valid_output"],
            "authoritative_racket_evidence": "checks/audit/95315dd52287/counterexample_racket.json",
            "authoritative_racket_command": counterexample_racket["command"],
            "authoritative_racket_cwd": counterexample_racket["cwd"],
        },
        "finding": (
            "The generated distribution supports a fixed-orientation shortcut: the rival matches all "
            f"{generated_matches}/{len(generated_cases)} authoritative generated labels but only "
            f"{canonical_matches}/{len(canonical_cases)} canonical labels."
        ),
        "source_left_unchanged": True,
        "racket_evidence": "checks/audit/95315dd52287/racket.json",
        "command": ["python3", "checks/audit/95315dd52287/analyze_rival.py"],
        "cwd": ".",
    }
    OUT_PATH.write_text(json.dumps(observation, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "generated_matches": f"{generated_matches}/{len(generated_cases)}",
        "canonical_matches": f"{canonical_matches}/{len(canonical_cases)}",
        "counterexample": None if witness is None else f"{witness['split']}[{witness['index']}]",
        "output": str(OUT_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()
