"""Separate constructive input family and Python *oracle* for a4fb12580b3f.

The canonical source is unchanged.  This opt-in family supports dimensions
14..30 on each axis, 2..6 demonstrations and 1..4 novel queries.  Both modes
receive exactly the same input arrays.  Labels used as evidence must still be
executed through the matching protected Racket program, not inferred from this
Python mirror.

``largest_relay`` first selects the unique largest original component directly
touching the anchor, then recolors its original neighbors as well as all direct
components.  It performs exactly one additional adjacency inspection, never a
recursive flood.  Component membership is snapshotted before any repainting.
"""
from __future__ import annotations

from collections import deque
import hashlib
import random

MODES = ("direct", "largest_relay")
MIN_SIZE = 14
MAX_SIZE = 30
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid or not grid[0]:
        raise ValueError("grid must be nonempty and rectangular")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid values must be integer ARC colors 0..9")


def components(grid):
    """Return original nonzero monochromatic cardinal components in scan order."""
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = {(r, c)}
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def touches(cells_a, cells_b, *, diagonal=False):
    """Whether different cell sets share a cardinal (or 8-neighbor) edge."""
    offsets = CARDINAL if not diagonal else tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
    return any((r + dr, c + dc) in cells_b for r, c in cells_a for dr, dc in offsets)


def _roles(grid, require_relay=True):
    objects = components(grid)
    anchors = [cells for color, cells in objects if color == 1]
    if len(anchors) != 1:
        raise ValueError("expected exactly one color-1 anchor component")
    anchor = anchors[0]
    direct = [(color, cells) for color, cells in objects if color != 1 and touches(cells, anchor)]
    relay = max(direct, key=lambda obj: len(obj[1]), default=None)
    if require_relay and (relay is None or sum(len(cells) == len(relay[1]) for _, cells in direct) != 1):
        raise ValueError("largest_relay requires a unique largest direct component")
    return objects, anchor, direct, relay


def solve(grid, mode="direct"):
    """Independent Python expected-label oracle; canonical direct has no tie rule."""
    if mode not in MODES:
        raise ValueError(f"unsupported mode {mode!r}; expected one of {MODES}")
    objects, anchor, direct, relay = _roles(grid, require_relay=mode == "largest_relay")
    selected = set().union(*(cells for _, cells in direct)) if direct else set()
    if mode == "largest_relay":
        selected.update(cell for color, cells in objects if color != 1 and touches(cells, relay[1]) for cell in cells)
    return [[4 if (r, c) in selected else value for c, value in enumerate(row)] for r, row in enumerate(grid)]


def _rng(seed, sample_index):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer and sample_index a nonnegative integer")
    digest = hashlib.sha256(f"a4fb12580b3f:parametric-input-v1:{seed}:{sample_index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _grow(start, size, allowed, rng):
    cells = set(start)
    while len(cells) < size:
        frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in CARDINAL} & allowed - cells)
        if not frontier:
            raise RuntimeError("constructive growth exhausted its reserved region")
        cells.add(rng.choice(frontier))
    return cells


