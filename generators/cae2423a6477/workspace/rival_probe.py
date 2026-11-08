#!/usr/bin/env python3
"""Mine simple object-level rivals for ARC task cae2423a6477.

The repository semantic gate validates rivals that a generator already
*declares*.  This probe is deliberately independent of those declarations: it
checks a small fixed grammar of plausible object selectors against canonical
pairs, then asks whether each canonical-fitting selector survives complete
three-demonstration generated lessons.

A nonzero exit means at least one low-complexity rival still fits every example
in one or more sampled lessons.  The JSON output gives a deterministic witness
location for every rival that is refuted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Callable, Iterable

TASK_ID = "cae2423a6477"
BANDS = ("easy", "medium", "hard")
Coord = tuple[int, int]
Shape = set[Coord]
Grid = list[list[int]]
Selector = Callable[[dict], bool]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATOR = REPO_ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_LEDGER = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_generator(path: Path):
    path = path.resolve()
    suffix = hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(f"rival_probe_{suffix}", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_grid(rows) -> Grid:
    if rows and isinstance(rows[0], str):
        return [[int(value) for value in row] for row in rows]
    return [list(row) for row in rows]


def _canonical_pairs() -> list[dict[str, Grid]]:
    with CANONICAL_LEDGER.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row["test"]
            raw_pairs = list(row["train"]) + (
                [test] if isinstance(test, dict) else list(test)
            )
            return [
                {
                    "input": _parse_grid(pair["input"]),
                    "output": _parse_grid(pair["output"]),
                }
                for pair in raw_pairs
            ]
    raise RuntimeError(f"canonical task {TASK_ID} not found in {CANONICAL_LEDGER}")


def _components(grid: Grid, color: int = 3) -> list[Shape]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result: list[Shape] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = [start]
        while queue:
            row, col = queue.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def _bbox(cells: Iterable[Coord]) -> tuple[int, int, int, int]:
    cells = set(cells)
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _enclosed_holes(cells: Shape) -> list[Shape]:
    row1, col1, row2, col2 = _bbox(cells)
    height, width = row2 - row1 + 1, col2 - col1 + 1
    occupied = {(row - row1, col - col1) for row, col in cells}
    background = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in occupied
    }
    exterior: set[Coord] = set()
    queue: deque[Coord] = deque(
        cell
        for cell in background
        if cell[0] in {0, height - 1} or cell[1] in {0, width - 1}
    )
    exterior.update(queue)
    while queue:
        row, col = queue.popleft()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in background and neighbor not in exterior:
                exterior.add(neighbor)
                queue.append(neighbor)

    remaining = background - exterior
    holes: list[Shape] = []
    while remaining:
        start = remaining.pop()
        hole = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    hole.add(neighbor)
                    queue.append(neighbor)
        holes.append(hole)
    return holes


def _is_filled_rectangle(cells: Shape) -> bool:
    row1, col1, row2, col2 = _bbox(cells)
    return cells == {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
    }


def _describe(cells: Shape) -> dict:
    row1, col1, row2, col2 = _bbox(cells)
    holes = _enclosed_holes(cells)
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    return {
        "size": len(cells),
        "height": row2 - row1 + 1,
        "width": col2 - col1 + 1,
        "has_hole": bool(holes),
        "closed_unbranched_loop": bool(holes)
        and all(
            sum((row + dr, col + dc) in cells for dr, dc in neighbors) == 2
            for row, col in cells
        ),
        "rectangular_hole": any(_is_filled_rectangle(hole) for hole in holes),
    }


def _paint_matching(grid: Grid, selector: Selector) -> Grid:
    output = [list(row) for row in grid]
    for cells in _components(grid):
        if selector(_describe(cells)):
            for row, col in cells:
                output[row][col] = 7
    return output


CANDIDATES: dict[str, Selector] = {
    "any_object_with_hole": lambda item: item["has_hole"],
    "closed_unbranched_loop": lambda item: item["closed_unbranched_loop"],
    "rectangular_hole": lambda item: item["rectangular_hole"],
    "size_at_least_8": lambda item: item["size"] >= 8,
    "bbox_at_least_3x3": lambda item: item["height"] >= 3
    and item["width"] >= 3,
}


def probe_generator(generator_path: Path, *, seeds_per_band: int = 12) -> dict:
    """Return deterministic rival-survival evidence for one generator file."""

    if seeds_per_band < 1:
        raise ValueError("seeds_per_band must be positive")
    generator_path = Path(generator_path).resolve()
    generator = _load_generator(generator_path)
    canonical = _canonical_pairs()
    examples_needed = int(getattr(generator, "EXAMPLES_NEEDED", 3))
    candidate_rows: dict[str, dict] = {}

    for name, selector in CANDIDATES.items():
        canonical_mismatches = [
            index
            for index, pair in enumerate(canonical)
            if _paint_matching(pair["input"], selector) != pair["output"]
        ]
        canonical_fit = not canonical_mismatches
        surviving_windows = 0
        first_refutation = None
        total_windows = len(BANDS) * seeds_per_band

        if canonical_fit:
            for band in BANDS:
                for seed in range(seeds_per_band):
                    survives = True
                    for sample_index in range(examples_needed):
                        grid = generator.generate(
                            seed,
                            sample_index,
                            difficulty=band,
                        )
                        target = generator.rule_mirror(grid)
                        if _paint_matching(grid, selector) != target:
                            survives = False
                            if first_refutation is None:
                                first_refutation = {
                                    "difficulty": band,
                                    "seed": seed,
                                    "sample_index": sample_index,
                                    "scene_profile": generator.observe_overrides(grid).get(
                                        "scene_profile"
                                    ),
                                }
                            break
                    if survives:
                        surviving_windows += 1

        candidate_rows[name] = {
            "canonical_fit": canonical_fit,
            "canonical_mismatch_indices": canonical_mismatches,
            "lesson_windows": total_windows if canonical_fit else 0,
            "surviving_windows": surviving_windows,
            "first_refutation": first_refutation,
        }

    surviving_rivals = sorted(
        name
        for name, row in candidate_rows.items()
        if row["canonical_fit"] and row["surviving_windows"] > 0
    )
    return {
        "schema": "cae2423a6477-rival-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_version": str(getattr(generator, "VERSION", "unknown")),
        "seeds_per_band": seeds_per_band,
        "candidates": candidate_rows,
        "surviving_rivals": surviving_rivals,
        "passed": not surviving_rivals,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=DEFAULT_GENERATOR,
        help="generator.py to probe (default: selected task generator)",
    )
    parser.add_argument(
        "--seeds-per-band",
        type=int,
        default=12,
        help="complete lesson windows sampled in each difficulty band",
    )
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    parser.add_argument(
        "--allow-survivors",
        action="store_true",
        help="report surviving rivals without returning a failing exit status",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = probe_generator(args.generator, seeds_per_band=args.seeds_per_band)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["passed"] or args.allow_survivors else 1


if __name__ == "__main__":
    raise SystemExit(main())
