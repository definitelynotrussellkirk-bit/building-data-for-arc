#!/usr/bin/env python3
"""Reproduce the numeric-minimum teaching shortcut for f6b13494be37.

Run from the packet's ``repo`` directory with::

    PYTHONPATH=shared/runtime:. python3 \
      ../checks/audit/f6b13494be37/probe_numeric_min_shortcut.py \
      --out ../checks/audit/f6b13494be37/probe-replay.json

The probe never changes the audited generator. It compares the generator's
Python rule mirror with one explicit rival: choose the numerically smallest
color common to every notch, instead of the globally rarest common color.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "f6b13494be37"
MODULE = f"generators.{TASK_ID}.generator"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rival(module: Any, grid: list[list[int]]) -> list[list[int]]:
    analysis = module._analyze(grid)  # task-local audit intentionally inspects semantics
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    marker = min(analysis["common"])
    return module._fill_selected(grid, marker)


def _pair(module: Any, *, band: str, seed: int, sample_index: int) -> dict[str, Any]:
    grid = module.generate(seed, sample_index, difficulty=band)
    analysis = module._analyze(grid)
    truth = module.rule_mirror(grid)
    rival = _rival(module, grid)
    return {
        "sample_index": sample_index,
        "input": grid,
        "truth": truth,
        "rival": rival,
        "common_colors": sorted(analysis["common"]),
        "true_marker": analysis["marker"],
        "rival_marker": min(analysis["common"]),
        "rival_matches": rival == truth,
    }


def run(seed_start: int, seed_stop: int) -> dict[str, Any]:
    module = importlib.import_module(MODULE)
    source = Path(module.__file__).resolve()
    stats: dict[str, dict[str, int]] = {}
    examples: list[dict[str, Any]] = []

    for band in ("easy", "medium", "hard"):
        band_stats = {
            "production_windows": 0,
            "production_ambiguous": 0,
            "rotations": 0,
            "ambiguous_rotations": 0,
        }
        for seed in range(seed_start, seed_stop):
            for cyclic_start in (0, 1, 2):
                pairs = [
                    _pair(
                        module,
                        band=band,
                        seed=seed,
                        sample_index=cyclic_start + offset,
                    )
                    for offset in range(4)
                ]
                band_stats["production_windows"] += 1
                if all(pair["rival_matches"] for pair in pairs[:3]) and not pairs[3]["rival_matches"]:
                    band_stats["production_ambiguous"] += 1
                    if len(examples) < 12:
                        examples.append(
                            {
                                "scope": "production",
                                "band": band,
                                "seed": seed,
                                "cyclic_start": cyclic_start,
                                "query_index": 3,
                                "sample_indices": [p["sample_index"] for p in pairs],
                                "query_common_colors": pairs[3]["common_colors"],
                                "query_true_marker": pairs[3]["true_marker"],
                                "query_rival_marker": pairs[3]["rival_marker"],
                            }
                        )
                for query_index, query in enumerate(pairs):
                    band_stats["rotations"] += 1
                    demos = [p for i, p in enumerate(pairs) if i != query_index]
                    if all(pair["rival_matches"] for pair in demos) and not query["rival_matches"]:
                        band_stats["ambiguous_rotations"] += 1
                        if len(examples) < 12:
                            examples.append(
                                {
                                    "scope": "rotation",
                                    "band": band,
                                    "seed": seed,
                                    "cyclic_start": cyclic_start,
                                    "query_index": query_index,
                                    "sample_indices": [p["sample_index"] for p in pairs],
                                    "query_common_colors": query["common_colors"],
                                    "query_true_marker": query["true_marker"],
                                    "query_rival_marker": query["rival_marker"],
                                }
                            )
        stats[band] = band_stats

    # Retain the smallest fixed witness used for the Racket confirmation.
    witness_pairs = [
        _pair(module, band="easy", seed=1, sample_index=index) for index in range(4)
    ]
    query_index = 2
    witness = {
        "band": "easy",
        "seed": 1,
        "sample_indices": [0, 1, 2, 3],
        "query_index": query_index,
        "demos_fit_rival": all(
            pair["rival_matches"] for i, pair in enumerate(witness_pairs) if i != query_index
        ),
        "query_rival_differs": not witness_pairs[query_index]["rival_matches"],
        "query_common_colors": witness_pairs[query_index]["common_colors"],
        "query_true_marker": witness_pairs[query_index]["true_marker"],
        "query_rival_marker": witness_pairs[query_index]["rival_marker"],
        "query_input": witness_pairs[query_index]["input"],
        "query_truth": witness_pairs[query_index]["truth"],
        "query_rival": witness_pairs[query_index]["rival"],
    }
    return {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": _sha256(source),
        "rival": "choose the numerically smallest color common to every notch",
        "seed_range": [seed_start, seed_stop - 1],
        "cyclic_starts": [0, 1, 2],
        "pairs_per_window": 4,
        "stats": stats,
        "examples": examples,
        "fixed_witness": witness,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-stop", type=int, default=50)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seed_stop <= args.seed_start:
        parser.error("--seed-stop must exceed --seed-start")
    report = run(args.seed_start, args.seed_stop)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "stats": report["stats"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
