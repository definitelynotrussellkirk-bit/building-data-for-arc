"""Self-contained edge-cut input generator and private geometric interpreter."""
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_4a21e3da"
RULE_TASK_ID = 'ee_4a21e3da'
VERSION = "1.0.0"
SUMMARY = "Cut a foreground mask from edge markers and translate selected whole sectors to their boundary corners."
INVARIANTS = ["equal background corners", "one or two orthogonal edge markers", "interior monochrome mask", "every marker axis hits the mask", "whole-sector bounding boxes"]
AXES = {}


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def selection(value):
    if type(value) is not str or value not in ("union", "intersection"):
        raise ValueError("selection must be union or intersection")
    return value


def parse(g):
    if type(g) is not list or not 5 <= len(g) <= 30:
        raise ValueError("height must be 5..30 with exact list rows")
    if type(g[0]) is not list or not 5 <= len(g[0]) <= 30:
        raise ValueError("width must be 5..30")
    h, w = len(g), len(g[0])
    if any(type(row) is not list or len(row) != w for row in g):
        raise ValueError("rectangular exact list rows required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row):
        raise ValueError("exact integer colors 0..9 required")
    bg = g[0][0]
    if any(g[r][c] != bg for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))):
        raise ValueError("all four corners must be background")
    markers = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row)
               if (r in (0, h - 1) or c in (0, w - 1)) and v != bg]
    if len(markers) not in (1, 2) or len({g[r][c] for r, c in markers}) != 1:
        raise ValueError("one or two same-color edge markers required")
    ray = g[markers[0][0]][markers[0][1]]
    other = {v for row in g for v in row} - {bg, ray}
    if len(other) != 1:
        raise ValueError("exactly one distinct foreground color required")
    fg = next(iter(other))
    if any(g[r][c] == ray for r in range(1, h - 1) for c in range(1, w - 1)):
        raise ValueError("marker color belongs only on the border")
    vertical = [p for p in markers if p[0] in (0, h - 1)]
    horizontal = [p for p in markers if p[1] in (0, w - 1)]
    if len(vertical) > 1 or len(horizontal) > 1:
        raise ValueError("markers must have distinct orientations")
    vc = vertical[0][1] if vertical else None
    hr = horizontal[0][0] if horizontal else None
    vs = (-1 if vertical[0][0] == 0 else 1) if vertical else None
    hs = (-1 if horizontal[0][1] == 0 else 1) if horizontal else None
    points = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == fg]
    if vc is not None and not any(c == vc for r, c in points):
        raise ValueError("vertical marker must hit foreground")
    if hr is not None and not any(r == hr for r, c in points):
        raise ValueError("horizontal marker must hit foreground")
    return {"height": h, "width": w, "background": bg, "foreground": fg,
            "ray_color": ray, "markers": [list(p) for p in markers], "points": points,
            "vertical_cut": vc, "horizontal_cut": hr, "vertical_side": vs, "horizontal_side": hs}


def analyze(g, mode="union"):
    selection(mode)
    a = parse(g)
    h, w, bg, fg, ray = (a[k] for k in ("height", "width", "background", "foreground", "ray_color"))
    vc, hr, vs, hs = (a[k] for k in ("vertical_cut", "horizontal_cut", "vertical_side", "horizontal_side"))
    output = [[bg] * w for _ in range(h)]
    rays = []
    if vc is not None:
        hits = [r for r, c in a["points"] if c == vc]
        lo, hi = (0, max(hits)) if vs == -1 else (min(hits), h - 1)
        rays += [[r, vc] for r in range(lo, hi + 1)]
    if hr is not None:
        hits = [c for r, c in a["points"] if r == hr]
        lo, hi = (0, max(hits)) if hs == -1 else (min(hits), w - 1)
        rays += [[hr, c] for c in range(lo, hi + 1)]
    for r, c in rays: output[r][c] = ray
    anchors = [(r, c) for r, c in a["points"] if c == vc or r == hr]
    for r, c in anchors: output[r][c] = fg
    regions = []
    for rs in (-1, 1) if hr is not None else (vs,):
        for cs in (-1, 1) if vc is not None else (hs,):
            cells = [(r, c) for r, c in a["points"] if c != vc and r != hr
                     and (hr is None or (r < hr if rs == -1 else r > hr))
                     and (vc is None or (c < vc if cs == -1 else c > vc))]
            if not cells:
                continue
            contacts = ([rs == vs] if vc is not None else []) + ([cs == hs] if hr is not None else [])
            keep = any(contacts) if mode == "union" else all(contacts)
            r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
            c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
            dr = -r0 if rs == -1 else h - 1 - r1
            dc = -c0 if cs == -1 else w - 1 - c1
            record = {"corner": ("N" if rs == -1 else "S") + ("W" if cs == -1 else "E"),
                      "cells": [list(p) for p in cells], "bounds": [r0, c0, r1, c1],
                      "shift": [dr, dc], "selected": keep}
            regions.append(record)
            if keep:
                for r, c in cells: output[r + dr][c + dc] = fg
    return {**a, "foreground_count": len(a["points"]), "rays": rays,
            "anchors": [list(p) for p in anchors], "regions": regions, "output": output}


