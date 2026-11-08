#!/usr/bin/env python3
"""Exhaustive schedule/override probe for generator 2c8fab02e3fe.

This is deliberately independent of the shared battery's random lesson sample.
It enumerates every joint endpoint combination of the public controls and every
held-out query position for a configurable set of cyclic schedule starts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "2c8fab02e3fe"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
for path in (REPO_ROOT / "src", REPO_ROOT / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def run_probe(*, starts: int = 64) -> dict[str, Any]:
    if type(starts) is not int or starts < 1:
        raise ValueError("starts must be a positive integer")
    gen = _load_generator()
    generator_path = TASK_DIR / "generator.py"
    report: dict[str, Any] = {
        "schema": "2c8fab02e3fe-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "starts_per_band": starts,
        "boundary_cases": 0,
        "boundary_failures": [],
        "lesson_windows": 0,
        "query_rotations": 0,
        "lesson_failures": [],
        "canonical_shortcuts_checked": 0,
        "canonical_shortcut_failures": [],
    }

    boundary_values = itertools.product(
        (8, 16),
        (10, 18),
        (4, 7),
        (4, 9),
        (1, 9),
        ("top", "right", "bottom", "left"),
        ("clean", "outside_pair", "inside_pair", "split_pair"),
    )
    for index, values in enumerate(boundary_values):
        requested = dict(
            zip(
                ("grid_h", "grid_w", "frame_h", "frame_w", "key_color", "key_side", "decoy_mode"),
                values,
            )
        )
        report["boundary_cases"] += 1
        try:
            grid = gen.generate(
                991,
                index,
                difficulty=("easy", "medium", "hard")[index % 3],
                **requested,
            )
            observed = gen.observe_overrides(grid)
            errors = gen.self_check(grid)
            oracle_match = gen.rule_mirror(grid) == gen.oracle_output(grid)
            if errors or observed != requested or not oracle_match:
                report["boundary_failures"].append(
                    {
                        "index": index,
                        "requested": requested,
                        "observed": observed,
                        "self_check": errors,
                        "oracle_match": oracle_match,
                    }
                )
        except Exception as exc:  # retain the exact failing endpoint
            report["boundary_failures"].append(
                {"index": index, "requested": requested, "exception": repr(exc)}
            )

    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        report["canonical_shortcuts_checked"] += 1
        misses = [index for index, pair in enumerate(canonical) if rival(pair["input"]) != pair["output"]]
        if misses:
            report["canonical_shortcut_failures"].append(
                {"rival": name, "canonical_pair_indices_not_fit": misses}
            )

    for band in ("easy", "medium", "hard"):
        for start in range(starts):
            pairs = [
                _pair(gen, gen.generate(1207 + start, start + offset, difficulty=band))
                for offset in range(gen.LESSON_SCHEDULE_PERIOD)
            ]
            report["lesson_windows"] += 1
            for query_index, query in enumerate(pairs):
                report["query_rotations"] += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                ambiguity = gen.lesson_identifiable(demos, query)
                surviving = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(item["input"]) == item["output"] for item in demos)
                ]
                if ambiguity or surviving:
                    report["lesson_failures"].append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "ambiguity": ambiguity,
                            "surviving_competitors": surviving,
                        }
                    )

    report["passed"] = not any(
        report[name]
        for name in (
            "boundary_failures",
            "lesson_failures",
            "canonical_shortcut_failures",
        )
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts", type=int, default=64, help="cyclic starts per difficulty band")
    parser.add_argument("--out", type=Path, help="optional JSON output path")
    args = parser.parse_args()
    report = run_probe(starts=args.starts)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
