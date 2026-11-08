#!/usr/bin/env python3
"""Adversarial curriculum audit for generator 983d0ea3bd17.

This tool checks properties that broad distribution gates cannot infer:

* every declared canonical shortcut really fits every public pair;
* every sliding three-demo window refutes every named lesson competitor;
* the scheduled probe contains two independently observable blocker colors;
* the generator's own lesson-identifiability hook agrees with materialization.

It is intentionally task-local.  Future reviewers can add a rival function to
``generator.py`` and immediately measure whether any curriculum window lets it
survive.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

THIS_FILE = Path(__file__).resolve()
TASK_ROOT = THIS_FILE.parents[1]
REPO_ROOT = THIS_FILE.parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
GENERATOR_PATH = TASK_ROOT / "generator.py"

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "deep_audit_target_983d0ea3bd17",
        GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _normalise_grid(raw: Any) -> list[list[int]]:
    if isinstance(raw, list) and raw and isinstance(raw[0], str):
        return [[int(character) for character in row] for row in raw]
    return copy.deepcopy(raw)


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != GEN.TASK_ID:
                continue
            raw_pairs = list(row["train"])
            raw_test = row["test"]
            raw_pairs.extend(raw_test if isinstance(raw_test, list) else [raw_test])
            return [
                {
                    "input": _normalise_grid(pair["input"]),
                    "output": _normalise_grid(pair["output"]),
                }
                for pair in raw_pairs
            ]
    raise RuntimeError(f"canonical task {GEN.TASK_ID} not found in {CANONICAL_PATH}")


def _blocker_entries(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, GEN.SOURCE_COLOR)
    ]


def _survivors(demos: Sequence[dict[str, Any]]) -> list[str]:
    return sorted(
        name
        for name, competitor in GEN.LESSON_COMPETITORS.items()
        if all(competitor(pair["input"]) == pair["output"] for pair in demos)
    )


def _probe_failures(grid: list[list[int]]) -> list[str]:
    failures = list(GEN.self_check(grid))
    blockers = _blocker_entries(grid)
    sources = GEN._positions(grid, GEN.SOURCE_COLOR)
    h = len(grid)
    w = len(grid[0])

    if len(blockers) != 2:
        failures.append(f"expected two blockers, found {len(blockers)}")
        return failures

    colors = {value for _, _, value in blockers}
    if len(colors) != 2:
        failures.append(f"blocker colors are not distinct: {sorted(colors)}")
    if GEN.ANCHOR_BLOCKER_COLOR not in colors:
        failures.append(
            f"anchor blocker color {GEN.ANCHOR_BLOCKER_COLOR} is absent"
        )
    if not any(
        row in (0, h - 1) or col in (0, w - 1)
        for row, col in sources
    ):
        failures.append("probe has no edge source")
    if not GEN._sources_have_shared_axis(sources):
        failures.append("probe has no axis-aligned source pair")

    for row, col, _ in blockers:
        if not GEN._blocker_is_observable(grid, (row, col)):
            failures.append(f"blocker {(row, col)} is not independently observable")

    for name in sorted(GEN.CANONICAL_SHORTCUTS):
        if GEN.SEMANTIC_RIVALS[name](grid) == GEN.rule_mirror(grid):
            failures.append(f"canonical shortcut {name!r} survives the probe")
    return failures


def run_audit(
    *,
    bands: Iterable[str] = ("easy", "medium", "hard"),
    seeds: Iterable[int] = (1, 91, 20260929),
    starts: Iterable[int] = range(24),
) -> dict[str, Any]:
    bands_tuple = tuple(str(value) for value in bands)
    seeds_tuple = tuple(int(value) for value in seeds)
    starts_tuple = tuple(int(value) for value in starts)
    if not bands_tuple or not seeds_tuple or not starts_tuple:
        raise ValueError("bands, seeds, and starts must each be nonempty")

    canonical = _canonical_pairs()
    shortcut_rows: dict[str, dict[str, Any]] = {}
    all_shortcuts_fit = True
    for name, shortcut in sorted(GEN.CANONICAL_SHORTCUTS.items()):
        fits = [shortcut(pair["input"]) == pair["output"] for pair in canonical]
        shortcut_rows[name] = {
            "fit_count": sum(fits),
            "canonical_pairs": len(fits),
            "fits_all": all(fits),
        }
        all_shortcuts_fit = all_shortcuts_fit and all(fits)

    survivor_counts: Counter[str] = Counter()
    survivor_examples: list[dict[str, Any]] = []
    identifiability_failures: list[dict[str, Any]] = []
    probe_failures: list[dict[str, Any]] = []
    windows_checked = 0
    probes_checked = 0

    for band in bands_tuple:
        for seed in seeds_tuple:
            for start in starts_tuple:
                demos: list[dict[str, Any]] = []
                blocked_grids: list[list[list[int]]] = []
                profiles: list[str] = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    grid = GEN.generate(seed, sample_index, difficulty=band)
                    output = GEN.rule_mirror(grid)
                    demos.append({"input": grid, "output": output})
                    profile = GEN.schedule_profile(seed, sample_index, band)
                    profiles.append(profile)
                    if GEN.observe_overrides(grid)["scene_kind"] == "blocked":
                        blocked_grids.append(grid)

                windows_checked += 1
                survivors = _survivors(demos)
                for name in survivors:
                    survivor_counts[name] += 1
                if survivors and len(survivor_examples) < 12:
                    survivor_examples.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "profiles": profiles,
                            "survivors": survivors,
                        }
                    )

                query_index = start + GEN.EXAMPLES_NEEDED
                query_grid = GEN.generate(seed, query_index, difficulty=band)
                query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
                reasons = GEN.lesson_identifiable(demos, query)
                if reasons and len(identifiability_failures) < 12:
                    identifiability_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

                if len(blocked_grids) != 1:
                    probe_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "failures": [
                                "expected exactly one blocked probe in the window; "
                                f"found {len(blocked_grids)}"
                            ],
                        }
                    )
                    continue

                probes_checked += 1
                failures = _probe_failures(blocked_grids[0])
                if failures:
                    probe_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "failures": failures,
                        }
                    )

    passed = (
        all_shortcuts_fit
        and not survivor_counts
        and not identifiability_failures
        and not probe_failures
    )
    return {
        "task_id": GEN.TASK_ID,
        "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "passed": passed,
        "config": {
            "bands": list(bands_tuple),
            "seeds": list(seeds_tuple),
            "starts": list(starts_tuple),
        },
        "canonical_shortcuts": {
            "canonical_pairs": len(canonical),
            "all_fit_all_canonical": all_shortcuts_fit,
            "results": shortcut_rows,
        },
        "lesson_windows": {
            "windows_checked": windows_checked,
            "competitors_checked": sorted(GEN.LESSON_COMPETITORS),
            "survivor_counts": dict(sorted(survivor_counts.items())),
            "survivor_examples": survivor_examples,
            "identifiability_failures": identifiability_failures,
        },
        "blocker_probes": {
            "probes_checked": probes_checked,
            "failures": probe_failures,
        },
    }


def _parse_starts(raw: str) -> tuple[int, ...]:
    values: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" in chunk:
            left, right = chunk.split(":", 1)
            start = int(left) if left else 0
            stop = int(right)
            values.extend(range(start, stop))
        else:
            values.append(int(chunk))
    if not values:
        raise argparse.ArgumentTypeError("starts must contain an integer or range")
    return tuple(values)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bands",
        nargs="+",
        default=["easy", "medium", "hard"],
        choices=["easy", "medium", "hard"],
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 91, 20260929])
    parser.add_argument(
        "--starts",
        default="0:24",
        help="comma-separated integers and half-open ranges, e.g. 0:24,31",
    )
    parser.add_argument("--out", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_audit(
        bands=args.bands,
        seeds=args.seeds,
        starts=_parse_starts(args.starts),
    )
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
