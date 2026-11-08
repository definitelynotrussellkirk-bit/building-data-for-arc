"""Select the singleton D4 shape class, then render canonical or observed pose."""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import random

TASK_ID = "004ca3500787"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"pose": ["canonical", "observed"]}
DEFAULT = {"pose": "canonical"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}

# Store A's signatures once; B consumes those values without recomputing them.
# This is also the exact boundary used by the protected causal intervention.
TAG_EXPRESSION = "(shape-key (canonical (obj-cells obj)))"
_PREFIX = CANONICAL.split("    (define comps", 1)[0]
ALTERNATIVE = _PREFIX + """    (define comps (filter (lambda (o) (= (obj-color o) 2)) (objects g 0)))
    (define tagged
      (map (lambda (obj) (list obj (shape-key (canonical (obj-cells obj))))) comps))
    (define counts (make-hash))
    (for ([item (in-list tagged)])
      (hash-update! counts (second item) add1 0))
    (define chosen
      (first (filter (lambda (item) (= (hash-ref counts (second item)) 1)) tagged)))
    (define odd (first chosen))
    (let* ((cells (normalize-cells (obj-cells odd)))
           (h (+ 1 (apply max (map first cells))))
           (w (+ 1 (apply max (map second cells)))))
      (grid-from-fn h w (lambda (r c) (if (member? (list r c) cells) 8 0))))))"""

SHAPES = {
    "F5": ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    "P5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "W5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "T5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "I3": ((0, 0), (0, 1), (0, 2)),
    "L3": ((0, 0), (1, 0), (1, 1)),
    "S13": tuple((0, c) for c in range(10)) + ((1, 0), (1, 9), (1, 10)),
}


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"pose"}:
        raise ValueError("settings must contain exactly pose")
    if type(settings["pose"]) is not str or settings["pose"] not in PARAMETERS["pose"]:
        raise ValueError("pose must be canonical or observed")
    return settings["pose"]


def program(settings):
    return CANONICAL if _settings(settings) == "canonical" else ALTERNATIVE


def normalize(cells):
    cells = tuple(cells)
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def pose(cells, k):
    """0..3 clockwise rotations; 4..7 vertical reflection then rotation."""
    cells = normalize(cells)
    if k >= 4:
        w = max(c for _, c in cells) + 1
        cells = normalize((r, w - 1 - c) for r, c in cells)
    for _ in range(k % 4):
        h = max(r for r, _ in cells) + 1
        cells = normalize((c, h - 1 - r) for r, c in cells)
    return cells


def variants(cells):
    return tuple(dict.fromkeys(pose(cells, k) for k in range(8)))


def shape_key(cells):
    """Match Racket's (format \"~a\" sorted-cells), including two-digit axes."""
    return "(" + " ".join(f"({r} {c})" for r, c in normalize(cells)) + ")"


def canonical(cells):
    return min(variants(cells), key=shape_key)


def analyze(grid):
    """Validate the expanded grammar; return row-major red 4-cc and singleton."""
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or v not in (0, 2) for row in grid for v in row):
        raise ValueError("cells must be exact integer colors 0 or 2")
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    components = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        found, frontier = {first}, [first]
        while frontier:
            r, c = frontier.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen:
                    unseen.remove(p)
                    found.add(p)
                    frontier.append(p)
        components.append(tuple(sorted(found)))
    keys = [canonical(obj) for obj in components]
    counts = Counter(keys)
    if len(components) < 3 or len(counts) != 2 or sorted(counts.values()) != [1, len(components) - 1]:
        raise ValueError("need at least three objects and two D4 classes with multiplicities n-1 and 1")
    return components, components[next(i for i, key in enumerate(keys) if counts[key] == 1)]


def solve(grid, pose="canonical"):
    _settings({"pose": pose})
    _, odd = analyze(grid)
    cells = set(canonical(odd) if pose == "canonical" else normalize(odd))
    return [[8 if (r, c) in cells else 0 for c in range(max(c for _, c in cells) + 1)]
            for r in range(max(r for r, _ in cells) + 1)]


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _paint(grid, cells, row, col):
    for r, c in cells:
        assert 0 <= row + r < len(grid) and 0 <= col + c < len(grid[0])
        assert grid[row + r][col + c] == 0
        grid[row + r][col + c] = 2


