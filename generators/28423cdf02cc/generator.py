"""Generator for puzzle 363442ee / canonical task 28423cdf02cc.

The input contains a fully colored asymmetric 3x3 template in the top-left,
a full-height gray(5) divider in column 3, and blue(1) marker cells to the
right.  The Racket rule copies the template, centered on every marker.

The default distribution uses a five-slot teaching schedule: two exact
canonical-profile slots followed by three guaranteed off-lattice slots.  This
preserves a 40% exact-canonical prior while ensuring every three-example lesson
and every four-pair query rotation contains evidence against a fixed-lattice
shortcut.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28423cdf02cc"
TASK_ID = "28423cdf02cc"
VERSION = "3.1.1"
RULE_HASH = "63b41fa0b187"

SUMMARY = (
    "A 0-background grid has a fully colored asymmetric 3x3 template at "
    "rows 0..2, columns 0..2; a full-height color-5 divider at column 3; "
    "and 3..6 color-1 markers in the right region.  For every marker, copy "
    "the complete 3x3 template centered on that marker.  The original "
    "template and divider remain unchanged."
)

INVARIANTS = [
    "grid dimensions are 9..16 by 13..20",
    "the top-left 3x3 template is full, uses 3..5 colors, excludes 0/1/5, "
    "and has eight distinct dihedral orientations",
    "column 3 is entirely color 5 and color 5 appears nowhere else",
    "column 4 is a blank separator in the input",
    "outside the template and divider, input cells are only background 0 or "
    "blue marker 1",
    "there are 3..6 markers, each center admits a complete 3x3 stamp",
    "marker stamps do not overlap, and markers span at least two rows and two "
    "columns",
]

_H_MIN, _H_MAX = 9, 16
_W_MIN, _W_MAX = 13, 20
_N_MIN, _N_MAX = 3, 6
_PALETTE_MIN, _PALETTE_MAX = 3, 5
_TEMPLATE_COLORS = (2, 3, 4, 6, 7, 8, 9)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35
LESSON_SCHEDULE_PERIOD = 5
SCHEDULE_PROFILES = ("canonical_profile", "anti_lattice")
_LESSON_PROFILE_SCHEDULE = (
    "canonical_profile",
    "canonical_profile",
    "anti_lattice",
    "anti_lattice",
    "anti_lattice",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the default teaching profile for a pair position.

    The profile is intentionally independent of seed and difficulty.  Every
    cyclic three-pair demonstration window contains an anti-lattice witness;
    every cyclic four-pair window contains at least two, so any held-out query
    still leaves one in the demonstrations.
    """
    del seed, difficulty
    return _LESSON_PROFILE_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]

# Exact joint canonical input profiles, including answer-bearing marker
# morphology.  The template colors vary; only the observed linked structure is
# pinned.  (n_markers, n_template_colors, marker_positions)
_CANONICAL_PROFILES = (
    (
        5,
        3,
        ((1, 8), (4, 5), (4, 11), (7, 5), (7, 8)),
    ),
    (
        3,
        3,
        ((1, 5), (4, 8), (7, 8)),
    ),
    (
        5,
        5,
        ((1, 5), (1, 11), (4, 8), (7, 8), (7, 11)),
    ),
    (
        6,
        4,
        ((1, 8), (1, 11), (4, 5), (4, 11), (7, 5), (7, 8)),
    ),
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "40% canonical h=9; otherwise difficulty-shaped",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "40% canonical w=13; otherwise difficulty-shaped",
        "valid": "13..20",
    },
    "n_dots": {
        "type": "int",
        "default": "40% canonical linked count; otherwise difficulty-shaped",
        "valid": "3..6",
    },
    "palette_size": {
        "type": "int",
        "default": "40% canonical linked size; otherwise difficulty-shaped",
        "valid": "3..5",
    },
}


