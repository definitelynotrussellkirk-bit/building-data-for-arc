"""Fill exactly-singleton columns, rebuilding the output on background zero.

An occupied column is eligible only when it contains exactly one nonzero CELL.
Colors shared by different columns are lawful. Ordinary four-pair windows mix
one canonical-size sparse scene and three scenes with a monochromatic rejected
column reusing an eligible seed's color. Explicit controls retain exact counts;
capacity endpoints can legitimately leave no room for that teaching feature.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49898d244b5f"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "53c8389bd783"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = "Rebuild a blank grid, filling only columns containing exactly one nonzero cell in that cell's color."
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_seeds", "all_columns_have_multiple", "columns_already_full")
# Backward-compatible call spelling, not a separate sampled degree of freedom.
COMPATIBILITY_ALIASES = {"n_distinct_colors": "palette_size"}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "background is 0; input is a rectangular 3..18 grid of integer colors 0..9",
    "at least one column contains exactly one nonzero cell",
    "multiple-cell columns are erased, even when their cells share one color",
    "output is rebuilt on a blank grid; row positions do not select columns",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical 7/8 or feasible keyed 3..18", "valid": "3..18"},
    "grid_w": {"type": "int", "default": "canonical 7/8 or feasible keyed 3..18", "valid": "3..18"},
    "palette_kind": {"type": "str", "default": "keyed default|warm|cool|varied", "valid": "|".join(PALETTE_KINDS)},
    "columns": {"type": "int", "default": "canonical 2 or weighted feasible keyed 1..12", "valid": "1..12"},
    "palette_size": {"type": "int", "default": "canonical 2 or weighted feasible keyed 1..9", "valid": "1..9"},
    "position_bias": {"type": "str", "default": "single_seed_columns", "valid": "single_seed_columns", "probe": "diagnostic"},
    # Compatibility token only: exact color-capacity endpoints may be dense.
    "density": {"type": "str", "default": "sparse (diagnostic; no occupancy ceiling)", "valid": "sparse", "probe": "diagnostic"},
    "texture": {"type": "str", "default": "alias of palette_kind", "valid": "|".join(PALETTE_KINDS)},
}
_INT_DOMAINS = {"grid_h": (3, 18), "grid_w": (3, 18), "columns": (1, 12),
                "palette_size": (1, 9), "n_distinct_colors": (1, 9)}
_PALETTES = {
    "default": (2, 6, 3, 7, 4, 1, 5, 8, 9),
    "warm": (2, 3, 4, 7, 9, 1, 5, 6, 8),
    "cool": (6, 8, 1, 5, 7, 4, 3, 2, 9),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}


class OverrideConflict(ValueError):
    """A concrete conflict involving only the caller's explicit axes."""

    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def _capacity_feasible(overrides):
    h = overrides.get("grid_h", 18)
    w = overrides.get("grid_w", 18)
    c = overrides.get("columns", 1)
    k = overrides.get("palette_size", overrides.get("n_distinct_colors", 1))
    return c <= w and k <= c + (w - c) * h


def _capacity_conflict(overrides):
    relevant = [name for name in ("grid_h", "grid_w", "columns", "palette_size", "n_distinct_colors")
                if name in overrides]
    for size in range(2, len(relevant) + 1):
        for names in combinations(relevant, size):
            if not _capacity_feasible({name: overrides[name] for name in names}):
                return names
    return tuple(relevant)


