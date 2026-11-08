#!/usr/bin/env python3
"""Enumerate 4x4 erasure masks by semantic depth for generator 135219aecdb4.

This is a review utility, not selected generator code.  It exposes when a
teaching profile depends on the Latin-square isomorphism class and makes
iteration-depth shortcuts visible before changing the generator.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Iterable


WORKSPACE = Path(__file__).resolve().parent
TASK_DIR = WORKSPACE.parent
REPO_ROOT = TASK_DIR.parents[1]


def _load_generator() -> ModuleType:
    runtime = REPO_ROOT / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("mask_census_target", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_census(erasure_counts: Iterable[int] = range(1, 11)) -> dict[str, object]:
    """Return exact mask counts grouped by base, erasure count, and semantics."""
    generator = _load_generator()
    rows: list[dict[str, object]] = []

    for base_index in range(len(generator._LATIN_BASES)):
        for n_erased in erasure_counts:
            if not 1 <= n_erased <= 16:
                raise ValueError(f"n_erased must be in 1..16, got {n_erased}")
            pass_histogram: Counter[str] = Counter()
            missing_symbol_histogram: Counter[str] = Counter()
            profile_counts: Counter[str] = Counter()
            joint_forced_masks = 0

            for mask in itertools.combinations(range(16), n_erased):
                grid = generator._mask_grid(base_index, mask)
                passes = generator._passes_to_complete(grid)
                pass_histogram[str(passes) if passes is not None else "unsolved"] += 1
                missing = {
                    generator._LATIN_BASES[base_index][index // 4][index % 4]
                    for index in mask
                }
                missing_symbol_histogram[str(len(missing))] += 1
                if generator._joint_forced_cells(grid):
                    joint_forced_masks += 1
                for profile in (
                    "one_pass",
                    "three_pass_cascade",
                    "joint_constraints",
                ):
                    if generator._mask_profile_matches(base_index, mask, profile):
                        profile_counts[profile] += 1

            rows.append(
                {
                    "base_index": base_index,
                    "n_erased": n_erased,
                    "total_masks": sum(pass_histogram.values()),
                    "pass_histogram": dict(sorted(pass_histogram.items())),
                    "missing_symbol_histogram": dict(
                        sorted(missing_symbol_histogram.items())
                    ),
                    "joint_forced_masks": joint_forced_masks,
                    "profile_counts": dict(sorted(profile_counts.items())),
                }
            )

    return {
        "schema": "135219aecdb4-mask-space-census-v1",
        "generator_version": generator.VERSION,
        "rows": rows,
    }


def _parse_counts(text: str) -> tuple[int, ...]:
    counts = tuple(int(piece) for piece in text.split(",") if piece.strip())
    if not counts:
        raise argparse.ArgumentTypeError("provide at least one erasure count")
    if any(not 1 <= count <= 16 for count in counts):
        raise argparse.ArgumentTypeError("erasure counts must be in 1..16")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--counts",
        type=_parse_counts,
        default=tuple(range(1, 11)),
        help="comma-separated erasure counts (default: 1..10)",
    )
    parser.add_argument("--out", type=Path, help="write JSON here instead of stdout")
    args = parser.parse_args()

    payload = build_census(args.counts)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
