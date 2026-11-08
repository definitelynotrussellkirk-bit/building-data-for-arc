#!/usr/bin/env python3
"""Task-local semantic regression probe for generator ``13d2544b2b64``.

The central battery is authoritative.  This smaller probe gives future agents a
fast, machine-readable check of the specific failure modes repaired in this
review: exact profile observability, canonical parity, canonical shortcut
survival, generated counterexamples, witness coverage, and lesson
identifiability.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from review_diagnostics import compare_structure
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "13d2544b2b64"
ROOT = find_root(__file__)
RIVAL_DECLARATIONS = ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")


def _load_generator():
    module, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    return module


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def build_report(generator, *, seeds: Iterable[int] = range(20)) -> dict[str, Any]:
    seed_values = tuple(int(seed) for seed in seeds)
    bands = ("easy", "medium", "hard")
    profiles = tuple(generator.SCENE_PROFILES)
    failures: list[str] = []
    profile_counts: Counter[str] = Counter()
    witness_counts: Counter[str] = Counter()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    generated_cases: list[tuple[str, list[list[int]], list[list[int]]]] = []

    for band in bands:
        for seed in seed_values:
            for sample_index, requested in enumerate(profiles):
                try:
                    grid = generator.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        scene_profile=requested,
                    )
                    official = generator.rule_mirror(grid)
                except Exception as exc:  # report exact replay rather than aborting the census
                    failures.append(
                        f"generation raised band={band} seed={seed} "
                        f"sample_index={sample_index} profile={requested}: {exc!r}"
                    )
                    continue

                observed = generator.observe_overrides(grid).get("scene_profile")
                profile_counts[str(observed)] += 1
                if observed != requested:
                    failures.append(
                        f"profile mismatch band={band} seed={seed} requested={requested} "
                        f"observed={observed}"
                    )
                self_errors = generator.self_check(grid, difficulty=band)
                if self_errors:
                    failures.append(
                        f"self_check band={band} seed={seed} profile={requested}: "
                        + "; ".join(self_errors)
                    )
                strict_errors = generator.strict_canonical_like(grid)
                if strict_errors:
                    failures.append(
                        f"strict_canonical_like band={band} seed={seed} profile={requested}: "
                        + "; ".join(strict_errors)
                    )
                if official == grid:
                    failures.append(
                        f"identity output band={band} seed={seed} profile={requested}"
                    )

                unique_inputs.add(_freeze(grid))
                replay = (
                    f"band={band} seed={seed} sample_index={sample_index} profile={requested}"
                )
                generated_cases.append((replay, grid, official))
                for name, witness in generator.SEMANTIC_WITNESSES.items():
                    try:
                        if witness(grid):
                            witness_counts[name] += 1
                    except Exception as exc:
                        failures.append(
                            f"witness {name} raised band={band} seed={seed} "
                            f"profile={requested}: {exc!r}"
                        )

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    canonical_parity_failures: list[str] = []
    for index, pair in enumerate(pairs):
        input_grid = pair["input"]
        expected = pair["output"]
        try:
            actual = generator.rule_mirror(input_grid)
        except Exception as exc:
            canonical_parity_failures.append(f"pair {index}: mirror raised {exc!r}")
            continue
        if actual != expected:
            canonical_parity_failures.append(f"pair {index}: mirror output mismatch")
        errors = generator.strict_canonical_like(input_grid)
        if errors:
            canonical_parity_failures.append(
                f"pair {index}: strict checker rejected canonical input: {errors}"
            )
    failures.extend(canonical_parity_failures)

    rivals: dict[str, dict[str, Any]] = {}
    for declaration in RIVAL_DECLARATIONS:
        for name, rival in getattr(generator, declaration).items():
            key = f"{declaration}.{name}"
            errors: list[str] = []
            fits = True
            for pair in pairs:
                replay = (
                    f"variant={pair['variant']} split={pair['split']} pair={pair['pair_index']}"
                )
                try:
                    actual = rival([row[:] for row in pair["input"]])
                    if actual != pair["output"]:
                        fits = False
                except Exception as exc:
                    fits = False
                    errors.append(f"canonical {replay}: {type(exc).__name__}: {exc}")
            counterexamples = 0
            for replay, grid, official in generated_cases:
                try:
                    if rival([row[:] for row in grid]) != official:
                        counterexamples += 1
                except Exception as exc:
                    errors.append(f"generated {replay}: {type(exc).__name__}: {exc}")
            rivals[key] = {
                "canonical_fit": fits,
                "generated_counterexamples": counterexamples,
                "errors": errors,
            }
            failures.extend(f"rival {key}: {error}" for error in errors)

    canonical_shortcuts: dict[str, bool] = {}
    generated_counterexamples: dict[str, bool] = {}
    for name in generator.CANONICAL_SHORTCUTS:
        result = rivals[f"CANONICAL_SHORTCUTS.{name}"]
        canonical_shortcuts[name] = result["canonical_fit"]
        generated_counterexamples[name] = result["generated_counterexamples"] > 0
        if not result["canonical_fit"]:
            failures.append(f"declared canonical shortcut {name} does not fit all canonical pairs")
        if not generated_counterexamples[name]:
            failures.append(f"no generated counterexample for canonical shortcut {name}")

    lesson_failures: list[str] = []
    for band in bands:
        for seed in seed_values:
            try:
                demos = []
                for sample_index in range(generator.EXAMPLES_NEEDED):
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": generator.rule_mirror(grid)})
                query_grid = generator.generate(
                    seed, generator.EXAMPLES_NEEDED, difficulty=band
                )
                query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
                reasons = generator.lesson_identifiable(demos, query)
            except Exception as exc:
                lesson_failures.append(
                    f"band={band} seed={seed}: lesson probe raised {type(exc).__name__}: {exc}"
                )
                continue
            if reasons:
                lesson_failures.append(
                    f"band={band} seed={seed}: " + "; ".join(reasons)
                )
    failures.extend(lesson_failures)

    expected_per_profile = len(seed_values) * len(bands)
    missing_witnesses = sorted(
        name for name in generator.SEMANTIC_WITNESSES if witness_counts[name] == 0
    )
    if missing_witnesses:
        failures.append(f"zero-hit semantic witnesses: {missing_witnesses}")

    training = [pair for pair in pairs if pair["split"] == "train"]
    structural_support = {
        "canonical_split": "train",
        "canonical_pairs_checked": len(training),
        "generated_label_source": "python_rule_mirror",
        "comparison": compare_structure(
            training,
            [{"input": grid, "output": output} for _replay, grid, output in generated_cases],
        ),
    }

    return {
        "schema": "13d2544b2b64-review-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "seeds": list(seed_values),
        "bands": list(bands),
        "profiles": list(profiles),
        "generated_cases": len(generated_cases),
        "expected_cases": len(seed_values) * len(bands) * len(profiles),
        "expected_per_profile": expected_per_profile,
        "profile_counts": {profile: profile_counts[profile] for profile in profiles},
        "unique_inputs": len(unique_inputs),
        "witness_counts": {
            name: witness_counts[name] for name in generator.SEMANTIC_WITNESSES
        },
        "canonical_pairs_checked": len(pairs),
        "canonical_parity_failures": canonical_parity_failures,
        "canonical_shortcuts": canonical_shortcuts,
        "generated_counterexamples": generated_counterexamples,
        "rivals": rivals,
        "structural_support": structural_support,
        "lesson_failures": lesson_failures,
        "failures": failures,
        "ok": not failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=20, help="number of seeds from zero")
    parser.add_argument("--json", type=Path, help="write the report to this path")
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")

    report = build_report(_load_generator(), seeds=range(args.seeds))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered)
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
