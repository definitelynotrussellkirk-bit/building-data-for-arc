"""Generator for Transform Timeline Gallery (task ``167a1374f6c3``).

The first row is a left-to-right program of transform codes.  A monochrome
motif appears below one blank separator row.  The output starts with the
motif's tight crop, then appends the *cumulative* state after each code, with
one blank column between top-aligned panels.

Code map: 1=rotate clockwise, 2=rotate 180 degrees,
3=rotate counterclockwise, 4=flip left/right.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "167a1374f6c3"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "91349b01b34b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read contiguous transform codes from row 0 until the first zero. Crop the "
    "monochrome motif below the blank separator row. Output the original crop "
    "followed by every cumulative transform state, top-aligned with one blank "
    "column between panels. Codes 1/2/3/4 mean rotate-cw/rotate-180/"
    "rotate-ccw/flip-lr."
)

INVARIANTS = [
    "background is 0 and every value is an ARC color 0..9",
    "row 0 contains 1..5 transform codes from 1..4 contiguously from column 0",
    "row 1 is entirely blank",
    "rows 2+ contain one monochrome motif of 3..8 cells",
    "the motif may be connected or disconnected, matching canonical support",
    "the motif crop is 2..4 by 2..4 and keeps every gallery within 30x30",
]

CONNECTIVITY_PROFILES = ("connected", "disconnected")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-slot curriculum over 7, 8, and 14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "three-slot curriculum over 10, 12, and 16",
        "valid": "10..16",
    },
    "n_codes": {
        "type": "int",
        "default": "three-slot curriculum over 2..3",
        "valid": "1..5",
    },
    "motif_color": {
        "type": "color",
        "default": "rng 5..9",
        "valid": "5..9",
    },
    "motif_cells": {
        "type": "int",
        "default": "three-slot curriculum over 4..6",
        "valid": "3..8",
    },
    "motif_connectivity": {
        "type": "str",
        "default": "three-slot curriculum covers both classes",
        "valid": "connected|disconnected",
    },
}

# Every declared boundary combination is constructible. Unexpected rejection is
# therefore a defect rather than an undocumented compatibility exception.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

# Any three consecutive indexes visit every slot.  Thus every generated lesson
# exposes all code meanings, a repeated code, connected and disconnected
# motifs, and a rectangular crop.  Two slots deliberately match canonical
# dimension profiles while one expands the lawful support envelope.
_SCHEDULE = (
    {
        "name": "repeat_disconnected_canonical",
        "codes": (1, 1, 4),
        "cells": 4,
        "connectivity": "disconnected",
        "h": 8,
        "w": 12,
    },
    {
        "name": "halfturn_ccw_expanded",
        "codes": (2, 3),
        "cells": 5,
        "connectivity": "connected",
        "h": 14,
        "w": 16,
    },
    {
        "name": "flip_cw_ccw_canonical",
        "codes": (4, 1, 3),
        "cells": 6,
        "connectivity": "connected",
        "h": 7,
        "w": 10,
    },
)
SCHEDULE_PROFILES = tuple(slot["name"] for slot in _SCHEDULE)

# Tight, transform-sensitive binary motifs.  D4 variants are selected at draw
# time, so a compact auditable catalog still yields broad lawful support.
_SHAPES: dict[tuple[int, str], tuple[tuple[str, ...], ...]] = {
    (3, "connected"): (("11", "10"),),
    (4, "connected"): (("111", "100"),),
    (5, "connected"): (("010", "111", "100"),),
    (6, "connected"): (("111", "101", "100"),),
    (7, "connected"): (("0011", "1110", "1000", "1000"),),
    (8, "connected"): (("1111", "1010", "1000", "1000"),),
    (3, "disconnected"): (("101", "010"),),
    (4, "disconnected"): (("101", "110"),),
    (5, "disconnected"): (("101", "110", "001"),),
    (6, "disconnected"): (("1011", "1100", "0010"),),
    (7, "disconnected"): (("1011", "1100", "0011"),),
    (8, "disconnected"): (("1011", "1100", "0011", "1000"),),
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
    value = overrides.get("motif_connectivity")
    if value is not None and value not in CONNECTIVITY_PROFILES:
        raise ValueError(
            f"motif_connectivity must be one of {CONNECTIVITY_PROFILES!r}"
        )


def _scheduled_int(
    ctx,
    label: str,
    scheduled: int,
    lo: int,
    hi: int,
    overrides: dict[str, Any],
) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _scheduled_choice(
    ctx,
    label: str,
    scheduled: str,
    options: tuple[str, ...],
    overrides: dict[str, Any],
) -> str:
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _rows_key(grid: list[list[int]]) -> tuple[str, ...]:
    return tuple("".join(str(value) for value in row) for row in grid)


def _d4_variants(rows: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    state = [[int(value) for value in row] for row in rows]
    variants: set[tuple[str, ...]] = set()
    for _ in range(4):
        variants.add(_rows_key(state))
        variants.add(_rows_key(_flip_lr(state)))
        state = _rotate_cw(state)
    return tuple(sorted(variants))


def _shape_rows(cells: int, connectivity: str, rng) -> tuple[str, ...]:
    base = rng.choice(_SHAPES[(cells, connectivity)])
    return rng.choice(_d4_variants(base))


def _code_program(n_codes: int, rng) -> list[int]:
    codes = [1, 2, 3, 4]
    rng.shuffle(codes)
    if n_codes <= 4:
        return codes[:n_codes]
    return codes + [codes[0]]


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

    h = _scheduled_int(ctx, "grid_h", slot["h"], 7, 14, overrides)
    w = _scheduled_int(ctx, "grid_w", slot["w"], 10, 16, overrides)
    n_codes = _scheduled_int(
        ctx, "n_codes", len(slot["codes"]), 1, 5, overrides
    )
    motif_cells = _scheduled_int(
        ctx, "motif_cells", slot["cells"], 3, 8, overrides
    )
    motif_connectivity = _scheduled_choice(
        ctx,
        "motif_connectivity",
        slot["connectivity"],
        CONNECTIVITY_PROFILES,
        overrides,
    )
    motif_color = ctx.draw_color("motif_color", exclude=range(5))

    code_rng = ctx.draw_rng(f"codes:{band_tag}")
    if overrides.get("n_codes") is None:
        codes = list(slot["codes"])
        code_rng.shuffle(codes)
    else:
        codes = _code_program(n_codes, code_rng)

    shape_rng = ctx.draw_rng(f"shape_variant:{band_tag}")
    rows = _shape_rows(motif_cells, motif_connectivity, shape_rng)
    sh, sw = len(rows), len(rows[0])

    grid = full_grid(h, w, 0)
    for column, code in enumerate(codes):
        grid[0][column] = code

    placement_rng = ctx.draw_rng(f"placement:{band_tag}")
    r0 = placement_rng.randint(2, h - sh)
    c0 = placement_rng.randint(0, w - sw)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value == "1":
                grid[r0 + r][c0 + c] = motif_color
    return grid


def _components(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _codes(grid: list[list[int]]) -> list[int]:
    codes: list[int] = []
    for value in grid[0]:
        if value == 0:
            break
        codes.append(value)
    return codes


def _crop_body(grid: list[list[int]]) -> list[list[int]]:
    points = [
        (r, c)
        for r in range(1, len(grid))
        for c, value in enumerate(grid[r])
        if value != 0
    ]
    if not points:
        raise ValueError("no nonzero motif below the code row")
    r1, r2 = min(r for r, _ in points), max(r for r, _ in points)
    c1, c2 = min(c for _, c in points), max(c for _, c in points)
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


_TRANSFORMS: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
    1: _rotate_cw,
    2: _rotate_180,
    3: _rotate_ccw,
    4: _flip_lr,
}

# A plausible neighboring-task codebook, deliberately wrong for this task.
_WRONG_TRANSFORMS: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
    1: _flip_lr,
    2: _rotate_cw,
    3: _rotate_180,
    4: _flip_ud,
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
    codes = _codes(grid)
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


def _grid_equal(left: list[list[int]], right: list[list[int]]) -> bool:
    return left == right


def _analysis(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "codes": [],
        "motif_cells": 0,
        "motif_color": None,
        "motif_connectivity": None,
        "motif_shape": None,
        "bbox": None,
        "orbit_size": 0,
    }
    if not isinstance(grid, list) or not grid or not all(
        isinstance(row, list) for row in grid
    ):
        result["errors"].append("grid must be a nonempty list of rows")
        return result
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        result["errors"].append("grid must be rectangular and nonempty")
        return result
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        result["errors"].append("grid values must be integer ARC colors 0..9")
        return result

    height = len(grid)
    if not 7 <= height <= 14:
        result["errors"].append(f"grid height must be 7..14, got {height}")
    if not 10 <= width <= 16:
        result["errors"].append(f"grid width must be 10..16, got {width}")

    stop = next(
        (index for index, value in enumerate(grid[0]) if value == 0), width
    )
    codes = grid[0][:stop]
    result["codes"] = codes
    if not 1 <= len(codes) <= 5:
        result["errors"].append(
            f"expected 1..5 contiguous row-0 codes, got {codes}"
        )
    if any(code not in (1, 2, 3, 4) for code in codes):
        result["errors"].append(f"transform codes must be in 1..4, got {codes}")
    if any(value != 0 for value in grid[0][stop:]):
        result["errors"].append("row-0 codes must be contiguous from column 0")

    if height >= 2 and any(value != 0 for value in grid[1]):
        result["errors"].append("row 1 must be blank")

    body = [
        (r, c, grid[r][c])
        for r in range(2, height)
        for c in range(width)
        if grid[r][c] != 0
    ]
    result["motif_cells"] = len(body)
    if not 3 <= len(body) <= 8:
        result["errors"].append(f"motif must contain 3..8 cells, got {len(body)}")
    colors = {value for _, _, value in body}
    if len(colors) != 1:
        result["errors"].append(
            f"motif must be monochrome, got colors {sorted(colors)}"
        )
    else:
        color = next(iter(colors))
        result["motif_color"] = color
        if not 5 <= color <= 9:
            result["errors"].append(f"motif color must be 5..9, got {color}")

    cells = {(r, c) for r, c, _ in body}
    if cells:
        component_count = _components(cells)
        result["motif_connectivity"] = (
            "connected" if component_count == 1 else "disconnected"
        )
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        bbox_height, bbox_width = r2 - r1 + 1, c2 - c1 + 1
        result["bbox"] = (r1, c1, r2, c2)
        if not (2 <= bbox_height <= 4 and 2 <= bbox_width <= 4):
            result["errors"].append(
                "motif crop must be 2..4 by 2..4, "
                f"got {bbox_height}x{bbox_width}"
            )
        result["motif_shape"] = (
            "square"
            if bbox_height == bbox_width
            else ("wide" if bbox_width > bbox_height else "tall")
        )

        binary = [
            [1 if (r, c) in cells else 0 for c in range(c1, c2 + 1)]
            for r in range(r1, r2 + 1)
        ]
        variants: set[tuple[tuple[int, ...], ...]] = set()
        state = binary
        for _ in range(4):
            variants.add(tuple(tuple(row) for row in state))
            variants.add(tuple(tuple(row) for row in _flip_lr(state)))
            state = _rotate_cw(state)
        result["orbit_size"] = len(variants)
        if len(variants) < 4:
            result["errors"].append(
                "motif symmetry hides too many transform meanings"
            )

        max_dimension = max(bbox_height, bbox_width)
        max_output_width = (len(codes) + 1) * max_dimension + len(codes)
        if max_dimension > 30 or max_output_width > 30:
            result["errors"].append(
                "cumulative gallery would exceed ARC 30x30 bounds"
            )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible input grammar."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold, including disconnected motifs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str | None]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe axes on malformed grid: "
            + "; ".join(analysis["errors"])
        )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_codes": len(analysis["codes"]),
        "motif_color": analysis["motif_color"],
        "motif_cells": analysis["motif_cells"],
        "motif_connectivity": analysis["motif_connectivity"],
    }


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]["name"]


def _rival_visible(
    grid,
    rival: Callable[[list[list[int]]], list[list[int]]],
    *,
    extra: bool = True,
) -> bool:
    try:
        return bool(extra) and not _grid_equal(_authority_output(grid), rival(grid))
    except Exception:
        return False


def _code_mapping_visible(code: int):
    return lambda grid: _rival_visible(
        grid, _wrong_code_map, extra=code in _codes(grid)
    )


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
    "cumulative_vs_independent_visible": lambda grid: _rival_visible(
        grid, _independent_transforms
    ),
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

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# All canonical programs use distinct codes, so this shortcut agrees with every
# canonical input/output pair.  Generated repeated-code lessons make it false.
CANONICAL_SHORTCUTS = {"deduplicate_codes": _deduplicate_codes}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the three-demo schedule to eliminate every named rival rule."""
    reasons: list[str] = []
    seen_codes = {code for demo in demos for code in _codes(demo["input"])}
    if seen_codes != {1, 2, 3, 4}:
        reasons.append(
            f"demos expose transform codes {sorted(seen_codes)}, not all 1..4"
        )
    if not any(
        len(_codes(demo["input"])) != len(set(_codes(demo["input"])))
        for demo in demos
    ):
        reasons.append("demos contain no repeated-code sequence")
    connectivity = {
        _analysis(demo["input"])["motif_connectivity"] for demo in demos
    }
    if connectivity != {"connected", "disconnected"}:
        reasons.append(
            "demos do not cover both connected and disconnected motifs"
        )
    if not any(
        _analysis(demo["input"])["motif_shape"] in ("wide", "tall")
        for demo in demos
    ):
        reasons.append(
            "demos contain no rectangular crop to expose top alignment"
        )

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _grid_equal(competitor(demo["input"]), demo["output"])
                for demo in demos
            )
            changes_query = not _grid_equal(
                competitor(query["input"]), query["output"]
            )
        except Exception as exc:
            reasons.append(
                f"competitor {name} raised {type(exc).__name__}: {exc}"
            )
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"competitor {name} fits every demo but changes the query"
            )
    return reasons
