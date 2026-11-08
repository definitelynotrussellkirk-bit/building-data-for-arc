#!/usr/bin/env python3
"""Independent semantic probe for generator 2038a3a66886.

This tool intentionally does not call a label helper from ``generator.py``.
It provides a second implementation of the selected row-span rule, confirms
canonical examples, measures semantic-pattern coverage, records exact rival
counterexamples, and checks every consecutive three-demo schedule window.

Run from the packet repo through ``run_with_racket.py`` or with
``PYTHONPATH=shared/runtime:src``::

    python3 generators/2038a3a66886/workspace/reference_probe.py \
        --per-band 100 --json-out ../checks/reference-probe.json
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

TASK_ID = "2038a3a66886"
HOME = Path(__file__).resolve().parents[1]


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
    """Independent implementation of the selected Racket authority."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        # dict.fromkeys reproduces remove-duplicates' first-occurrence order.
        for color in dict.fromkeys(value for value in row if value != 0):
            cols = [col for col, value in enumerate(row) if value == color]
            if len(cols) >= 2:
                for col in range(min(cols), max(cols) + 1):
                    out[row_index][col] = color
    return out


def outermost_nonzero(grid):
    """Plausible wrong rule: one leftmost-colored span per nonempty row."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        cols = [col for col, value in enumerate(row) if value != 0]
        if len(cols) >= 2:
            for col in range(cols[0], cols[-1] + 1):
                out[row_index][col] = row[cols[0]]
    return out


def exact_pair_only(grid):
    """Plausible wrong rule: ignore a color when it occurs three or more times."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        counts = Counter(value for value in row if value != 0)
        for color, count in counts.items():
            if count == 2:
                cols = [col for col, value in enumerate(row) if value == color]
                for col in range(cols[0], cols[-1] + 1):
                    out[row_index][col] = color
    return out


RIVALS: dict[str, Callable] = {
    "exact_pair_only": exact_pair_only,
    "outermost_nonzero": outermost_nonzero,
}
_PATTERN_BY_COUNTS = {
    (2,): "canonical",
    (3,): "triple",
    (2, 2): "multi_pair",
    (1, 2): "distractor",
    (2, 3): "combined",
}
_CANONICAL_PROFILES = {
    (7, 10, 4),
    (8, 12, 4),
    (6, 9, 3),
    (9, 11, 4),
    (7, 13, 4),
}


def classify_pattern(grid) -> str:
    patterns = {
        _PATTERN_BY_COUNTS[
            tuple(sorted(Counter(value for value in row if value != 0).values()))
        ]
        for row in grid
        if any(value != 0 for value in row)
    }
    if len(patterns) != 1:
        raise ValueError(f"expected one row pattern, observed {sorted(patterns)}")
    return patterns.pop()


def profile(grid) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _canonical_report() -> dict:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    mismatches = []
    survivors = []
    for index, pair in enumerate(pairs):
        if intended_output(pair["input"]) != pair["output"]:
            mismatches.append(index)
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in pairs):
            survivors.append(name)
    return {
        "pairs": len(pairs),
        "oracle_mismatches": mismatches,
        "shortcut_survivors": sorted(survivors),
    }


def _band_report(band: str, per_band: int) -> dict:
    patterns: Counter[str] = Counter()
    profiles: Counter[str] = Counter()
    strict_failures = []
    replay_failures = []
    identities = 0
    rival_counterexamples = Counter({name: 0 for name in RIVALS})

    for index in range(per_band):
        seed = 90_000 + index * 997
        sample_index = index
        grid = GEN.generate(seed, sample_index, difficulty=band)
        replay = GEN.generate(seed, sample_index, difficulty=band)
        if replay != grid:
            replay_failures.append(index)
        findings = GEN.self_check(grid)
        if findings:
            strict_failures.append({"index": index, "findings": findings})
            continue
        patterns[classify_pattern(grid)] += 1
        prof = profile(grid)
        profiles[f"{prof[0]}x{prof[1]}p{prof[2]}"] += 1
        authority = intended_output(grid)
        if authority == grid:
            identities += 1
        for name, rival in RIVALS.items():
            if rival(grid) != authority:
                rival_counterexamples[name] += 1

    exact_profile_hits = sum(
        count
        for key, count in profiles.items()
        if tuple(map(int, key.replace("x", " ").replace("p", " ").split()))
        in _CANONICAL_PROFILES
    )
    return {
        "draws": per_band,
        "patterns": dict(sorted(patterns.items())),
        "profiles": dict(sorted(profiles.items())),
        "exact_canonical_profile_hits": exact_profile_hits,
        "self_check_failures": strict_failures,
        "deterministic_replay_failures": replay_failures,
        "oracle_identity_count": identities,
        "rival_counterexamples": dict(sorted(rival_counterexamples.items())),
    }


def _lesson_window_report(lesson_starts: int) -> dict:
    failures = []
    windows = []
    for start in range(lesson_starts):
        grids = [
            GEN.generate(700_000 + start, start + offset, difficulty="medium")
            for offset in range(GEN.EXAMPLES_NEEDED)
        ]
        patterns = [classify_pattern(grid) for grid in grids]
        survivors = [
            name
            for name, rival in RIVALS.items()
            if all(rival(grid) == intended_output(grid) for grid in grids)
        ]
        entry = {
            "start": start,
            "patterns": patterns,
            "surviving_rivals": survivors,
        }
        windows.append(entry)
        if survivors:
            failures.append(entry)
    return {
        "starts_checked": lesson_starts,
        "examples_per_lesson": GEN.EXAMPLES_NEEDED,
        "all_identifiable": not failures,
        "failures": failures,
        "windows": windows,
    }


def run_probe(*, per_band: int = 100, lesson_starts: int = 25) -> dict:
    if type(per_band) is not int or per_band < 5:
        raise ValueError("per_band must be an integer >= 5")
    if type(lesson_starts) is not int or lesson_starts < 1:
        raise ValueError("lesson_starts must be a positive integer")

    canonical = _canonical_report()
    bands = {
        band: _band_report(band, per_band)
        for band in ("easy", "medium", "hard")
    }
    lessons = _lesson_window_report(lesson_starts)

    failures = []
    if canonical["oracle_mismatches"]:
        failures.append("independent oracle disagrees with canonical outputs")
    expected_patterns = set(GEN.ROW_PATTERNS)
    for band, stats in bands.items():
        if set(stats["patterns"]) != expected_patterns:
            failures.append(f"{band}: missing semantic row pattern")
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
    if not lessons["all_identifiable"]:
        failures.append("one or more three-demo windows leave a rival alive")

    return {
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "canonical": canonical,
        "bands": bands,
        "lesson_windows": lessons,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--lesson-starts", type=int, default=25)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(
        per_band=args.per_band,
        lesson_starts=args.lesson_starts,
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
