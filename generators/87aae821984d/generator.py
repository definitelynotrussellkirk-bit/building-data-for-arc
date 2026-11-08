"""Generator for ARC task ``87aae821984d``.

The authoritative rule counts yellow (4) cells, extracts every cyan (8) cell,
right/bottom-aligns the cyan motif in a 3x3 tile (equivalently pads a smaller
bounding box on its top and left), and repeats that tile horizontally once per
yellow cell.  Cyan cells are a single logical motif; they need not form one
4-connected component.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87aae821984d"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "6f52927247b0"

SUMMARY = (
    "Place one cyan motif with a 2x2, 2x3, 3x2, or 3x3 tight bounding box and "
    "one to five isolated yellow counter cells. Count the yellow cells; "
    "right/bottom-align all cyan cells in a 3x3 tile, padding smaller cyan "
    "bounding boxes on the top and/or left, then repeat that tile horizontally "
    "once per yellow cell. Connectivity of the cyan motif is irrelevant."
)

INVARIANTS = [
    "only colours 0, 4, and 8 occur",
    "one logical cyan motif has 3..8 cells in a 2..3 by 2..3 tight bounding box",
    "cyan connectivity is not semantic and disconnected canonical motifs are valid",
    "one to five yellow cells are pairwise isolated and isolated from cyan",
    "the output tile is always 3x3 and is aligned to the motif's bottom-right",
    "the canonical Racket program, pinned by RULE_HASH, is the output authority",
]

SHAPE_KINDS = ("span_3x3", "pad_top", "pad_left", "pad_top_left")
_SHAPE_DIMS = {
    "span_3x3": (3, 3),
    "pad_top": (2, 3),
    "pad_left": (3, 2),
    "pad_top_left": (2, 2),
}
_DIMS_TO_KIND = {dims: name for name, dims in _SHAPE_DIMS.items()}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9..14", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "scheduled 9..14", "valid": "9..14"},
    "n_4_cells": {"type": "int", "default": "scheduled 1..4", "valid": "1..5"},
    "shape_kind": {
        "type": "str",
        "default": "four-profile schedule",
        "valid": "|".join(SHAPE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_PROFILE_NAMES = (
    "span_fragmented_canonical",
    "pad_top_connected",
    "pad_left_fragmented",
    "pad_top_left_connected",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
LESSON_SCHEDULE_PERIOD = len(_PROFILE_NAMES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

Grid = list[list[int]]
Cell = tuple[int, int]


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the four-period teaching profile used by an ordinary draw."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _profile_index(sample_index: int) -> int:
    return int(sample_index) % LESSON_SCHEDULE_PERIOD


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int, int, str, bool]:
    """Return height, width, counter count, bbox class, fragmented preference."""
    index = _profile_index(sample_index)
    # The first residue pins exact canonical size/palette support in every band.
    if index == 0:
        return 9, 9, 1, "span_3x3", True
    if index == 1:
        return 9, 9, 2, "pad_top", False

    dims_by_band = {
        "easy": ((9, 10), (10, 9), (10, 10)),
        "medium": ((11, 12), (12, 11), (12, 12)),
        "hard": ((13, 14), (14, 13), (14, 14)),
        None: ((10, 12), (12, 10), (12, 12)),
    }
    band_dims = dims_by_band.get(difficulty, dims_by_band[None])
    h, w = band_dims[index - 1]
    defaults = (
        (1, "span_3x3", True),
        (2, "pad_top", False),
        (3, "pad_left", True),
        (4, "pad_top_left", False),
    )
    n_4, kind, fragmented = defaults[index]
    return h, w, n_4, kind, fragmented


def _validate_difficulty(difficulty) -> None:
    if difficulty is None or difficulty in {"easy", "medium", "hard"}:
        return
    if type(difficulty) in {int, float} and not isinstance(difficulty, bool):
        return
    raise ValueError("difficulty must be None, easy, medium, hard, or a numeric hint")


def _validate_override_types(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    for name in ("grid_h", "grid_w", "n_4_cells"):
        if name in overrides and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an integer (not bool/float/string/None)")
    if "shape_kind" in overrides and type(overrides["shape_kind"]) is not str:
        raise TypeError("shape_kind override must be a string")


def _scheduled_int(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _scheduled_choice(ctx, overrides, name: str, default: str, choices: tuple[str, ...]) -> str:
    if name in overrides:
        return ctx.draw_choice(name, choices)
    return ctx.draw_choice(name, (default,))


def _is_connected(cells: tuple[Cell, ...] | set[Cell]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    reached = {stack[0]}
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in remaining and nxt not in reached:
                reached.add(nxt)
                stack.append(nxt)
    return reached == remaining


@lru_cache(maxsize=None)
def _mask_pool(shape_kind: str, fragmented: bool) -> tuple[tuple[Cell, ...], ...]:
    h, w = _SHAPE_DIMS[shape_kind]
    universe = tuple((r, c) for r in range(h) for c in range(w))
    masks: list[tuple[Cell, ...]] = []
    for size in range(3, min(8, len(universe)) + 1):
        for selected in combinations(universe, size):
            rows = {r for r, _ in selected}
            cols = {c for _, c in selected}
            if not ({0, h - 1} <= rows and {0, w - 1} <= cols):
                continue
            if _is_connected(selected) == fragmented:
                continue
            masks.append(tuple(selected))
    return tuple(masks)


def _choose_mask(ctx, shape_kind: str, fragmented: bool, canonical_profile: bool) -> tuple[Cell, ...]:
    pool = list(_mask_pool(shape_kind, fragmented))
    if not pool:
        # Some tiny boxes (notably 2x2) cannot be disconnected. Overrides remain
        # universally constructive; only the ordinary teaching schedule promises
        # fragmentation at the two profiles where it is realizable.
        pool = list(_mask_pool(shape_kind, not fragmented))
    if canonical_profile:
        narrowed = [mask for mask in pool if 4 <= len(mask) <= 6]
        if narrowed:
            pool = narrowed
    if not pool:
        raise RuntimeError(f"no legal masks for {shape_kind}, fragmented={fragmented}")
    return tuple(ctx.draw_rng("shape_mask").choice(pool))


def _counter_candidates(h: int, w: int, shape: set[Cell], n: int, rng) -> list[Cell] | None:
    viable_phases: list[list[Cell]] = []
    for row_phase in (0, 1):
        for col_phase in (0, 1):
            cells = []
            for r in range(row_phase, h, 2):
                for c in range(col_phase, w, 2):
                    if all(max(abs(r - sr), abs(c - sc)) > 1 for sr, sc in shape):
                        cells.append((r, c))
            if len(cells) >= n:
                viable_phases.append(cells)
    if not viable_phases:
        return None
    cells = list(rng.choice(viable_phases))
    rng.shuffle(cells)
    return cells[:n]


def _construct_layout(
    h: int, w: int, local_mask: tuple[Cell, ...], n_4: int, ctx
) -> tuple[set[Cell], list[Cell]]:
    sh = max(r for r, _ in local_mask) + 1
    sw = max(c for _, c in local_mask) + 1
    origins = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    origin_rng = ctx.draw_rng("shape_origin")
    origin_rng.shuffle(origins)
    counter_rng = ctx.draw_rng("counter_layout")
    for row0, col0 in origins:
        shape = {(row0 + r, col0 + c) for r, c in local_mask}
        counters = _counter_candidates(h, w, shape, n_4, counter_rng)
        if counters is not None:
            return shape, counters
    raise RuntimeError("no constructive placement for a legal override combination")


def _grid_structure(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return len(grid), width, [f"cell ({r},{c}) is not an ARC colour integer 0..9"]
    return len(grid), width, []


def _cells_of(grid: Grid, colour: int) -> set[Cell]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == colour
    }


def _bbox(cells: set[Cell]) -> tuple[int, int, int, int] | None:
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(cells: set[Cell]) -> list[set[Cell]]:
    remaining = set(cells)
    result: list[set[Cell]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical manifold and reject malformed/rule-hiding inputs."""
    del difficulty, meta
    h, w, issues = _grid_structure(grid)
    if issues:
        return issues
    if not (9 <= h <= 14):
        issues.append(f"height {h} outside supported range 9..14")
    if not (9 <= w <= 14):
        issues.append(f"width {w} outside supported range 9..14")

    colours = {value for row in grid for value in row}
    illegal = sorted(colours - {0, 4, 8})
    if illegal:
        issues.append(f"unsupported colours {illegal}; expected only 0, 4, 8")
    if 0 not in colours:
        issues.append("background colour 0 is required")

    fours = _cells_of(grid, 4)
    eights = _cells_of(grid, 8)
    if not (1 <= len(fours) <= 5):
        issues.append(f"expected 1..5 yellow counter cells, found {len(fours)}")
    if not (3 <= len(eights) <= 8):
        issues.append(f"expected 3..8 cyan motif cells, found {len(eights)}")

    bounds = _bbox(eights)
    if bounds is not None:
        r1, c1, r2, c2 = bounds
        dims = (r2 - r1 + 1, c2 - c1 + 1)
        if dims not in _DIMS_TO_KIND:
            issues.append(f"cyan tight bounding box {dims} is not one of {sorted(_DIMS_TO_KIND)}")
        if dims == (3, 3) and len(eights) == 9:
            issues.append("solid 3x3 cyan block hides motif geometry")

    for r, c in fours:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nxt = (r + dr, c + dc)
                if nxt in fours or nxt in eights:
                    issues.append("yellow counter cells must be isolated from all yellow/cyan cells")
                    return issues
    return issues


