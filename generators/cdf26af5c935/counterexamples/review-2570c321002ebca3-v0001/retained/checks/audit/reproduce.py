#!/usr/bin/env python3
"""Prepare source-bound audit inputs and sampler probes for the assigned targets.

Run from the packet's ``repo`` directory with ``PYTHONPATH=shared/runtime:src``.
This script does not import or invoke private Racket runners; authoritative outputs
are added separately with the public ``arcpuzzles apply`` command.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ASSIGNED = {
    "cdf26af5c935": "c8f050d99cddaf8d25eb2e7c01f105696e1cab028a4a94f0972aea153940f772",
    "f0e701850a95": "9cb24e0f3bfb9cac6d03cc9d691d1d52819e8467383ca1b6826476ffcab8b4f4",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(repo: Path, task_id: str):
    path = repo / "generators" / task_id / "generator.py"
    actual = sha256(path)
    expected = ASSIGNED[task_id]
    if actual != expected:
        raise RuntimeError(f"{task_id}: source hash changed: {actual} != {expected}")
    name = f"audit_{task_id}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path, actual


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"color": color, "area": len(cells), "cells": cells})
    return out


def prepare_cdf(repo: Path, out_root: Path) -> None:
    task = "cdf26af5c935"
    gen, path, source_hash = load_generator(repo, task)
    target = out_root / task
    target.mkdir(parents=True, exist_ok=True)

    seed = 76844440487152
    sample_indices = [33, 34, 35, 36]
    inputs = [gen.generate(seed, i, difficulty="medium") for i in sample_indices]
    checks = [gen.self_check(grid) for grid in inputs]
    if any(checks):
        raise RuntimeError(f"unexpected validator failure: {checks}")
    counts = [gen.semantic_observables(grid)["n_rects"] for grid in inputs]
    if not all(n >= 2 for n in counts[:3]) or counts[3] != 1:
        raise RuntimeError(f"expected three multi-rectangle demos and one single query, got {counts}")

    (target / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    report = {
        "schema": "audit-pre-apply-v1",
        "task_id": task,
        "generator_path": str(path.relative_to(repo)),
        "generator_sha256": source_hash,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "seed": seed,
        "difficulty": "medium",
        "sample_indices": sample_indices,
        "lesson_policy": {"train_indices": [0, 1, 2], "query_index": 3},
        "n_rectangles": counts,
        "validator_errors": checks,
        "documented_generator_domain": True,
        "actual_sampler_support": True,
        "rival": "Apply the intended per-color rectangle fill only when the input has at least two rectangle colors; otherwise return the input unchanged.",
        "rival_fits_all_three_demos": True,
        "rival_disagrees_on_query": True,
    }
    (target / "pre_apply.json").write_text(json.dumps(report, indent=2) + "\n")


def large_component_counterexample() -> list[list[int]]:
    return [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [8, 8, 0, 0, 0, 0, 4, 0, 0, 0],
        [8, 0, 0, 0, 4, 4, 4, 4, 0, 0],
        [8, 8, 8, 0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 4, 4, 4, 4, 0],
        [0, 0, 0, 8, 8, 0, 0, 0, 0, 0],
        [0, 0, 8, 8, 8, 8, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def prepare_f0e(repo: Path, out_root: Path) -> None:
    task = "f0e701850a95"
    gen, path, source_hash = load_generator(repo, task)
    target = out_root / task
    target.mkdir(parents=True, exist_ok=True)

    grid = large_component_counterexample()
    validator_errors = gen.self_check(grid)
    if validator_errors:
        raise RuntimeError(f"counterexample should pass self_check: {validator_errors}")
    areas = sorted(comp["area"] for comp in components(grid))
    if max(areas) <= 5:
        raise RuntimeError(f"counterexample needs a component larger than five cells: {areas}")
    (target / "input.json").write_text(json.dumps(grid, indent=2) + "\n")

    band_counts: dict[str, Any] = {}
    global_max = 0
    errors: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        max_area = 0
        valid = 0
        for sample_index in range(100):
            try:
                generated = gen.generate(918273, sample_index, difficulty=band)
                findings = gen.self_check(generated)
                if findings:
                    raise ValueError(f"self_check: {findings}")
                area = max(comp["area"] for comp in components(generated))
                max_area = max(max_area, area)
                global_max = max(global_max, area)
                valid += 1
            except Exception as exc:  # evidence, not a hidden retry
                errors.append({"band": band, "sample_index": sample_index,
                               "error": f"{type(exc).__name__}: {exc}"})
        band_counts[band] = {"draws": 100, "valid": valid, "max_component_area": max_area}

    base = gen.generate(123456, 17, difficulty="medium")
    palette_size_grid = gen.generate(123456, 17, difficulty="medium", palette_size=2)
    typo_grid = gen.generate(123456, 17, difficulty="medium", typo_axis=999)
    texture_errors = {
        name: gen.self_check(gen.generate(7, 0, difficulty="medium", texture=name))
        for name in gen.DEGENERATE_TEXTURES
    }
    probe = {
        "schema": "audit-sampler-probe-v2",
        "task_id": task,
        "generator_path": str(path.relative_to(repo)),
        "generator_sha256": source_hash,
        "rule_hash": "5fdcc4e7a023",
        "seed": 918273,
        "sample_indices": "0..99 per band",
        "bands": band_counts,
        "total_draws": 300,
        "generation_errors": errors,
        "max_component_area_seen": global_max,
        "all_generated_components_area_le_5": not errors and global_max <= 5,
        "counterexample_component_areas": areas,
        "counterexample_validator_errors": validator_errors,
        "documented_generator_domain": True,
        "actual_sampler_support": False,
        "palette_size_override_changes_grid": palette_size_grid != base,
        "unknown_override_accepted": typo_grid == base,
        "degenerate_texture_self_check_errors": texture_errors,
        "rival": "If every source component has area <=5, apply the intended packer; otherwise return the input unchanged.",
    }
    (target / "sampler_probe.json").write_text(json.dumps(probe, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    prepare_cdf(repo, out)
    prepare_f0e(repo, out)
    print(json.dumps({"status": "prepared", "targets": sorted(ASSIGNED), "out": str(out)}))


if __name__ == "__main__":
    main()
