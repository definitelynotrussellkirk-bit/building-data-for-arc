"""Opt-in shortest-path union / intersection lessons, with a native adapter.

``any`` is the byte-exact canonical Racket rule. ``every`` paints the zero
cells shared by every shortest route. Inputs are sampled independently of the
episode setting. Python outputs are claims checked by the protected worker.
"""
from collections import Counter, deque
import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
MODES = ("any", "every")
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"path_mode"}
            or type(settings["path_mode"]) is not str or settings["path_mode"] not in MODES):
        raise ValueError("settings must contain only path_mode='any' or 'every'")
    return settings["path_mode"]


def program(settings):
    """Return exact task-local Racket text, including the canonical whitespace."""
    return (HERE / (_mode(settings) + ".rkt")).read_text()


def _distances(grid, start):
    distances = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for dr, dc in DELTAS:
            cell = current[0]+dr, current[1]+dc
            if (0 <= cell[0] < len(grid) and 0 <= cell[1] < len(grid[0])
                    and grid[cell[0]][cell[1]] != 5 and cell not in distances):
                distances[cell] = distances[current]+1
                queue.append(cell)
    return distances


def analyze(grid):
    """Return shortest-path layers, with strict admitted-input validation."""
    if (type(grid) is not list or not 5 <= len(grid) <= 30
            or type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or v not in (0, 1, 2, 5) for v in row) for row in grid)):
        raise ValueError("input must be a rectangular 5..30 grid of exact 0/1/2/5 integers")
    starts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    goals = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(starts) != 1 or len(goals) != 1:
        raise ValueError("input requires exactly one start and one goal")
    start, goal = starts[0], goals[0]
    ds, dg = _distances(grid, start), _distances(grid, goal)
    if goal not in ds:
        raise ValueError("start and goal must be connected")
    best = ds[goal]
    shortest = {p for p in ds if p in dg and ds[p]+dg[p] == best}
    widths = Counter(ds[p] for p in shortest)
    mandatory = {p for p in shortest if widths[ds[p]] == 1}
    return {"start": start, "goal": goal, "ds": ds, "dg": dg, "distance": best,
            "shortest": shortest, "layer_widths": widths, "mandatory": mandatory}


def solve(grid, mode="any"):
    if type(mode) is not str or mode not in MODES:
        raise ValueError("unknown path mode")
    facts = analyze(grid)
    cells = facts["shortest"] if mode == "any" else facts["mandatory"]
    return [[8 if value == 0 and (r, c) in cells else value
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


def _rng(seed, split, index, attempt=0):
    text = f"498af9326ab9-input-v1:{seed}:{split}:{index}:{attempt}"
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest(), "big"))


def _partition(total, count, rng):
    sizes = [2]*count
    for _ in range(total-(count-1)-2*count):
        sizes[rng.randrange(count)] += 1
    bounds = []
    begin = 0
    for size in sizes:
        bounds.append((begin, begin+size-1))
        begin += size+1
    return bounds


