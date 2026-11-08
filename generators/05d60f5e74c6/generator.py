"""Solid same-color 4-components become bbox corners; nonrectangles vanish.

The canonical Racket rule is unchanged. Ordinary consecutive four-demo lessons
contain plain rectangles, a nonrectangular blob, bars plus a singleton, and an
L-shaped merge with diagonal-only same-color rectangle contact. Special objects
are packed jointly with rectangles; a constructive fallback never drops an axis.
The named degenerate textures are diagnostic negatives, not ordinary lessons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "05d60f5e74c6"
VERSION = "4.0.0"
RULE_HASH = "a74660ace2a2"
EXAMPLES_NEEDED = 4
SUMMARY = (
    "Reduce each solid same-color 4-connected component to its distinct bbox "
    "corners; discard non-solid components. Four scheduled demos distinguish "
    "solidity, component-vs-color grouping, 4-vs-8 connectivity, and thin/dot "
    "corner collapse. Rectangle counts and textures are observable and exact."
)
INVARIANTS = [
    "rectangular integer ARC grid, colors 0..9, with 0 background present",
    "at least one solid >=2x2 component with area >4, making the input nonidentity",
    "the rectangles axis counts all solid components whose height and width are >=2",
    "ordinary blob/l_merge textures contain a non-solid component, never silently omitted",
    "thin texture contains both a length>=3 bar and a singleton",
]
HELPFUL_TEXTURES = ("plain", "blob", "thin", "l_merge")
DEGENERATE_TEXTURES = ("no_rects", "all_2x2", "single_cell_rects")
SCHEDULE_PROFILES = HELPFUL_TEXTURES
# (height, width, fat-object count), not copied canonical grids or labels.
# Plain-phase anchors retain source-scale support in every difficulty band.
CANONICAL_ANCHOR_PROFILES = ((8, 10, 3), (9, 11, 3), (8, 9, 3), (10, 10, 2), (9, 10, 3))
AXES = {
    "grid_h": {"type": "int", "default": "plain: canonical-size anchor; otherwise difficulty-aware 8..20", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "plain: canonical-size anchor; otherwise difficulty-aware 9..22", "valid": "9..22"},
    "rectangles": {"type": "int", "default": "plain: anchor count 2..3; otherwise difficulty-aware 2..4", "valid": "1..6",
                   "doc": "Exact number of solid components with both dimensions >=2."},
    "texture": {"type": "str", "default": "four-sample cyclic schedule",
                "valid": "plain|blob|thin|l_merge",
                "doc": "Diagnostic negatives remain callable but are outside this teaching domain."},
}


def _components(grid, *, diagonal=False, by_color=False):
    h, w = len(grid), len(grid[0])
    seen, out = set(), []
    deltas = [(r, c) for r in (-1, 0, 1) for c in (-1, 0, 1)
              if (r or c) and (diagonal or abs(r) + abs(c) == 1)]
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            if by_color:
                cells = {(x, y) for x in range(h) for y in range(w) if grid[x][y] == color}
                seen.update(cells)
            else:
                cells, todo = {(r, c)}, [(r, c)]
                seen.add((r, c))
                while todo:
                    x, y = todo.pop()
                    for dx, dy in deltas:
                        p = x + dx, y + dy
                        if (0 <= p[0] < h and 0 <= p[1] < w and p not in seen
                                and grid[p[0]][p[1]] == color):
                            cells.add(p)
                            seen.add(p)
                            todo.append(p)
            r0, r1 = min(x for x, y in cells), max(x for x, y in cells)
            c0, c1 = min(y for x, y in cells), max(y for x, y in cells)
            corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
            out.append({"cells": cells, "color": color, "corners": corners,
                        "h": r1-r0+1, "w": c1-c0+1,
                        "solid": len(cells) == (r1-r0+1)*(c1-c0+1)})
    return out


def _project(grid, *, diagonal=False, by_color=False, all_boxes=False,
             keep_nonrect=False, drop_thin=False, keep_thin=False):
    out = full_grid(len(grid), len(grid[0]), 0)
    for obj in _components(grid, diagonal=diagonal, by_color=by_color):
        thin = min(obj["h"], obj["w"]) == 1
        if drop_thin and thin:
            continue
        if (keep_nonrect and not obj["solid"]) or (keep_thin and thin):
            points = obj["cells"]
        elif all_boxes or obj["solid"]:
            points = obj["corners"]
        else:
            points = ()
        for r, c in points:
            out[r][c] = obj["color"]
    return out


def expected_output(grid):
    """Test/semantic mirror only; production labels still come from Racket."""
    return _project(grid)


def _grid_errors(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["ARC grid dimensions must be <=30"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid colors must be integers 0..9, excluding bool"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the nontrivial teaching domain, not every input the rule accepts."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    if not any(0 in row for row in grid):
        return ["teaching scene must include 0 background"]
    if not any(o["solid"] and min(o["h"], o["w"]) >= 2 and len(o["cells"]) > 4
               for o in _components(grid)):
        return ["no nonidentity solid rectangle >=2x2 with area >4"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if any(not o["solid"] or min(o["h"], o["w"]) < 2 for o in _components(grid)):
        return ["canonical examples contain only fat solid rectangles"]
    return []


MIN_STRICT_FRAC = 0.15


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("outside teaching domain: " + "; ".join(errors))
    parts = _components(grid)
    irregular = [o for o in parts if not o["solid"]]
    if any(min(o["h"], o["w"]) == 1 for o in parts):
        texture = "thin"
    elif irregular:
        texture = "l_merge" if any(len(o["cells"] & o["corners"]) == 3 for o in irregular) else "blob"
    else:
        texture = "plain"
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "rectangles": sum(o["solid"] and min(o["h"], o["w"]) >= 2 for o in parts),
            "texture": texture}


def schedule_profile(seed, sample_index, difficulty=None):
    del difficulty
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _rect(h, w):
    return {(r, c) for r in range(h) for c in range(w)}


def _turn(cells, rotations):
    cells = set(cells)
    for _ in range(rotations):
        cells = {(c, -r) for r, c in cells}
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return {(r-r0, c-c0) for r, c in cells}


def _specials(texture, color, rng):
    if texture == "blob":
        cells = (_rect(3, 3) - {(1, 1)} if rng.randrange(2)
                 else {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)})
        return [(cells, color)]
    if texture == "l_merge":
        # Two edge-touching rectangles of unequal widths: rows 110/110/111.
        cells = _rect(3, 2) | {(2, 2)}
        return [(_turn(cells, rng.randrange(4)), color)]
    if texture == "thin":
        return [(_turn(_rect(1, rng.randint(3, 5)), rng.randrange(2)), color), ({(0, 0)}, color)]
    return []


def _can_place(grid, cells, color, r0, c0):
    h, w = len(grid), len(grid[0])
    points = {(r0+r, c0+c) for r, c in cells}
    if any(grid[r][c] for r, c in points):
        return False
    # Different colors may touch, as in canonical examples. Same-color groups
    # must not join cardinally; diagonal contact is allowed and exercised.
    for r, c in points:
        for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in points and grid[rr][cc] == color:
                return False
    return True


def _paint(grid, cells, color, r0, c0):
    for r, c in cells:
        grid[r0+r][c0+c] = color


def _pack(h, w, count, texture, colors, rng):
    """Bounded joint packing. None means retry layout, never drop an object."""
    for attempt in range(10):
        groups = []
        diagonal_pair = texture == "l_merge" and count >= 2
        small = attempt >= 4
        first_h, first_w = (2, 3) if small else (rng.randint(2, 4), rng.randint(3, 5))
        first = _rect(first_h, first_w)
        if diagonal_pair:
            second = {(r+first_h, c+first_w) for r, c in _rect(2, 2 if not small else 3)}
            groups.append((first | second, colors[0]))
            start = 2
        else:
            groups.append((first, colors[0]))
            start = 1
        for index in range(start, count):
            shape = _rect(2, 2 if rng.randrange(2) else 3) if small else _rect(rng.randint(2, 5), rng.randint(2, 6))
            groups.append((shape, colors[index]))
        groups.extend(_specials(texture, colors[0], rng))
        # Reserve the large/decisive groups before incidental small rectangles.
        groups.sort(key=lambda item: (-len(item[0]), -max(r for r, c in item[0])))
        grid = full_grid(h, w, 0)
        for cells, color in groups:
            sh, sw = max(r for r, c in cells)+1, max(c for r, c in cells)+1
            candidates = [(r, c) for r in range(h-sh+1) for c in range(w-sw+1)]
            rng.shuffle(candidates)
            position = next(((r, c) for r, c in candidates if _can_place(grid, cells, color, r, c)), None)
            if position is None:
                break
            _paint(grid, cells, color, *position)
        else:
            return grid
    return None


def _fallback(h, w, count, texture, colors, rng):
    """Proven 8x9 packing supports every advertised dimension/count combination."""
    grid = full_grid(h, w, 0)
    top, left = rng.randint(0, h-8), rng.randint(0, w-9)
    slots = ((0, 0), (2, 3), (0, 3), (0, 6), (2, 0), (2, 6))
    for index, (r, c) in enumerate(slots[:count]):
        color = colors[0] if texture == "l_merge" and index == 1 else colors[index]
        _paint(grid, _rect(2, 3), color, top+r, left+c)
    if texture in ("blob", "l_merge"):
        cells, color = _specials(texture, colors[0], rng)[0]
        _paint(grid, cells, color, top+5, left)
    elif texture == "thin":
        _paint(grid, _rect(1, 3), colors[0], top+5, left)
        _paint(grid, {(0, 0)}, colors[0], top+7, left+4)
    return grid


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override axes: {sorted(unknown)}")
    for key in ("grid_h", "grid_w", "rectangles"):
        if key in overrides and overrides[key] is not None and type(overrides[key]) is not int:
            raise TypeError(f"{key} must be an integer, excluding bool")
    texture = overrides.get("texture")
    if texture is not None and texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture: {texture!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    diagnostic = overrides.get("texture") in DEGENERATE_TEXTURES
    options = HELPFUL_TEXTURES + DEGENERATE_TEXTURES if diagnostic else HELPFUL_TEXTURES
    if overrides.get("texture") is None:
        options = (schedule_profile(seed, sample_index, difficulty),)
    texture = ctx.draw_choice("texture", options)
    if texture == "plain":
        ah, aw, an = ctx.draw_choice("canonical_size_anchor", CANONICAL_ANCHOR_PROFILES)
        h = ctx.draw_int("grid_h", 8, 20) if overrides.get("grid_h") is not None else ctx.draw_int("grid_h", ah, ah)
        w = ctx.draw_int("grid_w", 9, 22) if overrides.get("grid_w") is not None else ctx.draw_int("grid_w", aw, aw)
        count = ctx.draw_int("rectangles", 1, 6) if overrides.get("rectangles") is not None else ctx.draw_int("rectangles", an, an)
    else:
        h, w = ctx.draw_int_diff("grid_h", 8, 20), ctx.draw_int_diff("grid_w", 9, 22)
        count = (ctx.draw_int("rectangles", 1, 6) if overrides.get("rectangles") is not None
                 else ctx.draw_int_diff("rectangles", 2, 4))
    rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("palette", n=6, exclude=(0,)))
    if diagnostic:
        grid = full_grid(h, w, 0)
        if texture == "no_rects":
            if overrides.get("rectangles") is not None:
                raise ValueError("no_rects diagnostic is incompatible with a positive rectangles override")
            return grid
        size = 2 if texture == "all_2x2" else 1
        for index in range(count):
            r, c = 3*(index//3), 3*(index%3)
            _paint(grid, _rect(size, size), colors[index], r, c)
    else:
        grid = _pack(h, w, count, texture, colors, rng)
        if grid is None:
            grid = _fallback(h, w, count, texture, colors, rng)
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if rng.randrange(2):
        grid = grid[::-1]
    if not diagnostic:
        realized = observe_overrides(grid)
        wanted = {"grid_h": h, "grid_w": w, "rectangles": count, "texture": texture}
        if realized != wanted:
            raise RuntimeError(f"internal placement defect: expected {wanted}, observed {realized}")
    return grid


SEMANTIC_RIVALS = {
    "all_component_bbox_corners": lambda g: _project(g, all_boxes=True),
    "keep_nonrectangles": lambda g: _project(g, keep_nonrect=True),
    "one_component_per_color": lambda g: _project(g, by_color=True),
    "eight_connected_objects": lambda g: _project(g, diagonal=True),
    "drop_thin_and_singletons": lambda g: _project(g, drop_thin=True),
    "keep_thin_unchanged": lambda g: _project(g, keep_thin=True),
    "identity": lambda g: [row[:] for row in g],
}
CANONICAL_SHORTCUTS = {name: fn for name, fn in SEMANTIC_RIVALS.items() if name != "identity"}
LESSON_COMPETITORS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {
    "refute_" + name: (lambda g, fn=fn: fn(g) != expected_output(g))
    for name, fn in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {"refute_" + name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Require correct labels and reject any surviving rival that changes query."""
    if not isinstance(demos, list) or not demos:
        return ["at least one labeled demonstration is required"]
    errors = []
    for i, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {i} missing input/output")
            continue
        invalid = _grid_errors(pair["input"])
        if invalid:
            errors.append(f"pair {i}: {invalid}")
        elif pair["output"] != expected_output(pair["input"]):
            errors.append(f"pair {i} label disagrees with rectangle-corner rule")
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(p["input"]) == p["output"] for p in demos) and rival(query["input"]) != query["output"]:
            errors.append(f"surviving rival changes query: {name}")
    return errors


def mutation_fixtures():
    blank = full_grid(8, 9, 0)
    singleton = full_grid(8, 9, 0)
    singleton[3][3] = 2
    square = full_grid(8, 9, 0)
    _paint(square, _rect(2, 2), 2, 0, 0)
    return [("blank", blank), ("singleton", singleton), ("identity_2x2", square),
            ("ragged", [[0, 0], [0]]), ("invalid_color", [[10, 0], [0, 0]])]
