"""Generator for ARC task c4d1a9ae — cyclic hole filling across 3 column regions.

The modal color is the background. Exactly two full-background columns split
three vertical regions. Each region contains one distinct non-background color
plus background holes. The output keeps all existing cells and separator
columns unchanged, while filling each region's holes with the NEXT region's
color, cyclically from right back to left.

The teaching distribution intentionally varies the background color, region
widths, region colors, and independent hole masks. Most ordinary draws use
asymmetric region widths so fixed-position / equal-width shortcuts cannot fit
all generated lessons. Sparse scheduled profiles retain exact canonical-like
morphologies, including one equal-width input, while neighboring lesson items
remain asymmetric.
Both numeric color-cycle orientations are sampled: any three consecutive
indices include both, so neither numeric successor nor numeric predecessor
can explain a complete ordinary lesson. This guarantee assumes no sampler
rejections; the production lesson census checks the actual accepted pairs.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "19e04051ad0d"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "3448ae999e2e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Infer the modal background color and the three vertical column-regions "
    "separated by two full-background columns. Each region contains one "
    "distinct foreground color and background holes. Fill only those holes "
    "with the NEXT region's color in a cyclic left-to-right rotation; preserve "
    "all original foreground cells and the separator columns."
)

INVARIANTS = [
    "the background is the unique modal color (not fixed to color 0)",
    "exactly two full-background columns separate exactly three nonempty regions",
    "each region contains exactly one foreground color and the three colors are distinct",
    "every region contains visible background holes and visible foreground cells",
    "separator columns remain background in the output",
    "region 0 holes use region 1's color, region 1 holes use region 2's color, and region 2 holes use region 0's color",
]

# Width strings are directly recoverable from the returned grid.  Most are
# canonical-width (sum=6 -> overall width 8); a few widen/narrow the canvas.
LAYOUTS = (
    "222",  # canonical equal-width case; overrideable and sparsely scheduled
    "312",  # canonical asymmetric case
    "321",
    "231",
    "213",
    "132",
    "123",
    "411",
    "141",
    "114",
    "223",  # width 9
    "232",  # width 9
    "122",  # width 7
    "212",  # width 7
)
ORDINARY_LAYOUTS = tuple(layout for layout in LAYOUTS if layout != "222")

# Binary foreground masks copied from two distinct canonical morphologies.
# They are palette-neutral: 1 means the region's foreground color, 0 means
# background.  The 222 profile matches the canonical all-nonzero topology;
# the 312 profile matches the canonical background-zero topology.
_CANONICAL_MASKS_222 = (
    ("01", "10", "01", "10", "01", "10", "01", "10", "01", "10"),
    ("01", "01", "01", "10", "10", "10", "10", "01", "01", "01"),
    ("11", "01", "11", "01", "11", "01", "11", "01", "11", "01"),
)
_CANONICAL_MASKS_BG0_312 = (
    ("000", "100", "010", "001", "010", "100", "010", "001", "010", "100"),
    ("0", "1", "0", "1", "0", "1", "0", "1", "0", "1"),
    ("01", "10", "01", "01", "10", "01", "01", "10", "01", "01"),
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed choice in 8..12, strongly anchored at 10",
        "valid": "8..12",
    },
    "layout": {
        "type": "str",
        "default": "asymmetric region-width profile",
        "valid": "|".join(LAYOUTS),
    },
    "bg_color": {
        "type": "color",
        "default": "keyed draw in 0..9",
        "valid": "0..9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_request(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    for name, value in overrides.items():
        if value is None:
            continue
        expected = str if name == "layout" else int
        if type(value) is not expected:
            type_name = "a string" if expected is str else "an integer (not bool)"
            raise TypeError(f"{name} must be {type_name}")


def _height_options(difficulty: str | None) -> list[int]:
    # All valid boundary values remain legal in every band. Duplicates only
    # skew ordinary draws and make canonical height 10 common in every band.
    if difficulty == "easy":
        return [8, 9, 10, 10, 10, 10, 10, 10, 11, 12]
    if difficulty == "hard":
        return [8, 9, 10, 10, 10, 10, 10, 11, 11, 12, 12]
    return [8, 9, 10, 10, 10, 10, 10, 11, 12]


def _layout_options(difficulty: str | None) -> list[str]:
    # Ordinary generation excludes the equal-width 222 shortcut.  The exact
    # override path passes the complete declared domain to draw_choice.
    core = list(ORDINARY_LAYOUTS)
    canonical_width = [x for x in ORDINARY_LAYOUTS if sum(map(int, x)) == 6]
    if difficulty == "easy":
        return canonical_width * 3 + core
    if difficulty == "hard":
        return core + list(ORDINARY_LAYOUTS[-4:]) * 2 + canonical_width
    return canonical_width * 2 + core


def _parse_layout(layout: str) -> tuple[int, int, int]:
    if layout not in LAYOUTS:
        raise ValueError(f"unsupported layout {layout!r}")
    widths = tuple(int(ch) for ch in layout)
    if len(widths) != 3 or any(width < 1 for width in widths):
        raise ValueError(f"malformed layout {layout!r}")
    return widths  # type: ignore[return-value]


def _background_color(grid: Sequence[Sequence[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    if not counts:
        raise ValueError("empty grid has no background")
    ranked = counts.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError("background is not uniquely modal")
    return ranked[0][0]


def _separator_columns(grid: Sequence[Sequence[int]], bg: int) -> list[int]:
    h = len(grid)
    w = len(grid[0])
    return [c for c in range(w) if all(grid[r][c] == bg for r in range(h))]


def _regions_from_separators(width: int, separators: Sequence[int]) -> list[list[int]]:
    sep = set(separators)
    regions: list[list[int]] = []
    current: list[int] = []
    for c in range(width):
        if c in sep:
            if current:
                regions.append(current)
                current = []
        else:
            current.append(c)
    if current:
        regions.append(current)
    return regions


def _analyze(grid: Sequence[Sequence[int]]) -> tuple[int, list[int], list[list[int]], list[int]]:
    bg = _background_color(grid)
    separators = _separator_columns(grid, bg)
    regions = _regions_from_separators(len(grid[0]), separators)
    region_colors: list[int] = []
    for region in regions:
        colors = {
            grid[r][c]
            for r in range(len(grid))
            for c in region
            if grid[r][c] != bg
        }
        if len(colors) != 1:
            raise ValueError(f"region has {len(colors)} foreground colors")
        region_colors.append(next(iter(colors)))
    return bg, separators, regions, region_colors


def _hole_fractions(difficulty: str | None) -> list[float]:
    if difficulty == "easy":
        return [0.28, 0.36, 0.44]
    if difficulty == "hard":
        return [0.44, 0.54, 0.64]
    return [0.34, 0.44, 0.54]


def _place_region(
    grid: list[list[int]],
    *,
    columns: list[int],
    color: int,
    hole_fraction: float,
    rng,
    connected: bool = False,
) -> None:
    h = len(grid)
    cells = [(r, c) for c in columns for r in range(h)]
    target_holes = round(len(cells) * hole_fraction)
    target_holes = max(2, min(target_holes, len(cells) - len(columns) - 1))

    if connected:
        # Canonical examples include profiles with no persistent singleton
        # foreground objects.  Start with one horizontal bridge through every
        # region column, then grow a keyed-random 4-connected support until the
        # ordinary hole-count target is reached.
        target_solids = len(cells) - target_holes
        anchor_row = rng.randrange(h)
        solids = {(anchor_row, c) for c in columns}
        allowed = set(cells)
        while len(solids) < target_solids:
            frontier = sorted(
                {
                    neighbor
                    for r, c in solids
                    for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                    if neighbor in allowed and neighbor not in solids
                }
            )
            if not frontier:
                raise RuntimeError("connected region growth exhausted its frontier")
            solids.add(frontier[rng.randrange(len(frontier))])
        for r, c in solids:
            grid[r][c] = color
        return

    # Reserve one solid cell in every column, preventing an accidental extra
    # all-background separator column from appearing inside a region.
    reserved = {(rng.randrange(h), c) for c in columns}
    hole_candidates = [cell for cell in cells if cell not in reserved]
    holes = set(rng.sample(hole_candidates, target_holes))

    for r, c in cells:
        if (r, c) not in holes:
            grid[r][c] = color


def _place_canonical_morphology(
    grid: list[list[int]],
    *,
    starts: Sequence[int],
    widths: Sequence[int],
    colors: Sequence[int],
    bg: int,
) -> None:
    """Place one palette-neutral canonical morphology into the blank grid."""
    if len(grid) != 10:
        raise ValueError("canonical morphology requires height 10")

    if bg == 0:
        masks = _CANONICAL_MASKS_BG0_312
        expected_widths = (3, 1, 2)
        mask_order = (0, 1, 2)
    else:
        masks = _CANONICAL_MASKS_222
        expected_widths = (2, 2, 2)
        # When zero is a foreground color, generation rotates it into region
        # zero.  This canonical mask permutation retains the measured
        # 21-object topology while preserving the spatial color-cycle rule.
        mask_order = (2, 0, 1) if 0 in colors else (0, 1, 2)

    if tuple(widths) != expected_widths:
        raise ValueError(
            f"canonical morphology expected widths {expected_widths}, got {tuple(widths)}"
        )

    for physical_region, (start, width, color) in enumerate(
        zip(starts, widths, colors)
    ):
        rows = masks[mask_order[physical_region]]
        if any(len(row) != width for row in rows):
            raise RuntimeError("canonical morphology mask width mismatch")
        for r, row in enumerate(rows):
            for offset, marker in enumerate(row):
                if marker == "1":
                    grid[r][start + offset] = color


SCHEDULE_PROFILES = ("ascending", "descending")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Observable color-cycle orientation, period two in sample_index only.

    Seed is deliberately not added to sample_index: callers often advance
    both together, which would collapse a seed+index parity schedule.
    """
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


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

    canonical_morphology = (
        sample_index % 8 == 7
        and overrides.get("grid_h") is None
        and overrides.get("layout") is None
    )
    height_domain = [10] if canonical_morphology else _height_options(difficulty)
    h = ctx.draw_choice("grid_h", height_domain)
    bg = ctx.draw_color_strict("bg_color")
    if overrides.get("layout") is not None:
        layout_domain = list(LAYOUTS)
    elif canonical_morphology:
        layout_domain = ["312" if bg == 0 else "222"]
    else:
        layout_domain = _layout_options(difficulty)
    layout = ctx.draw_choice("layout", layout_domain)
    widths = _parse_layout(layout)

    # With three distinct colors there are only two cycle orientations.
    # Excluding ascending cycles makes numeric PREDECESSOR correct everywhere
    # (including all canonical pairs). Balance both orientations across each
    # consecutive lesson instead. The three rotations remain keyed random
    # nuisance variation; collectively all six color orders have support.
    raw_colors = sorted(ctx.draw_distinct_colors("region_colors", n=3, exclude={bg}))
    color_order_rng = ctx.draw_rng("region_color_order")
    if schedule_profile(seed, sample_index, difficulty=difficulty) == "descending":
        raw_colors = [raw_colors[0], raw_colors[2], raw_colors[1]]
    rotation = color_order_rng.randrange(3)
    colors = raw_colors[rotation:] + raw_colors[:rotation]
    if canonical_morphology and bg != 0 and 0 in colors:
        zero_index = colors.index(0)
        colors = colors[zero_index:] + colors[:zero_index]

    w = sum(widths) + 2
    grid = full_grid(h, w, bg)
    starts = [0, widths[0] + 1, widths[0] + widths[1] + 2]

    if canonical_morphology:
        _place_canonical_morphology(
            grid,
            starts=starts,
            widths=widths,
            colors=colors,
            bg=bg,
        )
    else:
        fractions = _hole_fractions(difficulty)
        rotate = (seed + sample_index) % 3
        fractions = fractions[rotate:] + fractions[:rotate]
        connected_profile = sample_index % 6 == 0
        for index, (start, width, color, fraction) in enumerate(
            zip(starts, widths, colors, fractions)
        ):
            columns = list(range(start, start + width))
            _place_region(
                grid,
                columns=columns,
                color=color,
                hole_fraction=fraction,
                rng=ctx.draw_rng(f"holes_{index}"),
                connected=connected_profile,
            )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid cyclic-region scene: " + "; ".join(errors))

    observed = observe_overrides(grid)
    expected = {"grid_h": h, "layout": layout, "bg_color": bg}
    if observed != expected:
        raise RuntimeError(f"axis observation mismatch: expected {expected}, got {observed}")
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar shared by canonical inputs and generated lessons."""
    errors = _shape_errors(grid)
    if errors:
        return errors

    h, w = len(grid), len(grid[0])
    if not 8 <= h <= 12:
        errors.append(f"height must be in 8..12, got {h}")
    if not 7 <= w <= 9:
        errors.append(f"width must be in 7..9, got {w}")

    try:
        bg = _background_color(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    separators = _separator_columns(grid, bg)
    if len(separators) != 2:
        errors.append(f"expected exactly 2 full-background separator columns, got {len(separators)}")
        return errors

    regions = _regions_from_separators(w, separators)
    if len(regions) != 3 or any(not region for region in regions):
        errors.append(f"expected exactly 3 nonempty regions, got {len(regions)}")
        return errors

    layout = "".join(str(len(region)) for region in regions)
    if layout not in LAYOUTS:
        errors.append(f"region-width layout {layout!r} is outside the teaching grammar")

    region_colors: list[int] = []
    for index, region in enumerate(regions):
        values = [grid[r][c] for r in range(h) for c in region]
        foreground = {value for value in values if value != bg}
        if len(foreground) != 1:
            errors.append(
                f"region {index} must contain exactly 1 foreground color, got {sorted(foreground)}"
            )
            continue
        region_colors.append(next(iter(foreground)))
        holes = sum(value == bg for value in values)
        solids = len(values) - holes
        if holes < 1:
            errors.append(f"region {index} has no background hole to transform")
        if solids < 2:
            errors.append(f"region {index} has too little foreground support ({solids} cells)")

    if len(region_colors) == 3 and len(set(region_colors)) != 3:
        errors.append("the three regions must use distinct foreground colors")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked semantic manifold for cyclic three-region hole filling."""
    errors = self_check(grid)
    if errors:
        return errors
    bg, _, regions, _ = _analyze(grid)
    for index, region in enumerate(regions):
        values = [grid[r][c] for r in range(len(grid)) for c in region]
        holes = sum(value == bg for value in values)
        solids = len(values) - holes
        if holes < 2:
            errors.append(f"region {index} needs at least two visible holes")
        if solids < 2:
            errors.append(f"region {index} needs at least two visible foreground cells")
    return errors


