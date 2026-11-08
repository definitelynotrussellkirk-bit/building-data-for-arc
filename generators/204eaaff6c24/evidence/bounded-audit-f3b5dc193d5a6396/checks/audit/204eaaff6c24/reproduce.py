#!/usr/bin/env python3
"""Source-bound reproduction of current 204eaaff6c24 construction defects."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "204eaaff6c24"


def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def attempt(fn):
    try:
        value = fn()
    except Exception as exc:  # evidence captures exact current behavior
        return {
            "status": "raised",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    return {
        "status": "returned",
        "grid": value,
        "grid_sha256": digest(value),
    }


def main() -> int:
    here = Path(__file__).resolve().parent
    root = find_root(__file__)
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=root)

    seed = 17
    invalid_sample = 3
    invalid_base = {"seed": seed, "sample_index": invalid_sample, "difficulty": "medium"}
    valid_two = gen.generate(seed, invalid_sample, difficulty="medium", n_cells=2)
    default = gen.generate(seed, invalid_sample, difficulty="medium")

    invalid_cases = {
        "float_n_cells_2_7": attempt(
            lambda: gen.generate(seed, invalid_sample, difficulty="medium", n_cells=2.7)
        ),
        "bool_n_cells_true": attempt(
            lambda: gen.generate(seed, invalid_sample, difficulty="medium", n_cells=True)
        ),
        "unknown_axis": attempt(
            lambda: gen.generate(seed, invalid_sample, difficulty="medium", unknown_axis=123)
        ),
    }
    invalid_cases["float_n_cells_2_7"]["equals_integer_2"] = (
        invalid_cases["float_n_cells_2_7"].get("grid") == valid_two
    )
    invalid_cases["bool_n_cells_true"]["observed"] = (
        gen.observe_overrides(invalid_cases["bool_n_cells_true"]["grid"])
        if invalid_cases["bool_n_cells_true"]["status"] == "returned"
        else None
    )
    invalid_cases["unknown_axis"]["equals_default"] = (
        invalid_cases["unknown_axis"].get("grid") == default
    )
    for case in invalid_cases.values():
        if case["status"] == "returned":
            case["self_check"] = gen.self_check(case["grid"])

    free_request = {
        "seed": 17,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": {"n_cells": 8, "fg_layout": "diagonal", "fg_color": 4},
    }
    free_attempt = attempt(
        lambda: gen.generate(
            free_request["seed"],
            free_request["sample_index"],
            difficulty=free_request["difficulty"],
            **free_request["overrides"],
        )
    )
    control_overrides = {
        **free_request["overrides"],
        "grid_h": 8,
        "grid_w": 8,
    }
    control_grid = gen.generate(
        free_request["seed"],
        free_request["sample_index"],
        difficulty=free_request["difficulty"],
        **control_overrides,
    )
    control = {
        "request": {
            "seed": free_request["seed"],
            "sample_index": free_request["sample_index"],
            "difficulty": free_request["difficulty"],
            "overrides": control_overrides,
        },
        "grid": control_grid,
        "grid_sha256": digest(control_grid),
        "self_check": gen.self_check(control_grid),
        "observed_overrides": gen.observe_overrides(control_grid),
    }

    semantic_contract_symbols = {
        name: hasattr(gen, name)
        for name in (
            "strict_canonical_like",
            "SEMANTIC_WITNESSES",
            "SEMANTIC_RIVALS",
            "lesson_identifiable",
        )
    }

    report = {
        "schema": "204eaaff6c24-audit-reproduction-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "invalid_scalar_and_unknown_override_request": invalid_base,
        "valid_integer_two_grid_sha256": digest(valid_two),
        "default_grid_sha256": digest(default),
        "invalid_cases": invalid_cases,
        "free_dimension_layout_request": free_request,
        "free_dimension_layout_result": free_attempt,
        "explicit_dimension_control": control,
        "semantic_contract_symbols": semantic_contract_symbols,
        "conclusions": [
            "n_cells=2.7 is accepted and coerced to the integer-2 result",
            "n_cells=True is accepted as a one-cell request",
            "an unknown override key is ignored and yields the default grid",
            "a feasible 8-cell diagonal request is rejected when dimensions are free, but succeeds with exact 8x8 dimensions",
            "the selected source declares no strict/semantic lesson contract",
        ],
    }
    (here / "reproduction.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (here / "input.json").write_text(
        json.dumps({"input": control_grid}, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "generator_sha256": source_sha,
        "invalid_cases": {
            key: value["status"] for key, value in invalid_cases.items()
        },
        "free_dimension_layout_result": free_attempt,
        "control_self_check": control["self_check"],
        "control_observed": control["observed_overrides"],
        "semantic_contract_symbols": semantic_contract_symbols,
        "out": str(here / "reproduction.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
