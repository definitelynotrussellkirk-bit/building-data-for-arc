"""Semantic generator for ARC task 272f95fa / 08f1d9bdd2ef.

Two complete cyan rows and two complete cyan columns partition a black canvas
into nine positive-area zones.  The five zones of the central cross receive
fixed, position-dependent colors; the four corner zones remain black.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "08f1d9bdd2ef"
VERSION = "4.0.0"
TASK_ID = "08f1d9bdd2ef"
RULE_HASH = "99b51630ed1d"
SUMMARY = (
    "Two full cyan rows and two full cyan columns divide a black canvas into "
    "a 3-by-3 zone grid. Preserve the cyan dividers and color the cross zones "
    "top red, left yellow, center magenta, right green, and bottom blue."
)
INVARIANTS = [
    "the input palette is exactly black 0 and cyan 8",
    "exactly two complete cyan rows and two complete cyan columns are present",
    "the dividers leave three positive-area row bands and three positive-area column bands",
    "every non-divider input cell is black",
    "the output preserves every divider and fills exactly the five central-cross zones",
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCENE_FAMILY_SCHEDULE = ("public", "generalized", "generalized", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "curriculum schedule: 1 public, 3 generalized",
        "valid": "public|generalized",
        "doc": "Complete official divider profile or a broader lawful layout.",
    },
}

BACKGROUND = 0
DIVIDER = 8
_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# Every official input profile, expressed as
# (height, width, separator rows, separator columns).
_PUBLIC_BASE_PROFILES = (
    (12, 14, (4, 7), (2, 9)),
    (18, 19, (2, 7), (4, 11)),
    (17, 15, (6, 13), (3, 8)),
)


def _transform_spec(height, width, sep_rows, sep_cols, transform):
    """Apply one of the eight D4 canvas transforms to a divider profile."""
    rows = tuple(sep_rows)
    cols = tuple(sep_cols)
    if transform == 0:
        return height, width, rows, cols
    if transform == 1:
        return height, width, rows, tuple(sorted(width - 1 - c for c in cols))
    if transform == 2:
        return height, width, tuple(sorted(height - 1 - r for r in rows)), cols
    if transform == 3:
        return (
            height,
            width,
            tuple(sorted(height - 1 - r for r in rows)),
            tuple(sorted(width - 1 - c for c in cols)),
        )
    if transform == 4:
        return width, height, cols, rows
    if transform == 5:
        return (
            width,
            height,
            cols,
            tuple(sorted(height - 1 - r for r in rows)),
        )
    if transform == 6:
        return (
            width,
            height,
            tuple(sorted(width - 1 - c for c in cols)),
            rows,
        )
    if transform == 7:
        return (
            width,
            height,
            tuple(sorted(width - 1 - c for c in cols)),
            tuple(sorted(height - 1 - r for r in rows)),
        )
    raise ValueError(f"unknown D4 transform: {transform}")


_PUBLIC_PROFILES = tuple(sorted({
    _transform_spec(*profile, transform)
    for profile in _PUBLIC_BASE_PROFILES
    for transform in range(8)
}))
_PUBLIC_SIGNATURES = frozenset(_PUBLIC_PROFILES)


def _order_style(values):
    """Dense ranks describing only the relative ordering/ties of a triple."""
    ordered = sorted(set(values))
    return tuple(ordered.index(value) for value in values)


def _style_from_specs(height, width, sep_rows, sep_cols):
    row_sizes = (sep_rows[0], sep_rows[1] - sep_rows[0] - 1,
                 height - sep_rows[1] - 1)
    col_sizes = (sep_cols[0], sep_cols[1] - sep_cols[0] - 1,
                 width - sep_cols[1] - 1)
    return _order_style(row_sizes), _order_style(col_sizes)


# The complete D4 closure collapses to sixteen qualitative band-order
# profiles.  These are the public anchor: sizes may scale, while every
# canonical ordering and equality relation is retained.
_PUBLIC_STYLE_PAIRS = frozenset(
    _style_from_specs(*profile) for profile in _PUBLIC_PROFILES
)
_BAND_DIMENSIONS = {
    "easy": (7, 20),
    "medium": (10, 25),
    "hard": (15, 30),
}

# The production sampler keeps its broad lawful distribution, but one quarter
# of deterministic coordinates anchor an exact canonical canvas scale.  This
# is a curriculum schedule rather than a gate-specific seed list: every band
# receives repeatable canonical-scale examples while the scene-family axis
# still controls the divider-band style.
SCHEDULE_PROFILES = ("canonical_scale", "broad")
_CANONICAL_SCALE_PERIOD = 4
_CANONICAL_SCALE_DIMENSIONS = tuple(
    (height, width) for height, width, _rows, _cols in _PUBLIC_BASE_PROFILES
)


def _triples_by_style(minimum, maximum):
    grouped = {}
    for dimension in range(minimum, maximum + 1):
        total = dimension - 2
        for first in range(1, total - 1):
            for second in range(1, total - first):
                third = total - first - second
                triple = (first, second, third)
                grouped.setdefault(_order_style(triple), []).append(triple)
    return {style: tuple(values) for style, values in grouped.items()}


_TRIPLES = {
    band: _triples_by_style(*bounds)
    for band, bounds in _BAND_DIMENSIONS.items()
}


def _build_candidate_blocks(band, family):
    grouped = _TRIPLES[band]
    blocks = []
    total = 0
    for row_style in sorted(grouped):
        for col_style in sorted(grouped):
            is_public = (row_style, col_style) in _PUBLIC_STYLE_PAIRS
            if is_public != (family == "public"):
                continue
            row_triples = grouped[row_style]
            col_triples = grouped[col_style]
            count = len(row_triples) * len(col_triples)
            blocks.append((row_triples, col_triples, count))
            total += count
    return tuple(blocks), total


_CANDIDATES = {
    (band, family): _build_candidate_blocks(band, family)
    for band in _BAND_DIMENSIONS
    for family in ("public", "generalized")
}


def _triples_for_dimension(dimension):
    total = dimension - 2
    return tuple(
        (first, second, total - first - second)
        for first in range(1, total - 1)
        for second in range(1, total - first)
    )


def _build_exact_profile_candidates(band, family):
    minimum, maximum = _BAND_DIMENSIONS[band]
    candidates = []
    for height, width in _CANONICAL_SCALE_DIMENSIONS:
        if not (minimum <= height <= maximum and minimum <= width <= maximum):
            continue
        for row_sizes in _triples_for_dimension(height):
            for col_sizes in _triples_for_dimension(width):
                is_public = (
                    _order_style(row_sizes), _order_style(col_sizes)
                ) in _PUBLIC_STYLE_PAIRS
                if is_public != (family == "public"):
                    continue
                sep_rows = (
                    row_sizes[0], row_sizes[0] + row_sizes[1] + 1
                )
                sep_cols = (
                    col_sizes[0], col_sizes[0] + col_sizes[1] + 1
                )
                candidates.append((height, width, sep_rows, sep_cols))
    if not candidates:
        raise RuntimeError(f"empty exact-profile space for {band}/{family}")
    return tuple(candidates)


_EXACT_PROFILE_CANDIDATES = {
    (band, family): _build_exact_profile_candidates(band, family)
    for band in _BAND_DIMENSIONS
    for family in ("public", "generalized")
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _band(index, first, second):
    if index < first:
        return 0
    if index < second:
        return 1
    return 2


def _paint_cross(height, width, sep_rows, sep_cols):
    first_row, second_row = sep_rows
    first_col, second_col = sep_cols
    zone_colors = {
        (0, 1): 2,
        (1, 0): 4,
        (1, 1): 6,
        (1, 2): 3,
        (2, 1): 1,
    }
    output = full_grid(height, width, BACKGROUND)
    for row in range(height):
        for col in range(width):
            if row in sep_rows or col in sep_cols:
                output[row][col] = DIVIDER
            else:
                output[row][col] = zone_colors.get(
                    (_band(row, first_row, second_row),
                     _band(col, first_col, second_col)),
                    BACKGROUND,
                )
    return output


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
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append("dimensions must lie in 5..30")
    palette = {value for row in grid for value in row}
    if palette != {BACKGROUND, DIVIDER}:
        errors.append(f"input palette must be exactly {{0, 8}}, found {sorted(palette)}")
    sep_rows = tuple(
        row for row in range(height)
        if all(grid[row][col] == DIVIDER for col in range(width))
    )
    sep_cols = tuple(
        col for col in range(width)
        if all(grid[row][col] == DIVIDER for row in range(height))
    )
    if len(sep_rows) != 2:
        errors.append(f"expected exactly two complete cyan rows, found {sep_rows}")
    if len(sep_cols) != 2:
        errors.append(f"expected exactly two complete cyan columns, found {sep_cols}")
    if len(sep_rows) != 2 or len(sep_cols) != 2:
        return {"errors": errors, "facts": None}

    row_sizes = (sep_rows[0], sep_rows[1] - sep_rows[0] - 1,
                 height - sep_rows[1] - 1)
    col_sizes = (sep_cols[0], sep_cols[1] - sep_cols[0] - 1,
                 width - sep_cols[1] - 1)
    if min(row_sizes) < 1 or min(col_sizes) < 1:
        errors.append("all nine zones must have positive area")
    for row in range(height):
        for col in range(width):
            expected = DIVIDER if row in sep_rows or col in sep_cols else BACKGROUND
            if grid[row][col] != expected:
                errors.append("every non-divider cell must be black")
                row = height
                break
        else:
            continue
        break

    output = _paint_cross(height, width, sep_rows, sep_cols)
    facts = {
        "height": height,
        "width": width,
        "sep_rows": sep_rows,
        "sep_cols": sep_cols,
        "row_band_sizes": row_sizes,
        "col_band_sizes": col_sizes,
        "signature": (height, width, sep_rows, sep_cols),
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def strict_canonical_like(grid):
    """Return [] exactly for lawful members of this task's semantic domain."""
    return self_check(grid)


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    style = (_order_style(facts["row_band_sizes"]),
             _order_style(facts["col_band_sizes"]))
    return "public" if style in _PUBLIC_STYLE_PAIRS else "generalized"