def _grid_copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _rotate(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    n = len(template)
    return tuple(
        tuple(template[n - 1 - c][r] for c in range(n))
        for r in range(n)
    )


def _flip_lr(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in template)


def _dihedral_variants(
    template: tuple[tuple[int, ...], ...],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    variants: list[tuple[tuple[int, ...], ...]] = []
    current = template
    for _ in range(4):
        variants.append(current)
        current = _rotate(current)
    current = _flip_lr(template)
    for _ in range(4):
        variants.append(current)
        current = _rotate(current)
    return tuple(variants)


def _template_is_asymmetric(template: tuple[tuple[int, ...], ...]) -> bool:
    return len(set(_dihedral_variants(template))) == 8


def _draw_template(palette_size: int, rng) -> list[list[int]]:
    """Return a full 3x3 template with exactly palette_size colors.

    Every selected color is used at least once and the pattern has no dihedral
    symmetry, so copying the exact orientation is answer-bearing.
    """
    palette = rng.sample(list(_TEMPLATE_COLORS), palette_size)
    for _ in range(256):
        values = list(palette)
        while len(values) < 9:
            values.append(rng.choice(palette))
        rng.shuffle(values)
        template = tuple(
            tuple(values[3 * r + c] for c in range(3))
            for r in range(3)
        )
        if _template_is_asymmetric(template):
            return [list(row) for row in template]
    raise RuntimeError("could not draw an asymmetric 3x3 template")


def _stamps_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return abs(left[0] - right[0]) <= 2 and abs(left[1] - right[1]) <= 2


def _valid_marker_set(points: list[tuple[int, int]], n_dots: int) -> bool:
    if len(points) != n_dots:
        return False
    if len({r for r, _ in points}) < 2 or len({c for _, c in points}) < 2:
        return False
    return all(
        not _stamps_overlap(points[i], points[j])
        for i in range(len(points))
        for j in range(i + 1, len(points))
    )


def _lattice_points(
    h: int,
    w: int,
    row_start: int,
    col_start: int,
) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(row_start, h - 1, 3)
        for c in range(col_start, w - 1, 3)
    ]


def _choose_subset(
    pool: list[tuple[int, int]],
    n_dots: int,
    rng,
) -> list[tuple[int, int]] | None:
    if len(pool) < n_dots:
        return None
    for _ in range(128):
        points = rng.sample(pool, n_dots)
        if _valid_marker_set(points, n_dots):
            return sorted(points)
    return None


def _choose_scattered(
    h: int,
    w: int,
    n_dots: int,
    rng,
) -> list[tuple[int, int]] | None:
    candidates = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(5, w - 1)
    ]
    for _ in range(256):
        order = candidates[:]
        rng.shuffle(order)
        chosen: list[tuple[int, int]] = []
        for point in order:
            if all(not _stamps_overlap(point, prior) for prior in chosen):
                chosen.append(point)
                if len(chosen) == n_dots:
                    if _valid_marker_set(chosen, n_dots):
                        return sorted(chosen)
                    break
    return None


def _draw_markers(h: int, w: int, n_dots: int, rng) -> list[tuple[int, int]]:
    families = (
        "canonical_lattice",
        "canonical_lattice",
        "shifted_lattice",
        "scattered",
        "scattered",
    )
    family = rng.choice(families)

    if family == "canonical_lattice":
        points = _choose_subset(_lattice_points(h, w, 1, 5), n_dots, rng)
        if points is not None:
            return points

    if family == "shifted_lattice":
        offsets = [
            (row_start, col_start)
            for row_start in (1, 2, 3)
            for col_start in (5, 6, 7)
            if (row_start, col_start) != (1, 5)
        ]
        rng.shuffle(offsets)
        for row_start, col_start in offsets:
            points = _choose_subset(
                _lattice_points(h, w, row_start, col_start),
                n_dots,
                rng,
            )
            if points is not None:
                return points

    points = _choose_scattered(h, w, n_dots, rng)
    if points is not None:
        return points

    # The canonical 3-spaced lattice has at least nine cells at the declared
    # minimum dimensions, so this fallback is guaranteed for n_dots <= 6.
    points = _choose_subset(_lattice_points(h, w, 1, 5), n_dots, rng)
    if points is None:
        raise RuntimeError(
            f"could not place {n_dots} non-overlapping markers in {h}x{w}"
        )
    return points


def _is_canonical_lattice_marker(point: tuple[int, int]) -> bool:
    r, c = point
    return (r - 1) % 3 == 0 and (c - 5) % 3 == 0


