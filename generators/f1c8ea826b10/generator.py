"""Generator for bank task H99 / f1c8ea826b10.

Color-5 wall rows and columns partition the grid into chambers, which may also
contain a small number of isolated color-5 blockers. Each connected non-wall
region contains one to three distinct marker colors. A singleton color fills
its region solid; otherwise the smallest and largest marker colors fill an
alternating checkerboard anchored at the region's bounding-box top-left.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f1c8ea826b10"
VERSION = "3.0.0"
TASK_ID = "f1c8ea826b10"
RULE_HASH = "b59c7b8974ab"

SUMMARY = (
    "Build a sealed color-5 wall lattice with two to four chamber rows and "
    "columns plus optional isolated wall blockers. Each connected chamber "
    "region has one, two, or on harder generalized lessons three distinct "
    "markers. A singleton fills solid; multiple colors fill a bbox-anchored "
    "checkerboard using only the numeric minimum and maximum."
)

INVARIANTS = [
    "zero is background and five is the wall color",
    "full color-5 boundary and separator lines form macro-chambers",
    "a macro-chamber has at most one blocker and one connected non-wall region",
    "there are two through four chamber rows and columns",
    "chamber heights are one through six and widths are two through six",
    "each chamber has one through three distinct single-cell markers",
    "at least one chamber exercises the multi-color checkerboard branch",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_LATTICE_COUNTS = (2, 3, 4)
_PROFILE_PRIOR = 0.28
_BAND_LATTICE = {
    "easy": (2,),
    "medium": (2, 3),
    "hard": (3, 4),
}
_BAND_HEIGHT = {
    "easy": (1, 3),
    "medium": (1, 5),
    "hard": (2, 6),
}
_BAND_WIDTH = {
    "easy": (3, 4),
    "medium": (3, 6),
    "hard": (3, 6),
}

AXES = {
    "lattice_rows": {
        "type": "int",
        "default": "difficulty-aware choice",
        "valid": "2|3|4",
    },
    "lattice_cols": {
        "type": "int",
        "default": "difficulty-aware choice",
        "valid": "2|3|4",
    },
}

# Every public input. Profile matching normalizes each chamber's concrete
# marker values to local numeric ranks while retaining the complete wall
# geometry and marker-role positions.
_PROFILE_GRIDS = (
    (
        "5555555555",
        "5200050305",
        "5070050065",
        "5555555555",
        "5000050005",
        "5040050105",
        "5008050095",
        "5555555555",
    ),
    (
        "55555555555",
        "52050405065",
        "50550905085",
        "50050005005",
        "55555555555",
        "50050005005",
        "57050205015",
        "50350805045",
        "55555555555",
    ),
    (
        "5555555555",
        "5200050305",
        "5090050405",
        "5555555555",
        "5040050605",
        "5007050015",
        "5555555555",
        "5008050505",
        "5070050205",
        "5555555555",
    ),
    (
        "5555555555555",
        "5200504005065",
        "5030508005705",
        "5555555555555",
        "5900500005405",
        "5030507205085",
        "5555555555555",
    ),
    (
        "5555555555555",
        "5240503950455",
        "5555555555555",
        "5060507050805",
        "5010508050205",
        "5555555555555",
        "5000500050005",
        "5093502750365",
        "5555555555555",
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if value not in _LATTICE_COUNTS:
            raise ValueError(f"{label} must be 2, 3, or 4")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _scene_analysis(grid):
    if not isinstance(grid, list) and not isinstance(grid, tuple):
        return None, None, ["grid must be a list or tuple of rows"]
    if not grid:
        return None, None, ["grid must be non-empty"]
    if not all(isinstance(row, (list, tuple, str)) and row for row in grid):
        return None, None, [
            "grid rows must be non-empty lists, tuples, or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]

    height = len(coerced)
    errors = []
    if not 4 <= height <= 30:
        errors.append("grid height must be between 4 and 30")
    if not 7 <= width <= 30:
        errors.append("grid width must be between 7 and 30")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return coerced, None, errors
    if errors:
        return coerced, None, errors

    wall_rows = tuple(
        row
        for row, values in enumerate(coerced)
        if all(value == 5 for value in values)
    )
    wall_cols = tuple(
        col
        for col in range(width)
        if all(coerced[row][col] == 5 for row in range(height))
    )
    if (
        not 3 <= len(wall_rows) <= 5
        or wall_rows[0] != 0
        or wall_rows[-1] != height - 1
    ):
        errors.append(
            "full wall rows must bound two through four chamber rows"
        )
    if (
        not 3 <= len(wall_cols) <= 5
        or wall_cols[0] != 0
        or wall_cols[-1] != width - 1
    ):
        errors.append(
            "full wall columns must bound two through four chamber columns"
        )
    if errors:
        return coerced, None, errors

    if any(
        coerced[row][col] != 5
        for row in range(height)
        for col in range(width)
        if row in wall_rows or col in wall_cols
    ):
        errors.append(
            "every boundary and separator cell must be color 5"
        )

    row_heights = tuple(
        bottom - top - 1
        for top, bottom in zip(wall_rows, wall_rows[1:])
    )
    col_widths = tuple(
        right - left - 1
        for left, right in zip(wall_cols, wall_cols[1:])
    )
    if any(not 1 <= value <= 6 for value in row_heights):
        errors.append("chamber heights must be between 1 and 6")
    if any(not 2 <= value <= 6 for value in col_widths):
        errors.append("chamber widths must be between 2 and 6")
    if errors:
        return coerced, None, errors

    chambers = []
    checker_chambers = 0
    for chamber_row, (top, bottom) in enumerate(
        zip(wall_rows, wall_rows[1:])
    ):
        for chamber_col, (left, right) in enumerate(
            zip(wall_cols, wall_cols[1:])
        ):
            blockers = tuple(
                (
                    row - top - 1,
                    col - left - 1,
                )
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
                if coerced[row][col] == 5
            )
            if len(blockers) > 1:
                errors.append(
                    "a chamber may contain at most one wall blocker"
                )
            region_cells = {
                (row, col)
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
                if coerced[row][col] != 5
            }
            if not region_cells:
                errors.append("a chamber must retain a non-wall region")
                continue
            reached = set()
            pending = [next(iter(region_cells))]
            while pending:
                row, col = pending.pop()
                if (row, col) in reached:
                    continue
                reached.add((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = row + dr, col + dc
                    if neighbor in region_cells and neighbor not in reached:
                        pending.append(neighbor)
            if reached != region_cells:
                errors.append(
                    "blockers must leave one connected non-wall region"
                )

            markers = tuple(
                (
                    row - top - 1,
                    col - left - 1,
                    coerced[row][col],
                )
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
                if coerced[row][col] not in (0, 5)
            )
            colors = tuple(sorted({value for _r, _c, value in markers}))
            if not 1 <= len(colors) <= 3:
                errors.append(
                    "each chamber must contain one through three colors"
                )
            if len(markers) != len(colors):
                errors.append(
                    "each chamber color must appear as exactly one marker"
                )
            if len(markers) >= len(region_cells):
                errors.append(
                    "each chamber must retain at least one background cell"
                )
            if any(value in (0, 5) for value in colors):
                errors.append("markers must be nonzero and non-wall colors")
            checker_chambers += len(colors) >= 2
            bbox_top = min(row for row, _col in region_cells)
            bbox_left = min(col for _row, col in region_cells)
            chambers.append({
                "chamber_row": chamber_row,
                "chamber_col": chamber_col,
                "top": top + 1,
                "left": left + 1,
                "height": bottom - top - 1,
                "width": right - left - 1,
                "blockers": blockers,
                "region_cells": tuple(sorted(region_cells)),
                "bbox_top": bbox_top,
                "bbox_left": bbox_left,
                "markers": markers,
                "colors": colors,
            })
    if checker_chambers == 0:
        errors.append(
            "at least one chamber must exercise the checkerboard branch"
        )
    if errors:
        return coerced, None, errors

    arities = tuple(len(chamber["colors"]) for chamber in chambers)
    return coerced, {
        "height": height,
        "width": width,
        "wall_rows": wall_rows,
        "wall_cols": wall_cols,
        "row_heights": row_heights,
        "col_widths": col_widths,
        "lattice_rows": len(row_heights),
        "lattice_cols": len(col_widths),
        "chambers": tuple(chambers),
        "arities": arities,
        "solid_chambers": sum(arity == 1 for arity in arities),
        "checker_chambers": sum(arity >= 2 for arity in arities),
        "middle_decoy_chambers": sum(arity == 3 for arity in arities),
        "blocked_chambers": sum(
            bool(chamber["blockers"]) for chamber in chambers
        ),
        "blocker_cells": sum(
            len(chamber["blockers"]) for chamber in chambers
        ),
    }, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "lattice_rows": features["lattice_rows"],
        "lattice_cols": features["lattice_cols"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = [row[:] for row in coerced]
    for chamber in features["chambers"]:
        colors = chamber["colors"]
        for row, col in chamber["region_cells"]:
            if len(colors) == 1:
                value = colors[0]
            else:
                value = (
                    colors[0]
                    if (
                        row - chamber["bbox_top"]
                        + col - chamber["bbox_left"]
                    ) % 2 == 0
                    else colors[-1]
                )
            output[row][col] = value
    return output


def _profile_feature(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    chamber_signatures = []
    for chamber in features["chambers"]:
        rank = {
            color: index
            for index, color in enumerate(chamber["colors"])
        }
        chamber_signatures.append((
            chamber["height"],
            chamber["width"],
            chamber["blockers"],
            tuple(
                (row, col, rank[value])
                for row, col, value in chamber["markers"]
            ),
        ))
    return (
        features["height"],
        features["width"],
        features["wall_rows"],
        features["wall_cols"],
        tuple(chamber_signatures),
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_feature(grid) for grid in _PROFILE_GRIDS
)


def canonical_profile_signature(grid):
    signature = _profile_feature(grid)
    return (
        signature
        if signature in _CANONICAL_PROFILE_SIGNATURES
        else None
    )


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def _build_lattice(row_heights, col_widths):
    height = sum(row_heights) + len(row_heights) + 1
    width = sum(col_widths) + len(col_widths) + 1
    grid = full_grid(height, width, 5)
    tops = []
    start = 1
    for chamber_height in row_heights:
        tops.append(start)
        start += chamber_height + 1
    lefts = []
    start = 1
    for chamber_width in col_widths:
        lefts.append(start)
        start += chamber_width + 1
    for chamber_row, top in enumerate(tops):
        for chamber_col, left in enumerate(lefts):
            for row in range(row_heights[chamber_row]):
                for col in range(col_widths[chamber_col]):
                    grid[top + row][left + col] = 0
    return grid, tuple(tops), tuple(lefts)


def _draw_profile(source, rng):
    source_grid, features, errors = _scene_analysis(source)
    if errors:
        raise AssertionError("invalid embedded profile: " + "; ".join(errors))
    grid, _tops, _lefts = _build_lattice(
        features["row_heights"],
        features["col_widths"],
    )
    for chamber in features["chambers"]:
        replacement = tuple(
            sorted(rng.sample(_COLORS, len(chamber["colors"])))
        )
        mapping = dict(zip(chamber["colors"], replacement))
        for local_row, local_col in chamber["blockers"]:
            grid[
                chamber["top"] + local_row
            ][chamber["left"] + local_col] = 5
        for local_row, local_col, value in chamber["markers"]:
            grid[
                chamber["top"] + local_row
            ][chamber["left"] + local_col] = mapping[value]
    if canonical_profile_signature(grid) is None:
        raise AssertionError("constructed public profile drifted")
    return grid


def _varied_sizes(rng, count, bounds):
    low, high = bounds
    sizes = [rng.randint(low, high) for _ in range(count)]
    if (
        count > 1
        and low < high
        and len(set(sizes)) == 1
        and rng.random() < 0.75
    ):
        sizes[-1] = low if sizes[-1] != low else high
    return tuple(sizes)


def _sample_arity(rng, band, area):
    draw = rng.random()
    if band == "easy":
        arity = 1 if draw < 0.30 else 2
    elif band == "medium":
        arity = 1 if draw < 0.25 else 2 if draw < 0.90 else 3
    else:
        arity = 1 if draw < 0.20 else 2 if draw < 0.75 else 3
    return min(arity, area - 1)


def _draw_general(ctx, band, overrides):
    row_options = (
        _LATTICE_COUNTS
        if overrides.get("lattice_rows") is not None
        else _BAND_LATTICE[band]
    )
    col_options = (
        _LATTICE_COUNTS
        if overrides.get("lattice_cols") is not None
        else _BAND_LATTICE[band]
    )
    lattice_rows = ctx.draw_choice("lattice_rows", row_options)
    lattice_cols = ctx.draw_choice("lattice_cols", col_options)
    rng = ctx.draw_rng("layout")
    row_heights = _varied_sizes(
        rng,
        lattice_rows,
        _BAND_HEIGHT[band],
    )
    col_widths = _varied_sizes(
        rng,
        lattice_cols,
        _BAND_WIDTH[band],
    )
    grid, tops, lefts = _build_lattice(row_heights, col_widths)

    chambers = [
        (chamber_row, chamber_col)
        for chamber_row in range(lattice_rows)
        for chamber_col in range(lattice_cols)
    ]
    order = chambers[:]
    rng.shuffle(order)
    arities = {}
    for chamber_row, chamber_col in chambers:
        area = (
            row_heights[chamber_row] * col_widths[chamber_col]
        )
        arities[(chamber_row, chamber_col)] = _sample_arity(
            rng,
            band,
            area,
        )

    # General lessons always witness both demonstrated branches. Hard lessons
    # also force the rule's explicit 2+-color min/max decoy behavior.
    arities[order[0]] = 1
    arities[order[1]] = 2
    if band == "hard" and len(order) >= 3:
        arities[order[2]] = 3

    blockers = {}
    for chamber_row, chamber_col in chambers:
        blockers[(chamber_row, chamber_col)] = (
            1
            if rng.random() < (
                0.08 if band == "easy" else 0.18 if band == "medium" else 0.28
            )
            else 0
        )
    if band in ("medium", "hard"):
        blockers[order[-1]] = 1
    for chamber_row, chamber_col in chambers:
        chamber_height = row_heights[chamber_row]
        chamber_width = col_widths[chamber_col]
        cells = [
            (
                tops[chamber_row] + local_row,
                lefts[chamber_col] + local_col,
            )
            for local_row in range(chamber_height)
            for local_col in range(chamber_width)
        ]
        blocker_count = min(
            blockers[(chamber_row, chamber_col)],
            max(0, len(cells) - 4),
        )
        if chamber_height == 1:
            blocker_count = 0
        blocker_cells = []
        if blocker_count:
            local_candidates = [
                (local_row, local_col)
                for local_row in range(chamber_height)
                for local_col in range(chamber_width)
                if not (
                    chamber_height == 1
                    and local_col == 0
                )
            ]
            # Prefer right/bottom edge blockers. They preserve the bbox anchor
            # and cannot split a rectangular non-wall region.
            local_candidates.sort(
                key=lambda cell: (
                    cell[1] != chamber_width - 1,
                    cell[0] != chamber_height - 1,
                    rng.random(),
                )
            )
            for local_row, local_col in local_candidates[:blocker_count]:
                cell = (
                    tops[chamber_row] + local_row,
                    lefts[chamber_col] + local_col,
                )
                grid[cell[0]][cell[1]] = 5
                blocker_cells.append(cell)
        available_cells = [
            cell for cell in cells if cell not in blocker_cells
        ]
        arity = min(
            arities[(chamber_row, chamber_col)],
            len(available_cells) - 1,
        )
        colors = rng.sample(_COLORS, arity)
        for (row, col), color in zip(
            rng.sample(available_cells, arity),
            colors,
        ):
            grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_GRIDS))),
            )

    if profile_index is not None:
        grid = _draw_profile(
            _PROFILE_GRIDS[profile_index],
            ctx.draw_rng("profile_layout"),
        )
        _coerced, features, errors = _scene_analysis(grid)
        if errors:
            raise AssertionError(
                "generated invalid profile: " + "; ".join(errors)
            )
        ctx.draw_choice(
            "lattice_rows",
            (features["lattice_rows"],),
        )
        ctx.draw_choice(
            "lattice_cols",
            (features["lattice_cols"],),
        )
    else:
        grid = _draw_general(ctx, band, overrides)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
