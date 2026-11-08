"""Generator for ARC task 092360ee834f (Pick the Object with Area N).

Canonical rule
--------------
Count color-1 cells in row 0 to obtain ``k``.  In the body (rows 1+),
keep only color 3, enumerate 4-connected objects in row-major scan order,
and paint the first object with area ``k`` cyan (8) on a blank canvas.
If no object matches, return a blank canvas.

The ordinary generator deliberately varies header positions and includes green
area decoys.  Optional textures refute common shortcuts.  Explicit degenerate
textures are retained as rule probes but are not ordinary training draws.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "092360ee834f"
VERSION = "2.1.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "Scattered row-0 blue cells encode k; among 4-connected green body "
    "objects, the first row-major object of area k is retained alone and "
    "recolored cyan. Same-area non-green objects, body blue cells, and "
    "area decoys defeat color/count/location shortcuts."
)

EXAMPLES_NEEDED = 3
HELPFUL_TEXTURES = ("plain", "other_color", "body_one")
DEGENERATE_TEXTURES = ("no_header", "no_match", "multiple_match")
ALL_TEXTURES = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "target_size", "texture"}

INVARIANTS = [
    "row 0 contains exactly k color-1 cells at noncanonical positions",
    "row 1 is a blank separator",
    "ordinary draws contain at least one color-3 body object of area k",
    "body objects are 4-connected internally and halo-separated externally",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 8..12", "valid": "6..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware 9..13", "valid": "7..18"},
    "target_size": {"type": "int", "default": "difficulty-aware 2..5", "valid": "1..8"},
    "texture": {
        "type": "str",
        "default": "weighted helpful texture",
        "valid": "plain|other_color|body_one|no_header|no_match|multiple_match",
    },
}


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    w = len(grid[0])
    if len(grid) > 30 or w > 30:
        raise ValueError("grid dimensions must be at most 30")
    for row in grid:
        if type(row) is not list or len(row) != w:
            raise ValueError("grid must be rectangular")
        if any(type(v) is not int or not 0 <= v <= 9 for v in row):
            raise ValueError("grid cells must be exact integers in 0..9")
    return len(grid), w


def _neighbors4(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r - 1, c), (r, c - 1), (r, c + 1), (r + 1, c))


def _components_for_color(grid: list[list[int]], color: int, *, row_lo: int = 1) -> list[list[tuple[int, int]]]:
    h, w = _validate_grid(grid)
    remaining = {(r, c) for r in range(row_lo, h) for c in range(w) if grid[r][c] == color}
    components: list[list[tuple[int, int]]] = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        queue = deque([first])
        cells: list[tuple[int, int]] = []
        while queue:
            cell = queue.popleft()
            cells.append(cell)
            for nxt in _neighbors4(cell):
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
        components.append(sorted(cells))
    return components


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    """Return rule-relevant facts in the same scan order as the Racket rule."""
    h, w = _validate_grid(grid)
    target = sum(value == 1 for value in grid[0])
    green = _components_for_color(grid, 3, row_lo=1)
    matching = [cells for cells in green if len(cells) == target]
    same_size_other = 0
    for color in range(1, 10):
        if color == 3:
            continue
        same_size_other += sum(
            len(cells) == target
            for cells in _components_for_color(grid, color, row_lo=1)
        )
    return {
        "grid_h": h,
        "grid_w": w,
        "target_size": target,
        "green_components": green,
        "green_component_sizes": [len(cells) for cells in green],
        "green_component_count": len(green),
        "matching_green_components": matching,
        "matching_green_count": len(matching),
        "same_size_other_color_count": same_size_other,
        "body_blue_count": sum(grid[r][c] == 1 for r in range(1, h) for c in range(w)),
    }


def rule_mirror(grid: list[list[int]], *, match_order: str = "first") -> list[list[int]]:
    """Pure-Python mirror used for generator review and focused tests."""
    facts = analyze(grid)
    if match_order not in {"first", "last"}:
        raise ValueError("match_order must be first or last")
    out = full_grid(facts["grid_h"], facts["grid_w"], 0)
    matches = facts["matching_green_components"]
    if not matches:
        return out
    chosen = matches[0] if match_order == "first" else matches[-1]
    for r, c in chosen:
        out[r][c] = 8
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or lesson-hiding ordinary inputs.

    Degenerate textures intentionally fail one or more checks; they are explicit
    rule probes and are never sampled by the ordinary prior.
    """
    try:
        h, _ = _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if any(value not in (0, 1) for value in grid[0]):
        errors.append("row 0 may contain only background and color 1")
    if h < 2 or any(grid[1]):
        errors.append("row 1 must be a blank separator")
    facts = analyze(grid)
    if facts["target_size"] == 0:
        errors.append("row 0 has no color-1 cells")
    if facts["matching_green_count"] == 0:
        errors.append("no color-3 body object has the encoded area")
    if facts["green_component_count"] < 2:
        errors.append("need at least one green area decoy")
    return errors


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    """Recover the visible exact axes for generated fixtures."""
    facts = analyze(grid)
    if facts["target_size"] == 0:
        texture = "no_header"
    elif facts["matching_green_count"] == 0:
        texture = "no_match"
    elif facts["matching_green_count"] >= 2:
        texture = "multiple_match"
    elif facts["body_blue_count"]:
        texture = "body_one"
    elif facts["same_size_other_color_count"]:
        texture = "other_color"
    else:
        texture = "plain"
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "target_size": facts["target_size"],
        "texture": texture,
    }


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _grow(rng, size: int, *, max_h: int = 4, max_w: int = 4) -> tuple[tuple[int, int], ...]:
    for _ in range(256):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = sorted(
                nxt
                for cell in cells
                for nxt in _neighbors4(cell)
                if nxt not in cells
            )
            cells.add(frontier[rng.randrange(len(frontier))])
        shape = _normalize_shape(cells)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh <= max_h and sw <= max_w:
            return shape
    raise ValueError(f"could not grow compact shape of area {size}")


