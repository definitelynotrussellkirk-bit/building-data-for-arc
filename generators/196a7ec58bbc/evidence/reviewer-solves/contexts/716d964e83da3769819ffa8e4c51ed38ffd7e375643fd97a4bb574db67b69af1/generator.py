"""Generator for ARC task ``196a7ec58bbc`` (source puzzle ``46442a0e``).

The Racket oracle makes a 2×2 kaleidoscope of a square input: original in the
top-left, 90° clockwise in the top-right, 90° counterclockwise in the
bottom-left, and 180° in the bottom-right.

Ordinary generated lessons use all requested colors, have four distinct
rotations, and distinguish rotational tiling from a plausible reflection-based
tiling.  The canonical 2×2 diagonal checker is retained as an explicit
answer-equivalence exception: its original and 180° tiles coincide, as do its
clockwise and counterclockwise tiles, but all matching interpretations still
produce the official answer.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.textures import fill_texture

GENERATOR_ID = "196a7ec58bbc"
VERSION = "2.1.0"
TASK_ID = "196a7ec58bbc"
RULE_HASH = "24bc23963715"

SUMMARY = (
    "A 2×2 or 3×3 colored square is tiled into a 2N×2N output with the "
    "original, clockwise, counterclockwise, and 180° rotations in TL/TR/BL/BR."
)

INVARIANTS = [
    "input is a square 2×2 or 3×3 ARC grid",
    "ordinary generated inputs use exactly the requested 2..4 colors",
    "ordinary generated inputs have four distinct rotations so all quadrant roles fire",
    "ordinary generated inputs distinguish rotational tiling from reflection tiling",
    "generated two-color 2×2 inputs use 3:1 counts; canonical diagonal 2:2 inputs remain accepted",
    "the canonical two-color diagonal 2×2 family is accepted as an answer-equivalent exception",
    "the Racket oracle is the only output authority",
]

_TEXTURE_PRIORS = (
    "noise",
    "sparse",
    "blob",
    "stripes",
    "gradient",
    "checkerboard",
    "frame",
    "ring",
    "plus",
)
AXES = {
    "grid_n": {
        "type": "int",
        "default": "2 easy, rng 2..3 medium, 3 hard",
        "valid": "2..3",
        "doc": "Input side length. An explicit override is honored in every band.",
    },
    "palette_size": {
        "type": "int",
        "default": "2-color profile anchors plus 3..4 for 2×2; 2..4 for 3×3",
        "valid": "2..4",
        "doc": "Exact number of distinct colors visible in the returned input.",
    },
}


def _strict_int(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    return value


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotations(grid):
    r0 = [row[:] for row in grid]
    r1 = _rotate_cw(r0)
    r2 = _rotate_cw(r1)
    r3 = _rotate_cw(r2)
    return r0, r1, r2, r3


def _rotation_orbit_size(grid) -> int:
    return len({tuple(tuple(row) for row in rotated) for rotated in _rotations(grid)})


def _tile_quadrants(top_left, top_right, bottom_left, bottom_right):
    top = [left + right for left, right in zip(top_left, top_right)]
    bottom = [left + right for left, right in zip(bottom_left, bottom_right)]
    return top + bottom


def rule_mirror(grid):
    """Independent Python mirror of the canonical Racket rotation rule."""
    original, clockwise, half_turn, counterclockwise = _rotations(grid)
    return _tile_quadrants(original, clockwise, counterclockwise, half_turn)


def _mirror_quadrants(grid):
    """Plausible wrong rule: reflect into adjacent quadrants instead of rotate."""
    original = [row[:] for row in grid]
    mirror_left_right = [row[::-1] for row in grid]
    mirror_top_bottom = [row[:] for row in grid[::-1]]
    half_turn = _rotations(grid)[2]
    return _tile_quadrants(
        original, mirror_left_right, mirror_top_bottom, half_turn
    )


def _rotation_not_reflection(grid) -> bool:
    return rule_mirror(grid) != _mirror_quadrants(grid)


def _target_counts(total: int, palette, rng) -> dict[int, int]:
    """Exact counts; every color appears and generated 2×2/2-color cases are 3:1."""
    if total == 4 and len(palette) == 2:
        order = list(palette)
        rng.shuffle(order)
        return {order[0]: 3, order[1]: 1}
    base, remainder = divmod(total, len(palette))
    counts = {color: base for color in palette}
    order = list(palette)
    rng.shuffle(order)
    for color in order[:remainder]:
        counts[color] += 1
    return counts


def _balance_texture(base_grid, palette, rng, *, easy: bool):
    """Preserve as much of a texture as possible while enforcing exact counts."""
    n = len(base_grid)
    target = _target_counts(n * n, palette, rng)
    remaining = dict(target)
    positions = [(r, c) for r in range(n) for c in range(n)]
    if not easy:
        rng.shuffle(positions)

    out = [[None for _ in range(n)] for _ in range(n)]
    unfilled = []
    for r, c in positions:
        value = base_grid[r][c]
        if value in remaining and remaining[value] > 0:
            out[r][c] = value
            remaining[value] -= 1
        else:
            unfilled.append((r, c))

    fill_values = [
        color
        for color in palette
        for _ in range(remaining[color])
    ]
    rng.shuffle(fill_values)
    for (r, c), value in zip(unfilled, fill_values):
        out[r][c] = value
    return out


def _fallback_asymmetric(n: int, palette, ctx, band: str):
    """Guaranteed finite fallback if a highly symmetric texture resists repair."""
    for attempt in range(256):
        rng = ctx.draw_rng(f"fallback:{band}:{attempt}")
        counts = _target_counts(n * n, palette, rng)
        values = [color for color in palette for _ in range(counts[color])]
        rng.shuffle(values)
        grid = [values[r * n:(r + 1) * n] for r in range(n)]
        if _rotation_orbit_size(grid) == 4 and _rotation_not_reflection(grid):
            return grid
    raise RuntimeError(
        "could not construct a rotation-distinct, reflection-distinguishing tiny square"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    seed = _strict_int(seed, "seed")
    sample_index = _strict_int(sample_index, "sample_index")
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, got {sample_index}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be one of easy/medium/hard or None, got {difficulty!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    explicit_n = overrides.get("grid_n")
    explicit_palette_size = overrides.get("palette_size")
    if explicit_n is not None:
        explicit_n = _strict_int(explicit_n, "grid_n")
        if not 2 <= explicit_n <= 3:
            raise ValueError(f"grid_n {explicit_n} outside 2..3")
    if explicit_palette_size is not None:
        explicit_palette_size = _strict_int(explicit_palette_size, "palette_size")
        if not 2 <= explicit_palette_size <= 4:
            raise ValueError(f"palette_size {explicit_palette_size} outside 2..4")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"

    # Difficulty shapes defaults only. Exact overrides always use the full
    # declared range. A lone palette override leaves size under the normal band
    # schedule, so every declared cross-product remains realizable.
    if explicit_n is not None:
        n = ctx.draw_int("grid_n", 2, 3)
    elif band == "easy":
        n = ctx.draw_int("grid_n", 2, 2)
    elif band == "hard":
        n = ctx.draw_int("grid_n", 3, 3)
    else:
        n = ctx.draw_int("grid_n", 2, 3)

    if explicit_palette_size is not None:
        palette_size = ctx.draw_int("palette_size", 2, 4)
    elif sample_index % 4 == 0:
        # A deterministic profile anchor guarantees every 20-draw band window
        # includes a canonical 2-color size profile.  Layout remains randomized.
        palette_size = ctx.draw_int("palette_size", 2, 2)
    elif n == 2:
        palette_size = ctx.draw_int("palette_size", 3, 4)
    else:
        palette_size = ctx.draw_int("palette_size", 2, 4)

    texture = ctx.draw_choice("texture", list(_TEXTURE_PRIORS))
    palette = list(ctx.draw_distinct_colors("palette", n=palette_size))

    for attempt in range(64):
        rng = ctx.draw_rng(f"layout:{band}:{texture}:{attempt}")
        base = fill_texture(texture, n, n, palette, rng)
        grid = _balance_texture(base, palette, rng, easy=(band == "easy"))
        if _rotation_orbit_size(grid) == 4 and _rotation_not_reflection(grid):
            return grid
    return _fallback_asymmetric(n, palette, ctx, band)


def observe_overrides(grid) -> dict[str, int]:
    """Recover exact semantic axes from the returned grid itself."""
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
        or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)
    ):
        return {}
    return {
        "grid_n": len(grid),
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the chosen teaching envelope while accepting every canonical input."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    height = len(grid)
    if height != width:
        errors.append(f"input must be square; got {height}x{width}")
    if height not in (2, 3) or width not in (2, 3):
        errors.append(f"input must be canonical-sized 2×2 or 3×3; got {height}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
    if errors:
        return errors

    counts = Counter(value for row in grid for value in row)
    palette_size = len(counts)
    if not 2 <= palette_size <= 4:
        errors.append(f"expected 2..4 visible colors; got {palette_size}")
        return errors

    orbit_size = _rotation_orbit_size(grid)
    if height == 2 and palette_size == 2:
        diagonal_equivalence = (
            grid[0][0] == grid[1][1]
            and grid[0][1] == grid[1][0]
            and grid[0][0] != grid[0][1]
        )
        generated_profile = (
            sorted(counts.values()) == [1, 3]
            and orbit_size == 4
            and _rotation_not_reflection(grid)
        )
        if not (diagonal_equivalence or generated_profile):
            errors.append(
                "two-color 2×2 inputs must be either the canonical diagonal "
                "answer-equivalence pattern or a 3:1 reflection-distinguishing lesson"
            )
    elif orbit_size != 4:
        errors.append(
            f"teaching input must expose four distinct rotations; got orbit size {orbit_size}"
        )

    if height == 3 and min(counts.values()) < 2:
        errors.append("every visible color in a 3×3 teaching input must occur at least twice")
    return errors

# --- Semantic teaching contract ---------------------------------------------

_CANONICAL_PROFILES = {(2, 2, 2), (3, 3, 2), (3, 3, 3)}
EXAMPLES_NEEDED = 3


def strict_canonical_like(grid) -> list[str]:
    """Accept canonical size/palette profiles inside the validated envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    if profile not in _CANONICAL_PROFILES:
        return [
            "input profile must match a canonical size/palette profile; "
            f"got {profile[0]}x{profile[1]} with {profile[2]} colors"
        ]
    return []


SEMANTIC_RIVALS = {
    "mirror_quadrants": _mirror_quadrants,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "rotation_not_reflection": _rotation_not_reflection,
}
WITNESS_RIVALS = {
    "rotation_not_reflection": ["mirror_quadrants"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where the named reflection rival survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    pairs = list(demos) + [query]
    for pair in pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["lesson pair must contain input and reference output"]
        errors = self_check(pair["input"])
        if errors:
            return errors
        if rule_mirror(pair["input"]) != pair["output"]:
            return ["authoring mirror disagrees with reference output"]
    return [
        f"competitor '{name}' fits every demonstration and changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
