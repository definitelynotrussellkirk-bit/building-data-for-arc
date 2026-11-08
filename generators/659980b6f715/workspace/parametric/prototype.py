"""Native top-left/bottom-right normalized-overlay family for 659980b6f715."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "659980b6f715"
ALIGNMENTS = ("top_left", "bottom_right")
DEFAULT_ALIGNMENT = ALIGNMENTS[0]
PARAMETER_NAME = "alignment_anchor"
_HERE = Path(__file__).resolve().parent
_PROGRAMS = {
    "top_left": (_HERE / "canonical.rkt").read_text(encoding="utf-8"),
    "bottom_right": (_HERE / "bottom_right.rkt").read_text(encoding="utf-8"),
}

# canvas h, canvas w, low bbox h/w, high bbox h/w, shape variants
_DEMO_SPECS = (
    (10, 14, 4, 7, 7, 4, 0, 1),
    (12, 16, 8, 4, 4, 8, 2, 3),
    (14, 18, 5, 9, 9, 5, 4, 5),
    (16, 20, 10, 5, 6, 10, 6, 7),
    (18, 22, 7, 11, 11, 6, 8, 9),
    (20, 24, 12, 6, 7, 12, 10, 11),
)
_QUERY_SPECS = (
    (13, 17, 5, 9, 9, 5, 12, 13),
    (18, 21, 10, 6, 6, 11, 14, 15),
    (24, 27, 14, 8, 9, 14, 16, 17),
    (30, 30, 18, 10, 12, 14, 18, 19),
)

CANDIDATE_RULES = (
    "top_left",
    "bottom_right",
    "top_right",
    "bottom_left",
    "center",
    "low_top_left_high_bottom_right",
    "low_bottom_right_high_top_left",
    "larger_top_left_smaller_bottom_right",
)

Grid = list[list[int]]
Cell = tuple[int, int]


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_alignment(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("alignment_anchor must be a string")
    if value not in ALIGNMENTS:
        raise ValueError(f"alignment_anchor must be one of {list(ALIGNMENTS)}")
    return value


def program_for(alignment: Any) -> str:
    return _PROGRAMS[validate_alignment(alignment)]


def choose_alignment(seed: int, selection: str = "seeded") -> str:
    _integer("seed", seed, 0, 2**63 - 1)
    if selection != "seeded":
        return validate_alignment(selection)
    digest = hashlib.sha256(f"{TASK_ID}|alignment-v2|{seed}".encode()).digest()
    return ALIGNMENTS[digest[0] % len(ALIGNMENTS)]


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|native-v2|{seed}|{stream}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _shape(height: int, width: int, variant: int, rng: random.Random) -> set[Cell]:
    """Build a dense connected ragged corner shape with exact bbox extents."""
    left = variant % 2 == 0
    cells: set[Cell] = set()
    # A full boundary row and boundary column guarantee the requested bbox and
    # give every additional row a path to the backbone.
    for col in range(width):
        cells.add((0, col))
    spine = 0 if left else width - 1
    for row in range(height):
        cells.add((row, spine))
    for row in range(1, height):
        span = 2 + ((row * (variant % 5 + 1) + variant) % max(2, width - 1))
        span = min(width, span)
        columns = range(span) if left else range(width - span, width)
        # Alternating filled and comb rows keep topology varied but connected.
        for col in columns:
            if row % 3 != 1 or col == spine or (col + row + variant) % 2 == 0:
                cells.add((row, col))
    if rng.randrange(2):
        cells = {(height - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, width - 1 - c) for r, c in cells}
    return cells


def _normalize(cells: Iterable[Cell]) -> set[Cell]:
    values = set(cells)
    if not values:
        raise ValueError("cannot normalize empty cells")
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return {(r - r0, c - c0) for r, c in values}


def _bbox_size(cells: set[Cell]) -> tuple[int, int]:
    return 1 + max(r for r, _ in cells), 1 + max(c for _, c in cells)


def _analyze(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer colors 0..9")
    colors = sorted({value for row in grid for value in row if value})
    if len(colors) != 2 or 9 in colors:
        raise ValueError("grid must contain exactly two nonzero colors other than 9")
    raw = {
        color: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        for color in colors
    }
    normalized = {color: _normalize(raw[color]) for color in colors}
    sizes = {color: _bbox_size(normalized[color]) for color in colors}
    return {
        "height": len(grid),
        "width": width,
        "colors": colors,
        "raw": raw,
        "normalized": normalized,
        "sizes": sizes,
    }


def analyze_input(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    return {
        "height": info["height"],
        "width": info["width"],
        "colors": info["colors"],
        "sizes": info["sizes"],
        "nonzero_cells": sum(len(v) for v in info["raw"].values()),
    }


def _shift_for(anchor: str, shape: tuple[int, int], output: tuple[int, int]) -> Cell:
    h, w = shape
    out_h, out_w = output
    if anchor == "top_left":
        return 0, 0
    if anchor == "bottom_right":
        return out_h - h, out_w - w
    if anchor == "top_right":
        return 0, out_w - w
    if anchor == "bottom_left":
        return out_h - h, 0
    if anchor == "center":
        return (out_h - h) // 2, (out_w - w) // 2
    raise ValueError(anchor)


def _render(grid: Grid, mode: str) -> Grid:
    info = _analyze(grid)
    low, high = info["colors"]
    shapes = {color: info["normalized"][color] for color in (low, high)}
    sizes = {color: info["sizes"][color] for color in (low, high)}
    out_h = max(size[0] for size in sizes.values())
    out_w = max(size[1] for size in sizes.values())
    output_size = (out_h, out_w)

    if mode in {"top_left", "bottom_right", "top_right", "bottom_left", "center"}:
        anchors = {low: mode, high: mode}
    elif mode == "low_top_left_high_bottom_right":
        anchors = {low: "top_left", high: "bottom_right"}
    elif mode == "low_bottom_right_high_top_left":
        anchors = {low: "bottom_right", high: "top_left"}
    elif mode == "larger_top_left_smaller_bottom_right":
        areas = {color: sizes[color][0] * sizes[color][1] for color in (low, high)}
        larger = max((low, high), key=lambda color: (areas[color], color))
        anchors = {color: ("top_left" if color == larger else "bottom_right") for color in (low, high)}
    else:
        raise ValueError(f"unknown candidate rule {mode!r}")

    aligned = {}
    for color in (low, high):
        dr, dc = _shift_for(anchors[color], sizes[color], output_size)
        aligned[color] = {(r + dr, c + dc) for r, c in shapes[color]}
    return [
        [
            9 if (r, c) in aligned[low] and (r, c) in aligned[high]
            else low if (r, c) in aligned[low]
            else high if (r, c) in aligned[high]
            else 0
            for c in range(out_w)
        ]
        for r in range(out_h)
    ]


def solve(grid: Grid, alignment: Any) -> Grid:
    return _render(grid, validate_alignment(alignment))


def solve_candidate(grid: Grid, candidate: Any) -> Grid:
    if type(candidate) is not str or candidate not in CANDIDATE_RULES:
        raise ValueError(f"candidate must be one of {list(CANDIDATE_RULES)}")
    return _render(grid, candidate)


def _scene(seed: int, stream: str, index: int, spec: tuple[int, ...]) -> Grid:
    height, width, lh, lw, hh, hw, lv, hv = spec
    rng = _rng(seed, stream, index)
    low_color, high_color = sorted(rng.sample(range(1, 9), 2))
    low_shape = _shape(lh, lw, lv, rng)
    high_shape = _shape(hh, hw, hv, rng)
    if lw + hw + 2 > width:
        raise RuntimeError("profile cannot separate shapes horizontally")

    low_left = bool(rng.randrange(2))
    if low_left:
        placements = {
            low_color: (0 if index % 2 == 0 else height - lh, 0),
            high_color: (height - hh if index % 2 == 0 else 0, width - hw),
        }
    else:
        placements = {
            high_color: (0 if index % 2 == 0 else height - hh, 0),
            low_color: (height - lh if index % 2 == 0 else 0, width - lw),
        }
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, shape in ((low_color, low_shape), (high_color, high_shape)):
        dr, dc = placements[color]
        for r, c in shape:
            if grid[dr + r][dc + c] != 0:
                raise RuntimeError("profile shapes overlap in the input")
            grid[dr + r][dc + c] = color
    if solve(grid, "top_left") == solve(grid, "bottom_right"):
        raise RuntimeError("profile does not expose alignment")
    return grid


def episode_inputs(seed: int, *, demos: int, queries: int) -> dict[str, list[Grid]]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    train = [_scene(seed, "demo", i, _DEMO_SPECS[i]) for i in range(demos)]
    test = [_scene(seed, "query", i, _QUERY_SPECS[i]) for i in range(queries)]
    return {"train": train, "test": test}


def generate_episode(seed: int, alignment: Any, *, demos: int, queries: int) -> dict[str, Any]:
    selected = validate_alignment(alignment)
    inputs = episode_inputs(seed, demos=demos, queries=queries)
    return {
        "schema": "659980b6f715-native-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER_NAME: selected},
        "program_solution": program_for(selected),
        "train": [{"input": grid, "output": solve(grid, selected)} for grid in inputs["train"]],
        "test": [{"input": grid, "output": solve(grid, selected)} for grid in inputs["test"]],
    }


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is outside this episode")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(challenge: dict[str, Any]) -> bytes:
    return public_challenge_bytes(challenge)


def public_id(challenge: dict[str, Any]) -> str:
    return public_challenge_id(challenge)


def intermediate_for(grid: Grid, alignment: Any) -> dict[str, Any]:
    selected = validate_alignment(alignment)
    info = _analyze(grid)
    out = (max(v[0] for v in info["sizes"].values()), max(v[1] for v in info["sizes"].values()))
    return {
        "normalized_bbox_sizes": {str(k): list(v) for k, v in info["sizes"].items()},
        "output_size": list(out),
        "alignment_shifts": {
            str(color): list(_shift_for(selected, info["sizes"][color], out))
            for color in info["colors"]
        },
    }
