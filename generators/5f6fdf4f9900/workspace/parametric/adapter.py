"""Native parameterized corner enlargement; labels are replayed by Racket.

The input RNG never depends on settings. Canonical generation is untouched.
This separate grammar allows disconnected regions of the same color, so
component area cannot be replaced by whole-color frequency.
"""
from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path


HOME = Path(__file__).resolve().parent
SETTINGS = ({"corner_priority": "scan"}, {"corner_priority": "largest_component"})
PALETTE = (1, 3, 4, 5, 6, 7, 8, 9)
DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Both templates contain meaningful conflicts and disconnected same-color
# pieces. The second has a fourth color, defeating fixed-three scale.
TEACHING_ROWS = (
    ("000333", "110303", "000000", "010440", "110040", "100000"),
    ("110333", "110300", "400300", "040300", "040000", "440500"),
)

LARGEST_PROGRAM = """(rule! (lambda (g)
  (let* ((n (length (filter (lambda (v) (!= v 0)) (grid-colors g))))
         (parts (objects g 0))
         (areas (build-grid h w (ar ac)
                  (if (zero? (at g ar ac)) 0
                      (obj-size
                        (first (filter
                          (lambda (o) (member (list ar ac) (obj-cells o)))
                          parts)))))))
    (build-grid (* h n) (* w n) (br bc)
      (let* ((r (quotient br n)) (c (quotient bc n))
             (lr (modulo br n)) (lc (modulo bc n))
             (v (at g r c)))
        (if (!= v 0) v
            (let* ((eligible
                     (filter
                       (lambda (d)
                         (let ((nr (+ r (first d))) (nc (+ c (second d))))
                           (and (in-bounds? nr nc h w)
                                (!= (at g nr nc) 0)
                                (zero? (at g nr c))
                                (zero? (at g r nc)))))
                       diagonal-deltas))
                   (chosen
                     (if (null? eligible) #f
                         (pick-max eligible
                           (lambda (d)
                             (at areas (+ r (first d)) (+ c (second d))))))))
              (if chosen
                  (if (= (first chosen) (second chosen))
                      (if (= lr lc) 2 0)
                      (if (= lr (- (- n 1) lc)) 2 0))
                  0))))))))"""


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"corner_priority"}
            or type(settings["corner_priority"]) is not str
            or settings["corner_priority"] not in ("scan", "largest_component")):
        raise ValueError("settings must declare corner_priority=scan|largest_component")
    return settings["corner_priority"]


def program(settings):
    """Exact standalone Racket rule; the default resource has no added newline."""
    return (HOME / "canonical.rkt").read_text() if _setting(settings) == "scan" else LARGEST_PROGRAM


def _validate_grid(grid):
    if (type(grid) is not list or not 4 <= len(grid) <= 15
            or type(grid[0]) is not list or not 4 <= len(grid[0]) <= 15
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or v not in (0, *PALETTE) for row in grid for v in row)):
        raise ValueError("input must be a rectangular 4..15 grid of literal colors, with red reserved")
    n = len({v for row in grid for v in row if v})
    if not 2 <= n <= 5:
        raise ValueError("input needs 2..5 distinct nonzero colors")
    if len(grid) * n > 30 or len(grid[0]) * n > 30:
        raise ValueError("color-count enlargement must fit a 30x30 output")
    return n


def component_areas(grid):
    """Map every foreground cell to its same-color four-connected area."""
    height, width = len(grid), len(grid[0])
    areas = [[0] * width for _ in grid]
    for r in range(height):
        for c in range(width):
            if not grid[r][c] or areas[r][c]:
                continue
            cells = {(r, c)}
            frontier = deque([(r, c)])
            while frontier:
                row, col = frontier.popleft()
                for dr, dc in ORTHOGONALS:
                    nr, nc = row + dr, col + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == grid[r][c] and (nr, nc) not in cells):
                        cells.add((nr, nc))
                        frontier.append((nr, nc))
            for row, col in cells:
                areas[row][col] = len(cells)
    return areas


def corner_candidates(grid, r, c):
    if grid[r][c]:
        return []
    height, width = len(grid), len(grid[0])
    return [(dr, dc) for dr, dc in DIAGONALS
            if 0 <= r + dr < height and 0 <= c + dc < width
            and grid[r + dr][c + dc] and not grid[r + dr][c] and not grid[r][c + dc]]


