"""Constructive bbox-aspect lessons; Python claims are re-executed in Racket.

The separate family supports 8..30 canvases. Canonical production stays intact.
Inputs and their order depend on seed and role, never on hidden rule settings.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import random

SETTINGS = ({"reference": "axes"}, {"reference": "largest"})
FOUR = ((-1, 0), (1, 0), (0, -1), (0, 1))


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"reference"}:
        raise ValueError("settings must name exactly reference")
    if type(settings["reference"]) is not str or settings["reference"] not in ("axes", "largest"):
        raise ValueError("reference must be axes or largest")
    return settings["reference"]


def program(settings):
    mode = validate_settings(settings)
    return Path(__file__).with_name("canonical.rkt" if mode == "axes" else "relative.rkt").read_text()


def components(grid):
    seen = set()
    result = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for rr, cc in cells:
                for dr, dc in FOUR:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            result.append((color, cells))
    return result


def dimensions(cells):
    return (max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
            max(c for _, c in cells) - min(c for _, c in cells) + 1)


def aspect(cells):
    h, w = dimensions(cells)
    return "tall" if h > w else "wide" if w > h else "square"


def transform(grid, settings):
    mode = validate_settings(settings)
    groups = components(grid)
    rh, rw = (1, 1)
    if mode == "largest" and groups:
        # Stable first-raster tie behavior agrees with Racket; sampled anchors
        # are strictly unique, so tie behavior is outside the admitted grammar.
        anchor = max(groups, key=lambda item: len(item[1]))
        rh, rw = dimensions(anchor[1])
    out = [[0] * len(grid[0]) for _ in grid]
    for _, cells in groups:
        h, w = dimensions(cells)
        left, right = h * rw, w * rh
        color = 2 if left > right else 3 if left < right else 4
        for r, c in cells:
            out[r][c] = color
    return out


def _rng(seed, *parts):
    text = repr((seed, *parts)).encode()
    return random.Random(int.from_bytes(hashlib.sha256(text).digest(), "big"))


def _shape(rng, h, w, count):
    """Connected exact-count shape spanning its bbox, with randomized growth."""
    cells = {(r, 0) for r in range(h)} | {(0, c) for c in range(w)}
    if not h + w - 1 <= count <= h * w:
        raise ValueError("impossible connected shape count")
    while len(cells) < count:
        frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in FOUR
                           if 0 <= r + dr < h and 0 <= c + dc < w} - cells)
        cells.add(rng.choice(frontier))
    if rng.randrange(2):
        cells = {(h - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, w - 1 - c) for r, c in cells}
    return cells


def _bands(length, n):
    usable = length - n + 1
    q, extra = divmod(usable, n)
    sizes = [q + (i < extra) for i in range(n)]
    result, offset = [], 0
    for size in sizes:
        result.append((offset, size))
        offset += size + 1
    return result


def sample_scene(seed, h, w, anchor_aspect="tall", teaching=False):
    for name, value in (("height", h), ("width", w)):
        if type(value) is not int or not 8 <= value <= 30:
            raise ValueError(f"{name} must be an integer in 8..30")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if anchor_aspect not in ("tall", "wide", "square"):
        raise ValueError("unknown anchor aspect")
    rng = _rng(seed, "scene", h, w, anchor_aspect, teaching)
    if min(h, w) >= 24:
        nr, nc = 3, 3
    elif h >= 9 and w >= 14:
        nr, nc = 2, 3
    elif h >= 14 and w >= 9:
        nr, nc = 3, 2
    else:
        nr, nc = 2, 2
    rows, cols = _bands(h, nr), _bands(w, nc)
    side = min(size for _, size in rows + cols)
    slots = [(r, c, rh, cw, ri, ci) for ri, (r, rh) in enumerate(rows)
             for ci, (c, cw) in enumerate(cols)]
    n = len(slots)
    if teaching and side < 4:
        raise ValueError("teaching scenes need six slots of at least 4x4")

    if anchor_aspect == "square":
        ah = aw = max(2, side - 1)
    elif side >= 8 and h == 30 and w == 30:
        ah, aw = 8, 6
    elif teaching:
        ah, aw = rng.choice([(a, b) for a, b in ((4, 2), (6, 2), (6, 4), (8, 4), (8, 6))
                             if a <= side])
    else:
        choices = [(a, b) for a in range(3, side + 1) for b in range(2, a)
                   if a * b >= 2 * (math.isqrt(a * b) + 1)]
        ah, aw = rng.choice(choices)
    square_side = min(side, math.isqrt(ah * aw) + 1)
    minimum = max(ah + aw, 2 * square_side)
    if teaching:
        # The mild-aspect distractor below is sparse but has the largest bbox.
        # Keep the reference strictly larger by foreground count.
        minimum = max(minimum, 2 * ah - 1)
    anchor_count = rng.randint(min(minimum, ah * aw), ah * aw)
    if h == 30 and w == 30 and anchor_aspect != "square":
        anchor_count = 44 + rng.randrange(5)
    square_count = 2 * square_side - 1
    if square_count >= anchor_count:
        square_side = max(2, square_side - 1)
        square_count = 2 * square_side - 1
    anchor = _shape(rng, ah, aw, anchor_count)
    square = _shape(rng, square_side, square_side, square_count)
    extreme_length = min(side, anchor_count - 1)
    extreme = _shape(rng, extreme_length, 1, extreme_length)
    # The minimum square anchor has four cells. Its opposite-aspect distractor
    # must then be a three-cell bar, otherwise the reference would be tied.
    opposite = _shape(rng, 2, 3, 4) if anchor_count > 4 else _shape(rng, 1, 3, 3)
    divisor = math.gcd(ah, aw)
    eh, ew = ah // divisor, aw // divisor
    equal = _shape(rng, eh, ew, eh + ew - 1)
    mild_sizes = [(a, b) for a in range(2, side + 1) for b in range(2, a)
                  if a * aw < b * ah and a + b - 1 < anchor_count]
    if teaching:
        # A square bbox-max would let a bbox-reference rival mimic the fixed
        # axes rule on every demonstration, then diverge on a nonsquare query.
        # This nonsquare box is larger than both reference and square boxes.
        mh, mw = ah, ah - 1
    else:
        mh, mw = rng.choice(mild_sizes) if mild_sizes else (2, 2)
    mild = _shape(rng, mh, mw, mh + mw - 1)
    shapes = [anchor, square, extreme, opposite] if n == 4 else [anchor, square, equal, extreme, opposite, mild]
    for _ in range(n - len(shapes)):
        sizes = [(a, b) for a in range(3, side + 1) for b in range(3, side + 1)
                 if a + b - 1 < anchor_count]
        sh, sw = rng.choice(sizes)
        lower = sh + sw - 1
        upper = min(sh * sw, anchor_count - 1)
        count = rng.randint(max(lower, min(upper, anchor_count // 2)), upper)
        shapes.append(_shape(rng, sh, sw, count))
    # Transposition changes anchor orientation while retaining all size cues.
    if anchor_aspect == "wide":
        shapes = [{(c, r) for r, c in cells} for cells in shapes]
    palette = rng.sample(range(1, 10), rng.randint(2, min(6, n - 1)))
    colors = [palette[0], palette[0]] + [rng.choice(palette) for _ in range(n - 2)]
    plan = list(enumerate(zip(colors, shapes)))
    rng.shuffle(plan)
    if teaching:
        # Defeat first-raster anchor without a fixed anchor slot. Square is an
        # unambiguous different-ratio reference for both tall and wide anchors.
        first_candidates = [i for i, (role, _) in enumerate(plan) if role in (1, 3, 4, 5)]
        j = rng.choice(first_candidates)
        plan[0], plan[j] = plan[j], plan[0]
    grid = [[0] * w for _ in range(h)]
    for (_, (color, shape)), (r0, c0, rh, cw, ri, ci) in zip(plan, slots):
        sh, sw = dimensions(shape)
        dr, dc = rng.randrange(rh - sh + 1), rng.randrange(cw - sw + 1)
        if teaching and ri == 0 and ci == 0:
            # Ordering slots alone does not fix raster order: a different slot
            # could start on an earlier row. This object spans its top row.
            dr = 0
        # Large examples occupy all extreme bands, including real edge contact.
        if h == 30 and w == 30:
            if ri == 0: dr = 0
            if ri == nr - 1: dr = rh - sh
            if ci == 0: dc = 0
            if ci == nc - 1: dc = cw - sw
        for r, c in shape:
            grid[r0 + dr + r][c0 + dc + c] = color
    return grid


def generate(seed, settings, demos=3, queries=4):
    validate_settings(settings)
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    for name, value, low, high in (("demos", demos, 2, 6), ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an integer in {low}..{high}")
    result = {"train": [], "test": [], "program_solution": program(settings),
              "settings": dict(settings), "seed": seed}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            rng = _rng(seed, split, index)
            if split == "train":
                h, w = rng.randint(9, 17), rng.randint(14, 26)
                orientation = "tall" if index % 2 == 0 else "wide"
                teaching = True
            else:
                h, w = ((8, 8), (rng.randint(9, 20), rng.randint(9, 20)),
                        (30, 30), (rng.randint(15, 30), rng.randint(15, 30)))[index]
                orientation = ("tall", "wide", "tall", "square")[index]
                teaching = False
            for attempt in range(8):
                sub_seed = rng.getrandbits(128)
                grid = sample_scene(sub_seed, h, w, orientation, teaching)
                key = tuple(tuple(row) for row in grid)
                if key not in seen:
                    break
            else:
                raise RuntimeError("bounded distinct-input construction exhausted")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
