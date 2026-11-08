"""Input sampler for 746b3537: compress adjacent identical FULL rows and columns.

The unchanged Racket ``compress-grid`` is the label authority. Equal neighbors
inside one row are retained when another row distinguishes those full columns.
Inputs are made by shared row/column expansion, never independent rowwise RLE.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "4e081a15d785"
TASK_ID = GENERATOR_ID
RULE_HASH = "0805714fcf25"
VERSION = "2.0.0"
SUMMARY = "Remove adjacent identical whole rows and whole columns; preserve separated repeats and locally equal cells in globally distinct columns."
ALLOW_IDENTITY_OUTPUT = True
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("witness", "canonical", "broad")

INVARIANTS = [
    "nonempty rectangular integer-color grid with at least two colors; Racket yields a rectangle",
    "full-line equality, not independent horizontal run equality, controls compression",
    "all exact dimensions, realized palette size, and deleted-row/column counts are observable",
    "default consecutive four-pair windows contain two rich rival-refuting examples",
]
AXES = {
    "grid_h": {"type": "int", "default": "profile mixture; exact returned height", "valid": "1..18"},
    "grid_w": {"type": "int", "default": "profile mixture; exact returned width", "valid": "1..22"},
    "base_color_count": {"type": "int", "default": "profile mixture; exact realized colors", "valid": "2..10"},
    "n_duplicates": {"type": "int", "default": "profile mixture; adjacent full rows removed", "valid": "0..17"},
    "n_column_duplicates": {"type": "int", "default": "profile mixture; adjacent full columns removed", "valid": "0..21"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []  # Dynamic feasibility errors carry axes.
_LIMITS = {"grid_h": (1, 18), "grid_w": (1, 22), "base_color_count": (2, 10),
           "n_duplicates": (0, 17), "n_column_duplicates": (0, 21)}


class IncompatibleOverrides(ValueError):
    def __init__(self, axes):
        self.incompatible_axes = tuple(sorted(axes))
        super().__init__(
            "incompatible controls: core_h=grid_h-n_duplicates and "
            "core_w=grid_w-n_column_duplicates must be positive and contain "
            "enough cells for all requested colors (at least two)")


def _dedupe(sequence):
    result = []
    for item in sequence:
        if not result or item != result[-1]:
            result.append(item)
    return result


def _transpose(grid):
    return [list(column) for column in zip(*grid)]


def _compressed_view(grid):
    """Diagnostic mirror for predicates/rivals only; never used to supply labels."""
    return _transpose(_dedupe(_transpose(_dedupe(grid))))


def observe_overrides(grid):
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "base_color_count": len({value for row in grid for value in row}),
        "n_duplicates": len(grid) - len(_dedupe(grid)),
        "n_column_duplicates": len(grid[0]) - len(_dedupe(_transpose(grid))),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["expected 1..30 nonempty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["expected 1..30 columns"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["expected a rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding bool"]
    if len({value for row in grid for value in row}) < 2:
        return ["training domain requires at least two colors; monochrome cases are excluded"]
    return []


def strict_canonical_like(grid):
    """Conservative stripe manifold covering every canonical input."""
    errors = self_check(grid)
    if errors:
        return errors
    if all(row == grid[0] for row in grid) or all(len(set(row)) == 1 for row in grid):
        return []
    return ["lawful full-line compression, outside the canonical stripe subfamily"]


def schedule_profile(seed, sample_index, difficulty=None):
    return ("witness", "witness", "canonical", "broad")[sample_index % 4]


def _partition(total, parts, rng):
    lengths = [1] * parts
    for _ in range(total - parts):
        lengths[rng.randrange(parts)] += 1
    return lengths


def _expand(core, height, width, rng):
    row_lengths = _partition(height, len(core), rng)
    col_lengths = _partition(width, len(core[0]), rng)
    result = []
    for row, repeat in zip(core, row_lengths):
        expanded = [value for value, length in zip(row, col_lengths) for _ in range(length)]
        result.extend([list(expanded) for _ in range(repeat)])
    return result


def _general_core(height, width, palette, rng):
    area = height * width
    for _ in range(32):
        flat = list(palette) + [rng.choice(palette) for _ in range(area - len(palette))]
        rng.shuffle(flat)
        core = [flat[r * width:(r + 1) * width] for r in range(height)]
        if len(_dedupe(core)) == height and len(_dedupe(_transpose(core))) == width:
            return core
    # Constructive fallback, especially for thin two-color cores. Replacing
    # cells by distinct new colors cannot merge formerly distinct full lines.
    core = [[palette[(r + c) % 2] for c in range(width)] for r in range(height)]
    reserved = {(0, 0), (0, 1) if width > 1 else (1, 0)}
    available = [(r, c) for r in range(height) for c in range(width) if (r, c) not in reserved]
    for color, (r, c) in zip(palette[2:], rng.sample(available, len(palette) - 2)):
        core[r][c] = color
    return core


def _rich_core(height, width, palette, rng):
    a, b = palette[:2]
    first, second = [a, a, b, a], [a, b, b, a]
    for column in range(4, width):
        forced = palette[column - 2] if column - 2 < len(palette) else None
        choices = [(x, y) for x in palette for y in palette
                   if (forced is None or x == forced) and (x, y) != (first[-1], second[-1])]
        x, y = rng.choice(choices)
        first.append(x)
        second.append(y)
    core = [first, second, list(first)]
    for _ in range(3, height):
        prefix = rng.choice(([a, a, b, a], [a, b, b, a]))
        row = list(prefix) + [rng.choice(palette) for _ in range(width - 4)]
        if row == core[-1]:
            row[:4] = [a, b, b, a] if row[1] == a else [a, a, b, a]
        core.append(row)
    if rng.randrange(2):
        core.reverse()
    if rng.randrange(2):
        core = [row[::-1] for row in core]
    return core


def _canonical_draw(ctx, rng):
    # Shapes/palette cardinalities, not copied canonical grids or fixed colors.
    profile = ctx.draw_choice("canonical_shape", ((4, 2, 3), (3, 3, 3), (3, 5, 4),
                                                   (6, 4, 4), (3, 3, 2), (4, 9, 5)))
    height, width, count = profile
    palette = rng.sample(range(10), count)
    if profile in ((4, 2, 3), (6, 4, 4)):
        core = [[color] for color in palette]
    elif profile == (3, 3, 2):
        core = [[palette[0]], [palette[1]], [palette[0]]]
    else:
        core = [palette]
    return core, height, width


def _default_draw(ctx, rng, difficulty, sample_index):
    profile = schedule_profile(ctx.seed, sample_index, difficulty)
    if profile == "canonical":
        return _canonical_draw(ctx, rng)
    if profile == "witness":
        max_h, max_w = {"easy": (4, 6), "hard": (9, 12)}.get(difficulty, (6, 8))
        core_h, core_w = rng.randint(3, max_h), rng.randint(4, max_w)
        count = rng.randint(2, min(8, core_w - 2))
        palette = rng.sample(range(10), count)
        core = _rich_core(core_h, core_w, palette, rng)
        return core, core_h + rng.randint(1, min(4, 18 - core_h)), core_w + rng.randint(1, min(4, 22 - core_w))
    # A broad, independently sampled component avoids making the rich template
    # the entire non-stripe domain. Its scale stays near the tiny canonical task.
    height, width = rng.randint(2, 6), rng.randint(2, 9)
    core_h, core_w = rng.choice([(h, w) for h in range(1, height + 1)
                                for w in range(1, width + 1)
                                if h * w >= 2 and (h < height or w < width)])
    capacity = core_h * core_w
    count = rng.randint(2, min(5, capacity))
    palette = rng.sample(range(10), count)
    return _general_core(core_h, core_w, palette, rng), height, width


def _controlled_draw(ctx, rng, overrides):
    """Choose only feasible parameters; never clamp or silently drop a control."""
    heights = [overrides["grid_h"]] if "grid_h" in overrides else range(1, 19)
    widths = [overrides["grid_w"]] if "grid_w" in overrides else range(1, 23)
    wanted_colors = overrides.get("base_color_count", 2)
    dr, dc = overrides.get("n_duplicates"), overrides.get("n_column_duplicates")
    feasible = []
    for h in heights:
        for w in widths:
            max_core_h, max_core_w = h - (dr or 0), w - (dc or 0)
            if max_core_h < 1 or max_core_w < 1:
                continue
            valid = max_core_h * max_core_w >= wanted_colors
            if valid:
                feasible.append((h, w))
    if not feasible:
        raise IncompatibleOverrides(overrides)
    h = ctx.draw_choice("grid_h", sorted({h for h, _ in feasible}))
    w = ctx.draw_choice("grid_w", sorted({w for hh, w in feasible if hh == h}))
    max_core_h, max_core_w = h - (dr or 0), w - (dc or 0)
    color_choices = list(range(2, min(10, max_core_h * max_core_w) + 1))
    count = ctx.draw_choice("base_color_count", color_choices)
    row_choices = [d for d in range(h) if (h - d) * max_core_w >= count]
    row_deletions = ctx.draw_choice("n_duplicates", row_choices)
    core_h = h - row_deletions
    col_choices = [d for d in range(w) if core_h * (w - d) >= count]
    col_deletions = ctx.draw_choice("n_column_duplicates", col_choices)
    palette = rng.sample(range(10), count)
    return _general_core(core_h, w - col_deletions, palette, rng), h, w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    active = {key: value for key, value in overrides.items() if value is not None}
    for key, value in active.items():
        low, high = _LIMITS[key]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{key} must be an integer in {low}..{high}, excluding bool")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=active)
    rng = ctx.draw_rng("construction")
    if active:
        core, height, width = _controlled_draw(ctx, rng, active)
    else:
        core, height, width = _default_draw(ctx, rng, difficulty, sample_index)
        values = {"grid_h": height, "grid_w": width,
                  "base_color_count": len({v for row in core for v in row}),
                  "n_duplicates": height - len(core),
                  "n_column_duplicates": width - len(core[0])}
        for key, value in values.items():
            ctx.draw_choice(key, [value])
    return _expand(core, height, width, rng)


def _rowwise_runs(grid):
    """Incorrect local RLE; pad ragged results by each row's final color."""
    rows = [_dedupe(row) for row in _dedupe(grid)]
    width = max(map(len, rows))
    return [row + [row[-1]] * (width - len(row)) for row in rows]


