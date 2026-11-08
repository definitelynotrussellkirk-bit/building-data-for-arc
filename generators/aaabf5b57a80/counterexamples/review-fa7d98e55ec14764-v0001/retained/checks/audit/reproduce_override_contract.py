#!/usr/bin/env python3
"""Minimal source-bound witnesses for the two assigned peer audits."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
OUT_ROOT = ROOT.parent / "checks" / "audit"


def load(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_hash(task_id: str) -> str:
    # Same public convention as shared/tools/canonical_profile_gate.py:
    # sha256 of whitespace-normalized selected program_solution, first 12 hex.
    canonical = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with canonical.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            source = row.get("program_solution")
            if row.get("task_id") == task_id and source:
                normalized = " ".join(str(source).split())
                return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise FileNotFoundError(f"{task_id}: no selected program_solution")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(module: Any, *, seed: int, sample_index: int, difficulty: str, overrides: dict[str, Any]) -> dict[str, Any]:
    recipe = {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
    }
    try:
        grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
    except Exception as exc:  # witness records exact public-call behavior
        return {
            "recipe": recipe,
            "accepted": False,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    try:
        errors = module.self_check(grid, difficulty=difficulty)
    except TypeError:
        errors = module.self_check(grid)
    return {
        "recipe": recipe,
        "accepted": True,
        "grid": grid,
        "shape": [len(grid), len(grid[0]) if grid else 0],
        "self_check": list(errors),
    }


def write(task_id: str, payload: dict[str, Any]) -> None:
    task_dir = OUT_ROOT / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "override-contract-witness.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def audit_aaab() -> None:
    task_id = "aaabf5b57a80"
    module, source = load(task_id)
    payload = {
        "schema": "arc-peer-audit-override-witness-v1",
        "task_id": task_id,
        "finding": "advertised exact-control values are rejected, and unknown keys are accepted",
        "generator_path": str(source.relative_to(ROOT)),
        "generator_sha256": sha256(source),
        "canonical_rule_hash": canonical_hash(task_id),
        "command": ["python3", "../checks/audit/reproduce_override_contract.py"],
        "cwd": "repo",
        "declared_axes": module.AXES,
        "witnesses": {
            "declared_grid_minimum_rejected": call(
                module, seed=0, sample_index=3, difficulty="easy",
                overrides={"grid_h": 8, "grid_w": 8},
            ),
            "declared_palette_minimum_rejected": call(
                module, seed=0, sample_index=3, difficulty="easy",
                overrides={"interior_palette_size": 1},
            ),
            "unknown_key_silently_accepted": call(
                module, seed=0, sample_index=3, difficulty="easy",
                overrides={"__override_contract_unknown_axis__": 123},
            ),
        },
        "interpretation": (
            "AXES declares grid_h/grid_w 8..30 and interior_palette_size 1..6, "
            "but legal declared minima are rejected by band-local draw bounds. "
            "A misspelled axis is silently ignored, so a caller cannot trust an accepted call to honor its curriculum request."
        ),
        "patch_status": "audit only; target left unchanged",
    }
    write(task_id, payload)


def audit_8387() -> None:
    task_id = "8387b52c80df"
    module, source = load(task_id)
    base = call(module, seed=0, sample_index=0, difficulty="medium", overrides={})
    requested = {
        "frame_color": 1,
        "seed_color": 9,
        "palette_kind": "warm_frame",
        "palette_size": 2,
        "position_bias": "scattered",
        "n_distinct_colors": 7,
    }
    overridden = call(module, seed=0, sample_index=0, difficulty="medium", overrides=requested)
    frames = []
    if overridden.get("accepted"):
        for color, r0, c0, r1, c1 in module._frame_bboxes(overridden["grid"]):
            seed_colors = sorted({
                overridden["grid"][r][c]
                for r in range(r0 + 1, r1)
                for c in range(c0 + 1, c1)
                if overridden["grid"][r][c] not in (0, color)
            })
            frames.append({
                "bbox": [r0, c0, r1, c1],
                "actual_frame_color": color,
                "actual_seed_colors": seed_colors,
            })
    payload = {
        "schema": "arc-peer-audit-override-witness-v1",
        "task_id": task_id,
        "finding": "accepted exact semantic controls are ignored; other advertised values are rejected",
        "generator_path": str(source.relative_to(ROOT)),
        "generator_sha256": sha256(source),
        "canonical_rule_hash": canonical_hash(task_id),
        "command": ["python3", "../checks/audit/reproduce_override_contract.py"],
        "cwd": "repo",
        "declared_axes": module.AXES,
        "witnesses": {
            "baseline": base,
            "accepted_semantic_overrides": overridden,
            "accepted_overrides_equal_baseline": base.get("grid") == overridden.get("grid"),
            "requested_semantic_values": requested,
            "observed_frames": frames,
            "declared_grid_minimum_rejected": call(
                module, seed=0, sample_index=0, difficulty="easy",
                overrides={"grid_h": 6},
            ),
            "declared_frame_count_rejected": call(
                module, seed=0, sample_index=0, difficulty="easy",
                overrides={"n_frames": 2},
            ),
            "unknown_key_silently_accepted": call(
                module, seed=0, sample_index=0, difficulty="easy",
                overrides={"__override_contract_unknown_axis__": 123},
            ),
        },
        "interpretation": (
            "The accepted call requests frame_color=1 and seed_color=9 but is byte-for-byte identical to the baseline; "
            "the realized frame is color 8 and the seed is color 5, while self_check still passes. "
            "Thus accepted exact controls do not describe the generated lesson."
        ),
        "patch_status": "audit only; target left unchanged",
    }
    write(task_id, payload)


if __name__ == "__main__":
    audit_aaab()
    audit_8387()
