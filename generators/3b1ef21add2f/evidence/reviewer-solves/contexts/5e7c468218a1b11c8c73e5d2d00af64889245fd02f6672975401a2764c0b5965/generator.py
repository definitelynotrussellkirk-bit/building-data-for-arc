"""Contrastful lessons for simultaneous recoloring of every red 2x2 window.

The selected Racket rule remains the label authority. Python transformations
below are deliberately wrong diagnostic rivals, never exported reference labels.
The sampler is a bounded teaching grammar; self_check is broader than its support
but narrower than the total rule domain. See notes.md for that distinction.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers import grid as grid_helpers, objects as object_helpers
from puzzle_generators.helpers.grid import (
    clone_grid, draw_rect, full_grid, occurrences, paint_cells,
    paste, rot90_cw,
)
from puzzle_generators.helpers.objects import find_objects, to_indices

GENERATOR_ID = TASK_ID = "3b1ef21add2f"
VERSION = "3.0.0"
RULE_HASH = "200a2c36d86e"
SUMMARY = (
    "Recolor to 3 the union of all complete color-2 2x2 windows in the original "
    "input. Preserve all other cells, including attached red tails and nonred "
    "squares. Lessons mix isolated squares with overlapping windows, unequal "
    "red components, hollow red rings, and unchanged nonred squares."
)
INVARIANTS = [
    "zero background and at least two four-connected red components",
    "any scene with red windows also has uncovered red cells",
    "n_windows counts every original red 2x2 neighborhood, including overlaps",
    "every four consecutive default draws contain an anchor and at least two rich scenes",
]
AXES = {
    "grid_h": {"type": "int", "default": "profile/band 7..16", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "profile/band 7..16", "valid": "7..16"},
    "n_windows": {"type": "int", "default": "anchor 1..2; rich 3..8", "valid": "0..8"},
}
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("two_colors", "rich_contrast")


def _red_windows(grid):
    return occurrences(grid, [[2, 2], [2, 2]])


def _window_cells(grid):
    return {(r + dr, c + dc) for r, c in _red_windows(grid)
            for dr in (0, 1) for dc in (0, 1)}


def _red_components(grid):
    found = find_objects(grid, univalued=True, diagonal=False,
                         without_bg=True, bg=0)
    return [to_indices(part) for part in found if object_helpers.obj_color(part) == 2]


def rule_grid_errors(grid):
    """Validate the broad rectangular digit-grid domain, without lesson claims."""
    if type(grid) is not list or not grid:
        return ["expected a nonempty list of rows"]
    if any(type(row) is not list or not row for row in grid):
        return ["expected nonempty list rows"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["grid dimensions must be 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["pixels must be exact integers in 0..9 (not bool)"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Select contrastful teaching inputs, not all inputs the rule can label."""
    errors = rule_grid_errors(grid)
    if errors:
        return errors
    palette = {value for row in grid for value in row}
    if not {0, 2} <= palette:
        errors.append("teaching scenes require zero background and red cells")
    components = _red_components(grid)
    if len(components) < 2:
        errors.append("teaching scenes require at least two red components")
    covered = _window_cells(grid)
    if covered and not any(part - covered for part in components):
        errors.append("a scene with windows must also show unchanged red cells")
    return errors


def observe_overrides(grid):
    """Observe the three exact axes from pixels, independent of draw metadata."""
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_windows": len(_red_windows(grid))}


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[0 if sample_index % LESSON_SCHEDULE_PERIOD == 0 else 1]


def _simple_tile(count):
    tile = full_grid(7, 7, 0)
    for row, col in ((0, 0), (0, 5), (5, 0), (5, 5))[:count]:
        draw_rect(tile, row, col, 2, 2, 2)
    paint_cells(tile, ((3, 3), (3, 4), (4, 3)), 2)
    if count == 0:
        paint_cells(tile, ((0, 0), (0, 1), (1, 0)), 2)
    return tile


def _rich_tile(count, rng, *, foreign_square):
    tile = full_grid(7, 7, 0)
    primary_count = max(0, count - 1) if count != 1 else 1
    # These row lengths have exactly k windows. For k>=2 their covered union
    # cannot be tiled by disjoint 2x2s; every orientation defeats an in-place scan.
    lengths = {
        0: (2, 1), 1: (2, 2), 2: (3, 3), 3: (3, 3, 2),
        4: (3, 3, 3), 5: (4, 4, 3), 6: (4, 4, 4), 7: (5, 5, 4),
    }[primary_count]
    for row, width in enumerate(lengths):
        draw_rect(tile, row, 0, 1, width, 2)
    tile[len(lengths)][0] = 2  # attached tail adds no window
    if count >= 2:
        draw_rect(tile, 5, 0, 2, 2, 2)
    else:
        paint_cells(tile, ((5, 0), (5, 1), (6, 0)), 2)
    # A hollow ring has a red graph cycle but no complete red 2x2. It defeats
    # the otherwise surviving shortcut "remove red leaves, recolor the rest".
    ring = [(row, col) for row in range(4, 7) for col in range(4, 7)
            if row != 5 or col != 5]
    paint_cells(tile, ring, 2)
    tail = rng.choice(((), ((4, 3),), ((3, 6),)))
    paint_cells(tile, tail, 2)
    if foreign_square:
        draw_rect(tile, 0, 5, 2, 2, rng.choice((1, 4, 5, 6, 7, 8, 9)))
    return tile


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or obsolete override(s): {sorted(unknown)}")
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    anchor = schedule_profile(seed, sample_index, difficulty) == "two_colors"
    default_max = 8 if anchor else {"easy": 10, "medium": 13, "hard": 16}[band]
    height = ctx.draw_int_strict("grid_h", 7,
                                16 if overrides.get("grid_h") is not None else default_max)
    width = ctx.draw_int_strict("grid_w", 7,
                               16 if overrides.get("grid_w") is not None else default_max)
    lower, upper = ((1, 2) if anchor else
                    {"easy": (3, 4), "medium": (3, 6), "hard": (4, 8)}[band])
    if overrides.get("n_windows") is not None:
        lower, upper = 0, 8
    count = ctx.draw_int_strict("n_windows", lower, upper)
    rng = ctx.draw_rng("motif_and_placement")
    tile = (_simple_tile(count) if anchor and count <= 4 else
            _rich_tile(count, rng, foreign_square=not anchor))
    for _ in range(rng.randrange(4)):
        tile = rot90_cw(tile)
    if rng.randrange(2):
        tile = grid_helpers.flip_lr(tile)
    grid = full_grid(height, width, 0)
    paste(grid, tile, rng.randrange(height - 6), rng.randrange(width - 6))
    return grid


