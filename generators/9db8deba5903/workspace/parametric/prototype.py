"""Opt-in rotation-first, largest-component-second family for 9db8deba5903.

``canonical`` is the byte-exact source rule.  ``largest_tiled_component`` first
constructs that rotation mosaic, then finds the unique largest four-connected
color-1 component in the mosaic and recolors only that component to 9.  The
winner is input-dependent because rotated copies merge across a quadrant seam.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from random import Random
from typing import Any, Callable, Sequence

from reviewer_support import (
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _visible_id,
)

TASK_ID = "9db8deba5903"
MODES = ("canonical", "largest_tiled_component")
_HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HERE / "rules" / "canonical.rkt").read_text()
LARGEST_COMPONENT_PROGRAM = (
    _HERE / "rules" / "largest_tiled_component.rkt"
).read_text()

_DEMO_SPECS = (
    (6, "top"),
    (7, "bottom"),
    (8, "top"),
    (9, "bottom"),
    (11, "top"),
    (13, "bottom"),
)
_QUERY_SPECS = (
    (10, "bottom"),
    (12, "top"),
    (14, "bottom"),
    (15, "top"),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return {"mode": mode}


def rule_text(mode: str) -> str:
    if mode == "canonical":
        return CANONICAL_PROGRAM
    if mode == "largest_tiled_component":
        return LARGEST_COMPONENT_PROGRAM
    raise ValueError(f"unknown mode {mode!r}")


def _grid(value: Sequence[Sequence[int]]) -> list[list[int]]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if len(value) != width:
        raise ValueError("input must be square")
    return [list(row) for row in value]


def _rot_cw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*reversed(grid))]


def _rot_ccw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(list(zip(*grid)))]


def _rot_180(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _tile(
    top_left: Sequence[Sequence[int]],
    top_right: Sequence[Sequence[int]],
    bottom_left: Sequence[Sequence[int]],
    bottom_right: Sequence[Sequence[int]],
) -> list[list[int]]:
    n = len(top_left)
    return (
        [list(top_left[r]) + list(top_right[r]) for r in range(n)]
        + [list(bottom_left[r]) + list(bottom_right[r]) for r in range(n)]
    )


def tile_rotations(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    original = _grid(grid)
    return _tile(original, _rot_ccw(original), _rot_180(original), _rot_cw(original))


def _repeat_identity(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    original = _grid(grid)
    return _tile(original, original, original, original)


def _swap_quarter_turns(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    original = _grid(grid)
    return _tile(original, _rot_cw(original), _rot_180(original), _rot_ccw(original))


def _components(grid: Sequence[Sequence[int]], color: int = 1) -> list[tuple[tuple[int, int], ...]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: cells[0])


def _winner(components: Sequence[tuple[tuple[int, int], ...]]) -> tuple[tuple[int, int], ...]:
    if not components:
        raise ValueError("mosaic must contain color 1")
    ordered = sorted(components, key=lambda cells: (-len(cells), cells[0]))
    if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
        raise ValueError("mosaic must have a unique largest color-1 component")
    return ordered[0]


def _paint(grid: Sequence[Sequence[int]], cells, color: int) -> list[list[int]]:
    out = [list(row) for row in grid]
    for row, col in cells:
        out[row][col] = color
    return out


def solve(grid: Sequence[Sequence[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    mosaic = tile_rotations(grid)
    if mode == "canonical":
        return mosaic
    return _paint(mosaic, _winner(_components(mosaic, 1)), 9)


def solve_with_repeat_identity_intermediate(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Causal counterfactual: use four unrotated copies before stage B."""
    wrong = _repeat_identity(grid)
    components = _components(wrong, 1)
    chosen = sorted(components, key=lambda cells: (-len(cells), cells[0]))[0]
    return _paint(wrong, chosen, 9)


def _component_crosses_seam(cells, n: int) -> bool:
    rows = {row < n for row, _ in cells}
    cols = {col < n for _, col in cells}
    return len(rows) > 1 or len(cols) > 1


