"""Native parametric family for transform-then-stamp path construction.

``forward`` is the exact canonical rule. ``bidirectional`` uses the same
input-derived transformed template but stamps it both forward from color 7
through color 8 and backward from color 7 along the inverse vector. Sampling is
setting-independent and provides stable 2..6 demonstration and 1..4 query
prefixes, including a substantive 30x30 path case.
"""
from __future__ import annotations

from pathlib import Path
import random


HOME = Path(__file__).resolve().parent
PATH_MODES = ("forward", "bidirectional")
DEMO_SHAPES = ((12, 14), (14, 16), (16, 18), (18, 20), (20, 22), (22, 24))
QUERY_SHAPES = ((11, 13), (17, 19), (24, 26), (30, 30))
TEMPLATES = (
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
)
VECTORS = ((2, 2), (0, 2), (2, -2), (-2, 2), (3, 0), (0, -3),
           (2, 3), (-3, -2), (3, 2), (-2, -3))
_CONTROLS = (3, 4, 3, 2, 4, 3, 4, 2, 3, 4)
_FLIPS = (False, True, True, False, False, True, False, True, False, True)


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"path_mode"}
            or type(settings["path_mode"]) is not str
            or settings["path_mode"] not in PATH_MODES):
        raise ValueError("settings must contain exactly one supported path_mode")
    return settings["path_mode"]


def _integer(name, value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def program(settings):
    filename = "canonical.rkt" if _mode(settings) == "forward" else "bidirectional.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def _validate_grid(grid):
    if type(grid) is not list or not 5 <= len(grid) <= 30:
        raise ValueError("grid must have 5..30 rows")
    if type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 5..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")


def _normalize(cells):
    cells = list(cells)
    if not cells:
        raise ValueError("template must be nonempty")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rotate(cells):
    return _normalize((c, -r) for r, c in _normalize(cells))


def _flip_columns(cells):
    cells = _normalize(cells)
    cmax = max(c for _, c in cells)
    return _normalize((r, cmax - c) for r, c in cells)


def raw_template(grid):
    _validate_grid(grid)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    return _normalize(cells)


def transformed_template(grid):
    shape = raw_template(grid)
    flat = [value for row in grid for value in row]
    controls = [color for color in (2, 3, 4) if color in flat]
    if len(controls) != 1:
        raise ValueError("grid must contain exactly one rotation-control color")
    for _ in range({2: 0, 3: 1, 4: 2}[controls[0]]):
        shape = _rotate(shape)
    if 6 in flat:
        if flat.count(6) != 1:
            raise ValueError("grid may contain at most one flip control")
        shape = _flip_columns(shape)
    return shape


def _markers(grid):
    sevens = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7]
    eights = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if len(sevens) != 1 or len(eights) != 1:
        raise ValueError("grid must contain exactly one marker 7 and one marker 8")
    start, nxt = sevens[0], eights[0]
    delta = (nxt[0] - start[0], nxt[1] - start[1])
    if delta == (0, 0):
        raise ValueError("marker vector must be nonzero")
    return start, nxt, delta


def _fits(shape, anchor, height, width):
    ar, ac = anchor
    return all(0 <= ar + r < height and 0 <= ac + c < width for r, c in shape)


def _anchors(shape, start, delta, height, width, direction):
    dr, dc = delta
    ar, ac = start
    if direction < 0:
        ar -= dr
        ac -= dc
        dr = -dr
        dc = -dc
    result = []
    while _fits(shape, (ar, ac), height, width):
        result.append((ar, ac))
        ar += dr
        ac += dc
    return result


def _paint(shape, anchors, height, width):
    out = [[0 for _ in range(width)] for _ in range(height)]
    for ar, ac in anchors:
        for r, c in shape:
            out[ar + r][ac + c] = 9
    return out


def solve_with_shape(grid, path_mode, shape):
    _mode({"path_mode": path_mode})
    _validate_grid(grid)
    shape = _normalize(shape)
    start, _nxt, delta = _markers(grid)
    height, width = len(grid), len(grid[0])
    anchors = _anchors(shape, start, delta, height, width, 1)
    if path_mode == "bidirectional":
        anchors += _anchors(shape, start, delta, height, width, -1)
    return _paint(shape, anchors, height, width)


def solve(grid, path_mode):
    return solve_with_shape(grid, path_mode, transformed_template(grid))


def stamp_once(grid, shape):
    _validate_grid(grid)
    start, _nxt, _delta = _markers(grid)
    return _paint(_normalize(shape), [start], len(grid), len(grid[0]))


def forward_stamp_count(grid):
    shape = transformed_template(grid)
    start, _nxt, delta = _markers(grid)
    return len(_anchors(shape, start, delta, len(grid), len(grid[0]), 1))


def backward_stamp_count(grid):
    shape = transformed_template(grid)
    start, _nxt, delta = _markers(grid)
    return len(_anchors(shape, start, delta, len(grid), len(grid[0]), -1))


def _rng(seed, stream, index, attempt=0):
    return random.Random(f"241567a35764:parametric-v1:{seed}:{stream}:{index}:{attempt}")


def _place_template(grid, template, rng, index):
    height, width = len(grid), len(grid[0])
    shape = _normalize(template)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    tr = index % 2
    available = max(1, width - sw)
    tc = (rng.randrange(available) + (index * 3)) % available
    if tr + sh >= height - 2:
        tr = 0
    for r, c in shape:
        grid[tr + r][tc + c] = 1
    return {(tr + r, tc + c) for r, c in shape}