def _place(
    grid: list[list[int]],
    rng,
    shape: tuple[tuple[int, int], ...],
    color: int,
    occupied: set[tuple[int, int]],
    *,
    row_lo: int = 2,
    row_hi: int | None = None,
    col_lo: int = 0,
    col_hi: int | None = None,
) -> set[tuple[int, int]] | None:
    h, w = len(grid), len(grid[0])
    row_hi = h if row_hi is None else min(h, row_hi)
    col_hi = w if col_hi is None else min(w, col_hi)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = [
        (r0, c0)
        for r0 in range(row_lo, row_hi - sh + 1)
        for c0 in range(col_lo, col_hi - sw + 1)
    ]
    rng.shuffle(candidates)
    for r0, c0 in candidates:
        cells = {(r0 + r, c0 + c) for r, c in shape}
        halo = {
            (r + dr, c + dc)
            for r, c in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        }
        if halo & occupied:
            continue
        for r, c in cells:
            grid[r][c] = color
        occupied.update(cells)
        return cells
    return None


def _draw_axis(ctx, label: str, global_bounds: tuple[int, int], sampled_bounds: tuple[int, int]) -> int:
    override = ctx.overrides.get(label)
    if override is not None:
        return ctx.draw_int_strict(label, *global_bounds)
    return ctx.draw_int(label, *sampled_bounds)


def _sampled_bounds(difficulty) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (8, 9), (9, 11), (2, 3)
    if difficulty == "hard":
        return (12, 16), (14, 18), (5, 8)
    if difficulty == "medium":
        return (10, 13), (11, 15), (3, 6)
    return (8, 12), (9, 13), (2, 5)


def _header_columns(rng, width: int, count: int) -> list[int]:
    if count > width:
        raise ValueError(f"target_size {count} cannot fit in grid_w {width}")
    if count == width:
        return list(range(width))
    for _ in range(64):
        columns = sorted(rng.sample(range(width), count))
        if columns != list(range(count)) and columns != list(range(width - count, width)):
            return columns
    return sorted(rng.sample(range(width), count))


def _decoy_sizes(k: int) -> list[int]:
    result: list[int] = []
    for size in (k - 2, k - 1, k + 1, k + 2, 1, 2, 3, 4):
        if 1 <= size <= 8 and size != k and size not in result:
            result.append(size)
    return result[:3]


def _build_scene(ctx, h: int, w: int, k: int, texture: str) -> list[list[int]]:
    rng = ctx.draw_rng("layout")
    for attempt in range(128):
        # Derive a deterministic retry stream without touching global RNG.
        local = ctx.draw_rng(f"layout-retry-{attempt}") if attempt else rng
        grid = full_grid(h, w, 0)
        header_k = 0 if texture == "no_header" else k
        for c in _header_columns(local, w, header_k):
            grid[0][c] = 1
        occupied: set[tuple[int, int]] = set()

        wanted_matches = 0 if texture in {"no_header", "no_match"} else (2 if texture == "multiple_match" else 1)
        okay = True
        for _ in range(wanted_matches):
            if _place(grid, local, _grow(local, k), 3, occupied) is None:
                okay = False
                break
        if not okay:
            continue

        placed_decoys = 0
        for size in _decoy_sizes(k):
            if _place(grid, local, _grow(local, size), 3, occupied) is not None:
                placed_decoys += 1
        if placed_decoys < 1:
            continue

        if texture == "other_color":
            if _place(grid, local, _grow(local, k), local.choice([2, 4, 5, 6, 7, 9]), occupied) is None:
                continue
        elif texture == "body_one":
            if _place(grid, local, ((0, 0),), 1, occupied) is None:
                continue

        facts = analyze(grid)
        if facts["target_size"] != header_k:
            continue
        if texture == "no_match" and facts["matching_green_count"] != 0:
            continue
        if texture == "multiple_match" and facts["matching_green_count"] < 2:
            continue
        if texture in HELPFUL_TEXTURES and facts["matching_green_count"] != 1:
            continue
        return grid
    raise ValueError(
        f"could not construct {h}x{w} target_size={k} texture={texture} after bounded retries"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    hb, wb, kb = _sampled_bounds(difficulty)
    h = _draw_axis(ctx, "grid_h", (6, 16), hb)
    w = _draw_axis(ctx, "grid_w", (7, 18), wb)
    k = _draw_axis(ctx, "target_size", (1, 8), kb)
    if k > w:
        raise ValueError(f"target_size {k} cannot exceed grid_w {w}")

    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", ALL_TEXTURES)
    else:
        texture = ctx.draw_choice("texture", ("plain", "plain", "other_color", "body_one"))
    return _build_scene(ctx, h, w, k, texture)