def analyze(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    mosaic = tile_rotations(grid)
    components = _components(mosaic, 1)
    winner = _winner(components)
    n = len(grid)
    seam_sizes = sorted(
        (len(cells) for cells in components if _component_crosses_seam(cells, n)),
        reverse=True,
    )
    return {
        "input_size": n,
        "output_size": len(mosaic),
        "component_sizes": sorted((len(cells) for cells in components), reverse=True),
        "seam_component_sizes": seam_sizes,
        "winner_size": len(winner),
        "winner_cells": [[row, col] for row, col in winner],
    }


def _rng(seed: int, split: str, index: int) -> Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:rotation-component-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return Random(int.from_bytes(digest, "big"))


def _target_shapes(n: int, profile: str) -> tuple[list[tuple[int, int]], ...]:
    if profile == "top":
        primary = [(0, n - 2), (0, n - 1), (1, n - 2), (1, n - 1)]
        secondary = [(n - 2, 0), (n - 1, 0)]
    elif profile == "bottom":
        primary = [(n - 2, 0), (n - 2, 1), (n - 1, 0), (n - 1, 1)]
        secondary = [(0, n - 1), (1, n - 1)]
    else:
        raise ValueError(f"unknown profile {profile!r}")
    return primary, secondary


def _input_grid(seed: int, split: str, index: int, spec) -> list[list[int]]:
    n, profile = spec
    rng = _rng(seed, split, index)
    grid = [[0 for _ in range(n)] for _ in range(n)]
    primary, secondary = _target_shapes(n, profile)
    for row, col in primary + secondary:
        grid[row][col] = 1

    # A separate internal L gives the tiled mosaic four untouched size-three
    # controls. Its orientation varies with the seed without approaching a seam.
    top = n // 2 - 1
    left = n // 2 - 1
    variants = (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    )
    for dr, dc in variants[rng.randrange(len(variants))]:
        grid[top + dr][left + dc] = 1

    # Dense neutral structure makes the 15x15 input / 30x30 output a real
    # boundary and content stress while preserving the color-1 component grammar.
    phase = rng.randrange(7)
    for row in range(n):
        for col in range(n):
            if grid[row][col] == 0 and (row * 5 + col * 3 + phase) % 7 == 0:
                grid[row][col] = 8
    for row, col in (
        (0, 0),
        (n - 1, n - 1),
        (0, n // 2),
        (n - 1, n // 2),
        (n // 2, 0),
        (n // 2, n - 1),
    ):
        if grid[row][col] == 0:
            grid[row][col] = 8

    facts = analyze(grid)
    if facts["component_sizes"][:4] != [8, 4, 4, 4]:
        raise RuntimeError("constructed input lost the intended tiled component grammar")
    if facts["seam_component_sizes"][:2] != [8, 4]:
        raise RuntimeError("constructed input must contain large and small seam components")
    return grid


def _pair(seed: int, split: str, index: int, spec, mode: str) -> dict[str, Any]:
    grid = _input_grid(seed, split, index, spec)
    return {"input": grid, "output": solve(grid, mode)}


def generate_episode(seed: int, *, mode: str, demos: int, queries: int) -> dict[str, Any]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    train = [
        _pair(seed, "demo", index, _DEMO_SPECS[index], mode)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "query", index, _QUERY_SPECS[index], mode)
        for index in range(queries)
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": rule_text(mode),
        "settings": {"mode": mode},
    }


def _all_target(grid):
    return [[9 if value == 1 else value for value in row] for row in tile_rotations(grid)]


def _all_seam_components(grid):
    mosaic = tile_rotations(grid)
    n = len(grid)
    cells = [
        cell
        for component in _components(mosaic, 1)
        if _component_crosses_seam(component, n)
        for cell in component
    ]
    return _paint(mosaic, cells, 9)


def _first_component(grid):
    mosaic = tile_rotations(grid)
    return _paint(mosaic, _components(mosaic, 1)[0], 9)


def _fixed_top_component(grid):
    mosaic = tile_rotations(grid)
    touching_top = [component for component in _components(mosaic, 1) if any(r == 0 for r, _ in component)]
    chosen = sorted(touching_top, key=lambda cells: (-len(cells), cells[0]))[0]
    return _paint(mosaic, chosen, 9)


def _largest_before_tiling(grid):
    original = _grid(grid)
    chosen = _winner(_components(original, 1))
    return tile_rotations(_paint(original, chosen, 9))


def audit_rivals(mode: str) -> dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]]:
    if mode == "canonical":
        return {
            "repeat_identity": _repeat_identity,
            "swap_quarter_turns": _swap_quarter_turns,
            "apply_relay_stage": lambda grid: solve(grid, "largest_tiled_component"),
        }
    if mode == "largest_tiled_component":
        return {
            "recolor_all_target_cells": _all_target,
            "recolor_all_seam_components": _all_seam_components,
            "row_major_first_component": _first_component,
            "fixed_top_component": _fixed_top_component,
            "largest_before_tiling": _largest_before_tiling,
            "repeat_identity_intermediate": solve_with_repeat_identity_intermediate,
            "skip_recolor_stage": lambda grid: solve(grid, "canonical"),
        }
    raise ValueError(f"unknown mode {mode!r}")


def public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_challenge_bytes(episode: dict[str, Any]) -> bytes:
    return _public_challenge_bytes(public_projection(episode))


def public_challenge_id(episode: dict[str, Any]) -> str:
    return _visible_id(public_projection(episode))