def observe_overrides(grid):
    family = canonical_profile_signature(grid)
    return {} if family == "invalid" else {"scene_family": family}


def _build_scene(height, width, sep_rows, sep_cols):
    grid = full_grid(height, width, BACKGROUND)
    for row in sep_rows:
        for col in range(width):
            grid[row][col] = DIVIDER
    for col in sep_cols:
        for row in range(height):
            grid[row][col] = DIVIDER
    return grid


def _validate_generation_coordinates(seed, sample_index):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _zigzag(value):
    return 2 * value if value >= 0 else -2 * value - 1


def _scene_rank(seed, sample_index):
    """Stable high-period rank for validated seed/sample coordinates."""
    _validate_generation_coordinates(seed, sample_index)
    if seed >= 0:
        return seed * 1_000_003 + sample_index
    left, right = _zigzag(seed), _zigzag(sample_index)
    diagonal = left + right
    return diagonal * (diagonal + 1) // 2 + right


def schedule_scene_family(seed, sample_index, difficulty=None):
    """One public and three generalized scenes in every four-pair window."""
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_generation_coordinates(seed, sample_index)
    phase = _scene_rank(seed, 0) % LESSON_SCHEDULE_PERIOD
    return SCENE_FAMILY_SCHEDULE[(sample_index - phase) % LESSON_SCHEDULE_PERIOD]