def _cores(rng):
    a = [[0] * 20 for _ in range(12)]
    f, w, p, s = (canonical(SHAPES[name]) for name in ("F5", "W5", "P5", "S13"))
    ka = rng.choice([k for k in range(1, 4) if pose(w, k) != w])
    observed_w = pose(w, ka)
    kb = rng.choice([k for k in range(4, 8) if pose(s, k) != s and pose(w, k) != observed_w])
    for cells, row, col in ((pose(f, rng.randrange(4)), 0, 0),
                            (observed_w, 4, 7),
                            (pose(f, 4 + rng.randrange(4)), 8, 14)):
        _paint(a, cells, row + rng.randrange(2), col + rng.randrange(2))

    b = [[0] * 23 for _ in range(16)]
    rare = pose(s, kb)
    near = pose(p, rng.randrange(4))
    far = pose(p, 4 + rng.randrange(4))
    row, col = rng.randrange(2), 2 + rng.randrange(2)
    h = max(r for r, _ in rare) + 1
    edge_a = max(c for r, c in rare if r == h - 1)
    edge_b = min(c for r, c in near if r == 0)
    _paint(b, rare, row, col)
    _paint(b, near, row + h, col + edge_a + 1 - edge_b)
    _paint(b, far, row, 18 + rng.randrange(2))
    # These are grammar assertions, not retries or post-hoc label filtering.
    assert len(analyze(a)[0]) == len(analyze(b)[0]) == 3
    return a, b


def _scaled(cells, scale):
    return tuple((r * scale + dr, c * scale + dc) for r, c in cells
                 for dr in range(scale) for dc in range(scale))


def _field(h, w, n, rows, cols, common, rare, scale, rng):
    grid = [[0] * w for _ in range(h)]
    common, rare = SHAPES[common], SHAPES[rare]
    extent = scale * max(max(max(r, c) for r, c in shape) + 1 for shape in (common, rare))
    starts_r = [i * (h - extent) // (rows - 1) if rows > 1 else 0 for i in range(rows)]
    starts_c = [i * (w - extent) // (cols - 1) if cols > 1 else 0 for i in range(cols)]
    assert all(b - a > extent for a, b in zip(starts_r, starts_r[1:]))
    assert all(b - a > extent for a, b in zip(starts_c, starts_c[1:]))
    slots = [(r, c) for r in starts_r for c in starts_c]
    rng.shuffle(slots)
    for i, (row, col) in enumerate(slots[:n]):
        cells = _scaled(pose(rare if i == 0 else common, rng.randrange(8)), scale)
        ch, cw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
        _paint(grid, cells, row + rng.randrange(extent - ch + 1), col + rng.randrange(extent - cw + 1))
    assert len(analyze(grid)[0]) == n
    return grid


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    demos_rng, queries_rng = _rng(seed, "demos"), _rng(seed, "queries")
    a, b = _cores(demos_rng)
    demos = [a, b, [[2, 0, 2, 0, 2, 2]],
             _field(12, 18, 6, 2, 3, "F5", "P5", 1, demos_rng),
             _field(24, 27, 9, 3, 3, "F5", "P5", 2, demos_rng),
             _field(30, 30, 9, 3, 3, "F5", "P5", 3, demos_rng)]
    queries = [_field(7, 12, 3, 2, 2, "I3", "L3", 1, queries_rng),
               _field(17, 22, 8, 3, 3, "F5", "T5", 1, queries_rng),
               _field(26, 29, 4, 2, 2, "P5", "F5", 4, queries_rng),
               _field(30, 30, 16, 4, 4, "F5", "W5", 2, queries_rng)]
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"pose": _rng(seed, "settings").choice(PARAMETERS["pose"])}
    selected = _settings(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, selected)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]),
            "program_solution": program(settings)}
