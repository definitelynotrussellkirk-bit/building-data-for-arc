#!/usr/bin/env python3
"""Replay canonical shortcut-fit and generated lesson-identifiability checks.

The probe intentionally discovers rivals from the generator declarations rather
than maintaining a second name list.  It is lightweight enough to run after any
future edit to ``generator.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

WORKSPACE = Path(__file__).resolve().parent
TASK_HOME = WORKSPACE.parent
REPO_ROOT = TASK_HOME.parents[1]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "323fded12174"
BANDS = ("easy", "medium", "hard")


def _load_generator():
    source = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"workspace_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _occupancy(row: list[int]) -> int:
    return sum(value != 0 for value in row)


def _intended(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in sorted(grid, key=_occupancy, reverse=True)]


def run_probe(*, samples_per_band: int = 12, seed_base: int = 323) -> dict[str, Any]:
    """Return a JSON-safe report for all declared rivals and cyclic lessons."""
    if samples_per_band < 3:
        raise ValueError("samples_per_band must be at least 3 for two demos plus query")

    generator, source = _load_generator()
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))

    shortcut_report: dict[str, dict[str, Any]] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in canonical]
        shortcut_report[name] = {
            "canonical_pairs": len(matches),
            "matching_pairs": sum(matches),
            "fits_all_canonical": bool(matches) and all(matches),
        }

    grids_by_band: dict[str, list[list[list[int]]]] = {}
    invalid_inputs: list[dict[str, Any]] = []
    rival_agreements: list[dict[str, Any]] = []
    witness_misses: list[dict[str, Any]] = []
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()

    for band_index, band in enumerate(BANDS):
        grids: list[list[list[int]]] = []
        for sample in range(samples_per_band):
            seed = seed_base + band_index * 100_003 + sample * 997
            sample_index = band_index * samples_per_band + sample
            grid = generator.generate(seed, sample_index, difficulty=band)
            grids.append(grid)
            unique_inputs.add(tuple(tuple(row) for row in grid))

            errors = generator.self_check(grid, difficulty=band)
            if errors:
                invalid_inputs.append({
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "errors": errors,
                })

            expected = _intended(grid)
            for name, rival in generator.LESSON_COMPETITORS.items():
                if rival(grid) == expected:
                    rival_agreements.append({
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "rival": name,
                    })
            for name, witness in generator.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    witness_misses.append({
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "witness": name,
                    })
        grids_by_band[band] = grids

    unidentifiable: list[dict[str, Any]] = []
    windows_checked = 0
    examples = int(generator.EXAMPLES_NEEDED)
    for band, grids in grids_by_band.items():
        for start in range(len(grids)):
            demos = []
            for offset in range(examples):
                grid = grids[(start + offset) % len(grids)]
                demos.append({"input": grid, "output": _intended(grid)})
            query = {"input": grids[(start + examples) % len(grids)]}
            reasons = generator.lesson_identifiable(demos, query)
            windows_checked += 1
            if reasons:
                unidentifiable.append({"band": band, "start": start, "reasons": reasons})

    return {
        "schema": "323fded12174-rival-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": generator.RULE_HASH,
        "samples_per_band": samples_per_band,
        "seed_base": seed_base,
        "canonical_shortcuts": shortcut_report,
        "generated": {
            "samples": samples_per_band * len(BANDS),
            "unique_inputs": len(unique_inputs),
            "invalid_inputs": invalid_inputs,
            "rival_agreements": rival_agreements,
            "witness_misses": witness_misses,
        },
        "lessons": {
            "examples_per_lesson": examples,
            "assembly": "all cyclic starts within each difficulty band",
            "windows_checked": windows_checked,
            "unidentifiable_windows": unidentifiable,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-per-band", type=int, default=12)
    parser.add_argument("--seed-base", type=int, default=323)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(samples_per_band=args.samples_per_band, seed_base=args.seed_base)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    failed = (
        any(not row["fits_all_canonical"] for row in report["canonical_shortcuts"].values())
        or bool(report["generated"]["invalid_inputs"])
        or bool(report["generated"]["rival_agreements"])
        or bool(report["generated"]["witness_misses"])
        or bool(report["lessons"]["unidentifiable_windows"])
    )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
