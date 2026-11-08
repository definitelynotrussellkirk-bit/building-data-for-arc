"""Reviewed generator for ``fill_the_frame_by_the_singleton_key``.

The selected Racket authority finds the bounding box of color 8, finds the
unique non-{0,8} color that occurs once, and paints the strict bbox interior
with that key color.  This sampler keeps one complete color-8 frame and one
outside singleton key, while scheduled repeated-color distractors teach that
*singleton count* selects the key and that the whole interior is overwritten.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "2c8fab02e3fe"
TASK_ID = GENERATOR_ID
RULE_HASH = "716ceab8f6ca"
VERSION = "2.2.0"
SUMMARY = (
    "A complete hollow color-8 rectangular frame and one singleton key color "
    "appear on a zero background. The key is outside the frame. Paint every "
    "strict-interior cell of the frame with the singleton key color, preserving "
    "the frame and the key. Optional repeated-color decoys test singleton "
    "selection and interior overwrite behavior; seed-phased roles prevent key "
    "color, side, decoy mode, and geometry from becoming fixed proxies."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

INVARIANTS = [
    "background is color 0",
    "all color-8 cells form exactly one complete hollow rectangle of at least 4x4",
    "exactly one non-{0,8} color occurs once; that singleton key lies outside the frame bbox",
    "zero or one decoy color occurs exactly twice, never on the frame border",
    "the frame's strict interior is nonempty and is wholly painted by the rule",
]

KEY_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
KEY_SIDES = ("top", "right", "bottom", "left")
DECOY_MODES = ("clean", "outside_pair", "inside_pair", "split_pair")

AXES = {
    "grid_h": {"type": "int", "default": "four-profile schedule", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "four-profile schedule", "valid": "10..18"},
    "frame_h": {"type": "int", "default": "four-profile schedule", "valid": "4..7"},
    "frame_w": {"type": "int", "default": "four-profile schedule", "valid": "4..9"},
    "key_color": {"type": "color", "default": "seed-phased eight-color cycle", "valid": "1..7|9"},
    "key_side": {"type": "str", "default": "seed-phased four-side cycle", "valid": "top|right|bottom|left"},
    "decoy_mode": {
        "type": "str",
        "default": "seed-phased four-mode cycle",
        "valid": "clean|outside_pair|inside_pair|split_pair",
    },
}

# Every advertised joint combination is constructive.  The smallest canvas is
# still one row and one column larger than the largest frame, and a 4x4 frame
# has four strict-interior cells, enough for an inside pair.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Every four consecutive samples still contain all four key sides and all four
# decoy roles, but independent seed-derived phase shifts prevent side, geometry,
# decoy role, and key color from becoming globally interchangeable shortcuts.
# The alternating canonical/novel palette ordering guarantees that every
# four-pair lesson contains at least two colors outside the old fixed mapping.
_KEY_COLOR_CYCLE = (5, 1, 7, 2, 6, 3, 4, 9)


def _scheduled_role(seed: int, sample_index: int) -> dict[str, object]:
    seed_value = int(seed)
    return {
        "key_color": _KEY_COLOR_CYCLE[(sample_index + (seed_value // 4)) % len(_KEY_COLOR_CYCLE)],
        "key_side": KEY_SIDES[(sample_index + seed_value) % len(KEY_SIDES)],
        "decoy_mode": DECOY_MODES[(sample_index + (seed_value // 2)) % len(DECOY_MODES)],
    }

_GEOMETRY_BY_BAND = {
    "easy": (
        (8, 10, 5, 5),
        (8, 11, 4, 6),
        (9, 12, 4, 9),
        (10, 12, 7, 9),
    ),
    "medium": (
        (8, 10, 5, 5),
        (10, 12, 7, 9),
        (8, 11, 4, 6),
        (9, 12, 4, 9),
    ),
    "hard": (
        (8, 10, 5, 5),
        (14, 16, 7, 9),
        (9, 12, 4, 9),
        (10, 12, 7, 9),
    ),
}


def _validate_request(difficulty, overrides) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "frame_h", "frame_w", "key_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    for name in ("key_side", "decoy_mode"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} must be a string")
    return "medium" if difficulty is None else difficulty


def _scheduled_choice(ctx, overrides, label, legal, default):
    options = tuple(legal) if overrides.get(label) is not None else (default,)
    return ctx.draw_choice(label, options)


def _frame_position(ctx, h: int, w: int, fh: int, fw: int, side: str) -> tuple[int, int]:
    rng = ctx.draw_rng("frame_position")
    if side == "top":
        top = rng.randint(1, h - fh)
        left = rng.randint(0, w - fw)
    elif side == "bottom":
        top = rng.randint(0, h - fh - 1)
        left = rng.randint(0, w - fw)
    elif side == "left":
        top = rng.randint(0, h - fh)
        left = rng.randint(1, w - fw)
    elif side == "right":
        top = rng.randint(0, h - fh)
        left = rng.randint(0, w - fw - 1)
    else:  # guarded by draw_choice, retained as a defensive diagnostic
        raise ValueError(f"unsupported key side: {side!r}")
    return top, left


def _key_candidates(h, w, top, left, bottom, right, side):
    if side == "top":
        return [(r, c) for r in range(0, top) for c in range(left, right + 1)]
    if side == "bottom":
        return [(r, c) for r in range(bottom + 1, h) for c in range(left, right + 1)]
    if side == "left":
        return [(r, c) for r in range(top, bottom + 1) for c in range(0, left)]
    return [(r, c) for r in range(top, bottom + 1) for c in range(right + 1, w)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    residue = sample_index % LESSON_SCHEDULE_PERIOD
    role = _scheduled_role(seed, sample_index)
    default_h, default_w, default_fh, default_fw = _GEOMETRY_BY_BAND[band][residue]

    h = _scheduled_choice(ctx, overrides, "grid_h", range(8, 17), default_h)
    w = _scheduled_choice(ctx, overrides, "grid_w", range(10, 19), default_w)
    fh = _scheduled_choice(ctx, overrides, "frame_h", range(4, 8), default_fh)
    fw = _scheduled_choice(ctx, overrides, "frame_w", range(4, 10), default_fw)
    key_color = _scheduled_choice(ctx, overrides, "key_color", KEY_COLORS, role["key_color"])
    key_side = _scheduled_choice(ctx, overrides, "key_side", KEY_SIDES, role["key_side"])
    decoy_mode = _scheduled_choice(ctx, overrides, "decoy_mode", DECOY_MODES, role["decoy_mode"])

    top, left = _frame_position(ctx, h, w, fh, fw, key_side)
    bottom, right = top + fh - 1, left + fw - 1
    grid = full_grid(h, w, 0)
    draw_rect_outline(grid, top, left, fh, fw, 8)

    key_candidates = _key_candidates(h, w, top, left, bottom, right, key_side)
    key_position = ctx.draw_rng("key_position").choice(key_candidates)
    grid[key_position[0]][key_position[1]] = key_color

    if decoy_mode != "clean":
        decoy_color = ctx.draw_rng("decoy_color").choice(
            [color for color in KEY_COLORS if color != key_color]
        )
        interior = [
            (r, c)
            for r in range(top + 1, bottom)
            for c in range(left + 1, right)
        ]
        outside = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if not (top <= r <= bottom and left <= c <= right)
            and (r, c) != key_position
        ]
        rng = ctx.draw_rng("decoy_positions")
        if decoy_mode == "outside_pair":
            chosen = rng.sample(outside, 2)
        elif decoy_mode == "inside_pair":
            chosen = rng.sample(interior, 2)
        else:
            chosen = [rng.choice(interior), rng.choice(outside)]
        for r, c in chosen:
            grid[r][c] = decoy_color

    return grid


def _rectangular(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def analyze_grid(grid) -> dict[str, object]:
    """Parse the declared task domain or raise a diagnostic ``ValueError``."""
    h, w = _rectangular(grid)
    frame_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    if not frame_cells:
        raise ValueError("missing color-8 frame")
    top = min(r for r, _ in frame_cells)
    left = min(c for _, c in frame_cells)
    bottom = max(r for r, _ in frame_cells)
    right = max(c for _, c in frame_cells)
    frame_h, frame_w = bottom - top + 1, right - left + 1
    if frame_h < 4 or frame_w < 4:
        raise ValueError(f"frame must be at least 4x4, got {frame_h}x{frame_w}")
    perimeter = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }
    if frame_cells != perimeter:
        missing = len(perimeter - frame_cells)
        extra = len(frame_cells - perimeter)
        raise ValueError(
            f"color-8 cells must be one complete hollow rectangle (missing={missing}, extra={extra})"
        )

    counts = Counter(value for row in grid for value in row)
    singleton_colors = [
        color for color, count in counts.items() if color not in (0, 8) and count == 1
    ]
    if len(singleton_colors) != 1:
        raise ValueError(f"expected exactly one non-{{0,8}} singleton key, got {singleton_colors}")
    key_color = singleton_colors[0]
    key_positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == key_color
    ]
    key_position = key_positions[0]
    kr, kc = key_position
    if top <= kr <= bottom and left <= kc <= right:
        raise ValueError("singleton key must lie outside the frame bounding box")

    decoy_colors = [color for color in counts if color not in (0, 8, key_color)]
    if len(decoy_colors) > 1:
        raise ValueError(f"expected at most one repeated decoy color, got {decoy_colors}")
    decoy_positions: list[tuple[int, int]] = []
    if decoy_colors:
        decoy_color = decoy_colors[0]
        if counts[decoy_color] != 2:
            raise ValueError(
                f"decoy color must occur exactly twice, got color {decoy_color} count {counts[decoy_color]}"
            )
        decoy_positions = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == decoy_color
        ]

    def strict_inside(point):
        r, c = point
        return top < r < bottom and left < c < right

    def outside(point):
        r, c = point
        return not (top <= r <= bottom and left <= c <= right)

    if not decoy_positions:
        decoy_mode = "clean"
    else:
        inside_count = sum(strict_inside(point) for point in decoy_positions)
        outside_count = sum(outside(point) for point in decoy_positions)
        if inside_count == 2:
            decoy_mode = "inside_pair"
        elif outside_count == 2:
            decoy_mode = "outside_pair"
        elif inside_count == 1 and outside_count == 1:
            decoy_mode = "split_pair"
        else:
            raise ValueError("decoy cells must be strictly inside or outside the frame bbox")

    # Generated keys are aligned with exactly one side.  Canonical data also
    # contains a diagonal bottom-left key; row relation takes precedence there.
    if kr < top:
        key_side = "top"
    elif kr > bottom:
        key_side = "bottom"
    elif kc < left:
        key_side = "left"
    elif kc > right:
        key_side = "right"
    else:  # the inside case was rejected above
        raise ValueError("could not classify key side")

    return {
        "grid_h": h,
        "grid_w": w,
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "frame_h": frame_h,
        "frame_w": frame_w,
        "key_color": key_color,
        "key_position": key_position,
        "key_side": key_side,
        "decoy_mode": decoy_mode,
        "decoy_positions": tuple(decoy_positions),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    try:
        analyze_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    """The complete lawful manifold sampled here, including decoy witnesses."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    info = analyze_grid(grid)
    return {name: info[name] for name in AXES}


