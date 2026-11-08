"""Connected-network propagation with an episode-fixed room-selection rule.

The default Racket text is byte-identical to the canonical authority.  This
separate sampler extends its input grammar; it does not claim that the new
woven, notched, rotated, or unmarked-distractor scenes pass the base validator.
Python labels are claims checked independently by native protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random

TASK_ID = "9c75b1456763"
HERE = Path(__file__).resolve().parent
SETTINGS = ({"fill_scope": "all_interiors"}, {"fill_scope": "unmarked_rooms"})
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"fill_scope"}
            or type(settings["fill_scope"]) is not str
            or settings["fill_scope"] not in {"all_interiors", "unmarked_rooms"}):
        raise ValueError("settings must contain exactly a declared fill_scope")
    return settings["fill_scope"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings):
    scope = _setting(settings)
    return (HERE / ("canonical.rkt" if scope == "all_interiors"
                    else "unmarked_rooms.rkt")).read_text(encoding="utf-8")


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")


def _groups(cells):
    remaining = set(cells)
    groups = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, group = [start], {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    group.add(nxt)
                    stack.append(nxt)
        groups.append(group)
    return groups


def analyze(grid):
    """Return the actual connected networks and their connected erosion cores.

    Blue-only distractors are lawful and unchanged.  A marked network needs
    one marker inside a nontrivial core and at least one separate remote core.
    """
    _grid(grid)
    h, w = len(grid), len(grid[0])
    components = _groups((r, c) for r in range(h) for c in range(w) if grid[r][c])
    result = []
    for cells in components:
        markers = [(r, c, grid[r][c]) for r, c in sorted(cells) if grid[r][c] != 1]
        if len(markers) > 1:
            raise ValueError("a marked network must have exactly one marker")
        interiors = {(r, c) for r, c in cells if 0 < r < h-1 and 0 < c < w-1
                     and all(grid[r+dr][c+dc] != 0 for dr, dc in EIGHT)}
        rooms = _groups(interiors)
        marker = markers[0] if markers else None
        if marker is not None:
            marked = [room for room in rooms if marker[:2] in room]
            if len(rooms) < 2 or len(marked) != 1 or len(marked[0]) < 2:
                raise ValueError("marker needs a nontrivial interior core and a remote room")
        result.append({"cells": cells, "marker": marker, "interiors": interiors, "rooms": rooms})
    return result


def solve(grid, settings):
    """Independent Python claim, never a substitute for Racket verification."""
    scope = _setting(settings)
    output = copy.deepcopy(grid)
    for comp in analyze(grid):
        marker = comp["marker"]
        if marker is None:
            continue
        for room in comp["rooms"]:
            if scope == "unmarked_rooms" and marker[:2] in room:
                continue
            for r, c in room:
                output[r][c] = marker[2]
    return output


def _rng(seed, split, index, attempt):
    raw = f"room-scope-v1:{seed}:{split}:{index}:{attempt}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _line(grid, a, b):
    if a[0] == b[0]:
        for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
            grid[a[0]][c] = 1
    elif a[1] == b[1]:
        for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
            grid[r][a[1]] = 1
    else:
        raise ValueError("corridor segments must be axis-aligned")


def _room(grid, r, c, width, rng, *, notch=True):
    half = width//2
    for y in range(r-2, r+3):
        for x in range(c-width//2, c+width//2+1):
            grid[y][x] = 1
    if notch:
        dr, dc = rng.choice(((-2, -half), (-2, half), (2, -half), (2, half)))
        grid[r+dr][c+dc] = 0
    return (r, c, width)


def _stripes(grid, rng):
    size = len(grid)
    rows = {18: (2, 8, 15), 20: (2, 9, 17), 30: (2, 14, 27)}[size]
    count = rng.choice((2, 3)) if size < 30 else rng.choice((3, 4))
    cols = [round(2 + i*(size-5)/(count-1)) for i in range(count)]
    networks = []
    for r in rows:
        rooms = [_room(grid, r, c, rng.choice((3, 5)), rng) for c in cols]
        route = r + rng.choice((-2, 0, 2))
        for left, right in zip(cols, cols[1:]):
            _line(grid, (r, left), (route, left))
            _line(grid, (route, left), (route, right))
            _line(grid, (route, right), (r, right))
        networks.append(rooms)
    return networks


def _woven(grid, rng):
    """An outer bent network encloses inner chains without connecting to them.

    The long first room exposes the difference between core membership and a
    radius-two exclusion.  A remote outer room is closer to an inner marker by
    both axes and by Manhattan distance, forcing actual network association.
    """
    size = len(grid)
    a = [_room(grid, 3, 3, 7, rng)]
    if size == 30:
        a.extend(_room(grid, 3, c, rng.choice((3, 5)), rng) for c in (15, 26))
    a.append(_room(grid, size-4, size-4, rng.choice((3, 5)), rng))
    _line(grid, (1, 3), (1, size-2))
    _line(grid, (1, size-2), (size-4, size-2))
    _line(grid, (size-4, size-4), (size-4, size-2))
    r = size//2
    bcols = (3, size-9) if size < 30 else (3, 13, 23)
    b = [_room(grid, r, c, 3 if size == 18 else rng.choice((3, 5)), rng) for c in bcols]
    # A bent inner connector and rectangular-room corners expose erosion rules.
    route = r + rng.choice((-2, 0, 2))
    for left, right in zip(bcols, bcols[1:]):
        _line(grid, (r, left), (route, left))
        _line(grid, (route, left), (route, right))
        _line(grid, (route, right), (r, right))
    networks = [a, b]
    if size == 30:
        c = [_room(grid, 25, col, rng.choice((3, 5)), rng) for col in (3, 13)]
        _line(grid, (25, 3), (25, 13))
        networks.append(c)
    return networks


def _orient(grid, code):
    result = [row[:] for row in grid]
    if code >= 4:
        result = [row[::-1] for row in result]
    for _ in range(code % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def sample_scene(seed, split, index, attempt=0):
    """Construct a private-settings-independent input, without rejection sampling."""
    _integer(seed, 0, 2**63-1, "seed")
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    _integer(index, 0, 5 if split == "demo" else 3, "index")
    _integer(attempt, 0, 31, "attempt")
    rng = _rng(seed, split, index, attempt)
    if split == "demo":
        size = (20, 18, 30, 20, 30, 18)[index]
        woven = index % 2 == 0
    else:
        size = (18, 20, 30, 30)[index]
        woven = index % 2 == 0
    grid = [[0]*size for _ in range(size)]
    networks = _woven(grid, rng) if woven else _stripes(grid, rng)
    colors = rng.sample(list(range(2, 10)), len(networks))
    for n, (rooms, color) in enumerate(zip(networks, colors)):
        if split == "demo" and index == 0:
            room_index = 0 if n == 0 else len(rooms)-1
        else:
            room_index = rng.randrange(len(rooms))
        r, c, width = rooms[room_index]
        if woven and room_index == 0 and n == 0:
            mr, mc = r, c-width//2+1
        else:
            # Pick actual complete-8-neighborhood cells, independently of output.
            candidates = [(rr, cc) for rr in range(r-1, r+2)
                          for cc in range(c-width//2+1, c+width//2)
                          if all(grid[rr+dr][cc+dc] for dr, dc in EIGHT)]
            mr, mc = rng.choice(candidates)
        grid[mr][mc] = color
    # Blue-only distractors cannot donate a marker or be mistaken for a room.
    empty = [(r,c) for r in range(1,size-1) for c in range(1,size-1)
             if grid[r][c] == 0 and all(grid[r+dr][c+dc] == 0 for dr,dc in EIGHT)]
    if empty:
        r, c = rng.choice(empty)
        grid[r][c] = 1
    grid = _orient(grid, rng.randrange(8))
    comps = analyze(grid)
    marked = [comp for comp in comps if comp["marker"] is not None]
    if len(marked) != len(networks) or len({c["marker"][2] for c in marked}) != len(networks):
        raise RuntimeError("constructed networks merged or lost a marker")
    return grid


def generate(seed, settings, demos=3, queries=4):
    """Construct 2..6 demos and 1..4 novel queries under one fixed rule.

    Geometry streams do not depend on settings or requested counts.  Only an
    exact duplicate may cause a bounded retry; the consumed attempt is private.
    """
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _setting(settings)
    result = {"train": [], "test": [], "program_solution": program(settings),
              "settings": dict(settings), "seed": seed, "attempts": []}
    seen = set()
    for name, split, count in (("train", "demo", demos), ("test", "query", queries)):
        for index in range(count):
            for attempt in range(32):
                grid = sample_scene(seed, split, index, attempt)
                key = tuple(tuple(row) for row in grid)
                if key not in seen:
                    seen.add(key)
                    result[name].append({"input": grid, "output": solve(grid, settings)})
                    result["attempts"].append(attempt+1)
                    break
            else:
                raise RuntimeError("cannot produce distinct inputs within 32 attempts")
    return result


def public_turn(episode, query_index=0):
    """Existing-controller projection: exactly one current query, no hints."""
    _integer(query_index, 0, len(episode["test"])-1, "query_index")
    return {"train": [{"input": copy.deepcopy(pair["input"]),
                       "output": copy.deepcopy(pair["output"])} for pair in episode["train"]],
            "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}]}
