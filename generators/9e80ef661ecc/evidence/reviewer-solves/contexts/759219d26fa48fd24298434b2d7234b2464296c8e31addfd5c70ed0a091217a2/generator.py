"""Task-linked generator for ARC task 9e80ef661ecc: hole-count recoloring.

The canonical transformation preserves every same-color orthogonally connected
object in place and recolors it by the number of holes in the object's own
bounding-box mask: 0 -> 2, 1 -> 3, 2 -> 4, 3 -> 6, and 4+ -> 9.

A four-profile curriculum is scheduled over consecutive sample indices:

* ``canonical`` matches the public size/palette/object grammar.
* ``equal_features`` gives 0/1/2-hole objects the same input color, area and
  bounding box, falsifying area, color and enclosed-cell-count shortcuts.
* ``touching`` makes different-colored objects touch, falsifying a merger of
  all nonzero connectivity.
* ``extended`` exposes the 3-hole and 4+-hole output branches absent from the
  public demonstrations.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9e80ef661ecc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "609d24e8c088"

SUMMARY = (
    "Preserve each same-color 4-connected object in place and recolor it only "
    "by the number of enclosed complement regions in its own bounding box: "
    "0 holes -> 2, 1 -> 3, 2 -> 4, 3 -> 6, and 4 or more -> 9. A four-example "
    "profile schedule includes canonical scenes, equal-area/equal-bbox objects, "
    "touching different colors, and 3/4-hole extensions so common shortcut "
    "rules are explicitly falsified."
)

INVARIANTS = [
    "background is 0; generated canvases retain top/bottom margin",
    "objects are orthogonally connected components of one color; touching different colors stay separate",
    "each ordinary lesson contains 0-, 1-, and 2-hole objects",
    "the extended profile also contains 3- and 4-hole objects",
    "the selected canonical Racket program remains output authority",
]

PROFILES = ("canonical", "equal_features", "touching", "extended")
SCHEDULE_PROFILES = PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

AXES = {
    "profile": {
        "type": "str",
        "default": "sample_index mod 4 curriculum",
        "valid": PROFILES,
        "probe": "diagnostic",
        "doc": "Internal semantic lesson profile; each consecutive four-demo window covers all profiles.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[object, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]
Object = dict[str, Any]
Rival = Callable[[Sequence[Sequence[int]]], Grid]

# The four public input profiles plus the three non-public teaching canvases.
_CANONICAL_DIMS = {(10, 14), (11, 13), (9, 15), (10, 12)}
_GENERATED_DIMS = {
    "canonical": (10, 14),
    "equal_features": (11, 18),
    "touching": (9, 15),
    "extended": (12, 24),
}
_PROFILE_BY_DIMS = {dims: name for name, dims in _GENERATED_DIMS.items()}
_BAND_COLOR_SHIFTS = {None: 0, "easy": 1, "medium": 3, "hard": 5}


def _mask(*rows: str) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == "1"
    )


_SOLID_2 = _mask("11", "11")
_SOLID_3 = _mask("111", "111", "111")
_RING_3 = _mask("111", "101", "111")
_RING_4 = _mask("1111", "1001", "1001", "1111")
_DOUBLE = _mask("11111", "10101", "11111")
_EQUAL_ZERO = _mask("10011", "11111", "11111")
_EQUAL_ONE = _mask("11111", "10011", "11111")
_EQUAL_TWO = _mask("11111", "10101", "11111")
_THREE_HOLES = _mask("1111111", "1010101", "1111111")
_FOUR_HOLES = _mask("111111111", "101010101", "111111111")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Deterministic curriculum schedule; every length-four window is complete."""
    del seed, difficulty
    return PROFILES[int(sample_index) % len(PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Sequence[Sequence[int]], *, merge_colors: bool = False) -> list[Object]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[Object] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = int(grid[r][c])
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[Cell] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    value = int(grid[nr][nc])
                    if value == 0 or (not merge_colors and value != color):
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _hole_regions(obj: Object) -> list[set[Cell]]:
    cells = set(obj["cells"])
    r0, c0, r1, c1 = obj["bbox"]
    complement = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r, c) not in cells
    }
    outside: set[Cell] = set()
    queue = deque(
        point
        for point in complement
        if point[0] in (r0, r1) or point[1] in (c0, c1)
    )
    outside.update(queue)
    while queue:
        r, c = queue.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in complement and point not in outside:
                outside.add(point)
                queue.append(point)

    pending = complement - outside
    holes: list[set[Cell]] = []
    while pending:
        start = next(iter(pending))
        pending.remove(start)
        region = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in pending:
                    pending.remove(point)
                    region.add(point)
                    stack.append(point)
        holes.append(region)
    return holes