def schedule_profile(seed, sample_index, difficulty=None):
    """Declare the deterministic canonical-scale curriculum schedule."""
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    rank = _scene_rank(seed, sample_index)
    return (
        "canonical_scale"
        if rank % _CANONICAL_SCALE_PERIOD == 0
        else "broad"
    )


def _select_specs(seed, sample_index, band, family):
    blocks, total = _CANDIDATES[(band, family)]
    if total <= 0:
        raise RuntimeError(f"empty {band}/{family} candidate space")
    target = _scene_rank(seed, sample_index) % total
    for row_triples, col_triples, count in blocks:
        if target >= count:
            target -= count
            continue
        row_index, col_index = divmod(target, len(col_triples))
        row_sizes = row_triples[row_index]
        col_sizes = col_triples[col_index]
        height, width = sum(row_sizes) + 2, sum(col_sizes) + 2
        sep_rows = (row_sizes[0], row_sizes[0] + row_sizes[1] + 1)
        sep_cols = (col_sizes[0], col_sizes[0] + col_sizes[1] + 1)
        return height, width, sep_rows, sep_cols
    raise RuntimeError("candidate rank was not resolved")


def _select_exact_profile_specs(seed, sample_index, band, family):
    candidates = _EXACT_PROFILE_CANDIDATES[(band, family)]
    # The low two rank bits select the schedule profile.  Divide them away so
    # the exact-profile choice still traverses the full candidate list.
    target = (_scene_rank(seed, sample_index) // _CANONICAL_SCALE_PERIOD) % len(candidates)
    return candidates[target]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generation_coordinates(seed, sample_index)
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
    scheduled_family = schedule_scene_family(seed, sample_index, difficulty)
    family_options = (
        ("public", "generalized")
        if overrides.get("scene_family") is not None
        else (scheduled_family,)
    )
    family = ctx.draw_choice("scene_family", family_options)
    band = "medium" if difficulty in (None, "default") else difficulty
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "canonical_scale":
        specs = _select_exact_profile_specs(seed, sample_index, band, family)
    else:
        specs = _select_specs(seed, sample_index, band, family)
    grid = _build_scene(*specs)
    if self_check(grid) or canonical_profile_signature(grid) != family:
        raise RuntimeError(f"constructed invalid {family} divider scene")
    return grid


# ---------------------------------------------------------------------------
# Executable semantic rivals and lesson-level teaching contract
# ---------------------------------------------------------------------------


def _rival_public_style_only(grid):
    """Plausible shortcut: transform only public-style divider layouts."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if canonical_profile_signature(grid) == "public":
        return _copy_grid(analysis["facts"]["output"])
    return _copy_grid(grid)


def _witness_generalized_style(grid):
    return (
        canonical_profile_signature(grid) == "generalized"
        and _rival_public_style_only(grid) != rule_mirror(grid)
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "public_style_only": _rival_public_style_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "generalized_style": _witness_generalized_style,
}
WITNESS_RIVALS = {
    "generalized_style": ["public_style_only"],
}


def lesson_identifiable(demos, query):
    """Reject lessons whose demonstrations do not refute the named shortcut."""
    reasons = []
    for index, pair in enumerate(list(demos) + [query]):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is outside the task domain: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"pair {index} output disagrees with the selected rule")
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair.get("output")
                for pair in demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name} crashed: {exc}")
            continue
        if survives:
            reasons.append(f"demonstrations fail to refute rival {name}")
    return reasons
