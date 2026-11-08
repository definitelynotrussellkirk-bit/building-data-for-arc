"""Independent semantic probe for task 83efd4fcb4f4.

This module deliberately does not import the production generator.  It gives
reviewers a small Python oracle, structural observations, and finite rival
rules that can be run against canonical or generated inputs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Sequence

Grid = Sequence[Sequence[int]]
Point = tuple[int, int]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _rectangular(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
    )


def true_centers(grid: Grid) -> list[Point]:
    """Return zero cells whose four cardinal neighbours are all color 3."""
    if not _rectangular(grid):
        return []
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0
        and all(grid[r + dr][c + dc] == 3 for dr, dc in _CARDINAL)
    ]


def rule_output(grid: Grid) -> list[list[int]]:
    """Independent mirror of the canonical local rule."""
    out = [list(row) for row in grid]
    for r, c in true_centers(grid):
        out[r][c] = 8
    return out


def cardinal_three_count(grid: Grid, r: int, c: int) -> int:
    h, w = len(grid), len(grid[0])
    return sum(
        0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 3
        for dr, dc in _CARDINAL
    )


def has_three_arm_decoy(grid: Grid) -> bool:
    if not _rectangular(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(
        grid[r][c] == 0 and cardinal_three_count(grid, r, c) == 3
        for r in range(1, h - 1)
        for c in range(1, w - 1)
    )


def has_diagonal_decoy(grid: Grid) -> bool:
    if not _rectangular(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(
        grid[r][c] == 0
        and all(grid[r + dr][c + dc] == 3 for dr, dc in _DIAGONAL)
        and cardinal_three_count(grid, r, c) < 4
        for r in range(1, h - 1)
        for c in range(1, w - 1)
    )


def arm_cells(center: Point) -> set[Point]:
    r, c = center
    return {(r + dr, c + dc) for dr, dc in _CARDINAL}


def has_shared_arm_targets(grid: Grid) -> bool:
    centers = true_centers(grid)
    return any(
        arm_cells(left) & arm_cells(right)
        for index, left in enumerate(centers)
        for right in centers[index + 1 :]
    )


def has_boundary_target(grid: Grid) -> bool:
    if not _rectangular(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(min(r, c, h - 1 - r, w - 1 - c) == 1 for r, c in true_centers(grid))


def distractor_components(grid: Grid) -> list[list[tuple[int, int, int]]]:
    """4-connected components formed by colors 6 and 7 together."""
    if not _rectangular(grid):
        return []
    h, w = len(grid), len(grid[0])
    seen: set[Point] = set()
    components: list[list[tuple[int, int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (6, 7) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            component: list[tuple[int, int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc, int(grid[rr][cc])))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] in (6, 7)
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def at_least_three_arms_rival(grid: Grid) -> list[list[int]]:
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and cardinal_three_count(grid, r, c) >= 3:
                out[r][c] = 8
    return out


def cardinal_or_diagonal_rival(grid: Grid) -> list[list[int]]:
    out = rule_output(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and all(
                grid[r + dr][c + dc] == 3 for dr, dc in _DIAGONAL
            ):
                out[r][c] = 8
    return out


def separated_targets_only_rival(grid: Grid) -> list[list[int]]:
    centers = true_centers(grid)
    out = [list(row) for row in grid]
    for center in centers:
        if not any(
            arm_cells(center) & arm_cells(other)
            for other in centers
            if other != center
        ):
            r, c = center
            out[r][c] = 8
    return out


def margin_two_only_rival(grid: Grid) -> list[list[int]]:
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r, c in true_centers(grid):
        if min(r, c, h - 1 - r, w - 1 - c) >= 2:
            out[r][c] = 8
    return out


RIVALS = {
    "at_least_three_arms": at_least_three_arms_rival,
    "cardinal_or_diagonal": cardinal_or_diagonal_rival,
    "separated_targets_only": separated_targets_only_rival,
    "margin_two_only": margin_two_only_rival,
}

WITNESSES = {
    "three_arm_decoy": has_three_arm_decoy,
    "diagonal_decoy": has_diagonal_decoy,
    "shared_arm_targets": has_shared_arm_targets,
    "boundary_target": has_boundary_target,
}


def summarize(grid: Grid) -> dict[str, Any]:
    centers = true_centers(grid)
    components = distractor_components(grid)
    truth = rule_output(grid)
    return {
        "shape": [len(grid), len(grid[0])],
        "true_centers": [list(point) for point in centers],
        "n_targets": len(centers),
        "color_counts": {
            str(color): sum(value == color for row in grid for value in row)
            for color in sorted({value for row in grid for value in row})
        },
        "distractor_component_sizes": [len(component) for component in components],
        "witnesses": {name: bool(fn(grid)) for name, fn in WITNESSES.items()},
        "rival_disagreements": {
            name: fn(grid) != truth for name, fn in RIVALS.items()
        },
    }


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("generator_under_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_report(generator_path: Path, samples: int) -> dict[str, Any]:
    gen = _load_generator(generator_path)
    report: dict[str, Any] = {"generator": str(generator_path), "bands": {}}
    for band in ("easy", "medium", "hard"):
        rows = []
        for index in range(samples):
            grid = gen.generate(91027 + index, index, difficulty=band)
            row = summarize(grid)
            row["seed"] = 91027 + index
            row["sample_index"] = index
            row["self_check"] = list(gen.self_check(grid))
            rows.append(row)
        report["bands"][band] = {
            "samples": samples,
            "lawful": sum(not row["self_check"] for row in rows),
            "unique": len({json.dumps(row["true_centers"]) + str(row["shape"]) for row in rows}),
            "target_counts": sorted({row["n_targets"] for row in rows}),
            "witness_hits": {
                name: sum(row["witnesses"][name] for row in rows)
                for name in WITNESSES
            },
            "rows": rows,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = sample_report(args.generator.resolve(), args.samples)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
