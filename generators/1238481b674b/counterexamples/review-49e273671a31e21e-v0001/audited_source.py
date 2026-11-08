"""Generator for 1238481b674b — draw the missing-corner triangle.

The input is an orange field with exactly four gray cells. Three gray cells
occupy three corners of an axis-aligned square; the fourth is a strictly
interior distractor. The missing square corner selects a triangular outline:
paint the two square sides incident to the missing corner plus the diagonal
joining the two opposite present corners, while preserving every gray cell.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1238481b674b"
TASK_ID = "1238481b674b"
VERSION = "3.0.0"
RULE_HASH = "cbabe9d66374"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

# Exact single-axis overrides are always realizable. Multi-axis geometric
# contradictions are raised as structured incompatibilities below.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SUMMARY = (
    "On an orange-7 grid, exactly four gray-5 cells define a square: three "
    "are square corners and one is a strictly interior distractor. Infer the "
    "missing square corner. Paint color 8 on the two square sides incident "
    "to that missing corner and on the diagonal joining the other two "
    "corners. Paint only orange cells, so all four gray markers are preserved."
)

INVARIANTS = [
    "the input palette is exactly orange 7 and gray 5",
    "exactly four gray cells are present",
    "exactly three gray cells occupy corners of one axis-aligned square bbox",
    "the fourth gray cell lies strictly inside the selected triangle",
    "the square side length is 3..10 and the complete bbox is in bounds",
    "the missing corner selects two incident sides plus the opposite diagonal",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CORNER_NAMES = ("top_left", "top_right", "bottom_left", "bottom_right")
_DISTRACTOR_VARIANTS = ("near_missing", "clockwise", "counterclockwise")
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "translated_clockwise",
    "translated_counterclockwise",
    "expanded_near_missing",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 8 or difficulty-aware 9..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 8 or difficulty-aware 9..16",
        "valid": "8..16",
    },
    "side_len": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 3..10",
        "valid": "3..10",
    },
    "missing_corner": {
        "type": "str",
        "default": "balanced four-slot sample_index schedule",
        "valid": "|".join(_CORNER_NAMES),
    },
    "row_offset": {
        "type": "int",
        "default": "scheduled/random lawful square top row",
        "valid": "0..12",
    },
    "col_offset": {
        "type": "int",
        "default": "scheduled/random lawful square left column",
        "valid": "0..12",
    },
    "distractor_variant": {
        "type": "str",
        "default": "near_missing/cw/ccw four-slot schedule",
        "valid": "|".join(_DISTRACTOR_VARIANTS),
    },
}


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for key in ("grid_h", "grid_w", "side_len", "row_offset", "col_offset"):
        value = overrides.get(key)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            raise TypeError(f"override {key!r} must be an integer, got {value!r}")
    for key in ("missing_corner", "distractor_variant"):
        value = overrides.get(key)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"override {key!r} must be a string, got {value!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _canonical_side(difficulty: str | None) -> int:
    return {"easy": 3, "medium": 5, "hard": 7}.get(difficulty, 5)


def _band_dim_bounds(difficulty: str | None) -> tuple[int, int]:
    return {
        "easy": (9, 11),
        "medium": (10, 14),
        "hard": (12, 16),
    }.get(difficulty, (9, 14))


def _band_side_options(difficulty: str | None) -> tuple[int, ...]:
    return {
        "easy": (4, 5, 6),
        "medium": (4, 5, 6, 7, 8),
        "hard": (5, 6, 7, 8, 9, 10),
    }.get(difficulty, (4, 5, 6, 7, 8))


class IncompatibleOverrides(ValueError):
    """A deliberate rejection carrying the exact conflicting override axes."""

    def __init__(self, message: str, axes: tuple[str, ...]):
        super().__init__(message)
        self.incompatible_axes = axes


def _raise_incompatible(overrides: dict[str, Any], message: str, *axes: str) -> None:
    explicit = tuple(axis for axis in axes if overrides.get(axis) is not None)
    if len(explicit) >= 2:
        raise IncompatibleOverrides(message, explicit)
    raise ValueError(message)


def _planned_min_dim(
    *, target: int, side_floor: int, offset_override: int | None
) -> int:
    offset_floor = offset_override if offset_override is not None else 0
    needed = side_floor + offset_floor + 1
    return max(target, needed)


def _draw_dimension(ctx, label: str, *, target: int, minimum: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, 8, 16)
    lo = max(8, minimum)
    hi = max(lo, min(16, target))
    return ctx.draw_int(label, lo, hi)


def _draw_scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if ctx.overrides.get(label) is not None:
        value = ctx.draw_int(label, lo, hi)
    else:
        value = ctx.draw_int(label, scheduled, scheduled)
    return value


def _local_to_grid(missing: int, d: int, u: int, v: int) -> tuple[int, int]:
    """Map triangle-local coordinates from the missing corner into bbox offsets."""
    if missing == 0:
        return u, v
    if missing == 1:
        return u, d - v
    if missing == 2:
        return d - u, v
    if missing == 3:
        return d - u, d - v
    raise ValueError(f"invalid missing-corner index {missing}")


def _grid_to_local(missing: int, d: int, rel_r: int, rel_c: int) -> tuple[int, int]:
    if missing == 0:
        return rel_r, rel_c
    if missing == 1:
        return rel_r, d - rel_c
    if missing == 2:
        return d - rel_r, rel_c
    if missing == 3:
        return d - rel_r, d - rel_c
    raise ValueError(f"invalid missing-corner index {missing}")


def _variant_local(variant: str, d: int) -> tuple[int, int]:
    if variant == "near_missing":
        return 1, 1
    if d < 4:
        raise ValueError(
            f"distractor_variant={variant!r} is incompatible with side_len={d}; "
            "clockwise/counterclockwise require side_len >= 4"
        )
    if variant == "clockwise":
        return 1, d - 2
    if variant == "counterclockwise":
        return d - 2, 1
    raise ValueError(f"unknown distractor variant {variant!r}")


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts.update(height=h, width=w)
    if not 8 <= h <= 16:
        errors.append(f"grid height {h} outside 8..16")
    if not 8 <= w <= 16:
        errors.append(f"grid width {w} outside 8..16")

    palette = {value for row in grid for value in row}
    facts["palette"] = palette
    if palette != {5, 7}:
        errors.append(f"input palette must be exactly [5, 7], found {sorted(palette)}")

    marks = sorted(
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 5
    )
    facts["marks"] = tuple(marks)
    if len(marks) != 4:
        errors.append(f"expected exactly four gray markers, found {len(marks)}")
        return facts

    r0 = min(r for r, _ in marks)
    r1 = max(r for r, _ in marks)
    c0 = min(c for _, c in marks)
    c1 = max(c for _, c in marks)
    dr, dc = r1 - r0, c1 - c0
    facts.update(r0=r0, r1=r1, c0=c0, c1=c1, side_len=dr)
    if dr != dc:
        errors.append(f"marker bbox must be square, found height {dr} and width {dc}")
    if not 3 <= dr <= 10:
        errors.append(f"square side length {dr} outside 3..10")
    if errors:
        return facts

    corners = ((r0, c0), (r0, c1), (r1, c0), (r1, c1))
    occupied = [index for index, corner in enumerate(corners) if corner in marks]
    missing = [index for index, corner in enumerate(corners) if corner not in marks]
    if len(occupied) != 3 or len(missing) != 1:
        errors.append(
            "exactly three of the four square bbox corners must be gray; "
            f"occupied indices={occupied}"
        )
        return facts

    missing_index = missing[0]
    extras = [mark for mark in marks if mark not in corners]
    if len(extras) != 1:
        errors.append(f"expected one non-corner distractor, found {len(extras)}")
        return facts
    distractor = extras[0]
    rel_r, rel_c = distractor[0] - r0, distractor[1] - c0
    u, v = _grid_to_local(missing_index, dr, rel_r, rel_c)
    if not (u >= 1 and v >= 1 and u + v <= dr - 1):
        errors.append(
            "the non-corner gray marker must lie strictly inside the selected "
            f"triangle; local position={(u, v)}, side={dr}"
        )
        return facts

    variant_positions = {
        name: _variant_local(name, dr)
        for name in _DISTRACTOR_VARIANTS
        if name == "near_missing" or dr >= 4
    }
    variants = [name for name, position in variant_positions.items() if position == (u, v)]
    if len(variants) != 1:
        errors.append(
            "distractor must use one declared observable position; "
            f"local position={(u, v)}, allowed={variant_positions}"
        )
        return facts

    facts.update(
        corners=corners,
        missing_index=missing_index,
        missing_corner=_CORNER_NAMES[missing_index],
        distractor=distractor,
        distractor_local=(u, v),
        distractor_variant=variants[0],
        row_offset=r0,
        col_offset=c0,
    )
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete authority-valid input grammar."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact canonical morphology without overfitting placement."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analyze(grid)
    strict: list[str] = []
    if (facts["height"], facts["width"]) != (8, 8):
        strict.append("canonical profile requires an 8x8 grid")
    if facts["side_len"] not in {3, 5, 6, 7}:
        strict.append("canonical profile requires side length in {3,5,6,7}")
    if facts["distractor_variant"] != "near_missing":
        strict.append("canonical profile requires the near-missing distractor")
    return strict


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared axis exactly from a returned input grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "side_len": facts["side_len"],
        "missing_corner": facts["missing_corner"],
        "row_offset": facts["row_offset"],
        "col_offset": facts["col_offset"],
        "distractor_variant": facts["distractor_variant"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = int(sample_index) % len(SCHEDULE_PROFILES)

    side_override = overrides.get("side_len")
    variant_override = overrides.get("distractor_variant")
    variant_side_floor = 4 if variant_override in {"clockwise", "counterclockwise"} else 3
    effective_side_floor = side_override if side_override is not None else variant_side_floor
    row_override = overrides.get("row_offset")
    col_override = overrides.get("col_offset")
    if slot == 0 and not any(
        overrides.get(name) is not None
        for name in ("grid_h", "grid_w", "side_len", "row_offset", "col_offset")
    ):
        target_h = target_w = 8
    else:
        lo, hi = _band_dim_bounds(difficulty)
        target_h = ctx.draw_rng("grid_h_target").randint(lo, hi)
        target_w = ctx.draw_rng("grid_w_target").randint(lo, hi)

    min_h = _planned_min_dim(
        target=8, side_floor=effective_side_floor, offset_override=row_override
    )
    min_w = _planned_min_dim(
        target=8, side_floor=effective_side_floor, offset_override=col_override
    )
    if min_h > 16:
        _raise_incompatible(
            overrides,
            f"incompatible grid_h/side_len/row_offset/distractor_variant overrides "
            f"require height {min_h}, above maximum 16",
            "grid_h", "side_len", "row_offset", "distractor_variant",
        )
    if min_w > 16:
        _raise_incompatible(
            overrides,
            f"incompatible grid_w/side_len/col_offset/distractor_variant overrides "
            f"require width {min_w}, above maximum 16",
            "grid_w", "side_len", "col_offset", "distractor_variant",
        )
    h = _draw_dimension(ctx, "grid_h", target=target_h, minimum=min_h)
    w = _draw_dimension(ctx, "grid_w", target=target_w, minimum=min_w)

    max_side = min(
        10,
        h - 1 - (row_override if row_override is not None else 0),
        w - 1 - (col_override if col_override is not None else 0),
    )
    if max_side < effective_side_floor:
        _raise_incompatible(
            overrides,
            "incompatible grid_h/grid_w/row_offset/col_offset overrides leave "
            f"no lawful side length >= {effective_side_floor}",
            "grid_h", "grid_w", "side_len", "row_offset", "col_offset", "distractor_variant",
        )
    if side_override is not None:
        side = ctx.draw_int("side_len", 3, 10)
        if side > max_side:
            _raise_incompatible(
                overrides,
                f"incompatible grid_h/grid_w/side_len/row_offset/col_offset: "
                f"side_len={side}, maximum is {max_side}",
                "grid_h", "grid_w", "side_len", "row_offset", "col_offset",
            )
    elif slot == 0 and h == 8 and w == 8:
        scheduled = min(max(effective_side_floor, _canonical_side(difficulty)), max_side)
        side = ctx.draw_int("side_len", scheduled, scheduled)
    else:
        options = tuple(
            value
            for value in _band_side_options(difficulty)
            if effective_side_floor <= value <= max_side
        )
        if not options:
            options = tuple(range(effective_side_floor, max_side + 1))
        side = ctx.draw_choice("side_len", options)

    scheduled_missing = _CORNER_NAMES[slot]
    missing_name = _draw_scheduled_choice(
        ctx, "missing_corner", scheduled_missing, _CORNER_NAMES
    )
    missing_index = _CORNER_NAMES.index(missing_name)

    max_row = h - side - 1
    max_col = w - side - 1
    if row_override is not None:
        row_offset = _draw_scheduled_int(ctx, "row_offset", 0, 0, 12)
        if row_offset > max_row:
            _raise_incompatible(
                overrides,
                f"incompatible grid_h/side_len/row_offset: row_offset={row_offset}; "
                f"maximum is {max_row}",
                "grid_h", "side_len", "row_offset",
            )
    else:
        row_scheduled = (None, max_row, 0, max_row)[slot]
        row_offset = (
            ctx.draw_int("row_offset", 0, max_row)
            if row_scheduled is None
            else ctx.draw_int("row_offset", row_scheduled, row_scheduled)
        )
    if col_override is not None:
        col_offset = _draw_scheduled_int(ctx, "col_offset", 0, 0, 12)
        if col_offset > max_col:
            _raise_incompatible(
                overrides,
                f"incompatible grid_w/side_len/col_offset: col_offset={col_offset}; "
                f"maximum is {max_col}",
                "grid_w", "side_len", "col_offset",
            )
    else:
        col_scheduled = (None, max_col, max_col, 0)[slot]
        col_offset = (
            ctx.draw_int("col_offset", 0, max_col)
            if col_scheduled is None
            else ctx.draw_int("col_offset", col_scheduled, col_scheduled)
        )

    scheduled_variant = (
        "near_missing",
        "clockwise",
        "counterclockwise",
        "near_missing",
    )[slot]
    if side < 4 and scheduled_variant != "near_missing" and overrides.get(
        "distractor_variant"
    ) is None:
        scheduled_variant = "near_missing"
    variant = _draw_scheduled_choice(
        ctx, "distractor_variant", scheduled_variant, _DISTRACTOR_VARIANTS
    )
    if side < 4 and variant != "near_missing":
        _raise_incompatible(
            overrides,
            f"incompatible side_len/distractor_variant: side_len={side}, "
            f"distractor_variant={variant!r}; non-near variants require side_len >= 4",
            "side_len", "distractor_variant",
        )
    u, v = _variant_local(variant, side)

    r0, c0 = row_offset, col_offset
    r1, c1 = r0 + side, c0 + side
    corners = ((r0, c0), (r0, c1), (r1, c0), (r1, c1))
    grid = full_grid(h, w, 7)
    for index, (r, c) in enumerate(corners):
        if index != missing_index:
            grid[r][c] = 5
    rel_r, rel_c = _local_to_grid(missing_index, side, u, v)
    grid[r0 + rel_r][c0 + rel_c] = 5

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator emitted invalid grid: {errors}")
    expected = {
        "grid_h": h,
        "grid_w": w,
        "side_len": side,
        "missing_corner": missing_name,
        "row_offset": row_offset,
        "col_offset": col_offset,
        "distractor_variant": variant,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"axis observer mismatch: observed={observed}, expected={expected}")
    return grid


def _paint_if_background(grid: list[list[int]], r: int, c: int, color: int = 8) -> None:
    if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] == 7:
        grid[r][c] = color


def _paint_triangle(
    grid: list[list[int]], *, r0: int, c0: int, side: int, missing: int
) -> list[list[int]]:
    out = copy.deepcopy(grid)
    r1, c1 = r0 + side, c0 + side
    for k in range(side + 1):
        if missing == 0:
            cells = ((r0, c0 + k), (r0 + k, c0), (r0 + k, c1 - k))
        elif missing == 1:
            cells = ((r0, c0 + k), (r0 + k, c1), (r0 + k, c0 + k))
        elif missing == 2:
            cells = ((r1, c0 + k), (r0 + k, c0), (r0 + k, c0 + k))
        else:
            cells = ((r1, c0 + k), (r0 + k, c1), (r0 + k, c1 - k))
        for r, c in cells:
            _paint_if_background(out, r, c)
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror of the Racket authority; never output authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("grid is outside rule domain: " + "; ".join(facts["errors"]))
    return _paint_triangle(
        grid,
        r0=facts["r0"],
        c0=facts["c0"],
        side=facts["side_len"],
        missing=facts["missing_index"],
    )


def _valid_facts(grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _rival_always_top_left(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return copy.deepcopy(grid)
    return _paint_triangle(
        grid, r0=facts["r0"], c0=facts["c0"], side=facts["side_len"], missing=0
    )


def _rival_always_bottom_right(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return copy.deepcopy(grid)
    return _paint_triangle(
        grid, r0=facts["r0"], c0=facts["c0"], side=facts["side_len"], missing=3
    )


def _rival_two_incident_sides_only(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return copy.deepcopy(grid)
    out = copy.deepcopy(grid)
    r0, c0, side, missing = (
        facts["r0"], facts["c0"], facts["side_len"], facts["missing_index"]
    )
    r1, c1 = r0 + side, c0 + side
    for k in range(side + 1):
        if missing == 0:
            cells = ((r0, c0 + k), (r0 + k, c0))
        elif missing == 1:
            cells = ((r0, c0 + k), (r0 + k, c1))
        elif missing == 2:
            cells = ((r1, c0 + k), (r0 + k, c0))
        else:
            cells = ((r1, c0 + k), (r0 + k, c1))
        for r, c in cells:
            _paint_if_background(out, r, c)
    return out


def _rival_bbox_border(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return copy.deepcopy(grid)
    out = copy.deepcopy(grid)
    r0, c0, side = facts["r0"], facts["c0"], facts["side_len"]
    r1, c1 = r0 + side, c0 + side
    for k in range(side + 1):
        for r, c in ((r0, c0 + k), (r1, c0 + k), (r0 + k, c0), (r0 + k, c1)):
            _paint_if_background(out, r, c)
    return out


def _rival_solid_triangle(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return copy.deepcopy(grid)
    out = copy.deepcopy(grid)
    r0, c0, side, missing = (
        facts["r0"], facts["c0"], facts["side_len"], facts["missing_index"]
    )
    for rel_r in range(side + 1):
        for rel_c in range(side + 1):
            u, v = _grid_to_local(missing, side, rel_r, rel_c)
            if u >= 0 and v >= 0 and u + v <= side:
                _paint_if_background(out, r0 + rel_r, c0 + rel_c)
    return out


def _rival_erase_interior_marker(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return copy.deepcopy(grid)
    out = rule_mirror(grid)
    r, c = facts["distractor"]
    out[r][c] = 7
    return out


def _rival_fixed_origin(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return copy.deepcopy(grid)
    return _paint_triangle(
        grid, r0=0, c0=0, side=facts["side_len"], missing=facts["missing_index"]
    )


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "always_top_left_missing": _rival_always_top_left,
    "always_bottom_right_missing": _rival_always_bottom_right,
    "two_incident_sides_only": _rival_two_incident_sides_only,
    "full_bbox_border": _rival_bbox_border,
    "solid_triangle": _rival_solid_triangle,
    "erase_interior_gray": _rival_erase_interior_marker,
    "fixed_top_left_origin": _rival_fixed_origin,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "erase_interior_gray": _rival_erase_interior_marker,
    "solid_triangle": _rival_solid_triangle,
}


def _fact_witness(predicate: Callable[[dict[str, Any]], bool]):
    def witness(grid) -> bool:
        facts = _valid_facts(grid)
        return bool(facts is not None and predicate(facts))

    return witness


def _has_unpainted_triangle_interior(facts: dict[str, Any]) -> bool:
    side, missing = facts["side_len"], facts["missing_index"]
    distractor = facts["distractor_local"]
    for u in range(1, side):
        for v in range(1, side):
            if u + v <= side - 1 and (u, v) != distractor:
                rel_r, rel_c = _local_to_grid(missing, side, u, v)
                # Exclude the diagonal boundary; strict interior is enough.
                if u + v < side:
                    return True
    return False


SEMANTIC_WITNESSES = {
    "missing_top_left": _fact_witness(lambda f: f["missing_index"] == 0),
    "missing_top_right": _fact_witness(lambda f: f["missing_index"] == 1),
    "missing_bottom_left": _fact_witness(lambda f: f["missing_index"] == 2),
    "missing_bottom_right": _fact_witness(lambda f: f["missing_index"] == 3),
    "interior_gray_must_be_preserved": _fact_witness(lambda f: True),
    "diagonal_is_required": _fact_witness(lambda f: True),
    "full_square_border_is_wrong": _fact_witness(lambda f: True),
    "outline_not_solid": _fact_witness(_has_unpainted_triangle_interior),
    "translated_bbox": _fact_witness(lambda f: f["r0"] > 0 or f["c0"] > 0),
}
WITNESS_RIVALS = {
    "missing_top_left": ["always_bottom_right_missing"],
    "missing_top_right": ["always_top_left_missing"],
    "missing_bottom_left": ["always_top_left_missing"],
    "missing_bottom_right": ["always_top_left_missing"],
    "interior_gray_must_be_preserved": ["erase_interior_gray"],
    "diagonal_is_required": ["two_incident_sides_only"],
    "full_square_border_is_wrong": ["full_bbox_border"],
    "outline_not_solid": ["solid_triangle"],
    "translated_bbox": ["fixed_top_left_origin"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a named plausible wrong rule survives demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, item in enumerate([*demos, query]):
        label = f"demo {index}" if index < len(demos) else "query"
        try:
            input_grid = item["input"]
        except (KeyError, TypeError):
            reasons.append(f"{label} is missing an input grid")
            continue
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"{label} input is outside the teaching grammar: {errors}")
            continue
        official = rule_mirror(input_grid)
        if item.get("output") != official:
            reasons.append(f"{label} output does not match the missing-corner triangle rule")
    if reasons:
        return reasons

    query_answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"]
            for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    base = generate(8101, 2, difficulty="medium", side_len=6)
    facts = _analyze(base)
    fixtures: list[tuple[str, list[list[int]]]] = []

    three_markers = copy.deepcopy(base)
    r, c = facts["distractor"]
    three_markers[r][c] = 7
    fixtures.append(("pre_repair_three_marker_shortcut", three_markers))

    all_four_corners = copy.deepcopy(base)
    r, c = facts["distractor"]
    all_four_corners[r][c] = 7
    mr, mc = facts["corners"][facts["missing_index"]]
    all_four_corners[mr][mc] = 5
    fixtures.append(("four_bbox_corners_no_interior_distractor", all_four_corners))

    five_markers = copy.deepcopy(base)
    missing_local = next(
        (u, v)
        for u in range(1, facts["side_len"])
        for v in range(1, facts["side_len"])
        if u + v <= facts["side_len"] - 1
        and (u, v) != facts["distractor_local"]
    )
    rr, cc = _local_to_grid(
        facts["missing_index"], facts["side_len"], *missing_local
    )
    five_markers[facts["r0"] + rr][facts["c0"] + cc] = 5
    fixtures.append(("second_interior_distractor", five_markers))

    rectangular_bbox = copy.deepcopy(base)
    corner = facts["corners"][(facts["missing_index"] + 1) % 4]
    rectangular_bbox[corner[0]][corner[1]] = 7
    shifted = (corner[0], corner[1] + (1 if corner[1] + 1 < facts["width"] else -1))
    rectangular_bbox[shifted[0]][shifted[1]] = 5
    fixtures.append(("non_square_corner_bbox", rectangular_bbox))

    on_diagonal = copy.deepcopy(base)
    r, c = facts["distractor"]
    on_diagonal[r][c] = 7
    rr, cc = _local_to_grid(
        facts["missing_index"], facts["side_len"], 1, facts["side_len"] - 1
    )
    on_diagonal[facts["r0"] + rr][facts["c0"] + cc] = 5
    fixtures.append(("distractor_on_triangle_edge", on_diagonal))

    wrong_palette = copy.deepcopy(base)
    wrong_palette[0][0] = 0
    fixtures.append(("wrong_background_color", wrong_palette))

    fixtures.append(("already_transformed_output", rule_mirror(base)))
    return fixtures
