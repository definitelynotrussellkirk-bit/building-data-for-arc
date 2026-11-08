#!/usr/bin/env python3
"""Reproducible, source-bound probes for the two assigned audit targets.

This script never edits the audited generators. It records exact source hashes,
inputs, outputs, override comparisons, and validator behavior as JSON.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_generator(task_id: str):
    source = REPO / "generators" / task_id / "generator.py"
    body = source.read_bytes()
    name = f"audit_{task_id}_{sha256_bytes(body)}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    # Compile the exact bytes whose digest we report, avoiding stale bytecode.
    exec(compile(body, str(source), "exec"), module.__dict__)
    return module, source, sha256_bytes(body)


def summarize_grid(grid: list[list[int]]) -> dict[str, Any]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    nonzero = [
        [r, c, value]
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    return {
        "dimensions": [h, w],
        "grid_sha256": grid_sha256(grid),
        "nonzero_cells": nonzero,
        "nonzero_count": len(nonzero),
        "colors": sorted({value for row in grid for value in row}),
        "grid": grid,
    }


def generation_case(module, *, seed: int, sample_index: int, **overrides: Any) -> dict[str, Any]:
    case: dict[str, Any] = {
        "seed": seed,
        "sample_index": sample_index,
        "overrides": overrides,
    }
    try:
        grid = module.generate(seed, sample_index, **overrides)
    except Exception as exc:  # evidence should preserve rejection as data
        case.update(
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        return case
    case["status"] = "ok"
    case.update(summarize_grid(grid))
    try:
        case["self_check"] = module.self_check(grid)
    except Exception as exc:
        case["self_check_error"] = {
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return case


def same_grid(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("status") == right.get("status") == "ok"
        and left.get("grid_sha256") == right.get("grid_sha256")
    )


def write_result(task_id: str, build: Callable[[Any], dict[str, Any]]) -> Path:
    module, source, source_hash = load_generator(task_id)
    payload = {
        "schema": "arcpuzzles-assigned-audit-probe-v1",
        "task_id": task_id,
        "generator_path": str(source.relative_to(REPO)),
        "generator_sha256": source_hash,
        "generator_version": getattr(module, "VERSION", None),
        "declared_axes": getattr(module, "AXES", None),
        "reproduction": {
            "cwd": "WORK/repo",
            "command": "PYTHONPATH=shared/runtime python3 ../checks/audit/probe_audit_targets.py",
        },
    }
    payload.update(build(module))
    out = HERE / task_id / "override_and_validator_probe.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return out


def probe_4de(module) -> dict[str, Any]:
    seed, sample_index = 20261020, 4
    cases = {
        "baseline": generation_case(module, seed=seed, sample_index=sample_index),
        "palette_warm": generation_case(
            module, seed=seed, sample_index=sample_index, palette_kind="warm"
        ),
        "palette_cool": generation_case(
            module, seed=seed, sample_index=sample_index, palette_kind="cool"
        ),
        "helpful_texture_warm": generation_case(
            module, seed=seed, sample_index=sample_index, texture="warm"
        ),
        "helpful_texture_cool": generation_case(
            module, seed=seed, sample_index=sample_index, texture="cool"
        ),
        "anchor_false": generation_case(
            module, seed=seed, sample_index=sample_index, anchor_corner=False
        ),
        "anchor_true": generation_case(
            module, seed=seed, sample_index=sample_index, anchor_corner=True
        ),
        "asymmetry_false": generation_case(
            module, seed=seed, sample_index=sample_index, asymmetry_force=False
        ),
        "asymmetry_true": generation_case(
            module, seed=seed, sample_index=sample_index, asymmetry_force=True
        ),
        "unknown_override": generation_case(
            module, seed=seed, sample_index=sample_index, misspelled_axis="accepted"
        ),
        "consumed_size_control": generation_case(
            module, seed=seed, sample_index=sample_index, grid_h=7, grid_w=7
        ),
    }
    comparisons = {
        "palette_kind_warm_equals_cool": same_grid(
            cases["palette_warm"], cases["palette_cool"]
        ),
        "helpful_texture_warm_equals_cool": same_grid(
            cases["helpful_texture_warm"], cases["helpful_texture_cool"]
        ),
        "anchor_false_equals_true": same_grid(
            cases["anchor_false"], cases["anchor_true"]
        ),
        "asymmetry_false_equals_true": same_grid(
            cases["asymmetry_false"], cases["asymmetry_true"]
        ),
        "unknown_override_equals_baseline": same_grid(
            cases["unknown_override"], cases["baseline"]
        ),
    }
    return {
        "cases": cases,
        "comparisons": comparisons,
        "finding": {
            "summary": (
                "Several advertised helpful controls and an unknown override are "
                "accepted without changing the generated instance."
            ),
            "all_inert_control_comparisons_true": all(comparisons.values()),
        },
    }


def probe_29d(module) -> dict[str, Any]:
    seed, sample_index = 20261020, 4
    cases = {
        "baseline": generation_case(module, seed=seed, sample_index=sample_index),
        "color_1": generation_case(
            module, seed=seed, sample_index=sample_index, color=1
        ),
        "color_9": generation_case(
            module, seed=seed, sample_index=sample_index, color=9
        ),
        "invalid_color_99": generation_case(
            module, seed=seed, sample_index=sample_index, color=99
        ),
        "helpful_texture_warm": generation_case(
            module, seed=seed, sample_index=sample_index, texture="warm"
        ),
        "helpful_texture_cool": generation_case(
            module, seed=seed, sample_index=sample_index, texture="cool"
        ),
        "anchor_false": generation_case(
            module, seed=seed, sample_index=sample_index, anchor_corner=False
        ),
        "anchor_true": generation_case(
            module, seed=seed, sample_index=sample_index, anchor_corner=True
        ),
        "unknown_override": generation_case(
            module, seed=seed, sample_index=sample_index, misspelled_axis="accepted"
        ),
        "consumed_size_control": generation_case(
            module, seed=seed, sample_index=sample_index, grid_h=6, grid_w=6
        ),
    }
    comparisons = {
        "color_1_equals_color_9": same_grid(cases["color_1"], cases["color_9"]),
        "invalid_color_99_equals_baseline": same_grid(
            cases["invalid_color_99"], cases["baseline"]
        ),
        "helpful_texture_warm_equals_cool": same_grid(
            cases["helpful_texture_warm"], cases["helpful_texture_cool"]
        ),
        "anchor_false_equals_true": same_grid(
            cases["anchor_false"], cases["anchor_true"]
        ),
        "unknown_override_equals_baseline": same_grid(
            cases["unknown_override"], cases["baseline"]
        ),
    }
    malformed = [[1, 2], [3, 4]]
    validator = {
        "grid": malformed,
        "ordinary_self_check": module.self_check(malformed),
        "full_grid_meta_self_check": module.self_check(
            malformed, meta={"texture": "full_grid"}
        ),
        "two_seeds_meta_self_check": module.self_check(
            malformed, meta={"texture": "two_seeds"}
        ),
        "no_seed_meta_self_check": module.self_check(
            malformed, meta={"texture": "no_seed"}
        ),
    }
    return {
        "cases": cases,
        "comparisons": comparisons,
        "validator_bypass": validator,
        "finding": {
            "summary": (
                "The advertised color and several helpful controls are inert, "
                "invalid/unknown overrides are silently accepted, and caller-supplied "
                "degenerate metadata bypasses structural self-checking."
            ),
            "all_inert_control_comparisons_true": all(comparisons.values()),
            "arbitrary_rectangular_grid_accepted_with_degenerate_meta": all(
                validator[key] == []
                for key in (
                    "full_grid_meta_self_check",
                    "two_seeds_meta_self_check",
                    "no_seed_meta_self_check",
                )
            ),
        },
    }


if __name__ == "__main__":
    outputs = [
        write_result("4de7c8083804", probe_4de),
        write_result("29d9bc0725c4", probe_29d),
    ]
    for path in outputs:
        print(path)
