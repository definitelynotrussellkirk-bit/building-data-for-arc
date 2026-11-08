#!/usr/bin/env python3
"""Cheap source-bound probe for the task's global-frequency shortcut.

The probe deliberately uses an independent implementation of the selected law
and the rival, so it can compare a baseline generator and a proposed repair even
when neither module declares semantic hooks.  It reports per-example rival
agreement and every one-query rotation of each consecutive four-pair window.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Iterable

CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_grid(grid: object) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and non-empty")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid colors must be integer values in 0..9")
    return len(grid), width


def authority_output(grid: list[list[int]]) -> list[list[int]]:
    """Keep cells with a same-colour cardinal neighbour."""
    height, width = _validate_grid(grid)
    out = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            if any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == color
                for dr, dc in CARDINALS
            ):
                out[row][col] = color
    return out


def global_frequency_output(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: keep every cell whose colour occurs at least twice."""
    height, width = _validate_grid(grid)
    counts = Counter(value for row in grid for value in row if value != 0)
    return [
        [value if value != 0 and counts[value] >= 2 else 0 for value in row]
        for row in grid
    ]


def analyze_module(
    module: ModuleType | object,
    *,
    seed: int,
    per_band: int,
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, object]:
    if per_band < 4:
        raise ValueError("per_band must be at least 4 to inspect four-pair windows")
    report: dict[str, object] = {
        "seed": seed,
        "sample_indices": [0, per_band - 1],
        "per_band": per_band,
        "bands": {},
    }
    band_reports: dict[str, object] = report["bands"]  # type: ignore[assignment]
    for band in bands:
        pairs: list[dict[str, object]] = []
        accepted = 0
        rival_matches = 0
        for sample_index in range(per_band):
            grid = module.generate(seed, sample_index, difficulty=band)
            validator = getattr(module, "self_check", None)
            errors = validator(grid) if callable(validator) else []
            accepted += not errors
            output = authority_output(grid)
            rival = global_frequency_output(grid)
            rival_matches += rival == output
            pairs.append({"input": grid, "output": output, "rival": rival})

        ambiguous_rotations = 0
        rotations_checked = 0
        ambiguous_examples: list[dict[str, object]] = []
        for start in range(per_band - 3):
            window = pairs[start : start + 4]
            for query_index in range(4):
                rotations_checked += 1
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                query = window[query_index]
                rival_fits_demos = all(pair["rival"] == pair["output"] for pair in demos)
                rival_changes_query = query["rival"] != query["output"]
                if rival_fits_demos and rival_changes_query:
                    ambiguous_rotations += 1
                    if len(ambiguous_examples) < 10:
                        ambiguous_examples.append(
                            {
                                "start": start,
                                "demo_indices": [
                                    start + index for index in range(4) if index != query_index
                                ],
                                "query_index": start + query_index,
                            }
                        )
        band_reports[str(band)] = {
            "generated": len(pairs),
            "self_check_passed": accepted,
            "rival_matches": rival_matches,
            "rival_disagreements": len(pairs) - rival_matches,
            "rotations_checked": rotations_checked,
            "ambiguous_rotations": ambiguous_rotations,
            "ambiguous_examples": ambiguous_examples,
        }
    return report


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("generator_under_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=808217)
    parser.add_argument("--per-band", type=int, default=100)
    args = parser.parse_args()

    path = args.generator.resolve()
    module = load_module(path)
    report = analyze_module(module, seed=args.seed, per_band=args.per_band)
    report.update(
        {
            "schema": "8e8d21720efb-locality-shortcut-probe-v1",
            "task_id": "8e8d21720efb",
            "generator_path": str(path),
            "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "rival": "keep_nonzero_cells_whose_color_occurs_at_least_twice_globally",
        }
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
