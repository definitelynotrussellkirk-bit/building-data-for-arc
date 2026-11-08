#!/usr/bin/env python3
"""Fast source-bound contract probe for generator 9d0a6f959321.

Run from the repository root with::

    PYTHONPATH=shared/runtime python3 generators/9d0a6f959321/workspace/contract_probe.py \
        --out generators/9d0a6f959321/workspace/contract_probe_report.json

The public battery remains authoritative.  This probe is a cheap future-agent
triage tool: it checks exact overrides, an independent rule mirror, semantic
witness/rival coverage, and both production-order and query-rotation lesson
identifiability on a deterministic sample.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("contract_probe_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            touches = any(
                r in (0, height - 1) or c in (0, width - 1) for r, c in cells
            )
            result.append({"color": color, "cells": cells, "touches_border": touches})
    return result


def _independent_oracle(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for component in _components(grid):
        if component["color"] == 7 and component["touches_border"]:
            for row, col in component["cells"]:
                out[row][col] = 3
    return out


def _axis_profiles() -> tuple[dict[str, int], ...]:
    return (
        {
            "grid_h": 7,
            "grid_w": 9,
            "n_border_components": 1,
            "n_interior_components": 1,
            "n_distractors": 0,
        },
        {
            "grid_h": 12,
            "grid_w": 14,
            "n_border_components": 2,
            "n_interior_components": 2,
            "n_distractors": 2,
        },
    )


def run_probe(*, samples_per_band: int = 48, starts: int = 12) -> dict[str, Any]:
    if samples_per_band < 1 or starts < 1:
        raise ValueError("samples_per_band and starts must both be positive")

    gen = _load_generator()
    bands = ("easy", "medium", "hard")
    override_failures: list[dict[str, Any]] = []
    self_check_failures: list[dict[str, Any]] = []
    mirror_failures: list[dict[str, Any]] = []
    deterministic_failures: list[dict[str, Any]] = []
    production_ambiguities: list[dict[str, Any]] = []
    rotation_ambiguities: list[dict[str, Any]] = []
    witness_counts: Counter[str] = Counter()
    rival_refutations: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()

    for band_index, band in enumerate(bands):
        for profile_index, requested in enumerate(_axis_profiles()):
            grid = gen.generate(
                7300 + band_index,
                900 + profile_index,
                difficulty=band,
                **requested,
            )
            observed = gen.observe_overrides(grid)
            if observed != requested:
                override_failures.append(
                    {"band": band, "requested": requested, "observed": observed}
                )

        for index in range(samples_per_band):
            seed = 91_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            replay = gen.generate(seed, index, difficulty=band)
            if replay != grid:
                deterministic_failures.append({"band": band, "seed": seed, "index": index})
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                self_check_failures.append(
                    {"band": band, "seed": seed, "index": index, "errors": errors}
                )
            intended = _independent_oracle(grid)
            if gen.rule_mirror(grid) != intended:
                mirror_failures.append({"band": band, "seed": seed, "index": index})
            profile_counts[f"{len(grid)}x{len(grid[0])}"] += 1
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(witness(deepcopy(grid)))
            for name, rival in gen.SEMANTIC_RIVALS.items():
                rival_refutations[name] += rival(deepcopy(grid)) != intended

        for start in range(starts):
            lesson = []
            for offset in range(4):
                grid = gen.generate(777 + band_index, start + offset, difficulty=band)
                lesson.append({"input": grid, "output": _independent_oracle(grid)})

            reasons = gen.lesson_identifiable(deepcopy(lesson[:3]), deepcopy(lesson[3]))
            if reasons:
                production_ambiguities.append(
                    {"band": band, "start": start, "query_index": 3, "reasons": reasons}
                )

            for query_index in range(4):
                demos = [pair for i, pair in enumerate(lesson) if i != query_index]
                query = lesson[query_index]
                reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                if reasons:
                    rotation_ambiguities.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

    missing_witnesses = sorted(name for name in gen.SEMANTIC_WITNESSES if not witness_counts[name])
    unrefuted_rivals = sorted(name for name in gen.SEMANTIC_RIVALS if not rival_refutations[name])
    summary = {
        "generated": len(bands) * samples_per_band,
        "override_profiles_checked": len(bands) * len(_axis_profiles()),
        "override_failures": len(override_failures),
        "self_check_failures": len(self_check_failures),
        "rule_mirror_failures": len(mirror_failures),
        "determinism_failures": len(deterministic_failures),
        "production_lessons_checked": len(bands) * starts,
        "query_rotations_checked": len(bands) * starts * 4,
        "ambiguous_production_lessons": len(production_ambiguities),
        "ambiguous_query_rotations": len(rotation_ambiguities),
        "missing_witnesses": missing_witnesses,
        "unrefuted_rivals": unrefuted_rivals,
    }
    failed = any(
        (
            override_failures,
            self_check_failures,
            mirror_failures,
            deterministic_failures,
            production_ambiguities,
            rotation_ambiguities,
            missing_witnesses,
            unrefuted_rivals,
        )
    )
    return {
        "schema": "arc-generator-contract-probe-v1",
        "status": "fail" if failed else "pass",
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "policy": {
            "bands": list(bands),
            "samples_per_band": samples_per_band,
            "lesson_starts_per_band": starts,
            "demonstrations": 3,
            "production_query_index": 3,
            "rotation_policy": "hold out each of four materialized pairs once",
            "scope": "declared rivals and witnesses only; Python mirror, not a substitute for Racket battery",
        },
        "summary": summary,
        "profile_counts": dict(sorted(profile_counts.items())),
        "witness_counts": dict(sorted(witness_counts.items())),
        "rival_refutations": dict(sorted(rival_refutations.items())),
        "failures": {
            "overrides": override_failures,
            "self_check": self_check_failures,
            "rule_mirror": mirror_failures,
            "determinism": deterministic_failures,
            "production_lessons": production_ambiguities,
            "query_rotations": rotation_ambiguities,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=48)
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(samples_per_band=args.samples_per_band, starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
