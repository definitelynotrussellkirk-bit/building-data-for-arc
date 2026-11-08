"""Opt-in, episode-fixed diagonal-gap variant of task 59a7762bc6da.

The selected production generator is unchanged.  ``keep`` executes its exact
canonical source.  ``bridge_once`` fills diagonal holes simultaneously, then
recomputes the canonical component rule on that intermediate grid.  Python
labels are claims for the native worker to replay through protected Racket.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random


_CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
_POLICIES = ("keep", "bridge_once")
_MIN_SIDE = 16
_MAX_SIDE = 30


def _integer(value, minimum, maximum, name):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an exact integer in {minimum}..{maximum}")
    return value


def _policy(settings):
    if (type(settings) is not dict or set(settings) != {"gap_policy"}
            or type(settings["gap_policy"]) is not str
            or settings["gap_policy"] not in _POLICIES):
        raise ValueError("settings must be exactly {'gap_policy': 'keep'|'bridge_once'}")
    return settings["gap_policy"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or value not in (5, 7) for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 5 and 7")
    return [row[:] for row in grid]


def program(settings):
    """Return one complete Racket rule; the default resource is byte-exact."""
    if _policy(settings) == "keep":
        return _CANONICAL
    # Only unwrap the known, source-bound outer rule! registration.  Its lambda
    # remains verbatim and is applied to the newly produced intermediate grid.
    canonical_lambda = _CANONICAL[len("(rule! "):-1]
    return """(rule! (lambda (g)
  (define (gray? r c)
    (and (<= 0 r) (< r (rows g)) (<= 0 c) (< c (cols g))
         (= (cell-at g r c) 5)))
  (define intermediate
    (map-grid g
      (lambda (r c value)
        (if (and (= value 7)
                 (or (and (gray? (- r 1) (- c 1))
                          (gray? (+ r 1) (+ c 1)))
                     (and (gray? (- r 1) (+ c 1))
                          (gray? (+ r 1) (- c 1)))))
            5 value))))
  (""" + canonical_lambda + " intermediate)))"


def bridge_once(grid):
    """Fill one-cell diagonal gaps using only the original grid's cells."""
    original = _grid(grid)
    result = [row[:] for row in original]
    height, width = len(original), len(original[0])
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if original[r][c] == 7 and (
                original[r - 1][c - 1] == original[r + 1][c + 1] == 5
                or original[r - 1][c + 1] == original[r + 1][c - 1] == 5
            ):
                result[r][c] = 5
    return result


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value == 5}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for rr in range(max(0, r - 1), min(height, r + 2)):
                for cc in range(max(0, c - 1), min(width, c + 2)):
                    neighbor = (rr, cc)
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        cells.add(neighbor)
                        stack.append(neighbor)
        result.append(tuple(sorted(cells)))
    return tuple(result)


def components(grid):
    """Expose deterministic gray 8-components for focused authoring checks."""
    return _components(_grid(grid))


def _max_diagonal(component):
    cells = set(component)
    maximum = 1
    for r, c in cells:
        for dc in (-1, 1):
            if (r - 1, c - dc) in cells:
                continue
            length = 1
            while (r + length, c + length * dc) in cells:
                length += 1
            maximum = max(maximum, length)
    return maximum


def transform(grid, settings):
    """Python label claim, including recomputation after bridge insertion."""
    policy = _policy(settings)
    intermediate = bridge_once(grid) if policy == "bridge_once" else _grid(grid)
    result = [row[:] for row in intermediate]
    for component in _components(intermediate):
        if _max_diagonal(component) >= 3:
            for r, c in component:
                result[r][c] = 8
    return result


def _rng(seed, purpose):
    material = f"59a7762bc6da/gap-v1/{seed}/{purpose}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _dimensions(seed, split, index):
    candidates = [(height, width) for height in range(_MIN_SIDE, _MAX_SIDE + 1)
                  for width in range(_MIN_SIDE, _MAX_SIDE + 1)]
    _rng(seed, "dimensions").shuffle(candidates)
    return candidates[index if split == "train" else 6 + index]


def _slots(side):
    count = 2 if side < 25 else 3
    usable = side - 2 * (count - 1)
    base, extra = divmod(usable, count)
    result = []
    start = 0
    for index in range(count):
        size = base + int(index < extra)
        result.append((start, size))
        start += size + 2
    return result


def _mirror(cells):
    last = max(c for _, c in cells)
    return {(r, last - c) for r, c in cells}


def _motif(name, rng):
    if name in ("broken_dr", "broken_dl"):
        end = rng.choice((5, 6))
        cells = {(0, 0)} | {(2, c) for c in range(2, end + 1)}
        return _mirror(cells) if name == "broken_dl" else cells
    if name == "intact_dl3":
        return {(0, 2), (1, 1), (2, 0), (2, 1), (2, 2)}
    if name in ("intact_dr_long", "intact_dl_long"):
        length = rng.choice((4, 5, 6))
        cells = {(i, i) for i in range(length)}
        cells.update({(length - 1, length - 2), (length - 1, length - 3)})
        return _mirror(cells) if name == "intact_dl_long" else cells
    if name == "dense_negative":
        return {(r, c) for r in range(2) for c in range(6)}
    if name == "orthogonal_gaps":
        return {(0, 0), (0, 2), (0, 4), (0, 5)}
    if name == "near_miss":
        return {(0, 0), (1, 1), (2, 1), (3, 2)}
    if name == "cascade":
        return {(0, 2), (2, 0), (3, 3)}
    if name == "x_branch":
        return {(0, 0), (1, 1), (2, 2), (0, 2), (2, 0), (2, 3), (2, 4)}
    if name == "double_gap":
        return {(0, 0), (2, 2), (4, 4), (4, 3), (4, 2), (4, 5)}
    raise ValueError(f"unknown motif {name!r}")


def _motifs(split, index, rng):
    if split == "train" and index == 0:
        return ["broken_dr", "intact_dl3", "dense_negative", "orthogonal_gaps"]
    if split == "train" and index == 1:
        return ["broken_dl", "intact_dr_long", "near_miss", "cascade"]
    return [
        rng.choice(("broken_dr", "broken_dl", "double_gap")),
        rng.choice(("intact_dr_long", "intact_dl_long", "x_branch")),
        rng.choice(("dense_negative", "near_miss")),
        rng.choice(("cascade", "orthogonal_gaps", "dense_negative")),
    ]


def sample_input(seed, split, index, *, height=None, width=None):
    """Construct one scene without retries or dependence on private settings.

    Each episode reserves six dimension pairs for demos and four other pairs
    for queries.  Count changes therefore preserve every already-visible pair.
    Explicit dimensions are for bounded stress checks and bypass that schedule.
    """
    _integer(seed, 0, 2**63 - 1, "seed")
    if type(split) is not str or split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    _integer(index, 0, 5 if split == "train" else 3, "index")
    if height is None and width is None:
        height, width = _dimensions(seed, split, index)
    elif height is None or width is None:
        raise ValueError("height and width must be supplied together")
    else:
        _integer(height, _MIN_SIDE, _MAX_SIDE, "height")
        _integer(width, _MIN_SIDE, _MAX_SIDE, "width")
    rng = _rng(seed, f"{split}/{index}/layout")
    slots = [(r, c, h, w) for r, h in _slots(height) for c, w in _slots(width)]
    names = _motifs(split, index, rng)
    filler = ("broken_dr", "broken_dl", "intact_dr_long", "intact_dl_long",
              "dense_negative", "x_branch", "double_gap")
    names.extend(rng.choice(filler) for _ in range(len(slots) - len(names)))
    rng.shuffle(names)
    grid = [[7] * width for _ in range(height)]
    for slot_index, ((r0, c0, slot_h, slot_w), name) in enumerate(zip(slots, names)):
        cells = _motif(name, rng)
        motif_h = max(r for r, _ in cells) + 1
        motif_w = max(c for _, c in cells) + 1
        if slot_index == 0:
            dr = dc = 0
        elif slot_index == len(slots) - 1:
            dr, dc = slot_h - motif_h, slot_w - motif_w
        else:
            dr = rng.randrange(slot_h - motif_h + 1)
            dc = rng.randrange(slot_w - motif_w + 1)
        for r, c in cells:
            grid[r0 + dr + r][c0 + dc + c] = 5
    # The same reflection for the entire episode preserves the opposing slope
    # witnesses in demos zero and one.  Independent motif reflections would not.
    reflection = _rng(seed, "episode-reflection").randrange(4)
    if reflection & 1:
        grid = [list(reversed(row)) for row in grid]
    if reflection & 2:
        grid = list(reversed(grid))
    return grid


def generate(seed, settings, demos, queries):
    """Generate independent-count private pairs for native verification."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _policy(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {"program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            grid = sample_input(seed, split, index)
            pairs.append({"input": grid, "output": transform(grid, settings)})
        episode[split] = pairs
    return episode
