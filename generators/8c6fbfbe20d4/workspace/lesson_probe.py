#!/usr/bin/env python3
"""Probe complete generated lessons against every declared shortcut rival.

Run this from a prepared portable runtime so both ``puzzle_generators`` and
``scripts.generator_semantic_gate`` are importable.  ``mirror`` mode is a fast
schedule regression.  ``racket`` mode materializes outputs through the
canonical Racket rule using the semantic gate's production runner.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ID = "8c6fbfbe20d4"
_GENERATOR_MODULE = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"


def _load_contract():
    try:
        generator = importlib.import_module(_GENERATOR_MODULE)
        gate = importlib.import_module("scripts.generator_semantic_gate")
    except ModuleNotFoundError as exc:  # pragma: no cover - CLI guidance
        raise SystemExit(
            "lesson_probe.py must run with a prepared portable runtime on "
            "PYTHONPATH; see workspace/README.md"
        ) from exc
    return generator, gate


def _pair(generator, seed: int, sample_index: int, axes: dict[str, Any]) -> dict:
    grid = generator.generate(seed, sample_index, **axes)
    return {"input": grid, "output": generator.rule_mirror(grid)}


def _mirror_lessons(generator, gate, lessons_per_band: int) -> tuple[list[dict], list[str]]:
    bands = tuple(gate.BANDS)
    count = lessons_per_band * len(bands)
    plan = gate._lesson_plan(
        TASK_ID,
        count,
        bands=bands,
        pass_difficulty=True,
        legacy=False,
    )
    lessons: list[dict] = []
    for index, (band, seed, sample_index, axes) in enumerate(plan):
        demos = [
            _pair(generator, seed, sample_index + offset, axes)
            for offset in range(generator.EXAMPLES_NEEDED)
        ]
        query = _pair(
            generator,
            seed,
            sample_index + generator.EXAMPLES_NEEDED,
            axes,
        )
        lessons.append(
            {
                "index": index,
                "band": band,
                "seed": seed,
                "sample_index": sample_index,
                "replay": (
                    f"band={band} seed={seed} sample_index={sample_index}"
                ),
                "demos": demos,
                "query": query,
            }
        )
    return lessons, []


def _racket_lessons(generator, gate, lessons_per_band: int) -> tuple[list[dict], list[str]]:
    count = lessons_per_band * len(tuple(gate.BANDS))
    return gate.materialize_lessons(
        TASK_ID,
        count,
        n_demos=generator.EXAMPLES_NEEDED,
        n_queries=1,
        bands=tuple(gate.BANDS),
        pass_difficulty=True,
        legacy=False,
    )


def _input_digest(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def run_probe(
    *,
    lessons_per_band: int = 100,
    mode: str = "mirror",
    max_examples: int = 8,
) -> dict[str, Any]:
    """Return a machine-readable shortcut-survival census.

    A passing report means every declared competitor is falsified by every
    complete demonstration set in the pinned per-band sample, and the task's
    ``lesson_identifiable`` hook agrees.
    """
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    if mode not in {"mirror", "racket"}:
        raise ValueError("mode must be 'mirror' or 'racket'")

    generator, gate = _load_contract()
    competitors = dict(generator.LESSON_COMPETITORS)
    bands = tuple(gate.BANDS)
    materializer = _mirror_lessons if mode == "mirror" else _racket_lessons
    lessons, materialization_errors = materializer(
        generator, gate, lessons_per_band
    )

    requested_per_band = {band: lessons_per_band for band in bands}
    per_band: dict[str, dict[str, Any]] = {
        band: {
            "requested": lessons_per_band,
            "materialized": 0,
            "unidentifiable": 0,
            "competitor_survivor_counts": {name: 0 for name in competitors},
        }
        for band in bands
    }
    survivor_counts = {name: 0 for name in competitors}
    survived_all_counts = {name: 0 for name in competitors}
    survivor_examples: list[dict[str, Any]] = []
    hook_errors: list[str] = []
    hook_reason_examples: list[dict[str, Any]] = []
    unidentifiable = 0
    unique_inputs: set[str] = set()

    for lesson in lessons:
        band = str(lesson.get("band", "unknown"))
        band_row = per_band.setdefault(
            band,
            {
                "requested": 0,
                "materialized": 0,
                "unidentifiable": 0,
                "competitor_survivor_counts": {
                    name: 0 for name in competitors
                },
            },
        )
        band_row["materialized"] += 1
        for pair in [*lesson["demos"], lesson["query"]]:
            unique_inputs.add(_input_digest(pair["input"]))

        scored = gate.evaluate_competitors(competitors, lesson)
        for name in scored["survived_demos"]:
            survivor_counts[name] += 1
            band_row["competitor_survivor_counts"][name] += 1
        for name in scored["survived_all"]:
            survived_all_counts[name] += 1
        if scored["errors"]:
            hook_errors.extend(scored["errors"])
        if scored["survived_demos"] and len(survivor_examples) < max_examples:
            survivor_examples.append(
                {
                    "replay": lesson.get("replay"),
                    "survived_demos": scored["survived_demos"],
                    "survived_all": scored["survived_all"],
                    "query_discriminates": scored["query_discriminates"],
                }
            )

        try:
            reasons = generator.lesson_identifiable(
                copy.deepcopy(lesson["demos"]),
                copy.deepcopy(lesson["query"]),
            )
        except Exception as exc:  # pragma: no cover - defensive report path
            hook_errors.append(
                f"{lesson.get('replay')}: {type(exc).__name__}: {exc}"
            )
            continue
        if not isinstance(reasons, list):
            hook_errors.append(
                f"{lesson.get('replay')}: lesson_identifiable returned "
                f"{type(reasons).__name__}, expected list"
            )
            continue
        if reasons:
            unidentifiable += 1
            band_row["unidentifiable"] += 1
            if len(hook_reason_examples) < max_examples:
                hook_reason_examples.append(
                    {
                        "replay": lesson.get("replay"),
                        "reasons": reasons[:8],
                    }
                )

    generator_path = Path(generator.__file__).resolve()
    generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    expected_total = lessons_per_band * len(bands)
    survivor_total = sum(survivor_counts.values())
    status = "pass"
    if (
        materialization_errors
        or hook_errors
        or unidentifiable
        or survivor_total
        or len(lessons) != expected_total
    ):
        status = "fail"

    return {
        "status": status,
        "task_id": TASK_ID,
        "generator_version": getattr(generator, "VERSION", None),
        "generator_sha256": generator_sha256,
        "rule_hash": getattr(generator, "RULE_HASH", None),
        "mode": mode,
        "oracle": (
            "generator.rule_mirror"
            if mode == "mirror"
            else "canonical Racket rule through generator_semantic_gate"
        ),
        "sample_policy": {
            "planner": "generator_semantic_gate._lesson_plan",
            "bands": list(bands),
            "sample_stride": gate.LESSON_SAMPLE_STRIDE,
            "examples_needed": generator.EXAMPLES_NEEDED,
            "query_count": 1,
        },
        "requested_per_band": requested_per_band,
        "expected_lessons": expected_total,
        "materialized_lessons": len(lessons),
        "unique_inputs": len(unique_inputs),
        "competitors": sorted(competitors),
        "competitor_survivor_counts": survivor_counts,
        "competitor_survived_all_counts": survived_all_counts,
        "unidentifiable_lessons": unidentifiable,
        "per_band": per_band,
        "materialization_errors": list(materialization_errors),
        "hook_errors": hook_errors[:max_examples],
        "hook_reason_examples": hook_reason_examples,
        "survivor_examples": survivor_examples,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--mode", choices=("mirror", "racket"), default="mirror")
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = run_probe(
        lessons_per_band=args.lessons_per_band,
        mode=args.mode,
        max_examples=args.max_examples,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"{report['status'].upper()} {report['task_id']} "
        f"mode={report['mode']} lessons={report['materialized_lessons']}/"
        f"{report['expected_lessons']} unique_inputs={report['unique_inputs']} "
        f"survivors={sum(report['competitor_survivor_counts'].values())}"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
