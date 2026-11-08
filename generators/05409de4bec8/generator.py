"""Semantic paired-line generator for ARC task 6cdd2623 / 05409de4bec8.

One color occurs at four structured points.  Every row or column containing
exactly two of those points becomes a full line.  A four-corner rectangle is
the special case: only its longer axis is extended.  Two high-count distractor
colors are erased by the transformation.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "05409de4bec8"
VERSION = "5.0.0"
TASK_ID = "05409de4bec8"
RULE_HASH = "dfbf6efa8173"
SUMMARY = (
    "A modal black field contains four structured cells of one target color "
    "and two dense distractor colors. Rows and columns containing exactly two "
    "target cells become full target-colored lines; for a four-corner "
    "rectangle, only the longer rectangle axis is extended."
)
INVARIANTS = [
    "the background is black and the palette is exactly background, target, and two distractor colors",
    "exactly one nonzero color occurs four times on at most three rows and three columns",
    "the four target cells produce at least one exact pair row or exact pair column",
    "rectangle scenes have unequal row and column spans and extend only the longer axis",
    "both distractor colors occur at least five times and can never hijack target selection",
    "the transformation is visible and outputs only black plus the target color",
]
EXAMPLES_NEEDED = 4
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng public|generalized",
        "valid": "public|generalized",
        "doc": "Complete official feature profile or broader lawful paired-line scene.",
    },
}

BACKGROUND = 0
_COLORS = tuple(range(1, 10))
_PATTERNS = (
    "rectangle", "cross", "two_rows_one_col", "two_cols_one_row",
    "row_only", "col_only",
)

# Four demonstrations plus one query are assembled from consecutive sample
# indices.  Any four consecutive slots in this five-cycle contain at least one
# rectangle and one multi-pair scene.  The duplicated witnesses make every
# one-query rotation distinguish both declared shortcuts.
SCHEDULE_PROFILES = (
    "rectangle_a",
    "multi_row",
    "rectangle_b",
    "multi_col",
    "cross_anchor",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

# Complete role-normalized official input profiles.  Distractor positions are
# nuisance variation, but their two color counts are retained jointly with the
# dimensions and all four target coordinates.
_PUBLIC_PROFILES = (
    (13, 20, ((3, 0), (3, 19), (11, 0), (11, 19)), (10, 11)),
    (11, 22, ((0, 11), (8, 0), (8, 21), (10, 11)), (19, 28)),
    (15, 17, ((0, 13), (10, 0), (10, 16), (14, 13)), (8, 29)),
    (16, 19, ((0, 3), (5, 0), (5, 18), (15, 3)), (14, 25)),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _transform_points(height, width, points, transform):
    if transform == 0:
        return height, width, tuple(points)
    if transform == 1:
        return height, width, tuple((r, width - 1 - c) for r, c in points)
    if transform == 2:
        return height, width, tuple((height - 1 - r, c) for r, c in points)
    if transform == 3:
        return height, width, tuple(
            (height - 1 - r, width - 1 - c) for r, c in points
        )
    if transform == 4:
        return width, height, tuple((c, r) for r, c in points)
    if transform == 5:
        return width, height, tuple((c, height - 1 - r) for r, c in points)
    if transform == 6:
        return width, height, tuple((width - 1 - c, r) for r, c in points)
    if transform == 7:
        return width, height, tuple(
            (width - 1 - c, height - 1 - r) for r, c in points
        )
    raise ValueError(f"unknown D4 transform: {transform}")


def _target_candidates(grid):
    color_cells = defaultdict(list)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != BACKGROUND:
                color_cells[value].append((row_index, col_index))
    candidates = []
    for color, cells in color_cells.items():
        if (
            len(cells) == 4
            and len({row for row, _ in cells}) <= 3
            and len({col for _, col in cells}) <= 3
        ):
            candidates.append((color, tuple(sorted(cells))))
    return candidates, color_cells


def _line_facts(points):
    row_counts = Counter(row for row, _ in points)
    col_counts = Counter(col for _, col in points)
    row_pairs = tuple(sorted(row for row, count in row_counts.items() if count == 2))
    col_pairs = tuple(sorted(col for col, count in col_counts.items() if count == 2))
    rectangle = len(row_pairs) == 2 and len(col_pairs) == 2
    if rectangle:
        row_span = row_pairs[1] - row_pairs[0]
        col_span = col_pairs[1] - col_pairs[0]
        if col_span > row_span:
            horizontal, vertical = row_pairs, ()
        else:
            horizontal, vertical = (), col_pairs
    else:
        row_span = None
        col_span = None
        horizontal, vertical = row_pairs, col_pairs
    return {
        "row_pairs": row_pairs,
        "col_pairs": col_pairs,
        "rectangle": rectangle,
        "row_span": row_span,
        "col_span": col_span,
        "horizontal": tuple(horizontal),
        "vertical": tuple(vertical),
    }


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"], "facts": None}

    height = len(grid)
    if not (9 <= height <= 28 and 9 <= width <= 28):
        errors.append("dimensions must lie in 9..28")
    palette = {value for row in grid for value in row}
    if len(palette) != 4 or BACKGROUND not in palette:
        errors.append("palette must be exactly black plus three nonzero colors")
    if sum(value == BACKGROUND for row in grid for value in row) <= height * width / 2:
        errors.append("black must be the modal field")

    candidates, color_cells = _target_candidates(grid)
    if len(candidates) != 1:
        errors.append(f"expected exactly one target color, found {len(candidates)}")
        return {"errors": errors, "facts": None}
    target_color, points = candidates[0]
    decoy_counts = sorted(
        len(cells) for color, cells in color_cells.items() if color != target_color
    )
    if len(decoy_counts) != 2 or any(not 5 <= count <= 50 for count in decoy_counts):
        errors.append("exactly two distractor colors must each occur 5..50 times")

    lines = _line_facts(points)
    if not lines["horizontal"] and not lines["vertical"]:
        errors.append("target points must define at least one exact-pair line")
    if lines["rectangle"] and lines["row_span"] == lines["col_span"]:
        errors.append("rectangle spans must be unequal")

    output = full_grid(height, width, BACKGROUND)
    for row in lines["horizontal"]:
        for col in range(width):
            output[row][col] = target_color
    for col in lines["vertical"]:
        for row in range(height):
            output[row][col] = target_color
    if output == [list(row) for row in grid]:
        errors.append("rule must visibly replace points/noise with full lines")
    facts = {
        "height": height,
        "width": width,
        "target_color": target_color,
        "points": points,
        "decoy_counts": tuple(decoy_counts),
        "output": output,
        **lines,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid):
    """Return errors for the complete lawful manifold sampled here."""
    return self_check(grid)


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def _paint_pair_lines(facts, horizontal, vertical):
    output = full_grid(facts["height"], facts["width"], BACKGROUND)
    for row in horizontal:
        for col in range(facts["width"]):
            output[row][col] = facts["target_color"]
    for col in vertical:
        for row in range(facts["height"]):
            output[row][col] = facts["target_color"]
    return output


def _all_pair_lines(grid):
    """Plausible rival: omit the rectangle exception entirely."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return _paint_pair_lines(facts, facts["row_pairs"], facts["col_pairs"])


