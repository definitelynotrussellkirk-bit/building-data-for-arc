"""Generator for ARC task af902bf9 / selected task dbecc530afd0.

Canonical rule: every four yellow(4) cells that form an axis-aligned rectangle
identify that rectangle; paint every strict rectangle interior red(2), preserving
all other cells.  Production inputs contain one or two complete, corner-disjoint
rectangles plus at most three isolated yellow distractors that complete no extra
rectangle.

The four-slot default lesson schedule alternates canonical-profile anchors with
lawful interleaved-rectangle witnesses.  Because a lesson uses three examples
and one query, every query rotation retains a witness against the strongest
canonical-fitting shortcut declared below.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dbecc530afd0"
VERSION = "3.0.0"
TASK_ID = GENERATOR_ID
RULE_HASH = "bd0dec43bf33"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "One or two corner-disjoint yellow rectangles, optionally with up to three "
    "isolated yellow distractors; fill every strict rectangle interior red. "
    "A four-slot schedule alternates canonical anchors and interleaved-row "
    "counterexamples to the adjacent-row-pair shortcut."
)

INVARIANTS = [
    "background is 0 and every non-background input cell is yellow(4)",
    "exactly one or two complete axis-aligned rectangle corner sets are present",
    "each rectangle is at least 3x3 and distinct rectangles share no corner",
    "zero to three additional yellow cells belong to no complete rectangle",
    "every four consecutive ordinary draws contain two canonical anchors and two interleaved witnesses",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
HELPFUL_TEXTURES = POSITION_BIASES
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "interleaved_rectangles",
    "canonical_anchor",
    "interleaved_rectangles",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 10 or difficulty-weighted 9..14",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 10 or difficulty-weighted 9..14",
        "valid": "8..18",
    },
    "n_rects": {
        "type": "int",
        "default": "scheduled 1..2 (interleaved slots force 2)",
        "valid": "1..2",
    },
    "n_extra_yellows": {
        "type": "int",
        "default": "0..3 (canonical slots force 0)",
        "valid": "0..3",
    },
    "position_bias": {
        "type": "str",
        "default": "keyed choice from helpful biases",
        "valid": "|".join(POSITION_BIASES),
    },
    "texture": {
        "type": "str",
        "default": "optional alias for position_bias",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# The four official forms: (10x10 canvas, exact yellow corner sets).
_CANONICAL_FORMS = (
    ((1, 1), (1, 6), (6, 1), (6, 6)),
    ((3, 3), (3, 5), (5, 3), (5, 5)),
    ((1, 1), (1, 3), (3, 1), (3, 3), (6, 4), (6, 9), (9, 4), (9, 9)),
    ((0, 5), (0, 9), (4, 5), (4, 9), (5, 0), (5, 3), (8, 0), (8, 3)),
)

_INT_BOUNDS = {
    "grid_h": (8, 18),
    "grid_w": (8, 18),
    "n_rects": (1, 2),
    "n_extra_yellows": (0, 3),
}
_STRING_VALUES = {
    "position_bias": POSITION_BIASES,
    "texture": HELPFUL_TEXTURES,
}
_DIFFICULTIES = (None, "easy", "medium", "hard")


def _rect_corners(r1: int, r2: int, c1: int, c2: int) -> set[tuple[int, int]]:
    return {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}


def _all_rects(cells) -> list[tuple[int, int, int, int]]:
    """Return every axis-aligned rectangle whose four corners are in cells."""
    rects: list[tuple[int, int, int, int]] = []
    by_row: dict[int, set[int]] = {}
    for r, c in cells:
        by_row.setdefault(r, set()).add(c)
    rows = sorted(by_row)
    for index, r1 in enumerate(rows):
        for r2 in rows[index + 1 :]:
            common = sorted(by_row[r1] & by_row[r2])
            for left_index, c1 in enumerate(common):
                for c2 in common[left_index + 1 :]:
                    rects.append((r1, r2, c1, c2))
    return rects


def _yellow_cells(grid) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    }


def _validate_request(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a non-negative integer (not bool)")
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise KeyError(f"unknown override axes: {sorted(unknown)}")
    for name, (lo, hi) in _INT_BOUNDS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    for name, values in _STRING_VALUES.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{name} must be a string")
        if value not in values:
            raise ValueError(f"{name}={value!r}; valid values are {values}")
    texture = overrides.get("texture")
    position = overrides.get("position_bias")
    if texture is not None and position is not None and texture != position:
        raise ValueError(
            f"texture={texture!r} aliases position_bias and disagrees with "
            f"position_bias={position!r}"
        )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the declared production input manifold."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 18 or not 8 <= width <= 18:
        return [f"dims {height}x{width} outside the declared 8..18 envelope"]
    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if type(value) is not int or value not in (0, 4)
        },
        key=repr,
    )
    if bad_values:
        return [f"cells must be integer colors from {{0,4}}; bad values: {bad_values}"]

    yellows = _yellow_cells(grid)
    rectangles = _all_rects(yellows)
    if not 1 <= len(rectangles) <= 2:
        errors.append(
            f"expected one or two complete rectangles (n_rects 1..2), found {len(rectangles)}"
        )
        return errors

    used: set[tuple[int, int]] = set()
    for r1, r2, c1, c2 in rectangles:
        if r2 - r1 < 2 or c2 - c1 < 2:
            errors.append(
                f"rectangle ({r1},{c1})-({r2},{c2}) must be at least 3x3"
            )
        used.update(_rect_corners(r1, r2, c1, c2))
    if len(used) != 4 * len(rectangles):
        errors.append("complete rectangles must not share yellow corners")
    extra_count = len(yellows - used)
    if not 0 <= extra_count <= 3:
        errors.append(f"n_extra_yellows={extra_count} outside [0, 3]")
    return errors


def strict_canonical_like(grid):
    """The semantic gate uses the same declared manifold as production."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Return realized structural axis values for a rectangular grid."""
    yellows = _yellow_cells(grid)
    rectangles = _all_rects(yellows)
    used: set[tuple[int, int]] = set()
    for r1, r2, c1, c2 in rectangles:
        used.update(_rect_corners(r1, r2, c1, c2))
    return {
        "n_rects": len(rectangles),
        "n_extra_yellows": len(yellows - used),
    }


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Four slots with two witnesses; every three-of-four rotation keeps one."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a non-negative integer (not bool)")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _difficulty_shape_band(difficulty) -> tuple[int, int]:
    if difficulty == "easy":
        return 9, 11
    if difficulty == "hard":
        return 11, 14
    return 10, 12


