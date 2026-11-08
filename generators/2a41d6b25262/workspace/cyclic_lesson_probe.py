#!/usr/bin/env python3
"""Replayable cyclic-query lesson probe for task 2a41d6b25262.

The shared lesson census scores the production train/query orientation.  This
companion takes each deterministic five-pair lesson and rotates every pair into
the query position, checking dynamically declared LESSON_COMPETITORS against
the remaining four demonstrations.  It records replay seeds and input hashes
without embedding large grids in the report.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


def _bootstrap_packet_runtime() -> None:
    """Make direct/subprocess execution work in source and portable snapshots."""
    roots = []
    configured = os.environ.get("ARCPUZZLES_HOME")
    if configured:
        roots.append(Path(configured).resolve())
    roots.append(Path(__file__).resolve().parents[3])
    for root in roots:
        for candidate in (root / "src", root / "shared" / "runtime"):
            if candidate.is_dir() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))


_bootstrap_packet_runtime()

from reference_probe import TASK_ID, canonical_pairs, load_generator, reference_output

BANDS = ("easy", "medium", "hard")
SEED_RECIPE = "sha256('cyclic-lesson:v1:TASK:BAND:INDEX')[:8] as uint32"


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _seed(task_id: str, band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"cyclic-lesson:v1:{task_id}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:8], 16)


def _same_grid(left: Any, right: Any) -> bool:
    return left == right


def build_report(generator_path: Path, per_band: int) -> dict[str, Any]:
    if per_band < 1:
        raise ValueError("per_band must be positive")
    gen = load_generator(generator_path)
    competitors = getattr(gen, "LESSON_COMPETITORS", {})
    if not isinstance(competitors, dict) or any(
        not isinstance(name, str) or not callable(fn)
        for name, fn in competitors.items()
    ):
        raise TypeError("LESSON_COMPETITORS must be dict[str, callable]")
    if not competitors:
        raise ValueError("LESSON_COMPETITORS is empty; no identifiability probe exists")

    demo_count = getattr(gen, "EXAMPLES_NEEDED", 4)
    if type(demo_count) is not int or demo_count < 1:
        raise ValueError("EXAMPLES_NEEDED must be a positive integer")
    pair_count = demo_count + 1

    counts = {
        "bands": len(BANDS),
        "lessons": 0,
        "pairs": 0,
        "rotations": 0,
        "ambiguous_rotations": 0,
        "errors": 0,
    }
    lessons: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()

    for band in BANDS:
        for lesson_index in range(per_band):
            seed = _seed(TASK_ID, band, lesson_index)
            row: dict[str, Any] = {
                "band": band,
                "lesson_index": lesson_index,
                "seed": seed,
                "sample_indices": [],
                "profiles": [],
                "input_sha256": [],
                "ambiguous_rotations": [],
            }
            pairs = []
            try:
                for offset in range(pair_count):
                    sample_index = lesson_index + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    validation = gen.self_check(grid)
                    if validation:
                        raise ValueError(
                            f"self_check rejected sample_index={sample_index}: {validation}"
                        )
                    output = reference_output(grid)
                    pair = {"input": grid, "output": output}
                    pairs.append(pair)
                    input_hash = _json_digest(grid)
                    unique_inputs.add(input_hash)
                    row["sample_indices"].append(sample_index)
                    row["profiles"].append(
                        gen.schedule_profile(seed, sample_index, difficulty=band)
                    )
                    row["input_sha256"].append(input_hash)
                counts["lessons"] += 1
                counts["pairs"] += len(pairs)
            except Exception as exc:  # evidence path, not silent recovery
                counts["errors"] += 1
                error = {
                    "band": band,
                    "lesson_index": lesson_index,
                    "seed": seed,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                row["error"] = error["error"]
                errors.append(error)
                lessons.append(row)
                continue

            for query_index, query in enumerate(pairs):
                counts["rotations"] += 1
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                survivors: list[dict[str, Any]] = []
                rotation_errors: list[str] = []
                for name, rival in sorted(competitors.items()):
                    try:
                        fits_demos = all(
                            _same_grid(rival(deepcopy(demo["input"])), demo["output"])
                            for demo in demos
                        )
                        if fits_demos:
                            survivors.append(
                                {
                                    "name": name,
                                    "agrees_with_query": _same_grid(
                                        rival(deepcopy(query["input"])), query["output"]
                                    ),
                                }
                            )
                    except Exception as exc:
                        rotation_errors.append(
                            f"{name}: {type(exc).__name__}: {exc}"
                        )
                hook_reasons: list[str] = []
                hook = getattr(gen, "lesson_identifiable", None)
                if callable(hook):
                    try:
                        hook_reasons = list(hook(deepcopy(demos), deepcopy(query)))
                    except Exception as exc:
                        rotation_errors.append(
                            f"lesson_identifiable: {type(exc).__name__}: {exc}"
                        )
                if rotation_errors:
                    counts["errors"] += 1
                    errors.append(
                        {
                            "band": band,
                            "lesson_index": lesson_index,
                            "query_index": query_index,
                            "errors": rotation_errors,
                        }
                    )
                if survivors or hook_reasons:
                    counts["ambiguous_rotations"] += 1
                    row["ambiguous_rotations"].append(
                        {
                            "query_index": query_index,
                            "query_sample_index": row["sample_indices"][query_index],
                            "survivors": survivors,
                            "hook_reasons": hook_reasons,
                            "errors": rotation_errors,
                        }
                    )
            lessons.append(row)

    canonical_fit: dict[str, Any] = {}
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    for name, shortcut in sorted(shortcuts.items()):
        fits = 0
        shortcut_errors = []
        pairs = canonical_pairs()
        for pair_index, pair in enumerate(pairs):
            try:
                fits += int(
                    _same_grid(shortcut(deepcopy(pair["input"])), pair["output"])
                )
            except Exception as exc:
                shortcut_errors.append(
                    {"pair_index": pair_index, "error": f"{type(exc).__name__}: {exc}"}
                )
        canonical_fit[name] = {
            "pairs": len(pairs),
            "fits": fits,
            "errors": shortcut_errors,
            "status": (
                "error"
                if shortcut_errors
                else "fits_all"
                if fits == len(pairs)
                else "refuted"
            ),
        }

    status = (
        "error"
        if counts["errors"]
        else "ambiguous"
        if counts["ambiguous_rotations"]
        else "pass"
    )
    return {
        "schema": "arcpuzzles-cyclic-lesson-probe-v1",
        "status": status,
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seed_recipe": SEED_RECIPE,
        "sampler": {
            "bands": list(BANDS),
            "per_band": per_band,
            "demo_count": demo_count,
            "query_rotations_per_lesson": pair_count,
            "sample_index_recipe": "lesson_index + offset",
            "oracle": "independent reference_probe.reference_output",
        },
        "competitors": sorted(competitors),
        "canonical_shortcut_fit": canonical_fit,
        "counts": counts,
        "unique_inputs": len(unique_inputs),
        "errors": errors,
        "lessons": lessons,
        "limits": [
            "Finite declared-rival check, not proof of universal identifiability.",
            "Outputs use the independent Python task statement; Racket parity is checked separately.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args.generator.resolve(), args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"status={report['status']} lessons={report['counts']['lessons']} "
        f"rotations={report['counts']['rotations']} "
        f"ambiguous={report['counts']['ambiguous_rotations']} "
        f"errors={report['counts']['errors']}"
    )
    return 2 if report["status"] == "error" else 1 if report["status"] == "ambiguous" else 0


if __name__ == "__main__":
    raise SystemExit(main())
