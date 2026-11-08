"""Cue-count layer rotations for public parent 6ffbe589."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("clockwise", "counterclockwise")


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
    if (type(settings) is not dict or set(settings) != {"turn_direction"}
            or type(settings["turn_direction"]) is not str
            or settings["turn_direction"] not in MODES):
        raise ValueError("settings must name exactly one declared turn_direction")
    return settings["turn_direction"]


def program(settings):
    mode = setting(settings)
    return (HERE / ("canonical.rkt" if mode == "clockwise" else "counterclockwise.rkt")).read_text()


def _rng(seed, label):
    raw = hashlib.sha256(f"public_eval_6ffbe589:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def components_radius(cells, radius=2):
    todo = set(cells)
    out = []
    while todo:
        start = min(todo)
        todo.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            near = [p for p in todo if max(abs(p[0] - r), abs(p[1] - c)) <= radius]
            for p in near:
                todo.remove(p)
                component.add(p)
                stack.append(p)
        out.append(component)
    return out


def main_box(g):
    grid(g)
    h, w = len(g), len(g[0])
    bg = Counter(cell for row in g for cell in row).most_common(1)[0][0]
    cells = {(r, c) for r in range(h) for c in range(w) if g[r][c] != bg}
    if not cells:
        raise ValueError("expected non-background cells")
    main = max(
        components_radius(cells, 2),
        key=lambda obj: (
            len(obj),
            -min(r for r, _ in obj),
            -min(c for _, c in obj),
        ),
    )
    r0 = min(r for r, _ in main)
    r1 = max(r for r, _ in main)
    c0 = min(c for _, c in main)
    c1 = max(c for _, c in main)
    if r1 - r0 != c1 - c0:
        raise ValueError("largest radius-two component must have a square bounding box")
    return bg, r0, c0, r1 - r0 + 1


def rotate_cell(r, c, side, turns):
    for _ in range(turns % 4):
        r, c = c, side - 1 - r
    return r, c


def turn_counts(g):
    bg, r0, c0, side = main_box(g)
    h, w = len(g), len(g[0])
    colors = sorted({g[r][c] for r in range(r0, r0 + side)
                     for c in range(c0, c0 + side) if g[r][c] != bg})
    counts = {}
    for color in colors:
        counts[color] = sum(
            g[r][c] == color
            for r in range(h) for c in range(w)
            if not (r0 <= r < r0 + side and c0 <= c < c0 + side)
        ) % 4
    return counts


def solve(g, mode="clockwise"):
    grid(g)
    if mode not in MODES:
        raise ValueError("unknown turn direction")
    bg, r0, c0, side = main_box(g)
    counts = turn_counts(g)
    out = [[bg] * side for _ in range(side)]
    sign = 1 if mode == "clockwise" else -1
    for r in range(side):
        for c in range(side):
            color = g[r0 + r][c0 + c]
            if color == bg:
                continue
            rr, cc = rotate_cell(r, c, side, sign * counts[color])
            if out[rr][cc] != bg:
                raise ValueError("independent rotated layers collide")
            out[rr][cc] = color
    return out


def intermediate(g):
    bg, r0, c0, side = main_box(g)
    return {
        "background": bg,
        "main_box": [r0, c0, side, side],
        "turns": {str(k): v for k, v in turn_counts(g).items()},
    }


def _frame(side, inset, notch, color):
    lo, hi = inset, side - 1 - inset
    cells = {(lo, c) for c in range(lo, hi + 1)}
    cells |= {(hi, c) for c in range(lo, hi + 1)}
    cells |= {(r, lo) for r in range(lo + 1, hi)}
    cells |= {(r, hi) for r in range(lo + 1, hi)}
    cells.discard(notch)
    return {(r, c, color) for r, c in cells}


def _rotate_grid(g, turns):
    out = [row[:] for row in g]
    for _ in range(turns % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def scene(seed, index):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 2**31 - 1, "index")
    profile = index % 10
    sizes = (18, 19, 20, 22, 24, 26, 22, 25, 28, 30)
    n = sizes[profile]
    side = n - 8
    rng = _rng(seed, f"scene:{index}")
    colors = rng.sample([1, 2, 3, 4, 5, 6, 8, 9], 3)
    counts_table = ((1, 3, 2), (3, 1, 1), (2, 1, 3), (1, 2, 3),
                    (5, 3, 2), (3, 5, 1), (1, 1, 2), (3, 2, 1),
                    (2, 3, 5), (5, 1, 3))
    counts = counts_table[profile]
    g = [[0] * n for _ in range(n)]
    r0 = c0 = 1
    # Two separated annuli and an asymmetric inner polyomino.  Radius-two
    # connectivity joins the annuli but leaves the cue groups outside.
    outer_notch = (0, 1 + (index % max(1, side - 2)))
    middle_hi = side - 3
    middle_notch = (2 + (index % max(1, side - 5)), middle_hi)
    triples = set()
    triples |= _frame(side, 0, outer_notch, colors[0])
    triples |= _frame(side, 2, middle_notch, colors[1])
    # Keep the third layer strictly inside the middle annulus under every
    # quarter-turn.  The earlier center polyomino touched the middle frame in
    # the smallest profile, so independent rotations could create collisions.
    inner_lo, inner_hi = 4, side - 5
    center = (inner_lo + inner_hi) // 2
    inner = {(center, center), (center, center + 1), (center + 1, center)}
    if center - 1 >= inner_lo and center + 1 <= inner_hi:
        inner.add((center - 1, center + 1))
    if center + 2 <= inner_hi:
        inner |= {(center + 2, center), (center + 2, center - 1)}
    triples |= {(r, c, colors[2]) for r, c in inner}
    for r, c, color in triples:
        g[r0 + r][c0 + c] = color
    # Three separated cue banks.  Counts, not cue orientation, determine turns.
    for j in range(counts[0]):
        g[n - 2][1 + j] = colors[0]
    for j in range(counts[1]):
        g[1 + j][n - 2] = colors[1]
    for j in range(counts[2]):
        g[n - 5][n - 2 - j] = colors[2]
    # Vary absolute placement while preserving the same inference problem.
    g = _rotate_grid(g, rng.randrange(4))
    if rng.randrange(2):
        g = [row[::-1] for row in g]
    # Every generated scene must be valid for both settings and distinguish them
    # in the two teaching profiles.
    solve(g, "clockwise")
    solve(g, "counterclockwise")
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


def rival(g, name):
    if name in MODES:
        return solve(g, name)
    bg, r0, c0, side = main_box(g)
    if name == "crop_only":
        return [row[c0:c0 + side] for row in g[r0:r0 + side]]
    if name == "total_count":
        counts = turn_counts(g)
        turns = sum(counts.values()) % 4
        out = [[bg] * side for _ in range(side)]
        for r in range(side):
            for c in range(side):
                value = g[r0 + r][c0 + c]
                if value != bg:
                    rr, cc = rotate_cell(r, c, side, turns)
                    out[rr][cc] = value
        return out
    if name == "binary_presence":
        out = [[bg] * side for _ in range(side)]
        counts = turn_counts(g)
        for r in range(side):
            for c in range(side):
                value = g[r0 + r][c0 + c]
                if value != bg:
                    rr, cc = rotate_cell(r, c, side, 1 if counts[value] else 0)
                    out[rr][cc] = value
        return out
    raise ValueError(name)


RIVALS = MODES + ("crop_only", "total_count", "binary_presence")
