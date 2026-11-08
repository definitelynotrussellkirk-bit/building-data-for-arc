"""Semantic generator for ARC task 0f55521cc320 (source b8cdaf2b).

A centered outer-color segment sits one row above the bottom.  The same
columns on the bottom row contain a distinct inner color, while the remaining
bottom-row cells contain the outer color.  The oracle extends the inner color
upward along the two outward diagonals from the upper segment's endpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette


GENERATOR_ID = "0f55521cc320"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "480e6d87f0e5"
SUMMARY = (
    "Extend the bottom center color upward on the two outward diagonals "
    "starting at the endpoints of the centered segment directly above it."
)

OFFICIAL_NARROW = ((3, 1), (5, 1))
OFFICIAL_MID = ((5, 3), (7, 3), (9, 3))
SCENE_PROFILES = (
    "official_narrow",
    "official_mid",
    "generalized_narrow",
    "generalized_wide",
)
_DEFAULT_PROFILE_CHOICES = (
    "official_narrow",
    "official_narrow",
    "official_narrow",
    "official_mid",
    "official_mid",
    "official_mid",
    "generalized_narrow",
    "generalized_narrow",
    "generalized_wide",
    "generalized_wide",
)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "60% official-profile families and 40% semantic generalizations",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "observable linked square-size and centered-segment-width family",
    }
}
INVARIANTS = [
    "the input is an odd square from 3x3 through 29x29 with black background",
    "only the bottom two rows contain nonzero cells",
    "the upper nonzero cells form one centered odd-width outer-color segment",
    "the bottom row uses the inner color under exactly that segment and the outer color elsewhere",
    "outer and inner colors are distinct nonzero ARC colors",
    "the upper segment leaves at least one column on each side for visible outward diagonals",
]

_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be literal ARC integers from zero through nine"]
    return []


def _analyze(grid) -> dict:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors, "facts": None}

    height, width = len(grid), len(grid[0])
    if height != width:
        errors.append("calibrated input must be square")
    if not 3 <= height <= 29 or height % 2 == 0:
        errors.append("calibrated square size must be odd and between 3 and 29")

    if height < 2:
        return {"errors": errors, "facts": None}

    nonzero_rows = [
        row
        for row in range(height)
        if any(grid[row][col] != 0 for col in range(width))
    ]
    if nonzero_rows != [height - 2, height - 1]:
        errors.append("only the bottom two rows may contain nonzero cells")

    upper_positions = [
        col for col in range(width) if grid[height - 2][col] != 0
    ]
    if not upper_positions:
        errors.append("the upper row must contain a centered outer-color segment")
        return {"errors": errors, "facts": None}

    left, right = upper_positions[0], upper_positions[-1]
    segment_width = right - left + 1
    expected_positions = list(range(left, right + 1))
    if upper_positions != expected_positions:
        errors.append("the upper nonzero cells must form one contiguous segment")
    if segment_width % 2 == 0:
        errors.append("the upper segment width must be odd")
    if left + right != width - 1:
        errors.append("the upper segment must be horizontally centered")
    if left == 0 or right == width - 1:
        errors.append("the upper segment must leave a nonempty flank on each side")

    upper_colors = {grid[height - 2][col] for col in upper_positions}
    if len(upper_colors) != 1:
        errors.append("the upper segment must use exactly one outer color")
        outer = None
    else:
        outer = next(iter(upper_colors))
        if outer == 0:
            errors.append("the outer color must be nonzero")

    center = width // 2
    inner = grid[height - 1][center]
    if inner == 0:
        errors.append("the bottom center inner color must be nonzero")
    if outer is not None and inner == outer:
        errors.append("the inner and outer colors must be distinct")

    if outer is not None:
        for col in range(width):
            expected = inner if left <= col <= right else outer
            if grid[height - 1][col] != expected:
                errors.append(
                    "the bottom row must align the inner segment under the upper "
                    "segment and use outer color on both flanks"
                )
                break
        for col in range(width):
            expected = outer if left <= col <= right else 0
            if grid[height - 2][col] != expected:
                errors.append("the upper row contains a misplaced color")
                break

    facts = {
        "height": height,
        "width": width,
        "segment_width": segment_width,
        "left": left,
        "right": right,
        "outer_color": outer,
        "inner_color": inner,
    }
    facts["scene_profile"] = _scene_profile(facts)
    if facts["scene_profile"] is None:
        errors.append("linked geometry is outside the declared scene-profile families")
    return {"errors": errors, "facts": facts}


def _scene_profile(facts) -> str | None:
    signature = (facts["height"], facts["segment_width"])
    if signature in OFFICIAL_NARROW:
        return "official_narrow"
    if signature in OFFICIAL_MID:
        return "official_mid"
    if facts["height"] >= 11 and facts["segment_width"] in (1, 3):
        return "generalized_narrow"
    if facts["height"] >= 7 and facts["segment_width"] >= 5:
        return "generalized_wide"
    return None


def canonical_profile_signature(grid):
    """Return the exact official linked geometry, or ``None`` off-manifold."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"] is None:
        return None
    signature = (
        analysis["facts"]["height"],
        analysis["facts"]["segment_width"],
    )
    return signature if signature in set(OFFICIAL_NARROW + OFFICIAL_MID) else None


