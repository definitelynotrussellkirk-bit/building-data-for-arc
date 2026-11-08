"""Generator for arc_puzzle_bank_eleventh21:M72 — recolor by size palette.

Canonical rule: read the nonzero, non-orange cells in row 0 from left to
right.  Every 4-connected orange (7) component in the body is recolored by
its area: area 1 uses the first legend color, area 2 the second, and so on.
Non-orange body decoration is unchanged.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import has_neighbor
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "01f4294de005"
VERSION = "1.4.0"
TASK_ID = "01f4294de005"
SUMMARY = (
    "Row 0 holds an N-color legend at scattered columns (order = "
    "column order); below, orange(7) blobs of sizes 1..N are recolored "
    "to legend[size-1], while non-7 decor blobs stay unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "row 0 has N legend cells (colors not in {0,7}) at scattered columns",
    "every 7-blob in rows 1+ has size in 1..N",
    "non-7 body decoration is left unchanged",
    ">=1 7-blob exists",
    "row 1 is sometimes occupied and sometimes blank across ordinary draws",
]


AXES = {
    "grid_h": {"type": "int", "default": "rng 7..10 (hard 9..12)",
               "valid": "6..14", "doc": "Grid height."},
    "grid_w": {"type": "int", "default": "rng 9..12 (hard 11..14)",
               "valid": "8..14", "doc": "Grid width."},
    "n_legend": {"type": "int", "default": "rng 3..4 (hard 3..5)",
                 "valid": "2..5", "doc": "Legend colors in row 0."},
    "n_blobs": {"type": "int", "default": "rng 2..4", "valid": "1..5",
                 "doc": "Orange components below row 0."},
    "decoy": {"type": "int", "default": "rng 0|1", "valid": "0|1",
              "doc": "Whether to add an unchanged non-orange body object."},
    "top_contact": {"type": "int", "default": "rng 0|1", "valid": "0|1",
                    "doc": "Whether at least one body object occupies row 1."},
}

_PALETTE_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer; bool is forbidden")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer; bool is forbidden")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_h", 6, 14),
        ("grid_w", 8, 14),
        ("n_legend", 2, 5),
        ("n_blobs", 1, 5),
        ("decoy", 0, 1),
        ("top_contact", 0, 1),
    ):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an exact integer in [{lo}, {hi}]")


def _banded_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _draw_axes(ctx, difficulty, overrides):
    if difficulty == "easy":
        h_bounds, w_bounds, n_bounds = (7, 8), (9, 10), (2, 3)
    elif difficulty == "hard":
        h_bounds, w_bounds, n_bounds = (9, 12), (11, 14), (3, 5)
    else:
        h_bounds, w_bounds, n_bounds = (7, 10), (9, 12), (3, 4)
    h = _banded_int(ctx, overrides, "grid_h", *h_bounds, 6, 14)
    w = _banded_int(ctx, overrides, "grid_w", *w_bounds, 8, 14)
    n = _banded_int(ctx, overrides, "n_legend", *n_bounds, 2, 5)
    n_blobs = _banded_int(ctx, overrides, "n_blobs", 2, 4, 1, 5)
    decoy = ctx.draw_int_strict("decoy", 0, 1)
    if overrides.get("top_contact") is not None:
        top_contact = ctx.draw_int_strict("top_contact", 0, 1)
    else:
        top_contact = ctx.draw_int_strict("top_contact", 0, 1)
    return h, w, n, n_blobs, decoy, top_contact


def _grow_from_seed(rng, h: int, w: int, used: set[tuple[int, int]],
                    target_size: int, seed: tuple[int, int], *, min_row: int = 0):
    if not (min_row <= seed[0] < h and 0 <= seed[1] < w):
        return None
    if seed in used or has_neighbor(seed, used):
        return None
    cells = {seed}
    frontier = [seed]
    while frontier and len(cells) < target_size:
        index = rng.randrange(len(frontier))
        r, c = frontier.pop(index)
        directions = list(_CARDINAL)
        rng.shuffle(directions)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            candidate = (nr, nc)
            if not (min_row <= nr < h and 0 <= nc < w):
                continue
            if candidate in cells or candidate in used:
                continue
            if has_neighbor(candidate, used, ignore=cells):
                continue
            cells.add(candidate)
            frontier.append(candidate)
            if len(cells) == target_size:
                break
    return cells if len(cells) == target_size else None


def _place_blob(rng, h: int, w: int, used: set[tuple[int, int]], size: int,
                *, require_top: bool | None) -> set[tuple[int, int]]:
    min_row = 0 if require_top is not False else 1
    seeds = [(r, c) for r in range(min_row, h) for c in range(w)]
    if require_top is True:
        seeds = [(0, c) for c in range(w)]
    rng.shuffle(seeds)
    for seed in seeds:
        cells = _grow_from_seed(rng, h, w, used, size, seed, min_row=min_row)
        if cells is not None and (require_top is not True or any(r == 0 for r, _ in cells)):
            return cells
    raise ValueError(
        f"cannot place isolated blob of size {size} in {h}x{w} body "
        f"with require_top={require_top}"
    )



def _place_scene_objects(rng, body_h: int, width: int, sizes: list[int],
                         want_decoy: int, legend_palette: list[int],
                         top_contact: int):
    """Place every requested component or fail only after whole-scene retries.

    A greedy layout can strand the final component even when the requested
    combination is feasible.  Restarting the complete body fixes that source
    of order-dependent rejection while keeping every component isolated.
    """
    for _attempt in range(256):
        used: set[tuple[int, int]] = set()
        blobs: list[set[tuple[int, int]]] = []
        order = sorted(sizes, reverse=True)
        if top_contact:
            # The first (largest) object is forced against the legend boundary;
            # the remainder may use any body row.
            requirements = [True] + [None] * (len(order) - 1)
        else:
            requirements = [False] * len(order)
        try:
            for size, requirement in zip(order, requirements):
                cells = _place_blob(
                    rng, body_h, width, used, size,
                    require_top=requirement,
                )
                used |= cells
                blobs.append(cells)
            decoy = None
            if want_decoy:
                candidates = [
                    color for color in _PALETTE_COLORS
                    if color not in legend_palette
                ]
                decoy_color = rng.choice(candidates or [9])
                decoy_cells = _place_blob(
                    rng, body_h, width, used, 2,
                    require_top=None if top_contact else False,
                )
                decoy = (decoy_color, decoy_cells)
            return blobs, decoy
        except ValueError:
            continue
    raise ValueError(
        f"cannot place {len(sizes)} isolated orange blobs"
        f"{' plus a decoy' if want_decoy else ''} in {body_h}x{width} body"
    )

def _components(grid: list[list[int]], color: int, *, row_start: int = 0):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(row_start, h)
        for c in range(w)
        if grid[r][c] == color
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h, w, n, n_blobs, want_decoy, top_contact = _draw_axes(ctx, difficulty, overrides)
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    legend_cols = sorted(rng.sample(range(w), n))
    legend_palette = rng.sample(list(_PALETTE_COLORS), n)
    for col, color in zip(legend_cols, legend_palette):
        grid[0][col] = color

    body_h = h - 1
    sizes = [1 + ((sample_index + offset) % n) for offset in range(n_blobs)]
    rng.shuffle(sizes)
    blobs, decoy = _place_scene_objects(
        rng, body_h, w, sizes, want_decoy, legend_palette, top_contact
    )
    for cells in blobs:
        for row, col in cells:
            grid[row + 1][col] = 7
    if decoy is not None:
        decoy_color, cells = decoy
        for row, col in cells:
            grid[row + 1][col] = decoy_color

    # Assert the requested public axes are represented; never silently return a
    # lower object count after a failed random placement.
    observed = semantic_observables(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_legend": n,
        "n_blobs": n_blobs,
        "decoy": int(bool(want_decoy)),
        "top_contact": int(bool(top_contact)),
    }
    if observed != expected:
        raise RuntimeError(f"generated axes drifted: expected {expected}, observed {observed}")
    return grid


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if not 2 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be within ARC bounds and include a body")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integers in 0..9; bool is forbidden")
    return len(grid), width


def semantic_observables(grid: list[list[int]]) -> dict[str, int]:
    _validate_grid(grid)
    legend = [value for value in grid[0] if value not in (0, 7)]
    blobs = _components(grid, 7, row_start=1)
    body_nonorange = {
        value
        for row in grid[1:]
        for value in row
        if value not in (0, 7)
    }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_legend": len(legend),
        "n_blobs": len(blobs),
        "decoy": int(bool(body_nonorange)),
        "top_contact": int(any(value != 0 for value in grid[1])),
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    return semantic_observables(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    _validate_grid(grid)
    palette = [value for value in grid[0] if value != 0]
    if not palette:
        raise ValueError("legend row is empty")
    output = [row[:] for row in grid]
    for component in _components(grid, 7, row_start=1):
        size = len(component)
        if not 1 <= size <= len(palette):
            raise ValueError("orange component size is outside the legend")
        color = palette[size - 1]
        for row, col in component:
            output[row][col] = color
    return output


def self_check(grid, *, difficulty=None, meta=None):
    messages = []
    try:
        h, w = _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    if any(value == 7 for value in grid[0]):
        messages.append("row 0 contains orange; orange is reserved for body components")
    legend_cols = [col for col in range(w) if grid[0][col] not in (0, 7)]
    if not legend_cols:
        messages.append("row 0 has no legend cells (non-{0,7} colors)")
    n = len(legend_cols)
    blobs = _components(grid, 7, row_start=1)
    if not blobs:
        messages.append("no color-7 blob in body rows (rule needs >=1 to recolor)")
    elif n:
        for index, blob in enumerate(blobs):
            size = len(blob)
            if not 1 <= size <= n:
                messages.append(
                    f"7-blob {index} size {size} outside 1..{n} "
                    "(legend length; rule would crash)"
                )
    return messages
