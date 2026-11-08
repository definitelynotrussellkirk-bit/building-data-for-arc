"""Generator for Transform Timeline Gallery (task ``2ad9e1922f57``).

The first row is a left-to-right program of transform codes.  A monochrome
object appears below two blank separator rows.  The output starts with the
object's tight crop, then appends the *cumulative* state after each code, with
one blank column between top-aligned panels.

Code map: 1=rotate clockwise, 2=flip left/right, 3=rotate 180 degrees,
4=flip up/down.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2ad9e1922f57"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "07dadf929353"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the contiguous transform-code program in row 0. Crop the single "
    "monochrome object below the two blank separator rows. Output the original "
    "crop followed by the cumulative state after each code, top-aligned and "
    "separated by one blank column. Codes 1/2/3/4 mean rotate-cw/flip-lr/"
    "rotate-180/flip-ud."
)

INVARIANTS = [
    "background is 0 and all values are ARC colors 0..9",
    "row 0 contains 2..4 transform codes from 1..4 contiguously from column 0",
    "rows 1 and 2 are entirely blank",
    "rows 3+ contain one 4-connected monochrome motif of 5..8 cells",
    "motif color is 5..9, disjoint from transform-code colors",
    "the motif crop is at most 4x4 and fits every cumulative gallery within 30x30",
]

SHAPE_PROFILES = ("square", "wide", "tall")
POSITION_PROFILES = ("left", "center", "right")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw over 9..12",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw over 10..14",
        "valid": "10..14",
    },
    "n_codes": {
        "type": "int",
        "default": "four-slot teaching schedule over 2..4",
        "valid": "2..4",
    },
    "motif_color": {
        "type": "color",
        "default": "rng 5..9",
        "valid": "5..9",
    },
    "motif_cells": {
        "type": "int",
        "default": "four-slot teaching schedule over 5..8",
        "valid": "5..8",
    },
    "motif_shape": {
        "type": "str",
        "default": "four-slot teaching schedule",
        "valid": "|".join(SHAPE_PROFILES),
    },
    "motif_position": {
        "type": "str",
        "default": "rng horizontal zone",
        "valid": "|".join(POSITION_PROFILES),
    },
}

# Every declared boundary combination is constructible.  An empty declaration
# opts into the strict override-rejection policy: any unexpected rejection is a
# defect rather than an undocumented incompatibility.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

# Four consecutive sample indexes always expose all four code meanings, a
# repeated-code sequence, a non-square crop, and multiple noncommuting orders.
_SCHEDULE = (
    {"name": "rot_flip_square", "codes": (1, 2), "cells": 5, "shape": "square", "h": 9, "w": 10},
    {"name": "halfturn_ud_wide", "codes": (3, 4), "cells": 6, "shape": "wide", "h": 10, "w": 10},
    {"name": "repeat_lr_tall", "codes": (2, 1, 2), "cells": 7, "shape": "tall", "h": 9, "w": 11},
    {"name": "all_codes_square", "codes": (4, 1, 3, 2), "cells": 8, "shape": "square", "h": 10, "w": 12},
)
SCHEDULE_PROFILES = tuple(slot["name"] for slot in _SCHEDULE)

# Fully D4-asymmetric, 4-connected tight crops.  Tall variants are transposes
# of the listed wide variants.  Keeping the catalog explicit avoids expensive
# import-time shape enumeration and makes the teaching support auditable.
_SHAPES: dict[tuple[int, str], tuple[tuple[str, ...], ...]] = {
    (5, "square"): (("010", "111", "100"),),
    (5, "wide"): (
        ("1111", "1000"),
        ("1111", "0100"),
        ("0111", "1100"),
        ("111", "110"),
    ),
    (6, "square"): (
        ("111", "101", "100"),
        ("110", "111", "100"),
        ("101", "111", "100"),
        ("011", "111", "100"),
    ),
    (6, "wide"): (
        ("1111", "1000", "1000"),
        ("0111", "1100", "1000"),
        ("0011", "1110", "1000"),
        ("0100", "1111", "1000"),
    ),
    (7, "square"): (
        ("0011", "1110", "1000", "1000"),
        ("1000", "1111", "1000", "1000"),
        ("0100", "1111", "1000", "1000"),
        ("0010", "1111", "1000", "1000"),
    ),
    (7, "wide"): (
        ("1111", "1100", "1000"),
        ("1111", "1010", "1000"),
        ("1011", "1110", "1000"),
        ("0111", "1110", "1000"),
    ),
    (8, "square"): (
        ("1111", "1010", "1000", "1000"),
        ("1011", "1110", "1000", "1000"),
        ("0111", "1110", "1000", "1000"),
        ("1111", "1001", "1000", "1000"),
    ),
    (8, "wide"): (
        ("1111", "1110", "1000"),
        ("1111", "1101", "1000"),
        ("1111", "1011", "1000"),
        ("1110", "1111", "1000"),
    ),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "n_codes", "motif_color", "motif_cells"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name, options in (
        ("motif_shape", SHAPE_PROFILES),
        ("motif_position", POSITION_PROFILES),
    ):
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"{name} must be one of {options!r}")


def _scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int, overrides: dict[str, Any]) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...], overrides: dict[str, Any]) -> str:
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _transpose_rows(rows: tuple[str, ...]) -> tuple[str, ...]:
    return tuple("".join(column) for column in zip(*rows))


def _shape_rows(cells: int, profile: str, rng) -> tuple[str, ...]:
    source_profile = "wide" if profile == "tall" else profile
    base = rng.choice(_SHAPES[(cells, source_profile)])
    rows = _transpose_rows(base) if profile == "tall" else base

    # Orientation is itself lawful task variation.  Square crops admit all D4
    # orientations; rectangular crops admit the four orientations that retain
    # the requested wide/tall profile.  This materially expands output support
    # without inventing a new semantic axis or changing any override value.
    grid = [list(row) for row in rows]
    variants: set[tuple[str, ...]] = set()
    state = grid
    rotations = 4 if profile == "square" else 2
    for _ in range(rotations):
        variants.add(tuple("".join(row) for row in state))
        variants.add(tuple("".join(reversed(row)) for row in state))
        state = _rotate_cw(state)
    profile_variants = [
        variant
        for variant in variants
        if (len(variant) == len(variant[0]))
        == (profile == "square")
        and (
            profile == "square"
            or (profile == "wide" and len(variant[0]) > len(variant))
            or (profile == "tall" and len(variant) > len(variant[0]))
        )
    ]
    return rng.choice(sorted(profile_variants))


def _placement_column(width: int, motif_width: int, profile: str) -> int:
    if profile == "left":
        return 1
    if profile == "right":
        return width - motif_width - 1
    return (width - motif_width) // 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one lawful input grid; every override is exact or rejected."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = _SCHEDULE[sample_index % len(_SCHEDULE)]
    band_tag = difficulty or "unbanded"

    # Ordinary draws cycle through the four canonical dimension profiles.
    # Explicit overrides still receive the full declared range in every band.
    h = _scheduled_int(ctx, "grid_h", slot["h"], 9, 12, overrides)
    w = _scheduled_int(ctx, "grid_w", slot["w"], 10, 14, overrides)
    n_codes = _scheduled_int(ctx, "n_codes", len(slot["codes"]), 2, 4, overrides)
    motif_cells = _scheduled_int(ctx, "motif_cells", slot["cells"], 5, 8, overrides)
    motif_shape = _scheduled_choice(
        ctx, "motif_shape", slot["shape"], SHAPE_PROFILES, overrides
    )
    motif_position = ctx.draw_choice("motif_position", POSITION_PROFILES)
    motif_color = ctx.draw_color("motif_color", exclude=range(5))

    code_rng = ctx.draw_rng(f"codes:{band_tag}")
    if overrides.get("n_codes") is None:
        codes = list(slot["codes"])
    else:
        codes = [1, 2, 3, 4]
        code_rng.shuffle(codes)
        codes = codes[:n_codes]

    shape_rng = ctx.draw_rng(f"shape_variant:{band_tag}")
    rows = _shape_rows(motif_cells, motif_shape, shape_rng)
    sh, sw = len(rows), len(rows[0])

    g = full_grid(h, w, 0)
    for column, code in enumerate(codes):
        g[0][column] = code

    placement_rng = ctx.draw_rng(f"vertical_position:{band_tag}")
    r0 = placement_rng.randint(3, h - sh - 1)
    c0 = _placement_column(w, sw, motif_position)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value == "1":
                g[r0 + r][c0 + c] = motif_color
    return g


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _crop_body(grid: list[list[int]]) -> list[list[int]]:
    points = [
        (r, c)
        for r in range(1, len(grid))
        for c, value in enumerate(grid[r])
        if value != 0
    ]
    if not points:
        raise ValueError("no nonzero object below the code row")
    r1 = min(r for r, _ in points)
    r2 = max(r for r, _ in points)
    c1 = min(c for _, c in points)
    c2 = max(c for _, c in points)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


_TRANSFORMS: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
    1: _rotate_cw,
    2: _flip_lr,
    3: _rotate_180,
    4: _flip_ud,
}
_WRONG_TRANSFORMS: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
    1: _flip_lr,
    2: _rotate_180,
    3: _flip_ud,
    4: _rotate_cw,
}


def _pack(states: list[list[list[int]]], *, bottom_align: bool = False) -> list[list[int]]:
    height = max(len(state) for state in states)
    width = sum(len(state[0]) for state in states) + len(states) - 1
    out = full_grid(height, width, 0)
    left = 0
    for state in states:
        top = height - len(state) if bottom_align else 0
        for r, row in enumerate(state):
            for c, value in enumerate(row):
                out[top + r][left + c] = value
        left += len(state[0]) + 1
    return out


def _solve_variant(
    grid: list[list[int]],
    *,
    transform_map: dict[int, Callable[[list[list[int]]], list[list[int]]]] = _TRANSFORMS,
    include_initial: bool = True,
    independent: bool = False,
    reverse_codes: bool = False,
    deduplicate_codes: bool = False,
    bottom_align: bool = False,
) -> list[list[int]]:
    codes = [value for value in grid[0] if value != 0]
    if reverse_codes:
        codes = list(reversed(codes))
    if deduplicate_codes:
        codes = list(dict.fromkeys(codes))
    initial = _crop_body(grid)
    states = [initial] if include_initial else []
    state = initial
    for code in codes:
        source = initial if independent else state
        state = transform_map[code](source)
        states.append(state)
    if not states:
        raise ValueError("variant produced no gallery states")
    return _pack(states, bottom_align=bottom_align)


def _authority_output(grid: list[list[int]]) -> list[list[int]]:
    return _solve_variant(grid)


def _wrong_code_map(grid: list[list[int]]) -> list[list[int]]:
    return _solve_variant(grid, transform_map=_WRONG_TRANSFORMS)


def _independent_transforms(grid: list[list[int]]) -> list[list[int]]:
    return _solve_variant(grid, independent=True)


def _omit_initial(grid: list[list[int]]) -> list[list[int]]:
    return _solve_variant(grid, include_initial=False)


def _reverse_code_order(grid: list[list[int]]) -> list[list[int]]:
    return _solve_variant(grid, reverse_codes=True)


def _bottom_align_panels(grid: list[list[int]]) -> list[list[int]]:
    return _solve_variant(grid, bottom_align=True)


def _deduplicate_codes(grid: list[list[int]]) -> list[list[int]]:
    return _solve_variant(grid, deduplicate_codes=True)


def _grid_equal(a: list[list[int]], b: list[list[int]]) -> bool:
    return a == b


def _analysis(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "codes": [],
        "motif_cells": 0,
        "motif_color": None,
        "motif_shape": None,
        "motif_position": None,
        "bbox": None,
        "orbit_size": 0,
    }
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        result["errors"].append("grid must be a nonempty list of rows")
        return result
    w = len(grid[0]) if grid[0] else 0
    if w == 0 or any(len(row) != w for row in grid):
        result["errors"].append("grid must be rectangular and nonempty")
        return result
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        result["errors"].append("grid values must be integer ARC colors 0..9")
        return result

    h = len(grid)
    if not 9 <= h <= 12:
        result["errors"].append(f"grid height must be 9..12, got {h}")
    if not 10 <= w <= 14:
        result["errors"].append(f"grid width must be 10..14, got {w}")

    stop = next((index for index, value in enumerate(grid[0]) if value == 0), w)
    codes = grid[0][:stop]
    result["codes"] = codes
    if not 2 <= len(codes) <= 4:
        result["errors"].append(f"expected 2..4 contiguous row-0 codes, got {codes}")
    if any(code not in (1, 2, 3, 4) for code in codes):
        result["errors"].append(f"transform codes must be in 1..4, got {codes}")
    if any(value != 0 for value in grid[0][stop:]):
        result["errors"].append("row-0 codes must be contiguous from column 0")
    if len(set(codes)) < 2:
        result["errors"].append("the code program must expose at least two meanings")

    if h >= 2 and any(value != 0 for value in grid[1]):
        result["errors"].append("row 1 must be blank")
    if h >= 3 and any(value != 0 for value in grid[2]):
        result["errors"].append("row 2 must be blank")

    body = [
        (r, c, grid[r][c])
        for r in range(3, h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    result["motif_cells"] = len(body)
    if not 5 <= len(body) <= 8:
        result["errors"].append(f"motif must contain 5..8 cells, got {len(body)}")
    colors = {value for _, _, value in body}
    if len(colors) != 1:
        result["errors"].append(f"motif must be monochrome, got colors {sorted(colors)}")
    else:
        color = next(iter(colors))
        result["motif_color"] = color
        if not 5 <= color <= 9:
            result["errors"].append(f"motif color must be 5..9, got {color}")

    cells = {(r, c) for r, c, _ in body}
    if cells and not _connected(cells):
        result["errors"].append("motif must be 4-connected")
    if cells:
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        result["bbox"] = (r1, c1, r2, c2)
        if not (2 <= bh <= 4 and 2 <= bw <= 4):
            result["errors"].append(f"motif crop must be 2..4 by 2..4, got {bh}x{bw}")
        result["motif_shape"] = "square" if bh == bw else ("wide" if bw > bh else "tall")
        left = 1
        center = (w - bw) // 2
        right = w - bw - 1
        if c1 == left:
            result["motif_position"] = "left"
        elif c1 == center:
            result["motif_position"] = "center"
        elif c1 == right:
            result["motif_position"] = "right"

        binary = [
            [1 if (r, c) in cells else 0 for c in range(c1, c2 + 1)]
            for r in range(r1, r2 + 1)
        ]
        variants: set[tuple[tuple[int, ...], ...]] = set()
        current = binary
        for _ in range(4):
            variants.add(tuple(tuple(row) for row in current))
            variants.add(tuple(tuple(row) for row in _flip_lr(current)))
            current = _rotate_cw(current)
        result["orbit_size"] = len(variants)
        if len(variants) < 4:
            result["errors"].append("motif symmetry hides too many transform meanings")

        max_output_width = (len(codes) + 1) * max(bh, bw) + len(codes)
        if max(bh, bw) > 30 or max_output_width > 30:
            result["errors"].append("cumulative gallery would exceed ARC 30x30 bounds")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible teaching grammar."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str | None]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes on malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_codes": len(analysis["codes"]),
        "motif_color": analysis["motif_color"],
        "motif_cells": analysis["motif_cells"],
        "motif_shape": analysis["motif_shape"],
        "motif_position": analysis["motif_position"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold, stricter than generic morphology."""
    return self_check(grid)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]["name"]


