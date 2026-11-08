"""Independent, repeatable qualification probe for task 6737eb62cf42.

The selected Racket program remains the label authority.  This tool checks the
Python generator contract, an independent crop oracle, the declared rivals, the
complete finite override product, every cyclic schedule window/query rotation,
and emits an exact singleton-boundary witness for an authoritative `arcpuzzles
apply` run.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "6737eb62cf42"
sys.path[:0] = [str(ROOT / "shared/runtime"), str(ROOT / "src")]
from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator(path: Path | None = None):
    source = (path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_crop_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source


def crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def labelled(grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": crop_nonzero(grid)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_probe(module) -> tuple[dict[str, Any], list[list[int]]]:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical = {
        name: all(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in module.CANONICAL_SHORTCUTS.items()
    }

    override_cases = 0
    override_errors: list[dict[str, Any]] = []
    distinct_inputs: set[str] = set()
    for case_index, values in enumerate(
        itertools.product(
            (None, "easy", "medium", "hard"),
            module.SCHEDULE_PROFILES,
            module.PLACEMENTS,
            range(2, 5),
            module.TEXTURES,
        )
    ):
        band, profile, placement, palette_size, texture = values
        requested = {
            "scene_profile": profile,
            "placement": placement,
            "palette_size": palette_size,
            "texture": texture,
        }
        grid = module.generate(50000 + case_index, case_index, difficulty=band, **requested)
        override_cases += 1
        observed = module.observe_overrides(grid)
        problems = module.self_check(grid, difficulty=band, meta={"overrides": requested})
        if observed != requested or problems or module.rule_mirror(grid) != crop_nonzero(grid):
            override_errors.append(
                {
                    "case_index": case_index,
                    "difficulty": band,
                    "requested": requested,
                    "observed": observed,
                    "self_check": problems,
                }
            )
        distinct_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())

    schedule_windows = 0
    rotations = 0
    ambiguities: list[dict[str, Any]] = []
    witness_counts: Counter[str] = Counter()
    for band in (None, "easy", "medium", "hard"):
        for start in range(module.LESSON_SCHEDULE_PERIOD):
            pairs4 = [
                labelled(module.generate(70000 + start, start + offset, difficulty=band))
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            schedule_windows += 1
            for pair in pairs4:
                for name, predicate in module.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(predicate(pair["input"]))
            for query_index in range(len(pairs4)):
                query = pairs4[query_index]
                demos = [pair for index, pair in enumerate(pairs4) if index != query_index]
                rotations += 1
                findings = module.lesson_identifiable(demos, query)
                if findings:
                    ambiguities.append(
                        {
                            "difficulty": band,
                            "start": start,
                            "query_index": query_index,
                            "findings": findings,
                        }
                    )

    difficulty_collisions: list[dict[str, int]] = []
    for seed, sample_index in ((0, 0), (17, 3), (4400, 11)):
        grids = [module.generate(seed, sample_index, difficulty=band) for band in ("easy", "medium", "hard")]
        if len({json.dumps(grid, separators=(",", ":")) for grid in grids}) != 3:
            difficulty_collisions.append({"seed": seed, "sample_index": sample_index})

    witness = module.generate(
        52,
        1,
        difficulty="medium",
        scene_profile="canonical_9x10_crop5x7",
        placement="lower_right",
        palette_size=3,
        texture="singleton_extreme",
    )
    intended = crop_nonzero(witness)
    rival_outputs = {
        name: rival(witness) for name, rival in module.CANONICAL_SHORTCUTS.items()
    }
    differing_cells = {}
    for name, output in rival_outputs.items():
        max_h = max(len(intended), len(output))
        max_w = max(max(map(len, intended)), max(map(len, output)))
        differences = []
        for row in range(max_h):
            for col in range(max_w):
                a = intended[row][col] if row < len(intended) and col < len(intended[row]) else None
                b = output[row][col] if row < len(output) and col < len(output[row]) else None
                if a != b:
                    differences.append([row, col, a, b])
        differing_cells[name] = differences

    report = {
        "schema": "6737eb62cf42-reference-probe-v1",
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "canonical_pairs": len(pairs),
        "canonical_shortcuts_fit": canonical,
        "override_product": {
            "cases": override_cases,
            "errors": override_errors,
            "distinct_inputs": len(distinct_inputs),
        },
        "schedule": {
            "windows": schedule_windows,
            "query_rotations": rotations,
            "ambiguities": ambiguities,
            "witness_counts_across_pairs": dict(witness_counts),
        },
        "difficulty_collisions": difficulty_collisions,
        "witness": {
            "generation": {
                "seed": 52,
                "sample_index": 1,
                "difficulty": "medium",
                "overrides": {
                    "scene_profile": "canonical_9x10_crop5x7",
                    "placement": "lower_right",
                    "palette_size": 3,
                    "texture": "singleton_extreme",
                },
            },
            "input": witness,
            "independent_intended_output": intended,
            "rival_outputs": rival_outputs,
            "differing_cells": differing_cells,
            "self_check": module.self_check(witness),
            "observed_axes": module.observe_overrides(witness),
        },
        "limits": [
            "The independent Python crop is supplementary; the canonical Racket output must be retained separately.",
            "Finite declared-rival checks do not prove uniqueness against every possible program.",
        ],
    }
    return report, witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-input", type=Path)
    args = parser.parse_args()
    module, source = load_generator(args.generator)
    report, witness = run_probe(module)
    report["generator_sha256"] = sha256(source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.witness_input:
        args.witness_input.parent.mkdir(parents=True, exist_ok=True)
        args.witness_input.write_text(json.dumps(witness, indent=2) + "\n")
    summary = {
        "generator_sha256": report["generator_sha256"],
        "canonical_shortcuts_fit": report["canonical_shortcuts_fit"],
        "override_cases": report["override_product"]["cases"],
        "override_errors": len(report["override_product"]["errors"]),
        "schedule_windows": report["schedule"]["windows"],
        "query_rotations": report["schedule"]["query_rotations"],
        "ambiguities": len(report["schedule"]["ambiguities"]),
        "difficulty_collisions": len(report["difficulty_collisions"]),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(
        not all(report["canonical_shortcuts_fit"].values())
        or bool(report["override_product"]["errors"])
        or bool(report["schedule"]["ambiguities"])
        or bool(report["difficulty_collisions"])
    )


if __name__ == "__main__":
    raise SystemExit(main())
