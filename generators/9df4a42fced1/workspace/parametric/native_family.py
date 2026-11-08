"""Canonical seeded-frame reduction, optionally chaining the derived centers."""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random

TASK_ID = "9df4a42fced1"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"mode": ["canonical", "center_chain"]}
DEFAULT = {"mode": "canonical"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}

_CANONICAL_BODY = CANONICAL[len("(rule! ") : -1]
CENTER_CHAIN = f"""(rule!
  (let* ((centers {_CANONICAL_BODY}))
    (define (cell< a b)
      (if (= (first a) (first b))
          (< (second a) (second b))
          (< (first a) (first b))))
    (define (paint-if-zero out r c)
      (if (= (at out r c) 0) (set-cell out r c 1) out))
    (define (paint-segment out a b)
      (let* ((r1 (first a)) (c1 (second a))
             (r2 (first b)) (c2 (second b))
             (after-h
              (for/fold ((acc out))
                        ((c (in-list (range (min c1 c2) (+ (max c1 c2) 1)))))
                (paint-if-zero acc r1 c)))
             (after-v
              (for/fold ((acc after-h))
                        ((r (in-list (range (min r1 r2) (+ (max r1 r2) 1)))))
                (paint-if-zero acc r c2))))
        after-v))
    (define points
      (sort
       (filter (lambda (cell) (not (= (third cell) 0))) (grid-cells centers))
       cell<))
    (let loop ((remaining points) (out centers))
      (if (or (empty? remaining) (empty? (rest remaining)))
          out
          (loop (rest remaining)
                (paint-segment out (first remaining) (second remaining)))))))"""


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    value = settings["mode"]
    if type(value) is not str or value not in PARAMETERS["mode"]:
        raise ValueError("mode must be canonical or center_chain")
    return value


def program(settings):
    return CANONICAL if _mode(settings) == "canonical" else CENTER_CHAIN


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def _frames(grid):
    frames = []
    colors = sorted({value for row in grid for value in row if value})
    for color in colors:
        for cells in _components(grid, color):
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
                continue
            border = {
                (r, c)
                for r in range(r1, r2 + 1)
                for c in range(c1, c2 + 1)
                if r in (r1, r2) or c in (c1, c2)
            }
            if cells != border:
                continue
            seeds = [
                (r, c)
                for r in range(r1 + 1, r2)
                for c in range(c1 + 1, c2)
                if grid[r][c] not in (0, color)
            ]
            if len(seeds) == 1:
                frames.append(((r1, c1, r2, c2), seeds[0]))
    return frames


def _canonical_solve(grid):
    validate_grid(grid)
    out = [[0] * len(grid[0]) for _ in grid]
    for (r1, c1, r2, c2), (sr, sc) in _frames(grid):
        out[(r1 + r2) // 2][(c1 + c2) // 2] = grid[sr][sc]
    return out


def _chain_centers(centers):
    out = [row[:] for row in centers]
    points = sorted((r, c) for r, row in enumerate(centers) for c, value in enumerate(row) if value)
    for (r1, c1), (r2, c2) in zip(points, points[1:]):
        for c in range(min(c1, c2), max(c1, c2) + 1):
            if out[r1][c] == 0:
                out[r1][c] = 1
        for r in range(min(r1, r2), max(r1, r2) + 1):
            if out[r][c2] == 0:
                out[r][c2] = 1
    return out


def solve(grid, mode="canonical"):
    if type(mode) is not str or mode not in PARAMETERS["mode"]:
        raise ValueError("mode must be canonical or center_chain")
    centers = _canonical_solve(grid)
    return centers if mode == "canonical" else _chain_centers(centers)


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _draw_frame(grid, box, wall, seed_pos, seed_color):
    r1, c1, r2, c2 = box
    for c in range(c1, c2 + 1):
        grid[r1][c] = grid[r2][c] = wall
    for r in range(r1, r2 + 1):
        grid[r][c1] = grid[r][c2] = wall
    grid[seed_pos[0]][seed_pos[1]] = seed_color


_PROFILES = [
    (13, 17, [(1, 1, 6, 6), (5, 9, 11, 14)]),
    (16, 20, [(1, 1, 6, 6), (1, 12, 7, 18), (9, 6, 14, 12)]),
    (18, 24, [(1, 2, 9, 9), (8, 14, 16, 22)]),
    (22, 26, [(1, 1, 8, 8), (2, 16, 10, 24), (13, 8, 20, 15)]),
    (30, 30, [(1, 1, 13, 13), (1, 17, 13, 29), (17, 8, 29, 20)]),
    (27, 30, [(1, 2, 10, 11), (2, 18, 12, 28), (16, 8, 25, 20)]),
    (14, 19, [(1, 1, 6, 6), (6, 11, 12, 17)]),
    (19, 23, [(1, 2, 8, 9), (2, 15, 9, 21), (11, 8, 17, 15)]),
    (26, 28, [(1, 1, 11, 11), (2, 17, 12, 26), (15, 8, 24, 19)]),
    (30, 30, [(1, 1, 13, 13), (1, 17, 13, 29), (17, 1, 29, 29)]),
]


def _scene(seed, index):
    h, w, boxes = _PROFILES[index]
    grid = [[0] * w for _ in range(h)]
    rng = _rng(seed, f"scene:{index}")
    palette = list(range(2, 10))
    rng.shuffle(palette)
    for frame_index, box in enumerate(boxes):
        wall, seed_color = palette[2 * frame_index : 2 * frame_index + 2]
        r1, c1, r2, c2 = box
        center = ((r1 + r2) // 2, (c1 + c2) // 2)
        interior = [
            (r, c)
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
            if (r, c) != center
        ]
        seed_pos = interior[rng.randrange(len(interior))]
        _draw_frame(grid, box, wall, seed_pos, seed_color)
    # Geometry must remain input-derived rather than a fixed location lookup.
    # Deterministic whole-scene reflections preserve the frame grammar while
    # moving every derived center across seeds.
    if (seed + index) % 2:
        grid = [row[::-1] for row in grid]
    if ((seed // 2) + index) % 2:
        grid = grid[::-1]
    if h == w and ((seed // 4) + index) % 2:
        grid = [list(row) for row in zip(*grid)]
    return [row[:] for row in grid]


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    grids = [_scene(seed, index) for index in range(len(_PROFILES))]
    keys = [tuple(map(tuple, grid)) for grid in grids]
    if len(keys) != len(set(keys)):
        raise ValueError("constructed inputs must be distinct")
    return grids[:6], grids[6:]


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"mode": _rng(seed, "settings").choice(PARAMETERS["mode"])}
    mode = _mode(settings)
    train, test = input_bank(seed)

    def pair(grid):
        return {"input": [row[:] for row in grid], "output": solve(grid, mode)}

    return {
        "train": [pair(grid) for grid in train[:demos]],
        "test": [pair(grid) for grid in test[:queries]],
        "program_solution": program(settings),
    }
