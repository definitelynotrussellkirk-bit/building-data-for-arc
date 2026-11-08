"""Input-only generator and geometric claims for public parent 80a900e0.

No reference runtime, official examples, sibling modules, or hidden labels are
read here. This file remains usable when relocated by the normal base worker.
"""
RULE_TASK_ID = 'ee_80a900e0'
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_80a900e0"
VERSION = "1.0.0"
SUMMARY = "Recognize diagonal hollow frames and extend their colored side caps as outward beams."
INVARIANTS = ["0/1 checkerboard", "geometric color roles", "complete diagonal frame perimeters", "clipped side caps", "original foreground preserved"]
AXES = {}  # Diversity comes from seeded profiles; no caller overrides are exposed.
SIDES = ("NW", "SE", "NE", "SW")


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def validate_grid(g):
    if type(g) is not list or not 5 <= len(g) <= 30:
        raise ValueError("expected 5..30 exact list rows")
    if type(g[0]) is not list or not 5 <= len(g[0]) <= 30:
        raise ValueError("expected width 5..30")
    width = len(g[0])
    if any(type(row) is not list or len(row) != width for row in g):
        raise ValueError("grid must be rectangular exact lists")
    if any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row):
        raise ValueError("grid cells must be exact integers 0..9")
    active = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v]
    if not active:
        raise ValueError("missing checkerboard carrier")
    phase = sum(active[0]) % 2
    if any((v == 0) == ((r + c) % 2 == phase) for r, row in enumerate(g) for c, v in enumerate(row)):
        raise ValueError("expected one active checkerboard parity")
    return len(g), width


def _xy(u, v):
    return ((u + v) // 2, (u - v) // 2)


def _components(g):
    remaining = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v > 1}
    found = []
    while remaining:
        start = min(remaining)
        color = g[start[0]][start[1]]
        seen, pending = {start}, [start]
        remaining.remove(start)
        while pending:
            r, c = pending.pop()
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                p = (r + dr, c + dc)
                if p in remaining and g[p[0]][p[1]] == color:
                    remaining.remove(p)
                    seen.add(p)
                    pending.append(p)
        found.append((color, seen))
    return found


def discover(g):
    h, w = validate_grid(g)
    cores, caps = [], []
    for color, cells in _components(g):
        u0, u1 = min(r + c for r, c in cells), max(r + c for r, c in cells)
        v0, v1 = min(r - c for r, c in cells), max(r - c for r, c in cells)
        if u1 - u0 < 4 or v1 - v0 < 4:
            continue
        border = {_xy(u, v) for u in range(u0, u1 + 1, 2) for v in range(v0, v1 + 1, 2)
                  if u in (u0, u1) or v in (v0, v1)}
        if cells != border:
            continue
        index = len(cores)
        cores.append({"color": color, "bounds": [u0, v0, u1, v1], "cells": [list(p) for p in sorted(cells)]})
        faces = [
            ("NW", (-1, -1), [_xy(u0 - 2, v) for v in range(v0, v1 + 1, 2)]),
            ("SE", (1, 1), [_xy(u1 + 2, v) for v in range(v0, v1 + 1, 2)]),
            ("NE", (-1, 1), [_xy(u, v0 - 2) for u in range(u0, u1 + 1, 2)]),
            ("SW", (1, -1), [_xy(u, v1 + 2) for u in range(u0, u1 + 1, 2)]),
        ]
        for side, direction, points in faces:
            visible = [(r, c) for r, c in points if 0 <= r < h and 0 <= c < w]
            colors = {g[r][c] for r, c in visible}
            if len(colors) == 1 and next(iter(colors)) > 1 and color not in colors:
                caps.append({"core_index": index, "side": side, "color": next(iter(colors)),
                             "direction": list(direction), "cells": [list(p) for p in points],
                             "visible_cells": [list(p) for p in visible]})
    return cores, caps


def analyze(g, beam="walls"):
    if beam not in ("walls", "solid") or type(beam) is not str:
        raise ValueError("beam must be walls or solid")
    h, w = validate_grid(g)
    cores, caps = discover(g)
    output = [row[:] for row in g]
    painted = {}
    conflicts = []
    for cap in caps:
        origins = cap["cells"] if beam == "solid" else [cap["cells"][0], cap["cells"][-1]]
        dr, dc = cap["direction"]
        for r, c in origins:
            for distance in range(1, h + w):
                nr, nc = r + distance * dr, c + distance * dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 1:
                    key = (nr, nc)
                    if key in painted and painted[key] != cap["color"]:
                        conflicts.append([nr, nc])
                    painted[key] = cap["color"]
                    output[nr][nc] = cap["color"]
    return {"cores": cores, "caps": caps, "output": output,
            "painted_cells": [[r, c, color] for (r, c), color in sorted(painted.items())],
            "conflicting_cells": conflicts}


