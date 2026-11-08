"""Parametric horizontal-sandwich family for ``dfc7297269cc``.

``horizontal_all`` is the byte-exact canonical rule. ``ranked_vertical`` first
finds every canonical horizontal sandwich, uses their count as a one-based
rank, and then also completes the same-ranked vertical sandwich in row-major
order. Inputs are sampled independently of the private setting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random
from pathlib import Path
from typing import Any, Callable

TASK_ID = "dfc7297269cc"
PARAMETER = "completion"
SETTINGS = ("horizontal_all", "ranked_vertical")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "horizontal_all": _HOME / "canonical.rkt",
    "ranked_vertical": _HOME / "ranked_vertical.rkt",
}

# (height, width, number of horizontal sandwiches). The first two demos use
# ranks two and four so the minimum visible curriculum defeats fixed-rank,
# first/last, row-count, and color-count selectors.
_TRAIN_PROFILES = (
    (12, 14, 2),
    (14, 16, 4),
    (16, 18, 1),
    (18, 20, 3),
    (20, 22, 4),
    (22, 24, 2),
)
_QUERY_PROFILES = (
    (15, 17, 3),
    (20, 22, 1),
    (25, 27, 4),
    (30, 30, 2),
)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAM_FILES[_validate_settings(settings)].read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return len(grid), width


def horizontal_centers(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    height, width = _validate_grid(grid)
    return [
        (row, col, grid[row][col - 1])
        for row in range(height)
        for col in range(1, width - 1)
        if grid[row][col] == 0
        and grid[row][col - 1] != 0
        and grid[row][col - 1] == grid[row][col + 1]
    ]


def vertical_centers(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    height, width = _validate_grid(grid)
    return [
        (row, col, grid[row - 1][col])
        for row in range(1, height - 1)
        for col in range(width)
        if grid[row][col] == 0
        and grid[row - 1][col] != 0
        and grid[row - 1][col] == grid[row + 1][col]
    ]


def _paint_centers(grid: list[list[int]], centers: list[tuple[int, int, int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for row, col, color in centers:
        out[row][col] = color
    return out


def apply_with_vertical_rank(grid: list[list[int]], rank: int) -> list[list[int]]:
    """Fill canonical centers and one explicit one-based vertical candidate."""
    if type(rank) is not int:
        raise TypeError("rank must be an exact integer")
    horizontal = horizontal_centers(grid)
    vertical = vertical_centers(grid)
    if not 1 <= rank <= len(vertical):
        raise ValueError(f"rank must be in [1, {len(vertical)}]")
    out = _paint_centers(grid, horizontal)
    row, col, color = vertical[rank - 1]
    out[row][col] = color
    return out


def apply_rule(grid: list[list[int]], completion: str) -> list[list[int]]:
    if type(completion) is not str or completion not in SETTINGS:
        raise ValueError(f"completion must be one of {SETTINGS!r}")
    horizontal = horizontal_centers(grid)
    if completion == "horizontal_all":
        return _paint_centers(grid, horizontal)
    if not horizontal:
        raise ValueError("ranked_vertical requires at least one horizontal sandwich")
    return apply_with_vertical_rank(grid, len(horizontal))


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if _validate_grid(left) != _validate_grid(right):
        raise ValueError("grids must have the same shape")
    return sum(
        left[row][col] != right[row][col]
        for row in range(len(left))
        for col in range(len(left[0]))
    )


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|ranked-vertical-inputs-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _set(grid: list[list[int]], row: int, col: int, color: int) -> None:
    if grid[row][col] != 0:
        raise RuntimeError(f"construction overlap at {(row, col)}")
    grid[row][col] = color


def _solid_rect(
    grid: list[list[int]], top: int, left: int, height: int, width: int, color: int
) -> None:
    for row in range(top, top + height):
        for col in range(left, left + width):
            _set(grid, row, col, color)


def _motif_specs(rank: int, width: int, colors: tuple[int, int]) -> list[tuple[int, int, int]]:
    left, right = 2, width - 3
    if rank == 1:
        return [(1, left, colors[0])]
    if rank == 2:
        return [(1, left, colors[0]), (1, right, colors[0])]
    if rank == 3:
        return [
            (1, left, colors[0]),
            (1, right, colors[0]),
            (4, width // 2, colors[1]),
        ]
    if rank == 4:
        return [
            (1, left, colors[0]),
            (1, right, colors[0]),
            (4, 3, colors[1]),
            (4, width - 4, colors[1]),
        ]
    raise ValueError(f"unsupported horizontal rank {rank}")


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, rank = profiles[index]
    rng = _rng(seed, split, index)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    motif_colors = (palette[0], palette[1])
    # The relative order makes the lowest candidate rank 3 and the highest rank
    # 4, so neither color-extreme shortcut can fit the first two demonstrations.
    sorted_candidates = sorted(palette[2:8])
    candidate_colors = tuple(sorted_candidates[i] for i in (1, 4, 0, 5, 2, 3))
    distractor = palette[8]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, center, color in _motif_specs(rank, width, motif_colors):
        _set(grid, row, center - 1, color)
        _set(grid, row, center + 1, color)

    candidate_rows = (height - 5, height - 2)
    candidate_cols = (2, width // 2, width - 3)
    for color, (row, col) in zip(
        candidate_colors,
        ((row, col) for row in candidate_rows for col in candidate_cols),
    ):
        _set(grid, row - 1, col, color)
        _set(grid, row + 1, col, color)

    # Ensure the second motif color is visible even in rank-1/rank-2 profiles.
    _solid_rect(grid, 2, width // 2 - 1, 2, 2, motif_colors[1])

    # Boundary-touching and dense distractors are solid, so they add content
    # without creating another zero-centered sandwich.
    _solid_rect(grid, 0, width // 2 - 1, 1, 3, distractor)
    _solid_rect(grid, height // 2 - 1, 0, 2, 1, distractor)
    _solid_rect(grid, height // 2 + 1, width - 1, 2, 1, motif_colors[1])
    if height >= 20:
        _solid_rect(grid, 7, 1, 3, 6, distractor)
        _solid_rect(grid, height // 2, width - 6, 4, 4, distractor)

    if rng.choice((False, True)):
        grid = [row[::-1] for row in grid]
    if rng.choice((False, True)):
        grid = grid[::-1]

    horizontal = horizontal_centers(grid)
    vertical = vertical_centers(grid)
    if len(horizontal) != rank:
        raise RuntimeError(f"constructed {len(horizontal)} horizontal centers, expected {rank}")
    if len(vertical) != 6:
        raise RuntimeError(f"constructed {len(vertical)} vertical centers, expected 6")
    if set((r, c) for r, c, _ in horizontal) & set((r, c) for r, c, _ in vertical):
        raise RuntimeError("horizontal and vertical centers must be disjoint")
    return grid


def _fill_all_vertical(grid: list[list[int]]) -> list[list[int]]:
    return _paint_centers(_paint_centers(grid, horizontal_centers(grid)), vertical_centers(grid))


def _candidate_color_rank(grid: list[list[int]], chooser: Callable[[list[int]], int]) -> int:
    colors = [color for _, _, color in vertical_centers(grid)]
    chosen = chooser(colors)
    return colors.index(chosen) + 1


def _rival_outputs(grid: list[list[int]], completion: str) -> dict[str, list[list[int]]]:
    horizontal = horizontal_centers(grid)
    vertical = vertical_centers(grid)
    canonical = _paint_centers(grid, horizontal)
    if completion == "horizontal_all":
        return {
            "ranked_vertical": apply_with_vertical_rank(grid, len(horizontal)),
            "fill_all_vertical": _fill_all_vertical(grid),
            "first_vertical": apply_with_vertical_rank(grid, 1),
        }
    rows = len({row for row, _, _ in horizontal})
    colors = len({color for _, _, color in horizontal})
    return {
        "horizontal_only": canonical,
        "fill_all_vertical": _fill_all_vertical(grid),
        "first_vertical": apply_with_vertical_rank(grid, 1),
        "last_vertical": apply_with_vertical_rank(grid, len(vertical)),
        "fixed_second": apply_with_vertical_rank(grid, 2),
        "fixed_fourth": apply_with_vertical_rank(grid, 4),
        "horizontal_row_count": apply_with_vertical_rank(grid, rows),
        "horizontal_color_count": apply_with_vertical_rank(grid, colors),
        "reverse_rank": apply_with_vertical_rank(grid, len(vertical) + 1 - len(horizontal)),
        "lowest_candidate_color": apply_with_vertical_rank(
            grid, _candidate_color_rank(grid, min)
        ),
        "highest_candidate_color": apply_with_vertical_rank(
            grid, _candidate_color_rank(grid, max)
        ),
    }


def surviving_rivals(train: list[dict[str, Any]], completion: str) -> list[str]:
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty list")
    if completion not in SETTINGS:
        raise ValueError(f"completion must be one of {SETTINGS!r}")
    names = set(_rival_outputs(train[0]["input"], completion))
    return sorted(
        name
        for name in names
        if all(
            _rival_outputs(pair["input"], completion)[name] == pair["output"]
            for pair in train
        )
    )


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    completion = _validate_settings(settings)

    train = []
    for index in range(demos):
        grid = _sample_input(seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, completion)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, completion)})

    serialized = [repr(pair["input"]) for pair in [*train, *test]]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    if surviving_rivals(train, completion):
        raise RuntimeError("visible demonstrations leave a declared rival alive")
    return {
        "train": train,
        "test": test,
        "program_solution": program({PARAMETER: completion}),
    }
