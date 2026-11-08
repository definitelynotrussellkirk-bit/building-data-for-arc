"""Exact run compression followed optionally by logical-component selection.

Returned labels are Python claims. Native qualification and example export
independently execute the exact Racket programs in this same checkout.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "c1fd38e5812b"
VIEWS = ("compressed", "largest_component_crop")
MAX_ATTEMPTS = 128
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"view"}:
        raise ValueError("settings must contain exactly view")
    if type(settings["view"]) is not str or settings["view"] not in VIEWS:
        raise ValueError("unsupported view")
    return settings["view"]


def _matrix(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("expected a nonempty grid within 30x30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("expected rectangular literal integer ARC cells")


def _dedup_consecutive(values):
    return [list(value) for i, value in enumerate(values) if i == 0 or value != values[i-1]]


def compress(grid):
    """Canonical consecutive whole-row, then whole-column compression."""
    _matrix(grid)
    rows = _dedup_consecutive(grid)
    return [list(row) for row in zip(*_dedup_consecutive(list(zip(*rows))))]


def expand(logical, row_spans, col_spans):
    return [[value for value, width in zip(row, col_spans) for _ in range(width)]
            for row, height in zip(logical, row_spans) for _ in range(height)]


def analyze(grid):
    _matrix(grid)
    rows = [0] + [r for r in range(1, len(grid)) if grid[r][0] != grid[r-1][0]]
    cols = [0] + [c for c in range(1, len(grid[0])) if grid[0][c] != grid[0][c-1]]
    rs = [b-a for a, b in zip(rows, rows[1:] + [len(grid)])]
    cs = [b-a for a, b in zip(cols, cols[1:] + [len(grid[0])])]
    logical = [[grid[r][c] for c in cols] for r in rows]
    return {"logical": logical, "row_starts": rows, "col_starts": cols,
            "row_spans": rs, "col_spans": cs}


def validate_grid(grid):
    info = analyze(grid)
    logical, rs, cs = info["logical"], info["row_spans"], info["col_spans"]
    if not (2 <= len(logical) <= 10 and 2 <= len(logical[0]) <= 10):
        raise ValueError("logical grid must be 2..10 by 2..10")
    if any(not 2 <= span <= 12 for span in rs+cs):
        raise ValueError("every run span must be 2..12")
    if len({v for row in logical for v in row}) < 4:
        raise ValueError("logical grid must use at least four colors")
    if expand(logical, rs, cs) != grid or compress(grid) != logical:
        raise ValueError("input must be exact Cartesian runs with visible first-axis boundaries")
    return True


def components(grid, connectivity=4):
    _matrix(grid)
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    pending = {(r, c) for r, row in enumerate(grid) for c in range(len(row))}
    groups = []
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                  if (dr or dc) and (connectivity == 8 or abs(dr)+abs(dc) == 1)]
    while pending:
        start = min(pending); pending.remove(start)
        color = grid[start[0]][start[1]]
        stack, group = [start], [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                point = r+dr, c+dc
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point); stack.append(point); group.append(point)
        groups.append(tuple(sorted(group)))
    return groups


def bbox(component):
    return (min(r for r, c in component), min(c for r, c in component),
            max(r for r, c in component), max(c for r, c in component))


def _lex(grid, component):
    return (*bbox(component), grid[component[0][0]][component[0][1]])


def select_component(grid, connectivity=4):
    return min(components(grid, connectivity), key=lambda o: (-len(o), *_lex(grid, o)))


def crop(grid, component):
    r1, c1, r2, c2 = bbox(component)
    return [row[c1:c2+1] for row in grid[r1:r2+1]]


def solve(grid, *, view="compressed"):
    validate_settings({"view": view})
    validate_grid(grid)
    logical = compress(grid)
    return logical if view == "compressed" else crop(logical, select_component(logical))


def program(settings):
    if validate_settings(settings) == "compressed":
        return CANONICAL
    # Base31 exactly represents bbox lex order for coordinates0..29. A size
    # difference dominates every possible bbox/color key by construction.
    return """(rule! (lambda (g)
  (let* ((small (compress-grid g))
         (ordered (sort-by (objects small -1)
           (lambda (o)
             (+ (* -10000000 (obj-size o))
                (* 10 (+ (* 29791 (obj-r1 o)) (* 961 (obj-c1 o))
                         (* 31 (obj-r2 o)) (obj-c2 o)))
                (obj-color o)))))
         (chosen (first ordered)))
    (crop-object small chosen))))"""


def _rng(seed, role, attempt=0):
    value = hashlib.sha256(f"{TASK_ID}/logical-v1/{seed}/{role}/{attempt}".encode()).digest()
    return random.Random(int.from_bytes(value, "big"))


def _checker(height, width, colors):
    return [[colors[(r+c) % 2] for c in range(width)] for r in range(height)]


def _paint(grid, points, color, origin=(0, 0)):
    for r, c in points:
        grid[r+origin[0]][c+origin[1]] = color


def _ring(rng):
    h, w = rng.choice((3, 5)), rng.choice((3, 5))
    a, b, inside = rng.sample(range(1, 10), 3)
    grid = _checker(h+2, w+2, (a, b))
    for r in range(1, h+1):
        for c in range(1, w+1):
            grid[r][c] = 0 if r in (1, h) or c in (1, w) else inside
    rs, cs = [2]*(h+2), [rng.choice((2, 3))]*(w+2)
    rs[rng.randrange(2, h)] = rng.choice((5, 6, 7, 8))
    return grid, rs, cs


SIX_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
)


def _physical(rng):
    filler, target, loser, earlier = rng.sample(range(1, 10), 4)
    target, loser = sorted((target, loser))
    grid = _checker(9, 9, (0, filler))
    shape = rng.choice(SIX_SHAPES)
    _paint(grid, shape, target, (1, 2))
    _paint(grid, [(r, 6) for r in range(2, 8)], loser)
    _paint(grid, ((0,1),(1,1)), earlier)
    rs, cs = [rng.choice((2, 3))]*9, [2]*9
    cs[6] = rng.choice((7, 8, 9, 10))
    return grid, rs, cs


def _tie(rng):
    a, b, first, second = rng.sample(range(10), 4)
    second, first = sorted((first, second))
    grid = _checker(8, 9, (a, b))
    small = rng.choice(SIX_SHAPES[:2])
    large = ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2))
    _paint(grid, small, first, (1, 1))
    _paint(grid, large, second, (3, 5))
    rs = [2]*8; cs = [2]*9
    rs[rng.randrange(1, 7)] = rng.choice((3, 4, 5))
    cs[rng.randrange(1, 8)] = rng.choice((3, 4, 5))
    return grid, rs, cs


def _transform(spec, rng, transpose=False):
    grid, rs, cs = spec
    if rng.randrange(2):
        grid, cs = [row[::-1] for row in grid], cs[::-1]
    if transpose:
        grid, rs, cs = [list(row) for row in zip(*grid)], cs, rs
    return expand(grid, rs, cs)


def _rival(grid, view, name):
    info = analyze(grid)
    logical = info["logical"]
    rs, cs = info["row_spans"], info["col_spans"]
    rows, cols = info["row_starts"], info["col_starts"]
    if name == "fixed_stride":
        rows, cols = list(range(0, len(grid), rs[0])), list(range(0, len(grid[0]), cs[0]))
    elif name == "coupled_cols" and len(set(rs)) == 1:
        cols = list(range(0, len(grid[0]), cs[0]))
    elif name == "coupled_rows" and len(set(cs)) == 1:
        rows = list(range(0, len(grid), rs[0]))
    if name in ("fixed_stride", "coupled_cols", "coupled_rows"):
        logical = [[grid[r][c] for c in cols] for r in rows]
    if name == "global_dedup":
        logical = [list(row) for row in dict.fromkeys(map(tuple, grid))]
        logical = [list(row) for row in zip(*dict.fromkeys(zip(*logical)))]
    if view == "compressed":
        return logical
    groups = components(logical, 8 if name == "connectivity8" else 4)
    if name == "ignore_zero":
        groups = [o for o in groups if logical[o[0][0]][o[0][1]] != 0]
    if name == "first_nontrivial":
        groups = [o for o in groups if len(o) > 1] or groups
    def key(o):
        lex = _lex(logical, o)
        r1, c1, r2, c2 = bbox(o)
        color = logical[o[0][0]][o[0][1]]
        if name == "physical_area":return (-sum(rs[r]*cs[c] for r, c in o), *lex)
        if name == "bbox_area":return (-(r2-r1+1)*(c2-c1+1), *lex)
        if name == "color_total":return (-sum(v == color for row in logical for v in row), -len(o), *lex)
        if name in ("first_component", "first_nontrivial"):return lex
        if name == "last_component":return tuple(-v for v in lex)
        if name == "min_color":return (color, -len(o), *lex)
        if name == "max_color":return (-color, -len(o), *lex)
        if name == "reverse_tie":return (-len(o), *(-v for v in lex))
        if name == "tie_min_color":return (-len(o), color, *lex)
        if name == "tie_max_color":return (-len(o), -color, *lex)
        return (-len(o), *lex)
    selected = min(groups, key=key)
    output = crop(logical, selected)
    if name == "solid_bbox":
        return [[logical[selected[0][0]][selected[0][1]]]*len(output[0]) for _ in output]
    if name == "isolate_component":
        r1, c1, _, _ = bbox(selected)
        return [[v if (r+r1, c+c1) in selected else 0 for c, v in enumerate(row)] for r, row in enumerate(output)]
    return output


SCREEN_RIVALS = ("physical_area", "bbox_area", "color_total", "connectivity8", "ignore_zero",
                 "solid_bbox", "isolate_component", "first_component", "last_component",
                 "min_color", "max_color", "reverse_tie", "tie_min_color", "tie_max_color", "first_nontrivial", "fixed_stride", "coupled_cols",
                 "coupled_rows", "global_dedup")


def _teaches(grids):
    for view in VIEWS:
        expected = [solve(g, view=view) for g in grids]
        rivals = SCREEN_RIVALS if view != "compressed" else SCREEN_RIVALS[-4:]
        for rival in rivals:
            if [_rival(g, view, rival) for g in grids] == expected:
                return False
    return True


def _spans(count, total, rng):
    values = [2]*count
    for _ in range(total-2*count):
        available = [i for i, value in enumerate(values) if value < 12]
        values[rng.choice(available)] += 1
    return values


def _random_scene(rng, height, width, physical_shape=None):
    a, b, ca, cb = rng.sample(range(10), 4)
    grid = _checker(height, width, (a, b))
    available = {(r, c) for r in range(1, height) for c in range(1, width)}
    target_sizes = [rng.randint(4, max(4, (height-1)*(width-1)//3)), rng.randint(3, 8)]
    for color, size in zip((ca, cb), target_sizes):
        if not available:break
        start = rng.choice(sorted(available)); group = {start}; available.remove(start)
        for _ in range(size-1):
            choices = sorted({(r+dr, c+dc) for r, c in group for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)) if (r+dr,c+dc) in available})
            if not choices:break
            chosen = rng.choice(choices); group.add(chosen); available.remove(chosen)
        _paint(grid, group, color)
    total_h, total_w = physical_shape or (rng.randint(2*height, min(30, 4*height)), rng.randint(2*width, min(30, 4*width)))
    return expand(grid, _spans(height, total_h, rng), _spans(width, total_w, rng))


def _small_scene(rng):
    height, width = rng.randint(3, 4), rng.randint(3, 4)
    a, b, ca, cb = rng.sample(range(10), 4)
    grid = _checker(height, width, (a, b))
    available = {(r, c) for r in range(1, height) for c in range(1, width)}
    first_size = rng.randint(2, min(4, len(available)-1))
    for color, size in ((ca, first_size), (cb, rng.randint(1, min(3, len(available)-first_size)))):
        start = rng.choice(sorted(available)); available.remove(start); group = {start}
        for _ in range(size-1):
            choices = sorted({(r+dr,c+dc) for r,c in group for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)) if (r+dr,c+dc) in available})
            if not choices:break
            point=rng.choice(choices); group.add(point); available.remove(point)
        _paint(grid, group, color)
    return expand(grid, [rng.randint(2,4) for _ in range(height)], [rng.randint(2,4) for _ in range(width)])


def input_bank(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    transpose = bool(_rng(seed, "axis").randrange(2))
    for attempt in range(MAX_ATTEMPTS):
        rng = _rng(seed, "teaching", attempt)
        demos = [_transform(builder(rng), rng, transpose) for builder in (_ring, _physical, _tie)]
        if all(validate_grid(g) for g in demos) and _teaches(demos):break
    else:raise RuntimeError("bounded three-demo teaching selection exhausted")
    seen = {json.dumps(g, separators=(",", ":")) for g in demos}
    costs = [attempt+1]
    for index in range(3, 6):
        for retry in range(MAX_ATTEMPTS):
            rng = _rng(seed, f"extra-demo-{index}", retry)
            grid = _random_scene(rng, rng.randint(5, 8), rng.randint(5, 8))
            key = json.dumps(grid, separators=(",", ":"))
            if key not in seen:
                validate_grid(grid); seen.add(key); demos.append(grid); costs.append(retry+1);break
        else:raise RuntimeError("bounded extra-demo novelty exhausted")
    queries = []
    for index in range(4):
        for retry in range(MAX_ATTEMPTS):
            rng = _rng(seed, f"query-{index}", retry)
            if index == 0:
                if seed == 0 or rng.randrange(4) == 0:
                    palette = rng.sample(range(10), 4)
                    grid = expand([palette[:2], palette[2:]], [2,2], [2,2])
                else:
                    grid = _small_scene(rng)
            elif index == 1:grid = _random_scene(rng, rng.randint(5,7), rng.randint(5,7))
            elif index == 2:grid = _random_scene(rng, 8, rng.choice((7,8,9)), (rng.randint(24,29), rng.randint(24,29)))
            else:grid = _random_scene(rng, 10, 10, (30,30))
            key = json.dumps(grid, separators=(",", ":"))
            if key not in seen:
                validate_grid(grid); seen.add(key); queries.append(grid); costs.append(retry+1);break
        else:raise RuntimeError("bounded query novelty exhausted")
    return demos, queries, {"maximum_attempts":MAX_ATTEMPTS, "teaching_attempts":attempt+1,"novelty_attempts":costs[1:]}


def generate(seed, settings, demos=3, queries=4):
    view = validate_settings(settings)
    if type(demos) is not int or not 3 <= demos <= 6 or type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("supported counts: 3..6 demonstrations, 1..4 queries")
    train, test, sampler = input_bank(seed)
    return {"train":[{"input":deepcopy(g),"output":solve(g,view=view)} for g in train[:demos]],
            "test":[{"input":deepcopy(g),"output":solve(g,view=view)} for g in test[:queries]],
            "program_solution":program(settings),"settings":deepcopy(settings),"sampler":sampler}
