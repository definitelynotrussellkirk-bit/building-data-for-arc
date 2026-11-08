#!/usr/bin/env python3
"""Deterministically audit the be7f70e60fb7 semantic curriculum.

This is a reviewer-facing probe, not part of runtime generator selection.  It
checks schedule coverage, deterministic generation, exact override
observability, grammar/self-checks, non-identity transformations, whole-lesson
identifiability, and rival refutation over a configurable seed prefix.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Iterable, Sequence

TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
BANDS = ("easy", "medium", "hard")


def _load_generator() -> ModuleType:
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("be7f70e60fb7_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(failures: list[dict[str, object]], kind: str, **context: object) -> None:
    failures.append({"kind": kind, **context})


def build_report(generator: ModuleType, *, seeds: Iterable[int]) -> dict[str, object]:
    seed_values = tuple(int(seed) for seed in seeds)
    failures: list[dict[str, object]] = []
    profile_counts: Counter[str] = Counter()
    rivals_refuted = {name: False for name in generator.LESSON_COMPETITORS}
    generated_cases = 0

    for seed in seed_values:
        for band in BANDS:
            scheduled = [
                generator.schedule_profile(seed, index, band)
                for index in range(len(generator.SCENE_PROFILES))
            ]
            if set(scheduled) != set(generator.SCENE_PROFILES):
                _record(
                    failures,
                    "schedule_coverage",
                    seed=seed,
                    band=band,
                    observed=scheduled,
                )

            demos = []
            for index, profile in enumerate(generator.SCENE_PROFILES):
                grid = generator.generate(
                    seed,
                    index,
                    difficulty=band,
                    scene_profile=profile,
                )
                repeated = generator.generate(
                    seed,
                    index,
                    difficulty=band,
                    scene_profile=profile,
                )
                generated_cases += 1
                profile_counts[profile] += 1

                if grid != repeated:
                    _record(
                        failures,
                        "nondeterministic",
                        seed=seed,
                        band=band,
                        profile=profile,
                    )
                observed = generator.observe_overrides(grid)
                if observed != {"scene_profile": profile}:
                    _record(
                        failures,
                        "override_not_observable",
                        seed=seed,
                        band=band,
                        profile=profile,
                        observed=observed,
                    )
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    _record(
                        failures,
                        "self_check",
                        seed=seed,
                        band=band,
                        profile=profile,
                        errors=errors,
                    )
                output = generator.rule_mirror(grid)
                if output == grid:
                    _record(
                        failures,
                        "identity_rule",
                        seed=seed,
                        band=band,
                        profile=profile,
                    )
                demos.append({"input": grid, "output": output})

            query_grid = generator.generate(
                seed,
                len(generator.SCENE_PROFILES),
                difficulty=band,
            )
            query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
            lesson_errors = generator.lesson_identifiable(demos, query)
            if lesson_errors:
                _record(
                    failures,
                    "lesson_not_identifiable",
                    seed=seed,
                    band=band,
                    errors=lesson_errors,
                )

            for name, rival in generator.LESSON_COMPETITORS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    rivals_refuted[name] = True
                else:
                    _record(
                        failures,
                        "rival_not_refuted",
                        seed=seed,
                        band=band,
                        rival=name,
                    )

    return {
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "seed_count": len(seed_values),
        "bands": list(BANDS),
        "generated_cases": generated_cases,
        "profiles": {
            profile: profile_counts.get(profile, 0)
            for profile in generator.SCENE_PROFILES
        },
        "rivals_refuted": rivals_refuted,
        "failures": failures,
        "ok": not failures and all(rivals_refuted.values()),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        type=int,
        default=20,
        help="audit integer seeds in range(0, N); default: 20",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="write the complete JSON report to this path",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.seeds < 1:
        raise SystemExit("--seeds must be at least 1")
    report = build_report(_load_generator(), seeds=range(args.seeds))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
