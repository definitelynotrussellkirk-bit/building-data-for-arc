"""Generator for ARC task 4a1526f51fb4 — palette-recolored nested frames.

The input has one monochromatic family of concentric rectangular outlines above
an ordered palette on the bottom row.  The Racket oracle crops the outline
bounding box and recolors depth ``d`` with palette entry ``d``.

Normal draws mix exact canonical geometry profiles with generalized rectangular,
offset, palette-spaced, and four-depth witnesses.  Every declared axis is
recoverable from the returned grid; malformed/ambiguous teaching scenes are
rejected structurally by :func:`self_check`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "4a1526f51fb4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2e5956bb4999"

SUMMARY = (
    "A zero-background grid contains two to four concentric rectangular "
    "outlines in one placeholder color above an ordered, distinct non-zero "
    "palette on the bottom row.  The palette may carry one unused tail color "
    "after the entries needed by the frames.  Successive outlines are inset "
    "by two cells on every side.  Crop the outline bounding box, then recolor "
    "the outermost outline with the first palette color, the next outline with "
    "the second, and so on inward; the palette row is not copied to the output."
)

INVARIANTS = [
    "background is 0 and every non-bottom non-zero cell has one frame color",
    "the bottom row contains distinct non-zero palette colors in reading order",
    "the palette has one entry per outline plus at most one unused tail distractor",
    "successive outline bounding boxes are inset by exactly two cells per side",
    "at least one palette color differs from the frame color, so recoloring fires",
]

CANON_D2_SQUARE = "canon_d2_square_margin"
CANON_D3_RIGHT = "canon_d3_square_wide_right"
CANON_D2_WIDE = "canon_d2_wide_flush_top"
CANON_D3_LEFT = "canon_d3_square_left3"
CANON_D3_COMPACT = "canon_d3_square_compact"
GENERAL_D2_TALL = "general_d2_tall"
GENERAL_D2_WIDE = "general_d2_wide"
GENERAL_D3_RECT = "general_d3_rect"
GENERAL_D3_SPREAD = "general_d3_palette_spread"
GENERAL_D4_DEEP = "general_d4_deep"

SCENE_PROFILES = (
    CANON_D2_SQUARE,
    CANON_D3_RIGHT,
    CANON_D2_WIDE,
    CANON_D3_LEFT,
    CANON_D3_COMPACT,
    GENERAL_D2_TALL,
    GENERAL_D2_WIDE,
    GENERAL_D3_RECT,
    GENERAL_D3_SPREAD,
    GENERAL_D4_DEEP,
)
CANONICAL_PROFILES = frozenset(
    (CANON_D2_SQUARE, CANON_D3_RIGHT, CANON_D2_WIDE, CANON_D3_LEFT, CANON_D3_COMPACT)
)
PALETTE_RELATIONS = ("excludes_frame", "contains_frame")
PALETTE_TAILS = ("exact", "one_extra")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted canonical/generalized profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "frame_color": {
        "type": "color",
        "default": "weighted toward canonical color 8",
        "valid": "1..9",
    },
    "palette_relation": {
        "type": "str",
        "default": "rng excludes_frame|contains_frame",
        "valid": "|".join(PALETTE_RELATIONS),
    },
    "palette_tail": {
        "type": "str",
        "default": "rng exact|one_extra",
        "valid": "|".join(PALETTE_TAILS),
    },
}

# Exact official input-layout signatures.  Tuple fields are:
# (depths, frame_h, frame_w, top, left, right, gap_to_palette,
#  palette_start, palette_stride).
_FIXED_PROFILE_SPECS = {
    CANON_D2_SQUARE: (2, 7, 7, 1, 2, 3, 1, 0, 1),
    CANON_D3_RIGHT: (3, 9, 9, 1, 1, 3, 0, 0, 1),
    CANON_D2_WIDE: (2, 7, 9, 0, 1, 1, 1, 0, 1),
    CANON_D3_LEFT: (3, 9, 9, 1, 3, 2, 1, 0, 1),
    CANON_D3_COMPACT: (3, 9, 9, 1, 1, 1, 0, 0, 1),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, structurally valid lesson input."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = (int(seed) + int(sample_index)) % 4
    profile_options = (
        SCENE_PROFILES
        if "scene_profile" in overrides
        else _profile_draw_options(difficulty, slot)
    )
    profile = ctx.draw_choice("scene_profile", profile_options)
    # Duplicating 8 is an intentional prior, not an unrecorded branch.  Every
    # legal color remains overrideable and appears on ordinary draws.
    frame_color = ctx.draw_choice(
        "frame_color", tuple(range(1, 10)) + (8,) * 8
    )
    palette_relation = ctx.draw_choice("palette_relation", PALETTE_RELATIONS)
    tail_options = (
        PALETTE_TAILS
        if "palette_tail" in overrides
        else (("one_extra",) if slot in (1, 2) else ("exact",))
    )
    palette_tail = ctx.draw_choice("palette_tail", tail_options)

    spec = _profile_spec(profile, ctx.draw_rng("profile-variant"))
    (
        n_depths,
        frame_h,
        frame_w,
        top,
        left,
        right,
        gap,
        palette_start,
        palette_stride,
    ) = spec

    height = top + frame_h + gap + 1
    width = left + frame_w + right
    palette_count = n_depths + (palette_tail == "one_extra")
    last_palette_col = palette_start + palette_stride * (palette_count - 1)
    if last_palette_col >= width:
        raise AssertionError("profile palette does not fit its declared canvas")

    grid = full_grid(height, width, 0)
    palette = _draw_palette(
        palette_count,
        frame_color,
        palette_relation,
        ctx.draw_rng("palette-colors"),
    )
    for index, color in enumerate(palette):
        grid[-1][palette_start + index * palette_stride] = color

    r0, c0 = top, left
    r1, c1 = top + frame_h - 1, left + frame_w - 1
    for depth in range(n_depths):
        draw_frame(
            grid,
            r0 + 2 * depth,
            c0 + 2 * depth,
            r1 - 2 * depth,
            c1 - 2 * depth,
            frame_color,
        )

    requested = {
        "scene_profile": profile,
        "frame_color": frame_color,
        "palette_relation": palette_relation,
        "palette_tail": palette_tail,
    }
    observed = observe_overrides(grid)
    if observed != requested:
        raise AssertionError(
            f"internal axis drift: requested={requested}, observed={observed}"
        )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal invalid scene: " + "; ".join(errors))
    return grid


def _profile_draw_options(difficulty, slot):
    """A four-pair episode covers decisive depth/geometry branches by schedule."""
    d2 = (
        CANON_D2_SQUARE,
        CANON_D2_SQUARE,
        CANON_D2_WIDE,
        CANON_D2_WIDE,
        GENERAL_D2_TALL,
        GENERAL_D2_WIDE,
    )
    d3_canonical = (
        CANON_D3_RIGHT,
        CANON_D3_LEFT,
        CANON_D3_COMPACT,
        CANON_D3_RIGHT,
        CANON_D3_COMPACT,
    )
    d3_general = (
        GENERAL_D3_RECT,
        GENERAL_D3_RECT,
        GENERAL_D3_SPREAD,
        GENERAL_D3_SPREAD,
        CANON_D3_LEFT,
    )
    d4 = (GENERAL_D4_DEEP,)

    if difficulty == "easy":
        return (d2, d3_canonical, d2, d2)[slot]
    if difficulty == "hard":
        return (d3_canonical, d3_canonical, d3_general, d4)[slot]
    # The actual downstream materializer calls the generator without a band.
    # Its sequential sample_index=0..3 episode therefore gets d2, canonical d3,
    # generalized d3, and d4 in some seed-rotated order.
    return (d2, d3_canonical, d3_general, d4)[slot]


def _profile_spec(profile, rng):
    if profile in _FIXED_PROFILE_SPECS:
        return _FIXED_PROFILE_SPECS[profile]
    if profile == GENERAL_D2_TALL:
        return (2, rng.choice((8, 10)), 6, 2, 0, 2, 2, 2, 2)
    if profile == GENERAL_D2_WIDE:
        return (2, 6, rng.choice((8, 10)), 2, 2, 0, 0, 1, 2)
    if profile == GENERAL_D3_RECT:
        return (3, rng.choice((10, 11)), rng.choice((12, 13)), 0, 2, 1, 2, 3, 1)
    if profile == GENERAL_D3_SPREAD:
        return (3, 9, 9, 2, 0, 2, 1, 1, 2)
    if profile == GENERAL_D4_DEEP:
        return (3 + 1, rng.choice((13, 15)), rng.choice((13, 15)), 0, 1, 1, 0, 0, 2)
    raise ValueError(f"unknown scene profile: {profile!r}")


def _draw_palette(n_depths, frame_color, relation, rng):
    legal_other = [color for color in range(1, 10) if color != frame_color]
    if relation == "contains_frame":
        palette = rng.sample(legal_other, n_depths - 1)
        palette.insert(rng.randrange(n_depths), frame_color)
        return tuple(palette)
    if relation == "excludes_frame":
        return tuple(rng.sample(legal_other, n_depths))
    raise ValueError(f"unknown palette relation: {relation!r}")


def _border_cells(r0, c0, r1, c1):
    cells = {(r0, col) for col in range(c0, c1 + 1)}
    cells.update((r1, col) for col in range(c0, c1 + 1))
    cells.update((row, c0) for row in range(r0, r1 + 1))
    cells.update((row, c1) for row in range(r0, r1 + 1))
    return cells


def _analysis(grid):
    result = {
        "errors": [],
        "scene_profile": None,
        "frame_color": None,
        "palette_relation": None,
        "palette_tail": None,
        "n_depths": None,
        "frame_bbox": None,
        "palette": (),
        "palette_positions": (),
        "signature": None,
    }
    errors = result["errors"]
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a nonempty list of rows")
        return result
    if not all(isinstance(row, list) and row for row in grid):
        errors.append("grid rows must be nonempty lists")
        return result
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    height = len(grid)
    if not (3 <= height <= 30 and 3 <= width <= 30):
        errors.append("grid dimensions must each be in 3..30")

    flat = [value for row in grid for value in row]
    if any(isinstance(value, bool) or not isinstance(value, int) for value in flat):
        errors.append("grid cells must be integer ARC colors")
        return result
    bad = sorted({value for value in flat if not 0 <= value <= 9})
    if bad:
        errors.append(f"cell colors outside 0..9: {bad}")
        return result
    if 0 not in flat:
        errors.append("background color 0 must be present")

    palette_positions = tuple(
        col for col, value in enumerate(grid[-1]) if value != 0
    )
    palette = tuple(grid[-1][col] for col in palette_positions)
    result["palette_positions"] = palette_positions
    result["palette"] = palette
    palette_count = len(palette)
    if not (2 <= palette_count <= 5):
        errors.append("bottom-row palette must contain two to five colors")
    if len(set(palette)) != len(palette):
        errors.append("bottom-row palette colors must be distinct")
    if any(color == 0 for color in palette):
        errors.append("palette colors must be non-zero")

    if palette_count >= 2:
        strides = {
            right - left
            for left, right in zip(palette_positions, palette_positions[1:])
        }
        if len(strides) != 1 or next(iter(strides), 0) not in (1, 2):
            errors.append("palette positions must have constant stride one or two")
        if palette_positions and not (0 <= palette_positions[0] <= 3):
            errors.append("palette must start in columns 0..3")

    frame_cells = {
        (row, col)
        for row in range(height - 1)
        for col in range(width)
        if grid[row][col] != 0
    }
    if not frame_cells:
        errors.append("no non-zero frame cells above the palette row")
        return result
    frame_colors = {grid[row][col] for row, col in frame_cells}
    if len(frame_colors) != 1:
        errors.append("all frame cells above the palette must share one color")
        return result
    frame_color = next(iter(frame_colors))
    result["frame_color"] = frame_color

    rows = [row for row, _ in frame_cells]
    cols = [col for _, col in frame_cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    result["frame_bbox"] = (r0, c0, r1, c1)
    matching_depths = []
    for candidate_depths in range(2, 5):
        expected = set()
        possible = True
        for depth in range(candidate_depths):
            rr0, cc0 = r0 + 2 * depth, c0 + 2 * depth
            rr1, cc1 = r1 - 2 * depth, c1 - 2 * depth
            if rr0 > rr1 or cc0 > cc1:
                possible = False
                break
            expected.update(_border_cells(rr0, cc0, rr1, cc1))
        if possible and frame_cells == expected:
            matching_depths.append(candidate_depths)
    if len(matching_depths) != 1:
        errors.append(
            "frame cells must identify exactly one two-to-four-depth family "
            f"of complete outlines; matches={matching_depths}"
        )
        n_depths = matching_depths[0] if matching_depths else 0
    else:
        n_depths = matching_depths[0]
    result["n_depths"] = n_depths

    if n_depths and palette_count not in (n_depths, n_depths + 1):
        errors.append(
            "palette must have one color per frame plus at most one tail distractor"
        )
    palette_tail = "one_extra" if n_depths and palette_count == n_depths + 1 else "exact"
    result["palette_tail"] = palette_tail

    relation = "contains_frame" if frame_color in palette else "excludes_frame"
    result["palette_relation"] = relation

    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    gap = (height - 1) - r1 - 1
    if gap < 0:
        errors.append("frame region overlaps the palette row")
    right = width - 1 - c1
    if n_depths >= 2 and palette_count >= 2 and palette_positions:
        stride = palette_positions[1] - palette_positions[0]
        signature = (
            n_depths,
            frame_h,
            frame_w,
            r0,
            c0,
            right,
            gap,
            palette_positions[0],
            stride,
        )
        result["signature"] = signature
        profile = _classify_profile(signature)
        result["scene_profile"] = profile
        if profile is None:
            errors.append(f"layout signature is outside the teaching profiles: {signature}")
    return result


def _classify_profile(signature):
    for profile, fixed in _FIXED_PROFILE_SPECS.items():
        if signature == fixed:
            return profile
    n, frame_h, frame_w, top, left, right, gap, start, stride = signature
    if (
        n == 2 and frame_h in (8, 10) and frame_w == 6
        and (top, left, right, gap, start, stride) == (2, 0, 2, 2, 2, 2)
    ):
        return GENERAL_D2_TALL
    if (
        n == 2 and frame_h == 6 and frame_w in (8, 10)
        and (top, left, right, gap, start, stride) == (2, 2, 0, 0, 1, 2)
    ):
        return GENERAL_D2_WIDE
    if (
        n == 3 and frame_h in (10, 11) and frame_w in (12, 13)
        and (top, left, right, gap, start, stride) == (0, 2, 1, 2, 3, 1)
    ):
        return GENERAL_D3_RECT
    if (
        n == 3 and frame_h == frame_w == 9
        and (top, left, right, gap, start, stride) == (2, 0, 2, 1, 1, 2)
    ):
        return GENERAL_D3_SPREAD
    if (
        n == 4 and frame_h in (13, 15) and frame_w in (13, 15)
        and (top, left, right, gap, start, stride) == (0, 1, 1, 0, 0, 2)
    ):
        return GENERAL_D4_DEEP
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding lesson inputs."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    """Recover every declared exact axis from a returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "scene_profile": analysis["scene_profile"],
        "frame_color": analysis["frame_color"],
        "palette_relation": analysis["palette_relation"],
        "palette_tail": analysis["palette_tail"],
    }