def _first_row_boundaries(grid):
    rows = _dedupe(grid)
    keep = [0] + [c for c in range(1, len(rows[0])) if rows[0][c] != rows[0][c - 1]]
    return [[row[c] for c in keep] for row in rows]


def _unique_lines(sequence):
    result = []
    for item in sequence:
        if item not in result:
            result.append(item)
    return result


def _global_unique_columns(grid):
    return _transpose(_unique_lines(_transpose(_dedupe(grid))))


def _global_unique_rows(grid):
    return _transpose(_dedupe(_transpose(_unique_lines(grid))))


def _rows_only(grid):
    return [list(row) for row in _dedupe(grid)]


def _columns_only(grid):
    return _transpose(_dedupe(_transpose(grid)))


def _local_run_witness(grid):
    return _rowwise_runs(grid) != _compressed_view(grid)


def _column_recurrence_witness(grid):
    return _global_unique_columns(grid) != _compressed_view(grid)


def _first_row_witness(grid):
    return _first_row_boundaries(grid) != _compressed_view(grid)


def _row_recurrence_witness(grid):
    return _global_unique_rows(grid) != _compressed_view(grid)


CANONICAL_SHORTCUTS = {"rowwise_runs": _rowwise_runs,
                       "first_row_boundaries": _first_row_boundaries,
                       "global_unique_columns": _global_unique_columns}
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS, "global_unique_rows": _global_unique_rows,
                     "rows_only": _rows_only, "columns_only": _columns_only}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {"local_runs_survive": _local_run_witness,
                      "first_row_is_not_authority": _first_row_witness,
                      "separated_columns_survive": _column_recurrence_witness,
                      "separated_rows_survive": _row_recurrence_witness}
WITNESS_RIVALS = {"local_runs_survive": ["rowwise_runs"],
                 "first_row_is_not_authority": ["first_row_boundaries"],
                 "separated_columns_survive": ["global_unique_columns"],
                 "separated_rows_survive": ["global_unique_rows"]}


def lesson_identifiable(demos, query):
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
