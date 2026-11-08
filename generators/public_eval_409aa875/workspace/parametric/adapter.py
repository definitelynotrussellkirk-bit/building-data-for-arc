"""Five-cell triomino pointers for public parent 409aa875."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("forward", "backward")
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1))
EIGHT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30 or type(value[0]) is not list
            or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("expected a rectangular 1..30 exact-integer grid")
    return value


def setting(settings):
    if (type(settings) is not dict or set(settings) != {"travel"}
            or type(settings["travel"]) is not str or settings["travel"] not in MODES):
        raise ValueError("settings must name exactly one declared travel mode")
    return settings["travel"]


def program(settings):
    mode = setting(settings)
    return (HERE / ("canonical.rkt" if mode == "forward" else "backward.rkt")).read_text()


def _rng(seed, label):
    raw = hashlib.sha256(f"public_eval_409aa875:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def components8(cells):
    todo = set(cells)
    out = []
    while todo:
        start = min(todo)
        todo.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in EIGHT:
                p = (r + dr, c + dc)
                if p in todo:
                    todo.remove(p)
                    component.add(p)
                    stack.append(p)
        out.append(component)
    return out


def pointer(cells):
    cells = set(cells)
    if len(cells) != 3:
        raise ValueError("pointer must have exactly three cells")
    for p in sorted(cells):
        diagonal = [q for q in cells if q != p and abs(q[0] - p[0]) == 1 and abs(q[1] - p[1]) == 1]
        if len(diagonal) == 2:
            mr = sum(q[0] for q in diagonal) // 2
            mc = sum(q[1] for q in diagonal) // 2
            direction = (p[0] - mr, p[1] - mc)
            if direction not in DIRECTIONS:
                raise ValueError("invalid chevron pointer")
            return p, direction
    for p in sorted(cells):
        cardinal = [q for q in cells if abs(q[0] - p[0]) + abs(q[1] - p[1]) == 1]
        if len(cardinal) == 2:
            dr = sum(q[0] - p[0] for q in cardinal)
            dc = sum(q[1] - p[1] for q in cardinal)
            direction = (-dr, -dc)
            if direction not in DIRECTIONS:
                raise ValueError("invalid L pointer")
            return p, direction
    raise ValueError("unsupported triomino pointer")


def pointer_cells(origin, direction):
    r, c = origin
    dr, dc = direction
    if direction not in DIRECTIONS:
        raise ValueError("invalid pointer direction")
    if dr == 0:
        return {(r, c), (r - 1, c - dc), (r + 1, c - dc)}
    if dc == 0:
        return {(r, c), (r - dr, c - 1), (r - dr, c + 1)}
    return {(r, c), (r - dr, c), (r, c - dc)}


def analyze(g, mode="forward"):
    grid(g)
    if mode not in MODES:
        raise ValueError("unknown travel mode")
    h, w = len(g), len(g[0])
    bg = Counter(cell for row in g for cell in row).most_common(1)[0][0]
    foreground = {(r, c) for r in range(h) for c in range(w) if g[r][c] != bg}
    objects = components8(foreground)
    if not objects or any(len(obj) != 3 for obj in objects):
        raise ValueError("every foreground object must be a separate triomino")
    sign = 1 if mode == "forward" else -1
    endpoints = []
    records = []
    for obj in objects:
        origin, direction = pointer(obj)
        direction = (sign * direction[0], sign * direction[1])
        endpoint = (origin[0] + 5 * direction[0], origin[1] + 5 * direction[1])
        if 0 <= endpoint[0] < h and 0 <= endpoint[1] < w:
            endpoints.append(endpoint)
        records.append((obj, origin, direction, endpoint))
    return bg, objects, endpoints, records


def solve(g, mode="forward"):
    bg, objects, endpoints, _ = analyze(g, mode)
    counts = Counter(endpoints)
    foreground = set().union(*objects)
    hit_cells = set().union(*(obj for obj in objects if obj & set(endpoints))) if objects else set()
    out = [row[:] for row in g]
    for r, c in hit_cells:
        out[r][c] = 9
    for (r, c), count in counts.items():
        if (r, c) not in foreground:
            out[r][c] = 1 if count >= 2 else 9
    return out


def intermediate(g, mode="forward"):
    bg, objects, endpoints, records = analyze(g, mode)
    counts = Counter(endpoints)
    return {
        "background": bg,
        "pointers": [
            {"origin": list(origin), "direction": list(direction), "endpoint": list(endpoint)}
            for _, origin, direction, endpoint in records
        ],
        "endpoints": [list(p) for p in endpoints],
        "endpoint_counts": {f"{r},{c}": n for (r, c), n in sorted(counts.items())},
        "hit_object_count": sum(bool(obj & set(endpoints)) for obj in objects),
    }


def _rotate_grid(g, turns):
    out = [row[:] for row in g]
    for _ in range(turns % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def scene(seed, index):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 2**31 - 1, "index")
    profile = index % 10
    sizes = (20, 21, 22, 23, 24, 25, 22, 25, 28, 30)
    n = sizes[profile]
    offset = (n - 20) // 2
    rng = _rng(seed, f"scene:{index}")
    backgrounds = [7, 0, 4, 8]
    bg = backgrounds[profile % len(backgrounds)]
    fg = rng.choice([color for color in (0, 2, 3, 4, 5, 6, 8) if color != bg])
    g = [[bg] * n for _ in range(n)]
    specs = [
        ((10 + offset, 5 + offset), (0, 1)),      # collision at (10,10)
        ((5 + offset, 10 + offset), (1, 0)),
        ((9 + offset, 9 + offset), (1, 1)),       # hits the target below
        ((14 + offset, 14 + offset), (-1, 0)),
        ((14 + offset, 6 + offset), (-1, 1)),
    ]
    occupied = set()
    for origin, direction in specs:
        cells = pointer_cells(origin, direction)
        occupied |= cells
        for r, c in cells:
            g[r][c] = fg
    target_objects = 5 + profile // 2
    attempts = 0
    while len(specs) < target_objects and attempts < 500:
        attempts += 1
        origin = (rng.randint(5, n - 6), rng.randint(5, n - 6))
        direction = rng.choice(DIRECTIONS)
        cells = pointer_cells(origin, direction)
        if any(not (0 <= r < n and 0 <= c < n) for r, c in cells):
            continue
        if any(max(abs(r - rr), abs(c - cc)) <= 1 for r, c in cells for rr, cc in occupied):
            continue
        specs.append((origin, direction))
        occupied |= cells
        for r, c in cells:
            g[r][c] = fg
    if len(specs) != target_objects:
        raise RuntimeError("could not place requested pointer set")
    g = _rotate_grid(g, rng.randrange(4))
    if rng.randrange(2):
        g = [row[::-1] for row in g]
    solve(g, "forward")
    solve(g, "backward")
    return g


def generate(seed, settings, demos=3, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    mode = setting(settings)

    def pair(index):
        g = scene(seed, index)
        return {"input": g, "output": solve(g, mode)}

    return {
        "train": [pair(i) for i in range(demos)],
        "test": [pair(i) for i in range(6, 6 + queries)],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
    }


def query_order(presentation_seed=0):
    integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    _rng(presentation_seed, "presentation").shuffle(order)
    return order


def public_turn(episode, turn, *, presentation_seed=0):
    integer(turn, 0, 3, "turn")
    if type(episode) is not dict or type(episode.get("test")) is not list or len(episode["test"]) != 4:
        raise ValueError("project from a complete four-query private bank")
    if type(episode.get("train")) is not list or not 2 <= len(episode["train"]) <= 6:
        raise ValueError("invalid demonstrations")
    index = query_order(presentation_seed)[turn]
    return copy.deepcopy({
        "train": [{"input": grid(p["input"]), "output": grid(p["output"])} for p in episode["train"]],
        "test": [{"input": grid(episode["test"][index]["input"])}],
    })


def rival(g, name, mode="forward"):
    if name in MODES:
        return solve(g, name)
    bg, objects, endpoints, _ = analyze(g, mode)
    counts = Counter(endpoints)
    foreground = set().union(*objects)
    out = [row[:] for row in g]
    if name == "identity":
        return out
    if name != "no_hit":
        hit_cells = set().union(*(obj for obj in objects if obj & set(endpoints))) if objects else set()
        for r, c in hit_cells:
            out[r][c] = 9
    for (r, c), count in counts.items():
        if (r, c) not in foreground:
            out[r][c] = 9 if name == "no_collision" else (1 if count >= 2 else 9)
    if name not in ("no_hit", "no_collision"):
        raise ValueError(name)
    return out


RIVALS = MODES + ("identity", "no_hit", "no_collision")