def _single_pair_per_axis(grid):
    """Canonical-fitting shortcut: assume at most one pair-line per axis.

    The canonical rectangle still uses its demonstrated longer-axis exception;
    every canonical non-rectangle is a cross with one pair row and one pair
    column.  Generated multi-row/multi-column scenes refute the shortcut.
    """
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if facts["rectangle"]:
        return _copy_grid(facts["output"])
    return _paint_pair_lines(
        facts, facts["horizontal"][:1], facts["vertical"][:1]
    )


def _rival_differs(name):
    return lambda grid: SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "all_pair_lines": _all_pair_lines,
    "single_pair_per_axis": _single_pair_per_axis,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "single_pair_per_axis": _single_pair_per_axis,
}
SEMANTIC_WITNESSES = {
    "rectangle_long_axis_exception": _rival_differs("all_pair_lines"),
    "multiple_parallel_pair_lines": _rival_differs("single_pair_per_axis"),
}
WITNESS_RIVALS = {
    "rectangle_long_axis_exception": ["all_pair_lines"],
    "multiple_parallel_pair_lines": ["single_pair_per_axis"],
}


def _pair_errors(pair, label):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label}: pair must contain input and output"]
    try:
        expected = rule_mirror(pair["input"])
    except Exception as exc:
        return [f"{label}: invalid input: {type(exc).__name__}: {exc}"]
    if pair["output"] != expected:
        return [f"{label}: output does not match the intended paired-line rule"]
    return []


