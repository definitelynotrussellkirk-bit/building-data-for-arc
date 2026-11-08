"""Deterministic native parametric family for ``eb60199b6eb8``.

The canonical setting keeps the exact selected Racket program.  The alternate
setting first completes valid horizontal endpoint rows on a fresh grid (A), then
uses that completed intermediate to select columns containing exactly two
same-colored cells and completes those columns (B).  B reads the frozen A
intermediate, so vertical writes do not cascade.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

SETTINGS = ("horizontal_only", "horizontal_then_vertical")
CANONICAL_PATH = Path(__file__).with_name("canonical.rkt")
CANONICAL_PROGRAM = CANONICAL_PATH.read_text(encoding="utf-8")
CANONICAL_SHA256 = hashlib.sha256(CANONICAL_PROGRAM.encode()).hexdigest()

_CANONICAL_FINAL = """(for/fold ((out (empty-grid (rows g) (cols g) 0))) ((r (in-range (rows g)))) (let ((pos (filter (lambda (c) (not (= (at g r c) 0))) (range (cols g))))) (if (and (= (length pos) 2) (= (at g r (first pos)) (at g r (second pos)))) (paint out (map (lambda (c) (list r c)) (range (min (first pos) (second pos)) (+ (max (first pos) (second pos)) 1))) (at g r (first pos))) out)))"""

_PASS_DEFINITIONS = """    (define (complete-horizontal grid)
      (for/fold ([out (empty-grid (rows grid) (cols grid) 0)]) ([r (in-range (rows grid))])
        (let ((pos (filter (lambda (c) (not (= (at grid r c) 0))) (range (cols grid)))))
          (if (and (= (length pos) 2) (= (at grid r (first pos)) (at grid r (second pos))))
              (paint out (map (lambda (c) (list r c))
                              (range (min (first pos) (second pos))
                                     (+ (max (first pos) (second pos)) 1)))
                     (at grid r (first pos)))
              out))))
    (define (complete-vertical grid)
      (for/fold ([out grid]) ([c (in-range (cols grid))])
        (let ((pos (filter (lambda (r) (not (= (at grid r c) 0))) (range (rows grid)))))
          (if (and (= (length pos) 2) (= (at grid (first pos) c) (at grid (second pos) c)))
              (paint out (map (lambda (r) (list r c))
                              (range (min (first pos) (second pos))
                                     (+ (max (first pos) (second pos)) 1)))
                     (at grid (first pos) c))
              out))))"""

if CANONICAL_SHA256 != "7d5c5a67ac1a9f8170fdb3247fadbef891cc3402414982933e55e442b90ac8b7":
    raise RuntimeError("task-local canonical Racket source does not match the selected authority")
if CANONICAL_PROGRAM.count(_CANONICAL_FINAL) != 1:
    raise RuntimeError("canonical tail needed for the composed rule was not found exactly once")

COMPOSED_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_FINAL,
    _PASS_DEFINITIONS + "\n    (complete-vertical (complete-horizontal g))",
    1,
)
_SKIP_A_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_FINAL,
    _PASS_DEFINITIONS + "\n    (complete-vertical g)",
    1,
)


def _closure(settings) -> str:
    if type(settings) is not dict or set(settings) != {"closure"}:
        raise ValueError("settings must contain exactly closure")
    value = settings["closure"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"closure must be one of {SETTINGS}")
    return value


def program(settings) -> str:
    return CANONICAL_PROGRAM if _closure(settings) == "horizontal_only" else COMPOSED_PROGRAM


def skip_a_program() -> str:
    """Standalone protected-Racket counterfactual used by the causal witness."""
    return _SKIP_A_PROGRAM


def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def complete_horizontal(grid):
    """Python claim/oracle for A; protected Racket remains label authority."""
    out = _blank_like(grid)
    for r, row in enumerate(grid):
        positions = [c for c, value in enumerate(row) if value != 0]
        if len(positions) != 2:
            continue
        left, right = positions
        if row[left] != row[right]:
            continue
        for c in range(left, right + 1):
            out[r][c] = row[left]
    return out


def complete_vertical(grid):
    """Python claim/oracle for B, evaluated from one frozen intermediate."""
    out = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for c in range(width):
        positions = [r for r in range(height) if grid[r][c] != 0]
        if len(positions) != 2:
            continue
        top, bottom = positions
        if grid[top][c] != grid[bottom][c]:
            continue
        for r in range(top, bottom + 1):
            out[r][c] = grid[top][c]
    return out


def _rng(seed: int, role: str, index: int, attempt: int) -> random.Random:
    payload = f"eb60199b6eb8-parametric-v1:{seed}:{role}:{index}:{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _shape(seed: int, role: str, index: int, rng: random.Random) -> tuple[int, int]:
    if role == "query":
        shapes = ((14, 24), (18, 27), (22, 30), (30, 30))
        return shapes[index]
    # Six independent demonstration slots; count changes never perturb queries.
    heights = (12, 13, 14, 15, 16, 17)
    widths = (24, 26, 28, 30, 25, 27)
    return heights[(index + rng.randrange(6)) % 6], widths[(2 * index + rng.randrange(6)) % 6]


def _zones(width: int, rng: random.Random) -> list[tuple[int, int]]:
    usable = width - 2  # one blank separator between the three reasoning regions
    base, remainder = divmod(usable, 3)
    sizes = [base + (i < remainder) for i in range(3)]
    zones = []
    left = 0
    for size in sizes:
        zones.append((left, left + size - 1))
        left += size + 1
    rng.shuffle(zones)
    return zones


def _put_pair(grid, row: int, left: int, right: int, color: int) -> None:
    grid[row][left] = color
    grid[row][right] = color


def _sample_input(seed: int, role: str, index: int, attempt: int = 0):
    rng = _rng(seed, role, index, attempt)
    height, width = _shape(seed, role, index, rng)
    grid = [[0] * width for _ in range(height)]

    boundary_positive = role == "query" and index in {2, 3}
    remaining = list(range(height))
    if boundary_positive:
        positive_rows = [0, height - 1]
    else:
        positive_rows = [rng.choice(range(0, max(1, height // 3))),
                         rng.choice(range(max(1, 2 * height // 3), height))]
        if positive_rows[0] == positive_rows[1]:
            positive_rows[1] = height - 1
    for row in positive_rows:
        remaining.remove(row)
    rng.shuffle(remaining)
    triple_rows = remaining[:3]
    mismatch_rows = remaining[3:5]
    decoy_rows = remaining[5:7]

    colors = list(range(1, 10))
    rng.shuffle(colors)
    positive_color, triple_color = colors[:2]
    mismatch_colors = colors[2:4]
    decoy_pair_colors = colors[4:6]
    decoy_outer, decoy_middle = colors[6:8]

    positive_zone, triple_zone, mismatch_zone = _zones(width, rng)

    # Positive causal region: A creates the inner overlap cells; B then sees
    # exactly two equal cells in those columns and paints between the rows.
    s, e = positive_zone
    inset = 2 if e - s + 1 >= 7 else 1
    positive_spans = [(s, e), (s + inset, e - inset)]
    if rng.randrange(2):
        positive_spans.reverse()
    for row, (left, right) in zip(positive_rows, positive_spans):
        _put_pair(grid, row, left, right, positive_color)

    # Exact-three negative control. Nested rows produce exact-two shoulder
    # columns but three-cell central columns, which B must leave unconnected.
    s, e = triple_zone
    triple_spans = [(s, e), (s + 1, e - 1), (s + 2, e - 2)]
    rng.shuffle(triple_spans)
    for row, (left, right) in zip(triple_rows, triple_spans):
        _put_pair(grid, row, left, right, triple_color)

    # Color-mismatch negative control: exactly two intermediate cells overlap,
    # but their colors differ, so B must not connect them.
    s, e = mismatch_zone
    mismatch_spans = [(s, e), (s + 1, e - 1)]
    if rng.randrange(2):
        mismatch_spans.reverse()
    for row, (left, right), color in zip(mismatch_rows, mismatch_spans, mismatch_colors):
        _put_pair(grid, row, left, right, color)

    # Canonical A-stage controls: these invalid rows disappear before B.
    c1, c2 = sorted(rng.sample(range(width), 2))
    if c2 == c1 + 1:
        c2 = min(width - 1, c2 + 1)
        if c2 == c1 + 1:
            c1 = max(0, c1 - 1)
    grid[decoy_rows[0]][c1] = decoy_pair_colors[0]
    grid[decoy_rows[0]][c2] = decoy_pair_colors[1]
    c1, c2, c3 = sorted(rng.sample(range(width), 3))
    grid[decoy_rows[1]][c1] = decoy_outer
    grid[decoy_rows[1]][c2] = decoy_middle
    grid[decoy_rows[1]][c3] = decoy_outer
    return grid


def _validate_request(seed, demos, queries) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def generate(seed, settings, demos=3, queries=4):
    closure = _closure(settings)
    _validate_request(seed, demos, queries)
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    seen: set[str] = set()

    for split, role, count in (("train", "demo", demos), ("test", "query", queries)):
        for index in range(count):
            for attempt in range(16):
                grid = _sample_input(seed, role, index, attempt)
                fingerprint = json.dumps(grid, separators=(",", ":"))
                if fingerprint not in seen:
                    break
            else:
                raise ValueError("distinct-input retry budget exhausted")
            seen.add(fingerprint)
            intermediate = complete_horizontal(grid)
            output = intermediate if closure == "horizontal_only" else complete_vertical(intermediate)
            episode[split].append({"input": grid, "output": output})
    return episode
