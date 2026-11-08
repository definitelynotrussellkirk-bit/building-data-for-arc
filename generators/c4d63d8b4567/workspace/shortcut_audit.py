#!/usr/bin/env python3
"""Audit the global-exactly-two shortcut against canonical and generated data.

Run from any directory inside the review repository, for example::

    PYTHONPATH=shared/runtime python3 \
      generators/c4d63d8b4567/workspace/shortcut_audit.py \
      --seeds 50 --window-starts 8 \
      --out ../checks/probes/global_exactly_two.json

The tool is task-local and read-only.  It verifies that the shortcut remains
plausible on the public canonical examples while every audited four-example
window contains a generated counterexample.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Iterable, Sequence

TASK_ID = "c4d63d8b4567"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
CANONICAL = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")


def _load_generator() -> ModuleType:
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid(value: object) -> list[list[int]]:
    if not isinstance(value, list) or not value:
        raise ValueError("canonical grid must be a non-empty list")
    if all(isinstance(row, str) for row in value):
        return [[int(cell) for cell in row] for row in value]
    if all(isinstance(row, list) for row in value):
        return [[int(cell) for cell in row] for row in value]
    raise ValueError("canonical grid rows must all be strings or lists")


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        test = row.get("test")
        raw_pairs = list(row.get("train") or [])
        if isinstance(test, dict):
            raw_pairs.append(test)
        elif isinstance(test, list):
            raw_pairs.extend(test)
        return [
            {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
            for pair in raw_pairs
        ]
    raise ValueError(f"missing canonical task {TASK_ID}")


def _counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value)


def _difference_cells(
    intended: list[list[int]], rival: list[list[int]]
) -> list[list[int]]:
    return [
        [row, col, intended[row][col], rival[row][col]]
        for row in range(len(intended))
        for col in range(len(intended[0]))
        if intended[row][col] != rival[row][col]
    ]


def _witness_record(
    generator: ModuleType,
    grid: list[list[int]],
    *,
    seed: int,
    sample_index: int,
    band: str,
) -> dict[str, object]:
    intended = generator.rule_mirror(grid)
    rival = generator.SEMANTIC_RIVALS["global_exactly_two"](grid)
    counts = _counts(grid)
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": band,
        "global_color_counts": dict(sorted(counts.items())),
        "max_global_multiplicity": max(counts.values(), default=0),
        "input": grid,
        "intended_output": intended,
        "global_exactly_two_output": rival,
        "difference_cells": _difference_cells(intended, rival),
    }


def build_report(
    generator: ModuleType,
    *,
    seeds: Iterable[int],
    window_starts: Iterable[int] = (0,),
) -> dict[str, object]:
    seed_values = tuple(int(seed) for seed in seeds)
    starts = tuple(int(start) for start in window_starts)
    if not seed_values:
        raise ValueError("at least one seed is required")
    if not starts or any(start < 0 for start in starts):
        raise ValueError("window starts must be non-negative")

    rival = generator.SEMANTIC_RIVALS["global_exactly_two"]
    canonical = _canonical_pairs()
    canonical_rival_matches = 0
    canonical_mirror_matches = 0
    canonical_max_multiplicity = 0
    failures: list[dict[str, object]] = []

    for index, pair in enumerate(canonical):
        counts = _counts(pair["input"])
        canonical_max_multiplicity = max(
            canonical_max_multiplicity,
            max(counts.values(), default=0),
        )
        if rival(pair["input"]) == pair["output"]:
            canonical_rival_matches += 1
        else:
            failures.append({"kind": "canonical_rival_disagreement", "pair": index})
        if generator.rule_mirror(pair["input"]) == pair["output"]:
            canonical_mirror_matches += 1
        else:
            failures.append({"kind": "canonical_mirror_disagreement", "pair": index})

    case_count = 0
    repeated_witnesses = 0
    rival_disagreements = 0
    windows_without_refutation: list[dict[str, object]] = []
    first_generated_witness: dict[str, object] | None = None

    for seed in seed_values:
        for band in BANDS:
            for start in starts:
                window_refuted = False
                for sample_index in range(
                    start, start + generator.EXAMPLES_NEEDED
                ):
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    case_count += 1
                    errors = generator.self_check(grid, difficulty=band)
                    if errors:
                        failures.append(
                            {
                                "kind": "self_check",
                                "seed": seed,
                                "difficulty": band,
                                "sample_index": sample_index,
                                "errors": errors,
                            }
                        )
                    is_repeated = generator.SEMANTIC_WITNESSES["repeated_color"](
                        grid
                    )
                    repeated_witnesses += int(is_repeated)
                    intended = generator.rule_mirror(grid)
                    if rival(grid) != intended:
                        rival_disagreements += 1
                        window_refuted = True
                        if first_generated_witness is None:
                            first_generated_witness = _witness_record(
                                generator,
                                grid,
                                seed=seed,
                                sample_index=sample_index,
                                band=band,
                            )
                if not window_refuted:
                    windows_without_refutation.append(
                        {"seed": seed, "difficulty": band, "start": start}
                    )

    if first_generated_witness is None:
        failures.append({"kind": "no_generated_shortcut_witness"})
    if windows_without_refutation:
        failures.append(
            {
                "kind": "unrefuted_windows",
                "count": len(windows_without_refutation),
            }
        )

    report = {
        "schema": "c4d63d8b4567-global-exactly-two-audit-v1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "shortcut": "require every active color to occur exactly twice globally",
        "canonical": {
            "pair_count": len(canonical),
            "rival_matches": canonical_rival_matches,
            "mirror_matches": canonical_mirror_matches,
            "max_global_multiplicity": canonical_max_multiplicity,
        },
        "generated": {
            "seed_count": len(seed_values),
            "bands": list(BANDS),
            "window_starts": list(starts),
            "case_count": case_count,
            "repeated_witnesses": repeated_witnesses,
            "rival_disagreements": rival_disagreements,
            "windows_without_refutation": windows_without_refutation,
        },
        "first_generated_witness": first_generated_witness,
        "failures": failures,
    }
    report["ok"] = (
        not failures
        and canonical_rival_matches == len(canonical)
        and canonical_mirror_matches == len(canonical)
        and rival_disagreements > 0
    )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        type=int,
        default=50,
        help="audit integer seeds in range(0, N); default: 50",
    )
    parser.add_argument(
        "--window-starts",
        type=int,
        default=8,
        help="audit four-example windows starting at 0 through N-1; default: 8",
    )
    parser.add_argument("--out", type=Path, help="write the JSON report here")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.seeds < 1:
        raise SystemExit("--seeds must be at least 1")
    if args.window_starts < 1:
        raise SystemExit("--window-starts must be at least 1")
    report = build_report(
        _load_generator(),
        seeds=range(args.seeds),
        window_starts=range(args.window_starts),
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