def lesson_identifiable(demos, query):
    """Reject a lesson when a named lawful rival fits demos but changes query."""
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    expected_query = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            if survives and rival(query["input"]) != expected_query:
                reasons.append(
                    f"named rival {name!r} fits every demo but changes the query"
                )
        except Exception as exc:
            reasons.append(f"named rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    """Fixed five-slot lesson curriculum; seed and difficulty affect nuisance draws."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative plain integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _profile_signature(height, width, points, decoy_counts):
    return height, width, tuple(sorted(points)), tuple(sorted(decoy_counts))


def _public_signatures():
    signatures = set()
    for height, width, points, decoy_counts in _PUBLIC_PROFILES:
        for transform in range(8):
            out_h, out_w, out_points = _transform_points(
                height, width, points, transform
            )
            signatures.add(_profile_signature(out_h, out_w, out_points, decoy_counts))
    return frozenset(signatures)


_PUBLIC_SIGNATURES = _public_signatures()


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    signature = _profile_signature(
        facts["height"], facts["width"], facts["points"], facts["decoy_counts"]
    )
    return "public" if signature in _PUBLIC_SIGNATURES else "generalized"


def observe_overrides(grid):
    family = canonical_profile_signature(grid)
    return {} if family == "invalid" else {"scene_family": family}


def _choose_dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(10, 15), rng.randint(15, 21)
    if difficulty == "hard":
        return rng.randint(15, 24), rng.randint(18, 28)
    return rng.randint(11, 19), rng.randint(16, 24)


def _rectangle_points(rng, height, width):
    for _ in range(200):
        rows = sorted(rng.sample(range(height), 2))
        cols = sorted(rng.sample(range(width), 2))
        if rows[1] - rows[0] == cols[1] - cols[0]:
            continue
        return tuple((row, col) for row in rows for col in cols)
    return None


def _cross_points(rng, height, width):
    rows = sorted(rng.sample(range(height), 3))
    cols = sorted(rng.sample(range(width), 3))
    return ((rows[0], cols[1]), (rows[1], cols[0]),
            (rows[1], cols[2]), (rows[2], cols[1]))


def _two_rows_one_col(rng, height, width):
    rows = sorted(rng.sample(range(height), 2))
    cols = sorted(rng.sample(range(width), 3))
    return ((rows[0], cols[0]), (rows[0], cols[1]),
            (rows[1], cols[1]), (rows[1], cols[2]))


def _row_only(rng, height, width):
    rows = sorted(rng.sample(range(height), 3))
    cols = sorted(rng.sample(range(width), 2))
    return ((rows[0], cols[0]), (rows[1], cols[0]),
            (rows[1], cols[1]), (rows[2], cols[0]))


def _transpose_points(points):
    return tuple((col, row) for row, col in points)


def _generalized_specs(rng, difficulty, forced_pattern=None):
    height, width = _choose_dimensions(rng, difficulty)
    if difficulty == "easy":
        pattern = forced_pattern or rng.choice(
            ("rectangle", "cross", "cross", "row_only", "col_only")
        )
        count_range = 8, 18
    elif difficulty == "hard":
        pattern = forced_pattern or rng.choice(_PATTERNS)
        count_range = 20, 42
    else:
        pattern = forced_pattern or rng.choice(_PATTERNS)
        count_range = 14, 30
    if pattern == "rectangle":
        points = _rectangle_points(rng, height, width)
    elif pattern == "cross":
        points = _cross_points(rng, height, width)
    elif pattern == "two_rows_one_col":
        points = _two_rows_one_col(rng, height, width)
    elif pattern == "two_cols_one_row":
        transposed = _two_rows_one_col(rng, width, height)
        points = _transpose_points(transposed)
    elif pattern == "row_only":
        points = _row_only(rng, height, width)
    else:
        transposed = _row_only(rng, width, height)
        points = _transpose_points(transposed)
    return height, width, points, (
        rng.randint(*count_range), rng.randint(*count_range)
    )


def _public_specs(rng, schedule=None):
    profiles = _PUBLIC_PROFILES
    if schedule in ("rectangle_a", "rectangle_b"):
        profiles = tuple(
            profile for profile in profiles if _line_facts(profile[2])["rectangle"]
        )
    elif schedule == "cross_anchor":
        profiles = tuple(
            profile for profile in profiles if not _line_facts(profile[2])["rectangle"]
        )
    height, width, points, decoy_counts = rng.choice(profiles)
    return (*_transform_points(height, width, points, rng.randrange(8)), decoy_counts)


def _scheduled_pattern(profile, rng):
    if profile in ("rectangle_a", "rectangle_b"):
        return "rectangle"
    if profile == "multi_row":
        return "two_rows_one_col"
    if profile == "multi_col":
        return "two_cols_one_row"
    return rng.choice(("cross", "row_only", "col_only"))


def _scheduled_family(ctx, profile):
    explicit = (
        "scene_family" in ctx.overrides
        and ctx.overrides["scene_family"] is not None
    )
    if explicit:
        return ctx.draw_choice("scene_family", ("public", "generalized")), True
    if profile == "cross_anchor":
        return ctx.draw_choice("scene_family", ("public",)), False
    if profile in ("rectangle_a", "rectangle_b"):
        return ctx.draw_choice(
            "scene_family", ("public",) + ("generalized",) * 7
        ), False
    return ctx.draw_choice("scene_family", ("generalized",)), False


def _build_scene(rng, height, width, points, decoy_counts):
    if points is None or len(set(points)) != 4:
        return None
    if any(not (0 <= row < height and 0 <= col < width) for row, col in points):
        return None
    target_color, first_decoy, second_decoy = rng.sample(_COLORS, 3)
    grid = full_grid(height, width, BACKGROUND)
    for row, col in points:
        grid[row][col] = target_color
    empty = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == BACKGROUND
    ]
    if sum(decoy_counts) > len(empty):
        return None
    rng.shuffle(empty)
    cursor = 0
    for color, count in zip((first_decoy, second_decoy), decoy_counts):
        for row, col in empty[cursor: cursor + count]:
            grid[row][col] = color
        cursor += count
    return grid


_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int:
            raise TypeError(f"{name} must be a plain integer (not bool)")
        if value < 0:
            raise ValueError(f"{name} must be nonnegative")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    family, explicit_family = _scheduled_family(ctx, profile)
    rng = ctx.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    forced_pattern = None if explicit_family else _scheduled_pattern(profile, rng)
    for _ in range(300):
        if family == "public":
            height, width, points, decoy_counts = _public_specs(
                rng, None if explicit_family else profile
            )
        else:
            height, width, points, decoy_counts = _generalized_specs(
                rng, band, forced_pattern
            )
        grid = _build_scene(rng, height, width, points, decoy_counts)
        if grid is None:
            continue
        if self_check(grid):
            continue
        if canonical_profile_signature(grid) != family:
            continue
        return grid
    raise RuntimeError(f"could not construct a valid {family} scene")
