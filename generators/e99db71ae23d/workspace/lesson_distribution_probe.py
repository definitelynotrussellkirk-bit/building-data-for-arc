#!/usr/bin/env python3
"""Measure default lesson diversity and cyclic-query identifiability.

Run from anywhere inside an extracted review packet, for example:

    python3 repo/generators/e99db71ae23d/workspace/lesson_distribution_probe.py \
        --seeds 100 --out checks/lesson-distribution-after.json \
        --require-rotations

The report is source-bound by SHA-256 and records exact seed/index denominators.
It uses only the selected Python generator's public generation/mirror/lesson hooks.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "e99db71ae23d"


def find_packet_root(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (
            (candidate / "repo/generators" / TASK_ID / "generator.py").is_file()
            and (candidate / "repo/shared/runtime/puzzle_generators/base.py").is_file()
        ):
            return candidate
    raise FileNotFoundError(f"could not find extracted packet root from {start}")


def load_generator(packet_root: Path):
    runtime = packet_root / "repo/shared/runtime"
    sys.path.insert(0, str(runtime))
    path = packet_root / "repo/generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"{TASK_ID}_distribution_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def build_report(gen: Any, generator_path: Path, *, seeds: int, bands: list[str]) -> dict[str, Any]:
    if seeds <= 0:
        raise ValueError("--seeds must be positive")
    lesson_size = int(gen.EXAMPLES_NEEDED) + 1
    report: dict[str, Any] = {
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seed_range": [0, seeds - 1],
        "seed_count": seeds,
        "sample_indices": list(range(lesson_size)),
        "examples_needed": int(gen.EXAMPLES_NEEDED),
        "bands": {},
    }
    for band in bands:
        profile_counts: Counter[str] = Counter()
        input_counts: Counter[tuple[tuple[int, ...], ...]] = Counter()
        duplicate_windows: list[int] = []
        rotation_failures: list[dict[str, Any]] = []
        for seed in range(seeds):
            episodes = []
            keys = []
            for sample_index in range(lesson_size):
                grid = gen.generate(seed, sample_index, difficulty=band)
                facts = gen.semantic_observables(grid)
                profile_counts[facts["scene_profile"]] += 1
                key = grid_key(grid)
                input_counts[key] += 1
                keys.append(key)
                episodes.append({"input": grid, "output": gen.rule_mirror(grid)})
            if len(set(keys)) != len(keys):
                duplicate_windows.append(seed)
            for query_index, query in enumerate(episodes):
                demos = [episode for index, episode in enumerate(episodes) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    rotation_failures.append(
                        {"seed": seed, "query_index": query_index, "reasons": reasons}
                    )
        instances = seeds * lesson_size
        repeated_groups = [count for count in input_counts.values() if count > 1]
        report["bands"][band] = {
            "instances": instances,
            "unique_inputs": len(input_counts),
            "unique_fraction": len(input_counts) / instances,
            "instances_in_repeated_groups": sum(repeated_groups),
            "excess_replays": sum(count - 1 for count in repeated_groups),
            "most_common_input_count": max(input_counts.values()),
            "profile_counts": dict(sorted(profile_counts.items())),
            "lesson_windows": seeds,
            "windows_with_internal_duplicate_inputs": len(duplicate_windows),
            "duplicate_window_seeds": duplicate_windows,
            "rotation_checks": seeds * lesson_size,
            "rotation_failure_count": len(rotation_failures),
            "rotation_failures": rotation_failures,
        }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument(
        "--bands",
        nargs="+",
        default=["easy", "medium", "hard"],
        choices=["easy", "medium", "hard"],
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--require-rotations",
        action="store_true",
        help="exit nonzero if any cyclic query position is ambiguous",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet_root = find_packet_root(Path(__file__))
    gen, generator_path = load_generator(packet_root)
    report = build_report(gen, generator_path, seeds=args.seeds, bands=args.bands)
    out = args.out if args.out.is_absolute() else packet_root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    for band, row in report["bands"].items():
        print(
            f"{band}: unique={row['unique_inputs']}/{row['instances']} "
            f"max_repeat={row['most_common_input_count']} "
            f"duplicate_windows={row['windows_with_internal_duplicate_inputs']} "
            f"rotation_failures={row['rotation_failure_count']}/{row['rotation_checks']}"
        )
    if args.require_rotations and any(
        row["rotation_failure_count"] for row in report["bands"].values()
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
