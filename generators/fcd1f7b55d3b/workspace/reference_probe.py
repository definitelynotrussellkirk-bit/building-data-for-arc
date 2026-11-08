#!/usr/bin/env python3
"""Source-bound regression probe for fcd1f7b55d3b.

This is intentionally independent of the Racket runtime.  It checks the selected
Python generator against an independently written mirror of the canonical rule,
exercises the complete small exact-control cross product, and verifies every
query rotation in consecutive five-pair lesson windows against the declared
canonical-fitting rivals.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "fcd1f7b55d3b"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

_CANONICAL_PROFILES = {
    (8, 9, 3),
    (9, 10, 3),
    (7, 8, 3),
    (9, 9, 3),
}


def _by_color(grid):
    result = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                result.setdefault(value, []).append((row, col))
    return result


def _paint_bbox(out, color, cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    for row in range(min(rows), max(rows) + 1):
        for col in range(min(cols), max(cols) + 1):
            out[row][col] = color


def oracle(grid):
    """Independent selected-rule mirror: exactly-two bboxes on a blank grid."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in _by_color(grid).items():
        if len(cells) == 2:
            _paint_bbox(out, color, cells)
    return out


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_report() -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    mismatches = [
        index
        for index, pair in enumerate(pairs)
        if oracle(pair["input"]) != pair["output"]
    ]
    survivors = sorted(
        name
        for name, rival in GEN.CANONICAL_SHORTCUTS.items()
        if all(rival(deepcopy(pair["input"])) == pair["output"] for pair in pairs)
    )
    return {
        "pairs": len(pairs),
        "oracle_mismatches": mismatches,
        "shortcut_survivors": survivors,
    }


def _override_report() -> dict[str, Any]:
    failures = []
    cases = 0
    for band in ("easy", "medium", "hard"):
        for grid_h, grid_w in ((7, 8), (14, 15)):
            for n_pairs in (2, 3, 4):
                for n_decoys in (0, 1):
                    for orientation in ("backslash", "slash"):
                        cases += 1
                        expected = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_pairs": n_pairs,
                            "n_decoys": n_decoys,
                            "orientation": orientation,
                        }
                        try:
                            grid = GEN.generate(
                                9101,
                                cases,
                                difficulty=band,
                                **expected,
                            )
                            errors = GEN.self_check(grid)
                            observed = GEN.observe_overrides(grid)
                            if errors or observed != expected:
                                failures.append(
                                    {
                                        "band": band,
                                        "expected": expected,
                                        "observed": observed,
                                        "errors": errors,
                                    }
                                )
                        except Exception as exc:
                            failures.append(
                                {
                                    "band": band,
                                    "expected": expected,
                                    "exception": f"{type(exc).__name__}: {exc}",
                                }
                            )
    return {"cases": cases, "failures": failures}


def _band_report(per_band: int) -> dict[str, Any]:
    report = {}
    for band in ("easy", "medium", "hard"):
        profiles = Counter()
        self_check_failures = []
        deterministic_failures = []
        exact_profile_hits = 0
        rival_counterexamples = Counter({name: 0 for name in GEN.SEMANTIC_RIVALS})
        for index in range(per_band):
            seed = 12000 + index
            grid = GEN.generate(seed, index, difficulty=band)
            replay = GEN.generate(seed, index, difficulty=band)
            if grid != replay:
                deterministic_failures.append(index)
            errors = GEN.self_check(grid)
            if errors:
                self_check_failures.append({"index": index, "errors": errors})
                continue
            profiles[GEN.schedule_profile(seed, index, band)] += 1
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            exact_profile_hits += int(profile in _CANONICAL_PROFILES)
            truth = oracle(grid)
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                rival_counterexamples[name] += int(rival(deepcopy(grid)) != truth)
        report[band] = {
            "draws": per_band,
            "profiles": dict(sorted(profiles.items())),
            "self_check_failures": self_check_failures,
            "deterministic_replay_failures": deterministic_failures,
            "exact_canonical_profile_hits": exact_profile_hits,
            "rival_counterexamples": dict(sorted(rival_counterexamples.items())),
        }
    return report


def _lesson_report(lesson_starts: int) -> dict[str, Any]:
    failures = []
    rotations = 0
    for band in ("easy", "medium", "hard"):
        for start in range(lesson_starts):
            pairs = []
            for index in range(start, start + 5):
                grid = GEN.generate(23000 + start, index, difficulty=band)
                pairs.append({"input": grid, "output": oracle(grid)})
            for query_index, query in enumerate(pairs):
                rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = GEN.lesson_identifiable(demos, query)
                undisproved = [
                    name
                    for name, rival in GEN.LESSON_COMPETITORS.items()
                    if all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
                ]
                if reasons or undisproved:
                    failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                            "undisproved_in_demos": undisproved,
                        }
                    )
    return {
        "starts_per_band": lesson_starts,
        "rotations": rotations,
        "failures": failures,
        "all_rotations_identifiable": not failures,
    }


def run_probe(*, per_band: int = 24, lesson_starts: int = 12) -> dict[str, Any]:
    canonical = _canonical_report()
    overrides = _override_report()
    bands = _band_report(per_band)
    lessons = _lesson_report(lesson_starts)
    failed = bool(
        canonical["oracle_mismatches"]
        or set(canonical["shortcut_survivors"]) != set(GEN.CANONICAL_SHORTCUTS)
        or overrides["failures"]
        or lessons["failures"]
        or any(
            stats["self_check_failures"]
            or stats["deterministic_replay_failures"]
            or stats["exact_canonical_profile_hits"] == 0
            or any(count == 0 for count in stats["rival_counterexamples"].values())
            for stats in bands.values()
        )
    )
    return {
        "schema": "fcd1f7b55d3b-reference-probe-v1",
        "status": "FAIL" if failed else "PASS",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(GENERATOR_PATH),
        "canonical": canonical,
        "override_matrix": overrides,
        "bands": bands,
        "lesson_windows": lessons,
    }


def main() -> int:
    report = run_probe()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