def _codes(grid: list[list[int]]) -> list[int]:
    return [value for value in grid[0] if value != 0]


def _rival_visible(grid, rival: Callable[[list[list[int]]], list[list[int]]], *, extra=True) -> bool:
    try:
        return bool(extra) and not _grid_equal(_authority_output(grid), rival(grid))
    except Exception:
        return False


def _code_mapping_visible(code: int):
    return lambda grid: _rival_visible(grid, _wrong_code_map, extra=code in _codes(grid))


SEMANTIC_RIVALS = {
    "wrong_code_map": _wrong_code_map,
    "independent_transforms": _independent_transforms,
    "omit_initial": _omit_initial,
    "reverse_code_order": _reverse_code_order,
    "bottom_align_panels": _bottom_align_panels,
    "deduplicate_codes": _deduplicate_codes,
}

SEMANTIC_WITNESSES = {
    "code_1_mapping_visible": _code_mapping_visible(1),
    "code_2_mapping_visible": _code_mapping_visible(2),
    "code_3_mapping_visible": _code_mapping_visible(3),
    "code_4_mapping_visible": _code_mapping_visible(4),
    "cumulative_vs_independent_visible": lambda grid: _rival_visible(grid, _independent_transforms),
    "initial_panel_visible": lambda grid: _rival_visible(grid, _omit_initial),
    "code_order_visible": lambda grid: _rival_visible(grid, _reverse_code_order),
    "rectangular_top_alignment_visible": lambda grid: _rival_visible(
        grid,
        _bottom_align_panels,
        extra=_analysis(grid)["motif_shape"] in ("wide", "tall"),
    ),
    "repeated_code_visible": lambda grid: _rival_visible(
        grid,
        _deduplicate_codes,
        extra=len(_codes(grid)) != len(set(_codes(grid))),
    ),
}