def _has_off_lattice_marker(points: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> bool:
    return any(not _is_canonical_lattice_marker(point) for point in points)


def _draw_off_lattice_markers(
    h: int,
    w: int,
    n_dots: int,
    rng,
) -> list[tuple[int, int]]:
    """Draw a lawful marker set with at least one noncanonical-lattice center."""
    strategies = ["shifted_lattice", "scattered", "scattered"]
    rng.shuffle(strategies)
    for strategy in strategies:
        if strategy == "scattered":
            for _ in range(4):
                points = _choose_scattered(h, w, n_dots, rng)
                if points is not None and _has_off_lattice_marker(points):
                    return points
            continue

        offsets = [
            (row_start, col_start)
            for row_start in (1, 2, 3)
            for col_start in (5, 6, 7)
            if (row_start, col_start) != (1, 5)
        ]
        rng.shuffle(offsets)
        for row_start, col_start in offsets:
            points = _choose_subset(
                _lattice_points(h, w, row_start, col_start),
                n_dots,
                rng,
            )
            if points is not None and _has_off_lattice_marker(points):
                return points

    # At the declared minimum 9x13 canvas, the (row=1, col=6) shifted
    # lattice has 3x2 = 6 non-overlapping centers, so this is guaranteed.
    points = _choose_subset(_lattice_points(h, w, 1, 6), n_dots, rng)
    if points is None or not _has_off_lattice_marker(points):
        raise RuntimeError(
            f"could not place {n_dots} off-lattice markers in {h}x{w}"
        )
    return points


def _band_bounds(difficulty: str | None) -> dict[str, tuple[int, int]]:
    if difficulty in (None, "medium"):
        return {
            "grid_h": (9, 14),
            "grid_w": (13, 18),
            "n_dots": (3, 5),
            "palette_size": (3, 5),
        }
    if difficulty == "easy":
        return {
            "grid_h": (9, 11),
            "grid_w": (13, 15),
            "n_dots": (3, 4),
            "palette_size": (3, 4),
        }
    if difficulty == "hard":
        return {
            "grid_h": (11, 16),
            "grid_w": (15, 20),
            "n_dots": (4, 6),
            "palette_size": (4, 5),
        }
    raise ValueError(
        f"difficulty must be easy, medium, hard, or None; got {difficulty!r}"
    )


def _draw_banded_int(
    ctx,
    overrides: dict,
    label: str,
    default_bounds: tuple[int, int],
    valid_bounds: tuple[int, int],
) -> int:
    """Band-shape defaults but validate overrides against the full contract."""
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, valid_bounds[0], valid_bounds[1])
    return ctx.draw_int_strict(label, default_bounds[0], default_bounds[1])


def _canonical_profile_index(
    h: int,
    w: int,
    n_dots: int,
    palette_size: int,
    markers: tuple[tuple[int, int], ...],
) -> int | None:
    if (h, w) != (9, 13):
        return None
    for index, (expected_n, expected_palette, expected_markers) in enumerate(
        _CANONICAL_PROFILES
    ):
        if (
            n_dots == expected_n
            and palette_size == expected_palette
            and markers == expected_markers
        ):
            return index
    return None


def _classify_layout(markers: tuple[tuple[int, int], ...]) -> str:
    if not markers:
        return "empty"
    row_residues = {(r - 1) % 3 for r, _ in markers}
    col_residues = {(c - 5) % 3 for _, c in markers}
    if row_residues == {0} and col_residues == {0}:
        return "canonical_lattice"
    if len(row_residues) == 1 and len(col_residues) == 1:
        return "shifted_lattice"
    return "scattered"