def _draw_axis_int(ctx, overrides, name, lo, hi, default_lo, default_hi) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default_lo, default_hi)


def _draw_bias(ctx, overrides) -> str:
    texture = None
    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    if overrides.get("position_bias") is not None:
        position = ctx.draw_choice("position_bias", POSITION_BIASES)
    elif texture is None:
        position = ctx.draw_choice("position_bias", POSITION_BIASES)
    else:
        position = texture
    return texture or position


def _place_rects(rng, height, width, n_rects, bias):
    """Place one/two corner-disjoint rectangles without accidental rectangles."""
    for _attempt in range(100):
        candidates = []
        for _ in range(n_rects):
            rect_height = rng.randint(3, max(3, height - 2))
            rect_width = rng.randint(3, max(3, width - 2))
            if bias == "centered":
                r1 = rng.randint(max(0, (height - rect_height) // 3), max(0, 2 * (height - rect_height) // 3))
                c1 = rng.randint(max(0, (width - rect_width) // 3), max(0, 2 * (width - rect_width) // 3))
            elif bias == "corner":
                r1 = rng.randint(0, min(1, height - rect_height))
                c1 = rng.randint(0, min(1, width - rect_width))
            elif bias == "near_edge":
                side = rng.randrange(4)
                if side == 0:
                    r1, c1 = 0, rng.randint(0, width - rect_width)
                elif side == 1:
                    r1, c1 = height - rect_height, rng.randint(0, width - rect_width)
                elif side == 2:
                    r1, c1 = rng.randint(0, height - rect_height), 0
                else:
                    r1, c1 = rng.randint(0, height - rect_height), width - rect_width
            else:
                r1 = rng.randint(0, height - rect_height)
                c1 = rng.randint(0, width - rect_width)
            candidates.append((r1, r1 + rect_height - 1, c1, c1 + rect_width - 1))
        corners: set[tuple[int, int]] = set()
        for rect in candidates:
            corners.update(_rect_corners(*rect))
        if len(corners) != 4 * n_rects:
            continue
        if sorted(_all_rects(corners)) == sorted(candidates):
            return candidates, corners
    return None, None


def _rank_quadruples(values, *, bias, extent, rng):
    options = list(combinations(range(extent), 4))
    if values == "columns":
        options = [quad for quad in options if quad[1] - quad[0] >= 2 and quad[3] - quad[2] >= 2]
    if not options:
        return None
    if bias == "corner":
        best = min(quad[0] + quad[3] for quad in options)
        pool = [quad for quad in options if quad[0] + quad[3] <= best + 2]
    elif bias == "near_edge":
        pool = [quad for quad in options if quad[0] == 0 or quad[3] == extent - 1]
        if not pool:
            pool = options
    elif bias == "centered":
        center2 = extent - 1
        scored = sorted(options, key=lambda quad: (abs(quad[0] + quad[3] - center2), quad[3] - quad[0]))
        cutoff = max(1, len(scored) // 8)
        pool = scored[:cutoff]
    else:
        pool = options
    return rng.choice(pool)


def _place_interleaved_rects(rng, height, width, bias):
    """Construct two rectangles with crossing row intervals and disjoint columns."""
    rows = _rank_quadruples("rows", bias=bias, extent=height, rng=rng)
    cols = _rank_quadruples("columns", bias=bias, extent=width, rng=rng)
    if rows is None or cols is None:
        return None, None
    r0, r1, r2, r3 = rows
    c0, c1, c2, c3 = cols
    rectangles = [(r0, r2, c0, c1), (r1, r3, c2, c3)]
    corners: set[tuple[int, int]] = set()
    for rect in rectangles:
        corners.update(_rect_corners(*rect))
    if sorted(_all_rects(corners)) != sorted(rectangles):
        raise RuntimeError("interleaved construction produced accidental rectangles")
    return rectangles, corners


def _add_isolated_yellows(rng, height, width, corners, n_extra):
    result = set(corners)
    for _ in range(n_extra):
        candidates = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if (r, c) not in result
        ]
        rng.shuffle(candidates)
        target_count = len(_all_rects(result))
        for point in candidates:
            if len(_all_rects(result | {point})) == target_count:
                result.add(point)
                break
        else:
            return None
    return result


def _canonical_grid(ctx) -> list[list[int]]:
    """Return a diverse 10x10/two-color anchor on which the canonical rival fits.

    Some anchors replay one of the official forms.  The rest construct fresh
    one/two-rectangle scenes with the same exact profile, no distractors, and
    non-interleaved row ordering.  This preserves the lesson role of an anchor
    while avoiding a four-grid collapse when callers vary only the seed.
    """
    ctx.draw_int_strict("grid_h", 10, 10)
    ctx.draw_int_strict("grid_w", 10, 10)
    anchor_kind = ctx.draw_choice(
        "canonical_anchor_kind", ("official", "constructive", "constructive")
    )
    if anchor_kind == "official":
        form_index = ctx.draw_choice("canonical_form", tuple(range(len(_CANONICAL_FORMS))))
        corners = set(_CANONICAL_FORMS[form_index])
        n_rects = len(corners) // 4
        ctx.draw_int_strict("n_rects", n_rects, n_rects)
        ctx.draw_int_strict("n_extra_yellows", 0, 0)
        grid = full_grid(10, 10, 0)
        for r, c in corners:
            grid[r][c] = 4
        return grid

    n_rects = ctx.draw_choice("canonical_n_rects", (1, 2))
    ctx.draw_int_strict("n_rects", n_rects, n_rects)
    ctx.draw_int_strict("n_extra_yellows", 0, 0)
    rng = ctx.draw_rng("canonical_anchor")

    if n_rects == 1:
        r1 = rng.randint(0, 7)
        r2 = rng.randint(r1 + 2, 9)
        c1 = rng.randint(0, 7)
        c2 = rng.randint(c1 + 2, 9)
        rectangles = [(r1, r2, c1, c2)]
    else:
        # Two vertically separated row pairs make the adjacent-row rival fit;
        # distinct column pairs avoid accidental cross rectangles.
        r1 = rng.randint(0, 1)
        r2 = rng.randint(r1 + 2, 4)
        r3 = rng.randint(5, 7)
        r4 = rng.randint(r3 + 2, 9)
        c1 = rng.randint(0, 7)
        c2 = rng.randint(c1 + 2, 9)
        while True:
            c3 = rng.randint(0, 7)
            c4 = rng.randint(c3 + 2, 9)
            if (c3, c4) != (c1, c2):
                break
        rectangles = [(r1, r2, c1, c2), (r3, r4, c3, c4)]

    corners: set[tuple[int, int]] = set()
    for rectangle in rectangles:
        corners.update(_rect_corners(*rectangle))
    if sorted(_all_rects(corners)) != sorted(rectangles):
        raise RuntimeError("canonical-profile anchor created an accidental rectangle")
    grid = full_grid(10, 10, 0)
    for r, c in corners:
        grid[r][c] = 4
    if self_check(grid) or _adjacent_equal_row_pairs_only(grid) != _intended_output(grid):
        raise RuntimeError("canonical-profile anchor violates its lesson role")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    fully_unoverridden = not any(value is not None for value in overrides.values())
    if fully_unoverridden and profile == "canonical_anchor":
        return _canonical_grid(ctx)

    default_lo, default_hi = _difficulty_shape_band(difficulty)
    height = _draw_axis_int(ctx, overrides, "grid_h", 8, 18, default_lo, default_hi)
    width = _draw_axis_int(ctx, overrides, "grid_w", 8, 18, default_lo, default_hi)
    bias = _draw_bias(ctx, overrides)
    if fully_unoverridden and profile == "interleaved_rectangles":
        n_rects = ctx.draw_int_strict("n_rects", 2, 2)
    else:
        n_rects = ctx.draw_int_strict("n_rects", 1, 2)
    n_extra = ctx.draw_int_strict("n_extra_yellows", 0, 3)
    rng = ctx.draw_rng("placement")

    for _attempt in range(40):
        if fully_unoverridden and profile == "interleaved_rectangles":
            rectangles, corners = _place_interleaved_rects(rng, height, width, bias)
        else:
            rectangles, corners = _place_rects(rng, height, width, n_rects, bias)
        if rectangles is None:
            continue
        yellows = _add_isolated_yellows(rng, height, width, corners, n_extra)
        if yellows is None:
            continue
        grid = full_grid(height, width, 0)
        for r, c in yellows:
            grid[r][c] = 4
        errors = self_check(grid)
        if not errors:
            return grid
    raise ValueError(
        f"cannot construct n_rects={n_rects}, n_extra_yellows={n_extra} "
        f"on {height}x{width} with bias={bias!r}"
    )


def _paint_interiors(grid, rectangles) -> list[list[int]]:
    output = [list(row) for row in grid]
    for r1, r2, c1, c2 in rectangles:
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                output[r][c] = 2
    return output


def _intended_output(grid) -> list[list[int]]:
    """Pure audit/test mirror; the selected Racket program remains authority."""
    return _paint_interiors(grid, _all_rects(_yellow_cells(grid)))


def _adjacent_equal_row_pairs_only(grid) -> list[list[int]]:
    """Wrong rival: pair only adjacent yellow-bearing rows with equal columns."""
    by_row: dict[int, set[int]] = {}
    for r, c in _yellow_cells(grid):
        by_row.setdefault(r, set()).add(c)
    rows = sorted(by_row)
    rectangles = []
    for r1, r2 in zip(rows, rows[1:]):
        columns = sorted(by_row[r1])
        if by_row[r1] == by_row[r2] and len(columns) == 2:
            c1, c2 = columns
            if r2 - r1 >= 2 and c2 - c1 >= 2:
                rectangles.append((r1, r2, c1, c2))
    return _paint_interiors(grid, rectangles)


def _has_interleaved_rectangles(grid) -> bool:
    if self_check(grid):
        return False
    rectangles = _all_rects(_yellow_cells(grid))
    for first, second in combinations(rectangles, 2):
        a1, a2 = first[0], first[1]
        b1, b2 = second[0], second[1]
        if (a1 < b1 < a2 < b2) or (b1 < a1 < b2 < a2):
            return _adjacent_equal_row_pairs_only(grid) != _intended_output(grid)
    return False


def lesson_identifiable(demos, query) -> list[str]:
    """Report when the declared canonical shortcut can change the query answer."""
    rival_survives = all(
        _adjacent_equal_row_pairs_only(demo["input"]) == demo["output"]
        for demo in demos
    )
    if rival_survives and _adjacent_equal_row_pairs_only(query["input"]) != query["output"]:
        return [
            "adjacent_equal_row_pairs_only fits every demonstration but changes the query"
        ]
    return []


_RIVAL_NAME = "adjacent_equal_row_pairs_only"
SEMANTIC_WITNESSES = {"interleaved_rectangles": _has_interleaved_rectangles}
SEMANTIC_RIVALS = {_RIVAL_NAME: _adjacent_equal_row_pairs_only}
WITNESS_RIVALS = {"interleaved_rectangles": [_RIVAL_NAME]}
CANONICAL_SHORTCUTS = {_RIVAL_NAME: _adjacent_equal_row_pairs_only}
LESSON_COMPETITORS = {_RIVAL_NAME: _adjacent_equal_row_pairs_only}