def strict_canonical_like(grid) -> list[str]:
    """Empirical strict subset shared by all seven labelled canonical pairs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    colours = {value for row in grid for value in row}
    if (len(grid), len(grid[0]), colours) != (9, 9, {0, 4, 8}):
        reasons.append("strict canonical profile is exactly 9x9 with palette {0,4,8}")
    if len(_cells_of(grid, 4)) > 4:
        reasons.append("canonical inputs contain at most four yellow counters")
    if not (4 <= len(_cells_of(grid, 8)) <= 6):
        reasons.append("canonical cyan motifs contain four to six cells")
    return reasons


def _canonical_tile_from_cells(cells: set[Cell]) -> Grid:
    bounds = _bbox(cells)
    if bounds is None:
        raise ValueError("at least one cyan cell is required")
    _, _, r2, c2 = bounds
    return [
        [8 if (r2 - 2 + r, c2 - 2 + c) in cells else 0 for c in range(3)]
        for r in range(3)
    ]


def _repeat_tile(tile: Grid, repeats: int) -> Grid:
    return [list(row) * repeats for row in tile]


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests/contracts; Racket remains authority."""
    eights = _cells_of(grid, 8)
    tile = _canonical_tile_from_cells(eights)
    return _repeat_tile(tile, len(_cells_of(grid, 4)))