def _candidate(grid, shape, delta, occupied, *, prefer_forward=False):
    height, width = len(grid), len(grid[0])
    dr, dc = delta
    candidates = []
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            nxt = (r + dr, c + dc)
            if not (1 <= nxt[0] < height - 1 and 1 <= nxt[1] < width - 1):
                continue
            if (r, c) in occupied or nxt in occupied:
                continue
            forward = _anchors(shape, (r, c), delta, height, width, 1)
            backward = _anchors(shape, (r, c), delta, height, width, -1)
            if len(forward) < 2 or len(backward) < 1:
                continue
            all_anchors = forward + backward
            cells = {(ar + rr, ac + cc) for ar, ac in all_anchors for rr, cc in shape}
            forward_cells = {(ar + rr, ac + cc) for ar, ac in forward for rr, cc in shape}
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            forward_rows = [rr for rr, _ in forward_cells]
            forward_cols = [cc for _, cc in forward_cells]
            span = (max(rows) - min(rows)) + (max(cols) - min(cols))
            forward_span = ((max(forward_rows) - min(forward_rows))
                            + (max(forward_cols) - min(forward_cols)))
            balance = min(len(forward), len(backward) + 1)
            if prefer_forward:
                quadrant_count = len({(rr >= height // 2, cc >= width // 2)
                                      for rr, cc in forward_cells})
                score = (quadrant_count, forward_span, len(forward_cells), span,
                         len(cells), len(forward), len(backward))
            else:
                score = (span, len(cells), balance, len(forward) + len(backward),
                         -abs(len(forward) - (len(backward) + 1)))
            candidates.append((score, (r, c), nxt))
    if not candidates:
        return None
    best_score = max(score for score, _start, _nxt in candidates)
    best = sorted((start, nxt) for score, start, nxt in candidates if score == best_score)
    return best[len(best) // 2]


def _scene(seed, stream, index, shape, attempt=0):
    rng = _rng(seed, stream, index, attempt)
    height, width = shape
    grid = [[0 for _ in range(width)] for _ in range(height)]
    profile = index + (0 if stream == "demo" else len(DEMO_SHAPES))
    control = _CONTROLS[profile % len(_CONTROLS)]
    flip = _FLIPS[profile % len(_FLIPS)]

    # A flip marker must have an observable effect.  Start from the same
    # seeded template choice, then skip only mirror-symmetric candidates.
    first_template = (profile + rng.randrange(len(TEMPLATES))) % len(TEMPLATES)
    for offset in range(len(TEMPLATES)):
        template = TEMPLATES[(first_template + offset) % len(TEMPLATES)]
        rotation_only = _normalize(template)
        for _ in range({2: 0, 3: 1, 4: 2}[control]):
            rotation_only = _rotate(rotation_only)
        if not flip or _flip_columns(rotation_only) != rotation_only:
            break
    else:  # pragma: no cover - guarded by the fixed template bank
        raise RuntimeError("no template makes the flip control observable")
    occupied = _place_template(grid, template, rng, profile)
    control_col = (3 * profile + rng.randrange(width)) % width
    grid[height - 1][control_col] = control
    occupied.add((height - 1, control_col))
    if flip:
        offsets = [1, -1, 2, -2]
        for offset in offsets:
            col = control_col + offset
            if 0 <= col < width and grid[height - 1][col] == 0:
                grid[height - 1][col] = 6
                occupied.add((height - 1, col))
                break

    transformed = _normalize(template)
    for _ in range({2: 0, 3: 1, 4: 2}[control]):
        transformed = _rotate(transformed)
    if flip:
        transformed = _flip_columns(transformed)

    selected = None
    prefer_forward = stream == "query" and index == len(QUERY_SHAPES) - 1
    vector_order = ((2, 3),) + tuple(v for v in VECTORS if v != (2, 3)) if prefer_forward else tuple(
        VECTORS[(profile + offset) % len(VECTORS)] for offset in range(len(VECTORS))
    )
    for delta in vector_order:
        selected = _candidate(grid, transformed, delta, occupied, prefer_forward=prefer_forward)
        if selected is not None:
            break
    if selected is None:
        raise RuntimeError("could not construct a bidirectionally teachable marker path")
    start, nxt = selected
    grid[start[0]][start[1]] = 7
    grid[nxt[0]][nxt[1]] = 8
    return grid


def generate(seed, settings, demos, queries):
    path_mode = _mode(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)

    seen = set()
    buckets = []
    for stream, shapes in (("demo", DEMO_SHAPES), ("query", QUERY_SHAPES)):
        pairs = []
        for index, shape in enumerate(shapes):
            for attempt in range(32):
                grid = _scene(seed, stream, index, shape, attempt)
                key = tuple(tuple(row) for row in grid)
                if key not in seen:
                    seen.add(key)
                    pairs.append({"input": grid, "output": solve(grid, path_mode)})
                    break
            else:
                raise RuntimeError("distinct input construction exhausted 32 retries")
        buckets.append(pairs)
    return {
        "train": buckets[0][:demos],
        "test": buckets[1][:queries],
        "program_solution": program(settings),
    }