def _analyze(grid) -> dict:
    errors: list[str] = []
    facts: dict = {
        "grid_h": 0,
        "grid_w": 0,
        "n_dots": 0,
        "palette_size": 0,
        "markers": (),
        "layout_family": "invalid",
        "canonical_profile": None,
    }

    if not isinstance(grid, list) or not grid:
        return {"errors": ["empty grid"], "facts": facts}
    if not all(isinstance(row, list) for row in grid) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of rows"], "facts": facts}

    h, w = len(grid), len(grid[0])
    facts["grid_h"], facts["grid_w"] = h, w
    if any(len(row) != w for row in grid):
        return {"errors": ["ragged grid"], "facts": facts}

    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append("all cells must be integer ARC colors 0..9")

    if not (_H_MIN <= h <= _H_MAX and _W_MIN <= w <= _W_MAX):
        errors.append(
            f"dims {h}x{w} outside {_H_MIN}..{_H_MAX} x {_W_MIN}..{_W_MAX}"
        )
    if h < 3 or w < 5:
        return {"errors": errors + ["grid too small for template/divider"], "facts": facts}

    template = tuple(tuple(grid[r][c] for c in range(3)) for r in range(3))
    template_values = [value for row in template for value in row]
    template_palette = set(template_values)
    facts["template"] = template
    facts["palette_size"] = len(template_palette)

    if any(value not in _TEMPLATE_COLORS for value in template_values):
        errors.append("top-left 3x3 template must be full and exclude colors 0, 1, and 5")
    if not (_PALETTE_MIN <= len(template_palette) <= _PALETTE_MAX):
        errors.append(
            f"template must use {_PALETTE_MIN}..{_PALETTE_MAX} distinct colors"
        )
    if len(template) == 3 and not _template_is_asymmetric(template):
        errors.append("template must have eight distinct dihedral orientations")

    if any(grid[r][3] != 5 for r in range(h)):
        errors.append("column 3 must be a full-height color-5 divider")
    if any(grid[r][c] == 5 for r in range(h) for c in range(w) if c != 3):
        errors.append("color 5 may appear only in divider column 3")
    if any(grid[r][4] != 0 for r in range(h)):
        errors.append("column 4 must remain a blank separator")

    body_violations: list[tuple[int, int, int]] = []
    markers: list[tuple[int, int]] = []
    for r in range(h):
        for c in range(w):
            if r < 3 and c < 3:
                continue
            if c == 3:
                continue
            value = grid[r][c]
            if value not in (0, 1):
                body_violations.append((r, c, value))
            if value == 1:
                markers.append((r, c))

    markers_tuple = tuple(markers)
    facts["markers"] = markers_tuple
    facts["n_dots"] = len(markers_tuple)
    facts["layout_family"] = _classify_layout(markers_tuple)
    facts["canonical_profile"] = _canonical_profile_index(
        h,
        w,
        len(markers_tuple),
        len(template_palette),
        markers_tuple,
    )

    if body_violations:
        errors.append(
            "outside the template/divider, cells must be only background 0 or marker 1"
        )
    if not (_N_MIN <= len(markers_tuple) <= _N_MAX):
        errors.append(f"expected {_N_MIN}..{_N_MAX} blue markers")
    if any(not (1 <= r <= h - 2 and 5 <= c <= w - 2) for r, c in markers_tuple):
        errors.append("every marker must be an interior stamp center right of the divider")
    if any(
        _stamps_overlap(markers_tuple[i], markers_tuple[j])
        for i in range(len(markers_tuple))
        for j in range(i + 1, len(markers_tuple))
    ):
        errors.append("marker-centered 3x3 stamps must not overlap")
    if markers_tuple and (
        len({r for r, _ in markers_tuple}) < 2
        or len({c for _, c in markers_tuple}) < 2
    ):
        errors.append("markers must span at least two rows and two columns")

    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons using the task's complete input grammar."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    facts = _analyze(grid)["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_dots": facts["n_dots"],
        "palette_size": facts["palette_size"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror of the canonical Racket rule.

    Generation never uses this function for output authority.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("rule_mirror expects a rectangular non-empty grid")
    h, w = len(grid), len(grid[0])
    template = [row[:3] for row in grid[:3]]
    markers = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 1
    ]
    output = _grid_copy(grid)
    for marker_r, marker_c in markers:
        for template_r in range(3):
            for template_c in range(3):
                target_r = marker_r - 1 + template_r
                target_c = marker_c - 1 + template_c
                if (
                    0 <= target_r < h
                    and 0 <= target_c < w
                    and output[target_r][target_c] in (0, 1)
                ):
                    output[target_r][target_c] = template[template_r][template_c]
    return output