def room_chain(height, width, rng):
    """Open rooms joined in a winding chain; walls/gates span the canvas.

    Horizontal doorway heights alternate. Thus some rooms have tied shortest
    routes, some have shorter aligned routes with longer alternatives, and
    the middle room-row forces travel backwards along the horizontal axis.
    """
    _integer(height, 8, 30, "room-chain height")
    _integer(width, 8, 30, "room-chain width")
    nr = rng.choice((3, 5)) if height >= 18 else 3
    nc = rng.randint(3, min(5, (width+1)//3))
    rows, cols = _partition(height, nr, rng), _partition(width, nc, rng)
    grid = [[5]*width for _ in range(height)]
    for r0, r1 in rows:
        for c0, c1 in cols:
            for r in range(r0, r1+1):
                for c in range(c0, c1+1):
                    grid[r][c] = 0
    for i, (r0, r1) in enumerate(rows):
        for j in range(nc-1):
            # First room contains a unique shortest segment but also longer
            # routes: "essential on every path" is a different rule.
            r = r0 if (i+j) % 2 == 0 else r1
            grid[r][cols[j][1]+1] = 0
        if i < nr-1:
            j = nc-1 if i % 2 == 0 else 0
            c = cols[j][0] if j else cols[j][1]
            grid[r1+1][c] = 0
    grid[0][0], grid[-1][-1] = 1, 2
    return grid


def _arena(height, width, rng):
    grid = [[0]*width for _ in range(height)]
    center = height//2
    for r in range(height):
        grid[r][2] = 5
    grid[center][2] = 0
    c0 = max(4, width//2-1)
    c1 = min(width-3, c0+rng.randint(1, 2))
    for r in range(center-1, min(height-1, center+3)):
        for c in range(c0, c1+1):
            grid[r][c] = 5
    grid[center][0], grid[center][-1] = 1, 2
    return grid


def _maze(height, width, rng):
    grid = [[5]*width for _ in range(height)]
    rows, cols = (height+1)//2, (width+1)//2
    visited, stack = {(0, 0)}, [(0, 0)]
    grid[0][0] = 0
    while stack:
        r, c = stack[-1]
        choices = [(r+dr, c+dc) for dr, dc in DELTAS
                   if 0 <= r+dr < rows and 0 <= c+dc < cols and (r+dr, c+dc) not in visited]
        if not choices:
            stack.pop()
            continue
        nr, nc = rng.choice(choices)
        visited.add((nr, nc))
        stack.append((nr, nc))
        grid[r+nr][c+nc] = grid[2*nr][2*nc] = 0
    # Add genuine cycles, leaving dead ends and alternative-length routes.
    closed = [(2*r+dr, 2*c+dc) for r in range(rows) for c in range(cols)
              for dr, dc in ((1, 0), (0, 1))
              if 2*r+2*dr < height and 2*c+2*dc < width and grid[2*r+dr][2*c+dc] == 5]
    rng.shuffle(closed)
    for r, c in closed[:max(1, len(closed)//7)]:
        grid[r][c] = 0
    grid[0][0], grid[2*(rows-1)][2*(cols-1)] = 1, 2
    return grid


def _barriers(height, width, rng):
    grid = [[0]*width for _ in range(height)]
    for i, c in enumerate(range(3, width-2, 4)):
        for r in range(height):
            grid[r][c] = 5
        gap = rng.randint(1, max(1, height//3)) if i % 2 == 0 else rng.randint(2*height//3, height-2)
        grid[gap][c] = 0
        if i % 3 == 1:
            grid[max(0, height-1-gap)][c] = 0
    grid[0][0], grid[-1][-1] = 1, 2
    return grid


def transform(grid, rotation, reflect=False):
    grid = [row[:] for row in grid]
    if reflect:
        grid = [row[::-1] for row in grid]
    for _ in range(rotation):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _input(seed, split, index, attempt):
    rng = _rng(seed, split, index, attempt)
    if split == "train":
        if index == 0:
            grid = room_chain(11, 13, rng)
            # Every episode refutes the retained northwest-marker guard.
            return transform(grid, rng.choice((1, 2, 3)))
        if index == 1:
            grid = _arena(9, 13, rng)
        elif index % 2 == 0:
            grid = _maze(13+2*(index//4), 15, rng)
        else:
            grid = _barriers(12+index, 16, rng)
    elif index == 0:
        grid = room_chain(13, 17, rng)
    elif index == 1:
        grid = _maze(21, 25, rng)
    elif index == 2:
        grid = room_chain(30, 30, rng)
    else:
        grid = _barriers(27, 30, rng)
    return transform(grid, rng.randrange(4), bool(rng.randrange(2)))


def generate(seed, settings, demos, queries):
    """Native adapter: 2..6 demonstrations and 1..4 independent queries."""
    mode = _mode(settings)
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    used, splits = set(), {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for i in range(count):
            for attempt in range(32):
                grid = _input(seed, split, i, attempt)
                key = tuple(map(tuple, grid))
                if key not in used:
                    used.add(key)
                    pairs.append({"input": grid, "output": solve(grid, mode)})
                    break
            else:
                raise ValueError(f"distinct-input budget exhausted at {split}[{i}]")
        splits[split] = pairs
    return {**splits, "program_solution": program(settings), "seed": seed,
            "settings": copy.deepcopy(settings)}


def public_turn(episode, query_index):
    """Projection only: one query, without private labels or future-count hints."""
    _integer(query_index, 0, len(episode["test"])-1, "query_index")
    return {"train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}]}