def observe_overrides(grid) -> dict[str, Any]:
    if self_check(grid):
        return {}
    eights = _cells_of(grid, 8)
    r1, c1, r2, c2 = _bbox(eights)  # type: ignore[misc]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_4_cells": len(_cells_of(grid, 4)),
        "shape_kind": _DIMS_TO_KIND[(r2 - r1 + 1, c2 - c1 + 1)],
    }


def _top_left_alignment(grid: Grid) -> Grid:
    eights = _cells_of(grid, 8)
    r1, c1, r2, c2 = _bbox(eights)  # type: ignore[misc]
    sh, sw = r2 - r1 + 1, c2 - c1 + 1
    tile = [[0] * 3 for _ in range(3)]
    for r in range(sh):
        for c in range(sw):
            if (r1 + r, c1 + c) in eights:
                tile[r][c] = 8
    return _repeat_tile(tile, len(_cells_of(grid, 4)))


def _tight_bbox_tile(grid: Grid) -> Grid:
    eights = _cells_of(grid, 8)
    r1, c1, r2, c2 = _bbox(eights)  # type: ignore[misc]
    tile = [
        [8 if (r, c) in eights else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]
    return _repeat_tile(tile, len(_cells_of(grid, 4)))


def _fixed_repeat(grid: Grid, repeats: int) -> Grid:
    return _repeat_tile(_canonical_tile_from_cells(_cells_of(grid, 8)), repeats)


def _fixed_one_repeat(grid: Grid) -> Grid:
    return _fixed_repeat(grid, 1)


def _fixed_three_repeats(grid: Grid) -> Grid:
    return _fixed_repeat(grid, 3)


def _largest_component_only(grid: Grid) -> Grid:
    components = _components(_cells_of(grid, 8))
    component = min(components, key=lambda cells: (-len(cells), min(cells)))
    return _repeat_tile(_canonical_tile_from_cells(component), len(_cells_of(grid, 4)))


def _left_align_narrow_motif(grid: Grid) -> Grid:
    """Plausible shortcut: bottom-align vertically, but pad narrow motifs right."""
    eights = _cells_of(grid, 8)
    r1, c1, r2, c2 = _bbox(eights)  # type: ignore[misc]
    sh, sw = r2 - r1 + 1, c2 - c1 + 1
    tile = [[0] * 3 for _ in range(3)]
    row0 = 3 - sh
    for r, c in eights:
        tile[row0 + (r - r1)][c - c1] = 8
    return _repeat_tile(tile, len(_cells_of(grid, 4)))


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "top_left_alignment": _top_left_alignment,
    "tight_bbox_without_3x3_padding": _tight_bbox_tile,
    "fixed_one_repeat": _fixed_one_repeat,
    "fixed_three_repeats": _fixed_three_repeats,
    "largest_connected_component_only": _largest_component_only,
    "left_align_narrow_motif": _left_align_narrow_motif,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Canonical motifs always span all three columns, so horizontal padding is not
# identified there. Retain the strongest fitting shortcut as executable code.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {
    "left_align_narrow_motif": _left_align_narrow_motif,
}


