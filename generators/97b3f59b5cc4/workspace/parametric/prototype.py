"""Native matched-input family for four- versus eight-connected border objects.

The selected setting preserves exact canonical behavior: segment nonzero cells
into same-color four-connected components and keep a whole component iff it
reaches the frame.  The alternate changes only the segmentation relation to
eight-neighbor connectivity.  Every generated scene contains a same-color
border/interior pair joined only diagonally, so demonstrations identify the
setting rather than merely documenting it.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "97b3f59b5cc4"
PARAMETER = "connectivity"
MODES = ("four", "eight")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "four": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "eight": (_DIR / "eight_connected.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((12, 14), (14, 16), (16, 18), (19, 21), (22, 24), (26, 28))
_QUERY_DIMS = ((11, 13), (17, 19), (24, 27), (30, 30))
_DIRS = {
    "four": ((-1, 0), (1, 0), (0, -1), (0, 1)),
    "eight": (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),             (0, 1),
        (1, -1),  (1, 0),   (1, 1),
    ),
}


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly connectivity")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"connectivity must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for a declared setting."""
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def components(grid: list[list[int]], connectivity: str = "four") -> list[dict[str, Any]]:
    """Return same-color components in row-major discovery order."""
    _validate_grid(grid)
    if connectivity not in MODES:
        raise ValueError(f"connectivity must be one of {MODES}")
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS[connectivity]:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            result.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "touches_border": any(
                    rr in (0, height - 1) or cc in (0, width - 1)
                    for rr, cc in cells
                ),
            })
    return result


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    """Python claim mirror; protected Racket remains the qualification authority."""
    mode = _mode(settings)
    _validate_grid(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for obj in components(grid, mode):
        if obj["touches_border"]:
            for row, col in obj["cells"]:
                output[row][col] = obj["color"]
    return output


def observables(grid: list[list[int]]) -> dict[str, Any]:
    """Expose the segmentation intermediate used by the sequential witness."""
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    four = components(grid, "four")
    eight = components(grid, "eight")
    touched_edges: set[str] = set()
    for obj in four:
        for row, col in obj["cells"]:
            if row == 0:
                touched_edges.add("top")
            if row == height - 1:
                touched_edges.add("bottom")
            if col == 0:
                touched_edges.add("left")
            if col == width - 1:
                touched_edges.add("right")
    border_colors = {obj["color"] for obj in four if obj["touches_border"]}
    interior_colors = {obj["color"] for obj in four if not obj["touches_border"]}
    return {
        "four_components": copy.deepcopy(four),
        "eight_components": copy.deepcopy(eight),
        "four_border_count": sum(bool(obj["touches_border"]) for obj in four),
        "four_interior_count": sum(not obj["touches_border"] for obj in four),
        "eight_border_count": sum(bool(obj["touches_border"]) for obj in eight),
        "eight_interior_count": sum(not obj["touches_border"] for obj in eight),
        "touched_edges": sorted(touched_edges),
        "shared_border_interior_colors": sorted(border_colors & interior_colors),
        "outputs_differ": solve(grid, {PARAMETER: "four"}) != solve(
            grid, {PARAMETER: "eight"}
        ),
    }


def validate_input(grid: Any) -> list[str]:
    """Return finite grammar violations instead of raising for generated-scene audits."""
    try:
        _validate_grid(grid)
        facts = observables(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if facts["touched_edges"] != ["bottom", "left", "right", "top"]:
        errors.append("border components must cover all four edges")
    if facts["four_border_count"] < 4:
        errors.append("need at least four four-connected border components")
    if facts["four_interior_count"] < 3:
        errors.append("need at least three four-connected interior components")
    if not facts["shared_border_interior_colors"]:
        errors.append("need a repeated color with opposite border fates")
    if not facts["outputs_differ"]:
        errors.append("four- and eight-connected labels must differ")
    return errors


def _derived_rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _paint_rect(
    grid: list[list[int]], top: int, left: int, height: int, width: int, color: int
) -> None:
    if height <= 0 or width <= 0:
        raise AssertionError("rectangle dimensions must be positive")
    for row in range(top, top + height):
        for col in range(left, left + width):
            if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
                raise AssertionError("rectangle leaves grid")
            if grid[row][col] != 0:
                raise AssertionError("rectangle collision")
            grid[row][col] = color


def _flip(grid: list[list[int]], vertical: bool, horizontal: bool) -> list[list[int]]:
    out = [row[:] for row in grid]
    if vertical:
        out.reverse()
    if horizontal:
        out = [list(reversed(row)) for row in out]
    return out


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    rng = _derived_rng(seed, split, index)
    if split == "train":
        height, width = _DEMO_DIMS[index]
    elif split == "test":
        height, width = _QUERY_DIMS[index]
    else:  # pragma: no cover - internal guard
        raise ValueError(split)

    palette = list(range(1, 10))
    rng.shuffle(palette)
    bridge_color, repeated_color, bottom_color, left_color, interior_color = palette[:5]
    grid = [[0] * width for _ in range(height)]

    tail_width = max(2, width // 8)
    bridge_height = max(3, height // 4)
    bridge_width = max(3, width // 5)
    _paint_rect(grid, 0, 1, 2, tail_width, bridge_color)
    # The top-left cell is diagonal to the tail's lower-right cell, but there is
    # no cardinal contact. This is the family discriminator.
    _paint_rect(grid, 2, 1 + tail_width, bridge_height, bridge_width, bridge_color)

    edge_height = max(3, height // 4)
    _paint_rect(grid, 2, width - 2, edge_height, 2, repeated_color)

    inner_height = max(2, height // 6)
    inner_width = max(2, width // 6)
    inner_top = height - inner_height - 3
    inner_left = width - inner_width - 4
    _paint_rect(grid, inner_top, inner_left, inner_height, inner_width, repeated_color)

    bottom_width = max(4, width // 4)
    _paint_rect(grid, height - 2, (width - bottom_width) // 2, 2, bottom_width, bottom_color)

    left_height = max(3, height // 4)
    _paint_rect(grid, height - left_height - 4, 0, left_height, 2, left_color)

    middle_height = max(2, height // 5)
    middle_width = max(2, width // 7)
    middle_top = max(2 + bridge_height + 1, (height - middle_height) // 2)
    if middle_top + middle_height >= height - 2:
        middle_top = height - middle_height - 3
    middle_left = max(3, (width - middle_width) // 2 - 1)
    if middle_left + middle_width >= width - 3:
        middle_left = width - middle_width - 4
    _paint_rect(grid, middle_top, middle_left, middle_height, middle_width, interior_color)

    grid = _flip(grid, vertical=bool(rng.randrange(2)), horizontal=bool(rng.randrange(2)))
    errors = validate_input(grid)
    if errors:
        raise AssertionError(f"constructed scene violates grammar: {errors}")
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Generate deterministic matched-input episodes with stable count prefixes."""
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    chosen = {PARAMETER: mode}
    return {
        "train": [{"input": grid, "output": solve(grid, chosen)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, chosen)} for grid in test_inputs],
        "program_solution": _PROGRAMS[mode],
    }


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    """Project one scoring query without settings, program, or hidden answer."""
    if type(query_index) is not int or isinstance(query_index, bool):
        raise ValueError("query_index must be an exact integer")
    tests = episode.get("test")
    if type(tests) is not list or not 0 <= query_index < len(tests):
        raise ValueError("query_index is outside the episode")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(tests[query_index]["input"])}],
    }


def _border_colors_globally(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    colors = {
        grid[row][col]
        for row in range(height)
        for col in range(width)
        if (row in (0, height - 1) or col in (0, width - 1)) and grid[row][col] != 0
    }
    return [[value if value in colors else 0 for value in row] for row in grid]


def _edge_cells_only(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    return [
        [
            value if (row in (0, height - 1) or col in (0, width - 1)) else 0
            for col, value in enumerate(line)
        ]
        for row, line in enumerate(grid)
    ]


def _rival_output(grid: list[list[int]], rival: str) -> list[list[int]]:
    if rival in MODES:
        return solve(grid, {PARAMETER: rival})
    if rival == "border_colors_globally":
        return _border_colors_globally(grid)
    if rival == "edge_cells_only":
        return _edge_cells_only(grid)
    if rival == "identity":
        return copy.deepcopy(grid)
    if rival == "erase_all":
        return [[0] * len(grid[0]) for _ in grid]
    raise ValueError(rival)


def audit_episode(seed: int, mode: str, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    """Fit a finite rival set on demonstrations only and report query harm."""
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    rivals = [candidate for candidate in MODES if candidate != mode]
    rivals += ["border_colors_globally", "edge_cells_only", "identity", "erase_all"]
    reports = []
    harmful_survivors = []
    for rival in rivals:
        fits = all(_rival_output(pair["input"], rival) == pair["output"] for pair in episode["train"])
        changes_query = any(_rival_output(pair["input"], rival) != pair["output"] for pair in episode["test"])
        record = {"rival": rival, "fits_demos": fits, "changes_query": changes_query}
        reports.append(record)
        if fits and changes_query:
            harmful_survivors.append(record)
    return {
        "seed": seed,
        "settings": {PARAMETER: mode},
        "fit_uses": "demonstrations_only",
        "candidate_results": reports,
        "harmful_survivors": harmful_survivors,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--connectivity", choices=MODES, default=MODES[0])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, {PARAMETER: args.connectivity}, args.demos, args.queries), indent=2))
