#!/usr/bin/env python3
"""Independent semantic and exact-control probe for generator ffa91bb651d1.

The probe deliberately reimplements the row rule and all three plausible
canonical-fitting shortcuts instead of importing generator label helpers.  It
checks canonical authority parity, joint exact overrides, per-band schedule and
profile support, deterministic replay, rival counterexamples, and every query
rotation of consecutive four-pair lesson windows.

Run through the packet wrapper so portable review helpers are on ``PYTHONPATH``::

    python3 run_with_racket.py python3 \
      generators/ffa91bb651d1/workspace/reference_probe.py \
      --per-band 100 --lesson-starts 40 \
      --json-out ../checks/reference-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from typing import Callable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "ffa91bb651d1"
HOME = Path(__file__).resolve().parents[1]
CANONICAL_PROFILES = {
    (8, 10, 6),
    (7, 11, 7),
    (9, 9, 7),
    (6, 12, 6),
    (8, 8, 7),
}


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"probe_generator_{TASK_ID}", HOME / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def intended_output(grid):
    """Independent implementation of the selected exact-row authority."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        nonzero = [(col, value) for col, value in enumerate(row) if value != 0]
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            left, color = nonzero[0]
            right = nonzero[1][0]
            for col in range(left, right + 1):
                out[row_index][col] = color
    return out


