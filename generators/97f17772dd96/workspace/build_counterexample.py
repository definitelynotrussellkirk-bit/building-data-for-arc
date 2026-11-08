#!/usr/bin/env python3
"""Rebuild the retained offset-frame counterexample with Racket authority.

Run through WORK/run_with_racket.py from WORK/ so Catalog can execute the
selected Racket rule. The output is a compact, source-bound JSON witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "97f17772dd96"
CALL = {
    "seed": 20261011,
    "sample_index": 97,
    "overrides": {
        "grid_h": 12,
        "grid_w": 15,
        "n_frames": 3,
        "asymmetry_force": True,
    },
}


def grid_sha256(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    witness = module.generate(
        CALL["seed"],
        CALL["sample_index"],
        **CALL["overrides"],
    )
    self_check_errors = module.self_check(witness, meta=CALL["overrides"])
    observed_axes = module.observe_overrides(witness)
    intended = module.rule_mirror(witness)
    rival = module.CANONICAL_SHORTCUTS["concentric_only"](witness)

    catalog = Catalog(root)
    receipt = catalog.apply(TASK_ID, [witness])
    result = receipt["results"][0]
    racket_output = result["output"]
    canonical = canonical_pairs(TASK_ID, root=root)
    canonical_rival_fit = [
        module.CANONICAL_SHORTCUTS["concentric_only"](pair["input"]) == pair["output"]
        for pair in canonical
    ]

    differences = differing_cells(racket_output, rival)
    checks = {
        "self_check_passed": self_check_errors == [],
        "exact_axes_observed": observed_axes == CALL["overrides"],
        "racket_executed_without_error": result["error"] is None,
        "racket_rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"] is True,
        "racket_rule_hash_matches_generator": receipt["executed_rule_hash"] == module.RULE_HASH,
        "python_mirror_matches_racket": intended == racket_output,
        "rival_fits_all_canonical_pairs": all(canonical_rival_fit),
        "rival_disagrees_on_witness": bool(differences),
        "witness_hook_fires": module.SEMANTIC_WITNESSES["offset_inner_frame"](witness),
    }
    if not all(checks.values()):
        raise SystemExit("counterexample validation failed: " + json.dumps(checks, sort_keys=True))

    report = {
        "schema": "arcpuzzles-counterexample-v1",
        "task_id": TASK_ID,
        "finding": "concentric_only fits every canonical demonstration but undercounts offset nested frames",
        "generator": {
            "source_path": source_path.relative_to(root).as_posix(),
            "sha256": source_sha256,
            "version": module.VERSION,
            "declared_rule_hash": module.RULE_HASH,
        },
        "reproduction": {
            "working_directory": "repo",
            "argv": [
                "python3",
                f"generators/{TASK_ID}/workspace/build_counterexample.py",
                "--out",
                f"generators/{TASK_ID}/counterexamples/concentric-only-offset-inner/counterexample.json",
            ],
            "call": CALL,
        },
        "canonical_fit": {
            "demonstrations": len(canonical),
            "per_pair": canonical_rival_fit,
            "fits_all": all(canonical_rival_fit),
        },
        "observed_axes": observed_axes,
        "self_check_errors": self_check_errors,
        "input": witness,
        "racket_output": racket_output,
        "python_mirror_output": intended,
        "concentric_only_output": rival,
        "differing_cells": differences,
        "hashes": {
            "input": grid_sha256(witness),
            "racket_output": grid_sha256(racket_output),
            "concentric_only_output": grid_sha256(rival),
        },
        "racket_receipt": {
            "executed_rule_hash": receipt["executed_rule_hash"],
            "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
            "error": result["error"],
        },
        "checks": checks,
        "verdict": "counterexample_confirmed",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": report["verdict"],
        "generator_sha256": source_sha256,
        "differing_cells": len(differences),
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
