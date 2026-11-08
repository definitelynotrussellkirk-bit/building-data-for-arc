"""Constructive, setting-independent native side-route lesson inputs.

Every call constructs the same full six-demo/four-query bank before slicing.
The independent SHA-256-derived streams keep query geometry and ordering
unaffected by demonstration controls. Labels belong to native_family.py;
horizontal reflection happens here only to inputs, before any label is made.
"""
from __future__ import annotations

import hashlib
import random


def _stream(seed: int, role: str) -> random.Random:
    digest = hashlib.sha256(f"b88894a36787/native-inputs/v1/{role}/{seed}".encode("ascii")).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _integer(name: str, value: int, low: int, high: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")


def _grid(rng: random.Random, h: int, w: int, n: int,
          targets: list[tuple[int, str] | None], *, noise: int = 0,
          reflect: bool = False,
          start_interval: tuple[int, int] | None = None) -> list[list[int]]:
    """Make one lawful profile without rejection or output-dependent choices."""
    colors = rng.sample(range(1, 10), n)
    start = (rng.randint(1, w - n - 1) if start_interval is None
             else rng.randint(*start_interval))
    grid = [[0] * w for _ in range(h)]
    grid[0][start:start + n] = colors
    for color, target in zip(colors, targets):
        if target is not None:
            row, side = target
            col = 0 if side == "left" else w - 1
            grid[row][col] = color
    available = [(r, c) for r in range(1, h) for c in (0, w - 1)
                 if grid[r][c] == 0]
    ignored_colors = [color for color in range(1, 10) if color not in colors]
    for row, col in rng.sample(available, noise):
        # Independent draws allow two ignored dots of the same color.
        grid[row][col] = rng.choice(ignored_colors)
    if reflect:
        return [list(reversed(row)) for row in grid]
    return grid


def _demos(rng: random.Random) -> list[list[list[int]]]:
    reflect = bool(rng.getrandbits(1))
    h1, w1 = rng.randint(11, 15), rng.randint(13, 17)
    # Before reflection the first missing hit is strictly left of center;
    # the second demonstration's hit is strictly right. A shared reflection
    # preserves this coverage of both canvas halves.
    first = _grid(rng, h1, w1, 6,
                  [(1, "left"), None, (h1 - 2, "left"), (h1 - 4, "left"), None,
                   (h1 - 2, "right")], noise=rng.randint(1, 2), reflect=reflect,
                  start_interval=(1, min(w1 - 7, (w1 - 4) // 2)))
    h2, w2 = rng.randint(9, 12), rng.randint(11, 15)
    second = _grid(rng, h2, w2, 4,
                   [(h2 - 1, "right"), (3, "left"), (1, "right"), None],
                   noise=1, reflect=reflect,
                   start_interval=((w2 - 7) // 2 + 1, w2 - 5))
    third = _grid(rng, rng.randint(11, 15), rng.randint(11, 15), 4,
                  [(2, "left"), (5, "left"), (5, "right"), (2, "right")],
                  reflect=bool(rng.getrandbits(1)))
    # Additional constructive profiles add minimal header count, two boundary
    # omissions, and a complete wider run, without duplicating query shapes.
    fourth = _grid(rng, 10, rng.randint(8, 12), 2,
                   [None, (6, "left")], noise=1,
                   reflect=bool(rng.getrandbits(1)))
    fifth = _grid(rng, rng.randint(14, 16), 18, 5,
                  [None, (9, "right"), (2, "left"), (12, "left"), None],
                  noise=2, reflect=bool(rng.getrandbits(1)))
    sixth = _grid(rng, 19, rng.randint(16, 20), 7,
                  [(3, "left"), (8, "right"), (11, "left"), (5, "right"),
                   (16, "left"), (18, "right"), (14, "right")],
                  reflect=bool(rng.getrandbits(1)))
    return [first, second, third, fourth, fifth, sixth]


def _queries(rng: random.Random) -> list[list[list[int]]]:
    small = _grid(rng, 8, 8, 3,
                  [(2, "right"), None, (6, "left")], noise=1,
                  reflect=bool(rng.getrandbits(1)))
    complete = _grid(rng, 17, 21, 5,
                     [(2, "left"), (7, "right"), (15, "left"),
                      (12, "right"), (4, "right")], noise=1,
                     reflect=bool(rng.getrandbits(1)))
    missing = rng.sample(range(7), rng.randint(1, 2))
    large_targets = [(18, "right"), (4, "left"), (22, "right"),
                     (11, "left"), (20, "left"), (7, "right"), (23, "left")]
    for index in missing:
        large_targets[index] = None
    large = _grid(rng, 24, 26, 7, large_targets, noise=rng.randint(0, 2),
                  reflect=bool(rng.getrandbits(1)))
    full = _grid(rng, 30, 30, 8,
                 [(17, "left"), None, (22, "right"), (26, "left"),
                  (29, "right"), (24, "left"), None, (19, "right")],
                 noise=rng.randint(0, 2), reflect=bool(rng.getrandbits(1)))
    return [small, complete, large, full]


def sample_inputs(seed: int, demos: int = 3, queries: int = 4
                  ) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    """Return fresh input-only banks with strict, bounded scalar controls."""
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 3, 6)
    _integer("queries", queries, 1, 4)
    demo_bank = _demos(_stream(seed, "demonstrations"))
    query_bank = _queries(_stream(seed, "queries"))
    _stream(seed, "query-order").shuffle(query_bank)
    return demo_bank[:demos], query_bank[:queries]
