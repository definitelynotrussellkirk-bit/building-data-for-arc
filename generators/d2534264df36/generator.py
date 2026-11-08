"""Generate nested corner-chain lessons for four-sided ring completion.

Each source corner names the color of all four corners on its Chebyshev
ring.  An optional same-colored pair immediately beside that corner names
the color of every non-corner lattice position on the same four sides.
"""

from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d2534264df36"
VERSION = "3.0.0"
TASK_ID = "d2534264df36"
RULE_HASH = "205ec75568f5"
SUMMARY = (
    "Complete nested square rings from corner colors and optional paired "
    "side-color witnesses."
)

INVARIANTS = [
    "the canvas is an odd square with a blank outer border",
    "source corners form one consistently oriented odd-radius diagonal chain",
    "a side role is represented by both inward neighbors of its ring corner",
    "corner and side roles use distinct nonzero colors",
    "corner roles copy to four corners and side roles fill the four sides",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
EXTRAPOLATION_PROFILES = (
    "dense_chain",
    "alternating_chain",
    "sparse_chain",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted curriculum",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# (number of nested odd-radius corners, side-role mask).
_PUBLIC_SPECS = {
    "public_train_1": (2, (False, True)),
    "public_train_2": (2, (True, False)),
    "public_train_3": (3, (True, False, False)),
    "public_test_1": (3, (True, False, True)),
}

# Four public entries and twelve extrapolation entries yield a 25% public
# anchor prior without making literal examples possible.
_DEFAULT_PROFILE_POOL = (
    *PUBLIC_PROFILES,
    *(("dense_chain",) * 4),
    *(("alternating_chain",) * 4),
    *(("sparse_chain",) * 4),
)

_ORIENTATIONS = (
    ("top", "left"),
    ("top", "right"),
    ("bottom", "right"),
    ("bottom", "left"),
)

# Compact role configurations of the four public literals.  A generated
# public-profile lesson may share their morphology, but never this complete
# orientation-and-color assignment.
_PUBLIC_LITERAL_CONFIGS = {
    "public_train_1": (
        ("top", "right"),
        (3, 4),
        (None, 1),
    ),
    "public_train_2": (
        ("top", "left"),
        (8, 2),
        (1, None),
    ),
    "public_train_3": (
        ("top", "left"),
        (4, 1, 8),
        (3, None, None),
    ),
    "public_test_1": (
        ("bottom", "left"),
        (1, 2, 4),
        (3, None, 8),
    ),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic nested-ring source grid."""
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
    profile = ctx.draw_choice(
        "scene_profile",
        _DEFAULT_PROFILE_POOL,
    )
    layout_rng = ctx.draw_rng("layout")

    if profile in _PUBLIC_SPECS:
        size = 19
        ring_count, arm_mask = _PUBLIC_SPECS[profile]
    else:
        size = layout_rng.choice(_control_sizes(difficulty))
        ring_count = 4
        if profile == "dense_chain":
            arm_mask = (True, True, True, True)
        elif profile == "alternating_chain":
            arm_mask = layout_rng.choice(
                (
                    (True, False, True, False),
                    (False, True, False, True),
                )
            )
        else:
            armed_ring = layout_rng.randrange(ring_count)
            arm_mask = tuple(
                index == armed_ring for index in range(ring_count)
            )

    orientation = layout_rng.choice(_ORIENTATIONS)
    role_count = ring_count + sum(arm_mask)
    role_colors = ctx.draw_rng("role_colors").sample(
        range(1, 10),
        role_count,
    )
    corner_colors = list(role_colors[:ring_count])
    arm_palette = iter(role_colors[ring_count:])
    arm_colors = [
        next(arm_palette) if has_arms else None
        for has_arms in arm_mask
    ]

    literal = _PUBLIC_LITERAL_CONFIGS.get(profile)
    if literal == (
        orientation,
        tuple(corner_colors),
        tuple(arm_colors),
    ):
        # A cyclic role recoloring preserves the lesson and deterministically
        # avoids replaying a complete public input.
        corner_colors = corner_colors[1:] + corner_colors[:1]

    return _build_source(
        size,
        orientation,
        corner_colors,
        arm_colors,
    )


def _control_sizes(difficulty):
    if difficulty == "easy":
        return (19,)
    if difficulty == "medium":
        return (19, 21)
    if difficulty == "hard":
        return (21, 23)
    return (19, 21, 23)


def _build_source(size, orientation, corner_colors, arm_colors):
    grid = full_grid(size, size, 0)
    vertical, horizontal = orientation
    for index, corner_color in enumerate(corner_colors):
        ring = 1 + 2 * index
        row = ring if vertical == "top" else size - 1 - ring
        col = ring if horizontal == "left" else size - 1 - ring
        grid[row][col] = corner_color

        arm_color = arm_colors[index]
        if arm_color is None:
            continue
        toward_row = row + (2 if vertical == "top" else -2)
        toward_col = col + (2 if horizontal == "left" else -2)
        grid[toward_row][col] = arm_color
        grid[row][toward_col] = arm_color
    return grid


def solve_python(grid):
    """Input-pure Python mirror of the canonical row-major Racket rule."""
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    height = len(grid)
    out = [row[:] for row in grid]
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] > 0
    ]
    for row, col in cells:
        color = grid[row][col]
        ring = min(
            row,
            col,
            height - 1 - row,
            width - 1 - col,
        )
        far = height - 1 - ring
        is_corner = (
            row in (ring, far)
            and col in (ring, far)
        )
        if is_corner:
            targets = (
                (ring, ring),
                (ring, far),
                (far, ring),
                (far, far),
            )
        else:
            offsets = range(ring + 2, far - 1, 2)
            targets = (
                [(ring, offset) for offset in offsets]
                + [(far, offset) for offset in offsets]
                + [(offset, ring) for offset in offsets]
                + [(offset, far) for offset in offsets]
            )
        for target_row, target_col in targets:
            out[target_row][target_col] = color
    return out


def _basic_grid_reasons(grid):
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return ["empty_or_non_grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["invalid_arc_value"]
    return []


def _analyze(grid):
    reasons = _basic_grid_reasons(grid)
    if reasons:
        return {
            "strict": False,
            "reasons": reasons,
            "scene_profile": None,
        }

    height = len(grid)
    width = len(grid[0])
    nonzero = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if height != width or height % 2 != 1:
        reasons.append("not_odd_square")
    if not 19 <= height <= 23:
        reasons.append("dimension_range")
    if not nonzero:
        reasons.append("no_sources")
    if any(row % 2 == 0 or col % 2 == 0 for row, col, _ in nonzero):
        reasons.append("off_odd_lattice")
    if any(
        grid[row][col] != 0
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    ):
        reasons.append("nonblank_border")

    center = height // 2
    by_ring = {}
    for row, col, color in nonzero:
        ring = min(
            row,
            col,
            height - 1 - row,
            width - 1 - col,
        )
        by_ring.setdefault(ring, []).append((row, col, color))

    rings = sorted(by_ring)
    if (
        rings != list(range(1, 2 * len(rings), 2))
        or not 2 <= len(rings) <= 4
    ):
        reasons.append("ring_chain")

    orientation = None
    corner_colors = []
    side_colors = []
    arm_mask = []
    accounted = set()
    for ring in rings:
        far = height - 1 - ring
        corners = [
            (row, col, color)
            for row, col, color in by_ring[ring]
            if row in (ring, far) and col in (ring, far)
        ]
        if len(corners) != 1:
            reasons.append("corner_cardinality")
            arm_mask.append(None)
            continue

        corner_row, corner_col, corner_color = corners[0]
        accounted.add((corner_row, corner_col))
        this_orientation = (
            "top" if corner_row < center else "bottom",
            "left" if corner_col < center else "right",
        )
        if orientation is None:
            orientation = this_orientation
        elif orientation != this_orientation:
            reasons.append("mixed_orientation")

        toward_row = corner_row + (
            2 if corner_row < center else -2
        )
        toward_col = corner_col + (
            2 if corner_col < center else -2
        )
        expected_arms = {
            (toward_row, corner_col),
            (corner_row, toward_col),
        }
        actual_sides = [
            (row, col, color)
            for row, col, color in by_ring[ring]
            if (row, col) != (corner_row, corner_col)
        ]
        if not actual_sides:
            arm_mask.append(False)
        elif (
            len(actual_sides) == 2
            and {(row, col) for row, col, _ in actual_sides}
            == expected_arms
            and len({color for _, _, color in actual_sides}) == 1
        ):
            arm_mask.append(True)
            side_colors.append(actual_sides[0][2])
            accounted.update((row, col) for row, col, _ in actual_sides)
        else:
            reasons.append("arm_pair")
            arm_mask.append(None)
        corner_colors.append(corner_color)

    if len(accounted) != len(nonzero):
        reasons.append("unaccounted_sources")
    if not any(value is True for value in arm_mask):
        reasons.append("no_side_role")
    role_colors = corner_colors + side_colors
    if len(role_colors) != len(set(role_colors)):
        reasons.append("role_color_alias")

    arm_tuple = tuple(arm_mask)
    public_match = next(
        (
            profile
            for profile, (ring_count, mask) in _PUBLIC_SPECS.items()
            if height == 19
            and len(rings) == ring_count
            and arm_tuple == mask
        ),
        None,
    )
    if public_match is not None:
        scene_profile = public_match
    elif len(rings) == 4 and arm_tuple == (True,) * 4:
        scene_profile = "dense_chain"
    elif (
        len(rings) == 4
        and arm_tuple
        in (
            (True, False, True, False),
            (False, True, False, True),
        )
    ):
        scene_profile = "alternating_chain"
    elif (
        len(rings) == 4
        and sum(value is True for value in arm_mask) == 1
    ):
        scene_profile = "sparse_chain"
    else:
        scene_profile = None
        reasons.append("unsupported_profile")

    if solve_python(grid) == grid:
        reasons.append("identity")
    return {
        "strict": not reasons,
        "reasons": sorted(set(reasons)),
        "height": height,
        "width": width,
        "nonzero_count": len(nonzero),
        "rings": rings,
        "ring_count": len(rings),
        "arm_mask": arm_tuple,
        "orientation": orientation,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete returned-grid lesson, not constructor intent."""
    return _analyze(grid)["reasons"]


def observe_overrides(grid):
    analysis = _analyze(grid)
    if not analysis["strict"]:
        return {"scene_profile": None}
    return {"scene_profile": analysis["scene_profile"]}
