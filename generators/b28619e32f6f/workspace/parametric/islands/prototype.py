"""Opt-in isolated-island removal followed by enclosed-area classification.

All labels here are claims: native qualification independently executes Racket.
Inputs are matched across settings. The first two demos are constructive witnesses,
not rejection-sampled lessons; all other draws use an independent per-slot RNG.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "b28619e32f6f"
POLICIES = ("keep", "absorb")
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if (r, c) != (0, 0))
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
FILL_LAMBDA = CANONICAL.strip()[len("(rule!"):].rsplit(")", 1)[0].strip()


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"island_policy"}
            or type(settings["island_policy"]) is not str or settings["island_policy"] not in POLICIES):
        raise ValueError("settings must be exactly island_policy=keep|absorb")
    return settings["island_policy"]


def _compose(fill_lambda, policy, neighbors=4):
    if policy == "keep":
        return "(rule!\n " + fill_lambda + ")"
    return f"""(rule!
 (lambda (grid)
   ;; A removes only original red four-neighbor singletons, simultaneously.
   ;; B discovers zero regions again on that changed grid, then measures area.
   (let* ((islands
           (filter
            (lambda (cell)
              (andmap (lambda (value) (= value 0))
                      (neighbors-{neighbors} grid (first cell) (second cell) 2)))
            (find-color grid 2)))
          (intermediate (recolor-cells grid islands 0)))
     ({fill_lambda} intermediate))))"""


def program(settings):
    policy = _settings(settings)
    return CANONICAL if policy == "keep" else _compose(FILL_LAMBDA, policy)


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0])
            or any(type(v) is not int or v not in (0, 2) for v in row) for row in grid)):
        raise ValueError("input must be a rectangular 1..30 grid of exact integer 0/2")


def regions(grid, color=0, connectivity=4):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    result = []
    directions = DIR4 if connectivity == 4 else DIR8
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        component, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    component.add(p)
                    stack.append(p)
        result.append(component)
    return result


def exterior(grid, region):
    return any(r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1) for r, c in region)


def islands(grid, connectivity=4):
    directions = DIR4 if connectivity == 4 else DIR8
    return {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2
            and all(0 <= r + dr < len(grid) and 0 <= c + dc < len(row)
                    and grid[r + dr][c + dc] == 0 for dr, dc in directions)}


def intermediate(grid, policy, connectivity=4):
    out = deepcopy(grid)
    if policy == "absorb":
        for r, c in islands(grid, connectivity):
            out[r][c] = 0
    return out


def bucket(size):
    return 8 if size <= 8 else 4 if size <= 24 else 3


def _bbox(region):
    return (min(r for r, c in region), min(c for r, c in region),
            max(r for r, c in region), max(c for r, c in region))


def _fill(grid, chooser=bucket, *, connectivity=4, fill_exterior=False, measure="area"):
    out = deepcopy(grid)
    holes = regions(grid, connectivity=connectivity)
    frames = []
    if measure == "frame":
        for red in regions(grid, color=2):
            r0, c0, r1, c1 = _bbox(red)
            if r1 - r0 >= 2 and c1 - c0 >= 2:
                border = {(r0, c) for c in range(c0, c1 + 1)} | {(r1, c) for c in range(c0, c1 + 1)}
                border |= {(r, c0) for r in range(r0, r1 + 1)} | {(r, c1) for r in range(r0, r1 + 1)}
                if border <= red:
                    frames.append((r0, c0, r1, c1))
    for region in holes:
        if not fill_exterior and exterior(grid, region):
            continue
        size = len(region)
        if measure == "bbox":
            r0, c0, r1, c1 = _bbox(region)
            size = (r1 - r0 + 1) * (c1 - c0 + 1)
        elif measure == "frame":
            r, c = min(region)
            owners = [b for b in frames if b[0] < r < b[2] and b[1] < c < b[3]]
            if owners:
                b = min(owners, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
                size = sum(grid[r][c] == 0 for r in range(b[0] + 1, b[2]) for c in range(b[1] + 1, b[3]))
        color = chooser(size)
        for r, c in region:
            out[r][c] = color
    return out


def solve(grid, policy):
    _grid(grid)
    if policy not in POLICIES:
        raise ValueError("unknown island policy")
    return _fill(intermediate(grid, policy))


def _erase_all_interior_red(grid):
    out = deepcopy(grid)
    # Retain large enclosing boundaries; wrongly erase every small red component.
    for component in regions(grid, color=2):
        if len(component) <= 6:
            for r, c in component:
                out[r][c] = 0
    return out


def _stale_sizes(grid, policy):
    if policy == "keep":
        return _fill(grid)
    out = _fill(grid)
    old_sizes = {cell: len(region) for region in regions(grid) for cell in region}
    for r, c in islands(grid):
        size = old_sizes[(r - 1, c)]
        out[r][c] = bucket(size)
    return out


def rival_outputs(grid, policy):
    mid = intermediate(grid, policy)
    return {
        "other_setting": solve(grid, "absorb" if policy == "keep" else "keep"),
        "strict_both": _fill(mid, lambda s: 8 if s < 8 else 4 if s < 24 else 3),
        "strict_8": _fill(mid, lambda s: 8 if s < 8 else 4 if s <= 24 else 3),
        "strict_24": _fill(mid, lambda s: 8 if s <= 8 else 4 if s < 24 else 3),
        "exact_8_24": _fill(mid, lambda s: 8 if s == 8 else 4 if s == 24 else 3),
        "bbox_area": _fill(mid, measure="bbox"),
        "per_frame_total": _fill(mid, measure="frame"),
        "zero_connectivity_8": _fill(mid, connectivity=8),
        "fill_exterior": _fill(mid, fill_exterior=True),
        "all_cyan": _fill(mid, lambda s: 8),
        "all_yellow": _fill(mid, lambda s: 4),
        "all_green": _fill(mid, lambda s: 3),
        "identity": deepcopy(grid),
        "singleton_connectivity_8": _fill(intermediate(grid, policy, 8)),
        "erase_dominoes_too": _fill(_erase_all_interior_red(grid)) if policy == "absorb" else _fill(grid),
        "reuse_original_regions": _stale_sizes(grid, policy),
    }


def teaching_failures(train, test, policy):
    wrong = set(rival_outputs(train[0]["input"], policy))
    for pair in train:
        if solve(pair["input"], policy) != pair["output"]:
            return ["incorrect demonstration label"]
        outputs = rival_outputs(pair["input"], policy)
        wrong &= {name for name, output in outputs.items() if output == pair["output"]}
    return sorted(name for name in wrong if any(
        rival_outputs(pair["input"], policy)[name] != pair["output"] for pair in test))


def _transform(grid, rng):
    out = deepcopy(grid)
    for _ in range(rng.randrange(4)):
        out = [list(row) for row in zip(*out[::-1])]
    return [row[::-1] for row in out] if rng.randrange(2) else out


def _chamber(h, w, kind, rng):
    inner = [[0] * w for _ in range(h)]
    if kind in ("notch1", "notch2"):
        inner[0][0] = 2
        if kind == "notch2":
            inner[0][1] = 2
    elif kind == "dot":
        inner[rng.randrange(1, h - 1)][rng.randrange(1, w - 1)] = 2
    elif kind == "domino":
        r, c = h // 2, (w - 1) // 2
        inner[r][c] = inner[r][c + 1] = 2
    elif kind == "diagonal":
        inner[0][0] = inner[1][1] = 2
    elif kind == "x":
        for r in range(h):
            for c in range(w):
                if r == c or r + c == w - 1:
                    inner[r][c] = 2
    elif kind == "block":
        for r, c in ((0, 0), (1, 1), (1, 2), (2, 1), (2, 2), (3, 3)):
            inner[r][c] = 2
    elif kind == "split":
        for row in inner:
            row[1] = 2
    elif kind != "plain":
        raise ValueError("unknown chamber kind")
    return _transform(inner, rng) if h == w else inner


def _room(h, w, kind, rng):
    inner = _chamber(h, w, kind, rng)
    return [[2] * (w + 2), *[[2, *row, 2] for row in inner], [2] * (w + 2)]


def _mosaic(rows, rng):
    tiles = [[_room(*spec, rng) for spec in row] for row in rows]
    for row in tiles:
        rng.shuffle(row)
    rng.shuffle(tiles)
    inner_h = sum(max(len(tile) for tile in row) for row in tiles) + len(tiles) - 1
    inner_w = max(sum(len(tile[0]) for tile in row) + len(row) - 1 for row in tiles)
    h, w = inner_h + rng.choice((2, 3)), inner_w + rng.choice((2, 3))
    if h > 30 or w > 30:
        raise ValueError("mosaic exceeds supported canvas")
    grid = [[0] * w for _ in range(h)]
    r0 = rng.randrange(h - inner_h)  # retain at least one exterior row
    for row in tiles:
        row_h = max(len(tile) for tile in row)
        row_w = sum(len(tile[0]) for tile in row) + len(row) - 1
        c0 = rng.randrange(w - row_w)
        for tile in row:
            start = r0 + rng.randrange(row_h - len(tile) + 1)
            for i, values in enumerate(tile):
                grid[start + i][c0:c0 + len(values)] = values
            c0 += len(tile[0]) + 1
        r0 += row_h + 1
    return _transform(grid, rng)


def _boundaries(rng):
    return _mosaic([[(3, 3, "notch2"), (3, 3, "notch1"), (3, 3, "plain")],
                    [(5, 5, "notch2"), (5, 5, "notch1"), (5, 5, "plain")]], rng)


def _topology(rng):
    return _mosaic([[(3, 3, "dot"), (5, 5, "dot"), (5, 5, "x")],
                    [(5, 5, "domino"), (4, 4, "block"), (5, 8, "split")]], rng)


def _varied(rng):
    rows = []
    for _ in range(rng.choice((1, 2, 3))):
        row = []
        for _ in range(rng.choice((2, 3))):
            h, w = rng.randrange(3, 7), rng.randrange(3, 7)
            kind = rng.choice(("plain", "notch1", "notch2", "dot", "domino", "diagonal"))
            row.append((h, w, kind))
        rows.append(row)
    return _mosaic(rows, rng)


def _small(rng, seed):
    spec = ((1, 1, "plain"), (1, 2, "plain"), (2, 3, "plain"),
            (3, 3, "dot"), (5, 5, "dot"))[seed % 5]
    room = _room(*spec, rng)
    grid = [row + [0] for row in room] + [[0] * (len(room[0]) + 1)]
    return _transform(grid, rng)


def _stress(rng):
    grid = [[0] * 30 for _ in range(30)]
    for r0, c0 in ((0, 0), (0, 16), (16, 0), (16, 16)):
        tile = [[2] * 14 for _ in range(14)]
        for r, c, h, w in ((1, 1, 5, 6), (1, 8, 5, 5), (7, 1, 6, 6), (7, 8, 6, 5)):
            kinds = ("plain", "dot", "domino", "diagonal", "notch1", "notch2")
            if h == w == 5:
                kinds += ("x",)
            part = _chamber(h, w, rng.choice(kinds), rng)
            for i, row in enumerate(part):
                tile[r + i][c:c + w] = row
        for i, row in enumerate(tile):
            grid[r0 + i][c0:c0 + 14] = row
    return _transform(grid, rng)


def _rng(seed, role, index, retry):
    digest = hashlib.sha256(f"{TASK_ID}:islands-v1:{seed}:{role}:{index}:{retry}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def generate(seed, settings, demos=3, queries=4):
    policy = _settings(settings)
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1), ("demos", demos, 2, 6), ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    seen, splits = set(), {"train": [], "test": []}
    # Queries first: their identities do not depend on requested demo count.
    for role, count in (("test", queries), ("train", demos)):
        for index in range(count):
            for retry in range(32):
                rng = _rng(seed, role, index, retry)
                if role == "train":
                    grid = (_boundaries if index == 0 else _topology if index == 1 else _varied)(rng)
                elif index == 0:
                    grid = _small(rng, seed)
                else:
                    grid = (_varied if index == 1 else _topology if index == 2 else _stress)(rng)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    seen.add(key)
                    splits[role].append({"input": grid, "output": solve(grid, policy)})
                    break
            else:
                raise RuntimeError("distinct-input budget exhausted")
    return {**splits, "program_solution": program(settings)}
