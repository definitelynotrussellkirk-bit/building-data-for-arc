"""Input generator for the vertical-mirror-above-original task.

The unchanged authority outputs ``flip_ud(input)`` above ``input``.  Official
inputs are all 3x4 two-colour grids, so the production sampler deliberately
keeps a high-support canonical-profile family while alternating it with broader
heights.  That alternation teaches that the rule mirrors *all* rows rather than
memorising a fixed three-row permutation.

Only four exact, observable controls are public.  Internal appearance choices
are nuisance variation, not pseudo-axes whose requested values cannot be
recovered from returned pixels.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "d89cff1052a2"
TASK_ID = GENERATOR_ID
RULE_HASH = "370a7fcc45fc"
VERSION = "2.0.2"
SUMMARY = (
    "A 3..15 by 3..30 grid using 2..4 colours.  The authority stacks the "
    "vertical reflection above the unchanged input.  Default lessons alternate "
    "canonical-profile 3x4 binary inputs with broader non-three-row inputs, and "
    "adjacent broad slots have opposite height parity so teaching witnesses "
    "survive duplicate rejection. All ordinary draws make the reflection visible."
)

INVARIANTS = [
    "rectangular input is 3..15 rows by 3..30 columns",
    "exactly 2..4 integer colours in 0..9, each used at least twice",
    "ordinary draws are vertically asymmetric so flip-then-stack differs from duplication",
    "every four consecutive ordinary samples contain two 3-row and two non-3-row inputs",
    "the two broad inputs in any four ordinary slots differ in height parity and cannot duplicate",
]

AXES = {
    "grid_h": {"type": "int", "default": "alternating 3 or band-weighted 4..15", "valid": "3..15"},
    "grid_w": {"type": "int", "default": "canonical 4 or band-weighted 3..30", "valid": "3..30"},
    "palette_size": {"type": "int", "default": "canonical 2 or band-weighted 2..4", "valid": "2..4"},
    "ud_asymmetric": {"type": "bool", "default": "true", "valid": "true|false"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Canonical / even-height broad / canonical / odd-height broad. Two broad
# witnesses in any four raw slots cannot duplicate each other or a 3-row
# anchor, so both survive the worker's duplicate-pair filter. Every query
# rotation of the first four accepted pairs retains a non-three-row demo.
LESSON_SCHEDULE_PERIOD = 4
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45


# ---------------------------------------------------------------------------
# Validation and small geometry helpers
# ---------------------------------------------------------------------------

def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    integer_bounds = {
        "grid_h": (3, 15),
        "grid_w": (3, 30),
        "palette_size": (2, 4),
    }
    for name, (lo, hi) in integer_bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

    value = overrides.get("ud_asymmetric")
    if value is not None and type(value) is not bool:
        raise TypeError("ud_asymmetric must be a bool")


def _is_ud_symmetric(grid):
    return all(
        grid[row][col] == grid[len(grid) - 1 - row][col]
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )


def _component_count(cells, height, width):
    unseen = set(cells)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            row, col = stack.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in unseen and 0 <= point[0] < height and 0 <= point[1] < width:
                    unseen.remove(point)
                    stack.append(point)
    return count


@lru_cache(maxsize=1)
def _canonical_masks():
    """Many 3x4 binary masks with canonical counts and two minority objects."""
    masks = []
    positions = tuple(range(12))
    for count in (4, 5):
        for chosen in combinations(positions, count):
            cells = frozenset(divmod(index, 4) for index in chosen)
            mask = tuple(tuple((row, col) in cells for col in range(4)) for row in range(3))
            if mask == tuple(reversed(mask)):
                continue
            if _component_count(cells, 3, 4) != 2:
                continue
            masks.append(mask)
    if not masks:
        raise RuntimeError("canonical mask construction unexpectedly produced no masks")
    return tuple(masks)


def _record_exact(ctx, height, width, palette_size, asymmetric):
    """Record every declared exact axis on the canonical-profile return path."""
    ctx.draw_int_strict("grid_h", height, height)
    ctx.draw_int_strict("grid_w", width, width)
    ctx.draw_int_strict("palette_size", palette_size, palette_size)
    ctx.draw_choice("ud_asymmetric", [asymmetric])


# ---------------------------------------------------------------------------
# Constructive input families
# ---------------------------------------------------------------------------

def _canonical_family(ctx, band):
    rng = ctx.draw_rng(f"canonical_family|{band}")
    palette = ctx.draw_distinct_colors("palette", n=2)
    mask = rng.choice(_canonical_masks())
    # Shuffle which sampled colour is the minority without changing the mask's
    # 4/8 or 5/7 support profile.
    if rng.randrange(2):
        background, minority = palette
    else:
        minority, background = palette
    grid = [
        [minority if mask[row][col] else background for col in range(4)]
        for row in range(3)
    ]
    _record_exact(ctx, 3, 4, 2, True)
    return grid


def _draw_broad_int(ctx, name, lo, hi, defaults, *, ordinary_lo=None, ordinary_parity=None):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # Duplicate the band defaults to make difficulty a distributional hint;
    # every explicit override still uses the full documented domain above.
    start = lo if ordinary_lo is None else ordinary_lo
    options = list(range(start, hi + 1)) + list(defaults) * 12
    if ordinary_parity is not None:
        options = [value for value in options if value % 2 == ordinary_parity]
    return ctx.draw_choice(name, options)


def _broad_axes(ctx, band, *, ordinary_height_parity=None):
    if band == "easy":
        heights = (4, 4, 5, 5, 6)
        widths = (4, 5, 5, 6, 7, 8)
        palettes = (2, 2, 2, 3)
    elif band == "hard":
        heights = (6, 7, 8, 9, 10)
        widths = (8, 9, 10, 12, 14)
        palettes = (2, 3, 3, 4, 4)
    else:
        heights = (4, 4, 5, 6, 7, 8)
        widths = (4, 5, 6, 7, 8, 10, 12)
        palettes = (2, 2, 3, 3, 4)

    # Height three is reserved for the canonical-profile schedule slot.  If a
    # broad slot could also draw height three, rotating the sole non-three-row
    # pair to query can leave only shortcut-consistent demonstrations.
    height = _draw_broad_int(
        ctx, "grid_h", 3, 15, heights,
        ordinary_lo=4, ordinary_parity=ordinary_height_parity,
    )
    width = _draw_broad_int(ctx, "grid_w", 3, 30, widths)
    palette_size = _draw_broad_int(ctx, "palette_size", 2, 4, palettes)
    if ctx.overrides.get("ud_asymmetric") is None:
        asymmetric = ctx.draw_choice("ud_asymmetric", [True])
    else:
        asymmetric = ctx.draw_choice("ud_asymmetric", [True, False])
    return height, width, palette_size, asymmetric


def _asymmetric_patch_grid(height, width, palette, rng):
    """Sparse foreground patches with at least two non-modal components."""
    colours = list(palette)
    rng.shuffle(colours)
    background = colours[0]
    grid = [[background for _ in range(width)] for _ in range(height)]

    # The first foreground colour occupies two separated dominoes.  This
    # excludes the one-object line/solid-block shortcut while matching the
    # canonical two-object foreground profile.
    first = colours[1]
    for row, col in ((0, 0), (0, 1), (height - 2, width - 1), (height - 1, width - 1)):
        grid[row][col] = first

    # Additional colours each get a compact two-cell component.  The minimum
    # 3x3 canvas still supports all four colours with background remaining.
    if len(colours) >= 3:
        second = colours[2]
        grid[height - 2][0] = second
        grid[height - 1][0] = second
    if len(colours) >= 4:
        third = colours[3]
        grid[1][width - 2] = third
        grid[1][width - 1] = third

    # Harmless whole-grid reflections add layout variety while preserving
    # component counts and vertical asymmetry.
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if rng.randrange(2):
        grid = list(reversed(grid))
    if _is_ud_symmetric(grid):
        raise RuntimeError("constructive asymmetric patch layout became symmetric")
    return grid


def _symmetric_patch_grid(height, width, palette, rng):
    """Vertically symmetric opt-in case with two isolated cells per foreground colour."""
    colours = list(palette)
    rng.shuffle(colours)
    background = colours[0]
    grid = [[background for _ in range(width)] for _ in range(height)]
    columns = rng.sample(range(width), len(colours) - 1)
    for colour, col in zip(colours[1:], columns):
        grid[0][col] = colour
        grid[height - 1][col] = colour
    if not _is_ud_symmetric(grid):
        raise RuntimeError("constructive symmetric patch layout failed")
    return grid


def _broad_family(ctx, band, *, ordinary_height_parity=None):
    height, width, palette_size, asymmetric = _broad_axes(
        ctx, band, ordinary_height_parity=ordinary_height_parity,
    )
    palette = ctx.draw_distinct_colors("palette", n=palette_size)
    rng = ctx.draw_rng(f"broad_layout|{band}")
    if asymmetric:
        return _asymmetric_patch_grid(height, width, palette, rng)
    return _symmetric_patch_grid(height, width, palette, rng)


# ---------------------------------------------------------------------------
# Public generator and observable contracts
# ---------------------------------------------------------------------------

def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    default_draw = not any(value is not None for value in overrides.values())

    # Half the raw draws retain the canonical profile. Opposite broad height
    # parities prevent duplicate rejection from removing a required witness.
    if default_draw and sample_index % 2 == 0:
        return _canonical_family(ctx, band)
    parity = (sample_index // 2) % 2 if default_draw else None
    return _broad_family(ctx, band, ordinary_height_parity=parity)


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "ud_asymmetric": not _is_ud_symmetric(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    height = len(grid)
    if not 3 <= height <= 15 or not 3 <= width <= 30:
        errors.append(f"dims {height}x{width} outside 3..15 x 3..30")

    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in flat):
        errors.append("cells must be literal integer colours in 0..9")
        return errors

    counts = Counter(flat)
    if not 2 <= len(counts) <= 4:
        errors.append(f"expected 2..4 distinct colours, found {len(counts)}")
    if counts and min(counts.values()) < 2:
        errors.append("every declared colour must occupy at least two cells")

    if len(counts) >= 2:
        modal = counts.most_common(1)[0][0]
        nonmodal_colours = [colour for colour in counts if colour != modal]
        nonmodal_components = sum(
            _component_count(
                {(row, col) for row in range(height) for col in range(width)
                 if grid[row][col] == colour},
                height,
                width,
            )
            for colour in nonmodal_colours
        )
        nonmodal_cells = sum(counts[colour] for colour in nonmodal_colours)
        if nonmodal_components < 2 and nonmodal_cells <= 4:
            errors.append(
                "a tiny non-modal foreground must contain at least two 4-connected components"
            )

    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for name in AXES:
            value = requested.get(name)
            if value is not None and observed[name] != value:
                errors.append(
                    f"requested {name}={value!r}, observed {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid):
    errors = list(self_check(grid))
    if errors:
        return errors
    observed = observe_overrides(grid)
    if (observed["grid_h"], observed["grid_w"], observed["palette_size"]) != (3, 4, 2):
        errors.append("strict profile requires exactly 3x4 with two colours")
    return errors


# ---------------------------------------------------------------------------
# Executable semantic rivals and witnesses
# ---------------------------------------------------------------------------

def _intended_output(grid):
    return [list(row) for row in reversed(grid)] + [list(row) for row in grid]


def _fixed_three_row_mirror(grid):
    """Canonical-consistent shortcut: mirror only the first three rows."""
    return [list(row) for row in reversed(grid[:3])] + [list(row) for row in grid]


def _duplicate_input(grid):
    """Ambiguous-on-symmetric-input shortcut: duplicate without reflecting."""
    return [list(row) for row in grid] + [list(row) for row in grid]


def _non_three_height(grid):
    return len(grid) != 3


def _visible_flip(grid):
    return not _is_ud_symmetric(grid)


SEMANTIC_WITNESSES = {
    "non_three_height": _non_three_height,
    "visible_flip": _visible_flip,
}
SEMANTIC_RIVALS = {
    "fixed_three_row_mirror": _fixed_three_row_mirror,
    "duplicate_input": _duplicate_input,
}
WITNESS_RIVALS = {
    "non_three_height": ["fixed_three_row_mirror"],
    "visible_flip": ["duplicate_input"],
}
CANONICAL_SHORTCUTS = {
    "fixed_three_row_mirror": _fixed_three_row_mirror,
}
LESSON_COMPETITORS = {
    "fixed_three_row_mirror": _fixed_three_row_mirror,
    "duplicate_input": _duplicate_input,
}
