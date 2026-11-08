#!/usr/bin/env python3
"""Portable semantic audit for the 611cc0f4e0fe curriculum.

This task-local probe complements the shared lesson census in two ways:

* it forces every declared profile in every difficulty band; and
* it rotates each scheduled profile into the query position while retaining a
  complete four-demonstration curriculum.

The report reads rival declarations from the generator itself, so future edits
cannot silently leave a copied rival list stale.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

TASK_ID = "611cc0f4e0fe"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

BANDS = ("easy", "medium", "hard")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_generator():
    return _load_module(f"audit_{TASK_ID}_generator", TASK_DIR / "generator.py")


def _canonical_row() -> dict[str, Any]:
    source = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in source.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise RuntimeError(f"canonical row {TASK_ID} not found in {source}")


def _grid(raw: Sequence[Sequence[int]]) -> list[list[int]]:
    return [[int(value) for value in row] for row in raw]


def _pair(input_grid, output_grid) -> dict[str, list[list[int]]]:
    return {"input": input_grid, "output": output_grid}


def build_report(generator, *, seeds: Iterable[int] = range(8)) -> dict[str, Any]:
    seeds = tuple(int(seed) for seed in seeds)
    profiles = tuple(generator.SCENE_PROFILES)
    failures: list[str] = []
    profile_counts: Counter[str] = Counter()
    band_counts: Counter[str] = Counter()
    strict_hits: Counter[str] = Counter()
    rival_counterexamples: Counter[str] = Counter(
        {name: 0 for name in generator.LESSON_COMPETITORS}
    )

    generated_cases = 0
    for band in BANDS:
        for seed in seeds:
            for profile_index, profile in enumerate(profiles):
                generated_cases += 1
                try:
                    grid = generator.generate(
                        seed,
                        profile_index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                except Exception as exc:  # report all cases instead of stopping early
                    failures.append(
                        f"generate({band}, seed={seed}, profile={profile}) raised "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue

                observed = generator.observe_overrides(grid).get("scene_profile")
                if observed != profile:
                    failures.append(
                        f"observer mismatch for {band}/seed={seed}/{profile}: {observed!r}"
                    )
                else:
                    profile_counts[profile] += 1
                band_counts[band] += 1

                check = generator.self_check(grid, difficulty=band)
                if check:
                    failures.append(
                        f"self_check rejected {band}/seed={seed}/{profile}: {check[0]}"
                    )

                intended = generator.rule_mirror(grid)
                if intended == grid:
                    failures.append(
                        f"identity transformation for {band}/seed={seed}/{profile}"
                    )
                if not generator.strict_canonical_like(grid):
                    strict_hits[band] += 1

                for name, rival in generator.LESSON_COMPETITORS.items():
                    try:
                        if rival(grid) != intended:
                            rival_counterexamples[name] += 1
                    except Exception as exc:
                        failures.append(
                            f"rival {name} raised on {band}/seed={seed}/{profile}: "
                            f"{type(exc).__name__}: {exc}"
                        )

    # Each four-demo window contains all profiles. Rotating the start index also
    # rotates every profile into the query slot (start + len(profiles)).
    cyclic_lessons = 0
    query_profile_counts: Counter[str] = Counter()
    lesson_failures: list[str] = []
    for band_index, band in enumerate(BANDS):
        for start in range(len(profiles)):
            seed = 100_000 + 1_000 * band_index + start
            demos = []
            for offset in range(len(profiles)):
                grid = generator.generate(seed, start + offset, difficulty=band)
                demos.append(_pair(grid, generator.rule_mirror(grid)))
            query_grid = generator.generate(
                seed, start + len(profiles), difficulty=band
            )
            query = _pair(query_grid, generator.rule_mirror(query_grid))
            cyclic_lessons += 1
            query_profile = generator.observe_overrides(query_grid).get("scene_profile")
            if query_profile is not None:
                query_profile_counts[query_profile] += 1
            reasons = generator.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append(
                    f"lesson {band}/start={start}/query={query_profile}: {reasons}"
                )
    failures.extend(lesson_failures)

    canonical = _canonical_row()
    canonical_shortcuts_fit: dict[str, bool] = {}
    canonical_pairs = [*canonical["train"], *canonical["test"]]
    for index, raw_pair in enumerate(canonical_pairs):
        input_grid = _grid(raw_pair["input"])
        expected = _grid(raw_pair["output"])
        mirrored = generator.rule_mirror(input_grid)
        if mirrored != expected:
            failures.append(f"rule_mirror disagrees with canonical pair {index}")
    for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
        fit = True
        for raw_pair in canonical_pairs:
            input_grid = _grid(raw_pair["input"])
            expected = _grid(raw_pair["output"])
            try:
                if shortcut(input_grid) != expected:
                    fit = False
            except Exception as exc:
                fit = False
                failures.append(
                    f"canonical shortcut {name} raised {type(exc).__name__}: {exc}"
                )
        canonical_shortcuts_fit[name] = fit
        if not fit:
            failures.append(
                f"declared canonical shortcut {name} does not fit every canonical pair"
            )

    for name, count in rival_counterexamples.items():
        if count == 0:
            failures.append(f"declared rival {name} has no generated counterexample")

    expected_query_counts = {profile: len(BANDS) for profile in profiles}
    if dict(query_profile_counts) != expected_query_counts:
        failures.append(
            f"query rotation mismatch: expected {expected_query_counts}, "
            f"observed {dict(query_profile_counts)}"
        )

    return {
        "schema": "611cc0f4e0fe_curriculum_audit/1",
        "task_id": TASK_ID,
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "seeds": list(seeds),
        "bands": list(BANDS),
        "profiles": list(profiles),
        "generated_cases": generated_cases,
        "profile_counts": dict(profile_counts),
        "band_counts": dict(band_counts),
        "strict_hits": dict(strict_hits),
        "rival_counterexamples": dict(rival_counterexamples),
        "canonical_shortcuts_fit": canonical_shortcuts_fit,
        "cyclic_lessons": cyclic_lessons,
        "query_profile_counts": dict(query_profile_counts),
        "lesson_failures": lesson_failures,
        "failures": failures,
        "ok": not failures,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        type=int,
        default=8,
        help="number of consecutive seeds to audit (default: 8)",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="optional report path; stdout is always emitted",
    )
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be at least 1")

    report = build_report(_load_generator(), seeds=range(args.seeds))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered)
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
