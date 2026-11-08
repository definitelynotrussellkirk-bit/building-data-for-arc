#!/usr/bin/env python3
"""Reproduce exact-transform override drift for ARC generator 28ad783a6a98.

This is an audit-only probe.  It never edits the target generator.  It exercises
all advertised transform pairs over a fixed seed range, infers the transforms
actually encoded in the generated panels, and writes one generated witness for
supported Racket evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "28ad783a6a98"
CODES = ("r1", "r2", "r3", "fh", "fv", "tr", "atr")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_generator(repo: Path):
    runtime = repo / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def infer_code(module: Any, source: list[list[int]], target: list[list[int]]) -> list[str]:
    return [code for code in CODES if module._xform_grid(source, code) == target]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--witness-seed", type=int, default=0)
    parser.add_argument("--witness-first", default="r1", choices=CODES)
    parser.add_argument("--witness-second", default="r3", choices=CODES)
    args = parser.parse_args()

    repo = args.repo.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    module, generator_path = load_generator(repo)
    generator_sha = sha256_bytes(generator_path.read_bytes())

    cases: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    for seed in range(args.seed_start, args.seed_start + args.seed_count):
        for first in CODES:
            for second in CODES:
                grid = module.generate(
                    seed,
                    args.sample_index,
                    first_transform=first,
                    second_transform=second,
                )
                panels = module._split_panels(grid)
                observed_first = infer_code(module, panels[0], panels[1])
                observed_second = infer_code(module, panels[2], panels[3])
                input_sha = sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())
                unique_inputs.add(input_sha)
                errors = module.self_check(
                    grid,
                    meta={"first_transform": first, "second_transform": second},
                )
                case = {
                    "seed": seed,
                    "sample_index": args.sample_index,
                    "requested": {"first_transform": first, "second_transform": second},
                    "observed": {
                        "first_transform": observed_first,
                        "second_transform": observed_second,
                    },
                    "self_check_errors": errors,
                    "input_sha256": input_sha,
                }
                cases.append(case)
                if observed_first != [first] or observed_second != [second]:
                    mismatches.append(case)

    witness_grid = module.generate(
        args.witness_seed,
        args.sample_index,
        first_transform=args.witness_first,
        second_transform=args.witness_second,
    )
    witness_panels = module._split_panels(witness_grid)
    witness_observed_first = infer_code(module, witness_panels[0], witness_panels[1])
    witness_observed_second = infer_code(module, witness_panels[2], witness_panels[3])
    requested_output = module._xform_grid(
        module._xform_grid(witness_panels[4], args.witness_first),
        args.witness_second,
    )
    observed_output = module._xform_grid(
        module._xform_grid(witness_panels[4], witness_observed_first[0]),
        witness_observed_second[0],
    )
    witness_errors = module.self_check(
        witness_grid,
        meta={
            "first_transform": args.witness_first,
            "second_transform": args.witness_second,
        },
    )

    report = {
        "schema": "arcpuzzles-audit-exact-override-matrix-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path.relative_to(repo.parent)),
        "generator_sha256": generator_sha,
        "generator_version": getattr(module, "VERSION", None),
        "advertised_transform_codes": list(CODES),
        "seed_range": [args.seed_start, args.seed_start + args.seed_count - 1],
        "sample_index": args.sample_index,
        "requested_pairs_per_seed": len(CODES) ** 2,
        "draws": len(cases),
        "unique_inputs": len(unique_inputs),
        "exact_matches": len(cases) - len(mismatches),
        "mismatches": len(mismatches),
        "mismatch_rate": len(mismatches) / len(cases),
        "self_check_failures": sum(bool(c["self_check_errors"]) for c in cases),
        "mismatch_cases": mismatches,
        "method": (
            "Generate each advertised transform pair, split the five 4x4 panels, "
            "and infer the unique D4 code mapping panel 1->2 and panel 3->4."
        ),
    }
    (out / "override_matrix.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "input.json").write_text(json.dumps(witness_grid, indent=2) + "\n")
    witness = {
        "schema": "arcpuzzles-audit-counterexample-pre-racket-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "seed": args.witness_seed,
        "sample_index": args.sample_index,
        "overrides": {
            "first_transform": args.witness_first,
            "second_transform": args.witness_second,
        },
        "observed": {
            "first_transform": witness_observed_first,
            "second_transform": witness_observed_second,
        },
        "input": witness_grid,
        "input_sha256": sha256_bytes(json.dumps(witness_grid, separators=(",", ":")).encode()),
        "requested_exact_control_output": requested_output,
        "output_implied_by_observed_panels": observed_output,
        "requested_output_differs_from_observed": freeze(requested_output) != freeze(observed_output),
        "self_check_errors": witness_errors,
        "documented_generator_domain": True,
        "domain_reason": (
            "The input was emitted by the assigned generator using two advertised exact "
            "transform overrides and passes its self_check."
        ),
    }
    (out / "witness_pre_racket.json").write_text(json.dumps(witness, indent=2) + "\n")

    print(json.dumps({
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "draws": len(cases),
        "unique_inputs": len(unique_inputs),
        "mismatches": len(mismatches),
        "witness_observed": witness["observed"],
        "witness_self_check_errors": witness_errors,
    }, indent=2))
    return 0 if mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
