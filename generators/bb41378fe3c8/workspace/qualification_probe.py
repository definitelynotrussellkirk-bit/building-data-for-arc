#!/usr/bin/env python3
"""Source-bound qualification probe for bb41378fe3c8.

This is intentionally task-local.  It checks the two historical defects, every
small cyclic lesson start/query rotation, and every rival currently declared by
the selected generator.  It uses the independent canonical labels for public
pairs and the generator's independent Python mirror for generated inputs; the
shared Racket-backed battery remains the authority check.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("bb41378fe3c8_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def marker_count(grid: list[list[int]]) -> int:
    return sum(value == 2 for row in grid for value in row)


def labelled(gen: Any, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=HOME / "generator.py",
        help="candidate generator.py (default: selected source)",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    source = args.generator.resolve()
    gen = load_generator(source)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    canon = canonical_pairs("bb41378fe3c8", root=find_root(__file__))
    shortcut_fit: dict[str, dict[str, Any]] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matched = sum(rival(pair["input"]) == pair["output"] for pair in canon)
        shortcut_fit[name] = {
            "matched": matched,
            "total": len(canon),
            "fits_all": matched == len(canon),
        }

    exact_counts: dict[str, int] = {}
    exact_failures: list[dict[str, Any]] = []
    for seed in range(200):
        grid = gen.generate(seed, 0, grid_h=6, grid_w=6, n_markers=7)
        count = marker_count(grid)
        exact_counts[str(count)] = exact_counts.get(str(count), 0) + 1
        observed = gen.observe_overrides(grid)
        if count != 7 or observed.get("n_markers") != 7 or gen.self_check(grid):
            exact_failures.append(
                {"seed": seed, "count": count, "observed": observed}
            )

    rotation_failures: list[dict[str, Any]] = []
    rotation_checks = 0
    bands = (None, "easy", "medium", "hard")
    period = len(gen.SCHEDULE_PROFILES)
    for band in bands:
        for seed in range(8):
            for start in range(period):
                lesson = [
                    labelled(gen, gen.generate(seed, start + offset, difficulty=band))
                    for offset in range(4)
                ]
                for query_index in range(4):
                    demos = [
                        pair for index, pair in enumerate(lesson)
                        if index != query_index
                    ]
                    reasons = gen.lesson_identifiable(demos, lesson[query_index])
                    survivors = [
                        name
                        for name, rival in gen.LESSON_COMPETITORS.items()
                        if all(rival(pair["input"]) == pair["output"] for pair in demos)
                    ]
                    rotation_checks += 1
                    if reasons or survivors:
                        rotation_failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "reasons": reasons,
                                "survivors": survivors,
                            }
                        )

    result = {
        "schema": "bb41378fe3c8-qualification-v1",
        "generator_path": str(source),
        "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH,
        "canonical_shortcuts": shortcut_fit,
        "exact_override_sweep": {
            "call": "generate(seed, 0, grid_h=6, grid_w=6, n_markers=7)",
            "seed_range": [0, 199],
            "observed_marker_counts": exact_counts,
            "failures": exact_failures,
        },
        "cyclic_rotation_probe": {
            "bands": ["default", "easy", "medium", "hard"],
            "seeds_per_band": 8,
            "cyclic_starts_per_seed": period,
            "query_positions_per_lesson": 4,
            "checks": rotation_checks,
            "failures": rotation_failures,
        },
        "status": "PASS"
        if not exact_failures
        and not rotation_failures
        and all(item["fits_all"] for item in shortcut_fit.values())
        else "FAIL",
        "limitations": [
            "Generated outputs in this probe come from rule_mirror, not Racket.",
            "The rival set is finite and generator-declared; this is not a uniqueness proof.",
        ],
    }

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