def _paint_interior(grid, color, *, preserve_existing=False):
    info = analyze_grid(grid)
    out = [list(row) for row in grid]
    for r in range(info["top"] + 1, info["bottom"]):
        for c in range(info["left"] + 1, info["right"]):
            if not preserve_existing or out[r][c] == 0:
                out[r][c] = color
    return out


def rule_mirror(grid):
    """Independent Python mirror for tests/diagnostics; Racket stays authority."""
    info = analyze_grid(grid)
    return _paint_interior(grid, info["key_color"])


oracle_output = rule_mirror


def _rival_most_frequent_nonframe_color(grid):
    counts = Counter(value for row in grid for value in row if value not in (0, 8))
    if not counts:
        return [list(row) for row in grid]
    color = max(sorted(counts), key=lambda value: counts[value])
    return _paint_interior(grid, color)


def _rival_preserve_existing_interior(grid):
    info = analyze_grid(grid)
    return _paint_interior(grid, info["key_color"], preserve_existing=True)


def _rival_constant_five(grid):
    return _paint_interior(grid, 5)


def _rival_square_only(grid):
    info = analyze_grid(grid)
    if info["frame_h"] != info["frame_w"]:
        return [list(row) for row in grid]
    return rule_mirror(grid)


def _rival_below_only(grid):
    info = analyze_grid(grid)
    if info["key_position"][0] <= info["bottom"]:
        return [list(row) for row in grid]
    return rule_mirror(grid)