def observe_overrides(grid):
    """Recover every exact declared axis from the returned grid itself."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"] is None:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["facts"]["scene_profile"]}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete linked two-row construction observationally."""
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    """Input-pure Python mirror of the canonical Racket transformation."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"] is None:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    output = [list(row) for row in grid]
    upper_row = facts["height"] - 2
    distance = 1
    while upper_row - distance >= 0:
        left = facts["left"] - distance
        right = facts["right"] + distance
        if left >= 0:
            output[upper_row - distance][left] = facts["inner_color"]
        if right < facts["width"]:
            output[upper_row - distance][right] = facts["inner_color"]
        distance += 1
    return output


def _geometry_for(profile, difficulty, rng) -> tuple[int, int]:
    if profile == "official_narrow":
        choices = {
            "easy": ((3, 1), (3, 1), (5, 1)),
            "medium": ((3, 1), (5, 1), (5, 1)),
            "hard": ((3, 1), (5, 1), (5, 1)),
        }.get(difficulty, OFFICIAL_NARROW)
        return rng.choice(choices)

    if profile == "official_mid":
        choices = {
            "easy": ((5, 3), (5, 3), (7, 3)),
            "medium": ((5, 3), (7, 3), (9, 3)),
            "hard": ((7, 3), (9, 3), (9, 3)),
        }.get(difficulty, OFFICIAL_MID)
        return rng.choice(choices)

    if profile == "generalized_narrow":
        sizes = {
            "easy": (11, 13),
            "medium": (15, 17, 19),
            "hard": (21, 23, 25, 27, 29),
        }.get(difficulty, tuple(range(11, 30, 2)))
        return rng.choice(sizes), rng.choice((1, 3))

    if profile == "generalized_wide":
        sizes = {
            "easy": (7, 9, 11),
            "medium": (11, 13, 15, 17, 19),
            "hard": (21, 23, 25, 27, 29),
        }.get(difficulty, tuple(range(7, 30, 2)))
        size = rng.choice(sizes)
        widths = tuple(range(5, size, 2))
        return size, rng.choice(widths)

    raise ValueError(f"unsupported scene_profile: {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'default', 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override axes: {', '.join(unknown)}")

    normalized_difficulty = None if difficulty == "default" else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=normalized_difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", _DEFAULT_PROFILE_CHOICES)
    rng = ctx.draw_rng("layout")
    size, segment_width = _geometry_for(profile, normalized_difficulty, rng)
    outer, inner = random_palette(rng, 2)

    grid = full_grid(size, size, 0)
    left = (size - segment_width) // 2
    right = left + segment_width - 1
    for col in range(left, right + 1):
        grid[size - 2][col] = outer
    for col in range(size):
        grid[size - 1][col] = inner if left <= col <= right else outer
    return grid