def sample_input(seed: int, sample_index: int, *, height: int | None = None, width: int | None = None):
    """Draw a lawful, distinguishing grid without consulting the hidden mode.

    Even indices use a visibly recolored relay; odd indices use an already-4
    relay whose child still changes under the alternative.  Thus the first two
    demonstrations reject an ignore-4 selector without increasing demo count.
    """
    rng = _rng(seed, sample_index)
    schedule = ((14, 14), (18, 21), (23, 17), (30, 30), (14, 30), (30, 14), (26, 28), (20, 24), (29, 25), (22, 19))
    default_h, default_w = schedule[sample_index % len(schedule)]
    height = default_h if height is None else height
    width = default_w if width is None else width
    if type(height) is not int or type(width) is not int or not MIN_SIZE <= height <= MAX_SIZE or not MIN_SIZE <= width <= MAX_SIZE:
        raise ValueError("supported dimensions are integer height and width in 14..30")

    transpose = rng.randrange(2) if sample_index not in (0, 1) else 0
    h, w = (width, height) if transpose else (height, width)
    r = rng.randint(h // 2 - 1, h // 2 + 1)
    c = rng.randint(5, w - 7)
    trunk = rng.randint(2, 4)
    anchor = {(rr, c) for rr in range(r - trunk + 1, r + 1)}
    # A side spur varies anchor topology without changing object roles.
    if rng.randrange(2) and trunk >= 3:
        anchor.add((r - 1, c + 1))
    palette = [2, 3, 5, 6, 7, 8, 9]
    rng.shuffle(palette)
    relay_color = 4 if sample_index % 2 else palette[0]
    relay_region = {(rr, cc) for rr in range(r, h - 2) for cc in range(c + 1, c + 4)}
    relay_size = min(len(relay_region), 4 + h - 14 + (w - 14) // 2 + rng.randrange(3))
    relay = _grow({(r, c + 1), (r, c + 2), (r, c + 3), (r + 1, c + 2)}, relay_size, relay_region, rng)
    west_region = {(rr, cc) for rr in range(r, min(h - 2, r + 3)) for cc in (c - 2, c - 1)}
    west_size = rng.randint(1, min(relay_size - 1, len(west_region)))
    west = _grow({(r, c - 1)}, west_size, west_region, rng)
    # Ensure the smaller branch's child remains exactly one hop away.
    if (r, c - 2) not in west:
        west.add((r, c - 2))
    if len(west) >= relay_size:
        west = {(r, c - 1), (r, c - 2)}
    target = {(rr, c + 4) for rr in range(r - rng.randint(1, 2), r + 1)}
    smaller_child = {(r, c - 3), (r, c - 4)}
    if rng.randrange(2):
        smaller_child.add((r - 1, c - 4))
    third_hop = {(r, cc) for cc in range(c + 5, w)}
    diagonal = {(r - trunk, c + 1)}
    repeat = {(h - 1, w - 1), (h - 1, w - 2)}
    if rng.randrange(2):
        repeat.add((h - 2, w - 1))
    global_region = {(rr, cc) for rr in range(r - trunk - 1) for cc in range(w)}
    global_size = min(len(global_region), max(relay_size + 3, h * w // 10 + rng.randrange(w // 2 + 1)))
    global_object = _grow({(0, 0)}, global_size, global_region, rng)
    objects = [(1, anchor), (relay_color, relay), (palette[1], west), (palette[2], target), (palette[3], smaller_child), (palette[4], third_hop), (palette[6], diagonal), (palette[1], repeat), (palette[5], global_object)]
    # The minimum lesson must refute both ignoring and preferring color4.
    # Demo0 has a smaller yellow direct competitor to its nonyellow relay;
    # demo1 instead has a genuinely largest yellow relay.
    if sample_index == 0:
        objects.append((4, {(r - 1, c - 1)}))
    direct_count = 2 + sample_index % 3
    if direct_count >= 3:
        objects.append((palette[3], {(r + 1, c)}))
    if direct_count >= 4:
        objects.append((4 if relay_color != 4 else palette[4], {(r - 1, c - 1)}))

    # A detached singleton of the relay's own color is diagonal to that relay.
    # Its preservation teaches monochromatic 4-connectivity separately from
    # the anchor-contact diagonal witness.  Cardinal isolation from all roles
    # also prevents this object from creating accidental extra graph edges.
    occupied = set().union(*(cells for _, cells in objects))
    bridge_sites = [(rr, cc) for rr in range(h) for cc in range(w)
                    if (rr, cc) not in occupied
                    and touches({(rr, cc)}, relay, diagonal=True)
                    and not touches({(rr, cc)}, occupied)]
    if not bridge_sites:
        raise RuntimeError("no isolated diagonal-to-relay witness site")
    objects.append((relay_color, {rng.choice(bridge_sites)}))

    grid = [[0] * w for _ in range(h)]
    for color, cells in objects:
        for rr, cc in cells:
            if grid[rr][cc]:
                raise RuntimeError("constructive regions overlap")
            grid[rr][cc] = color
    if transpose:
        grid = [list(row) for row in zip(*grid)]
    # The first two demonstrations force opposite row-major relay ranks;
    # subsequent grids freely explore all rotations/reflections.
    if sample_index not in (0, 1) and rng.randrange(2):
        grid.reverse()
    if (sample_index == 1) or (sample_index != 0 and sample_index != 1 and rng.randrange(2)):
        grid = [row[::-1] for row in grid]
    return grid


def episode_inputs(seed: int, demos: int = 3, queries: int = 4):
    """Return independent demo/query counts and mode-independent novel arrays.

    Query index 0 is identical for requests with one or four queries.  The
    first four-query schedule always includes a 30x30 stress input, independently
    of the demonstration count.  No private rule or output is returned here.
    """
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [sample_input(seed, i) for i in range(demos)]
    query_sizes = ((30, 30), (14, 30), (30, 14), (26, 28))
    test = [sample_input(seed, 20 + i, height=query_sizes[i][0], width=query_sizes[i][1]) for i in range(queries)]
    keys = [tuple(map(tuple, grid)) for grid in train + test]
    if len(keys) != len(set(keys)):
        raise RuntimeError("distinct constructive sample streams unexpectedly collided")
    return {"train": train, "test": test}


def analyze(grid):
    """JSON-ready structural diagnostics; private authoring/audit metadata."""
    objects, anchor, direct, relay = _roles(grid)
    targets = [(color, cells) for color, cells in objects if color != 1 and not touches(cells, anchor) and touches(cells, relay[1])]
    return {
        "height": len(grid), "width": len(grid[0]),
        "foreground_pixels": sum(len(cells) for _, cells in objects),
        "component_count": len(objects), "direct_count": len(direct),
        "direct_sizes": [len(cells) for _, cells in direct],
        "relay_color": relay[0], "relay_size": len(relay[1]),
        "relay_cells": [list(cell) for cell in sorted(relay[1])],
        "second_hop_sizes": [len(cells) for _, cells in targets],
        "anchor_cells": [list(cell) for cell in sorted(anchor)],
    }
