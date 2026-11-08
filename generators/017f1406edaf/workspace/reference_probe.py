"""Independent geometry oracle and sampler diagnostics for task 017f1406edaf.

This file deliberately does not import production helpers from generator.py.
Task-local tests use it to check the selected generator, and reviewers can run
it as a small JSON-producing distribution probe.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Callable, Iterable

TASK_ID = "017f1406edaf"


@dataclass(frozen=True)
class Component:
    color: int
    cells: tuple[tuple[int, int], ...]

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def touches_row0(self) -> bool:
        return any(row == 0 for row, _ in self.cells)

    @property
    def first(self) -> tuple[int, int]:
        return min(self.cells)


def components(grid: list[list[int]]) -> list[Component]:
    """Return monochrome 4-connected nonzero components in row-major order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[Component] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(Component(color, tuple(sorted(cells))))
    return found


def blank_like(grid: list[list[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in grid]


def paint(component: Component | None, grid: list[list[int]]) -> list[list[int]]:
    output = blank_like(grid)
    if component is not None:
        for row, col in component.cells:
            output[row][col] = 8
    return output


def row0_target(grid: list[list[int]]) -> int:
    return sum(value == 1 for value in grid[0])


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected Racket rule on its lawful domain."""
    target = row0_target(grid)
    selected = next(
        (
            component
            for component in components(grid)
            if component.color != 1
            and not component.touches_row0
            and component.size == target
        ),
        None,
    )
    return paint(selected, grid)


def rival_count_all_blue(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: count every blue cell, not just row-0 markers."""
    target = sum(value == 1 for row in grid for value in row)
    selected = next(
        (
            component
            for component in components(grid)
            if component.color != 1
            and not component.touches_row0
            and component.size == target
        ),
        None,
    )
    return paint(selected, grid)


def rival_include_row0(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: allow any nonblue size-K object, even one touching row 0."""
    target = row0_target(grid)
    selected = next(
        (
            component
            for component in components(grid)
            if component.color != 1 and component.size == target
        ),
        None,
    )
    return paint(selected, grid)


def rival_median_candidate(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule fitting the two canonical demonstrations: keep median area."""
    candidates = [
        component
        for component in components(grid)
        if component.color != 1 and not component.touches_row0
    ]
    candidates.sort(key=lambda component: (component.size, component.first))
    selected = candidates[(len(candidates) - 1) // 2] if candidates else None
    return paint(selected, grid)


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "count_all_blue": rival_count_all_blue,
    "include_row0_size_match": rival_include_row0,
    "median_candidate_size": rival_median_candidate,
}


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    target = row0_target(grid)
    found = components(grid)
    blue_decoy = any(
        component.color == 1
        and not component.touches_row0
        and component.size == target
        for component in found
    )
    row0_decoy = any(
        component.color != 1
        and component.touches_row0
        and component.size == target
        for component in found
    )
    if blue_decoy and row0_decoy:
        decoy = "both"
    elif blue_decoy:
        decoy = "blue"
    elif row0_decoy:
        decoy = "row0"
    else:
        decoy = "none"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "K": target,
        "n_blobs": sum(
            component.color != 1 and not component.touches_row0
            for component in found
        ),
        "decoy": decoy,
    }


def load_generator(path: str | os.PathLike[str] | None = None):
    raw = path or os.environ.get("GENERATOR_UNDER_TEST")
    source = Path(raw) if raw else Path(__file__).resolve().parents[1] / "generator.py"
    if not source.is_file():
        raise FileNotFoundError(source)
    spec = importlib.util.spec_from_file_location("generator_017f1406edaf_under_test", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def sample_report(generator, *, per_band: int = 200) -> dict:
    report: dict[str, object] = {"task_id": TASK_ID, "per_band": per_band, "bands": {}}
    for band in (None, "easy", "medium", "hard"):
        counts = {"none": 0, "blue": 0, "row0": 0, "both": 0}
        profiles: dict[str, int] = {}
        rival_disagreements = {name: 0 for name in RIVALS}
        for index in range(per_band):
            grid = generator.generate(4100 + index, index, difficulty=band)
            obs = observed(grid)
            counts[str(obs["decoy"])] += 1
            profile = generator.schedule_profile(4100 + index, index, band)
            profiles[profile] = profiles.get(profile, 0) + 1
            intended = intended_output(grid)
            for name, rival in RIVALS.items():
                rival_disagreements[name] += rival(grid) != intended
        report["bands"][str(band)] = {
            "decoys": counts,
            "profiles": profiles,
            "rival_disagreements": rival_disagreements,
        }
    return report


def main() -> None:
    generator = load_generator()
    print(json.dumps(sample_report(generator), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
