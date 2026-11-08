#!/usr/bin/env python3
"""Produce deterministic, Racket-backed evidence for the two assigned audit targets."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

from puzzle_generators import runner
from scripts.canonical_profile_gate import normalized_rule_hash


def _seed(task_id: str, label: str) -> int:
    digest = hashlib.sha256(f"generator-review-audit:{task_id}:{label}".encode()).hexdigest()
    return int(digest[:15], 16)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exception_record(exc: BaseException) -> dict:
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "repr": repr(exc),
        "traceback_tail": traceback.format_exc().splitlines()[-12:],
    }


def _racket_apply(bundle, grid):
    bridge = None
    try:
        bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
        return {"status": "ok", "output": runner._apply_rule(bridge, fn_name, grid)}
    except Exception as exc:  # evidence intentionally records the authority failure
        return {"status": "error", "error": _exception_record(exc)}
    finally:
        if bridge is not None:
            try:
                bridge.shutdown()
            except Exception:
                pass


def _global_overlay_rival(grid: list[list[int]]) -> list[list[int]]:
    """Tile 2x2, then paint every tiled background cell cyan, regardless of column."""
    h, w = len(grid), len(grid[0])
    return [
        [grid[r % h][c % w] if grid[r % h][c % w] != 0 else 8 for c in range(2 * w)]
        for r in range(2 * h)
    ]


def _base_record(task_id: str, bundle) -> dict:
    mod_path = Path(bundle.generator_module.__file__).resolve()
    rule_bytes = bundle.rule_source.encode("utf-8")
    return {
        "schema": "generator-review-audit-evidence-v1",
        "task_id": task_id,
        "generator": {
            "path": str(mod_path),
            "sha256": _sha256_bytes(mod_path.read_bytes()),
            "version": getattr(bundle.generator_module, "VERSION", None),
        },
        "racket_authority": {
            "rule_task_id": bundle.rule_task_id,
            "rule_file": bundle.rule_file,
            "source_sha256": _sha256_bytes(rule_bytes),
            "normalized_rule_hash": normalized_rule_hash(bundle.rule_source),
            "racket_path": os.environ.get("RACKET_PATH"),
        },
        "execution": {
            "cwd": str(Path.cwd()),
            "argv": sys.argv,
            "python": sys.version,
        },
    }


def audit_849(bundle) -> dict:
    mod = bundle.generator_module
    seed = _seed(bundle.task_id, "no-bar")
    overrides = {"grid_h": 7, "grid_w": 7, "texture": "no_bar"}
    grid = mod.generate(seed, 0, difficulty="easy", **overrides)
    check = mod.self_check(grid, difficulty="easy", meta=None)
    racket = _racket_apply(bundle, grid)
    return {
        "finding": "declared no_bar texture is accepted by self_check but crashes the canonical Racket rule",
        "severity": "high",
        "seed": seed,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": overrides,
        "declared_texture_valid": "no_bar" in str(mod.AXES["texture"]["valid"]).split("|"),
        "input": grid,
        "nonzero_cells": sum(cell != 0 for row in grid for cell in row),
        "self_check_findings": check,
        "self_check_accepts": not check,
        "racket": racket,
        "reproduced": (not check and racket["status"] == "error"),
    }


def _capture_generate(mod, *, seed, sample_index, difficulty, overrides) -> dict:
    try:
        grid = mod.generate(seed, sample_index, difficulty=difficulty, **overrides)
        return {"status": "ok", "grid": grid}
    except Exception as exc:
        return {"status": "error", "error": _exception_record(exc)}


def audit_15d(bundle) -> dict:
    mod = bundle.generator_module
    seed = _seed(bundle.task_id, "all-active")
    overrides = {"grid_h": 4, "grid_w": 4, "texture": "all_active_cols"}
    grid = mod.generate(seed, 0, difficulty="medium", **overrides)
    check = mod.self_check(grid, difficulty="medium", meta=None)
    racket = _racket_apply(bundle, grid)
    rival = _global_overlay_rival(grid)
    active_cols = [c for c in range(len(grid[0])) if any(row[c] != 0 for row in grid)]
    blank_cols = [c for c in range(len(grid[0])) if all(row[c] == 0 for row in grid)]

    boundary_seed = _seed(bundle.task_id, "declared-boundaries")
    declared_grid_boundary = {"grid_h": 7, "grid_w": 7}
    declared_palette_boundary = {"palette_size": 1}
    boundary_grid = _capture_generate(
        mod,
        seed=boundary_seed,
        sample_index=1,
        difficulty="medium",
        overrides=declared_grid_boundary,
    )
    boundary_palette = _capture_generate(
        mod,
        seed=boundary_seed,
        sample_index=2,
        difficulty="medium",
        overrides=declared_palette_boundary,
    )

    return {
        "primary_finding": "declared all_active_cols texture is self-check-valid and makes the global-overlay shortcut exactly answer-equivalent",
        "severity": "high",
        "seed": seed,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": overrides,
        "declared_texture_valid": "all_active_cols" in str(mod.AXES["texture"]["valid"]).split("|"),
        "input": grid,
        "active_columns": active_cols,
        "blank_columns": blank_cols,
        "documented_invariant_requires_blank_column": any(
            ">=1 column is entirely bg" in str(item) for item in mod.INVARIANTS
        ),
        "self_check_findings": check,
        "self_check_accepts": not check,
        "racket": racket,
        "global_overlay_rival_output": rival,
        "racket_equals_global_overlay_rival": racket.get("status") == "ok" and racket.get("output") == rival,
        "reproduced": (
            not check
            and not blank_cols
            and racket.get("status") == "ok"
            and racket.get("output") == rival
        ),
        "secondary_contract_findings": {
            "declared_domains": {
                "grid_h": mod.AXES["grid_h"]["valid"],
                "grid_w": mod.AXES["grid_w"]["valid"],
                "palette_size": mod.AXES["palette_size"]["valid"],
            },
            "grid_7x7_medium_attempt": {
                "seed": boundary_seed,
                "sample_index": 1,
                "difficulty": "medium",
                "overrides": declared_grid_boundary,
                "result": boundary_grid,
            },
            "palette_size_1_attempt": {
                "seed": boundary_seed,
                "sample_index": 2,
                "difficulty": "medium",
                "overrides": declared_palette_boundary,
                "result": boundary_palette,
            },
            "reproduced": boundary_grid["status"] == "error" and boundary_palette["status"] == "error",
        },
    }


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"849c171da23c", "15d6a8756e63"}:
        print("usage: probe_audit_target.py TASK_ID", file=sys.stderr)
        return 2
    task_id = sys.argv[1]
    bundle = runner._load_bundle(task_id)
    record = _base_record(task_id, bundle)
    record["evidence"] = audit_849(bundle) if task_id == "849c171da23c" else audit_15d(bundle)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["evidence"].get("reproduced") else 1


if __name__ == "__main__":
    raise SystemExit(main())
