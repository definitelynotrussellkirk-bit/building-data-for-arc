#!/usr/bin/env python3
"""Bounded source-pinned override-contract probe for e83be06f6b58."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "e83be06f6b58"
EXPECTED_SHA256 = "dbad09a9bda351d440790ad6bed1ca5def5ba013abfc449747cc60cf371093fa"


def attempt(module: Any, name: str, overrides: dict[str, Any]) -> dict[str, Any]:
    try:
        grid = module.generate(0, 0, **overrides)
    except Exception as exc:  # exact rejection is evidence
        return {
            "case": name,
            "overrides": overrides,
            "accepted": False,
            "exception": f"{type(exc).__name__}: {exc}",
        }
    return {
        "case": name,
        "overrides": overrides,
        "accepted": True,
        "shape": [len(grid), len(grid[0]) if grid else 0],
        "self_check": module.self_check(grid),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    module, source_path, source_sha256 = load_selected_generator(TASK_ID)
    if source_sha256 != EXPECTED_SHA256:
        raise ValueError(
            f"peer source differs from assignment: {source_sha256} != {EXPECTED_SHA256}"
        )

    cases = [
        attempt(module, "unknown_palette_kind", {"palette_kind": "not-a-palette"}),
        attempt(module, "unknown_texture", {"texture": "not-a-texture"}),
        attempt(module, "fractional_run_min", {"run_min": 2.5}),
        attempt(module, "boolean_run_min", {"run_min": True}),
        attempt(module, "declared_grid_w_lower_bound", {"grid_w": 6}),
        attempt(module, "declared_grid_w_upper_bound", {"grid_w": 16}),
    ]

    default_checks: list[dict[str, Any]] = []
    for difficulty in (None, "easy", "hard"):
        failures = []
        for seed in range(32):
            grid = module.generate(seed, 0, difficulty=difficulty)
            messages = module.self_check(grid, difficulty=difficulty)
            if messages:
                failures.append({"seed": seed, "messages": messages})
        default_checks.append(
            {
                "difficulty": difficulty,
                "seeds": 32,
                "self_check_failures": failures,
            }
        )

    findings = []
    by_name = {case["case"]: case for case in cases}
    for name in (
        "unknown_palette_kind",
        "unknown_texture",
        "fractional_run_min",
        "boolean_run_min",
    ):
        if by_name[name]["accepted"]:
            findings.append(
                f"{name} is silently accepted and normalized/falls back instead of being rejected"
            )
    for name in ("declared_grid_w_lower_bound", "declared_grid_w_upper_bound"):
        if not by_name[name]["accepted"]:
            findings.append(
                f"{name} is declared valid by AXES but rejected by the runtime draw range"
            )

    report = {
        "schema": "e83be06f6b58-override-contract-probe-v1",
        "task_id": TASK_ID,
        "source": str(source_path),
        "source_sha256": source_sha256,
        "status": "finding" if findings else "no_finding",
        "cases": cases,
        "default_self_check": default_checks,
        "findings": findings,
        "limits": "Bounded contract/type probe only; no Racket replay and no source edit.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