def solve(g, mode="union"):
    return analyze(g, mode)["output"]


def self_check(g):
    try:
        parse(g)
    except (ValueError, TypeError) as error:
        return [str(error)]
    return []


def rng_for(seed, label):
    return random.Random(int.from_bytes(hashlib.sha256(f"4a21e3da/{seed}/{label}".encode()).digest(), "big"))


def _rotate(g, turns):
    out = [row[:] for row in g]
    for _ in range(turns): out = [list(row) for row in zip(*out[::-1])]
    return out


def sample_profile(seed, label, profile):
    rng = rng_for(seed, label)
    profiles = [(17, 19, "BR"), (11, 15, "T"), (13, 21, "L"),
                (9, 13, "BL"), (21, 25, "B"), (25, 27, "R"),
                (5, 5, "TR"), (15, 23, "B"), (24, 28, "R"), (30, 30, "TL")]
    h, w, edges = profiles[profile]
    hr = h // 2 + (rng.randint(-1, 1) if h > 7 else 0)
    vc = w // 2 + (rng.randint(-1, 1) if w > 7 else 0)
    r0, r1, c0, c1 = (1, h - 2, 1, w - 2) if profile in (6, 9) else (2, h - 3, 2, w - 3)
    v = any(e in edges for e in "TB")
    horizontal = any(e in edges for e in "LR")
    points = set()
    rparts = [(r0, hr - 1), (hr + 1, r1)] if horizontal else [(r0, r1)]
    cparts = [(c0, vc - 1), (vc + 1, c1)] if v else [(c0, c1)]
    density = .75 if profile == 9 else rng.uniform(.25, .7)
    for lo_r, hi_r in rparts:
        for lo_c, hi_c in cparts:
            if lo_r > hi_r or lo_c > hi_c: continue
            points.update((r, c) for r in range(lo_r, hi_r + 1) for c in range(lo_c, hi_c + 1) if rng.random() < density)
            points.update({(lo_r, lo_c), (hi_r, hi_c)})
    if profile == 0:
        # Rich disconnected jointly-selected sector: one local box, not components.
        points = {(r, c) for r, c in points if not (r > hr and c > vc) and not (r < hr and c > vc)}
        points.update({(hr + 1, vc + 1), (hr + 1, vc + 2), (hr + 2, vc + 1), (r1 - 1, c1 - 1)})
        points.add((r0 + 1, c1))
    if profile == 1:
        points = {(r, c) for r, c in points if c < vc}
        points.add((r0 + 2, vc + 2))
    if v:
        points.update((r, vc) for r in ((r0 + 1, r1 - 1) if r1 - r0 >= 4 else (r0, r1)))
    if horizontal:
        points.update((hr, c) for c in ((c0 + 1, c1 - 1) if c1 - c0 >= 4 else (c0, c1)))
    bg, fg, ray = rng.sample(range(10), 3)
    g = [[bg] * w for _ in range(h)]
    for r, c in points: g[r][c] = fg
    for edge in edges:
        r, c = (0, vc) if edge == "T" else (h - 1, vc) if edge == "B" else (hr, 0) if edge == "L" else (hr, w - 1)
        g[r][c] = ray
    # Shared rotation keeps the two single-axis lessons physically distinct.
    turns = rng_for(seed, "lesson-rotation").randrange(4)
    if profile >= 3:
        if rng.choice((False, True)): g = g[::-1]
        if rng.choice((False, True)): g = [row[::-1] for row in g]
    g = _rotate(g, turns)
    parse(g)
    return g


def lesson_inputs(seed):
    integer(seed, 0, 2**63 - 1, "seed")
    demos = [sample_profile(seed, f"demo-{i}", i) for i in range(6)]
    queries = [sample_profile(seed, f"query-{i}", i + 6) for i in range(4)]
    rng_for(seed, "complete-query-order").shuffle(queries)
    return demos, queries


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(sample_index, 0, 2**63 - 1, "sample_index")
    if overrides: raise ValueError("no caller overrides are supported")
    return sample_profile(seed, f"base-{sample_index}", sample_index % 10)
