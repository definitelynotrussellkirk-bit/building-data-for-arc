"""Input sampler for recoloring connected components by area rank.

The unchanged Racket authority reads a contiguous legend from row 0, ranks all
nonzero components below it by area descending (ties: top row, then left
column), and recolors rank i with legend[i].  This sampler emits only inputs.

A four-sample curriculum schedule deliberately covers the two canonical edge
branches the imported sampler omitted: equal-area ties and color 8 appearing in
the legend.  Every four consecutive requested samples contain two witnesses of
each branch, so holding out any one pair still leaves both rules demonstrated.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "41a5c2fcf25a"
RULE_HASH = "729bc9e3873e"
VERSION = "3.0.0"
SUMMARY = (
    "A contiguous 2..4-color legend occupies the left of row 0. Rows below "
    "contain the same number of separated color-8 components. Rank components "
    "by area descending, breaking equal-area ties by top row then left column, "
    "and recolor rank i with legend[i]. Scheduled lessons retain examples with "
    "equal-area ties and with 8 itself as a legitimate legend color."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_source_tie",
    "broad_distinct",
    "source_distinct",
    "canonical_tie",
)

INVARIANTS = [
    "rectangular 10..14 by 11..16 integer grid with background 0",
    "row 0 is a contiguous prefix of 2..4 distinct nonzero legend colors",
    "below row 0 are exactly as many cardinal components, all initially color 8",
    "component areas are 2..8; equal areas are lawful and use top/left tie-breaking",
    "ordinary lessons separate area rank from position and numeric color order",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled/difficulty-weighted", "valid": "10..14"},
    "grid_w": {"type": "int", "default": "scheduled/difficulty-weighted", "valid": "11..16"},
    "n_blobs": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

BLOB_COLOR = 8
_DIFFICULTIES = {None, "easy", "medium", "hard"}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Connected shapes, all with a <=3x3 bounding box. D4 transforms are added
# below, so these few seeds still provide substantial local-shape diversity.
_SHAPE_SEEDS = {
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    ),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Declared four-period lesson schedule; explicit axes still take precedence."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer (not {type(seed).__name__})")
    if type(sample_index) is not int:
        raise TypeError(f"sample_index must be an integer (not {type(sample_index).__name__})")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"difficulty must be one of easy/medium/hard/None, not {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {"grid_h": (10, 14), "grid_w": (11, 16), "n_blobs": (2, 4)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_axis(ctx, overrides, name, lo, hi, options):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(options))


def _shape_options(profile, difficulty):
    if profile == "canonical_source_tie":
        return (11,), (13,)
    if profile == "canonical_tie":
        return (10,), (12,)
    heights = {
        "easy": (10, 10, 11, 11, 12),
        "medium": (10, 11, 12, 13),
        "hard": (11, 12, 13, 14, 14),
        None: tuple(range(10, 15)),
    }[difficulty]
    widths = {
        "easy": (11, 11, 12, 12, 13),
        "medium": (11, 12, 13, 14, 15),
        "hard": (12, 13, 14, 15, 16, 16),
        None: tuple(range(11, 17)),
    }[difficulty]
    return heights, widths


def _count_options(profile, difficulty):
    if profile in {"canonical_source_tie", "canonical_tie"}:
        return (3,)
    return {
        "easy": (2, 2, 3, 3, 4),
        "medium": (2, 3, 3, 4),
        "hard": (2, 3, 4, 4),
        None: (2, 3, 4),
    }[difficulty]


def _normalize(shape):
    min_row = min(row for row, _ in shape)
    min_col = min(col for _, col in shape)
    return tuple(sorted((row - min_row, col - min_col) for row, col in shape))


def _shape_transforms(size):
    transformed = set()
    for seed in _SHAPE_SEEDS[size]:
        for reflected in (False, True):
            points = tuple((row, -col if reflected else col) for row, col in seed)
            for turns in range(4):
                current = points
                for _ in range(turns):
                    current = tuple((col, -row) for row, col in current)
                normalized = _normalize(current)
                height = max(row for row, _ in normalized) + 1
                width = max(col for _, col in normalized) + 1
                if height <= 3 and width <= 3:
                    transformed.add(normalized)
    return tuple(sorted(transformed))


_SHAPES = {size: _shape_transforms(size) for size in _SHAPE_SEEDS}


def _slot_anchors(h, w):
    # A blank row separates the legend and top slots; at least one blank row
    # and three blank columns separate the two bands on the smallest canvas.
    return ((2, 1), (2, w - 4), (h - 4, 1), (h - 4, w - 4))


def _spatial_sizes(n_blobs, tie_profile):
    if tie_profile:
        return {
            2: (4, 4),
            3: (4, 6, 4),
            4: (4, 6, 4, 3),
        }[n_blobs]
    return {
        2: (2, 6),
        3: (2, 6, 4),
        4: (2, 6, 3, 5),
    }[n_blobs]


def _legend(ctx, n_blobs, include_source):
    rng = ctx.draw_rng("legend")
    ordinary = [color for color in range(1, 10) if color != BLOB_COLOR]
    colors = rng.sample(ordinary, n_blobs - int(include_source))
    if include_source:
        colors.append(BLOB_COLOR)
    rng.shuffle(colors)
    # The numeric-sort shortcut should never be accidentally identical.
    if colors == sorted(colors):
        colors.reverse()
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    height_options, width_options = _shape_options(profile, difficulty)
    count_options = _count_options(profile, difficulty)
    h = _draw_axis(ctx, overrides, "grid_h", 10, 14, height_options)
    w = _draw_axis(ctx, overrides, "grid_w", 11, 16, width_options)
    n_blobs = _draw_axis(ctx, overrides, "n_blobs", 2, 4, count_options)

    include_source = profile in {"canonical_source_tie", "source_distinct"}
    tie_profile = profile in {"canonical_source_tie", "canonical_tie"}
    legend = _legend(ctx, n_blobs, include_source)

    grid = full_grid(h, w, 0)
    for col, color in enumerate(legend):
        grid[0][col] = color

    slot_rng = ctx.draw_rng("component_slots")
    anchors = sorted(slot_rng.sample(_slot_anchors(h, w), n_blobs))
    sizes = _spatial_sizes(n_blobs, tie_profile)
    for index, ((top, left), size) in enumerate(zip(anchors, sizes)):
        shape = ctx.draw_rng(f"shape_{index}").choice(_SHAPES[size])
        for dr, dc in shape:
            grid[top + dr][left + dc] = BLOB_COLOR

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError(f"constructive generator violated its contract: {errors}")
    return grid


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(1, h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _CARDINAL:
                    nxt = current[0] + dr, current[1] + dc
                    if (1 <= nxt[0] < h and 0 <= nxt[1] < w
                            and grid[nxt[0]][nxt[1]] != 0 and nxt not in seen):
                        seen.add(nxt)
                        stack.append(nxt)
            found.append(tuple(sorted(cells)))
    return found


def _bbox_key(cells):
    return min(row for row, _ in cells), min(col for _, col in cells)


def _legend_values(grid):
    return [value for value in grid[0] if value != 0]


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(_components(grid))}


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not booleans)"]

    h, w = len(grid), len(grid[0])
    errors = []
    if not 10 <= h <= 14 or not 11 <= w <= 16:
        errors.append("canvas must be 10..14 rows by 11..16 columns")

    colors = _legend_values(grid)
    if not 2 <= len(colors) <= 4:
        errors.append(f"legend must contain 2..4 colors, found {len(colors)}")
    if len(colors) != len(set(colors)):
        errors.append("legend colors must be distinct")
    if any(value == 0 for value in grid[0][:len(colors)]):
        errors.append("legend must be a contiguous nonzero prefix")
    if any(value != 0 for value in grid[0][len(colors):]):
        errors.append("row 0 may contain no nonzero cells after the legend")

    wrong_payload = [(row, col, grid[row][col]) for row in range(1, h) for col in range(w)
                     if grid[row][col] not in (0, BLOB_COLOR)]
    if wrong_payload:
        errors.append("all component cells below row 0 must initially be color 8")
    comps = _components(grid)
    if len(comps) != len(colors):
        errors.append(f"component count {len(comps)} must equal legend length {len(colors)}")
    bad_sizes = [len(cells) for cells in comps if not 2 <= len(cells) <= 8]
    if bad_sizes:
        errors.append(f"component areas must be 2..8, found {bad_sizes}")

    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if value is not None and observed.get(name) != value:
                errors.append(f"override {name}={value!r} not observable (got {observed.get(name)!r})")
    return errors


def strict_canonical_like(grid):
    """Lawful task-domain input; teaching witnesses are checked separately."""
    return self_check(grid)


def _ranked(grid, mode="canonical"):
    comps = _components(grid)
    if mode == "canonical":
        return sorted(comps, key=lambda cells: (-len(cells), *_bbox_key(cells)))
    if mode == "position":
        return sorted(comps, key=_bbox_key)
    if mode == "ascending":
        return sorted(comps, key=lambda cells: (len(cells), *_bbox_key(cells)))
    if mode == "reverse_ties":
        return sorted(comps, key=lambda cells: (-len(cells), -_bbox_key(cells)[0], -_bbox_key(cells)[1]))
    raise ValueError(mode)


def _recolor(grid, *, mode="canonical", colors=None):
    output = deepcopy(grid)
    palette = list(colors) if colors is not None else _legend_values(grid)
    for index, cells in enumerate(_ranked(grid, mode)):
        color = palette[index] if index < len(palette) else palette[-1]
        for row, col in cells:
            output[row][col] = color
    return output


def _identity(grid):
    return deepcopy(grid)


def _position_only(grid):
    return _recolor(grid, mode="position")


def _ascending_area(grid):
    return _recolor(grid, mode="ascending")


def _sorted_legend(grid):
    return _recolor(grid, colors=sorted(_legend_values(grid)))


def _reverse_equal_size_ties(grid):
    return _recolor(grid, mode="reverse_ties")


def _exclude_source_from_legend(grid):
    colors = _legend_values(grid)
    if BLOB_COLOR not in colors:
        return _recolor(grid)
    kept = [color for color in colors if color != BLOB_COLOR]
    replacement = (kept + [kept[-1]] * len(colors))[:len(colors)]
    return _recolor(grid, colors=replacement)


def _visible_recolor(grid):
    return _identity(grid) != _recolor(grid)


def _rank_conflicts_position(grid):
    return _ranked(grid) != _ranked(grid, "position")


def _legend_order_matters(grid):
    colors = _legend_values(grid)
    return colors != sorted(colors)


def _equal_area_tie(grid):
    sizes = [len(cells) for cells in _components(grid)]
    return len(set(sizes)) < len(sizes)


def _source_color_in_legend(grid):
    return BLOB_COLOR in _legend_values(grid)


SEMANTIC_WITNESSES = {
    "visible_recolor": _visible_recolor,
    "rank_conflicts_with_position": _rank_conflicts_position,
    "legend_order_matters": _legend_order_matters,
    "equal_area_tie": _equal_area_tie,
    "source_color_in_legend": _source_color_in_legend,
}
SEMANTIC_RIVALS = {
    "identity": _identity,
    "position_only": _position_only,
    "ascending_area": _ascending_area,
    "sorted_legend": _sorted_legend,
    "reverse_equal_size_ties": _reverse_equal_size_ties,
    "exclude_source_from_legend": _exclude_source_from_legend,
}
WITNESS_RIVALS = {
    "visible_recolor": ["identity"],
    "rank_conflicts_with_position": ["position_only", "ascending_area"],
    "legend_order_matters": ["sorted_legend"],
    "equal_area_tie": ["reverse_equal_size_ties"],
    "source_color_in_legend": ["exclude_source_from_legend"],
}
CANONICAL_SHORTCUTS = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check against the supplied demonstration labels."""
    return [
        f"demonstrations do not distinguish declared rival {name}"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
