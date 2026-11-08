"""Generator for fd02da9e — move colored corner markers inward.

Every input is an orange (7) canvas with one or more colored markers at the
four corners and nowhere else. Top-corner markers become inward 2x2 blocks;
bottom-corner markers become inward three-cell bent diagonals. The source
markers are erased by the selected Racket oracle.

Default draws use a three-phase teaching schedule. Consecutive draws cycle
through top-only, bottom-only, and mixed-corner scenes, so every three-demo
rotation exposes both side-dependent branches. A substantial linked-profile
prior still covers all five official 8x8 signatures. The executable Python
mirror and rivals below are diagnostics only; generated labels remain bound to
the selected canonical Racket authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22e428cda452"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "2e6c42d70b0f"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "An orange canvas contains colored markers only at a nonempty subset of "
    "its four corners. Top markers project to inward 2x2 blocks; bottom "
    "markers project to inward three-cell bent diagonals, and all markers "
    "are erased. Three-phase lessons teach both side-dependent branches."
)

INVARIANTS = [
    "grid height and width are each 8..18",
    "background is exactly color 7",
    "every non-background cell is at one of the four corners",
    "at least one and at most four corner markers are present",
    "marker colors are exact integers 0..9 other than 7",
    "three consecutive default draws cover top-only, bottom-only, and mixed scenes",
]

_H_LO, _H_HI = 8, 18
_W_LO, _W_HI = 8, 18
_CANONICAL_PRIOR_PERCENT = 36
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")

# Bit order: top-left, top-right, bottom-left, bottom-right.
_CORNERS = (
    (1, lambda h, w: (0, 0)),
    (2, lambda h, w: (0, w - 1)),
    (4, lambda h, w: (h - 1, 0)),
    (8, lambda h, w: (h - 1, w - 1)),
)
_TOP_BITS = 1 | 2
_BOTTOM_BITS = 4 | 8
_TOP_ONLY_MASKS = (1, 2, 3)
_BOTTOM_ONLY_MASKS = (4, 8, 12)
_MIXED_MASKS = tuple(
    mask
    for mask in range(1, 16)
    if mask & _TOP_BITS and mask & _BOTTOM_BITS
)
SCHEDULE_PROFILES = ("top_only", "bottom_only", "mixed")
_PROFILE_MASKS = {
    "top_only": _TOP_ONLY_MASKS,
    "bottom_only": _BOTTOM_ONLY_MASKS,
    "mixed": _MIXED_MASKS,
}
_OFFICIAL_MASKS_BY_PROFILE = {
    "top_only": (1, 2),
    "bottom_only": (4, 8),
    "mixed": (15,),
}
_OFFICIAL_MASKS = (1, 2, 4, 8, 15)
_OFFICIAL_SIGNATURES = frozenset(
    (8, 8, mask, 1 if mask != 15 else 4) for mask in _OFFICIAL_MASKS
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "36% whole official profile at 8; otherwise band rng",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "36% whole official profile at 8; otherwise band rng",
        "valid": "8..18",
    },
    "corner_mask": {
        "type": "int",
        "default": "top-only / bottom-only / mixed three-phase schedule",
        "valid": "1..15",
    },
    "palette_size": {
        "type": "int",
        "default": "1..number of selected corners; official profiles use 1 or 4",
        "valid": "1..4",
    },
}
_AXIS_BOUNDS = {
    "grid_h": (_H_LO, _H_HI),
    "grid_w": (_W_LO, _W_HI),
    "corner_mask": (1, 15),
    "palette_size": (1, 4),
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer (bool is not accepted)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside {lo}..{hi}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the semantic phase; grid identity remains independently random."""
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _marker_cells(grid) -> list[tuple[int, int, int, int]]:
    h, w = len(grid), len(grid[0])
    cells = []
    for bit, position in _CORNERS:
        row, col = position(h, w)
        value = grid[row][col]
        if value != 7:
            cells.append((bit, row, col, value))
    return cells


def _mask_count(mask: int) -> int:
    return mask.bit_count()


def _record_exact_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    """Record every exact axis under its declared keyed label on every path."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _general_defaults(
    ctx,
    difficulty,
    requested_palette_size: int | None,
    profile: str,
):
    rng = ctx.draw_rng("general_profile")
    if difficulty == "easy":
        h = rng.randint(8, 11)
        w = rng.randint(8, 11)
        band_masks = [mask for mask in range(1, 16) if _mask_count(mask) <= 2]
    elif difficulty == "hard":
        h = rng.randint(13, 18)
        w = rng.randint(13, 18)
        band_masks = [mask for mask in range(1, 16) if _mask_count(mask) >= 2]
    else:
        h = rng.randint(9, 15)
        w = rng.randint(9, 15)
        band_masks = list(range(1, 16))

    masks = [mask for mask in band_masks if mask in _PROFILE_MASKS[profile]]
    if requested_palette_size is not None:
        masks = [
            mask for mask in masks if _mask_count(mask) >= requested_palette_size
        ]
    if not masks:
        # Exact palette overrides are global controls. Values 3 or 4 cannot fit
        # a top-only or bottom-only phase, so that explicit request takes
        # precedence over the default teaching schedule.
        masks = [
            mask
            for mask in band_masks
            if requested_palette_size is None
            or _mask_count(mask) >= requested_palette_size
        ]
    if not masks:
        masks = [15]

    mask = rng.choice(masks)
    count = _mask_count(mask)
    palette_size = rng.randint(1, count)
    return h, w, mask, palette_size


def observe_overrides(grid) -> dict[str, int]:
    """Recover exact semantic axes solely from the returned grid."""
    h, w = len(grid), len(grid[0])
    mask = 0
    colors = []
    for bit, position in _CORNERS:
        row, col = position(h, w)
        value = grid[row][col]
        if value != 7:
            mask |= bit
            colors.append(value)
    return {
        "corner_mask": mask,
        "palette_size": len(set(colors)),
    }


def feature_signature(grid):
    """Return the complete linked task profile used by semantic audits."""
    if self_check(grid):
        return None
    h, w = len(grid), len(grid[0])
    observed = observe_overrides(grid)
    return h, w, observed["corner_mask"], observed["palette_size"]


def canonical_profile_signature(grid):
    """Return an official linked profile signature, else ``None``."""
    signature = feature_signature(grid)
    return signature if signature in _OFFICIAL_SIGNATURES else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject grids outside the corner-marker task grammar without mutation."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errors = []
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errors.append(
            f"dims {h}x{w} outside {_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}"
        )

    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    corner_positions = {position(h, w) for _, position in _CORNERS}
    non_background = [
        (row, col, grid[row][col])
        for row in range(h)
        for col in range(w)
        if grid[row][col] != 7
    ]
    if not non_background:
        errors.append("no colored corner marker")
        return errors

    off_corner = [
        (row, col)
        for row, col, _ in non_background
        if (row, col) not in corner_positions
    ]
    if off_corner:
        errors.append(
            "non-background cells outside corners: " + repr(off_corner[:4])
        )
    if len(non_background) > 4:
        errors.append(f"too many non-background cells: {len(non_background)}")
    return errors


def strict_canonical_like(grid):
    """Generated inputs stay on the exact task grammar, with broader dimensions."""
    return self_check(grid)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    _validate_call(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    requested_palette_size = overrides.get("palette_size")
    has_exact_override = any(overrides.get(axis) is not None for axis in AXES)
    profile = schedule_profile(seed, sample_index, difficulty)
    use_official_profile = (
        not has_exact_override
        and ctx.draw_int("_official_roll", 0, 99) < _CANONICAL_PRIOR_PERCENT
    )

    if use_official_profile:
        mask = ctx.draw_choice(
            "_official_mask", _OFFICIAL_MASKS_BY_PROFILE[profile]
        )
        default_h = default_w = 8
        default_palette_size = 1 if mask != 15 else 4
    else:
        default_h, default_w, mask, default_palette_size = _general_defaults(
            ctx, difficulty, requested_palette_size, profile
        )

    h = _record_exact_int(ctx, "grid_h", default_h, _H_LO, _H_HI)
    w = _record_exact_int(ctx, "grid_w", default_w, _W_LO, _W_HI)
    corner_mask = _record_exact_int(ctx, "corner_mask", mask, 1, 15)
    marker_count = _mask_count(corner_mask)

    if requested_palette_size is None:
        default_palette_size = min(default_palette_size, marker_count)
    palette_size = _record_exact_int(
        ctx, "palette_size", default_palette_size, 1, 4
    )
    if palette_size > marker_count:
        raise ValueError(
            f"palette_size={palette_size} exceeds selected corner count "
            f"{marker_count} for corner_mask={corner_mask}"
        )

    colors = list(
        ctx.draw_distinct_colors("_marker_palette", n=palette_size, exclude={7})
    )
    active = [
        (bit, position(h, w))
        for bit, position in _CORNERS
        if corner_mask & bit
    ]
    assignment_rng = ctx.draw_rng("color_assignment")
    assignment_rng.shuffle(active)

    assigned = colors[:]
    while len(assigned) < len(active):
        assigned.append(assignment_rng.choice(colors))
    assignment_rng.shuffle(assigned)

    grid = full_grid(h, w, 7)
    for (_, (row, col)), color in zip(active, assigned):
        grid[row][col] = color
    return grid


# ---------------------------------------------------------------------------
# Selected-rule mirror and concrete plausible rivals (diagnostics only)
# ---------------------------------------------------------------------------

_SQUARE_OFFSETS = ((1, 1), (1, 2), (2, 1), (2, 2))
_BENT_OFFSETS = ((3, 2), (2, 2), (1, 3))


def _project(grid, *, top_shape: str, bottom_shape: str):
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    h, w = len(grid), len(grid[0])
    cells = _marker_cells(grid)
    output = [list(row) for row in grid]
    for _, row, col, _ in cells:
        output[row][col] = 7
    for _, row, col, color in cells:
        top = row == 0
        left = col == 0
        dr = 1 if top else -1
        dc = 1 if left else -1
        shape = top_shape if top else bottom_shape
        offsets = _SQUARE_OFFSETS if shape == "square" else _BENT_OFFSETS
        for row_offset, col_offset in offsets:
            output[row + dr * row_offset][col + dc * col_offset] = color
    return output


def rule_mirror(grid):
    """Pure-Python mirror of the selected canonical Racket authority."""
    return _project(grid, top_shape="square", bottom_shape="bent")


def _rival_all_corners_square(grid):
    """Wrong rule: use the top-corner 2x2 glyph for bottom corners too."""
    return _project(grid, top_shape="square", bottom_shape="square")


def _rival_all_corners_bent(grid):
    """Wrong rule: use the bottom-corner bent glyph for top corners too."""
    return _project(grid, top_shape="bent", bottom_shape="bent")


def _has_top_corner(grid) -> bool:
    return not self_check(grid) and bool(observe_overrides(grid)["corner_mask"] & _TOP_BITS)


def _has_bottom_corner(grid) -> bool:
    return not self_check(grid) and bool(observe_overrides(grid)["corner_mask"] & _BOTTOM_BITS)


SEMANTIC_WITNESSES = {
    "top_corner_branch": _has_top_corner,
    "bottom_corner_branch": _has_bottom_corner,
}
SEMANTIC_RIVALS = {
    "all_corners_square": _rival_all_corners_square,
    "all_corners_bent": _rival_all_corners_bent,
}
WITNESS_RIVALS = {
    "top_corner_branch": ["all_corners_bent"],
    "bottom_corner_branch": ["all_corners_square"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Both rivals are already refuted across the complete canonical labeled set.
CANONICAL_SHORTCUTS = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named side-agnostic rule survives all demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    normalized_demos = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with corner projection rule")
        normalized_demos.append((demo["input"], expected))

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with corner projection rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(grid) == expected for grid, expected in normalized_demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
