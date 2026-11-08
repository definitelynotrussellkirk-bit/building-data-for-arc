#!/usr/bin/env python3
"""Audit d8b498586958 lesson assembly against its declared rivals.

Two populations are reported separately:

1. ``production_windows``: four consecutive demonstrations followed by the
   next generated pair as query.  This is the generator's documented assembly
   policy and should be identifiable for every cyclic start.
2. ``arbitrary_query_rotations``: each member of the same five-pair window is
   moved into the query position.  This is intentionally a stronger, unsupported
   stress test; it makes the limitation of a four-demo/four-operation dictionary
   explicit instead of silently conflating it with the production policy.

The probe dynamically reads LESSON_COMPETITORS and CANONICAL_SHORTCUTS from the
selected generator.  It never copies a rival-name list.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Iterable

TASK_ID = "d8b498586958"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"


def _load_generator(path: Path = GENERATOR_PATH):
    spec = importlib.util.spec_from_file_location(f"lesson_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _named_rivals(gen) -> dict[str, Callable[[Any], Any]]:
    rivals: dict[str, Callable[[Any], Any]] = {}
    for namespace in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        declarations = getattr(gen, namespace, {})
        if not isinstance(declarations, dict):
            raise TypeError(f"{namespace} must be a dict, got {type(declarations).__name__}")
        for name, rival in declarations.items():
            if not isinstance(name, str) or not callable(rival):
                raise TypeError(f"invalid {namespace} entry: {name!r} -> {rival!r}")
            rivals[f"{namespace}:{name}"] = rival
    return rivals


def _evaluate_lesson(gen, rivals, demos, query) -> dict[str, Any]:
    reasons = list(gen.lesson_identifiable(demos, {"input": query["input"]}))
    ambiguous: list[str] = []
    survived_all: list[str] = []
    rival_errors: list[str] = []
    for name, rival in rivals.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if not fits:
                continue
            if rival(query["input"]) != query["output"]:
                ambiguous.append(name)
            else:
                survived_all.append(name)
        except Exception as exc:  # report contracts; never hide a rival crash
            rival_errors.append(f"{name}: {type(exc).__name__}: {exc}")
    return {
        "identifiable_hook_reasons": reasons,
        "ambiguous_rivals": sorted(ambiguous),
        "survived_all_rivals": sorted(survived_all),
        "rival_errors": sorted(rival_errors),
        "pass": not reasons and not ambiguous and not rival_errors,
    }


def audit(
    *,
    seeds: Iterable[int] = range(16),
    starts: Iterable[int] = range(8),
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    gen = _load_generator()
    rivals = _named_rivals(gen)
    seeds = list(seeds)
    starts = list(starts)
    bands = list(bands)
    n_demos = int(gen.EXAMPLES_NEEDED)

    production_failures: list[dict[str, Any]] = []
    rotation_failures: list[dict[str, Any]] = []
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    production_lessons = 0
    rotation_lessons = 0

    for band in bands:
        for seed in seeds:
            for start in starts:
                window = []
                for index in range(start, start + n_demos + 1):
                    grid = gen.generate(seed, index, difficulty=band)
                    unique_inputs.add(_grid_key(grid))
                    window.append({"input": grid, "output": gen.rule_mirror(grid)})

                # Documented policy: first N are demonstrations, final pair is query.
                production_lessons += 1
                production = _evaluate_lesson(gen, rivals, window[:n_demos], window[n_demos])
                if not production["pass"]:
                    production_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "demo_operations": [
                                gen.observe_overrides(pair["input"])["operation"]
                                for pair in window[:n_demos]
                            ],
                            "query_operation": gen.observe_overrides(window[n_demos]["input"])["operation"],
                            **production,
                        }
                    )

                # Stronger stress test: rotate each pair into the query position.
                for query_offset, query in enumerate(window):
                    rotation_lessons += 1
                    demos = [pair for offset, pair in enumerate(window) if offset != query_offset]
                    rotation = _evaluate_lesson(gen, rivals, demos, query)
                    if not rotation["pass"]:
                        rotation_failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_offset": query_offset,
                                "demo_operations": [
                                    gen.observe_overrides(pair["input"])["operation"] for pair in demos
                                ],
                                "query_operation": gen.observe_overrides(query["input"])["operation"],
                                **rotation,
                            }
                        )

    source_bytes = GENERATOR_PATH.read_bytes()
    return {
        "schema": "d8b498586958-lesson-window-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH),
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "assembly_policy": {
            "demonstrations": n_demos,
            "query": "immediately following generated pair",
            "index_window": "start..start+EXAMPLES_NEEDED",
        },
        "population": {"bands": bands, "seeds": seeds, "starts": starts},
        "declared_rivals": sorted(rivals),
        "unique_inputs": len(unique_inputs),
        "production_windows": {
            "lessons": production_lessons,
            "failures": len(production_failures),
            "status": "PASS" if not production_failures else "FAIL",
            "examples": production_failures[:20],
        },
        "arbitrary_query_rotations": {
            "lessons": rotation_lessons,
            "failures": len(rotation_failures),
            "status": "PASS" if not rotation_failures else "LIMITATION",
            "interpretation": (
                "This stress population is outside the documented production assembly policy. "
                "A rotation can withhold the only demonstration of one operation; a branch-local "
                "alias can then fit all remaining demonstrations and disagree on that query."
            ),
            "examples": rotation_failures[:20],
        },
        "status": "PASS" if not production_failures else "FAIL",
    }


def _parse_range(text: str) -> range:
    try:
        stop = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if stop <= 0:
        raise argparse.ArgumentTypeError("count must be positive")
    return range(stop)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-count", type=_parse_range, default=range(16))
    parser.add_argument("--start-count", type=_parse_range, default=range(8))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = audit(seeds=args.seed_count, starts=args.start_count)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
