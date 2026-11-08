"""Generator for the divider-lattice band-count task ``eb3171637821``.

A nonzero DIVIDER color forms full horizontal and vertical runs.  The other
nonzero CELL color fills every rectangular cell band.  The selected Racket rule
counts positive-width/height CELL bands and emits a fresh monochrome rectangle
with one output cell per band intersection.

The curriculum deliberately varies divider-run thickness and permits divider
runs on outer boundaries.  Those branches distinguish counting cell bands from
the tempting shortcut of counting individual full divider lines.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eb3171637821"
TASK_ID = GENERATOR_ID
RULE_HASH = "f7892897a4d5"
VERSION = "3.2.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Two nonzero colors form a Cartesian lattice: a divider color occupies "
    "full row/column runs and a cell color fills every positive-size band. "
    "Count non-divider row bands and column bands, then emit a fresh rectangle "
    "of that size filled with the cell color. Divider runs may be 1-2 cells "
    "thick and may occur on any outer boundary."
)

INVARIANTS = [
    "input is a nonempty rectangular 1..30 grid using exactly two distinct nonzero colors",
    "one divider color forms at least one full row and at least one full column",
    "every cell is divider color iff its row or column belongs to a divider run",
    "there are 2..8 positive cell bands on each axis",
    "all horizontal divider runs share thickness 1 or 2; all vertical runs share thickness 1 or 2",
]

_BOUNDARY_MODES = ("none", "start", "end", "both")
_INT_AXES = {
    "row_bands": (2, 8),
    "col_bands": (2, 8),
    "row_divider_thickness": (1, 2),
    "col_divider_thickness": (1, 2),
}
_STR_AXES = {
    "row_boundary_mode": _BOUNDARY_MODES,
    "col_boundary_mode": _BOUNDARY_MODES,
}

AXES = {
    "row_bands": {
        "type": "int",
        "default": "difficulty-weighted full-domain draw",
        "valid": "2..8",
    },
    "col_bands": {
        "type": "int",
        "default": "difficulty-weighted full-domain draw",
        "valid": "2..8",
    },
    "row_divider_thickness": {
        "type": "int",
        "default": "uniform 1..2",
        "valid": "1..2",
    },
    "col_divider_thickness": {
        "type": "int",
        "default": "uniform 1..2",
        "valid": "1..2",
    },
    "row_boundary_mode": {
        "type": "str",
        "default": "uniform none|start|end|both",
        "valid": "none|start|end|both",
    },
    "col_boundary_mode": {
        "type": "str",
        "default": "uniform none|start|end|both",
        "valid": "none|start|end|both",
    },
}

# Every advertised cross-product is constructive within the ARC 30x30 limit.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_AXES:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            lo, hi = _INT_AXES[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo},{hi}]")
        else:
            if type(value) is not str:
                raise ValueError(f"{name} must be a string, not {type(value).__name__}")
            if value not in _STR_AXES[name]:
                raise ValueError(f"{name}={value!r} not in {_STR_AXES[name]}")


def _weighted_band_options(difficulty):
    full = list(range(2, 9))
    if difficulty == "easy":
        return full + [2, 2, 3, 3, 4] * 3
    if difficulty == "hard":
        return full + [5, 6, 6, 7, 7, 8, 8] * 3
    if difficulty == "medium":
        return full + [3, 4, 4, 5, 5, 6] * 3
    return full


def _draw_axes(ctx, difficulty):
    """Draw the full override domain.

    This path is used whenever the caller supplies an exact override.  Explicit
    controls intentionally reach every lawful lattice, including dense stress
    cases outside the canonical morphology prior.
    """
    return {
        "row_bands": ctx.draw_choice("row_bands", _weighted_band_options(difficulty)),
        "col_bands": ctx.draw_choice("col_bands", _weighted_band_options(difficulty)),
        "row_divider_thickness": ctx.draw_choice("row_divider_thickness", (1, 2)),
        "col_divider_thickness": ctx.draw_choice("col_divider_thickness", (1, 2)),
        "row_boundary_mode": ctx.draw_choice("row_boundary_mode", _BOUNDARY_MODES),
        "col_boundary_mode": ctx.draw_choice("col_boundary_mode", _BOUNDARY_MODES),
    }


def _divider_cells(bands, thickness, boundary_mode):
    return thickness * ((bands - 1) + _boundary_count(boundary_mode))


def _cell_color_is_modal(height, width, axes):
    row_dividers = _divider_cells(
        axes["row_bands"],
        axes["row_divider_thickness"],
        axes["row_boundary_mode"],
    )
    col_dividers = _divider_cells(
        axes["col_bands"],
        axes["col_divider_thickness"],
        axes["col_boundary_mode"],
    )
    cell_area = (height - row_dividers) * (width - col_dividers)
    return cell_area * 2 > height * width


@lru_cache(maxsize=None)
def _default_axis_profiles(difficulty, extent):
    """Profiles whose cell color remains modal at ``extent`` x ``extent``.

    Canonical inputs use the cell color as the modal background and therefore
    expose one connected non-modal divider object.  Dense legal stress cases
    remain reachable through exact overrides, but the production sampler keeps
    this canonical morphology so distribution gates do not reinterpret every
    cell rectangle as a separate object.
    """
    profiles = []
    band_options = _weighted_band_options(difficulty)
    for row_bands, col_bands, row_thickness, col_thickness, row_mode, col_mode in product(
        band_options,
        band_options,
        (1, 2),
        (1, 2),
        _BOUNDARY_MODES,
        _BOUNDARY_MODES,
    ):
        axes = {
            "row_bands": row_bands,
            "col_bands": col_bands,
            "row_divider_thickness": row_thickness,
            "col_divider_thickness": col_thickness,
            "row_boundary_mode": row_mode,
            "col_boundary_mode": col_mode,
        }
        row_minimum = row_bands + _divider_cells(row_bands, row_thickness, row_mode)
        col_minimum = col_bands + _divider_cells(col_bands, col_thickness, col_mode)
        if row_minimum <= extent and col_minimum <= extent and _cell_color_is_modal(
            extent, extent, axes
        ):
            profiles.append(
                (row_bands, col_bands, row_thickness, col_thickness, row_mode, col_mode)
            )
    if not profiles:
        raise ValueError(f"no canonical-morphology profiles fit extent {extent}")
    return tuple(profiles)


def _draw_default_axes(ctx, difficulty, extent):
    profiles = _default_axis_profiles(difficulty, extent)
    # The production lesson sampler uses consecutive sample indices with three
    # demonstrations.  Alternating unit-only and thick-run instances guarantees
    # every such demo window contains a counterexample to line-counting while
    # retaining canonical unit-divider examples in the same lesson.
    if ctx.sample_index % 2 == 0:
        profiles = tuple(profile for profile in profiles if 2 in profile[2:4])
    else:
        profiles = tuple(profile for profile in profiles if profile[2:4] == (1, 1))
    if not profiles:
        raise ValueError(f"no scheduled profiles fit extent {extent}")
    profile = ctx.draw_rng("layout_profile").choice(profiles)
    values = dict(
        zip(
            (
                "row_bands",
                "col_bands",
                "row_divider_thickness",
                "col_divider_thickness",
                "row_boundary_mode",
                "col_boundary_mode",
            ),
            profile,
        )
    )
    # Record the realized values through the public keyed-draw API.  The
    # profile draw itself is internal; each advertised axis remains observable.
    for label, value in values.items():
        ctx.draw_choice(label, (value,))
    return values


def _boundary_count(mode):
    return int(mode in ("start", "both")) + int(mode in ("end", "both"))


def _positive_composition(total, parts, rng):
    """A deterministic random composition of total into ``parts`` positives."""
    if parts < 1 or total < parts:
        raise ValueError(f"cannot compose total={total} into {parts} positive parts")
    if parts == 1:
        return [total]
    cuts = sorted(rng.sample(range(1, total), parts - 1))
    points = [0, *cuts, total]
    return [points[index + 1] - points[index] for index in range(parts)]


def _target_extent(ctx, *, axis, bands, thickness, boundary_mode, difficulty, canonical_scale):
    separators = thickness * ((bands - 1) + _boundary_count(boundary_mode))
    minimum = separators + bands
    if minimum > 30:
        raise ValueError(
            f"{axis} axes require minimum extent {minimum}, exceeding ARC limit 30"
        )
    if canonical_scale:
        return 27
    preferred_hi = {"easy": 18, "medium": 24, "hard": 30}.get(difficulty, 30)
    upper = max(minimum, preferred_hi)
    upper = min(30, upper)
    return ctx.draw_rng(f"{axis}_extent").randint(minimum, upper)


def _axis_mask(band_sizes, divider_thickness, boundary_mode):
    mask = []
    if boundary_mode in ("start", "both"):
        mask.extend([True] * divider_thickness)
    for index, size in enumerate(band_sizes):
        mask.extend([False] * size)
        if index + 1 < len(band_sizes):
            mask.extend([True] * divider_thickness)
    if boundary_mode in ("end", "both"):
        mask.extend([True] * divider_thickness)
    return mask


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Frequent exact 27x27 anchors keep every difficulty band tied to a
    # canonical profile without replaying canonical layouts or palettes.
    canonical_scale = (
        ctx.draw_choice("scale_profile", ("canonical", "canonical", "broad"))
        == "canonical"
    )

    if overrides:
        axes = _draw_axes(ctx, difficulty)
        height = _target_extent(
            ctx,
            axis="row",
            bands=axes["row_bands"],
            thickness=axes["row_divider_thickness"],
            boundary_mode=axes["row_boundary_mode"],
            difficulty=difficulty,
            canonical_scale=canonical_scale,
        )
        width = _target_extent(
            ctx,
            axis="col",
            bands=axes["col_bands"],
            thickness=axes["col_divider_thickness"],
            boundary_mode=axes["col_boundary_mode"],
            difficulty=difficulty,
            canonical_scale=canonical_scale,
        )
    else:
        upper = 27 if canonical_scale else {
            "easy": 18,
            "medium": 24,
            "hard": 30,
        }.get(difficulty, 30)
        axes = _draw_default_axes(ctx, difficulty, upper)
        if canonical_scale:
            height = width = 27
        else:
            row_minimum = axes["row_bands"] + _divider_cells(
                axes["row_bands"],
                axes["row_divider_thickness"],
                axes["row_boundary_mode"],
            )
            col_minimum = axes["col_bands"] + _divider_cells(
                axes["col_bands"],
                axes["col_divider_thickness"],
                axes["col_boundary_mode"],
            )
            extent_pairs = [
                (candidate_h, candidate_w)
                for candidate_h in range(row_minimum, upper + 1)
                for candidate_w in range(col_minimum, upper + 1)
                if _cell_color_is_modal(candidate_h, candidate_w, axes)
            ]
            height, width = ctx.draw_rng("broad_extent").choice(extent_pairs)

    row_separator_cells = axes["row_divider_thickness"] * (
        axes["row_bands"] - 1 + _boundary_count(axes["row_boundary_mode"])
    )
    col_separator_cells = axes["col_divider_thickness"] * (
        axes["col_bands"] - 1 + _boundary_count(axes["col_boundary_mode"])
    )
    row_sizes = _positive_composition(
        height - row_separator_cells,
        axes["row_bands"],
        ctx.draw_rng("row_band_sizes"),
    )
    col_sizes = _positive_composition(
        width - col_separator_cells,
        axes["col_bands"],
        ctx.draw_rng("col_band_sizes"),
    )
    row_divider = _axis_mask(
        row_sizes, axes["row_divider_thickness"], axes["row_boundary_mode"]
    )
    col_divider = _axis_mask(
        col_sizes, axes["col_divider_thickness"], axes["col_boundary_mode"]
    )

    divider_color, cell_color = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    grid = full_grid(height, width, cell_color)
    for row, is_divider_row in enumerate(row_divider):
        for col, is_divider_col in enumerate(col_divider):
            if is_divider_row or is_divider_col:
                grid[row][col] = divider_color
    return grid


def _runs(indexes):
    groups = []
    for index in indexes:
        if not groups or index != groups[-1][-1] + 1:
            groups.append([index])
        else:
            groups[-1].append(index)
    return [tuple(group) for group in groups]


def _nondivider_runs(length, divider_indexes):
    blocked = set(divider_indexes)
    return _runs([index for index in range(length) if index not in blocked])


def _boundary_mode(divider_indexes, length):
    start = 0 in divider_indexes
    end = length - 1 in divider_indexes
    if start and end:
        return "both"
    if start:
        return "start"
    if end:
        return "end"
    return "none"


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["expected a nonempty rectangular grid"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["expected a nonempty rectangular grid"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["expected a nonempty rectangular grid"]}
    height = len(grid)
    if height > 30 or width > 30:
        errors.append(f"grid dimensions {height}x{width} exceed 30x30")
    if any(type(value) is not int or not 1 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer nonzero ARC colors 1..9")
        return {"errors": errors, "height": height, "width": width}

    palette = {value for row in grid for value in row}
    if len(palette) != 2:
        errors.append(f"expected exactly two colors, got {sorted(palette)}")
        return {"errors": errors, "height": height, "width": width, "palette": palette}

    candidates = []
    for color in sorted(palette):
        full_rows = [
            row for row in range(height)
            if all(grid[row][col] == color for col in range(width))
        ]
        full_cols = [
            col for col in range(width)
            if all(grid[row][col] == color for row in range(height))
        ]
        if full_rows and full_cols:
            candidates.append((color, full_rows, full_cols))
    if len(candidates) != 1:
        errors.append(f"expected exactly one divider color with full rows and columns, found {len(candidates)}")
        return {"errors": errors, "height": height, "width": width, "palette": palette}

    divider_color, divider_rows, divider_cols = candidates[0]
    cell_color = next(color for color in palette if color != divider_color)
    for row in range(height):
        for col in range(width):
            expected = divider_color if row in divider_rows or col in divider_cols else cell_color
            if grid[row][col] != expected:
                errors.append(
                    "every cell must equal divider color exactly on full divider rows/columns"
                )
                return {
                    "errors": errors,
                    "height": height,
                    "width": width,
                    "palette": palette,
                }

    row_divider_runs = _runs(divider_rows)
    col_divider_runs = _runs(divider_cols)
    row_band_runs = _nondivider_runs(height, divider_rows)
    col_band_runs = _nondivider_runs(width, divider_cols)
    if not 2 <= len(row_band_runs) <= 8:
        errors.append(f"expected 2..8 row bands, got {len(row_band_runs)}")
    if not 2 <= len(col_band_runs) <= 8:
        errors.append(f"expected 2..8 column bands, got {len(col_band_runs)}")

    row_thicknesses = {len(run) for run in row_divider_runs}
    col_thicknesses = {len(run) for run in col_divider_runs}
    if len(row_thicknesses) != 1 or not row_thicknesses <= {1, 2}:
        errors.append(
            "all horizontal divider runs must share thickness 1 or 2"
        )
    if len(col_thicknesses) != 1 or not col_thicknesses <= {1, 2}:
        errors.append(
            "all vertical divider runs must share thickness 1 or 2"
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "divider_color": divider_color,
        "cell_color": cell_color,
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "row_divider_runs": row_divider_runs,
        "col_divider_runs": col_divider_runs,
        "row_band_runs": row_band_runs,
        "col_band_runs": col_band_runs,
        "row_bands": len(row_band_runs),
        "col_bands": len(col_band_runs),
        "row_divider_thickness": (
            next(iter(row_thicknesses)) if len(row_thicknesses) == 1 else None
        ),
        "col_divider_thickness": (
            next(iter(col_thicknesses)) if len(col_thicknesses) == 1 else None
        ),
        "row_boundary_mode": _boundary_mode(divider_rows, height),
        "col_boundary_mode": _boundary_mode(divider_cols, width),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the exact two-color Cartesian divider-lattice grammar."""
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    return {axis: info[axis] for axis in AXES}


def _intended_output(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot solve malformed grid: " + "; ".join(info["errors"]))
    return full_grid(info["row_bands"], info["col_bands"], info["cell_color"])


def _count_individual_divider_lines(grid):
    """Rival: each full line is a separator; correct only for unit-thick runs."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot solve malformed grid: " + "; ".join(info["errors"]))
    row_edges = int(0 in info["divider_rows"]) + int(
        info["height"] - 1 in info["divider_rows"]
    )
    col_edges = int(0 in info["divider_cols"]) + int(
        info["width"] - 1 in info["divider_cols"]
    )
    rows = len(info["divider_rows"]) + 1 - row_edges
    cols = len(info["divider_cols"]) + 1 - col_edges
    return full_grid(rows, cols, info["cell_color"])


def _has_thick_divider_run(grid):
    info = _analysis(grid)
    return not info["errors"] and (
        info["row_divider_thickness"] == 2
        or info["col_divider_thickness"] == 2
    )


SEMANTIC_WITNESSES = {"thick_divider_run": _has_thick_divider_run}
SEMANTIC_RIVALS = {
    "count_individual_divider_lines": _count_individual_divider_lines,
}
WITNESS_RIVALS = {
    "thick_divider_run": ["count_individual_divider_lines"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
