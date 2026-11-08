#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK_ID = "41ea3019baeb"
BANDS = ("easy", "medium", "hard")
DRAWS_PER_BAND = 100
BASE_SEED = 50_000


def load_generator(repo_root: Path):
    source = repo_root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def turn(value: int, dr: int, dc: int) -> tuple[int, int]:
    if value == 6:
        return {
            (0, 1): (-1, 0),
            (0, -1): (1, 0),
            (-1, 0): (0, 1),
            (1, 0): (0, -1),
        }[(dr, dc)]
    if value == 7:
        return {
            (0, 1): (1, 0),
            (0, -1): (-1, 0),
            (-1, 0): (0, -1),
            (1, 0): (0, 1),
        }[(dr, dc)]
    return dr, dc


def trace_interactions(grid, start_row: int, start_col: int):
    height, width = len(grid), len(grid[0])
    row, col, dr, dc = start_row, start_col, 0, 1
    interactions = []
    path = []
    for _ in range(height * width * 8):
        next_row, next_col = row + dr, col + dc
        if not (0 <= next_row < height and 0 <= next_col < width):
            break
        value = grid[next_row][next_col]
        if value in (5, 6, 7):
            interactions.append((next_row, next_col, value))
        if value == 5 or (value != 0 and value not in (6, 7)):
            break
        path.append((next_row, next_col))
        dr, dc = turn(value, dr, dc)
        row, col = next_row, next_col
    return path, interactions


def straight_right_rival(grid):
    """Paint rightward through zeroes; treat all nonzero cells as blockers."""
    output = [list(row) for row in grid]
    width = len(grid[0])
    emitters = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    for row, col in emitters:
        for next_col in range(col + 1, width):
            if grid[row][next_col] != 0:
                break
            output[row][next_col] = 8
    return output


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3] / "repo"
    out_dir = Path(__file__).resolve().parent
    generator, source = load_generator(repo_root)
    counts = {}
    selected = None

    for band_index, band in enumerate(BANDS):
        stats = Counter()
        for index in range(DRAWS_PER_BAND):
            seed = BASE_SEED + 10_000 * band_index + index
            grid = generator.generate(seed, index, difficulty=band)
            errors = generator.self_check(grid)
            emitters = [
                (row, col)
                for row, values in enumerate(grid)
                for col, value in enumerate(values)
                if value == 2
            ]
            mirrors = [
                (row, col, value)
                for row, values in enumerate(grid)
                for col, value in enumerate(values)
                if value in (5, 6, 7)
            ]
            interactions = []
            for emitter in emitters:
                _path, touched = trace_interactions(grid, *emitter)
                interactions.extend(touched)

            stats["draws"] += 1
            stats["self_check_pass"] += not errors
            stats["zero_mirror_interactions"] += not interactions
            stats["at_least_one_mirror_interaction"] += bool(interactions)
            stats["at_least_two_mirror_interactions"] += len(interactions) >= 2

            if (
                selected is None
                and band == "easy"
                and len(mirrors) >= 2
                and not interactions
                and not errors
            ):
                selected = {
                    "band": band,
                    "seed": seed,
                    "sample_index": index,
                    "input": grid,
                    "emitters": emitters,
                    "mirrors": mirrors,
                    "validator_errors": errors,
                    "straight_right_rival_output": straight_right_rival(grid),
                }
        counts[band] = dict(stats)

    if selected is None:
        raise RuntimeError("no zero-interaction two-mirror witness found")

    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    report = {
        "schema": "arc-audit-mirror-interaction-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "sample_recipe": {
            "bands": list(BANDS),
            "draws_per_band": DRAWS_PER_BAND,
            "seed": "50000 + 10000*band_index + index",
            "sample_index": "index",
        },
        "counts": counts,
        "selected_witness": {
            key: value
            for key, value in selected.items()
            if key not in {"input", "straight_right_rival_output"}
        },
    }
    (out_dir / "probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "input.json").write_text(
        json.dumps(selected["input"], indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "rival.json").write_text(
        json.dumps(selected["straight_right_rival_output"], indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
