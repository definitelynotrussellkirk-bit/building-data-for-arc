#!/usr/bin/env python3
"""Source-bound distribution and shortcut probe for d1bf9a8e4c69.

The probe deliberately imports the selected generator's declarations instead of
copying axis, rival, or shortcut names.  It is suitable for a quick post-edit
census and writes only deterministic JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "distribution_probe_generator_d1bf9a8e4c69", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row(task_id: str) -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(f"canonical task {task_id!r} not found")


def _stable_seed(label: str) -> int:
    return int(hashlib.sha256(label.encode()).hexdigest()[:12], 16)


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _json_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _canonical_shortcut_report(gen, pairs: list[dict[str, Any]]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in pairs]
        report[name] = {
            "canonical_pairs": len(pairs),
            "matching_pairs": sum(matches),
            "fits_all_canonical_pairs": bool(matches) and all(matches),
        }
    return report


def _generated_shortcut_counterexamples(gen) -> dict[str, Any]:
    examples: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        found = None
        for band in ("easy", "medium", "hard"):
            for sample_index in range(max(8, len(gen.SCHEDULE_PROFILES) * 2)):
                seed = _stable_seed(
                    f"shortcut-probe:v1:{gen.TASK_ID}:{name}:{band}:{sample_index}"
                )
                grid = gen.generate(seed, sample_index, difficulty=band)
                intended = gen.rule_mirror(grid)
                rival_output = rival(grid)
                if rival_output != intended:
                    found = {
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "observed_axes": gen.observe_overrides(grid),
                        "input": grid,
                        "intended_output": intended,
                        "rival_output": rival_output,
                        "input_passes_self_check": gen.self_check(grid) == [],
                    }
                    break
            if found is not None:
                break
        examples[name] = found
    return examples


def _sample_census(gen, samples_per_band: int) -> dict[str, Any]:
    axis_counts: dict[str, Counter[Any]] = {
        axis: Counter() for axis in gen.AXES
    }
    family_counts: Counter[str] = Counter()
    palette_counts: Counter[str] = Counter()
    shape_sizes: Counter[int] = Counter()
    shape_digests: set[str] = set()
    input_digests: set[str] = set()
    strict_hits: Counter[str] = Counter()
    validation_failures: list[dict[str, Any]] = []

    for band in ("easy", "medium", "hard"):
        for sample_index in range(samples_per_band):
            seed = _stable_seed(
                f"distribution-probe:v1:{gen.TASK_ID}:{band}:{sample_index}"
            )
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(grid)
            if errors:
                validation_failures.append(
                    {
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": errors,
                    }
                )
            observed = gen.observe_overrides(grid)
            for axis in gen.AXES:
                axis_counts[axis][observed.get(axis)] += 1
            family_counts[str(observed.get("shape_family"))] += 1
            palette_counts[str(observed.get("palette_pattern"))] += 1
            strict_hits[band] += int(gen.strict_canonical_like(grid) == [])
            input_digests.add(_grid_digest(grid))
            for _, cells in gen._components(grid):
                shape = gen._normalize(cells)
                shape_sizes[len(shape)] += 1
                shape_digests.add(
                    hashlib.sha256(repr(shape).encode()).hexdigest()
                )

    total = 3 * samples_per_band
    return {
        "seed_formula": "sha256('distribution-probe:v1:<task>:<band>:<index>')[:12]",
        "sample_indexes": [0, max(0, samples_per_band - 1)],
        "samples_per_band": samples_per_band,
        "total_samples": total,
        "unique_inputs": len(input_digests),
        "validation_failures": validation_failures,
        "axis_counts": {
            axis: _json_counter(counts) for axis, counts in axis_counts.items()
        },
        "observed_shape_family_counts": _json_counter(family_counts),
        "observed_palette_pattern_counts": _json_counter(palette_counts),
        "strict_canonical_like_hits_by_band": _json_counter(strict_hits),
        "unique_component_shapes": len(shape_digests),
        "component_size_counts": _json_counter(shape_sizes),
    }


def _lesson_windows(gen, starts_per_band: int) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    competitor_refutations: dict[str, Counter[str]] = {
        name: Counter() for name in gen.LESSON_COMPETITORS
    }
    total_windows = 0

    for band in ("easy", "medium", "hard"):
        for start in range(starts_per_band):
            seed = _stable_seed(
                f"lesson-probe:v1:{gen.TASK_ID}:{band}:{start}"
            )
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                seed, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            reasons = gen.lesson_identifiable(demos, query)
            total_windows += 1
            if reasons:
                failures.append(
                    {
                        "difficulty": band,
                        "seed": seed,
                        "start": start,
                        "reasons": reasons,
                    }
                )
            for name, rival in gen.LESSON_COMPETITORS.items():
                refuted = any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                )
                competitor_refutations[name][band] += int(refuted)

    return {
        "seed_formula": "sha256('lesson-probe:v1:<task>:<band>:<start>')[:12]",
        "examples_needed": gen.EXAMPLES_NEEDED,
        "schedule_period": len(gen.SCHEDULE_PROFILES),
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "starts_per_band": starts_per_band,
        "cyclic_start_remainders": sorted(
            {start % len(gen.SCHEDULE_PROFILES) for start in range(starts_per_band)}
        ),
        "total_windows": total_windows,
        "all_windows_identifiable": not failures,
        "failures": failures,
        "competitor_refuted_windows_by_band": {
            name: _json_counter(counts)
            for name, counts in competitor_refutations.items()
        },
    }


def _profile_floor(gen) -> dict[str, Any]:
    per_band: Counter[str] = Counter()
    profiles: Counter[str] = Counter()
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            seed = _stable_seed(f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}")
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            profiles[str(profile)] += 1
            if 8 <= profile[0] <= 9 and 9 <= profile[1] <= 11 and profile[2] == 3:
                per_band[band] += 1
    return {
        "seed_formula": "sha256('profile-floor:v1:<task>:<band>:<index>')[:12]",
        "sample_index_formula": "seed % 7919 + index",
        "samples_per_band": 20,
        "total_samples": 60,
        "hits_by_band": _json_counter(per_band),
        "total_hits": sum(per_band.values()),
        "required_total_hits": 15,
        "observed_profile_counts": _json_counter(profiles),
    }


def build_report(*, samples_per_band: int = 24, lesson_starts: int | None = None) -> dict[str, Any]:
    if samples_per_band <= 0:
        raise ValueError("samples_per_band must be positive")
    gen = _load_generator()
    if lesson_starts is None:
        lesson_starts = len(gen.SCHEDULE_PROFILES)
    if lesson_starts <= 0:
        raise ValueError("lesson_starts must be positive")

    canonical = _canonical_row(gen.TASK_ID)
    pairs = [*canonical.get("train", []), *canonical.get("test", [])]
    generator_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    return {
        "schema": "d1bf9a8e4c69-distribution-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": generator_hash,
        "rule_hash": gen.RULE_HASH,
        "declared_axes": gen.AXES,
        "sample_census": _sample_census(gen, samples_per_band),
        "canonical_shortcuts": _canonical_shortcut_report(gen, pairs),
        "generated_shortcut_counterexamples": _generated_shortcut_counterexamples(gen),
        "lesson_windows": _lesson_windows(gen, lesson_starts),
        "profile_floor": _profile_floor(gen),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=24)
    parser.add_argument(
        "--lesson-starts",
        type=int,
        default=None,
        help="lesson starts per difficulty (default: one full schedule period)",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    report = build_report(
        samples_per_band=args.samples_per_band,
        lesson_starts=args.lesson_starts,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
