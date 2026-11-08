"""Task-linked generator for ARC task 9e80ef661ecc: hole-count recoloring.

The canonical transformation preserves every same-color orthogonally connected
object in place and recolors it by the number of holes in the object's own
bounding-box mask: 0 -> 2, 1 -> 3, 2 -> 4, 3 -> 6, and 4+ -> 9.

A four-profile curriculum is scheduled over consecutive sample indices:

* ``canonical`` alternates public-size examples with varied connected masks.
* ``equal_features`` gives 0/1/2-hole objects the same input color, area and
  bounding box, falsifying area, color and enclosed-cell-count shortcuts.
* ``touching`` includes same-color diagonal and different-color orthogonal
  contact, distinguishing both object-connectivity shortcuts.
* ``extended`` exposes 3-, 4-, 5- and 6-hole objects. Larger profiles share
  overlapping canvas sizes and include duplicated counts and border contact.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9e80ef661ecc"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "609d24e8c088"

SUMMARY = (
    "Preserve each same-color 4-connected object in place and recolor it only "
    "by the number of enclosed complement regions in its own bounding box: "
    "0 holes -> 2, 1 -> 3, 2 -> 4, 3 -> 6, and 4 or more -> 9. A four-example "
    "profile schedule includes canonical scenes, equal-area/equal-bbox objects, "
    "4/8-connectivity contrasts, procedurally varied connected masks, and "
    "3/4/5/6-hole extensions. Twelve explicit rivals are checked; this is "
    "finite evidence, not universal identifiability."
)

INVARIANTS = [
    "background is 0; diagnostic objects may contact any canvas border",
    "objects are orthogonally connected components of one color; touching different colors stay separate",
    "each ordinary lesson contains 0-, 1-, and 2-hole objects",
    "the extended profile also contains 3-, 4-, 5- and 6-hole objects",
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

# Small public-like floor; diagnostic canvases vary independently of profile.
_CANONICAL_DIMS = {(10, 14), (11, 13), (9, 15), (10, 12)}
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
_EQUAL_ZERO = _mask("1001", "1111", "1111", "1111")
_EQUAL_ONE = _mask("1111", "1001", "1111", "1111")
_EQUAL_TWO = _mask("1111", "1011", "1101", "1111")
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


def _neighbors(r, c, diagonal=False):
    return [(r+dr, c+dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
            if (dr or dc) and (diagonal or abs(dr)+abs(dc) == 1)]


def _components(grid: Sequence[Sequence[int]], *, merge_colors: bool = False, diagonal=False) -> list[Object]:
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
                for nr, nc in _neighbors(rr, cc, diagonal):
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


def _hole_regions(obj: Object, *, diagonal=False) -> list[set[Cell]]:
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
        for point in _neighbors(r, c, diagonal):
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
            for point in _neighbors(r, c, diagonal):
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


def _same_color_diagonal_touching(grid):
    objects = _components(grid)
    owner = {p: i for i, obj in enumerate(objects) for p in obj['cells']}
    for p, i in owner.items():
        r, c = p
        for q in ((r-1,c-1),(r-1,c+1),(r+1,c-1),(r+1,c+1)):
            j = owner.get(q)
            if j is not None and i != j and grid[r][c] == grid[q[0]][q[1]]:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural teaching grammar; dimensions and fixed masks are not labels."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (2 <= h <= 30 and 2 <= w <= 30):
        return ['task canvas must be 2..30 on each axis']
    stats = _object_stats(grid)
    if not 3 <= len(stats) <= 9:
        errors.append('expected 3..9 same-color components')
    if not {0, 1, 2} <= {item['holes'] for item in stats}:
        errors.append('scene must include 0-, 1- and 2-hole objects')
    for item in stats:
        if item['area'] < 4 or min(item['bbox']) < 2 or item['holes'] > 6:
            errors.append('object outside connected 0..6-hole teaching grammar')
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    if _grid_errors(grid):
        return {}
    stats = _object_stats(grid)
    if not stats:
        return {'profile': None}
    if any(item['holes'] >= 3 for item in stats):
        profile = 'extended'
    elif _cross_color_touching(grid) or _same_color_diagonal_touching(grid):
        profile = 'touching'
    elif (len({item['color'] for item in stats}) == 1
          and len({(item['bbox'], item['area']) for item in stats}) == 1
          and {item['holes'] for item in stats} == {0, 1, 2}):
        profile = 'equal_features'
    else:
        profile = 'canonical'
    return {'profile': profile}


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
    grid = _empty_grid(10, 14)
    shape_rng = ctx.draw_rng("canonical_shapes")
    layout_rng = ctx.draw_rng("canonical_layout")
    colors = ctx.draw_rng("canonical_palette").sample(range(1, 10), 3)
    solid = shape_rng.choice((_SOLID_2, _SOLID_3))
    ring = shape_rng.choice((_RING_3, _RING_4))
    _paint(grid, solid, (layout_rng.randint(1, 2), layout_rng.randint(1, 3)), colors[0])
    _paint(grid, ring, (layout_rng.randint(1, 1 if ring is _RING_4 else 2), layout_rng.randint(8, 9)), colors[1])
    _paint(grid, _DOUBLE, (6, layout_rng.randint(4, 6)), colors[2])
    return _finish_profile(grid, ctx.draw_rng("canonical_transform"))


def _mask_object(cells):
    cells = set(cells)
    return {'cells': cells, 'color': 1,
            'bbox': (min(r for r,c in cells), min(c for r,c in cells),
                     max(r for r,c in cells), max(c for r,c in cells))}


def _valid_mask(cells, holes, height, width):
    if not cells:
        return False
    grid = [[int((r,c) in cells) for c in range(width)] for r in range(height)]
    objects = _components(grid)
    return len(objects) == 1 and _hole_count(objects[0]) == holes


def _procedural_mask(rng, holes):
    """Connected masks with verified cavities, expansions and exterior notches."""
    height, width = rng.randint(7,8), rng.randint(7,8)
    cells = {(r,c) for r in range(height) for c in range(width)}
    centers = [(r,c) for r in range(1,height-1,2) for c in range(1,width-1,2)]
    rng.shuffle(centers)
    cavities = centers[:holes]
    cells.difference_update(cavities)
    for center in cavities:
        neighbors = _neighbors(*center)
        rng.shuffle(neighbors)
        for point in neighbors[:rng.randrange(3)]:
            if not (0 < point[0] < height-1 and 0 < point[1] < width-1) or point not in cells:
                continue
            proposed = cells - {point}
            if _valid_mask(proposed, holes, height, width):
                cells = proposed
    border = [(r,c) for r,c in cells if r in (0,height-1) or c in (0,width-1)]
    border.sort()
    rng.shuffle(border)
    for point in border[:rng.randrange(5)]:
        proposed = cells - {point}
        if _valid_mask(proposed, holes, height, width):
            cells = proposed
    if not _valid_mask(cells, holes, height, width):
        raise AssertionError('procedural mask failed connected-hole construction')
    for _ in range(rng.randrange(4)):
        cells = {(c,-r) for r,c in cells}
    if rng.randrange(2):
        cells = {(r,-c) for r,c in cells}
    r0, c0 = min(r for r,c in cells), min(c for r,c in cells)
    return tuple(sorted((r-r0,c-c0) for r,c in cells))


def _large_canvas(ctx, label):
    rng = ctx.draw_rng(label + '_canvas')
    return _empty_grid(rng.randint(27,30), rng.randint(27,30))


def _place_separated(grid, masks, colors, rng):
    slots = [(r*9,c*9) for r in range(3) for c in range(3)]
    rng.shuffle(slots)
    for mask, color, (r,c) in zip(masks, colors, slots):
        mh, mw = 1+max(x for x,y in mask), 1+max(y for x,y in mask)
        # Slot padding leaves at least one zero row/column between objects.
        origin = (r+rng.randrange(9-mh), c+rng.randrange(9-mw))
        _paint(grid, mask, origin, color)


def _finish_large(grid, rng):
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    grid = _finish_profile(grid, rng)
    h, w = len(grid), len(grid[0])
    points = [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    r0, c0 = min(r for r,c,v in points), min(c for r,c,v in points)
    bh = max(r for r,c,v in points)-r0+1
    bw = max(c for r,c,v in points)-c0+1
    dr = rng.choice((0,h-bh,rng.randrange(h-bh+1)))
    dc = rng.choice((0,w-bw,rng.randrange(w-bw+1)))
    result = _empty_grid(h,w)
    for r,c,v in points:
        result[r-r0+dr][c-c0+dc] = v
    return result


def _ordinary_grid(ctx):
    rng = ctx.draw_rng('ordinary_masks')
    holes = [0,1,2] + [rng.randrange(3) for _ in range(rng.randrange(4))]
    masks = [_procedural_mask(rng,n) for n in holes]
    colors = ctx.draw_rng('ordinary_palette').sample(range(1,10),len(masks))
    grid = _large_canvas(ctx,'ordinary')
    _place_separated(grid,masks,colors,rng)
    return _finish_large(grid,ctx.draw_rng('ordinary_transform'))


def _equal_features_grid(ctx) -> Grid:
    rng = ctx.draw_rng('equal_layout')
    masks = [_EQUAL_ZERO,_EQUAL_ONE,_EQUAL_TWO]
    masks += [rng.choice(masks) for _ in range(rng.randrange(3))]
    color = ctx.draw_rng('equal_palette').choice(range(1,10))
    grid = _large_canvas(ctx,'equal')
    _place_separated(grid,masks,[color]*len(masks),rng)
    return _finish_large(grid,ctx.draw_rng('equal_transform'))


def _touching_grid(ctx) -> Grid:
    grid = _large_canvas(ctx,'touching')
    colors = ctx.draw_rng('touching_palette').sample(range(1,10),5)
    # Solid and ring touch diagonally in the SAME color; ring/double touch
    # orthogonally in DIFFERENT colors. Both object relations change answers.
    _paint(grid,_SOLID_2,(0,0),colors[0])
    _paint(grid,_RING_3,(2,2),colors[0])
    _paint(grid,_DOUBLE,(2,5),colors[1])
    rng = ctx.draw_rng('touching_extras')
    for i in range(rng.randrange(1,4)):
        _paint(grid,_procedural_mask(rng,rng.randrange(3)),(10+i//2*9,i%2*10),colors[i+2])
    return _finish_large(grid,ctx.draw_rng('touching_transform'))


def _extended_grid(ctx) -> Grid:
    rng = ctx.draw_rng('extended_masks')
    holes = list(range(7)) + [rng.randrange(7) for _ in range(rng.randrange(3))]
    masks = [_procedural_mask(rng,n) for n in holes]
    colors = ctx.draw_rng('extended_palette').sample(range(1,10),len(masks))
    grid = _large_canvas(ctx,'extended')
    _place_separated(grid,masks,colors,rng)
    return _finish_large(grid,ctx.draw_rng('extended_transform'))


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
    if profile == 'canonical' and (int(sample_index)//4) % 2:
        grid = _ordinary_grid(ctx)
    else:
        grid = _BUILDERS[profile](ctx)
    grid = _shift_palette_for_band(grid, difficulty)
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


def _recolor_objects(grid: Sequence[Sequence[int]], color_for: Callable[[Object], int], *, merge_colors: bool = False, diagonal=False) -> Grid:
    out = [list(row) for row in grid]
    for obj in _components(grid, merge_colors=merge_colors, diagonal=diagonal):
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


def _max_gap_runs(obj, transpose=False):
    cells = {(c,r) if transpose else (r,c) for r,c in obj['cells']}
    r0, r1 = min(r for r,c in cells), max(r for r,c in cells)
    c0, c1 = min(c for r,c in cells), max(c for r,c in cells)
    maximum = 0
    for r in range(r0+1,r1):
        runs, start = 0, None
        for c in range(c0,c1+2):
            if c <= c1 and (r,c) not in cells:
                if start is None:
                    start = c
            elif start is not None:
                runs += start > c0 and c-1 < c1
                start = None
        maximum = max(maximum,runs)
    return maximum


def _row_gap_lookup(grid):
    return _recolor_objects(grid,lambda o:_output_color(_max_gap_runs(o)))


def _row_column_gap_lookup(grid):
    return _recolor_objects(grid,lambda o:_output_color(max(_max_gap_runs(o),_max_gap_runs(o,True))))


def _eight_connected_holes(grid):
    return _recolor_objects(grid,lambda o:_output_color(len(_hole_regions(o,diagonal=True))))


def _eight_connected_objects(grid):
    return _recolor_objects(grid,lambda o:_output_color(_hole_count(o)),diagonal=True)


def _four_only_not_four_plus(grid):
    return _recolor_objects(grid,lambda o:_output_color(_hole_count(o)) if _hole_count(o) <= 4 else 6)


def _shape_signature(cells):
    variants = []
    for flip in (1,-1):
        points = {(r,c*flip) for r,c in cells}
        for _ in range(4):
            r0, c0 = min(r for r,c in points), min(c for r,c in points)
            variants.append(tuple(sorted((r-r0,c-c0) for r,c in points)))
            points = {(c,-r) for r,c in points}
    return min(variants)


_LEGACY_TEMPLATE_COLORS = {
    _shape_signature(mask): color for mask,color in [
        (_SOLID_2,2), (_SOLID_3,2), (_RING_3,3), (_RING_4,3), (_DOUBLE,4),
        (_mask('10011','11111','11111'),2),
        (_mask('11111','10011','11111'),3), (_THREE_HOLES,6), (_FOUR_HOLES,9)]
}


def _shape_template_lookup(grid):
    return _recolor_objects(grid,lambda o:_LEGACY_TEMPLATE_COLORS.get(_shape_signature(o['cells']),9))


CANONICAL_SHORTCUTS: dict[str, Rival] = {
    "foreground_area_lookup": _foreground_area_lookup,
    "enclosed_cell_count_lookup": _enclosed_cell_lookup,
    "canonical_hole_range_only": _canonical_range_only,
    "same_color_global_object": _same_color_global,
    "max_horizontal_interior_gap_runs": _row_gap_lookup,
    "max_row_or_column_gap_runs": _row_column_gap_lookup,
    "eight_connected_holes": _eight_connected_holes,
    "eight_connected_objects": _eight_connected_objects,
    "four_only_not_four_plus": _four_only_not_four_plus,
    "shape_template_lookup": _shape_template_lookup,
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
