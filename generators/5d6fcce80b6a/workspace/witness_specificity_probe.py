#!/usr/bin/env python3
"""Counterfactual probe for semantic witness/rival declarations.

A useful witness/rival pair needs both sides of a causal contrast:

* a matched control where the named witness is absent and the rival agrees with
  the authority; and
* a positive example where the witness is present and the rival disagrees.

The ordinary semantic gate checks only the second condition.  This probe keeps
fixed examples for the two declarations that previously passed for confounded
reasons in task 5d6fcce80b6a.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "5d6fcce80b6a"
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
GENERATOR_PATH = REPO_ROOT / f"generators/{TASK_ID}/generator.py"
sys.path.insert(0, str(REPO_ROOT / "shared/runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_witness_probe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _observation(generator, witness_name: str, rival_name: str, grid: list[list[int]]) -> dict[str, Any]:
    authority = generator.rule_mirror(grid)
    rival_output = generator.SEMANTIC_RIVALS[rival_name](grid)
    return {
        "shape": [len(grid), len(grid[0])],
        "input_sha256_16": _grid_digest(grid),
        "witness_fires": bool(generator.SEMANTIC_WITNESSES[witness_name](grid)),
        "rival_matches_authority": rival_output == authority,
    }


def _case(
    generator,
    *,
    claim: str,
    rival: str,
    control: list[list[int]],
    positive: list[list[int]],
) -> dict[str, Any]:
    control_result = _observation(generator, claim, rival, control)
    positive_result = _observation(generator, claim, rival, positive)
    declaration_matches = generator.WITNESS_RIVALS.get(claim) == [rival]
    passed = bool(
        declaration_matches
        and not control_result["witness_fires"]
        and control_result["rival_matches_authority"]
        and positive_result["witness_fires"]
        and not positive_result["rival_matches_authority"]
    )
    return {
        "claim": claim,
        "rival": rival,
        "declaration_matches": declaration_matches,
        "control": control_result,
        "positive": positive_result,
        "passed": passed,
    }


def run_probe() -> dict[str, Any]:
    generator = _load_generator()

    singleton_control = [
        [0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0],
        [0, 4, 0, 0, 0],
        [0, 0, 4, 0, 0],
    ]
    multi_cell_positive = generator.generate(
        91,
        0,
        difficulty="medium",
        scene_profile="internal_anchor",
        palette_profile="single_4",
    )
    square_control = generator.generate(
        17,
        0,
        difficulty="medium",
        scene_profile="internal_anchor",
        palette_profile="single_8",
    )
    rectangular_positive = generator.generate(
        17,
        1,
        difficulty="medium",
        scene_profile="leading_control",
        palette_profile="pair_12",
    )

    cases = [
        _case(
            generator,
            claim="non_singleton_content_is_preserved",
            rival="copy_only_leftmost_nonzero_per_row",
            control=singleton_control,
            positive=multi_cell_positive,
        ),
        _case(
            generator,
            claim="rectangular_canvas_is_doubled",
            rival="assume_square_output_width_from_height",
            control=square_control,
            positive=rectangular_positive,
        ),
    ]
    return {
        "schema": "arc-witness-specificity-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "method": "matched negative control plus positive witness",
        "cases": cases,
        "passed": all(case["passed"] for case in cases),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="optional JSON output path")
    args = parser.parse_args(argv)
    report = run_probe()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
