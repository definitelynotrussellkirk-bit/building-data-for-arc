#!/usr/bin/env python3
"""Portable semantic/distribution audit for generator 2db2974cdb04.

This is intentionally useful outside the review harness: it independently
recomputes the hole-extraction answer, verifies all canonical pairs, samples
all difficulty bands, reports observable axes and named-rival disagreement,
and emits JSON suitable for a future reviewer or CI artifact.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK = "2db2974cdb04"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("audit_2db2974cdb04", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    spec.loader.exec_module(module)
    return module


def _components(grid: list[list[int]], *, zero: bool):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if (grid[r][c] == 0) is zero
    }
    result = []
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point not in unseen:
                    continue
                nr, nc = point
                if zero or grid[nr][nc] == color:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append((color, cells))
    return result


def independent_oracle(grid: list[list[int]]) -> list[list[int]]:
    """Mirror the canonical region/bbox semantics without generator helpers."""
    out = [[0 for _ in row] for row in grid]
    zero_regions = [cells for _, cells in _components(grid, zero=True)]
    for color, cells in _components(grid, zero=False):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        for region in zero_regions:
            if region and all(top < r < bottom and left < c < right for r, c in region):
                for r, c in region:
                    out[r][c] = color
    return out


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def run_audit(*, per_band: int = 100) -> dict[str, Any]:
    if type(per_band) is not int or per_band <= 0:
        raise ValueError("per_band must be a positive integer")
    gen = _load_generator()
    official = canonical_pairs(TASK, root=ROOT)
    canonical_profiles = {_profile(pair["input"]) for pair in official}
    canonical_failures = []
    for pair in official:
        tag = f"v{pair['variant']}-{pair['split']}{pair['pair_index']}"
        findings = gen.self_check(deepcopy(pair["input"]))
        if findings:
            canonical_failures.append({"pair": tag, "kind": "self_check", "detail": findings})
        predicted = independent_oracle(pair["input"])
        if predicted != pair["output"]:
            canonical_failures.append({"pair": tag, "kind": "oracle_mismatch"})

    report: dict[str, Any] = {
        "task_id": TASK,
        "generator_version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_pairs": len(official),
        "canonical_profiles": [list(item) for item in sorted(canonical_profiles)],
        "canonical_failures": canonical_failures,
        "bands": {},
        "errors": [],
    }
    if canonical_failures:
        report["errors"].append("canonical contract failure")

    for band_index, band in enumerate(("easy", "medium", "hard")):
        stats: dict[str, Any] = {
            "draws": per_band,
            "invalid": 0,
            "oracle_mismatches": 0,
            "identity_outputs": 0,
            "exact_canonical_profiles": 0,
            "distinct_inputs": 0,
            "distinct_outputs": 0,
            "axis_counts": {name: Counter() for name in gen.AXES},
            "schedule_counts": Counter(),
            "rival_disagreements": Counter(),
        }
        inputs = set()
        outputs = set()
        for index in range(per_band):
            seed = 520_000 + band_index * 10_000 + index
            sample_index = 31_000 + index
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:
                stats["invalid"] += 1
                report["errors"].append(
                    f"{band} generation crash at {index}: {type(exc).__name__}: {exc}"
                )
                continue
            findings = gen.self_check(deepcopy(grid))
            if findings:
                stats["invalid"] += 1
                report["errors"].append(f"{band} invalid draw {index}: {findings[0]}")
                continue
            expected = independent_oracle(grid)
            try:
                mirrored = gen.rule_mirror(deepcopy(grid))
            except Exception as exc:
                stats["oracle_mismatches"] += 1
                report["errors"].append(
                    f"{band} generator mirror crashed at {index}: {type(exc).__name__}: {exc}"
                )
                continue
            if mirrored != expected:
                stats["oracle_mismatches"] += 1
                report["errors"].append(f"{band} oracle mismatch at {index}")
            if expected == grid:
                stats["identity_outputs"] += 1
            if _profile(grid) in canonical_profiles:
                stats["exact_canonical_profiles"] += 1
            inputs.add(_freeze(grid))
            outputs.add(_freeze(expected))
            observed = gen.observe_overrides(grid)
            for name, value in observed.items():
                stats["axis_counts"][name][str(value)] += 1
            stats["schedule_counts"][str(gen.schedule_profile(seed, sample_index, band))] += 1
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if rival(deepcopy(grid)) != expected:
                    stats["rival_disagreements"][name] += 1
        stats["distinct_inputs"] = len(inputs)
        stats["distinct_outputs"] = len(outputs)
        stats["axis_counts"] = {
            name: dict(sorted(counts.items())) for name, counts in stats["axis_counts"].items()
        }
        stats["schedule_counts"] = dict(sorted(stats["schedule_counts"].items()))
        stats["rival_disagreements"] = dict(sorted(stats["rival_disagreements"].items()))
        report["bands"][band] = stats
        if stats["invalid"]:
            report["errors"].append(f"{band}: {stats['invalid']} invalid draw(s)")
        if stats["oracle_mismatches"]:
            report["errors"].append(f"{band}: {stats['oracle_mismatches']} oracle mismatch(es)")
        if stats["identity_outputs"]:
            report["errors"].append(f"{band}: {stats['identity_outputs']} identity output(s)")
        if not stats["exact_canonical_profiles"]:
            report["errors"].append(f"{band}: no exact canonical-profile support")

    # De-duplicate repeated aggregate and per-example errors while preserving order.
    report["errors"] = list(dict.fromkeys(report["errors"]))
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = run_audit(per_band=args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
