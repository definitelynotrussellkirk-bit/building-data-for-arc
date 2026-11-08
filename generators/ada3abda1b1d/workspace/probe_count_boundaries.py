#!/usr/bin/env python3
"""Measure upper-bound exact-count coverage across exhaustive cyclic starts.

This is intentionally independent of the declared semantic hooks: it catches a
future generator that silently stops emitting count-five counterexamples.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("ada3_boundary_probe_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value != 0)


def mask_by_count(
    grid: list[list[int]], predicate: Callable[[int], bool]
) -> list[list[int]]:
    totals = counts(grid)
    return [
        [
            value if value != 0 and predicate(totals[value]) else 0
            for value in row
        ]
        for row in grid
    ]


def keep_two_or_five_plus(grid: list[list[int]]) -> list[list[int]]:
    return mask_by_count(grid, lambda count: count == 2 or count >= 5)


def first_disagreement(
    grid: list[list[int]],
    intended: list[list[int]],
    rival: list[list[int]],
) -> dict[str, Any] | None:
    for row, (expected_row, rival_row) in enumerate(zip(intended, rival)):
        for col, (expected, actual) in enumerate(zip(expected_row, rival_row)):
            if expected != actual:
                return {
                    "cell": [row, col],
                    "input_value": grid[row][col],
                    "intended_value": expected,
                    "rival_value": actual,
                    "counts": dict(sorted(counts(grid).items())),
                }
    return None


def probe(
    generator_path: Path,
    seeds: list[int],
    starts: int,
    difficulties: list[str | None],
) -> dict[str, Any]:
    module = load_generator(generator_path)
    source = generator_path.read_bytes()
    report: dict[str, Any] = {
        "schema": "ada3-count-boundary-probe-v1",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "seeds": seeds,
        "starts": starts,
        "window_size": 3,
        "difficulties": {},
    }
    total_surviving = 0
    total_windows = 0
    first_witness: dict[str, Any] | None = None

    for difficulty in difficulties:
        key = "none" if difficulty is None else difficulty
        inputs = 0
        count_five_inputs = 0
        max_count = 0
        surviving_windows: list[dict[str, int]] = []
        signatures: Counter[tuple[int, ...]] = Counter()

        for seed in seeds:
            grids = [
                module.generate(seed, index, difficulty=difficulty)
                for index in range(starts + 2)
            ]
            for grid in grids:
                signature = tuple(sorted(counts(grid).values()))
                signatures[signature] += 1
                inputs += 1
                max_count = max(max_count, max(signature, default=0))
                count_five_inputs += 5 in signature

            for start in range(starts):
                total_windows += 1
                window = grids[start : start + 3]
                agrees = True
                for grid in window:
                    intended = module.rule_mirror(grid)
                    rival = keep_two_or_five_plus(grid)
                    if rival != intended:
                        agrees = False
                        if first_witness is None:
                            first_witness = {
                                "difficulty": key,
                                "seed": seed,
                                "sample_index": start,
                                "detail": first_disagreement(grid, intended, rival),
                                "input": grid,
                                "intended_output": intended,
                                "rival_output": rival,
                            }
                        break
                if agrees:
                    surviving_windows.append({"seed": seed, "start": start})
                    total_surviving += 1

        report["difficulties"][key] = {
            "inputs": inputs,
            "count_five_inputs": count_five_inputs,
            "max_nonzero_color_count": max_count,
            "surviving_three_example_windows": len(surviving_windows),
            "first_surviving_windows": surviving_windows[:10],
            "signatures": [
                {"counts": list(signature), "occurrences": frequency}
                for signature, frequency in signatures.most_common()
            ],
        }

    report["summary"] = {
        "total_three_example_windows": total_windows,
        "surviving_three_example_windows": total_surviving,
        "all_windows_reject_rival": total_surviving == 0,
        "first_rejection_witness": first_witness,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=HERE.parent.parent / "generator.py",
        help="generator.py to inspect (defaults to the selected source)",
    )
    parser.add_argument("--seeds", default="0,17,33")
    parser.add_argument("--starts", type=int, default=72)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    result = probe(
        args.generator.resolve(),
        seeds=seeds,
        starts=args.starts,
        difficulties=[None, "easy", "medium", "hard"],
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if result["summary"]["all_windows_reject_rival"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
