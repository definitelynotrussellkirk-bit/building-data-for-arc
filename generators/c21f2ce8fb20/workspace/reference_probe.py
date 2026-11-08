"""Independent oracle and curriculum probe for generator c21f2ce8fb20.

This module deliberately does not import production helpers from generator.py.
It supplies task-local tests and future reviewers with a repeatable way to:

* read every canonical pair,
* recover 4-connected 0/2 chambers,
* compute the intended max-red-chamber answer,
* score three plausible rival rules, and
* audit deterministic generated coverage by difficulty band.

The Python oracle is supplementary evidence.  ``--racket`` uses the repository's
selected canonical Racket authority and fails rather than silently falling back.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Callable, Iterable

TASK_ID = "c21f2ce8fb20"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

Grid = list[list[int]]
Cell = tuple[int, int]


def load_generator(path: str | os.PathLike[str] | None = None):
    """Load the selected source file without relying on package mapping."""
    source = Path(path or GENERATOR_PATH).resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(f"canonical task {TASK_ID!r} not found")


def _normalize_grid(grid) -> Grid:
    if not isinstance(grid, list) or not grid:
        raise ValueError("expected non-empty grid")
    normalized: Grid = []
    for raw_row in grid:
        if isinstance(raw_row, str):
            raw_row = [int(char) for char in raw_row if not char.isspace()]
        if not isinstance(raw_row, list) or not raw_row:
            raise ValueError("expected non-empty rows")
        if any(type(value) is not int or not 0 <= value <= 9 for value in raw_row):
            raise ValueError("expected integer ARC colors")
        normalized.append(list(raw_row))
    if len({len(row) for row in normalized}) != 1:
        raise ValueError("ragged canonical grid")
    return normalized


def canonical_pairs() -> list[dict]:
    """Return normalized train+test pairs with stable identities."""
    row = canonical_row()
    result: list[dict] = []
    for split in ("train", "test"):
        pairs = row.get(split, [])
        if isinstance(pairs, dict):
            pairs = [pairs]
        for index, pair in enumerate(pairs):
            result.append(
                {
                    "input": _normalize_grid(pair["input"]),
                    "output": _normalize_grid(pair["output"]),
                    "split": split,
                    "pair_index": index,
                }
            )
    return result


def regions(grid: Grid) -> list[list[Cell]]:
    """Find 4-connected components containing only authority-passable 0/2."""
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    found: list[list[Cell]] = []
    for start_r in range(height):
        for start_c in range(width):
            start = (start_r, start_c)
            if start in seen or grid[start_r][start_c] not in (0, 2):
                continue
            queue = deque([start])
            seen.add(start)
            component: list[Cell] = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    point = (nr, nc)
                    if point in seen or grid[nr][nc] not in (0, 2):
                        continue
                    seen.add(point)
                    queue.append(point)
            found.append(sorted(component))
    return found


def chamber_stats(grid: Grid) -> list[dict]:
    stats = []
    for cells in regions(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        stats.append(
            {
                "cells": cells,
                "seeds": sum(grid[r][c] == 2 for r, c in cells),
                "area": len(cells),
                "top_left": min(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            }
        )
    return stats


def _cell_string(cell: Cell) -> str:
    # Racket's `(format "~a" (first sorted-cells))` prints a two-item list.
    return f"({cell[0]} {cell[1]})"


def _paint(grid: Grid, cells: Iterable[Cell]) -> Grid:
    out = [[0 for _ in row] for row in grid]
    for r, c in cells:
        out[r][c] = 8
    return out


def _authority_order_key(stat: dict):
    # Max seeds, then max area, then lexicographically smallest printed cell.
    return (-stat["seeds"], -stat["area"], _cell_string(stat["top_left"]))


def intended_output(grid: Grid) -> Grid:
    stats = chamber_stats(grid)
    if not stats:
        return [[0 for _ in row] for row in grid]
    return _paint(grid, min(stats, key=_authority_order_key)["cells"])


def prefer_exactly_three_output(grid: Grid) -> Grid:
    """Plausible canonical shortcut: prefer 3 seeds, then 2, then max."""
    stats = chamber_stats(grid)
    if not stats:
        return [[0 for _ in row] for row in grid]
    three = [item for item in stats if item["seeds"] == 3]
    two = [item for item in stats if item["seeds"] == 2]
    pool = three or two or stats
    return _paint(grid, min(pool, key=_authority_order_key)["cells"])


def largest_room_output(grid: Grid) -> Grid:
    stats = chamber_stats(grid)
    if not stats:
        return [[0 for _ in row] for row in grid]
    chosen = min(
        stats,
        key=lambda item: (-item["area"], _cell_string(item["top_left"])),
    )
    return _paint(grid, chosen["cells"])


def densest_room_output(grid: Grid) -> Grid:
    stats = chamber_stats(grid)
    if not stats:
        return [[0 for _ in row] for row in grid]
    chosen = min(
        stats,
        key=lambda item: (
            -(item["seeds"] / item["area"]),
            -item["seeds"],
            -item["area"],
            _cell_string(item["top_left"]),
        ),
    )
    return _paint(grid, chosen["cells"])


RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "prefer_exactly_three": prefer_exactly_three_output,
    "largest_room": largest_room_output,
    "densest_room": densest_room_output,
}


def observed(grid: Grid) -> dict[str, int]:
    stats = chamber_stats(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_chambers": len(stats),
        "winner_seeds": max((item["seeds"] for item in stats), default=0),
    }


def winner_quadrant(grid: Grid) -> tuple[int, int]:
    stats = chamber_stats(grid)
    if not stats:
        raise ValueError("grid has no chambers")
    chosen = min(stats, key=_authority_order_key)
    r, c = chosen["top_left"]
    return (int(r >= len(grid) / 2), int(c >= len(grid[0]) / 2))


def _blank(height: int, width: int) -> Grid:
    return [[5] * width for _ in range(height)]


def _carve(grid: Grid, box: tuple[int, int, int, int], seeds: Iterable[Cell]) -> None:
    r0, c0, r1, c1 = box
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = 0
    for r, c in seeds:
        if not (r0 <= r <= r1 and c0 <= c <= c1):
            raise ValueError("seed outside witness chamber")
        grid[r][c] = 2


def count_above_three_witness() -> Grid:
    """Exact disagreement: intended 4-seed room versus canonical-fit 3 shortcut."""
    grid = _blank(10, 13)
    _carve(grid, (1, 1, 3, 4), ((1, 1), (1, 2), (2, 1), (3, 4)))
    _carve(grid, (1, 7, 3, 11), ((1, 7), (2, 8), (3, 11)))
    _carve(grid, (6, 1, 8, 4), ((7, 2),))
    _carve(grid, (6, 7, 8, 11), ((7, 9),))
    return grid


def size_density_witness() -> Grid:
    """Intended winner is neither the largest room nor the highest-density room."""
    grid = _blank(10, 14)
    _carve(grid, (1, 1, 3, 4), ((1, 1), (2, 2), (3, 4)))  # 3/12 winner
    _carve(grid, (1, 7, 2, 9), ((1, 7), (2, 9)))          # 2/6 denser
    _carve(grid, (5, 7, 8, 12), ((7, 10),))               # 1/24 larger
    _carve(grid, (6, 1, 8, 4), ((7, 2),))                 # 1/12
    return grid


def _signature(grid: Grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def audit(module, *, count: int = 100) -> tuple[dict, list[Grid]]:
    canonical = canonical_pairs()
    canonical_errors = [module.self_check(pair["input"]) for pair in canonical]
    canonical_matches = [intended_output(pair["input"]) == pair["output"] for pair in canonical]
    shortcut_matches = [prefer_exactly_three_output(pair["input"]) == pair["output"] for pair in canonical]

    by_band: dict[str, dict] = {}
    retained: list[Grid] = [pair["input"] for pair in canonical]
    all_signatures: set[str] = set()
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        counter = Counter()
        shapes: set[tuple[int, int]] = set()
        maxima: set[int] = set()
        chamber_counts: set[int] = set()
        quadrants: set[tuple[int, int]] = set()
        profiles: set[str] = set()
        signatures: set[str] = set()
        for index in range(count):
            seed = 20261003 + band_index * 100_000 + index
            sample_index = index * 7 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            counter["samples"] += 1
            counter["self_check_errors"] += bool(module.self_check(grid, difficulty=band))
            counter["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            out = intended_output(grid)
            counter["prefer_three_disagreements"] += out != prefer_exactly_three_output(grid)
            counter["largest_disagreements"] += out != largest_room_output(grid)
            counter["densest_disagreements"] += out != densest_room_output(grid)
            stats = observed(grid)
            shapes.add((stats["grid_h"], stats["grid_w"]))
            maxima.add(stats["winner_seeds"])
            chamber_counts.add(stats["n_chambers"])
            quadrants.add(winner_quadrant(grid))
            profiles.add(str(module.schedule_profile(seed, sample_index, band)))
            signatures.add(_signature(grid))
            if index < 8:
                retained.append(deepcopy(grid))
        all_signatures.update(signatures)
        by_band[str(band)] = {
            **dict(counter),
            "distinct_inputs": len(signatures),
            "shapes": sorted([list(shape) for shape in shapes]),
            "winner_seeds": sorted(maxima),
            "n_chambers": sorted(chamber_counts),
            "winner_quadrants": sorted([list(item) for item in quadrants]),
            "schedule_profiles": sorted(profiles),
        }

    report = {
        "schema": "c21f2ce8fb20-independent-audit-v1",
        "task_id": TASK_ID,
        "version": getattr(module, "VERSION", None),
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical": {
            "pairs": len(canonical),
            "self_check_errors": canonical_errors,
            "intended_matches": canonical_matches,
            "prefer_exactly_three_matches": shortcut_matches,
        },
        "by_band": by_band,
        "distinct_inputs_all_bands": len(all_signatures),
        "explicit_witnesses": {
            "count_above_three": {
                "input": count_above_three_witness(),
                "intended": intended_output(count_above_three_witness()),
                "prefer_exactly_three": prefer_exactly_three_output(count_above_three_witness()),
            },
            "size_density": {
                "input": size_density_witness(),
                "intended": intended_output(size_density_witness()),
                "largest_room": largest_room_output(size_density_witness()),
                "densest_room": densest_room_output(size_density_witness()),
            },
        },
        "sampling_design": (
            "Deterministic crossed-band census. Counts are descriptive, not an "
            "estimate from independent random samples. Python is supplementary "
            "to the selected Racket authority."
        ),
    }
    return report, retained


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Execute the selected canonical Racket authority; never fall back."""
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog

    catalog = Catalog(ROOT)
    receipt = catalog.apply(TASK_ID, grids, reference="canonical", timeout=300)
    problems = [item for item in receipt["results"] if item.get("error") is not None]
    if problems:
        raise RuntimeError(f"Racket apply failed: {problems[:2]}")
    return [item["output"] for item in receipt["results"]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100, help="samples per band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require selected Racket parity")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")

    module = load_generator(args.generator)
    report, grids = audit(module, count=args.count)
    failed = any(report["canonical"]["self_check_errors"])
    failed = failed or not all(report["canonical"]["intended_matches"])
    for band in report["by_band"].values():
        failed = failed or bool(band["self_check_errors"] or band["nondeterministic"])
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        try:
            expected = [intended_output(grid) for grid in grids]
            actual = racket_outputs(grids)
            mismatches = [index for index, (left, right) in enumerate(zip(actual, expected)) if left != right]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(actual),
                "mismatches": mismatches,
            }
            failed = failed or bool(mismatches)
        except Exception as exc:  # CLI records unavailable dependency as evidence.
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            failed = True

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"canonical": report["canonical"], "by_band": report["by_band"], "racket": report["racket"]}, indent=2))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