def _hole_count(obj: Object) -> int:
    return len(_hole_regions(obj))


def _output_color(n_holes: int) -> int:
    return {0: 2, 1: 3, 2: 4, 3: 6}.get(int(n_holes), 9)


def _object_stats(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    result = []
    for obj in _components(grid):
        r0, c0, r1, c1 = obj["bbox"]
        holes = _hole_regions(obj)
        result.append(
            {
                "color": obj["color"],
                "cells": obj["cells"],
                "holes": len(holes),
                "area": len(obj["cells"]),
                "bbox": (r1 - r0 + 1, c1 - c0 + 1),
                "enclosed_cells": sum(len(region) for region in holes),
            }
        )
    return result


def _cross_color_touching(grid: Sequence[Sequence[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            value = int(grid[r][c])
            if value == 0:
                continue
            for nr, nc in ((r + 1, c), (r, c + 1)):
                if 0 <= nr < h and 0 <= nc < w and int(grid[nr][nc]) not in (0, value):
                    return True
    return False


def _signature(item: dict[str, Any]) -> tuple[int, int, int, int]:
    bh, bw = item["bbox"]
    return bh, bw, item["area"], item["enclosed_cells"]


_CANONICAL_SIGNATURES = {
    0: {(2, 2, 4, 0), (3, 3, 9, 0)},
    1: {(3, 3, 8, 1), (4, 4, 12, 4)},
    2: {(3, 5, 13, 2)},
}
_EQUAL_SIGNATURES = {
    0: {(3, 5, 13, 0)},
    1: {(3, 5, 13, 2)},
    2: {(3, 5, 13, 2)},
}
_EXTENDED_SIGNATURES = {
    **_EQUAL_SIGNATURES,
    3: {(3, 7, 18, 3)},
    4: {(3, 9, 23, 4)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the declared task grammar, including all canonical inputs."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in _CANONICAL_DIMS | set(_GENERATED_DIMS.values()):
        errors.append(f"unsupported task canvas {(h, w)}")
    if any(grid[0][c] != 0 or grid[h - 1][c] != 0 for c in range(w)):
        errors.append("top and bottom borders must be background")

    stats = _object_stats(grid)
    if len(stats) not in (3, 5):
        errors.append(f"expected 3 or 5 same-color components, found {len(stats)}")
        return errors
    by_holes = {item["holes"]: item for item in stats}
    expected_holes = set(range(3 if len(stats) == 3 else 5))
    if set(by_holes) != expected_holes or len(by_holes) != len(stats):
        errors.append(
            f"expected exactly one object at each hole count {sorted(expected_holes)}, "
            f"found {sorted(item['holes'] for item in stats)}"
        )
        return errors

    dims = (h, w)
    if len(stats) == 5:
        if dims != _GENERATED_DIMS["extended"]:
            errors.append("five-object scenes require the extended canvas")
        expected = _EXTENDED_SIGNATURES
        if len({item["color"] for item in stats}) != 5:
            errors.append("extended objects must use five distinct input colors")
    elif dims == _GENERATED_DIMS["equal_features"]:
        expected = _EQUAL_SIGNATURES
        if len({item["color"] for item in stats}) != 1:
            errors.append("equal_features objects must share one input color")
    else:
        expected = _CANONICAL_SIGNATURES
        if len({item["color"] for item in stats}) != 3:
            errors.append("canonical and touching objects must use three distinct input colors")
        if dims == _GENERATED_DIMS["touching"] and not _cross_color_touching(grid):
            errors.append("touching profile must contain an orthogonal cross-color contact")

    for holes, item in sorted(by_holes.items()):
        if _signature(item) not in expected.get(holes, set()):
            errors.append(
                f"hole-{holes} object has unsupported (bbox_h,bbox_w,area,enclosed_cells) "
                f"signature {_signature(item)}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws and all public inputs inhabit this task grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    errors = _grid_errors(grid)
    if errors:
        return {}
    return {"profile": _PROFILE_BY_DIMS.get((len(grid), len(grid[0])))}


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; the selected Racket rule is authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for obj in _components(grid):
        color = _output_color(_hole_count(obj))
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def _empty_grid(height: int, width: int) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint(grid: Grid, mask: Sequence[Cell], origin: Cell, color: int) -> None:
    r0, c0 = origin
    for dr, dc in mask:
        r, c = r0 + dr, c0 + dc
        if grid[r][c] != 0:
            raise AssertionError(f"constructor overlap at {(r, c)}")
        grid[r][c] = int(color)


def _flip(grid: Grid, *, vertical: bool, horizontal: bool) -> Grid:
    result = [row[:] for row in grid]
    if vertical:
        result = result[::-1]
    if horizontal:
        result = [row[::-1] for row in result]
    return result


def _finish_profile(grid: Grid, transform_rng) -> Grid:
    return _flip(
        grid,
        vertical=bool(transform_rng.randrange(2)),
        horizontal=bool(transform_rng.randrange(2)),
    )


def _shift_palette_for_band(grid: Grid, difficulty) -> Grid:
    """Make difficulty bands observably distinct without changing topology."""
    shift = _BAND_COLOR_SHIFTS[difficulty]
    if shift == 0:
        return [row[:] for row in grid]
    return [
        [0 if value == 0 else 1 + ((int(value) - 1 + shift) % 9) for value in row]
        for row in grid
    ]


def _canonical_grid(ctx) -> Grid:
    grid = _empty_grid(*_GENERATED_DIMS["canonical"])
    shape_rng = ctx.draw_rng("canonical_shapes")
    layout_rng = ctx.draw_rng("canonical_layout")
    colors = ctx.draw_rng("canonical_palette").sample(range(1, 10), 3)
    solid = shape_rng.choice((_SOLID_2, _SOLID_3))
    ring = shape_rng.choice((_RING_3, _RING_4))
    _paint(grid, solid, (layout_rng.randint(1, 2), layout_rng.randint(1, 3)), colors[0])
    _paint(grid, ring, (layout_rng.randint(1, 1 if ring is _RING_4 else 2), layout_rng.randint(8, 9)), colors[1])
    _paint(grid, _DOUBLE, (6, layout_rng.randint(4, 6)), colors[2])
    return _finish_profile(grid, ctx.draw_rng("canonical_transform"))


def _equal_features_grid(ctx) -> Grid:
    grid = _empty_grid(*_GENERATED_DIMS["equal_features"])
    masks = [_EQUAL_ZERO, _EQUAL_ONE, _EQUAL_TWO]
    layout_rng = ctx.draw_rng("equal_layout")
    layout_rng.shuffle(masks)
    slots = [
        (layout_rng.randint(1, 2), layout_rng.randint(1, 3)),
        (layout_rng.randint(1, 3), 12),
        (7, layout_rng.randint(6, 8)),
    ]
    color = ctx.draw_rng("equal_palette").choice(range(1, 10))
    for mask, origin in zip(masks, slots):
        _paint(grid, mask, origin, color)
    return _finish_profile(grid, ctx.draw_rng("equal_transform"))


def _touching_grid(ctx) -> Grid:
    grid = _empty_grid(*_GENERATED_DIMS["touching"])
    colors = ctx.draw_rng("touching_palette").sample(range(1, 10), 3)
    # Exactly the canonical contact relation: ring bottom meets double top at one cell edge.
    _paint(grid, _RING_3, (1, 10), colors[0])
    _paint(grid, _DOUBLE, (4, 6), colors[1])
    _paint(grid, _SOLID_2, (5, 1), colors[2])
    return _finish_profile(grid, ctx.draw_rng("touching_transform"))


def _extended_grid(ctx) -> Grid:
    grid = _empty_grid(*_GENERATED_DIMS["extended"])
    colors = ctx.draw_rng("extended_palette").sample(range(1, 10), 5)
    _paint(grid, _FOUR_HOLES, (1, 1), colors[4])
    _paint(grid, _THREE_HOLES, (1, 15), colors[3])
    lower_masks = [_EQUAL_ZERO, _EQUAL_ONE, _EQUAL_TWO]
    layout_rng = ctx.draw_rng("extended_layout")
    layout_rng.shuffle(lower_masks)
    for mask, origin, color in zip(lower_masks, ((7, 1), (7, 9), (7, 17)), colors[:3]):
        _paint(grid, mask, origin, color)
    return _finish_profile(grid, ctx.draw_rng("extended_transform"))


_BUILDERS = {
    "canonical": _canonical_grid,
    "equal_features": _equal_features_grid,
    "touching": _touching_grid,
    "extended": _extended_grid,
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    choices = PROFILES if overrides.get("profile") is not None else (scheduled,)
    profile = str(ctx.draw_choice("profile", choices))
    grid = _shift_palette_for_band(_BUILDERS[profile](ctx), difficulty)
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"constructed invalid {profile} scene: {errors}")
    observed = observe_overrides(grid).get("profile")
    if observed != profile:
        raise AssertionError(f"profile {profile!r} realized as {observed!r}")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Explicit rival rules and task-linked semantic contract.
# ---------------------------------------------------------------------------


def _recolor_objects(grid: Sequence[Sequence[int]], color_for: Callable[[Object], int], *, merge_colors: bool = False) -> Grid:
    out = [list(row) for row in grid]
    for obj in _components(grid, merge_colors=merge_colors):
        color = int(color_for(obj))
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def _foreground_area_lookup(grid: Sequence[Sequence[int]]) -> Grid:
    lookup = {4: 2, 9: 2, 8: 3, 12: 3, 13: 4}
    return _recolor_objects(grid, lambda obj: lookup.get(len(obj["cells"]), int(obj["color"])))


def _enclosed_cell_lookup(grid: Sequence[Sequence[int]]) -> Grid:
    lookup = {0: 2, 1: 3, 4: 3, 2: 4}
    return _recolor_objects(
        grid,
        lambda obj: lookup.get(sum(len(region) for region in _hole_regions(obj)), 9),
    )


def _canonical_range_only(grid: Sequence[Sequence[int]]) -> Grid:
    return _recolor_objects(grid, lambda obj: {0: 2, 1: 3}.get(_hole_count(obj), 4))


def _merged_foreground(grid: Sequence[Sequence[int]]) -> Grid:
    return _recolor_objects(grid, lambda obj: _output_color(_hole_count(obj)), merge_colors=True)


def _same_color_global(grid: Sequence[Sequence[int]]) -> Grid:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    colors = sorted({int(value) for row in grid for value in row if value})
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        obj = {
            "color": color,
            "cells": cells,
            "bbox": (min(rows), min(cols), max(rows), max(cols)),
        }
        mapped = _output_color(_hole_count(obj))
        for r, c in cells:
            out[r][c] = mapped
    return out


def _identity(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


CANONICAL_SHORTCUTS: dict[str, Rival] = {
    "foreground_area_lookup": _foreground_area_lookup,
    "enclosed_cell_count_lookup": _enclosed_cell_lookup,
    "canonical_hole_range_only": _canonical_range_only,
    "same_color_global_object": _same_color_global,
}
SEMANTIC_RIVALS: dict[str, Rival] = {
    **CANONICAL_SHORTCUTS,
    "merge_touching_nonzero_colors": _merged_foreground,
    "identity": _identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _is_profile(grid: Sequence[Sequence[int]], profile: str) -> bool:
    return not strict_canonical_like(grid) and observe_overrides(grid).get("profile") == profile


def _disagrees(grid: Sequence[Sequence[int]], rival: str) -> bool:
    return SEMANTIC_RIVALS[rival](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "diagnostic_profiles_refute_named_shortcuts": lambda grid: (
        not strict_canonical_like(grid)
        and observe_overrides(grid).get("profile") in {"equal_features", "touching", "extended"}
        and any(_disagrees(grid, name) for name in SEMANTIC_RIVALS)
    ),
}

WITNESS_RIVALS = {
    "diagnostic_profiles_refute_named_shortcuts": list(SEMANTIC_RIVALS),
}



def lesson_identifiable(demos, query) -> list[str]:
    """Finite named-rival check; it does not claim universal induction."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the selected rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the selected rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons
