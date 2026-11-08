#!/usr/bin/env python3
"""Independent probes for the 7b0cb3b9a618 crossing-band curriculum.

This file intentionally does not import production helpers for the rule,
profile, or orientation observations.  It can load an arbitrary candidate
``generator.py`` and verify canonical outputs, generated structure, declared
rivals, and all 12 cyclic lesson starts.  Future reviewers can run it directly:

    PYTHONPATH=../../shared/runtime python3 reference_probe.py --samples 120

Pass ``GENERATOR_UNDER_TEST=/path/to/generator.py`` to bind a staged or patched
candidate instead of ``../generator.py``.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any


TASK_ID = "7b0cb3b9a618"
HOME = Path(__file__).resolve().parents[1]

_PROFILE_BY_SHAPE = {
    (3, 3): "tiny_3x3_c3",
    (8, 12): "h8_w12_c5",
    (9, 11): "h9_w11_c5",
    (11, 11): "h11_w11_c6",
    (11, 12): "h11_w12_c6",
    (11, 13): "h11_w13_c5",
}
CANONICAL_PROFILES = tuple(_PROFILE_BY_SHAPE.values())
SCHEDULE_PROFILES = tuple(
    f"{name}:{orientation}"
    for name in CANONICAL_PROFILES
    for orientation in ("horizontal", "vertical")
)


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    source = source.resolve()
    spec = importlib.util.spec_from_file_location(
        f"probe_candidate_{hashlib.sha256(source.read_bytes()).hexdigest()[:12]}",
        source,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rectangular(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal integers 0..9")
    return len(grid), width


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python spelling of the visible clean-row/anomaly rule."""
    _, width = _rectangular(grid)
    for row in grid:
        first = row[0]
        if first != 0 and all(value == first for value in row):
            return [[first]]
    for row in grid:
        first = row[0]
        if first == 0:
            continue
        differences = [value for value in row if value != first]
        if len(differences) == 1:
            return [[differences[0]]]
    raise ValueError("no clean row or one-anomaly dirty row")


def observe(grid: list[list[int]]) -> dict[str, Any]:
    """Recover the profile, winner orientation, and answer from pixels only."""
    height, width = _rectangular(grid)
    profile = _PROFILE_BY_SHAPE.get((height, width))
    if profile is None:
        raise ValueError(f"noncanonical shape {height}x{width}")

    clean_rows = [
        (index, row[0])
        for index, row in enumerate(grid)
        if row[0] != 0 and len(set(row)) == 1
    ]
    clean_cols = []
    for col in range(width):
        values = [grid[row][col] for row in range(height)]
        if values[0] != 0 and len(set(values)) == 1:
            clean_cols.append((col, values[0]))

    if clean_rows:
        colors = {color for _, color in clean_rows}
        if len(colors) != 1:
            raise ValueError("multiple clean-row colors")
        orientation = "horizontal"
        answer = clean_rows[0][1]
    else:
        if len(clean_cols) != 1:
            raise ValueError(f"expected one clean column; found {len(clean_cols)}")
        orientation = "vertical"
        answer = clean_cols[0][1]

    expected = rule_output(grid)[0][0]
    if answer != expected:
        raise ValueError(f"orientation observation {answer} disagrees with rule {expected}")
    return {
        "profile": profile,
        "orientation": orientation,
        "schedule_profile": f"{profile}:{orientation}",
        "answer": answer,
        "shape": [height, width],
        "palette_size": len({value for row in grid for value in row}),
    }


def probe_cyclic_lessons(*, seed: int = 190807, difficulty: str = "medium", generator_path=None) -> dict[str, Any]:
    """Exhaust every start and query rotation in the 12-slot schedule.

    Labels come from :func:`rule_output`; rivals are taken dynamically from the
    candidate's declarations so this probe cannot go stale when names change.
    """
    generator = load_generator(generator_path)
    rivals = dict(getattr(generator, "LESSON_COMPETITORS", {}) or {})
    starts = len(SCHEDULE_PROFILES)
    ambiguities: list[dict[str, Any]] = []
    profile_counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    rotations = 0

    for start in range(starts):
        pairs = []
        for offset in range(4):
            sample_index = start + offset
            grid = generator.generate(seed + start, sample_index, difficulty=difficulty)
            errors = generator.self_check(grid)
            if errors:
                raise AssertionError(f"start {start} offset {offset}: {errors}")
            observation = observe(grid)
            profile_counts[observation["schedule_profile"]] += 1
            unique_inputs.add(
                hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            )
            pairs.append({"input": grid, "output": rule_output(grid)})

        for query_index, query in enumerate(pairs):
            rotations += 1
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            for name, rival in sorted(rivals.items()):
                fits = all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
                changes_query = rival(deepcopy(query["input"])) != query["output"]
                if fits and changes_query:
                    ambiguities.append(
                        {
                            "start": start,
                            "query_index": query_index,
                            "rival": name,
                            "query": query,
                        }
                    )

    return {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(Path(generator.__file__).read_bytes()).hexdigest(),
        "starts": starts,
        "rotations": rotations,
        "rivals": sorted(rivals),
        "ambiguities": ambiguities,
        "profiles_seen": sorted(profile_counts),
        "profile_counts": dict(sorted(profile_counts.items())),
        "unique_inputs": len(unique_inputs),
    }


def probe_distribution(*, samples: int = 120, seed: int = 190807, generator_path=None) -> dict[str, Any]:
    generator = load_generator(generator_path)
    per_band = {}
    for band in ("easy", "medium", "hard"):
        profiles: Counter[str] = Counter()
        answers: Counter[int] = Counter()
        unique: set[str] = set()
        failures = []
        for index in range(samples):
            grid = generator.generate(seed + index, index, difficulty=band)
            errors = generator.self_check(grid)
            if errors:
                failures.append({"index": index, "errors": errors})
                continue
            observation = observe(grid)
            profiles[observation["schedule_profile"]] += 1
            answers[observation["answer"]] += 1
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        per_band[band] = {
            "draws": samples,
            "failures": failures,
            "unique_inputs": len(unique),
            "profiles": dict(sorted(profiles.items())),
            "answers": dict(sorted(answers.items())),
        }
    return {
        "task_id": TASK_ID,
        "samples_per_band": samples,
        "per_band": per_band,
        "cyclic_lessons": probe_cyclic_lessons(seed=seed, generator_path=generator_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=120)
    parser.add_argument("--seed", type=int, default=190807)
    parser.add_argument("--generator")
    parser.add_argument("--out")
    args = parser.parse_args()
    report = probe_distribution(samples=args.samples, seed=args.seed, generator_path=args.generator)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    failures = sum(len(row["failures"]) for row in report["per_band"].values())
    ambiguities = len(report["cyclic_lessons"]["ambiguities"])
    return 1 if failures or ambiguities else 0


if __name__ == "__main__":
    raise SystemExit(main())
