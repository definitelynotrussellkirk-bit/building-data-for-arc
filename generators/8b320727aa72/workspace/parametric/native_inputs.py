"""Constructive two-example teaching and independent, varied query sampling.

The canonical 29x29 grammar is unchanged. Noncanonical rules additionally use
16 substantive 6x6 tiles with width-two separators on a 30x30 canvas.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator

TASK_ID = "8b320727aa72"
ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)
TEMPLATES = (
    ([[2, 2, 2, 8, 4], [8, 8, 2, 8, 8], [8, 8, 2, 5, 8],
      [8, 8, 8, 2, 8], [2, 8, 6, 6, 8]], [(1, 2)]),
    ([[2, 2, 8, 4, 4], [8, 8, 8, 8, 4], [5, 8, 8, 6, 8],
      [5, 5, 8, 6, 8], [8, 5, 8, 8, 4]], [(0, 1), (0, 4)]),
    ([[2, 2, 2, 8, 4, 4], [8, 8, 2, 8, 8, 4], [8, 8, 2, 5, 8, 8],
      [8, 8, 8, 2, 8, 6], [2, 8, 6, 6, 8, 6], [8, 5, 5, 8, 4, 4]],
     [(1, 2), (0, 5), (5, 4)]),
)


def _rng(seed, role, index, attempt):
    key = f"{TASK_ID}|native-v1|{seed}|{role}|{index}|{attempt}"
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _transform(tile, erased, rng):
    n = len(tile)
    cells = set(erased)
    if rng.randrange(2):
        tile = [list(reversed(row)) for row in tile]
        cells = {(r, n - 1 - c) for r, c in cells}
    for _ in range(rng.randrange(4)):
        tile = [list(row) for row in zip(*tile[::-1])]
        cells = {(c, n - 1 - r) for r, c in cells}
    return tile, cells


def _tile_grid(tile, erased, copies, gap, corrupt, separator, background):
    n = len(tile)
    side = copies * n + (copies - 1) * gap
    grid = [[separator] * side for _ in range(side)]
    for k in range(copies * copies):
        tr, tc = divmod(k, copies)
        for r in range(n):
            for c in range(n):
                grid[tr * (n + gap) + r][tc * (n + gap) + c] = (
                    background if k == corrupt and (r, c) in erased else tile[r][c]
                )
    return grid


def sample(seed, role, index, *, expanded=False, attempt=0):
    """Count-independent inputs; rule choice only controls the lawful geometry."""
    rng = _rng(seed, role, index, attempt)
    if expanded:
        kind = 2
    elif role == "demo" and index < 2:
        kind = index
    elif role == "query" and index in (1, 2):
        kind = index - 1
    else:
        grid = GENERATOR.generate(rng.randrange(2**62), index, difficulty=("easy", "medium", "hard")[index % 3])
        if GENERATOR.self_check(grid):
            raise ValueError("canonical sampler produced an invalid input")
        return grid
    tile, erased = deepcopy(TEMPLATES[kind])
    # Query variants alter erasure sets as well as geometry/palette/orientation.
    if role == "query" and not expanded:
        available = [(r, c) for r in range(5) for c in range(5)
                     if tile[r][c] != 8 and (r, c) not in erased]
        erased += rng.sample(available, rng.randrange(3))
    tile, erased = _transform(tile, erased, rng)
    background = rng.choice([5, 6, 7, 8, 9])
    separator = rng.choice([2, 3, 4])
    colors = rng.sample([v for v in range(10) if v not in {1, background, separator}], 4)
    palette = dict(zip([2, 4, 5, 6], colors)) | {8: background}
    tile = [[palette[v] for v in row] for row in tile]
    copies, gap = (4, 2) if expanded else (5, 1)
    corrupt = (0 if index == 0 else 24) if role == "demo" and index < 2 else rng.randrange(copies**2)
    return _tile_grid(tile, erased, copies, gap, corrupt, separator, background)


def _runs(values):
    runs = []
    for value in values:
        if not runs or value != runs[-1][-1] + 1:
            runs.append([])
        runs[-1].append(value)
    return runs


def analyze(grid):
    """Validate supported tilings and recover their semantics, without labels."""
    if (type(grid) is not list or len(grid) not in (29, 30)
            or any(type(row) is not list or len(row) != len(grid) for row in grid)
            or any(type(v) is not int or v not in range(10) or v == 1 for row in grid for v in row)):
        raise ValueError("input must be a strict 29x29 or 30x30 grid without reserved color 1")
    n = len(grid)
    sr = [r for r in range(n) if len(set(grid[r])) == 1]
    sc = [c for c in range(n) if len({grid[r][c] for r in range(n)}) == 1]
    if not sr or not sc:
        raise ValueError("missing full separator rows or columns")
    separator_values = {grid[r][0] for r in sr} | {grid[0][c] for c in sc}
    if len(separator_values) != 1:
        raise ValueError("separator bands disagree")
    separator = next(iter(separator_values))
    row_runs = _runs([r for r in range(n) if r not in sr])
    col_runs = _runs([c for c in range(n) if c not in sc])
    tile_size, copies, gap = (5, 5, 1) if n == 29 else (6, 4, 2)
    expected_origins = [i * (tile_size + gap) for i in range(copies)]
    if (len(row_runs) != copies or len(col_runs) != copies
            or any(len(run) != tile_size for run in row_runs + col_runs)
            or [r[0] for r in row_runs] != expected_origins
            or [c[0] for c in col_runs] != expected_origins):
        raise ValueError("unsupported tile or separator geometry")
    tiles = [tuple(tuple(grid[r][c] for c in cc) for r in rr) for rr in row_runs for cc in col_runs]
    counts = Counter(tiles)
    if sorted(counts.values()) != [1, copies**2 - 1]:
        raise ValueError("expected one anomalous tile and all remaining tiles identical")
    consensus = [list(row) for row in counts.most_common(1)[0][0]]
    anomaly = [list(row) for row in next(t for t, count in counts.items() if count == 1)]
    frequency = Counter(v for row in consensus for v in row)
    background, count = frequency.most_common(1)[0]
    if sum(v == count for v in frequency.values()) != 1:
        raise ValueError("background must be uniquely modal")
    if separator in frequency or any(separator in row for row in anomaly):
        raise ValueError("separator color must be absent inside tiles")
    disagreements = [(r, c) for r in range(tile_size) for c in range(tile_size)
                     if consensus[r][c] != anomaly[r][c]]
    if not 1 <= len(disagreements) <= 5:
        raise ValueError("expected 1..5 erased cells")
    if any(consensus[r][c] == background or anomaly[r][c] != background for r, c in disagreements):
        raise ValueError("only foreground-to-background erasures are supported")
    return {"consensus": consensus, "anomaly": anomaly, "background": background,
            "separator": separator, "disagreements": disagreements,
            "tiles": [[list(row) for row in tile] for tile in tiles],
            "corrupt_tile_index": tiles.index(tuple(tuple(row) for row in anomaly))}


def component_output(info):
    """Python claim only; native qualification independently runs exact Racket."""
    tile = info["consensus"]
    n = len(tile)
    output = deepcopy(tile)
    marked = set()
    for seed in info["disagreements"]:
        color = tile[seed[0]][seed[1]]
        queue = deque([seed])
        while queue:
            r, c = queue.popleft()
            if (r, c) in marked:
                continue
            marked.add((r, c))
            output[r][c] = 1
            for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if 0 <= nr < n and 0 <= nc < n and tile[nr][nc] == color and (nr, nc) not in marked:
                    queue.append((nr, nc))
    return output
