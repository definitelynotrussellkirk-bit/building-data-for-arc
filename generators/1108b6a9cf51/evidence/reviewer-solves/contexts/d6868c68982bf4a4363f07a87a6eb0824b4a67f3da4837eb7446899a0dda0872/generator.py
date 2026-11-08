"""Generator for Three-Panel Transform Transfer.

The input is a horizontal strip of three square panels, A, B, and C,
separated by full color-9 columns.  Exactly one of the eight dihedral
transforms maps A to B.  The same transform must be applied to C to obtain
the output.

Generated A and C panels have full eight-element dihedral orbits.  This makes
the demonstration transform identifiable and keeps the query transform
visible instead of relying on symmetric or empty patterns.  Defaults cover
all eight transforms, panel sizes 3..6, several fill levels, and 2..6 panel
colors while retaining the canonical 3x3 sparse/balanced regime.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1108b6a9cf51"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4bae1d8a7451"
SUMMARY = (
    "Infer the unique dihedral transform mapping the first square panel to "
    "the second, then apply it to the third panel."
)

INVARIANTS = [
    "three equal square panels are separated by exactly two full color-9 columns",
    "panel values use ARC colors 0..8; color 9 is reserved for separators",
    "exactly one of the eight dihedral transforms maps panel A to panel B",
    "panels A and C are nonempty, contain background, and have full D4 orbits",
    "the output is the inferred transform applied to panel C",
]

TRANSFORMS = (
    "identity",
    "rotate_cw",
    "rotate_180",
    "rotate_ccw",
    "flip_lr",
    "flip_ud",
    "transpose",
    "anti_transpose",
)
FILL_LEVELS = ("sparse", "balanced", "dense")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "panel_size": {
        "type": "int",
        "default": "difficulty-aware draw across the full range",
        "valid": "3..6",
    },
    "transform": {
        "type": "str",
        "default": "uniform over all eight D4 transforms",
        "valid": "|".join(TRANSFORMS),
    },
    "panel_colors": {
        "type": "int",
        "default": "difficulty-aware draw across the full range",
        "valid": "2..6",
    },
    "a_fill_level": {
        "type": "str",
        "default": "easy favors sparse; hard favors dense",
        "valid": "|".join(FILL_LEVELS),
    },
    "c_fill_level": {
        "type": "str",
        "default": "easy favors sparse; hard favors dense",
        "valid": "|".join(FILL_LEVELS),
    },
}

_PANEL_SIZE_LO = 3
_PANEL_SIZE_HI = 6
_CANONICAL_PRIOR_P = 0.32
_FILL_RATIOS = {
    "sparse": 0.33,
    "balanced": 0.44,
    "dense": 0.67,
}

# (panel size, transform, A nonzero cells, C nonzero cells, distinct A/C
# colors).  These are independent extractions from all four official train
# inputs and the held-out test input.
_CANONICAL_PROFILES = (
    (3, "rotate_cw", 3, 4, 3),
    (3, "flip_lr", 4, 4, 2),
    (3, "transpose", 4, 4, 2),
    (3, "rotate_180", 4, 3, 3),
    (3, "anti_transpose", 4, 4, 2),
)
_CANONICAL_SIGNATURES = frozenset(_CANONICAL_PROFILES)


def _clone(grid):
    return [row[:] for row in grid]


def _xform(grid, name):
    """Return one D4 transform without mutating the input grid."""
    n = len(grid)
    if name == "identity":
        return _clone(grid)
    if name == "rotate_cw":
        return [[grid[n - 1 - r][c] for r in range(n)] for c in range(n)]
    if name == "rotate_180":
        return [row[::-1] for row in grid[::-1]]
    if name == "rotate_ccw":
        return [[grid[r][n - 1 - c] for r in range(n)] for c in range(n)]
    if name == "flip_lr":
        return [row[::-1] for row in grid]
    if name == "flip_ud":
        return [row[:] for row in grid[::-1]]
    if name == "transpose":
        return [[grid[c][r] for c in range(n)] for r in range(n)]
    if name == "anti_transpose":
        return [
            [grid[n - 1 - c][n - 1 - r] for c in range(n)]
            for r in range(n)
        ]
    raise ValueError(f"unknown transform {name!r}")


def _panel_key(grid):
    return tuple(tuple(row) for row in grid)


def _orbit_size(grid):
    return len({_panel_key(_xform(grid, name)) for name in TRANSFORMS})


def _fill_count(panel_size, level):
    return max(3, min(panel_size * panel_size - 1, round(
        _FILL_RATIOS[level] * panel_size * panel_size
    )))


def _fill_level(panel_size, count):
    hits = [
        level
        for level in FILL_LEVELS
        if _fill_count(panel_size, level) == count
    ]
    return hits[0] if len(hits) == 1 else None


def _split_panels(grid, separator_columns):
    first, second = separator_columns
    spans = ((0, first), (first + 1, second), (second + 1, len(grid[0])))
    return [
        [row[left:right] for row in grid]
        for left, right in spans
    ]


def _analysis(grid):
    """Recover all rule-relevant facts solely from a returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None
    height, width = len(grid), len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return None
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None

    separator_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    if len(separator_columns) != 2:
        return {
            "height": height,
            "width": width,
            "separator_columns": separator_columns,
            "panels": None,
        }

    panels = _split_panels(grid, separator_columns)
    square_panels = all(
        len(panel) == height
        and all(len(row) == height for row in panel)
        for panel in panels
    )
    if not square_panels:
        return {
            "height": height,
            "width": width,
            "separator_columns": separator_columns,
            "panels": panels,
        }

    panel_a, panel_b, panel_c = panels
    candidates = tuple(
        name for name in TRANSFORMS if _xform(panel_a, name) == panel_b
    )
    panel_colors = {
        value
        for panel in (panel_a, panel_c)
        for row in panel
        for value in row
        if value not in (0, 9)
    }
    a_cells = sum(value != 0 for row in panel_a for value in row)
    c_cells = sum(value != 0 for row in panel_c for value in row)
    return {
        "height": height,
        "width": width,
        "separator_columns": separator_columns,
        "panels": panels,
        "candidates": candidates,
        "panel_colors": panel_colors,
        "a_cells": a_cells,
        "c_cells": c_cells,
        "a_fill_level": _fill_level(height, a_cells),
        "c_fill_level": _fill_level(height, c_cells),
    }