def _valid_and(predicate: Callable[[Grid], bool], grid: Grid) -> bool:
    return not self_check(grid) and predicate(grid)


def _witness_padding(grid: Grid) -> bool:
    return _valid_and(lambda g: observe_overrides(g)["shape_kind"] != "span_3x3", grid)


def _witness_not_one(grid: Grid) -> bool:
    return _valid_and(lambda g: len(_cells_of(g, 4)) != 1, grid)


def _witness_not_three(grid: Grid) -> bool:
    return _valid_and(lambda g: len(_cells_of(g, 4)) != 3, grid)


def _witness_fragmented(grid: Grid) -> bool:
    return _valid_and(lambda g: len(_components(_cells_of(g, 8))) > 1, grid)


def _witness_left_padding(grid: Grid) -> bool:
    return _valid_and(
        lambda g: observe_overrides(g)["shape_kind"] in {"pad_left", "pad_top_left"},
        grid,
    )


SEMANTIC_WITNESSES = {
    "padded_shape": _witness_padding,
    "counter_count_not_one": _witness_not_one,
    "counter_count_not_three": _witness_not_three,
    "disconnected_cyan_motif": _witness_fragmented,
    "left_padded_shape": _witness_left_padding,
}
WITNESS_RIVALS = {
    "padded_shape": ["top_left_alignment", "tight_bbox_without_3x3_padding"],
    "counter_count_not_one": ["fixed_one_repeat"],
    "counter_count_not_three": ["fixed_three_repeats"],
    "disconnected_cyan_motif": ["largest_connected_component_only"],
    "left_padded_shape": ["left_align_narrow_motif"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that exact demos falsify every declared plausible rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    elif self_check(query["input"]):
        reasons.append("query input is outside the supported task domain")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the pinned rule")
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    _validate_override_types(overrides)
    default_h, default_w, default_n, default_kind, fragmented = _profile_defaults(
        sample_index, difficulty
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 9, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 9, 14)
    n_4 = _scheduled_int(ctx, overrides, "n_4_cells", default_n, 1, 5)
    shape_kind = _scheduled_choice(
        ctx, overrides, "shape_kind", default_kind, SHAPE_KINDS
    )

    local_mask = _choose_mask(
        ctx,
        shape_kind,
        fragmented,
        canonical_profile=_profile_index(sample_index) in {0, 1},
    )
    shape, counters = _construct_layout(height, width, local_mask, n_4, ctx)
    grid = full_grid(height, width, 0)
    for r, c in shape:
        grid[r][c] = 8
    for r, c in counters:
        grid[r][c] = 4

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_4_cells": n_4,
        "shape_kind": shape_kind,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid
