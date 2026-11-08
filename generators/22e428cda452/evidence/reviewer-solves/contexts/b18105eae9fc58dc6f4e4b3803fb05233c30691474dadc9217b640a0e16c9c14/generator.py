"""Generator for fd02da9e — move colored corner markers inward.

Every input is an orange (7) canvas with one or more colored markers at the
four corners and nowhere else.  Top-corner markers become inward 2x2 blocks;
bottom-corner markers become inward three-cell bent diagonals.  The source
markers are erased by the oracle.

The five official inputs form linked profiles: four 8x8 singleton-corner
examples and one 8x8 all-corners example with four distinct colors.  Default
draws retain a substantial whole-profile prior over those five signatures and
otherwise broaden the family across canvas size, corner subsets, and color
sharing without introducing unsupported edge/interior markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22e428cda452"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2e6c42d70b0f"

SUMMARY = (
    "An orange canvas contains colored markers only at a nonempty subset of "
    "its four corners. Top markers project to inward 2x2 blocks; bottom "
    "markers project to inward three-cell bent diagonals, and all markers "
    "are erased."
)

INVARIANTS = [
    "grid height and width are each 8..18",
    "background is exactly color 7",
    "every non-background cell is at one of the four corners",
    "at least one and at most four corner markers are present",
    "marker colors are integers 0..9 other than 7",
]

_H_LO, _H_HI = 8, 18
_W_LO, _W_HI = 8, 18
_CANONICAL_PRIOR_PERCENT = 36

# Bit order: top-left, top-right, bottom-left, bottom-right.
_CORNERS = (
    (1, lambda h, w: (0, 0)),
    (2, lambda h, w: (0, w - 1)),
    (4, lambda h, w: (h - 1, 0)),
    (8, lambda h, w: (h - 1, w - 1)),
)
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
        "default": "36% one of official masks 1,2,4,8,15; otherwise band rng",
        "valid": "1..15",
    },
    "palette_size": {
        "type": "int",
        "default": "1..number of selected corners; official profiles use 1 or 4",
        "valid": "1..4",
    },
}


def _marker_cells(grid) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    cells = []
    for bit, position in _CORNERS:
        row, col = position(h, w)
        value = grid[row][col]
        if value != 7:
            cells.append((bit, row, col))
    return cells


def _mask_count(mask: int) -> int:
    return int(mask).bit_count()


def _record_exact_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    """Record every exact axis under its declared keyed label on every path."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _general_defaults(ctx, difficulty, requested_palette_size: int | None):
    rng = ctx.draw_rng("general_profile")
    if difficulty == "easy":
        h = rng.randint(8, 11)
        w = rng.randint(8, 11)
        masks = [mask for mask in range(1, 16) if _mask_count(mask) <= 2]
    elif difficulty == "hard":
        h = rng.randint(13, 18)
        w = rng.randint(13, 18)
        masks = [mask for mask in range(1, 16) if _mask_count(mask) >= 2]
    else:
        h = rng.randint(9, 15)
        w = rng.randint(9, 15)
        masks = list(range(1, 16))

    if requested_palette_size is not None:
        masks = [
            mask for mask in masks if _mask_count(mask) >= requested_palette_size
        ]
        if not masks:
            # Global override semantics are band-independent.  A hard request
            # such as palette_size=4 must remain feasible even in easy mode.
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
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    corner_positions = {
        position(h, w) for _, position in _CORNERS
    }
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
        (row, col) for row, col, _ in non_background
        if (row, col) not in corner_positions
    ]
    if off_corner:
        errors.append(
            "non-background cells outside corners: "
            + repr(off_corner[:4])
        )
    if len(non_background) > 4:
        errors.append(f"too many non-background cells: {len(non_background)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    requested_palette_size = None
    if overrides.get("palette_size") is not None:
        requested_palette_size = int(overrides["palette_size"])
        if not 1 <= requested_palette_size <= 4:
            raise ValueError("palette_size override outside 1..4")

    has_exact_override = any(
        overrides.get(axis) is not None for axis in AXES
    )
    use_official_profile = (
        not has_exact_override
        and ctx.draw_int("_official_roll", 0, 99) < _CANONICAL_PRIOR_PERCENT
    )

    if use_official_profile:
        mask = ctx.draw_choice("_official_mask", _OFFICIAL_MASKS)
        default_h = default_w = 8
        default_palette_size = 1 if mask != 15 else 4
    else:
        default_h, default_w, mask, default_palette_size = _general_defaults(
            ctx, difficulty, requested_palette_size
        )

    h = _record_exact_int(ctx, "grid_h", default_h, _H_LO, _H_HI)
    w = _record_exact_int(ctx, "grid_w", default_w, _W_LO, _W_HI)
    corner_mask = _record_exact_int(ctx, "corner_mask", mask, 1, 15)
    marker_count = _mask_count(corner_mask)

    if overrides.get("palette_size") is None:
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