def observe_overrides(grid: Any) -> dict[str, int | str]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    bg, separators, regions, _ = _analyze(grid)
    if len(separators) != 2 or len(regions) != 3:
        raise ValueError("cannot observe layout outside the three-region grammar")
    return {
        "grid_h": len(grid),
        "layout": "".join(str(len(region)) for region in regions),
        "bg_color": bg,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains the output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("rule_mirror expects a lawful grid: " + "; ".join(errors))
    bg, _, regions, colors = _analyze(grid)
    out = [row[:] for row in grid]
    for index, region in enumerate(regions):
        replacement = colors[(index + 1) % 3]
        for r in range(len(grid)):
            for c in region:
                if grid[r][c] == bg:
                    out[r][c] = replacement
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _fill_with_own_region_color(grid):
    bg, _, regions, colors = _analyze(grid)
    out = [row[:] for row in grid]
    for region, color in zip(regions, colors):
        for r in range(len(grid)):
            for c in region:
                if grid[r][c] == bg:
                    out[r][c] = color
    return out


def _fill_with_previous_region_color(grid):
    bg, _, regions, colors = _analyze(grid)
    out = [row[:] for row in grid]
    for index, region in enumerate(regions):
        replacement = colors[(index - 1) % 3]
        for r in range(len(grid)):
            for c in region:
                if grid[r][c] == bg:
                    out[r][c] = replacement
    return out


def _fill_all_holes_with_middle_color(grid):
    bg, _, regions, colors = _analyze(grid)
    out = [row[:] for row in grid]
    replacement = colors[1]
    for region in regions:
        for r in range(len(grid)):
            for c in region:
                if grid[r][c] == bg:
                    out[r][c] = replacement
    return out


def _fill_separator_columns_too(grid):
    bg, separators, _, colors = _analyze(grid)
    out = rule_mirror(grid)
    for index, c in enumerate(separators):
        replacement = colors[(index + 1) % 3]
        for r in range(len(grid)):
            if grid[r][c] == bg:
                out[r][c] = replacement
    return out


def _numeric_color_cycle(grid):
    bg, _, regions, colors = _analyze(grid)
    ordered = sorted(colors)
    successor = {color: ordered[(i + 1) % 3] for i, color in enumerate(ordered)}
    out = [row[:] for row in grid]
    for region, color in zip(regions, colors):
        replacement = successor[color]
        for r in range(len(grid)):
            for c in region:
                if grid[r][c] == bg:
                    out[r][c] = replacement
    return out


def _reverse_numeric_color_cycle(grid):
    """Canonical-fitting rival: numeric predecessor instead of spatial next."""
    bg, _, regions, colors = _analyze(grid)
    ordered = sorted(colors)
    predecessor = {color: ordered[(i - 1) % 3] for i, color in enumerate(ordered)}
    out = [row[:] for row in grid]
    for region, color in zip(regions, colors):
        for r in range(len(grid)):
            for c in region:
                if grid[r][c] == bg:
                    out[r][c] = predecessor[color]
    return out


def _fixed_equal_width_boundaries(grid):
    # Plausible shortcut from the two canonical 2/2/2-looking examples:
    # assume width 8 and fixed separators at columns 2 and 5.  If those
    # assumptions fail structurally, this shortcut degenerates to identity.
    if len(grid[0]) != 8:
        return _identity(grid)
    try:
        bg = _background_color(grid)
        assumed_regions = [[0, 1], [3, 4], [6, 7]]
        colors = []
        for region in assumed_regions:
            found = {
                grid[r][c]
                for r in range(len(grid))
                for c in region
                if grid[r][c] != bg
            }
            if len(found) != 1:
                return _identity(grid)
            colors.append(next(iter(found)))
        out = [row[:] for row in grid]
        for i, region in enumerate(assumed_regions):
            replacement = colors[(i + 1) % 3]
            for r in range(len(grid)):
                for c in region:
                    if grid[r][c] == bg:
                        out[r][c] = replacement
        return out
    except Exception:
        return _identity(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "fill_holes_with_own_region_color": _fill_with_own_region_color,
    "fill_holes_with_previous_region_color": _fill_with_previous_region_color,
    "fill_all_holes_with_middle_region_color": _fill_all_holes_with_middle_color,
    "also_fill_separator_columns": _fill_separator_columns_too,
    "cycle_by_numeric_color_order": _numeric_color_cycle,
    "cycle_by_reverse_numeric_color_order": _reverse_numeric_color_cycle,
    "assume_fixed_2_2_2_region_boundaries": _fixed_equal_width_boundaries,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only this rival actually fits every usable canonical pair. The others
# remain useful competitors but must not be advertised as canonical fits.
CANONICAL_SHORTCUTS = {
    "cycle_by_reverse_numeric_color_order": _reverse_numeric_color_cycle,
}


def _all_regions_have_holes(grid) -> bool:
    bg, _, regions, _ = _analyze(grid)
    return all(any(grid[r][c] == bg for r in range(len(grid)) for c in region) for region in regions)


def _previous_direction_differs(grid) -> bool:
    return _fill_with_previous_region_color(grid) != rule_mirror(grid)


def _separator_preservation_matters(grid) -> bool:
    return _fill_separator_columns_too(grid) != rule_mirror(grid)


def _numeric_order_differs(grid) -> bool:
    return _numeric_color_cycle(grid) != rule_mirror(grid)


def _reverse_numeric_order_differs(grid) -> bool:
    return _reverse_numeric_color_cycle(grid) != rule_mirror(grid)


def _asymmetric_layout(grid) -> bool:
    _, _, regions, _ = _analyze(grid)
    return [len(region) for region in regions] != [2, 2, 2]


def _constant_middle_color_differs(grid) -> bool:
    return _fill_all_holes_with_middle_color(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "visible_holes_in_all_three_regions": _all_regions_have_holes,
    "cyclic_direction_discriminator": _previous_direction_differs,
    "separator_columns_must_stay_background": _separator_preservation_matters,
    "spatial_cycle_not_numeric_color_cycle": _numeric_order_differs,
    "spatial_cycle_not_reverse_numeric_color_cycle": _reverse_numeric_order_differs,
    "asymmetric_region_widths": _asymmetric_layout,
    "replacement_depends_on_source_region": _constant_middle_color_differs,
}

WITNESS_RIVALS = {
    "visible_holes_in_all_three_regions": [
        "identity",
        "fill_holes_with_own_region_color",
    ],
    "cyclic_direction_discriminator": ["fill_holes_with_previous_region_color"],
    "separator_columns_must_stay_background": ["also_fill_separator_columns"],
    "spatial_cycle_not_numeric_color_cycle": ["cycle_by_numeric_color_order"],
    "spatial_cycle_not_reverse_numeric_color_cycle": ["cycle_by_reverse_numeric_color_order"],
    "asymmetric_region_widths": ["assume_fixed_2_2_2_region_boundaries"],
    "replacement_depends_on_source_region": ["fill_all_holes_with_middle_region_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"{role} output does not match cyclic next-region filling")

    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Four targeted malformed/rule-hiding scenes the grammar must reject."""
    base = generate(910001, 17, difficulty="medium")
    bg, separators, regions, colors = _analyze(base)
    fixtures: list[tuple[str, list[list[int]]]] = []

    broken_separator = [row[:] for row in base]
    broken_separator[0][separators[0]] = colors[0]
    fixtures.append(("separator_not_full_background", broken_separator))

    mixed_region = [row[:] for row in base]
    target_col = regions[0][0]
    target_row = next(r for r in range(len(base)) if mixed_region[r][target_col] != bg)
    mixed_region[target_row][target_col] = colors[1]
    fixtures.append(("region_contains_two_foreground_colors", mixed_region))

    duplicate_color = [row[:] for row in base]
    for r in range(len(base)):
        for c in regions[1]:
            if duplicate_color[r][c] != bg:
                duplicate_color[r][c] = colors[0]
    fixtures.append(("two_regions_share_foreground_color", duplicate_color))

    no_holes = [row[:] for row in base]
    for r in range(len(base)):
        for c in regions[2]:
            if no_holes[r][c] == bg:
                no_holes[r][c] = colors[2]
    fixtures.append(("region_has_no_holes", no_holes))

    return fixtures
