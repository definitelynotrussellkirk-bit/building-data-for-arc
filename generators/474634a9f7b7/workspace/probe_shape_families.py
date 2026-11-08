#!/usr/bin/env python3
"""Audit generator 474634a9f7b7's shape diversity and declared rivals.

This is a fast, reproducible Python-mirror diagnostic.  It deliberately does
not replace the source-bound Racket battery or lesson census.  Run from the
packet repository root, for example:

    PYTHONPATH=shared/runtime python3 \
      generators/474634a9f7b7/workspace/probe_shape_families.py \
      --out ../checks/shape-family-probe.json \
      --witness-input ../checks/top-or-right-witness-input.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys
from typing import Any, Callable

SCRIPT = Path(__file__).resolve()
TASK_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
GENERATOR_PATH = TASK_ROOT / "generator.py"
TASK_ID = TASK_ROOT.name
sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs  # noqa: E402


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"shape_family_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _declared_rivals(gen) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    declaration = getattr(gen, "LESSON_COMPETITORS", None)
    if not isinstance(declaration, dict) or not declaration:
        raise ValueError("LESSON_COMPETITORS must be a non-empty mapping")
    rivals = {}
    for name, function in declaration.items():
        if not isinstance(name, str) or not callable(function):
            raise ValueError(f"invalid declared rival {name!r}")
        rivals[name] = function
    return rivals


def _target_signature(gen, grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    target = gen._analyze(grid)["target"]
    return tuple(sorted(gen._component_local_coordinates(target)))


def _changed_cells(before: list[list[int]], after: list[list[int]]) -> int:
    return sum(
        before[row][col] != after[row][col]
        for row in range(len(before))
        for col in range(len(before[0]))
    )


def _canonical_rival_fit(gen, rivals) -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=REPO_ROOT, labeled_only=True)
    results = {}
    for name, function in rivals.items():
        fits = [function(deepcopy(pair["input"])) == pair["output"] for pair in pairs]
        results[name] = {
            "pairs": len(pairs),
            "fits": sum(fits),
            "fits_all": all(fits),
            "refuted_pair_indices": [index for index, fit in enumerate(fits) if not fit],
        }
    return results


def _cross_product(gen) -> dict[str, Any]:
    failures = []
    signatures: dict[str, dict[str, str]] = {}
    combinations = 0
    for grid_h, grid_w, side, target_size, family in product(
        gen.GRID_SIZES,
        gen.GRID_SIZES,
        gen.SIDES,
        gen.TARGET_SIZES,
        gen.SHAPE_FAMILIES,
    ):
        expected = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "target_side": side,
            "target_size": target_size,
            "shape_family": family,
        }
        grid = gen.generate(20261007, 11, difficulty="hard", **expected)
        observed = gen.observe_overrides(grid)
        errors = gen.self_check(grid)
        combinations += 1
        if errors or observed != expected:
            failures.append(
                {
                    "expected": expected,
                    "observed": observed,
                    "self_check": errors,
                }
            )
        key = f"{side}:{target_size}"
        signatures.setdefault(key, {})[family] = _digest(_target_signature(gen, grid))
    indistinguishable = [
        key
        for key, family_signatures in signatures.items()
        if len(set(family_signatures.values())) != len(gen.SHAPE_FAMILIES)
    ]
    return {
        "combinations": combinations,
        "failures": failures,
        "distinct_family_signature_groups": len(signatures) - len(indistinguishable),
        "signature_groups": len(signatures),
        "indistinguishable_groups": indistinguishable,
        "signature_sha256_by_side_and_size": signatures,
    }


def _sampler_census(gen, *, seeds: int, indices: int) -> dict[str, Any]:
    report = {}
    all_inputs: set[str] = set()
    invalid = []
    wrong_change_count = []
    for band in ("easy", "medium", "hard"):
        family_counts: Counter[str] = Counter()
        side_counts: Counter[str] = Counter()
        target_size_counts: Counter[int] = Counter()
        signatures: set[str] = set()
        input_hashes: set[str] = set()
        for seed in range(seeds):
            for sample_index in range(indices):
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                observed = gen.observe_overrides(grid)
                output = gen.rule_mirror(grid)
                input_hash = _digest(grid)
                input_hashes.add(input_hash)
                all_inputs.add(input_hash)
                signatures.add(_digest(_target_signature(gen, grid)))
                family_counts[observed["shape_family"]] += 1
                side_counts[observed["target_side"]] += 1
                target_size_counts[observed["target_size"]] += 1
                if errors:
                    invalid.append(
                        {
                            "difficulty": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                changed = _changed_cells(grid, output)
                if changed != 6:
                    wrong_change_count.append(
                        {
                            "difficulty": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "changed_cells": changed,
                        }
                    )
        report[band] = {
            "draws": seeds * indices,
            "unique_inputs": len(input_hashes),
            "unique_target_signatures": len(signatures),
            "shape_family_counts": dict(sorted(family_counts.items())),
            "target_side_counts": dict(sorted(side_counts.items())),
            "target_size_counts": {
                str(key): value for key, value in sorted(target_size_counts.items())
            },
        }
    return {
        "bands": report,
        "unique_inputs_across_bands": len(all_inputs),
        "invalid": invalid,
        "wrong_change_count": wrong_change_count,
    }


def _rotation_census(gen, rivals, *, seeds: int) -> dict[str, Any]:
    demos_needed = int(gen.EXAMPLES_NEEDED)
    width = demos_needed + 1
    starts = range(len(gen.PROFILE_SCHEDULE))
    ambiguities = []
    windows = 0
    rotations = 0
    refutations: dict[str, Counter[str]] = {
        name: Counter() for name in rivals
    }
    for band in ("easy", "medium", "hard"):
        for seed in range(seeds):
            for start in starts:
                pairs = []
                for sample_index in range(start, start + width):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                windows += 1
                for query_index in range(width):
                    rotations += 1
                    query = pairs[query_index]
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    hook_reasons = gen.lesson_identifiable(
                        deepcopy(demos), deepcopy(query)
                    )
                    surviving_changers = []
                    for name, function in rivals.items():
                        survives = all(
                            function(deepcopy(pair["input"])) == pair["output"]
                            for pair in demos
                        )
                        changes_query = (
                            function(deepcopy(query["input"])) != query["output"]
                        )
                        if survives and changes_query:
                            refutations[name]["ambiguous"] += 1
                            surviving_changers.append(name)
                        else:
                            refutations[name]["distinguished"] += 1
                    if hook_reasons or surviving_changers:
                        ambiguities.append(
                            {
                                "difficulty": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "sample_indices": list(range(start, start + width)),
                                "surviving_query_changers": surviving_changers,
                                "lesson_identifiable_findings": hook_reasons,
                            }
                        )
    return {
        "windows": windows,
        "rotations": rotations,
        "ambiguities": ambiguities,
        "rival_rotation_verdicts": {
            name: dict(sorted(counts.items())) for name, counts in sorted(refutations.items())
        },
    }


def _shortcut_witness(gen) -> dict[str, Any]:
    seed = 20261007
    sample_index = 2
    difficulty = "medium"
    overrides = {"shape_family": "branched"}
    grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
    intended = gen.rule_mirror(grid)
    rival_name = "top_or_right_only"
    rival = gen.CANONICAL_SHORTCUTS[rival_name](deepcopy(grid))
    analysis = gen._analyze(grid)
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "observed": gen.observe_overrides(grid),
        "self_check": gen.self_check(grid),
        "rival": rival_name,
        "input": grid,
        "python_mirror_output": intended,
        "rival_output": rival,
        "disagrees": intended != rival,
        "target_color": analysis["target"]["color"],
        "target_side": analysis["target"]["side"],
        "target_size": analysis["target"]["size"],
        "input_sha256": _digest(grid),
        "python_mirror_output_sha256": _digest(intended),
        "rival_output_sha256": _digest(rival),
    }


def build_report(*, sampler_seeds: int, sampler_indices: int, rotation_seeds: int):
    gen = _load_generator()
    rivals = _declared_rivals(gen)
    witness = _shortcut_witness(gen)
    report = {
        "schema": "474634a9f7b7-shape-family-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "declared_rule_hash": gen.RULE_HASH,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        "sampler": {
            "seed_range": [0, sampler_seeds - 1],
            "sample_index_range": [0, sampler_indices - 1],
            **_sampler_census(gen, seeds=sampler_seeds, indices=sampler_indices),
        },
        "override_cross_product": _cross_product(gen),
        "canonical_rival_fit": _canonical_rival_fit(gen, rivals),
        "cyclic_rotations": {
            "seed_range": [0, rotation_seeds - 1],
            "starts_per_seed_and_band": len(gen.PROFILE_SCHEDULE),
            **_rotation_census(gen, rivals, seeds=rotation_seeds),
        },
        "top_or_right_shortcut_witness": witness,
        "limits": [
            "Generated labels and rival predictions use the Python audit mirror; the retained Racket battery/apply command is the authority.",
            "The rival census covers only the generator's current declared competitors, not every conceivable rule.",
            "Exact grid and normalized target-shape counts are finite sampled support, not an exhaustive grammar census.",
        ],
    }
    cross = report["override_cross_product"]
    sampler = report["sampler"]
    rotations = report["cyclic_rotations"]
    report["passed"] = bool(
        not cross["failures"]
        and not cross["indistinguishable_groups"]
        and not sampler["invalid"]
        and not sampler["wrong_change_count"]
        and all(
            set(band["shape_family_counts"]) == set(gen.SHAPE_FAMILIES)
            for band in sampler["bands"].values()
        )
        and not rotations["ambiguities"]
        and witness["disagrees"]
        and not witness["self_check"]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sampler-seeds", type=int, default=32)
    parser.add_argument("--sampler-indices", type=int, default=8)
    parser.add_argument("--rotation-seeds", type=int, default=16)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-input", type=Path, required=True)
    args = parser.parse_args()
    if min(args.sampler_seeds, args.sampler_indices, args.rotation_seeds) < 1:
        parser.error("sample counts must all be positive")

    report = build_report(
        sampler_seeds=args.sampler_seeds,
        sampler_indices=args.sampler_indices,
        rotation_seeds=args.rotation_seeds,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.witness_input.parent.mkdir(parents=True, exist_ok=True)
    args.witness_input.write_text(
        json.dumps(report["top_or_right_shortcut_witness"]["input"], indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "generator_sha256": report["generator_sha256"],
                "sampler_draws": sum(
                    band["draws"] for band in report["sampler"]["bands"].values()
                ),
                "override_combinations": report["override_cross_product"]["combinations"],
                "rotations": report["cyclic_rotations"]["rotations"],
                "ambiguities": len(report["cyclic_rotations"]["ambiguities"]),
                "passed": report["passed"],
                "out": str(args.out),
                "witness_input": str(args.witness_input),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