def strict_canonical_like(grid):
    """Actual canonical envelope: small, two-color, isolated red squares."""
    errors = self_check(grid)
    if errors:
        return errors
    if not (7 <= len(grid) <= 8 and 7 <= len(grid[0]) <= 8):
        return ["outside canonical 7..8 dimensions"]
    if {value for row in grid for value in row} != {0, 2}:
        return ["outside canonical two-color input palette"]
    covered = _window_cells(grid)
    if not 1 <= len(_red_windows(grid)) <= 2:
        return ["canonical inputs show one or two windows"]
    if any(part & covered and (len(part) != 4 or part != part & covered)
           for part in _red_components(grid)):
        return ["canonical windows are isolated 2x2 red components"]
    return []


def _paint_green(grid, cells):
    output = clone_grid(grid)
    paint_cells(output, cells, 3)
    return output


def _exact_components(grid):
    covered = _window_cells(grid)
    cells = set().union(*(part for part in _red_components(grid)
                          if len(part) == 4 and part <= covered))
    return _paint_green(grid, cells)


def _large_components(grid):
    cells = set().union(*(part for part in _red_components(grid) if len(part) >= 4))
    return _paint_green(grid, cells)


def _greedy_windows(grid):
    output = clone_grid(grid)
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            if all(output[row + dr][col + dc] == 2
                   for dr in (0, 1) for dc in (0, 1)):
                draw_rect(output, row, col, 2, 2, 3)
    return output


def _largest_window_components(grid):
    covered = _window_cells(grid)
    qualifying = [part for part in _red_components(grid) if part & covered]
    largest = max((len(part) for part in qualifying), default=0)
    cells = set().union(*(part & covered for part in qualifying if len(part) == largest))
    return _paint_green(grid, cells)


def _any_color_windows(grid):
    cells = set()
    for color in range(1, 10):
        for row, col in occurrences(grid, [[color, color], [color, color]]):
            cells.update((row + dr, col + dc) for dr in (0, 1) for dc in (0, 1))
    return _paint_green(grid, cells)


def _all_red(grid):
    return [[3 if value == 2 else value for value in row] for row in grid]


def _red_core_cells(grid):
    """Wrong-rule observation: the red four-neighbor graph's 2-core."""
    active = set().union(*_red_components(grid))
    while active:
        leaves = {(row, col) for row, col in active
                  if sum(cell in active for cell in ((row - 1, col), (row + 1, col),
                                                    (row, col - 1), (row, col + 1))) < 2}
        if not leaves:
            break
        active -= leaves
    return active


def _red_two_core(grid):
    return _paint_green(grid, _red_core_cells(grid))


CANONICAL_SHORTCUTS = {
    "exact_2x2_components": _exact_components,
    "components_mass_at_least4": _large_components,
    "greedy_inplace_windows": _greedy_windows,
    "largest_window_components": _largest_window_components,
    "any_color_windows": _any_color_windows,
    "red_two_core": _red_two_core,
}
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS, "all_red": _all_red}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _attached_tail(grid):
    covered = _window_cells(grid)
    return any(bool(part & covered) and bool(part - covered)
               for part in _red_components(grid))


def _snapshot_required(grid):
    greedy = _greedy_windows(grid)
    return any(greedy[row][col] != 3 for row, col in _window_cells(grid))


def _unequal_window_components(grid):
    covered = _window_cells(grid)
    sizes = {len(part) for part in _red_components(grid) if part & covered}
    return len(sizes) > 1


def _large_nonwindow_component(grid):
    covered = _window_cells(grid)
    return any(len(part) >= 4 and not part & covered for part in _red_components(grid))


def _nonred_square(grid):
    return any(bool(occurrences(grid, [[color, color], [color, color]]))
               for color in (1, 4, 5, 6, 7, 8, 9))


def _uncovered_red_cycle(grid):
    return bool(_red_core_cells(grid) - _window_cells(grid))


SEMANTIC_WITNESSES = {
    "attached_red_survives": _attached_tail,
    "overlap_requires_snapshot": _snapshot_required,
    "unequal_window_components": _unequal_window_components,
    "large_red_without_window": _large_nonwindow_component,
    "nonred_square_preserved": _nonred_square,
    "red_cycle_without_window": _uncovered_red_cycle,
}
WITNESS_RIVALS = {
    "attached_red_survives": ["exact_2x2_components", "components_mass_at_least4", "all_red"],
    "overlap_requires_snapshot": ["greedy_inplace_windows"],
    "unequal_window_components": ["largest_window_components"],
    "large_red_without_window": ["components_mass_at_least4"],
    "nonred_square_preserved": ["any_color_windows"],
    "red_cycle_without_window": ["red_two_core"],
}


def lesson_identifiable(demos, query):
    """Finite named-rival test using the supplied authoritative pair labels."""
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]