def strict_canonical_like(grid) -> list[str]:
    """Accept exactly the four linked canonical input profiles."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if not reasons and analysis["facts"]["canonical_profile"] is None:
        reasons.append("input is lawful but outside the four exact canonical profiles")
    return reasons


def _template_tuple(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(grid[r][c] for c in range(3)) for r in range(3))


def _input_markers(grid) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]


def _flip_ud(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(reversed(template))


def _transpose(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(template[r][c] for r in range(3)) for c in range(3))


def _anti_transpose(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return _transpose(_rotate(_rotate(template)))


def _stamp_variant(
    grid: list[list[int]],
    *,
    template: tuple[tuple[int, ...], ...] | None = None,
    markers: list[tuple[int, int]] | None = None,
    anchor_offset: tuple[int, int] = (-1, -1),
) -> list[list[int]]:
    """Apply a deterministic rival stamp while preserving canonical overwrite rules."""
    h, w = len(grid), len(grid[0])
    chosen_template = template if template is not None else _template_tuple(grid)
    chosen_markers = markers if markers is not None else _input_markers(grid)
    output = _grid_copy(grid)
    for marker_r, marker_c in chosen_markers:
        for template_r in range(3):
            for template_c in range(3):
                target_r = marker_r + anchor_offset[0] + template_r
                target_c = marker_c + anchor_offset[1] + template_c
                if (
                    0 <= target_r < h
                    and 0 <= target_c < w
                    and output[target_r][target_c] in (0, 1)
                ):
                    output[target_r][target_c] = chosen_template[template_r][template_c]
    return output


def _rival_rotate_90(grid):
    return _stamp_variant(grid, template=_rotate(_template_tuple(grid)))


def _rival_rotate_180(grid):
    return _stamp_variant(grid, template=_rotate(_rotate(_template_tuple(grid))))


def _rival_rotate_270(grid):
    return _stamp_variant(
        grid,
        template=_rotate(_rotate(_rotate(_template_tuple(grid)))),
    )


def _rival_flip_left_right(grid):
    return _stamp_variant(grid, template=_flip_lr(_template_tuple(grid)))


def _rival_flip_up_down(grid):
    return _stamp_variant(grid, template=_flip_ud(_template_tuple(grid)))


def _rival_transpose(grid):
    return _stamp_variant(grid, template=_transpose(_template_tuple(grid)))


def _rival_anti_transpose(grid):
    return _stamp_variant(grid, template=_anti_transpose(_template_tuple(grid)))


def _rival_marker_is_top_left(grid):
    return _stamp_variant(grid, anchor_offset=(0, 0))


def _rival_first_marker_only(grid):
    markers = _input_markers(grid)
    return _stamp_variant(grid, markers=markers[:1])


def _rival_center_cell_only(grid):
    output = _grid_copy(grid)
    center_color = grid[1][1]
    for r, c in _input_markers(grid):
        output[r][c] = center_color
    return output


def _rival_fixed_canonical_lattice_only(grid):
    markers = [
        point for point in _input_markers(grid)
        if _is_canonical_lattice_marker(point)
    ]
    return _stamp_variant(grid, markers=markers)


SEMANTIC_RIVALS = {
    "rotate_template_90": _rival_rotate_90,
    "rotate_template_180": _rival_rotate_180,
    "rotate_template_270": _rival_rotate_270,
    "flip_template_left_right": _rival_flip_left_right,
    "flip_template_up_down": _rival_flip_up_down,
    "transpose_template": _rival_transpose,
    "anti_transpose_template": _rival_anti_transpose,
    "marker_is_top_left": _rival_marker_is_top_left,
    "first_marker_only": _rival_first_marker_only,
    "center_cell_only": _rival_center_cell_only,
    "fixed_canonical_lattice_only": _rival_fixed_canonical_lattice_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_canonical_lattice_only": _rival_fixed_canonical_lattice_only,
}


def _lawful_input(grid) -> bool:
    return not self_check(grid)


def _witness_off_canonical_lattice(grid) -> bool:
    return _lawful_input(grid) and _has_off_lattice_marker(
        tuple(_input_markers(grid))
    )


SEMANTIC_WITNESSES = {
    "asymmetric_template_orientation": _lawful_input,
    "marker_is_stamp_center": _lawful_input,
    "all_markers_are_transformed": _lawful_input,
    "complete_template_is_copied": _lawful_input,
    "off_canonical_lattice_marker": _witness_off_canonical_lattice,
}
WITNESS_RIVALS = {
    "asymmetric_template_orientation": [
        "rotate_template_90",
        "rotate_template_180",
        "rotate_template_270",
        "flip_template_left_right",
        "flip_template_up_down",
        "transpose_template",
        "anti_transpose_template",
    ],
    "marker_is_stamp_center": ["marker_is_top_left"],
    "all_markers_are_transformed": ["first_marker_only"],
    "complete_template_is_copied": ["center_cell_only"],
    "off_canonical_lattice_marker": ["fixed_canonical_lattice_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared rivals that fit all demonstrations but change the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        return [f"query input is invalid: {query_errors[0]}"]
    query_expected = rule_mirror(query["input"])
    if query["output"] != query_expected:
        reasons.append("query output disagrees with the canonical rule mirror")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the canonical rule mirror")
        for name, rival in SEMANTIC_RIVALS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected

    for name, was_refuted in refuted.items():
        if not was_refuted and SEMANTIC_RIVALS[name](query["input"]) != query_expected:
            reasons.append(
                f"demonstrations do not refute query-changing rival {name}"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-specific near-misses that self_check must reject."""
    valid = generate(
        910_241,
        73,
        difficulty="medium",
        grid_h=9,
        grid_w=13,
        n_dots=5,
        palette_size=4,
    )
    facts = _analyze(valid)["facts"]

    missing_divider = _grid_copy(valid)
    missing_divider[5][3] = 0

    template_hole = _grid_copy(valid)
    template_hole[1][1] = 0

    foreign_body_color = _grid_copy(valid)
    foreign_body_color[5][4] = 7

    out_of_region_marker = _grid_copy(valid)
    old_r, old_c = facts["markers"][0]
    out_of_region_marker[old_r][old_c] = 0
    out_of_region_marker[0][5] = 1

    overlapping_markers = _grid_copy(valid)
    old_r, old_c = facts["markers"][1]
    overlapping_markers[old_r][old_c] = 0
    base_r, base_c = facts["markers"][0]
    candidate = (base_r, base_c + 1)
    if candidate[1] > len(valid[0]) - 2:
        candidate = (base_r + 1, base_c)
    overlapping_markers[candidate[0]][candidate[1]] = 1

    return [
        ("missing_divider_cell", missing_divider),
        ("template_hole", template_hole),
        ("foreign_body_color", foreign_body_color),
        ("marker_without_full_stamp", out_of_region_marker),
        ("overlapping_stamp_centers", overlapping_markers),
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    bounds = _band_bounds(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    has_override = any(value is not None for value in overrides.values())
    teaching_profile = (
        None
        if has_override
        else schedule_profile(seed, sample_index, difficulty=difficulty)
    )
    profile_rng = ctx.draw_rng("canonical_profile")
    canonical_profile = (
        profile_rng.randrange(len(_CANONICAL_PROFILES))
        if teaching_profile == "canonical_profile"
        else None
    )

    if canonical_profile is not None:
        n_profile, palette_profile, marker_profile = _CANONICAL_PROFILES[
            canonical_profile
        ]
        h = ctx.draw_int_strict("grid_h", 9, 9)
        w = ctx.draw_int_strict("grid_w", 13, 13)
        n_dots = ctx.draw_int_strict("n_dots", n_profile, n_profile)
        palette_size = ctx.draw_int_strict(
            "palette_size", palette_profile, palette_profile
        )
        markers = list(marker_profile)
    else:
        h = _draw_banded_int(
            ctx,
            overrides,
            "grid_h",
            bounds["grid_h"],
            (_H_MIN, _H_MAX),
        )
        w = _draw_banded_int(
            ctx,
            overrides,
            "grid_w",
            bounds["grid_w"],
            (_W_MIN, _W_MAX),
        )
        n_dots = _draw_banded_int(
            ctx,
            overrides,
            "n_dots",
            bounds["n_dots"],
            (_N_MIN, _N_MAX),
        )
        palette_size = _draw_banded_int(
            ctx,
            overrides,
            "palette_size",
            bounds["palette_size"],
            (_PALETTE_MIN, _PALETTE_MAX),
        )
        marker_rng = ctx.draw_rng("marker_layout")
        markers = (
            _draw_off_lattice_markers(h, w, n_dots, marker_rng)
            if teaching_profile == "anti_lattice"
            else _draw_markers(h, w, n_dots, marker_rng)
        )

    template = _draw_template(palette_size, ctx.draw_rng("template"))
    grid = full_grid(h, w, 0)
    for r in range(3):
        for c in range(3):
            grid[r][c] = template[r][c]
    for r in range(h):
        grid[r][3] = 5
    for r, c in markers:
        grid[r][c] = 1

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid instance: " + "; ".join(errors))
    return grid
