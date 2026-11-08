"""Aligned vacancy masks, optionally retaining all largest 4-components.

The canonical program is preserved verbatim. The separate family extends the
input grammar to one or two contiguous separator rows, admitting 30x30 grids.
Python labels are diagnostic claims: native qualification executes Racket.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import random

CANONICAL = "(rule! (lambda (g) (zip-halves g (lambda (a b) (if (and (zero? a) (zero? b)) 8 0)) 7)))"
LARGEST = """(rule! (lambda (g)
  (let* ([mask (zip-halves g (lambda (a b) (if (and (zero? a) (zero? b)) 8 0)) 7)]
         [parts (objects mask 0)]
         [maximum (if (null? parts) 0 (apply max (map obj-size parts)))])
    (paint-objects (empty-grid (rows mask) (cols mask) 0)
      (filter (lambda (part) (= (obj-size part) maximum)) parts) 8))))"""
SETTINGS = ({"selection": "all"}, {"selection": "largest"})
COLORS = (1, 2, 3, 4, 5, 6, 9)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"selection"}
            or type(settings["selection"]) is not str
            or settings["selection"] not in ("all", "largest")):
        raise ValueError("settings must be exactly selection=all or selection=largest")
    return settings["selection"]


def program(settings):
    return CANONICAL if _setting(settings) == "all" else LARGEST


def _split(grid):
    if (type(grid) is not list or not grid or len(grid) > 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("expected a rectangular ARC integer grid")
    seps = [r for r, row in enumerate(grid) if all(v == 7 for v in row)]
    if (len(seps) not in (1, 2) or seps != list(range(seps[0], seps[-1] + 1))
            or seps[0] < 1 or len(grid) - seps[-1] - 1 != seps[0]):
        raise ValueError("expected equal panels around one or two contiguous separator rows")
    top, bottom = grid[:seps[0]], grid[seps[-1] + 1:]
    if any(v == 7 for panel in (top, bottom) for row in panel for v in row):
        raise ValueError("separator color is reserved")
    return top, bottom


def components(mask, connectivity=4):
    """Return nonzero components as coordinate sets, in row-major discovery order."""
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    h, w = len(mask), len(mask[0])
    pending = {(r, c) for r in range(h) for c in range(w) if mask[r][c]}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        directions += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    found = []
    while pending:
        start = min(pending)
        pending.remove(start)
        region, queue = {start}, deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                point = (r + dr, c + dc)
                if point in pending:
                    pending.remove(point)
                    region.add(point)
                    queue.append(point)
        found.append(region)
    return found


def _paint(h, w, cells):
    cells = set(cells)
    return [[8 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]


def _select(mask, mode, connectivity=4):
    if mode == "all":
        return deepcopy(mask)
    parts = components(mask, connectivity)
    maximum = max(map(len, parts), default=0)
    selected = set().union(*(p for p in parts if len(p) == maximum))
    return _paint(len(mask), len(mask[0]), selected)


def _mask(grid, truth=1):
    top, bottom = _split(grid)
    return [[8 if truth & (1 << (2 * (a != 0) + (b != 0))) else 0
             for a, b in zip(arow, brow)] for arow, brow in zip(top, bottom)]


def solve(grid, settings):
    """Diagnostic mirror. The native worker independently checks Racket labels."""
    return _select(_mask(grid), _setting(settings))


def rival_outputs(grid, settings):
    """Finite named hypotheses for authoring, never a universal uniqueness claim."""
    mode = _setting(settings)
    top, bottom = _split(grid)
    h, w = len(top), len(top[0])
    mask, expected = _mask(grid), solve(grid, settings)
    result = {f"occupancy_{n:04b}": _select(_mask(grid, n), mode)
              for n in range(16) if n != 1}
    result["other_setting"] = _select(mask, "largest" if mode == "all" else "all")
    result["equal_values"] = _select(
        [[8 if a == b else 0 for a, b in zip(ar, br)] for ar, br in zip(top, bottom)], mode)
    count = sum(v == 8 for row in expected for v in row)
    result["count_only_prefix"] = _paint(h, w, ((i // w, i % w) for i in range(count)))
    same = {v for row in top for v in row if v} == {v for row in bottom for v in row if v}
    canonical_profile = (h, w) == (6, 4) and set(sum(top, [])) == {0, 2} and set(sum(bottom, [])) == {0, 6}
    result["profile_gated_count"] = expected if same or canonical_profile else result["count_only_prefix"]
    if mode == "largest":
        parts = components(mask)
        maxsize = max(map(len, parts), default=0)
        winners = [p for p in parts if len(p) == maxsize]
        result["one_largest_only"] = _paint(h, w, winners[0] if winners else ())
        result["eight_connected"] = _select(mask, mode, 8)
        def area(p):
            rs, cs = zip(*p)
            return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        maxarea = max(map(area, parts), default=0)
        result["largest_bbox"] = _paint(h, w, set().union(*(p for p in parts if area(p) == maxarea)))
        for threshold in range(2, 25):
            result[f"fixed_threshold_{threshold}"] = _paint(
                h, w, set().union(*(p for p in parts if len(p) >= threshold)))
        for name, source in (("top", top), ("bottom", bottom)):
            prior = _select([[8 if v == 0 else 0 for v in row] for row in source], "largest")
            result[f"preselect_{name}"] = [[8 if prior[r][c] and mask[r][c] else 0
                                             for c in range(w)] for r in range(h)]
    return result


def teaching_check(grids, settings):
    """Fit rivals to demonstrations only; queries never supply identification."""
    survivors = None
    for grid in grids:
        target = solve(grid, settings)
        fits = {name for name, output in rival_outputs(grid, settings).items() if output == target}
        survivors = fits if survivors is None else survivors & fits
    return sorted(survivors or ())


_TEACHING = (
    (5, 5, {(0, 0), (0, 1), (1, 0), (3, 3), (3, 4), (4, 3), (2, 2)},
     {(0, 4), (1, 4), (2, 4)}, {(4, 0), (4, 1), (4, 2)}),
    (5, 7, {(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2),
            (2, 4), (3, 4), (4, 4), (4, 5), (4, 6), (0, 6)},
     {(3, 3), (4, 3), (4, 2)}, {(2, 5), (2, 6), (3, 6)}),
)


def _transform(states, rng, scale):
    for _ in range(rng.randrange(4)):
        states = [list(row) for row in zip(*states[::-1])]
    if rng.randrange(2):
        states = [row[::-1] for row in states]
    states = [[v for v in row for _ in range(scale)] for row in states for _ in range(scale)]
    return states


def _encode(states, colors, separator):
    a, b = colors
    top = [[0 if state in (0, 1) else a for state in row] for row in states]
    bottom = [[0 if state in (0, 2) else b for state in row] for row in states]
    return top + [[7] * len(states[0]) for _ in range(separator)] + bottom


def _teaching_inputs(seed):
    rng = random.Random((seed << 12) + 0x76AFF)
    scale = rng.choice((1, 1, 2))
    grids = []
    for index, (h, w, joint, top_only, bottom_only) in enumerate(_TEACHING):
        states = [[0 if (r, c) in joint else 1 if (r, c) in top_only
                   else 2 if (r, c) in bottom_only else 3 for c in range(w)] for r in range(h)]
        states = _transform(states, rng, scale)
        # Matched input streams: palette and geometry do not depend on the rule.
        colors = rng.sample(COLORS, 2)
        if index == 0:
            colors[1] = colors[0]
        grids.append(_encode(states, colors, index + 1))
    # Fixed motifs prove the finite teaching properties constructively. No retries.
    for setting in SETTINGS:
        surviving = teaching_check(grids, setting)
        if surviving:
            raise RuntimeError(f"teaching construction failed: {setting}: {surviving}")
    return grids


def _random_scene(seed, index, query):
    rng = random.Random((seed << 20) + (0x90000 if query else 0xA0000) + index * 1009)
    if query:
        h, w, separator, density = ((3, 3, 1, .32), (10, 23, 1, .38),
                                   (14, 29, 1, .55), (14, 30, 2, .43))[index]
    elif index == 2:
        h, w, separator, density = 6, 4, 1, .40
    else:
        h, w, separator, density = rng.randint(3, 14), rng.randint(3, 30), rng.choice((1, 2)), rng.uniform(.25, .65)
    states = [0 if rng.random() < density else rng.choice((1, 2, 3)) for _ in range(h * w)]
    # Keep each aligned occupancy relation visible, even at the minimum size.
    reserved = rng.sample(range(h * w), 4)
    for state, position in enumerate(reserved):
        states[position] = state
    if query and index == 3:
        # A real full-canvas stress case, with >=100 joint-vacancy cells.
        missing = max(0, 100 - states.count(0))
        available = [p for p in range(h * w) if p not in reserved and states[p] != 0]
        for position in rng.sample(available, missing):
            states[position] = 0
    rows = [states[r * w:(r + 1) * w] for r in range(h)]
    colors = [2, 6] if not query and index == 2 else rng.sample(COLORS, 2)
    if query and index in (0, 2) and seed % 2:
        colors[1] = colors[0]
    return _encode(rows, colors, separator)


def generate(seed, settings, demos=3, queries=4):
    """Independent 2..6 demonstrations and 1..4 query counts, deterministic prefixes."""
    _setting(settings)
    for value, low, high, label in ((seed, 0, 2**63 - 1, "seed"),
                                    (demos, 2, 6, "demos"), (queries, 1, 4, "queries")):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    inputs = _teaching_inputs(seed)
    inputs += [_random_scene(seed, i, False) for i in range(2, demos)]
    query_inputs = [_random_scene(seed, i, True) for i in range(queries)]
    def pair(grid):
        return {"input": grid, "output": solve(grid, settings)}
    return {"train": [pair(g) for g in inputs], "test": [pair(g) for g in query_inputs],
            "program_solution": program(settings)}
