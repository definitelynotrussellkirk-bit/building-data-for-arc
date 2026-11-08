"""Complete isolated L triominoes, optionally haloing Stage-A squares."""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

TASK_ID = "fad48869c581"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"mode": ["canonical", "square_halo"]}
DEFAULT = {"mode": "canonical"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}

_CANONICAL_BODY = CANONICAL[len("(rule! ") : -1]
SQUARE_HALO = f"""(rule!
  (let* ((completed {_CANONICAL_BODY})
         (src completed))
    (define (solid-color r c)
      (let ((v (at src r c)))
        (if (and (not (= v 0))
                 (= (at src r (+ c 1)) v)
                 (= (at src (+ r 1) c) v)
                 (= (at src (+ r 1) (+ c 1)) v))
            v
            0)))
    (for*/fold ((out completed))
               ((r (in-range (- (rows src) 1)))
                (c (in-range (- (cols src) 1))))
      (let ((color (solid-color r c)))
        (if (= color 0)
            out
            (for*/fold ((acc out))
                       ((rr (in-range (max 0 (- r 1))
                                      (min (rows src) (+ r 3))))
                        (cc (in-range (max 0 (- c 1))
                                      (min (cols src) (+ c 3)))))
              (if (= (at acc rr cc) 0)
                  (set-cell acc rr cc color)
                  acc)))))))"""


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
        raise ValueError("mode must be canonical or square_halo")
    return value


def program(settings):
    return CANONICAL if _mode(settings) == "canonical" else SQUARE_HALO


def _l_windows(grid):
    result = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            cells = [
                (r, c, grid[r][c]),
                (r, c + 1, grid[r][c + 1]),
                (r + 1, c, grid[r + 1][c]),
                (r + 1, c + 1, grid[r + 1][c + 1]),
            ]
            nonzero = [value for _rr, _cc, value in cells if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                missing = next((rr, cc) for rr, cc, value in cells if value == 0)
                result.append((r, c, nonzero[0], missing))
    return result


def _canonical_solve(grid):
    validate_grid(grid)
    out = [row[:] for row in grid]
    for _r, _c, color, (missing_r, missing_c) in _l_windows(grid):
        out[missing_r][missing_c] = color
    return out


def _solid_squares(grid):
    validate_grid(grid)
    result = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            value = grid[r][c]
            if (
                value != 0
                and grid[r][c + 1] == value
                and grid[r + 1][c] == value
                and grid[r + 1][c + 1] == value
            ):
                result.append((r, c, value))
    return result


def _halo_squares(completed):
    validate_grid(completed)
    out = [row[:] for row in completed]
    h, w = len(completed), len(completed[0])
    for r, c, color in _solid_squares(completed):
        for rr in range(max(0, r - 1), min(h, r + 3)):
            for cc in range(max(0, c - 1), min(w, c + 3)):
                if out[rr][cc] == 0:
                    out[rr][cc] = color
    return out


def solve(grid, mode="canonical"):
    if type(mode) is not str or mode not in PARAMETERS["mode"]:
        raise ValueError("mode must be canonical or square_halo")
    completed = _canonical_solve(grid)
    return completed if mode == "canonical" else _halo_squares(completed)


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


# height, width, L count, isolated distractor count, force boundary contact
_PROFILES = [
    (11, 14, 4, 2, False),
    (14, 17, 5, 2, True),
    (16, 20, 6, 3, False),
    (19, 23, 8, 3, False),
    (30, 30, 16, 6, False),
    (24, 28, 12, 5, True),
    (13, 18, 5, 2, False),
    (18, 21, 8, 4, True),
    (26, 29, 14, 5, False),
    (30, 30, 18, 6, True),
]


def _candidate_slots(h, w):
    return [(r, c) for r in range(1, h - 1, 5) for c in range(1, w - 1, 5)]


def _quadrant(h, w, position):
    r, c = position
    return (2 if r + 0.5 >= h / 2 else 0) + (1 if c + 0.5 >= w / 2 else 0)


def _choose_slots(h, w, count, rng, force_boundary):
    selected = []
    candidates = _candidate_slots(h, w)
    if force_boundary:
        selected.append((0, 0))
        candidates = [
            position for position in candidates
            if not (abs(position[0]) < 4 and abs(position[1]) < 4)
        ]
    buckets = {index: [] for index in range(4)}
    for position in candidates:
        buckets[_quadrant(h, w, position)].append(position)
    for bucket in buckets.values():
        rng.shuffle(bucket)
    cursor = 0
    while len(selected) < count:
        made_progress = False
        for quadrant in range(4):
            bucket = buckets[quadrant]
            if cursor < len(bucket):
                selected.append(bucket[cursor])
                made_progress = True
                if len(selected) == count:
                    break
        if not made_progress:
            raise ValueError(f"cannot place {count} separated L blocks in {h}x{w}")
        cursor += 1
    return selected


def _draw_l(grid, top, left, color, missing):
    cells = [(top, left), (top, left + 1), (top + 1, left), (top + 1, left + 1)]
    for index, (r, c) in enumerate(cells):
        if index != missing:
            grid[r][c] = color


def _add_distractors(grid, count, rng):
    h, w = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(candidates)
    placed = []
    for r, c in candidates:
        if grid[r][c] != 0:
            continue
        if any(
            grid[rr][cc] != 0
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 1), min(w, c + 2))
        ):
            continue
        if any(abs(r - rr) <= 2 and abs(c - cc) <= 2 for rr, cc in placed):
            continue
        grid[r][c] = 9
        placed.append((r, c))
        if len(placed) == count:
            return
    raise ValueError(f"cannot place {count} isolated distractors")


def _scene(seed, index):
    h, w, block_count, distractor_count, force_boundary = _PROFILES[index]
    grid = [[0] * w for _ in range(h)]
    rng = _rng(seed, f"scene:{index}")
    slots = _choose_slots(h, w, block_count, rng, force_boundary)
    palette = list(range(1, 9))
    rng.shuffle(palette)
    for block_index, (r, c) in enumerate(slots):
        _draw_l(grid, r, c, palette[block_index % len(palette)], rng.randrange(4))
    _add_distractors(grid, distractor_count, rng)
    if (seed + index) % 2:
        grid = [row[::-1] for row in grid]
    if ((seed // 2) + index) % 2:
        grid = grid[::-1]
    if h == w and ((seed // 4) + index) % 2:
        grid = [list(row) for row in zip(*grid)]
    if len(_l_windows(grid)) != block_count:
        raise RuntimeError("constructed scene has spurious or missing L windows")
    if _solid_squares(grid):
        raise RuntimeError("constructed input contains a pre-completed square")
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
