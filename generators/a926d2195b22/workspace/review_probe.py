#!/usr/bin/env python3
"""Portable exact-axis and semantic-lesson probe for a926d2195b22."""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import itertools
import json
from pathlib import Path
import sys


TASK_ID = "a926d2195b22"
HERE = Path(__file__).resolve()
HOME = HERE.parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(failures, scope, exc=None, **details):
    row = {"scope": scope, **details}
    if exc is not None:
        row["error"] = f"{type(exc).__name__}: {exc}"
    failures.append(row)


def run(seeds_per_case: int, lesson_starts: int):
    gen = _load_generator()
    failures = []

    pairs = canonical_pairs(TASK_ID, root=find_root(HERE), labeled_only=True)
    for pair in pairs:
        identity = f"{pair['split']}{pair['pair_index']}"
        try:
            reasons = gen.self_check(pair["input"])
            if reasons:
                _record(failures, "canonical", identity=identity, reasons=reasons)
            if gen.rule_mirror(pair["input"]) != pair["output"]:
                _record(failures, "canonical", identity=identity, mismatch="rule_mirror")
            if gen.CANONICAL_SHORTCUTS["rarest_color"](pair["input"]) != pair["output"]:
                _record(failures, "canonical", identity=identity, mismatch="rarest_color")
        except Exception as exc:  # probe records all cases rather than aborting early
            _record(failures, "canonical", exc=exc, identity=identity)

    override_cases = 0
    bands = (None, "easy", "medium", "hard")
    domains = ([8, 13], [8, 14], [3, 5], [1, 3], [1, 2])
    for band, values in itertools.product(bands, itertools.product(*domains)):
        override_cases += 1
        options = dict(
            zip(
                ("grid_h", "grid_w", "num_objects", "smallest_size", "minimum_count"),
                values,
            )
        )
        for seed_offset in range(seeds_per_case):
            try:
                grid = gen.generate(1701 + seed_offset, 29, difficulty=band, **options)
                reasons = gen.self_check(
                    grid, difficulty=band, meta={"overrides": options}
                )
                observed = gen.observe_overrides(grid)
                if reasons or observed != options:
                    _record(
                        failures,
                        "override",
                        band=band,
                        options=options,
                        seed_offset=seed_offset,
                        reasons=reasons,
                        observed=observed,
                    )
            except Exception as exc:
                _record(
                    failures,
                    "override",
                    exc=exc,
                    band=band,
                    options=options,
                    seed_offset=seed_offset,
                )

    lesson_queries = 0
    for band in bands:
        for start in range(lesson_starts):
            try:
                lessons = []
                for offset in range(4):
                    grid = gen.generate(6001 + start, start * 4 + offset, difficulty=band)
                    lessons.append(
                        {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}
                    )
                for query_index in range(4):
                    lesson_queries += 1
                    query = lessons[query_index]
                    demos = [pair for index, pair in enumerate(lessons) if index != query_index]
                    reasons = gen.lesson_identifiable(demos, query)
                    if reasons:
                        _record(
                            failures,
                            "lesson",
                            band=band,
                            start=start,
                            query_index=query_index,
                            reasons=reasons,
                        )
            except Exception as exc:
                _record(failures, "lesson", exc=exc, band=band, start=start)

    return {
        "schema": "a926d2195b22-review-probe-v1",
        "status": "pass" if not failures else "fail",
        "summary": {
            "canonical_pairs": len(pairs),
            "competitors": len(gen.LESSON_COMPETITORS),
            "lesson_queries": lesson_queries,
            "override_cases": override_cases,
        },
        "failures": failures,
        "limitations": [
            "Python mirrors are diagnostic; the selected canonical Racket program remains label authority.",
            f"Lesson identifiability is checked only against the {len(gen.LESSON_COMPETITORS)} declared executable rivals.",
            "Boundary override coverage does not enumerate every interior integer value.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-case", type=int, default=2)
    parser.add_argument("--lesson-starts", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds_per_case < 1 or args.lesson_starts < 1:
        parser.error("counts must be positive")
    payload = run(args.seeds_per_case, args.lesson_starts)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
