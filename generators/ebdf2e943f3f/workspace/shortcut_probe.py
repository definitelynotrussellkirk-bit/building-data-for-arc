#!/usr/bin/env python3
"""Source-bound rival and lesson-schedule probe for ebdf2e943f3f.

The probe intentionally discovers rivals from the generator declarations instead
of copying a rival-name list.  It checks canonical fit, generated
counterexamples, every held-out query position in deterministic five-pair
bundles, and every requested cyclic start.  Labels here use ``rule_mirror``;
retain the public Racket battery/census as the final authority check.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
from typing import Any, Iterable


def _load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(
        path
        or os.environ.get("GENERATOR_UNDER_TEST")
        or Path(__file__).resolve().parents[1] / "generator.py"
    ).resolve()
    spec = importlib.util.spec_from_file_location("ebdf2e943f3f_probe_generator", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_file(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> list[dict[str, int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return [{"row": -1, "col": -1, "expected": -1, "rival": -1}]
    return [
        {"row": row, "col": col, "expected": expected, "rival": rival}
        for row, (expected_row, rival_row) in enumerate(zip(left, right))
        for col, (expected, rival) in enumerate(zip(expected_row, rival_row))
        if expected != rival
    ]


def _declared_mapping(gen: Any, name: str) -> dict[str, Any]:
    value = getattr(gen, name, {})
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a dict, found {type(value).__name__}")
    invalid = [key for key, fn in value.items() if not isinstance(key, str) or not callable(fn)]
    if invalid:
        raise TypeError(f"{name} contains invalid entries: {invalid!r}")
    return dict(value)


def _relevant_witnesses(gen: Any, rivals: dict[str, Any]) -> dict[str, Any]:
    witnesses = _declared_mapping(gen, "SEMANTIC_WITNESSES")
    claims = getattr(gen, "WITNESS_RIVALS", {})
    if not isinstance(claims, dict):
        raise TypeError("WITNESS_RIVALS must be a dict")
    result = {}
    for witness_name, claimed in claims.items():
        names = [claimed] if isinstance(claimed, str) else list(claimed)
        if witness_name in witnesses and any(name in rivals for name in names):
            result[witness_name] = witnesses[witness_name]
    return result


def _call_solver(fn, grid):
    original = deepcopy(grid)
    first = fn(deepcopy(grid))
    second = fn(deepcopy(grid))
    if grid != original:
        raise AssertionError("probe caller input was mutated")
    if first != second:
        raise AssertionError("solver is non-deterministic")
    return first


def build_report(
    gen: Any,
    *,
    canonical_pairs: Iterable[dict[str, Any]],
    seeds: Iterable[int],
    starts: Iterable[int],
    bands: Iterable[str | None],
) -> dict[str, Any]:
    """Return a JSON-serializable report; no private labels or runner imports."""
    canonical = list(canonical_pairs)
    seed_values = list(seeds)
    start_values = list(starts)
    band_values = list(bands)
    if not canonical:
        raise ValueError("at least one labeled canonical pair is required")
    if not seed_values or not start_values or not band_values:
        raise ValueError("seeds, starts, and bands must all be non-empty")

    shortcuts = _declared_mapping(gen, "CANONICAL_SHORTCUTS")
    competitors = _declared_mapping(gen, "LESSON_COMPETITORS")
    rivals = dict(shortcuts)
    rivals.update(competitors)
    witnesses = _relevant_witnesses(gen, rivals)
    examples_needed = getattr(gen, "EXAMPLES_NEEDED", None)
    if type(examples_needed) is not int or not 1 <= examples_needed <= 32:
        raise ValueError("EXAMPLES_NEEDED must be an integer in 1..32")

    source = inspect.getsourcefile(gen)
    source_path = Path(source).resolve() if source else None
    report: dict[str, Any] = {
        "schema": "ebdf2e943f3f-shortcut-probe-v1",
        "task_id": getattr(gen, "TASK_ID", None),
        "generator_version": getattr(gen, "VERSION", None),
        "generator_sha256": _sha256_file(source_path),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "label_authority": (
            "generator.rule_mirror for this task-local probe; validate final "
            "claims with the retained Racket battery and lesson census"
        ),
        "settings": {
            "seeds": seed_values,
            "starts": start_values,
            "bands": ["default" if band is None else band for band in band_values],
            "examples_needed": examples_needed,
            "pairs_per_bundle": examples_needed + 1,
            "rotation_policy": "hold out every pair once",
        },
        "canonical_shortcuts": {},
        "declared_competitors": sorted(competitors),
        "relevant_witnesses": sorted(witnesses),
        "first_counterexample": {},
        "schedule": {
            "bundles_checked": 0,
            "pairs_checked": 0,
            "rotations_checked": 0,
            "minimum_witnesses_per_bundle": None,
            "witness_firings": dict.fromkeys(witnesses, 0),
            "coverage_failures": [],
            "rotation_failures": [],
            "generation_failures": [],
        },
        "limits": [
            "Finite declared-rival probe, not proof of universal identifiability.",
            "Direct sequential draws are checked; runner rejection/resampling is covered by the public census.",
            "Python mirror labels are diagnostic; Racket remains the selected authority.",
        ],
    }

    for name, shortcut in sorted(shortcuts.items()):
        fits = 0
        errors = []
        for index, pair in enumerate(canonical):
            try:
                prediction = _call_solver(shortcut, pair["input"])
                fits += int(prediction == pair["output"])
            except Exception as exc:  # retained as evidence, not silently skipped
                errors.append({"pair_index": index, "error": f"{type(exc).__name__}: {exc}"})
        report["canonical_shortcuts"][name] = {
            "pairs": len(canonical),
            "fits": fits,
            "errors": errors,
            "status": "error" if errors else "fits_all" if fits == len(canonical) else "refuted",
        }

    minimum_witnesses: int | None = None
    for band in band_values:
        band_name = "default" if band is None else band
        for seed in seed_values:
            for start in start_values:
                bundle = []
                bundle_error = None
                for sample_index in range(start, start + examples_needed + 1):
                    try:
                        grid = gen.generate(seed, sample_index, difficulty=band)
                        errors = list(gen.self_check(grid) or [])
                        if errors:
                            raise ValueError("self_check: " + "; ".join(errors))
                        expected = gen.rule_mirror(deepcopy(grid))
                        pair = {
                            "input": grid,
                            "output": expected,
                            "sample_index": sample_index,
                        }
                        bundle.append(pair)
                        report["schedule"]["pairs_checked"] += 1
                        for witness_name, witness in witnesses.items():
                            if bool(witness(deepcopy(grid))):
                                report["schedule"]["witness_firings"][witness_name] += 1
                        for rival_name, rival in rivals.items():
                            prediction = _call_solver(rival, grid)
                            if prediction != expected and rival_name not in report["first_counterexample"]:
                                report["first_counterexample"][rival_name] = {
                                    "band": band_name,
                                    "seed": seed,
                                    "sample_index": sample_index,
                                    "input": grid,
                                    "expected_output": expected,
                                    "rival_output": prediction,
                                    "differing_cells": _diff_cells(expected, prediction),
                                }
                    except Exception as exc:
                        bundle_error = {
                            "band": band_name,
                            "seed": seed,
                            "start": start,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                        report["schedule"]["generation_failures"].append(bundle_error)
                        break
                if bundle_error:
                    continue

                report["schedule"]["bundles_checked"] += 1
                witness_count = sum(
                    any(bool(witness(deepcopy(pair["input"]))) for witness in witnesses.values())
                    for pair in bundle
                )
                minimum_witnesses = (
                    witness_count
                    if minimum_witnesses is None
                    else min(minimum_witnesses, witness_count)
                )
                if witnesses and witness_count < 2:
                    report["schedule"]["coverage_failures"].append(
                        {
                            "band": band_name,
                            "seed": seed,
                            "start": start,
                            "witness_inputs": witness_count,
                            "reason": "fewer than two rival-refuting inputs survive arbitrary one-pair holdout",
                        }
                    )

                for query_index, query in enumerate(bundle):
                    demos = [pair for index, pair in enumerate(bundle) if index != query_index]
                    public_demos = [
                        {"input": pair["input"], "output": pair["output"]}
                        for pair in demos
                    ]
                    public_query = {"input": query["input"], "output": query["output"]}
                    reasons = list(gen.lesson_identifiable(public_demos, public_query) or [])
                    ambiguous = []
                    scoring_errors = []
                    for rival_name, rival in rivals.items():
                        try:
                            fits_demos = all(
                                _call_solver(rival, demo["input"]) == demo["output"]
                                for demo in demos
                            )
                            changes_query = _call_solver(rival, query["input"]) != query["output"]
                            if fits_demos and changes_query:
                                ambiguous.append(rival_name)
                        except Exception as exc:
                            scoring_errors.append(
                                {"rival": rival_name, "error": f"{type(exc).__name__}: {exc}"}
                            )
                    report["schedule"]["rotations_checked"] += 1
                    if reasons or ambiguous or scoring_errors:
                        report["schedule"]["rotation_failures"].append(
                            {
                                "band": band_name,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "query_sample_index": query["sample_index"],
                                "hook_reasons": reasons,
                                "ambiguous_rivals": ambiguous,
                                "scoring_errors": scoring_errors,
                            }
                        )

    report["schedule"]["minimum_witnesses_per_bundle"] = minimum_witnesses
    missing_counterexamples = sorted(set(shortcuts) - set(report["first_counterexample"]))
    report["missing_counterexamples"] = missing_counterexamples
    canonical_failures = [
        name
        for name, row in report["canonical_shortcuts"].items()
        if row["status"] != "fits_all"
    ]
    report["status"] = (
        "pass"
        if not canonical_failures
        and not missing_counterexamples
        and not report["schedule"]["coverage_failures"]
        and not report["schedule"]["rotation_failures"]
        and not report["schedule"]["generation_failures"]
        else "fail"
    )
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", help="generator.py path (default: sibling or GENERATOR_UNDER_TEST)")
    parser.add_argument("--seed-base", type=int, default=1000)
    parser.add_argument("--seeds", type=int, default=8, help="number of consecutive seeds")
    parser.add_argument("--starts", type=int, default=16, help="cyclic starts 0..N-1")
    parser.add_argument("--out", type=Path, help="write JSON report here")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.seeds < 1 or args.starts < 1:
        raise SystemExit("--seeds and --starts must be positive")
    gen = _load_generator(args.generator)
    from reviewer_support import canonical_pairs, find_root

    report = build_report(
        gen,
        canonical_pairs=canonical_pairs(
            gen.TASK_ID,
            root=find_root(__file__),
            labeled_only=True,
        ),
        seeds=range(args.seed_base, args.seed_base + args.seeds),
        starts=range(args.starts),
        bands=(None, "easy", "medium", "hard"),
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