def profile_signature(grid):
    info = _analysis(grid)
    if (
        info is None
        or info.get("panels") is None
        or len(info.get("candidates", ())) != 1
    ):
        return None
    return (
        info["height"],
        info["candidates"][0],
        info["a_cells"],
        info["c_cells"],
        len(info["panel_colors"]),
    )


def canonical_profile_signature(grid):
    signature = profile_signature(grid)
    return signature if signature in _CANONICAL_SIGNATURES else None


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def rule_mirror(grid):
    """Independent Python mirror of transform inference and transfer."""
    info = _analysis(grid)
    if (
        info is None
        or info.get("panels") is None
        or len(info.get("candidates", ())) != 1
    ):
        raise ValueError("grid must identify exactly one A-to-B transform")
    return _xform(info["panels"][2], info["candidates"][0])


def observe_overrides(grid):
    """Derive every declared exact axis from observable grid structure."""
    info = _analysis(grid)
    if (
        info is None
        or info.get("panels") is None
        or len(info.get("candidates", ())) != 1
        or info["a_fill_level"] is None
        or info["c_fill_level"] is None
    ):
        return {}
    return {
        "panel_size": info["height"],
        "transform": info["candidates"][0],
        "panel_colors": len(info["panel_colors"]),
        "a_fill_level": info["a_fill_level"],
        "c_fill_level": info["c_fill_level"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete three-panel transform grammar."""
    info = _analysis(grid)
    if info is None:
        return ["grid must be a nonempty rectangular ARC-color matrix"]

    errors = []
    height, width = info["height"], info["width"]
    if not _PANEL_SIZE_LO <= height <= _PANEL_SIZE_HI:
        errors.append(
            f"panel height {height} outside "
            f"{_PANEL_SIZE_LO}..{_PANEL_SIZE_HI}"
        )
    if width != 3 * height + 2:
        errors.append(f"width {width} must equal 3*height+2")

    separators = info["separator_columns"]
    expected_separators = [height, 2 * height + 1]
    if separators != expected_separators:
        errors.append(
            f"expected full color-9 separators at {expected_separators}, "
            f"found {separators}"
        )
    if info.get("panels") is None:
        return errors or ["could not split three equal square panels"]

    panels = info["panels"]
    for index, panel in enumerate(panels):
        if any(value == 9 for row in panel for value in row):
            errors.append(f"panel {index} contains reserved separator color 9")

    panel_a, _panel_b, panel_c = panels
    for label, panel in (("A", panel_a), ("C", panel_c)):
        cells = [value for row in panel for value in row]
        if not any(value != 0 for value in cells):
            errors.append(f"panel {label} has no nonzero content")
        if not any(value == 0 for value in cells):
            errors.append(f"panel {label} has no background content")
        if _orbit_size(panel) != len(TRANSFORMS):
            errors.append(f"panel {label} does not have a full D4 orbit")

    candidates = info.get("candidates", ())
    if len(candidates) != 1:
        errors.append(
            "A-to-B transform must be unique; "
            f"found {len(candidates)} candidates"
        )

    if not 2 <= len(info.get("panel_colors", ())) <= 6:
        errors.append("A and C must jointly use 2..6 nonzero colors")

    requested = (
        (meta or {}).get("overrides", {})
        if isinstance(meta, dict)
        else {}
    )
    if requested:
        observed = observe_overrides(grid)
        for name in AXES:
            if name in requested and observed.get(name) != requested[name]:
                errors.append(
                    f"override {name}={requested[name]!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def _snake_path(panel_size, orientation, reverse):
    """A transformed Hamiltonian path through every panel cell."""
    base = []
    for row in range(panel_size):
        columns = (
            range(panel_size)
            if row % 2 == 0
            else range(panel_size - 1, -1, -1)
        )
        base.extend((row, col) for col in columns)

    order_grid = full_grid(panel_size, panel_size, 0)
    for index, (row, col) in enumerate(base):
        order_grid[row][col] = index
    transformed = _xform(order_grid, orientation)
    path = [None] * (panel_size * panel_size)
    for row in range(panel_size):
        for col in range(panel_size):
            path[transformed[row][col]] = (row, col)
    return path[::-1] if reverse else path


def _clustered_panel(rng, panel_size, colors, count):
    """Place every color as one connected segment of a snake path."""
    path = _snake_path(
        panel_size,
        rng.choice(TRANSFORMS),
        bool(rng.randrange(2)),
    )
    start = rng.randint(0, len(path) - count)
    positions = path[start:start + count]
    cuts = sorted(rng.sample(range(1, count), len(colors) - 1))
    bounds = [0, *cuts, count]
    color_order = colors[:]
    rng.shuffle(color_order)

    panel = full_grid(panel_size, panel_size, 0)
    for color, left, right in zip(color_order, bounds, bounds[1:]):
        for row, col in positions[left:right]:
            panel[row][col] = color
    return panel


def _fill_options(difficulty):
    if difficulty == "easy":
        return ("sparse", "sparse", "balanced", "dense")
    if difficulty == "hard":
        return ("sparse", "balanced", "dense", "dense")
    return FILL_LEVELS


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_profile = None
    if (
        not overrides
        and ctx.draw_rng("canonical_prior").random()
        < _CANONICAL_PRIOR_P
    ):
        canonical_profile = ctx.draw_rng("canonical_profile").choice(
            _CANONICAL_PROFILES
        )

    if canonical_profile is not None:
        (
            panel_size,
            transform,
            a_count,
            c_count,
            panel_colors,
        ) = canonical_profile
        a_fill_level = _fill_level(panel_size, a_count)
        c_fill_level = _fill_level(panel_size, c_count)
        ctx.overrides.update({
            "panel_size": panel_size,
            "transform": transform,
            "panel_colors": panel_colors,
            "a_fill_level": a_fill_level,
            "c_fill_level": c_fill_level,
        })
        panel_size = ctx.draw_int(
            "panel_size", panel_size, panel_size
        )
        transform = ctx.draw_choice("transform", (transform,))
        panel_colors = ctx.draw_int(
            "panel_colors", panel_colors, panel_colors
        )
        a_fill_level = ctx.draw_choice(
            "a_fill_level", (a_fill_level,)
        )
        c_fill_level = ctx.draw_choice(
            "c_fill_level", (c_fill_level,)
        )
    else:
        panel_size = ctx.draw_int_diff(
            "panel_size", _PANEL_SIZE_LO, _PANEL_SIZE_HI
        )
        transform = ctx.draw_choice("transform", TRANSFORMS)
        panel_colors = ctx.draw_int_diff("panel_colors", 2, 6)
        a_fill_level = ctx.draw_choice(
            "a_fill_level", _fill_options(difficulty)
        )
        c_fill_level = ctx.draw_choice(
            "c_fill_level", _fill_options(difficulty)
        )

    a_count = _fill_count(panel_size, a_fill_level)
    c_count = _fill_count(panel_size, c_fill_level)
    if panel_colors > a_count + c_count:
        raise ValueError(
            "panel_colors exceeds the available nonzero A/C cells"
        )

    palette_rng = ctx.draw_rng("panel_palette")
    colors = palette_rng.sample(list(range(1, 9)), panel_colors)
    panel_rng = ctx.draw_rng("panel_contents")
    for _attempt in range(512):
        color_order = colors[:]
        panel_rng.shuffle(color_order)
        min_a_colors = max(1, panel_colors - c_count)
        max_a_colors = min(panel_colors - 1, a_count)
        a_color_count = panel_rng.randint(min_a_colors, max_a_colors)
        panel_a = _clustered_panel(
            panel_rng,
            panel_size,
            color_order[:a_color_count],
            a_count,
        )
        panel_c = _clustered_panel(
            panel_rng,
            panel_size,
            color_order[a_color_count:],
            c_count,
        )
        if _orbit_size(panel_a) != len(TRANSFORMS):
            continue
        if _orbit_size(panel_c) != len(TRANSFORMS):
            continue

        panel_b = _xform(panel_a, transform)
        width = 3 * panel_size + 2
        grid = full_grid(panel_size, width, 0)
        for row in range(panel_size):
            grid[row][panel_size] = 9
            grid[row][2 * panel_size + 1] = 9
            grid[row][0:panel_size] = panel_a[row][:]
            grid[row][panel_size + 1:2 * panel_size + 1] = panel_b[row][:]
            grid[row][2 * panel_size + 2:width] = panel_c[row][:]

        errors = self_check(
            grid,
            difficulty=difficulty,
            meta={"overrides": overrides},
        )
        if not errors:
            return grid
    raise ValueError("could not construct asymmetric transform-transfer panels")