def per_color_exact_pair(grid):
    """Wrong rule: fill any color occurring twice even with another cell."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        counts = Counter(value for value in row if value != 0)
        for color, count in counts.items():
            if count == 2:
                cols = [col for col, value in enumerate(row) if value == color]
                for col in range(cols[0], cols[-1] + 1):
                    out[row_index][col] = color
    return out


def row_or_column(grid):
    """Wrong rule: apply the exact-pair predicate to rows and columns."""
    out = intended_output(grid)
    height, width = len(grid), len(grid[0])
    for col in range(width):
        nonzero = [(row, grid[row][col]) for row in range(height) if grid[row][col] != 0]
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            top, color = nonzero[0]
            bottom = nonzero[1][0]
            for row in range(top, bottom + 1):
                out[row][col] = color
    return out


def exactly_three_targets(grid):
    """Wrong rule: perform the row transform only for three-target scenes."""
    targets = 0
    for row in grid:
        nonzero = [(col, value) for col, value in enumerate(row) if value != 0]
        targets += int(len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1])
    return intended_output(grid) if targets == 3 else deepcopy(grid)


RIVALS: dict[str, Callable] = {
    "exactly_three_targets": exactly_three_targets,
    "per_color_exact_pair": per_color_exact_pair,
    "row_or_column": row_or_column,
}


def _row_counts(row) -> tuple[int, ...]:
    return tuple(sorted(Counter(value for value in row if value != 0).values()))


def classify_pattern(grid) -> str:
    return (
        "comprehensive"
        if any(_row_counts(row) == (1, 2) for row in grid)
        else "canonical"
    )


def profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _canonical_report() -> dict:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    mismatches = [
        index
        for index, pair in enumerate(pairs)
        if intended_output(pair["input"]) != pair["output"]
    ]
    survivors = [
        name
        for name, rival in RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    ]
    return {
        "pairs": len(pairs),
        "oracle_mismatches": mismatches,
        "shortcut_survivors": sorted(survivors),
    }


def _override_matrix() -> dict:
    failures = []
    cases = 0
    for band in (None, "easy", "medium", "hard"):
        for height in (6, 16):
            for width in (8, 16):
                for targets in (2, 3):
                    for pattern in ("canonical", "comprehensive"):
                        for palette in (6, 7):
                            cases += 1
                            key = {
                                "difficulty": band,
                                "grid_h": height,
                                "grid_w": width,
                                "n_targets": targets,
                                "scene_pattern": pattern,
                                "palette_count": palette,
                            }
                            try:
                                grid = GEN.generate(51_000 + cases, cases, **key)
                                findings = GEN.self_check(grid)
                                observed = GEN.observe_overrides(grid)
                                expected = {k: v for k, v in key.items() if k != "difficulty"}
                                if findings or observed != expected or intended_output(grid) == grid:
                                    failures.append(
                                        {
                                            "case": key,
                                            "findings": findings,
                                            "observed": observed,
                                            "expected": expected,
                                            "identity": intended_output(grid) == grid,
                                        }
                                    )
                            except Exception as exc:
                                failures.append(
                                    {
                                        "case": key,
                                        "error": f"{type(exc).__name__}: {exc}",
                                    }
                                )
    return {"cases": cases, "failures": failures}


def _band_report(band: str, per_band: int) -> dict:
    patterns: Counter[str] = Counter()
    profiles: Counter[str] = Counter()
    self_check_failures = []
    replay_failures = []
    identities = 0
    rival_counterexamples = Counter({name: 0 for name in RIVALS})

    for index in range(per_band):
        seed = 90_000 + index * 997
        grid = GEN.generate(seed, index, difficulty=band)
        replay = GEN.generate(seed, index, difficulty=band)
        if replay != grid:
            replay_failures.append(index)
        findings = GEN.self_check(grid)
        if findings:
            self_check_failures.append({"index": index, "findings": findings})
            continue
        patterns[classify_pattern(grid)] += 1
        prof = profile(grid)
        profiles[f"{prof[0]}x{prof[1]}p{prof[2]}"] += 1
        truth = intended_output(grid)
        identities += int(truth == grid)
        for name, rival in RIVALS.items():
            rival_counterexamples[name] += int(rival(grid) != truth)

    exact_hits = sum(
        count
        for key, count in profiles.items()
        if tuple(map(int, key.replace("x", " ").replace("p", " ").split()))
        in CANONICAL_PROFILES
    )
    return {
        "draws": per_band,
        "patterns": dict(sorted(patterns.items())),
        "profiles": dict(sorted(profiles.items())),
        "exact_canonical_profile_hits": exact_hits,
        "self_check_failures": self_check_failures,
        "deterministic_replay_failures": replay_failures,
        "oracle_identity_count": identities,
        "rival_counterexamples": dict(sorted(rival_counterexamples.items())),
    }


def _lesson_window_report(lesson_starts: int) -> dict:
    failures = []
    windows = []
    for band in ("easy", "medium", "hard"):
        for start in range(lesson_starts):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(700_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            rotations = []
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                survivors = [
                    name
                    for name, rival in RIVALS.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                    and rival(query["input"]) != query["output"]
                ]
                hook = GEN.lesson_identifiable(deepcopy(demos), deepcopy(query))
                rotation = {
                    "query_index": query_index,
                    "surviving_rivals": survivors,
                    "hook_findings": hook,
                }
                rotations.append(rotation)
                if survivors or hook:
                    failures.append(
                        {
                            "band": band,
                            "start": start,
                            **rotation,
                        }
                    )
            windows.append(
                {
                    "band": band,
                    "start": start,
                    "patterns": [classify_pattern(pair["input"]) for pair in pairs],
                    "rotations": rotations,
                }
            )
    return {
        "starts_per_band": lesson_starts,
        "examples_per_lesson": GEN.EXAMPLES_NEEDED,
        "all_rotations_identifiable": not failures,
        "failures": failures,
        "windows": windows,
    }


def run_probe(*, per_band: int = 100, lesson_starts: int = 25) -> dict:
    if type(per_band) is not int or per_band < 4:
        raise ValueError("per_band must be an integer >= 4")
    if type(lesson_starts) is not int or lesson_starts < 1:
        raise ValueError("lesson_starts must be a positive integer")

    canonical = _canonical_report()
    overrides = _override_matrix()
    bands = {
        band: _band_report(band, per_band)
        for band in ("easy", "medium", "hard")
    }
    lessons = _lesson_window_report(lesson_starts)

    failures = []
    if canonical["oracle_mismatches"]:
        failures.append("independent oracle disagrees with canonical outputs")
    if set(canonical["shortcut_survivors"]) != set(RIVALS):
        failures.append("canonical shortcut survivor set changed")
    if overrides["failures"]:
        failures.append("joint exact override matrix has failures")
    for band, stats in bands.items():
        if set(stats["patterns"]) != set(GEN.SCHEDULE_PROFILES):
            failures.append(f"{band}: schedule pattern missing")
        if stats["self_check_failures"]:
            failures.append(f"{band}: self_check failure")
        if stats["deterministic_replay_failures"]:
            failures.append(f"{band}: nondeterministic replay")
        if stats["oracle_identity_count"]:
            failures.append(f"{band}: identity transformation emitted")
        if stats["exact_canonical_profile_hits"] == 0:
            failures.append(f"{band}: no exact canonical-profile support")
        for rival, count in stats["rival_counterexamples"].items():
            if count == 0:
                failures.append(f"{band}: no counterexample for {rival}")
    if not lessons["all_rotations_identifiable"]:
        failures.append("a rotated lesson leaves a declared rival viable")

    return {
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "canonical": canonical,
        "override_matrix": overrides,
        "bands": bands,
        "lesson_windows": lessons,
        "limits": [
            "Finite checks cover declared rivals only; they are not a proof of unique induction.",
            "The independent oracle mirrors the selected rule but is not the Racket executor.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--lesson-starts", type=int, default=25)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(per_band=args.per_band, lesson_starts=args.lesson_starts)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