def _validate_overrides(overrides):
    unknown = set(overrides) - (set(AXES) | set(COMPATIBILITY_ALIASES))
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    explicit = {name: value for name, value in overrides.items() if value is not None}
    for name, value in explicit.items():
        if name in _INT_DOMAINS:
            lo, hi = _INT_DOMAINS[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        else:
            legal = PALETTE_KINDS if name == "palette_kind" else (
                HELPFUL_TEXTURES + DEGENERATE_TEXTURES if name == "texture" else
                ("sparse",) if name == "density" else ("single_seed_columns",))
            if not isinstance(value, str) or value not in legal:
                raise ValueError(f"invalid {name}: {value!r}")
    if all(name in explicit for name in ("palette_size", "n_distinct_colors")):
        if explicit["palette_size"] != explicit["n_distinct_colors"]:
            raise OverrideConflict("palette_size and n_distinct_colors disagree", ("palette_size", "n_distinct_colors"))
    if explicit.get("texture") in HELPFUL_TEXTURES and "palette_kind" in explicit:
        if explicit["texture"] != explicit["palette_kind"]:
            raise OverrideConflict("palette_kind and texture disagree", ("palette_kind", "texture"))
    if explicit.get("texture") in DEGENERATE_TEXTURES:
        for name in ("columns", "palette_size", "n_distinct_colors", "palette_kind"):
            if name in explicit:
                raise OverrideConflict(f"negative texture fixture cannot honor {name}", ("texture", name))
    if not _capacity_feasible(explicit):
        raise OverrideConflict("explicit controls exceed column/color cell capacity", _capacity_conflict(explicit))
    return explicit


def _choose(ctx, name, feasible, preferred=(), *, weighted=False):
    """Choose constructively from feasible values; explicit axes are never clipped."""
    feasible = tuple(feasible)
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, feasible)
    preferred = tuple(value for value in preferred if value in feasible)
    return ctx.draw_choice(name, feasible + preferred if weighted else preferred or feasible)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    explicit = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    ctx.draw_choice("density", ("sparse",))
    ctx.draw_choice("position_bias", ("single_seed_columns",))
    if explicit.get("texture") in DEGENERATE_TEXTURES:
        h = ctx.draw_int_strict("grid_h", 3, 18)
        w = ctx.draw_int_strict("grid_w", 3, 18)
        name = ctx.draw_choice("texture", DEGENERATE_TEXTURES)
        return _draw_from_degenerate(name, h, w)
    kind_hint = explicit.get("palette_kind", explicit.get("texture"))
    kind = ctx.draw_choice("palette_kind", (kind_hint,) if kind_hint else PALETTE_KINDS)
    ctx.draw_choice("texture", (kind,))
    phase = (sample_index + seed) % 4
    core = phase == 0
    # Half the default draws retain canonical size/palette morphology. Phase1
    # still teaches the rejected monochromatic column; only phase0 omits it.
    familiar_profile = phase in (0, 1)
    anchor = ctx.draw_choice("canonical_size", (7, 8))
    h_max, w_max = explicit.get("grid_h", 18), explicit.get("grid_w", 18)
    c_min = explicit.get("columns", 1)
    max_colors = min(9, c_min + (w_max - c_min) * h_max)
    color_hint = explicit.get("palette_size", explicit.get("n_distinct_colors"))
    if color_hint is not None:
        k = _choose(ctx, "palette_size", (color_hint,))
    else:
        k = _choose(ctx, "palette_size", range(1, max_colors + 1),
                    (2,) if familiar_profile else range(2, min(5, max_colors) + 1), weighted=not familiar_profile)
    ctx.draw_choice("n_distinct_colors", (k,))
    feasible_c = [c for c in range(1, min(12, w_max) + 1)
                  if k <= c + (w_max - c) * h_max]
    preferred_c = (2,) if familiar_profile else (range(2, 4) if difficulty == "easy" else
                                   range(3, 6) if difficulty == "hard" else range(2, 6))
    c = _choose(ctx, "columns", feasible_c, preferred_c, weighted=not familiar_profile)
    feasible_w = [w for w in range(max(3, c), 19) if k <= c + (w - c) * h_max]
    preferred_w = (anchor,) if familiar_profile else [w for w in feasible_w if w >= c + 2
                                        and k <= c + (w - c - 1) * h_max]
    w = _choose(ctx, "grid_w", feasible_w, preferred_w)
    feasible_h = [h for h in range(3, 19) if k <= c + (w - c) * h]
    if not core and "grid_h" not in explicit and w >= c + 2:
        # Preserve room for the active-color monochromatic column. This is
        # constructive default sampling; a pinned height remains exact.
        feasible_h = [h for h in feasible_h if k <= c + (w - c - 1) * h]
    preferred_h = (anchor,) if familiar_profile else (range(3, 9) if difficulty == "easy" else
                                        range(10, 19) if difficulty == "hard" else range(7, 13))
    h = _choose(ctx, "grid_h", feasible_h, preferred_h, weighted=not familiar_profile)
    palette = list(_PALETTES[kind])
    if kind == "varied":
        ctx.draw_rng("palette:varied").shuffle(palette)
    palette = palette[:k]
    rng = ctx.draw_rng(f"layout:{kind}")
    order = list(range(w))
    rng.shuffle(order)
    active, others = order[:c], order[c:]
    grid = full_grid(h, w, 0)
    for index, column in enumerate(active):
        grid[rng.randrange(h)][column] = palette[index % k]
    missing = palette[min(c, k):]
    # A completely monochromatic distractor consumes an entire column of
    # distinct-color capacity. Capacity endpoints honor exact axes instead.
    if not core and others and k <= c + (len(others) - 1) * h:
        column = others.pop(0)
        for row in rng.sample(range(h), rng.randint(2, h)):
            grid[row][column] = palette[0]
    need = (len(missing) + h - 1) // h
    if not core and others:
        need = max(need, 1)
    n_other = rng.randint(need, min(len(others), max(need, 2))) if need else 0
    selected_others = others[:n_other]
    missing_index = 0
    for index, column in enumerate(selected_others):
        unplaced = len(missing) - missing_index
        minimum = max(2, unplaced - (n_other - index - 1) * h)
        occupancy = rng.randint(minimum, h)
        rows = rng.sample(range(h), occupancy)
        first_color = None
        for offset, row in enumerate(rows):
            if missing_index < len(missing):
                color = missing[missing_index]
                missing_index += 1
            else:
                color = palette[offset % k]
                if offset == 1 and k >= 2 and color == first_color:
                    color = palette[(palette.index(first_color) + 1) % k]
            grid[row][column] = color
            if offset == 0:
                first_color = color
    assert missing_index == len(missing), "constructive color capacity was violated"
    return grid


