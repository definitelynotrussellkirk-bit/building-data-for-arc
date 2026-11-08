"""Source-bound parametric prototype for ARC family b5b012cd97d9.

The canonical setting preserves the selected catalog program exactly.  The
alternative keeps the same count-derived roles and packed shape, but first
infers whether the large role lies above or below the small role in the input.
It then orients the packed answer so the large role preserves that vertical
order.  Sampling is deterministic, prefix-stable, and independent of Python's
global random state.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from math import isqrt
from pathlib import Path
import random
from typing import Callable

from reviewer_support import public_challenge_id


TASK_ID = "b5b012cd97d9"
PLACEMENTS = ("canonical", "preserve_vertical")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "canonical": (_HOME / "canonical.rkt").read_text(encoding="utf-8"),
    "preserve_vertical": (_HOME / "preserve_vertical.rkt").read_text(encoding="utf-8"),
}


_DEMO_PROFILES = (
    {
        "canvas": (9, 12), "big_side": 4, "small_side": 3,
        "big_box": (0, 0, 4, 4), "small_box": (6, 8, 8, 11),
        "singleton": (5, 0), "zero_big": False,
    },
    {
        "canvas": (12, 10), "big_side": 4, "small_side": 2,
        "big_box": (7, 0, 11, 4), "small_box": (0, 7, 2, 9),
        "singleton": None, "zero_big": False,
    },
    {
        "canvas": (15, 16), "big_side": 5, "small_side": 3,
        "big_box": (0, 10, 5, 15), "small_box": (11, 0, 14, 4),
        "singleton": (7, 8), "zero_big": True,
    },
    {
        "canvas": (18, 14), "big_side": 6, "small_side": 4,
        "big_box": (11, 7, 17, 13), "small_box": (0, 0, 4, 4),
        "singleton": None, "zero_big": False,
    },
    {
        "canvas": (20, 22), "big_side": 7, "small_side": 5,
        "big_box": (0, 0, 7, 7), "small_box": (14, 16, 19, 21),
        "singleton": (10, 10), "zero_big": False,
    },
    {
        "canvas": (24, 18), "big_side": 8, "small_side": 5,
        "big_box": (15, 0, 23, 8), "small_box": (0, 12, 5, 17),
        "singleton": None, "zero_big": True,
    },
)

_QUERY_PROFILES = (
    {
        "canvas": (16, 20), "big_side": 5, "small_side": 4,
        "big_box": (10, 0, 15, 5), "small_box": (0, 15, 4, 19),
        "singleton": (7, 9), "zero_big": False,
    },
    {
        "canvas": (22, 24), "big_side": 7, "small_side": 5,
        "big_box": (0, 16, 7, 23), "small_box": (16, 0, 21, 5),
        "singleton": None, "zero_big": True,
    },
    {
        "canvas": (27, 29), "big_side": 9, "small_side": 6,
        "big_box": (17, 0, 26, 9), "small_box": (0, 22, 6, 28),
        "singleton": (13, 14), "zero_big": False,
    },
    {
        "canvas": (30, 30), "big_side": 18, "small_side": 11,
        "big_box": (0, 0, 13, 23), "small_box": (19, 19, 29, 29),
        "singleton": None, "zero_big": False,
    },
)


def _exact_int(value: object, name: str, minimum: int, maximum: int | None = None) -> int:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        bound = f"{minimum}..{maximum}" if maximum is not None else f">={minimum}"
        raise ValueError(f"{name} must be an exact integer in {bound}")
    return value


def _placement(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"placement"}:
        raise ValueError("settings must contain exactly {'placement'}")
    placement = settings["placement"]
    if placement not in PLACEMENTS:
        raise ValueError(f"placement must be one of {PLACEMENTS}")
    return placement


def program(settings: object) -> str:
    """Return the exact source-bound Racket rule for one declared setting."""
    return _PROGRAMS[_placement(settings)]


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    token = f"{TASK_ID}|{seed}|{split}|{index}|{purpose}".encode("utf-8")
    return random.Random(int.from_bytes(sha256(token).digest(), "big"))


def _role_colors(seed: int, split: str, index: int, zero_big: bool) -> dict[str, int | None]:
    palette = list(range(1, 10))
    _rng(seed, split, index, "palette").shuffle(palette)
    if zero_big:
        return {
            "background": palette[0],
            "big": 0,
            "small": palette[1],
            "single": palette[2],
        }
    return {
        "background": palette[0],
        "big": palette[1],
        "small": palette[2],
        "single": palette[3],
    }


def _cells_in_box(box: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def _irregular_mass(
    box: tuple[int, int, int, int],
    count: int,
    rng: random.Random,
) -> list[tuple[int, int]]:
    cells = _cells_in_box(box)
    r0, c0, r1, c1 = box
    corners = [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]
    forced = list(dict.fromkeys(corners))
    if count < len(forced) or count > len(cells):
        raise ValueError("role count cannot realize requested bounding box")
    remaining = [cell for cell in cells if cell not in forced]
    rng.shuffle(remaining)
    return forced + remaining[: count - len(forced)]


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    """Generate one deterministic role scene independent of requested counts."""
    if split == "train":
        if not 0 <= index < len(_DEMO_PROFILES):
            raise ValueError("training profile index out of range")
        profile = _DEMO_PROFILES[index]
    elif split == "test":
        if not 0 <= index < len(_QUERY_PROFILES):
            raise ValueError("query profile index out of range")
        profile = _QUERY_PROFILES[index]
    else:
        raise ValueError("split must be 'train' or 'test'")

    height, width = profile["canvas"]
    colors = _role_colors(seed, split, index, bool(profile["zero_big"]))
    grid = [[int(colors["background"])] * width for _ in range(height)]

    occupied: set[tuple[int, int]] = set()
    for role in ("big", "small"):
        side = int(profile[f"{role}_side"])
        box = profile[f"{role}_box"]
        cells = _irregular_mass(box, side * side, _rng(seed, split, index, role))
        if occupied.intersection(cells):
            raise AssertionError("profile role boxes overlap")
        occupied.update(cells)
        color = int(colors[role])
        for r, c in cells:
            grid[r][c] = color

    singleton = profile["singleton"]
    if singleton is not None:
        if singleton in occupied:
            raise AssertionError("singleton overlaps a repeated role")
        r, c = singleton
        grid[r][c] = int(colors["single"])
    return grid


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def analyze(grid: object) -> dict[str, object]:
    """Recover count-derived roles and the sequential vertical intermediate."""
    errors: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        errors.append("grid dimensions exceed 30x30")
    if any(type(row) is not list or len(row) != width for row in grid):
        return {"errors": errors + ["grid must be rectangular"]}
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return {"errors": errors + ["cells must be exact ARC colors 0..9"]}

    counts = Counter(cell for row in grid for cell in row)
    nonzero = {color: count for color, count in counts.items() if color != 0}
    if not nonzero:
        return {"errors": errors + ["no nonzero background candidate"]}
    mode_count = max(nonzero.values())
    mode_candidates = [color for color, count in nonzero.items() if count == mode_count]
    if len(mode_candidates) != 1:
        return {"errors": errors + ["nonzero background mode is not unique"]}
    background = mode_candidates[0]

    entries = sorted(
        ((count, color) for color, count in counts.items() if color != background),
        reverse=True,
    )
    if not entries:
        return {"errors": errors + ["no answer-bearing colors"]}
    big_n, big_color = entries[0]
    repeated = [entry for entry in entries[1:] if entry[0] > 1]
    if not repeated:
        return {"errors": errors + ["no smaller repeated role"]}
    small_n, small_color = repeated[0]
    singletons = [(count, color) for count, color in entries if count == 1]
    single_color = singletons[0][1] if singletons else None
    if len(singletons) > 1:
        errors.append("more than one singleton role")
    if big_n <= small_n:
        errors.append("big role is not uniquely larger than small role")

    big_side = isqrt(big_n)
    small_side = isqrt(small_n)
    if big_side * big_side != big_n:
        errors.append("big role count is not a perfect square")
    if small_side * small_side != small_n:
        errors.append("small role count is not a perfect square")

    locations: dict[int, list[tuple[int, int]]] = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in counts
    }
    big_box = _bbox(locations[big_color])
    small_box = _bbox(locations[small_color])
    big_row_center2 = big_box[0] + big_box[2]
    small_row_center2 = small_box[0] + small_box[2]
    if big_row_center2 == small_row_center2:
        errors.append("role vertical centers tie")
    big_above = big_row_center2 < small_row_center2
    big_col_center2 = big_box[1] + big_box[3]
    small_col_center2 = small_box[1] + small_box[3]

    role_colors = {big_color, small_color}
    if single_color is not None:
        role_colors.add(single_color)
    boundary_role_cells = sum(
        1
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in role_colors and (r == 0 or c == 0 or r == len(grid) - 1 or c == width - 1)
    )

    return {
        "errors": errors,
        "background": background,
        "big_color": big_color,
        "big_count": big_n,
        "big_side": big_side,
        "big_box": big_box,
        "small_color": small_color,
        "small_count": small_n,
        "small_side": small_side,
        "small_box": small_box,
        "single_color": single_color,
        "has_singleton": single_color is not None,
        "big_above": big_above,
        "big_left": big_col_center2 < small_col_center2,
        "non_background_cells": sum(count for color, count in counts.items() if color != background),
        "boundary_role_cells": boundary_role_cells,
    }


def _canonical_pack(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid generated grid: " + "; ".join(facts["errors"]))
    background = int(facts["background"])
    big_color = int(facts["big_color"])
    small_color = int(facts["small_color"])
    single_color = facts["single_color"]
    big_side = int(facts["big_side"])
    small_side = int(facts["small_side"])
    has_singleton = bool(facts["has_singleton"])

    out_h = max(big_side, small_side + (1 if has_singleton else 0))
    small_c = 2 if has_singleton else 0
    big_c = small_c + small_side + 1
    out_w = big_c + big_side
    small_r = out_h - small_side
    out = [[background] * out_w for _ in range(out_h)]
    for r in range(big_side):
        for c in range(big_c, big_c + big_side):
            out[r][c] = big_color
    for r in range(small_r, out_h):
        for c in range(small_c, small_c + small_side):
            out[r][c] = small_color
    if has_singleton:
        out[out_h - 1][0] = int(single_color)
    return out


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def solve_python(grid: list[list[int]], placement: str) -> list[list[int]]:
    if placement not in PLACEMENTS:
        raise ValueError(f"unknown placement {placement!r}")
    packed = _canonical_pack(grid)
    if placement == "canonical" or bool(analyze(grid)["big_above"]):
        return packed
    return _rotate_180(packed)


def _always_below(grid: list[list[int]]) -> list[list[int]]:
    return _rotate_180(_canonical_pack(grid))


def _reverse_vertical(grid: list[list[int]]) -> list[list[int]]:
    packed = _canonical_pack(grid)
    return _rotate_180(packed) if bool(analyze(grid)["big_above"]) else packed


def _horizontal_proxy(grid: list[list[int]]) -> list[list[int]]:
    packed = _canonical_pack(grid)
    return packed if bool(analyze(grid)["big_left"]) else _rotate_180(packed)


def declared_rivals(placement: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    if placement == "canonical":
        return {
            "preserve_vertical": lambda grid: solve_python(grid, "preserve_vertical"),
            "always_below": _always_below,
            "reverse_vertical": _reverse_vertical,
        }
    if placement == "preserve_vertical":
        return {
            "canonical": _canonical_pack,
            "always_below": _always_below,
            "reverse_vertical": _reverse_vertical,
            "horizontal_proxy": _horizontal_proxy,
        }
    raise ValueError(f"unknown placement {placement!r}")


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    """Build one private episode with setting-matched inputs and labels."""
    seed_i = _exact_int(seed, "seed", 0)
    demos_i = _exact_int(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries_i = _exact_int(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    placement = _placement(settings)

    def pair(split: str, index: int) -> dict[str, list[list[int]]]:
        grid = sample_input(seed_i, split, index)
        return {"input": grid, "output": solve_python(grid, placement)}

    return {
        "train": [pair("train", index) for index in range(demos_i)],
        "test": [pair("test", index) for index in range(queries_i)],
        "program_solution": _PROGRAMS[placement],
    }


def public_id(episode: dict[str, object], query_count: int | None = None) -> str:
    """Return the public content ID, optionally for only the first N queries."""
    if query_count is None:
        return public_challenge_id(episode)
    count = _exact_int(query_count, "query_count", 1, len(episode["test"]))
    view = {"train": episode["train"], "test": episode["test"][:count]}
    return public_challenge_id(view)


def sequential_turn(episode: dict[str, object], index: int) -> dict[str, object]:
    """Expose exactly one future query input and no private answer or settings."""
    index_i = _exact_int(index, "index", 0, len(episode["test"]) - 1)
    return {"test": [{"input": episode["test"][index_i]["input"]}]}
