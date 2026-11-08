"""Native rectangle-outline family; all returned labels are unverified Python claims.

The native qualification/export worker independently executes the adjacent Racket
programs. This module never accepts a family or changes canonical production.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
SETTINGS = ("cyan", "largest_interior")
PALETTE = (1, 2, 4, 5, 6, 7, 8, 9)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"color_source"}
            or type(settings["color_source"]) is not str
            or settings["color_source"] not in SETTINGS):
        raise ValueError("settings must contain only color_source=cyan|largest_interior")
    return settings["color_source"]


def program(settings):
    """Return exact source bytes as text, including the canonical whitespace."""
    name = "canonical.rkt" if _setting(settings) == "cyan" else "largest_interior.rkt"
    return (ROOT / name).read_text(encoding="utf-8")


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("grid must have exact integer colors, rectangular dimensions 1..30")


def components(grid, bounds=None):
    """Same-color 4-components after clipping to an optional strict rectangle."""
    h, w = len(grid), len(grid[0])
    cells = {(r, c) for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 3) and (bounds is None or
                bounds[0] < r < bounds[2] and bounds[1] < c < bounds[3])}
    found = []
    while cells:
        start = min(cells)
        color = grid[start[0]][start[1]]
        group, todo = set(), [start]
        cells.remove(start)
        while todo:
            r, c = todo.pop()
            group.add((r, c))
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in cells and grid[nxt[0]][nxt[1]] == color:
                    cells.remove(nxt)
                    todo.append(nxt)
        found.append({"color": color, "size": len(group), "cells": sorted(group)})
    return found


def analyze(grid):
    """Validate the parametric input grammar and expose the causal intermediate."""
    _grid(grid)
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if len(points) != 2:
        raise ValueError("exactly two green corner markers are required")
    (ar, ac), (br, bc) = points
    rect = min(ar, br), min(ac, bc), max(ar, br), max(ac, bc)
    if rect[2] - rect[0] < 2 or rect[3] - rect[1] < 2:
        raise ValueError("opposite markers must enclose a nonempty interior")
    groups = components(grid, rect)
    if not groups:
        raise ValueError("parametric grammar requires an interior object")
    largest = max(groups, key=lambda item: item["size"])
    if sum(item["size"] == largest["size"] for item in groups) != 1:
        raise ValueError("parametric grammar requires a unique largest interior component")
    return {"rectangle": rect, "components": groups, "selected": largest}


def solve(grid, settings):
    """Authoring mirror. A Python return alone is not a verified Racket label."""
    mode = _setting(settings)
    info = analyze(grid)
    color = 8 if mode == "cyan" else info["selected"]["color"]
    r0, c0, r1, c1 = info["rectangle"]
    out = copy.deepcopy(grid)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r in (r0, r1) or c in (c0, c1)) and grid[r][c] == 0:
                out[r][c] = color
    return out


def _rng(seed, *parts):
    text = ":".join(map(str, ("rectangle-color-v1", seed, *parts)))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest(), "big"))


def _grow(rng, box, count, start=None):
    """Construct a connected polyomino inside a slot, without rejection sampling."""
    r0, c0, r1, c1 = box
    pool = {(r, c) for r in range(r0, r1) for c in range(c0, c1)}
    if not 1 <= count <= len(pool):
        raise ValueError("object size exceeds its slot capacity")
    if start is not None and start not in pool:
        raise ValueError("object anchor must lie in its slot")
    selected = {rng.choice(sorted(pool)) if start is None else start}
    frontier = set()
    while len(selected) < count:
        for r, c in selected:
            frontier.update(p for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                            if p in pool and p not in selected)
        p = rng.choice(sorted(frontier))
        frontier.remove(p)
        selected.add(p)
    return sorted(selected)


def _rotate(grid, turns):
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def draw(seed, split, index, height, width, attempt=0):
    """Matched constructive inputs; setting and requested query count are absent."""
    rng = _rng(seed, split, index, attempt)
    turns = (0, 1)[index] if split == "train" and index < 2 else rng.randrange(4)
    h, w = (width, height) if turns % 2 else (height, width)
    r0, c0, r1, c1 = 2, 0, h - 1, w - 1
    grid = [[0] * w for _ in range(h)]
    # A separator keeps repeated-color objects 4-disconnected; explicit diagonal
    # contacts in heavy-repeat scenes distinguish 4- from 8-connectivity.
    rm = r0 + 1 + (r1 - r0 - 2) // 2
    cm = c0 + 1 + (c1 - c0 - 2) // 2
    slots = [(r0 + 1, c0 + 1, rm, cm), (r0 + 1, cm + 1, rm, c1),
             (rm + 1, c0 + 1, r1, cm), (rm + 1, cm + 1, r1, c1)]
    capacity = min((b[2] - b[0]) * (b[3] - b[1]) for b in slots)
    winner_size = max(4, min(28, capacity * 2 // 3, r0 * w - 3))
    heavy_repeat = index % 2 == 0
    repeated_size = winner_size * 3 // 5 + 1 if heavy_repeat else max(2, winner_size // 3)
    small_size = max(1, winner_size // 4)
    winner_slot = index if split == "train" and index < 2 else rng.randrange(4)
    repeated_slots = (1, 2) if winner_slot in (0, 3) else (0, 3)
    small_slot = next(i for i in range(4) if i not in (*repeated_slots, winner_slot))

    teaching_palette = [2, 4, 5, 6, 7]
    _rng(seed, "teaching-colors").shuffle(teaching_palette)
    if split == "train":
        winner_color = 8 if index == 1 else teaching_palette[index % len(teaching_palette)]
    else:
        colors = list(PALETTE)
        _rng(seed, "query-colors").shuffle(colors)
        winner_color = colors[index % len(colors)]
    small_color = (1 if index == 0 else 9) if split == "train" and index < 2 else None
    colors = [c for c in PALETTE if c not in (winner_color, small_color)]
    rng.shuffle(colors)
    if small_color is None:
        small_color = colors.pop()
    repeated_color, outside_color, border_color = colors[:3]
    roles = [(winner_slot, winner_size, winner_color),
             (repeated_slots[0], repeated_size, repeated_color),
             (repeated_slots[1], repeated_size, repeated_color),
             (small_slot, small_size, small_color)]
    if repeated_slots == (1, 2):
        contacts = {1: ((rm - 1, cm + 1), (rm, cm + 1)),
                    2: ((rm + 1, cm - 1), (rm + 1, cm))}
    else:
        contacts = {0: ((rm - 1, cm - 1), (rm - 1, cm)),
                    3: ((rm + 1, cm + 1), (rm, cm + 1))}
    for slot, count, color in roles:
        anchor, extra = contacts[slot] if heavy_repeat and slot in contacts else (None, None)
        for r, c in _grow(rng, slots[slot], count - (extra is not None), anchor):
            grid[r][c] = color
        if extra is not None:
            grid[extra[0]][extra[1]] = color
    # Cross the marked boundary in the empty separator column. Only its
    # one-cell interior fragment counts after clipping, not the large outside part.
    for r, c in _grow(rng, (0, 0, r0, w), winner_size + 3, (r0 - 1, cm)):
        grid[r][c] = outside_color
    grid[r0][cm] = grid[r0 + 1][cm] = outside_color
    main_diagonal = bool((index + (split == "test")) % 2)
    corners = ((r0, c0), (r1, c1)) if main_diagonal else ((r0, c1), (r1, c0))
    for r, c in corners:
        grid[r][c] = 3
    border = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if (r in (r0, r1) or c in (c0, c1)) and (r, c) not in corners
              and grid[r][c] == 0]
    for r, c in rng.sample(border, 2 if max(h, w) < 20 else 4):
        grid[r][c] = border_color
    return _rotate(grid, turns)


def generate(seed, settings, demos, queries, *, height=None, width=None):
    """Native adapter API; exact dimensions are additional authoring-only controls."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if (height is None) != (width is None):
        raise ValueError("height and width must be supplied together")
    if height is not None:
        _integer(height, 12, 30, "height")
        _integer(width, 12, 30, "width")
    schedules = {"train": ((12, 12), (14, 16), (16, 14), (18, 20), (20, 18), (22, 22)),
                 "test": ((12, 14), (20, 22), (24, 28), (30, 30))}
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for i in range(count):
            h, w = schedules[split][i] if height is None else (height, width)
            for attempt in range(32):
                grid = draw(seed, split, i, h, w, attempt)
                signature = tuple(map(tuple, grid))
                if signature not in seen:
                    break
            else:
                raise ValueError("bounded sampler exhausted distinct input support")
            seen.add(signature)
            result[split].append({"input": grid, "output": solve(grid, settings)})
    return result


def public_turn(episode, query_index=0):
    """One query, no answers, private settings, count hints or future inputs."""
    from reviewer_support import public_challenge_bytes
    import json
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return json.loads(public_challenge_bytes({"train": episode["train"],
                                            "test": [episode["test"][query_index]]}))
