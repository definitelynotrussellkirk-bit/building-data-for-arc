#!/usr/bin/env python3
"""Reproduce the two adversarial curriculum shortcuts assigned in this review.

This probe is read-only with respect to audited generators.  It checks each
shortcut against all canonical pairs and 500 default draws per difficulty band,
then retains one counterexample where the shortcut diverges from the task rule.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

def _find_packet_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "ASSIGNMENT.json").is_file() and (candidate / "repo").is_dir():
            return candidate
    raise FileNotFoundError("could not locate packet root from probe path")


PACKET_ROOT = _find_packet_root(Path(__file__).resolve().parent)
REPO = PACKET_ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_pairs(task_id: str) -> list[dict[str, Any]]:
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return [*row.get("train", []), *row.get("test", [])]
    raise KeyError(task_id)


def differing_cells(left, right) -> list[list[int]]:
    return [
        [r, c]
        for r, (lrow, rrow) in enumerate(zip(left, right))
        for c, (lv, rv) in enumerate(zip(lrow, rrow))
        if lv != rv
    ]


def audit_vertical_spans() -> dict[str, Any]:
    task_id = "3f93d8860778"
    gen, source = load_generator(task_id)

    def shortcut(grid):
        # Correlation exploit: all generated guard scenes contain a triple, and
        # all triple-free scenes contain only valid pairs.
        info = gen._analysis(grid)
        has_triple = any(
            decoy["kind"] == "same_colour_triple" for decoy in info["decoys"]
        )
        return (
            gen.rule_mirror(grid)
            if has_triple
            else gen._fill_every_active_column(grid)
        )

    canonical = canonical_pairs(task_id)
    canonical_fit = [shortcut(pair["input"]) == pair["output"] for pair in canonical]

    generated_total = 0
    generated_fit = 0
    by_band: dict[str, dict[str, int]] = {}
    for band in (None, "easy", "medium", "hard"):
        label = "default" if band is None else band
        fits = 0
        for index in range(500):
            grid = gen.generate(100_000 + index, index, difficulty=band)
            fits += shortcut(grid) == gen.rule_mirror(grid)
        by_band[label] = {"fit": fits, "total": 500}
        generated_fit += fits
        generated_total += 500

    # Remove the bundled singleton and triple from a generated guard scene.
    # The remaining mismatched pair is legal under the written rule but outside
    # this generator's intentionally bundled grammar.
    counterexample = gen.generate(4242, 1, difficulty="medium")
    analysis = gen._analysis(counterexample)
    counterexample = [row[:] for row in counterexample]
    removed: list[dict[str, Any]] = []
    for decoy in analysis["decoys"]:
        if decoy["kind"] == "mismatched_pair":
            continue
        removed.append(
            {
                "kind": decoy["kind"],
                "column": decoy["column"],
                "rows": list(decoy["rows"]),
            }
        )
        for row in decoy["rows"]:
            counterexample[row][decoy["column"]] = 0
    expected = gen.rule_mirror(counterexample)
    got = shortcut(counterexample)

    return {
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "shortcut": (
            "If any same-colour triple exists, apply the exact rule; otherwise "
            "fill between extrema in every column with at least two marks."
        ),
        "canonical_fit": {"fit": sum(canonical_fit), "total": len(canonical_fit)},
        "generated_fit": {
            "fit": generated_fit,
            "total": generated_total,
            "by_band": by_band,
        },
        "counterexample": {
            "construction": "generated seed=4242,index=1, then remove singleton and triple guards",
            "removed": removed,
            "analysis_errors": gen._analysis(counterexample)["errors"],
            "self_check_findings": gen.self_check(counterexample),
            "input": counterexample,
            "expected": expected,
            "shortcut_output": got,
            "differing_cells": differing_cells(expected, got),
        },
    }


def audit_seeded_rooms() -> dict[str, Any]:
    task_id = "d8ce64d73f8a"
    gen, source = load_generator(task_id)

    def shortcut(grid):
        # Correlation exploit: generated non-largest seeds always occupy the
        # largest non-main chamber, never one of the smaller pockets.
        parts = gen._regions(grid)
        seed = gen._seed_cell(grid)
        seed_part = next(part for part in parts if seed in part)
        main = max(parts, key=lambda cells: (len(cells), tuple(sorted(cells))))
        if seed_part == main:
            target = main
        else:
            target = max(
                (part for part in parts if part != main),
                key=lambda cells: (len(cells), tuple(sorted(cells))),
            )
        return gen._paint(grid, target)

    canonical = canonical_pairs(task_id)
    canonical_fit = [shortcut(pair["input"]) == pair["output"] for pair in canonical]

    generated_total = 0
    generated_fit = 0
    by_band: dict[str, dict[str, int]] = {}
    for band in (None, "easy", "medium", "hard"):
        label = "default" if band is None else band
        fits = 0
        for index in range(500):
            grid = gen.generate(200_000 + index, index, difficulty=band)
            fits += shortcut(grid) == gen.rule_mirror(grid)
        by_band[label] = {"fit": fits, "total": 500}
        generated_fit += fits
        generated_total += 500

    failure_indices = [index for index, fits in enumerate(canonical_fit) if not fits]
    index = failure_indices[0]
    pair = canonical[index]
    expected = pair["output"]
    got = shortcut(pair["input"])
    stats = gen._analysis(pair["input"])

    return {
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "shortcut": (
            "Paint the largest chamber when the seed is in it; otherwise paint "
            "the largest non-main chamber, ignoring which non-main chamber holds the seed."
        ),
        "canonical_fit": {
            "fit": sum(canonical_fit),
            "total": len(canonical_fit),
            "failure_indices": failure_indices,
        },
        "generated_fit": {
            "fit": generated_fit,
            "total": generated_total,
            "by_band": by_band,
        },
        "counterexample": {
            "construction": f"canonical pair index {index}",
            "self_check_findings": gen.self_check(pair["input"]),
            "room_sizes": [len(part) for part in stats["parts"]],
            "seed_room_size": len(stats["seed_part"]),
            "input": pair["input"],
            "expected": expected,
            "shortcut_output": got,
            "differing_cells": differing_cells(expected, got),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "schema": "arcpuzzles-assigned-audit-shortcuts-v1",
        "audits": [audit_vertical_spans(), audit_seeded_rooms()],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for audit in result["audits"]:
        print(
            audit["task_id"],
            "generated",
            f"{audit['generated_fit']['fit']}/{audit['generated_fit']['total']}",
            "canonical",
            f"{audit['canonical_fit']['fit']}/{audit['canonical_fit']['total']}",
            "counterexample differences",
            len(audit["counterexample"]["differing_cells"]),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