def solve(g, beam="walls"):
    return analyze(g, beam)["output"]


def _rng(seed, label):
    raw = hashlib.sha256(f"80a900e0/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _put_frame(g, r0, c0, nu, nv, color, sides):
    h, w = len(g), len(g[0])
    for i in range(nu):
        for j in range(nv):
            if i in (0, nu - 1) or j in (0, nv - 1):
                r, c = r0 + i + j, c0 + i - j
                if not (0 <= r < h and 0 <= c < w) or g[r][c] != 1:
                    raise ValueError("frame placement collision")
                g[r][c] = color
    for side, cap_color in sides.items():
        if side == "NW": lattice = [(-1, j) for j in range(nv)]
        elif side == "SE": lattice = [(nu, j) for j in range(nv)]
        elif side == "NE": lattice = [(i, -1) for i in range(nu)]
        else: lattice = [(i, nv) for i in range(nu)]
        for i, j in lattice:
            r, c = r0 + i + j, c0 + i - j
            if 0 <= r < h and 0 <= c < w:
                if g[r][c] != 1:
                    raise ValueError("cap placement collision")
                g[r][c] = cap_color


def _center(cr, cc, nu, nv):
    r0 = cr - (nu + nv - 2) // 2
    c0 = cc - (nu - nv) // 2
    if (r0 + c0) % 2:
        c0 += 1
    return r0, c0


def _transform(g, rng):
    out = [row[:] for row in g]
    for _ in range(rng.randrange(4)):
        out = [list(row) for row in zip(*out[::-1])]
    if rng.randrange(2):
        out = [row[::-1] for row in out]
    return out


def sample_profile(seed, label, profile):
    rng = _rng(seed, label)
    palette = rng.sample(list(range(2, 10)), 8)
    shapes = [(19, 19), (5, 11), (27, 29), (13, 17), (17, 21),
              (23, 25), (5, 7), (15, 23), (24, 26), (30, 30)]
    h, w = shapes[profile]
    g = [[int((r + c) % 2 == 0) for c in range(w)] for r in range(h)]
    count = 1
    if profile in (1, 6):
        r0, c0 = (0, 4) if profile == 1 else (0, 2)
        # A single clipped cap teaches that one side alone launches its beam.
        sides = {"NE": palette[1]}
        _put_frame(g, r0, c0, 3, 3, palette[0], sides)
    elif profile in (2, 9):
        count = 3
        centers = [(7, 7), (7, w - 8), (h - 8, w // 2)]
        sides = [{"NW": palette[1], "SW": palette[2]},
                 {"NE": palette[2], "SE": palette[0]},
                 {"SE": palette[0], "SW": palette[1]}]
        for i, (cr, cc) in enumerate(centers):
            nu, nv = rng.randint(3, 5), rng.randint(3, 5)
            r0, c0 = _center(cr, cc, nu, nv)
            _put_frame(g, r0, c0, nu, nv, palette[i], sides[i])
    elif profile == 8:
        count = 2
        for i, (cr, cc, sides) in enumerate([(6, 6, {"NW": palette[1], "SW": palette[2]}),
                                           (17, 19, {"NE": palette[0], "SE": palette[3]})]):
            nu, nv = rng.randint(3, 5), rng.randint(3, 5)
            r0, c0 = _center(cr, cc, nu, nv)
            _put_frame(g, r0, c0, nu, nv, palette[i], sides)
    else:
        nu, nv = (3, 4) if profile == 0 else (rng.randint(3, 6), rng.randint(3, 5))
        if profile == 0 and rng.randrange(2):
            nu, nv = nv, nu
        cr, cc = h // 2 + rng.randint(-1, 1), w // 2 + rng.randint(-1, 1)
        r0, c0 = _center(cr, cc, nu, nv)
        sides = {s: palette[i + 1] for i, s in enumerate(SIDES)}
        if profile in (3, 7):
            sides.pop(SIDES[rng.randrange(4)])
        _put_frame(g, r0, c0, nu, nv, palette[0], sides)
    result = analyze(g, "solid")
    if len(result["cores"]) != count or result["conflicting_cells"]:
        raise ValueError("constructed scene is outside the nonconflicting grammar")
    return _transform(g, rng)


def lesson_inputs(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    demos = [sample_profile(seed, f"demo-{i}", i) for i in range(6)]
    queries = [sample_profile(seed, f"query-{i}", i + 6) for i in range(4)]
    _rng(seed, "complete-query-order").shuffle(queries)
    return demos, queries


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 2**63 - 1, "sample_index")
    if overrides:
        raise ValueError("no base-generator overrides are supported")
    return sample_profile(seed, f"base-{sample_index}", sample_index % 10)


def self_check(grid):
    try:
        validate_grid(grid)
    except (ValueError, TypeError) as error:
        return [str(error)]
    return []
