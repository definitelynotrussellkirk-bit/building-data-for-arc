#!/usr/bin/env python3
"""Exhaustive cyclic lesson/rotation probe for task 8dbffe99308f.

Run from the repository through the packet wrapper, for example:

    python3 run_with_racket.py python3 \
      generators/8dbffe99308f/workspace/schedule_probe.py --cycles 2

The probe deliberately consumes the selected generator's own schedule,
``lesson_identifiable`` hook, witnesses, and declared competitors.  It is a
small complement to ``arcpuzzles lesson-census``: the census samples many
production lessons, while this script exhausts every start in the short cyclic
schedule for the requested seeds and rotates each of the four pairs into the
query position.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
from types import ModuleType
from typing import Iterable, Sequence


TASK_ID = "8dbffe99308f"
DEFAULT_BANDS = ("easy", "medium", "hard")
DEFAULT_SEEDS = (61_001, 61_002)


def _pair(generator: ModuleType, grid: list[list[int]]) -> dict[str, object]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def _source_sha256(generator: ModuleType) -> str:
    source = inspect.getsourcefile(generator)
    if not source:
        return ""
    return hashlib.sha256(Path(source).read_bytes()).hexdigest()


def probe_generator(
    generator: ModuleType,
    *,
    bands: Sequence[str] = DEFAULT_BANDS,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    cycles: int = 2,
) -> dict[str, object]:
    """Return exhaustive cyclic-start/query-rotation evidence.

    A lesson is four consecutive generated pairs: three demonstrations and one
    query.  Every pair is held out once.  Any nonempty result from the selected
    generator's ``lesson_identifiable`` hook is retained as an ambiguity or
    contract error rather than silently filtered.
    """
    if type(cycles) is not int or cycles < 1:
        raise ValueError("cycles must be a positive integer")
    if not bands:
        raise ValueError("at least one difficulty band is required")
    if not seeds:
        raise ValueError("at least one seed is required")

    period = len(generator.SCHEDULE_PROFILES)
    if period < 1:
        raise ValueError("generator schedule is empty")

    starts = range(period * cycles)
    checked_lessons = 0
    checked_rotations = 0
    minimum_conflicts: int | None = None
    ambiguous: list[dict[str, object]] = []
    profile_windows: set[tuple[str, ...]] = set()

    conflict_predicate = generator.SEMANTIC_WITNESSES.get("unequal_conflict")
    if conflict_predicate is None:
        raise ValueError("generator has no unequal_conflict witness")

    for band in bands:
        for seed in seeds:
            for start in starts:
                grids = [
                    generator.generate(seed, start + offset, difficulty=band)
                    for offset in range(4)
                ]
                pairs = [_pair(generator, grid) for grid in grids]
                profiles = tuple(
                    generator.schedule_profile(seed, start + offset, band)
                    for offset in range(4)
                )
                profile_windows.add(profiles)

                conflict_count = sum(bool(conflict_predicate(grid)) for grid in grids)
                minimum_conflicts = (
                    conflict_count
                    if minimum_conflicts is None
                    else min(minimum_conflicts, conflict_count)
                )
                checked_lessons += 1

                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    reasons = generator.lesson_identifiable(demos, query)
                    checked_rotations += 1
                    if reasons:
                        ambiguous.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "profiles": list(profiles),
                                "conflicts_in_four_pairs": conflict_count,
                                "reasons": list(reasons),
                            }
                        )

    return {
        "task_id": getattr(generator, "TASK_ID", TASK_ID),
        "generator_version": getattr(generator, "VERSION", None),
        "generator_sha256": _source_sha256(generator),
        "bands": list(bands),
        "seeds": list(seeds),
        "cycles": cycles,
        "schedule_period": period,
        "declared_competitors": sorted(generator.LESSON_COMPETITORS),
        "checked_lessons": checked_lessons,
        "checked_rotations": checked_rotations,
        "unique_profile_windows": len(profile_windows),
        "minimum_conflicts_per_lesson": minimum_conflicts,
        "ambiguous_rotation_count": len(ambiguous),
        "ambiguous_rotations": ambiguous,
        "status": "pass" if not ambiguous else "ambiguous",
        "scope_note": (
            "Exhaustive over cyclic starts for the requested seeds/bands and "
            "declared competitors only; this is not a proof against undeclared rules."
        ),
    }


def _load_selected_generator() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"workspace_probe_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_ints(values: Iterable[str]) -> tuple[int, ...]:
    result = tuple(int(value) for value in values)
    if not result:
        raise argparse.ArgumentTypeError("at least one integer is required")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument(
        "--bands",
        nargs="+",
        default=list(DEFAULT_BANDS),
        choices=DEFAULT_BANDS,
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        default=[str(value) for value in DEFAULT_SEEDS],
        metavar="N",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = probe_generator(
        _load_selected_generator(),
        bands=tuple(args.bands),
        seeds=_parse_ints(args.seeds),
        cycles=args.cycles,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