_OLD_SIDE_COLOR = {"left": 5, "right": 7, "top": 6, "bottom": 4}


def _rival_old_side_color_lookup(grid):
    """The fixed side→color rule that fit the first reviewed schedule."""
    info = analyze_grid(grid)
    return _paint_interior(grid, _OLD_SIDE_COLOR[info["key_side"]])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "most_frequent_nonframe_color": _rival_most_frequent_nonframe_color,
    "preserve_existing_interior": _rival_preserve_existing_interior,
    "constant_five": _rival_constant_five,
    "square_only": _rival_square_only,
    "below_only": _rival_below_only,
    "old_side_color_lookup": _rival_old_side_color_lookup,
}

# These two wrong rules fit every canonical labelled pair because canonical
# inputs have no repeated distractor and an empty interior.
CANONICAL_SHORTCUTS = {
    "most_frequent_nonframe_color": _rival_most_frequent_nonframe_color,
    "preserve_existing_interior": _rival_preserve_existing_interior,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_repeated_color(grid):
    return analyze_grid(grid)["decoy_mode"] != "clean"


def _witness_interior_overwrite(grid):
    return analyze_grid(grid)["decoy_mode"] in ("inside_pair", "split_pair")


def _witness_non_five(grid):
    return analyze_grid(grid)["key_color"] != 5


def _witness_non_square(grid):
    info = analyze_grid(grid)
    return info["frame_h"] != info["frame_w"]


def _witness_key_not_below(grid):
    return analyze_grid(grid)["key_side"] != "bottom"


def _witness_side_color_decoupled(grid):
    return _rival_old_side_color_lookup(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "repeated_color_distractor": _witness_repeated_color,
    "interior_overwrite": _witness_interior_overwrite,
    "non_five_key": _witness_non_five,
    "non_square_frame": _witness_non_square,
    "key_not_below": _witness_key_not_below,
    "side_color_decoupled": _witness_side_color_decoupled,
}
WITNESS_RIVALS = {
    "repeated_color_distractor": ["most_frequent_nonframe_color"],
    "interior_overwrite": ["preserve_existing_interior"],
    "non_five_key": ["constant_five"],
    "non_square_frame": ["square_only"],
    "key_not_below": ["below_only"],
    "side_color_decoupled": ["old_side_color_lookup"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return named surviving-rival diagnostics for one labelled lesson."""
    official_query = rule_mirror(query["input"])
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != official_query:
                reasons.append(f"demonstrations do not rule out rival {name}")
    return reasons