def _draw_from_degenerate(name, h=8, w=8):
    """Explicit rejection fixtures; full columns are erased, never identity."""
    grid = full_grid(h, w, 0)
    if name == "no_seeds":
        return grid
    for column in range(w):
        color = column % 9 + 1
        for row in (range(h) if name == "columns_already_full" else (0, h - 1)):
            grid[row][column] = color
    return grid


def _basic_errors(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    h, w = len(grid), len(grid[0])
    if not 3 <= h <= 18 or not 3 <= w <= 18:
        return ["grid dimensions must be 3..18"]
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be integer 0..9, excluding bool"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    errors = _basic_errors(grid)
    if errors:
        return errors
    if not any(sum(row[c] != 0 for row in grid) == 1 for c in range(len(grid[0]))):
        return ["no column has exactly one nonzero cell"]
    requested = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    observed = observe_overrides(grid)
    for name in ("grid_h", "grid_w", "columns", "palette_size", "n_distinct_colors"):
        if requested.get(name) is not None and observed[name] != requested[name]:
            errors.append(f"{name} requested {requested[name]}, observed {observed[name]}")
    return errors


def expected_output(grid):
    errors = _basic_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(len(grid), len(grid[0]), 0)
    for c in range(len(grid[0])):
        values = [row[c] for row in grid if row[c] != 0]
        if len(values) == 1:
            for row in output:
                row[c] = values[0]
    return output


def observe_overrides(grid):
    colors = len({value for row in grid for value in row if value != 0})
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "columns": sum(sum(row[c] != 0 for row in grid) == 1 for c in range(len(grid[0]))),
            "palette_size": colors, "n_distinct_colors": colors}


def strict_canonical_like(grid):
    return self_check(grid)


def _fill_columns(grid, predicate):
    output = full_grid(len(grid), len(grid[0]), 0)
    for c in range(len(grid[0])):
        values = [row[c] for row in grid if row[c] != 0]
        if predicate(values):
            for row in output:
                row[c] = values[0]
    return output


def _monochromatic_columns(grid):
    return _fill_columns(grid, lambda values: bool(values) and len(set(values)) == 1)


def _nonempty_columns(grid):
    return _fill_columns(grid, bool)


def _preserve_distractors(grid):
    filled = expected_output(grid)
    return [[filled[r][c] or grid[r][c] for c in range(len(grid[0]))] for r in range(len(grid))]


def _globally_unique_colors(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    return _fill_columns(grid, lambda values: len(values) == 1 and counts[values[0]] == 1)


def _seeded_rows(grid):
    return [[next(value for value in row if value != 0)] * len(row)
            if sum(value != 0 for value in row) == 1 else [0] * len(row) for row in grid]


def _identity(grid):
    return [row[:] for row in grid]


SEMANTIC_RIVALS = {
    "monochromatic_columns": _monochromatic_columns,
    "nonempty_columns": _nonempty_columns,
    "preserve_distractors": _preserve_distractors,
    "globally_unique_colors": _globally_unique_colors,
    "seeded_rows": _seeded_rows,
    "identity": _identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in (
    "monochromatic_columns", "nonempty_columns", "preserve_distractors", "globally_unique_colors")}
SEMANTIC_WITNESSES = {name: (lambda grid, name=name: SEMANTIC_RIVALS[name](grid) != expected_output(grid))
                      for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    if isinstance(query, dict):
        grid, answer = query["input"], query["output"]
    else:
        grid, answer = query, expected_output(query)
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(grid) != answer]