WITNESS_RIVALS = {
    "code_1_mapping_visible": ["wrong_code_map"],
    "code_2_mapping_visible": ["wrong_code_map"],
    "code_3_mapping_visible": ["wrong_code_map"],
    "code_4_mapping_visible": ["wrong_code_map"],
    "cumulative_vs_independent_visible": ["independent_transforms"],
    "initial_panel_visible": ["omit_initial"],
    "code_order_visible": ["reverse_code_order"],
    "rectangular_top_alignment_visible": ["bottom_align_panels"],
    "repeated_code_visible": ["deduplicate_codes"],
}

# The same named alternatives are scored over complete lessons.  They are also
# canonical-shortcut probes: if canonical examples ever cease to refute one,
# the corresponding witness must supply a generated killing example.
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require the four-demo schedule to eliminate every named rival rule."""
    reasons: list[str] = []
    seen_codes = {code for demo in demos for code in _codes(demo["input"])}
    if seen_codes != {1, 2, 3, 4}:
        reasons.append(f"demos expose transform codes {sorted(seen_codes)}, not all 1..4")
    if not any(len(_codes(demo["input"])) != len(set(_codes(demo["input"]))) for demo in demos):
        reasons.append("demos contain no repeated-code sequence")
    if not any(_analysis(demo["input"])["motif_shape"] in ("wide", "tall") for demo in demos):
        reasons.append("demos contain no rectangular crop to expose top alignment")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _grid_equal(competitor(demo["input"]), demo["output"])
                for demo in demos
            )
            changes_query = not _grid_equal(competitor(query["input"]), query["output"])
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
