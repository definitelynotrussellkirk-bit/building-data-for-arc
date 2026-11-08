"""Generator for arc_additional_puzzle_bank_volume17:E116.

Canonical rule: find every color-6 cell, take their minimal axis-aligned
bounding box, and return that crop unchanged.  Non-6 cells inside the box are
preserved; non-6 distractors outside it are discarded.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "07a647c5c28d"
VERSION = "4.1.0"
TASK_ID = "07a647c5c28d"
RULE_HASH = "fa0093f9ce0e"

SUMMARY = (
    "Crop the input to the minimal bounding box containing every color-6 "
    "cell. The marker geometry varies between two disconnected diagonal "
    "markers, a connected border-L, and a connected interior cross. Small "
    "non-6 payloads inside the box must be preserved, while connected non-6 "
    "distractors outside the box must disappear."
)

# Three consecutive sample indices traverse all normal marker grammars. This
# prevents a materialized three-demo lesson from hiding connectivity, marker
# count, or the possibility of strictly interior color-6 cells.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "at least two color-6 cells are present",
    "the color-6 bbox is at least 2x2 and strictly smaller than the grid",
    "at least one nonzero non-6 distractor lies outside the color-6 bbox",
    "all returned grids are valid ARC grids and normal draws are non-identity",
]

DEGENERATE_TEXTURES = ("only_one_six", "six_at_corners", "no_six")
HELPFUL_TEXTURES = ("two_sixes", "plain", "interior_six")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 7..16",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..16",
        "valid": "7..16",
    },
    "box_h": {
        "type": "int",
        "default": "difficulty-aware 2..8",
        "valid": "2..8",
    },
    "box_w": {
        "type": "int",
        "default": "difficulty-aware 2..8",
        "valid": "2..8",
    },
    "texture": {
        "type": "str",
        "default": "sample_index cycle",
        "valid": "two_sixes|plain|interior_six",
        "doc": (
            "two_sixes uses only opposite-corner markers; plain uses a "
            "connected border-L with no strictly interior 6; interior_six "
            "uses a connected cross with strictly interior 6s"
        ),
    },
}

_FILL = (1, 2, 3, 4, 5, 7, 8, 9)
_DIFFICULTY_BOUNDS = {
    "easy": ((7, 10), (7, 10), (2, 4), (2, 4)),
    "medium": ((9, 13), (9, 13), (2, 6), (2, 6)),
    "hard": ((12, 16), (12, 16), (3, 8), (3, 8)),
}

_PROFILE_BOX_BOUNDS = {
    "easy": {
        "two_sixes": ((2, 2), (2, 3)),
        "plain": ((3, 4), (2, 2)),
        "interior_six": ((3, 3), (3, 4)),
    },
    "medium": {
        "two_sixes": ((2, 3), (2, 3)),
        "plain": ((4, 6), (2, 3)),
        "interior_six": ((3, 4), (5, 6)),
    },
    "hard": {
        "two_sixes": ((3, 4), (3, 4)),
        "plain": ((6, 8), (3, 4)),
        "interior_six": ((3, 5), (6, 8)),
    },
}


def _is_explicit(overrides: dict, name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _scheduled_texture(sample_index: int, overrides: dict) -> str:
    requested = overrides.get("texture")
    if requested is not None:
        if requested in DEGENERATE_TEXTURES:
            return requested
        if requested not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture override: {requested!r}")
        return requested

    scheduled = HELPFUL_TEXTURES[sample_index % len(HELPFUL_TEXTURES)]
    # A single exact 2-cell box override must remain legal in every band. If
    # the scheduled interior-cross grammar cannot fit, advance to the next
    # lawful normal grammar rather than silently changing the requested size.
    if scheduled == "interior_six" and (
        overrides.get("box_h") == 2 or overrides.get("box_w") == 2
    ):
        return "two_sixes"
    return scheduled


def _draw_grid_dimension(
    ctx,
    label: str,
    band_bounds: tuple[int, int],
    box_label: str,
    overrides: dict,
) -> int:
    if _is_explicit(overrides, label):
        return ctx.draw_int(label, 7, 16)

    lo, hi = band_bounds
    if _is_explicit(overrides, box_label):
        required = int(overrides[box_label]) + 2
        lo = max(lo, required)
        hi = max(hi, lo)
    if lo > 16:
        raise ValueError(
            f"{box_label}={overrides.get(box_label)!r} cannot fit inside "
            f"declared {label} range 7..16 with a one-cell margin"
        )
    return ctx.draw_int(label, lo, min(hi, 16))


def _draw_box_dimension(
    ctx,
    label: str,
    band_bounds: tuple[int, int],
    grid_size: int,
    texture: str,
    overrides: dict,
) -> int:
    minimum = 3 if texture == "interior_six" else 2
    maximum = min(8, grid_size - 2)
    if _is_explicit(overrides, label):
        value = ctx.draw_int(label, 2, 8)
        if value < minimum:
            raise ValueError(
                f"texture={texture!r} requires {label} >= {minimum}, got {value}"
            )
        if value > maximum:
            raise ValueError(
                f"{label}={value} does not fit inside grid dimension "
                f"{grid_size} with a one-cell margin"
            )
        return value

    lo, hi = band_bounds
    lo = max(lo, minimum)
    hi = min(hi, maximum)
    if hi < lo:
        # This can only arise from an explicit small grid dimension. Choose the
        # full feasible normal range before drawing; never draw then clamp.
        lo, hi = minimum, maximum
    if hi < lo:
        raise ValueError(
            f"no feasible {label} for grid dimension {grid_size} and "
            f"texture={texture!r}"
        )
    return ctx.draw_int(label, lo, hi)


def _marker_cells(
    top: int,
    left: int,
    box_h: int,
    box_w: int,
    texture: str,
    rng,
) -> set[tuple[int, int]]:
    bottom = top + box_h - 1
    right = left + box_w - 1

    if texture == "two_sixes":
        if rng.randrange(2):
            return {(top, left), (bottom, right)}
        return {(top, right), (bottom, left)}

    if texture == "plain":
        # A randomly oriented border-L is connected and spans the bbox without
        # requiring all four corners or any strictly interior marker.
        orientation = rng.randrange(4)
        if orientation == 0:
            return ({(top, c) for c in range(left, right + 1)} |
                    {(r, right) for r in range(top, bottom + 1)})
        if orientation == 1:
            return ({(top, c) for c in range(left, right + 1)} |
                    {(r, left) for r in range(top, bottom + 1)})
        if orientation == 2:
            return ({(bottom, c) for c in range(left, right + 1)} |
                    {(r, right) for r in range(top, bottom + 1)})
        return ({(bottom, c) for c in range(left, right + 1)} |
                {(r, left) for r in range(top, bottom + 1)})

    if texture == "interior_six":
        cross_row = rng.randint(top + 1, bottom - 1)
        cross_col = rng.randint(left + 1, right - 1)
        return ({(cross_row, c) for c in range(left, right + 1)} |
                {(r, cross_col) for r in range(top, bottom + 1)})

    raise ValueError(f"unknown normal texture: {texture!r}")


def _grow_connected(
    allowed: set[tuple[int, int]],
    rng,
    target_size: int,
) -> list[tuple[int, int]]:
    """Return up to target_size 4-connected cells from an allowed region."""
    if not allowed:
        return []
    chosen = [rng.choice(sorted(allowed))]
    chosen_set = set(chosen)
    while len(chosen) < target_size:
        frontier = sorted({
            (rr, cc)
            for r, c in chosen
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if (rr, cc) in allowed and (rr, cc) not in chosen_set
        })
        if not frontier:
            break
        cell = rng.choice(frontier)
        chosen.append(cell)
        chosen_set.add(cell)
    return chosen


def _paint_payload(
    grid: list[list[int]],
    marker_cells: set[tuple[int, int]],
    top: int,
    left: int,
    box_h: int,
    box_w: int,
    color: int,
    rng,
    sample_index: int,
) -> None:
    # Two of every three sequential examples contain a non-6 payload inside
    # the crop, defeating a marker-only-output shortcut while retaining one
    # canonical-like sparse example per lesson window.
    if sample_index % 3 == 0:
        return
    allowed = {
        (r, c)
        for r in range(top, top + box_h)
        for c in range(left, left + box_w)
        if (r, c) not in marker_cells
    }
    cells = _grow_connected(allowed, rng, 1 + rng.randrange(3))
    for r, c in cells:
        grid[r][c] = color


def _paint_outside_distractors(
    grid: list[list[int]],
    top: int,
    left: int,
    box_h: int,
    box_w: int,
    colors: tuple[int, int],
    rng,
    difficulty: str,
) -> None:
    h, w = len(grid), len(grid[0])
    inside = {
        (r, c)
        for r in range(top, top + box_h)
        for c in range(left, left + box_w)
    }
    available = {(r, c) for r in range(h) for c in range(w)} - inside
    component_count = 2 if difficulty == "hard" and len(available) >= 6 else 1
    for index in range(component_count):
        component = _grow_connected(available, rng, 2 + rng.randrange(2))
        if not component:
            break
        for r, c in component:
            grid[r][c] = colors[index % len(colors)]
        # Keep separately counted distractor components from touching.
        blocked = set(component)
        blocked.update(
            (rr, cc)
            for r, c in component
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        )
        available -= blocked


def _bbox_of_sixes(grid: list[list[int]]) -> tuple[int, int, int, int]:
    sixes = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    if not sixes:
        raise ValueError("color-6 bbox is undefined because no color-6 cells exist")
    rows = [r for r, _ in sixes]
    cols = [c for _, c in sixes]
    return min(rows), min(cols), max(rows), max(cols)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authoritative."""
    r1, c1, r2, c2 = _bbox_of_sixes(grid)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic axis from a valid returned input grid."""
    r1, c1, r2, c2 = _bbox_of_sixes(grid)
    sixes = [
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if grid[r][c] == 6
    ]
    if len(sixes) == 2:
        texture = "two_sixes"
    elif any(r1 < r < r2 and c1 < c < c2 for r, c in sixes):
        texture = "interior_six"
    else:
        texture = "plain"
    return {
        "box_h": r2 - r1 + 1,
        "box_w": c2 - c1 + 1,
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, identity, no-distractor, and rule-hiding scenes."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular with nonempty rows"]

    errors: list[str] = []
    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("grid contains a non-integer or color outside 0..9")
                return errors

    h, w = len(grid), width
    sixes = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 6
    ]
    if len(sixes) < 2:
        return [f"expected at least two color-6 cells, found {len(sixes)}"]

    r1, c1, r2, c2 = _bbox_of_sixes(grid)
    box_h, box_w = r2 - r1 + 1, c2 - c1 + 1
    if box_h < 2 or box_w < 2:
        errors.append(f"color-6 bbox must be at least 2x2, got {box_h}x{box_w}")
    if box_h >= h or box_w >= w:
        errors.append(
            f"color-6 bbox {box_h}x{box_w} must be smaller than grid {h}x{w}"
        )

    outside_nonzero = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if not (r1 <= r <= r2 and c1 <= c <= c2) and grid[r][c] != 0
    ]
    if not outside_nonzero:
        errors.append("expected at least one nonzero distractor outside the color-6 bbox")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty is None:
        difficulty = "medium"
    if difficulty not in _DIFFICULTY_BOUNDS:
        raise ValueError(f"difficulty must be easy, medium, or hard, got {difficulty!r}")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(sorted(unknown))}")

    texture = _scheduled_texture(sample_index, overrides)
    if texture in DEGENERATE_TEXTURES:
        ctx = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version=VERSION,
            task_id=TASK_ID,
            difficulty=difficulty,
            overrides=overrides,
        )
        return _draw_from_degenerate(texture, ctx)

    effective_overrides = dict(overrides)
    if not _is_explicit(overrides, "texture"):
        effective_overrides["texture"] = texture
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    texture_options = HELPFUL_TEXTURES if _is_explicit(overrides, "texture") else (texture,)
    texture = ctx.draw_choice("texture", texture_options)

    grid_h_bounds, grid_w_bounds, _, _ = _DIFFICULTY_BOUNDS[difficulty]
    box_h_bounds, box_w_bounds = _PROFILE_BOX_BOUNDS[difficulty][texture]
    h = _draw_grid_dimension(ctx, "grid_h", grid_h_bounds, "box_h", overrides)
    w = _draw_grid_dimension(ctx, "grid_w", grid_w_bounds, "box_w", overrides)
    box_h = _draw_box_dimension(ctx, "box_h", box_h_bounds, h, texture, overrides)
    box_w = _draw_box_dimension(ctx, "box_w", box_w_bounds, w, texture, overrides)

    rng = ctx.draw_rng("layout")
    max_top = h - box_h - 1
    max_left = w - box_w - 1
    position_zone = (int(seed) + int(sample_index)) % 3
    if position_zone == 0:
        top, left = 1, 1
    elif position_zone == 1:
        top, left = max_top, max_left
    elif rng.randrange(2):
        top, left = 1, max_left
    else:
        top, left = max_top, 1
    markers = _marker_cells(top, left, box_h, box_w, texture, rng)

    grid = full_grid(h, w, 0)
    for r, c in markers:
        grid[r][c] = 6

    payload_color, outside_color = rng.sample(_FILL, 2)
    _paint_payload(
        grid,
        markers,
        top,
        left,
        box_h,
        box_w,
        payload_color,
        rng,
        sample_index,
    )
    _paint_outside_distractors(
        grid,
        top,
        left,
        box_h,
        box_w,
        (outside_color, payload_color),
        rng,
        difficulty,
    )
    return grid


def _draw_from_degenerate(name, ctx):
    """Produce deterministic negative fixtures for self-check mutation tests."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 16)
    w = ctx.draw_int("grid_w", 7, 16)
    grid = full_grid(h, w, 0)
    if name == "no_six":
        grid[1][1] = 3
        return grid
    if name == "only_one_six":
        grid[rng.randint(1, h - 2)][rng.randint(1, w - 2)] = 6
        grid[0][0] = 3
        return grid
    if name == "six_at_corners":
        for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
            grid[r][c] = 6
        grid[h // 2][w // 2] = 3
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")