def transform(grid, settings):
    """Python claim only: native qualification independently executes Racket."""
    priority = _setting(settings)
    n = _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    areas = component_areas(grid) if priority == "largest_component" else None
    out = [[0] * (width * n) for _ in range(height * n)]
    for r in range(height):
        for c in range(width):
            candidates = corner_candidates(grid, r, c)
            chosen = (max(candidates, key=lambda d: areas[r + d[0]][c + d[1]])
                      if candidates and areas is not None else
                      candidates[0] if candidates else None)
            for lr in range(n):
                for lc in range(n):
                    if grid[r][c]:
                        value = grid[r][c]
                    elif chosen is None:
                        value = 0
                    else:
                        on = lr == lc if chosen[0] == chosen[1] else lr + lc == n - 1
                        value = 2 if on else 0
                    out[r * n + lr][c * n + lc] = value
    return out


def _palette_copy(rows, rng):
    grid = [[int(x) for x in row] for row in rows]
    colors = sorted({v for row in grid for v in row if v})
    mapping = dict(zip(colors, rng.sample(PALETTE, len(colors))))
    return [[mapping.get(v, 0) for v in row] for row in grid]


def _random_scene(rng, height, width, count, density):
    """Bounded region-growth scenes with additional disconnected pieces."""
    target = max(count, round(height * width * density))
    for _ in range(160):
        colors = rng.sample(PALETTE, count)
        grid = [[0] * width for _ in range(height)]
        for color, cell in zip(colors, rng.sample(range(height * width), count)):
            grid[cell // width][cell % width] = color
        filled = count
        while filled < target:
            empty = [(r, c) for r in range(height) for c in range(width) if not grid[r][c]]
            r, c = rng.choice(empty)
            neighbors = [grid[r + dr][c + dc] for dr, dc in ORTHOGONALS
                         if 0 <= r + dr < height and 0 <= c + dc < width
                         and grid[r + dr][c + dc]]
            grid[r][c] = rng.choice(neighbors) if neighbors and rng.random() < .75 else rng.choice(colors)
            filled += 1
        orientations = {d[0] == d[1] for r in range(height) for c in range(width)
                        for d in corner_candidates(grid, r, c)}
        if orientations == {True, False}:
            return grid
    raise ValueError("bounded scene sampler could not produce both corner orientations")


def teaching_check(episode):
    """Demonstration-only identification against the two declared settings.

    It deliberately ignores test labels. Broader finite-rival Racket audits
    live in audit.py and do not claim universal uniqueness.
    """
    survivors = []
    for setting in SETTINGS:
        if all(transform(pair["input"], setting) == pair["output"] for pair in episode["train"]):
            survivors.append(dict(setting))
    selected = [s for s in SETTINGS if program(s) == episode.get("program_solution")]
    return {"ok": len(selected) == 1 and survivors == selected,
            "survivors": survivors, "basis": "demonstrations_only", "finite_settings": 2}


def generate(seed, settings, demos=3, queries=4):
    _setting(settings)
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train, test, seen = [], [], set()
    for index in range(demos):
        rng = random.Random(f"5f6fdf4f9900:{seed}:demo:{index}")
        if index < 2:
            grid = _palette_copy(TEACHING_ROWS[index], rng)
        else:
            grid = _random_scene(rng, 4 + index % 3, 5, 2 + index % 4, (.42, .55, .66)[index % 3])
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise ValueError("duplicate demonstration input")
        seen.add(key)
        train.append({"input": grid, "output": transform(grid, settings)})
    stress = (15, 15, 2, .58) if seed % 2 else (6, 6, 5, .58)
    profiles = ((4, 4, 2, .44), (5, 6, 3, .53), (6, 5, 4, .63), stress)
    for index, (height, width, count, density) in enumerate(profiles[:queries]):
        rng = random.Random(f"5f6fdf4f9900:{seed}:query:{index}")
        for _ in range(16):
            grid = _random_scene(rng, height, width, count, density)
            key = json.dumps(grid, separators=(",", ":"))
            if key not in seen:
                break
        else:
            raise ValueError("bounded query sampler exhausted distinct inputs")
        seen.add(key)
        test.append({"input": grid, "output": transform(grid, settings)})
    episode = {"train": train, "test": test, "program_solution": program(settings)}
    certificate = teaching_check(episode)
    if not certificate["ok"]:
        raise ValueError("constructive demonstrations failed finite-setting identification")
    return episode
