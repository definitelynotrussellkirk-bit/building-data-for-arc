"""Self-contained input generator and visual-program interpreter claims."""
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_136b0064"
VERSION = "1.0.0"
SUMMARY = "Decode glyph commands in columns and draw their stateful cursor path on the right canvas."
INVARIANTS = ["unique full-height separator4", "3x3 glyph codebook", "canvas marker5", "one-row command advance", "both scan orders stay in bounds"]
AXES = {}  # Diversity comes from seeded profiles; no caller overrides are exposed.
MASKS = {"R3": ("110", "101", "010"), "L2": ("101", "101", "111"),
         "L4": ("111", "010", "101"), "D2": ("101", "010", "010")}
DECODE = {mask: name for name, mask in MASKS.items()}
MOTIONS = {"R3": (0, 1, 3), "L2": (0, -1, 2), "L4": (0, -1, 4), "D2": (1, 0, 2)}
INKS = (1, 2, 3, 5, 6, 7, 8, 9)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _scan(scan):
    if type(scan) is not str or scan not in ("columns", "rows"):
        raise ValueError("scan must be columns or rows")
    return scan


def parse(grid):
    if type(grid) is not list or not 3 <= len(grid) <= 30:
        raise ValueError("height must be 3..30 exact list rows")
    if type(grid[0]) is not list or not 8 <= len(grid[0]) <= 30:
        raise ValueError("input width must be 8..30")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("rectangular exact list rows required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer colors 0..9 required")
    separators = [c for c in range(w) if all(grid[r][c] == 4 for r in range(h))]
    if len(separators) != 1:
        raise ValueError("expected one full-height separator4")
    sep = separators[0]
    if (sep + 1) % 4 or not 1 <= (sep + 1) // 4 <= 4 or w - sep - 1 < 4:
        raise ValueError("invalid program/canvas geometry")
    canvas = [row[sep + 1:] for row in grid]
    if any(v not in (0, 5) for row in canvas for v in row):
        raise ValueError("input canvas must be blank except marker5")
    markers = [(r, c) for r, row in enumerate(canvas) for c, v in enumerate(row) if v == 5]
    if len(markers) != 1:
        raise ValueError("expected one canvas marker")
    slots, covered = [], set()
    for r in range(0, h - 2, 4):
        for c in range(0, sep - 2, 4):
            points = [(r + dr, c + dc) for dr in range(3) for dc in range(3)]
            covered.update(points)
            colors = {grid[rr][cc] for rr, cc in points} - {0}
            if not colors:
                continue
            if len(colors) != 1 or 4 in colors:
                raise ValueError("glyphs require one non-separator ink")
            mask = tuple("".join("1" if grid[r + dr][c + dc] else "0" for dc in range(3)) for dr in range(3))
            if mask not in DECODE:
                raise ValueError("unknown glyph")
            op = DECODE[mask]
            dr, dc, length = MOTIONS[op]
            slots.append({"row": r // 4, "column": c // 4, "opcode": op,
                          "ink": next(iter(colors)), "direction": [dr, dc], "length": length})
    if not slots:
        raise ValueError("empty program")
    if any(grid[r][c] != 0 for r in range(h) for c in range(sep) if (r, c) not in covered):
        raise ValueError("nonzero gap or padding")
    return {"separator": sep, "canvas": canvas, "marker": list(markers[0]), "slots": slots}


def ordered(slots, scan):
    _scan(scan)
    return sorted(slots, key=(lambda x: (x["column"], x["row"])) if scan == "columns" else (lambda x: (x["row"], x["column"])))


def _execute(parsed, scan):
    canvas = [row[:] for row in parsed["canvas"]]
    h, w = len(canvas), len(canvas[0])
    r, c = parsed["marker"]
    instructions = ordered(parsed["slots"], scan)
    trace = []
    for instruction in instructions:
        sr, sc = r + 1, c
        dr, dc = instruction["direction"]
        cells = [[sr + k * dr, sc + k * dc] for k in range(instruction["length"])]
        if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in cells):
            raise ValueError("instruction leaves canvas")
        for rr, cc in cells:
            canvas[rr][cc] = instruction["ink"]
        r, c = cells[-1]
        trace.append({"opcode": instruction["opcode"], "ink": instruction["ink"],
                      "start": [sr, sc], "end": [r, c], "cells": cells})
    return {"marker": parsed["marker"], "instructions": instructions, "trace": trace, "output": canvas}


def analyze(grid, scan="columns"):
    _scan(scan)
    parsed = parse(grid)
    return _execute(parsed, scan)


def solve(grid, scan="columns"):
    return analyze(grid, scan)["output"]


def validate_grid(grid):
    # The matched sampler has a narrower domain than the original columns rule.
    # Two official inputs leave the canvas if interpreted in the alternate order.
    parsed = parse(grid)
    for mode in ("columns", "rows"):
        _execute(parsed, mode)
    return len(grid), len(grid[0])


def _rng(seed, label):
    return random.Random(int.from_bytes(hashlib.sha256(f"136b0064/{seed}/{label}".encode()).digest(), "big"))


def _range_for(slots, mode):
    x, lo, hi = 0, 0, 0
    for item in ordered(slots, mode):
        _, dc, n = MOTIONS[item["opcode"]]
        x += dc * (n - 1)
        lo, hi = min(lo, x), max(hi, x)
    return lo, hi


def sample_profile(seed, label, profile):
    rng = _rng(seed, label)
    # height, glyph rows, glyph columns, canvas width
    profiles = [(3, 1, 1, 8), (13, 3, 2, 10), (11, 2, 3, 9),
                (15, 3, 1, 11), (19, 4, 2, 12), (23, 5, 3, 14),
                (3, 1, 1, 6), (15, 3, 3, 11), (23, 5, 2, 16), (30, 7, 3, 18)]
    h, nrows, ncols, width = profiles[profile]
    holes = {(1, 0)} if profile == 1 else ({(1, 1), (2, 0)} if profile == 7 else set())
    positions = [(r, c) for r in range(nrows) for c in range(ncols) if (r, c) not in holes]
    count = len(positions)
    for attempt in range(256):
        if profile == 0:
            ops = ["R3"]
        elif profile == 2:
            ops = ["R3", "L2", "L4", "D2", "R3", "D2"]
        elif count >= 4:
            ops = list(MASKS) + rng.choices(["R3", "R3", "L2", "L4", "D2"], k=count - 4)
        else:
            ops = rng.choices(list(MASKS), k=count)
        rng.shuffle(ops)
        slots = [{"row": r, "column": c, "opcode": op} for (r, c), op in zip(positions, ops)]
        lo1, hi1 = _range_for(slots, "columns")
        lo2, hi2 = _range_for(slots, "rows")
        low, high = -min(lo1, lo2), width - 1 - max(hi1, hi2)
        duration = count + ops.count("D2")
        required_marker_row = (0 if profile == 0 else 1 if profile == 1 else 2 if profile == 2 else 0)
        if low > high or required_marker_row + duration >= h:
            continue
        marker_r = required_marker_row if profile in (0, 1, 2) else rng.randint(0, min(2, h - 1 - duration))
        marker_c = rng.randint(low, high)
        break
    else:
        raise ValueError("bounded matched-order sampler exhausted")
    sep = 4 * ncols - 1
    grid = [[0] * (sep + 1 + width) for _ in range(h)]
    for r in range(h):
        grid[r][sep] = 4
    grid[marker_r][sep + 1 + marker_c] = 5
    legacy_ink = {"R3": 1, "L2": 2, "L4": 3, "D2": 6}
    assigned_inks = {}
    for item in slots:
        op = item["opcode"]
        ink = 5 if profile == 0 or (profile == 1 and op == "D2") else rng.choice([x for x in INKS if x != legacy_ink[op]])
        if profile == 2 and (item["row"], item["column"]) == (1, 2):
            # Opposite ends of this odd row must distinguish straight and snake scans.
            other = assigned_inks[(1, 0)]
            if ink == other:
                ink = next(x for x in INKS if x not in (other, legacy_ink[op]))
        assigned_inks[(item["row"], item["column"])] = ink
        for r in range(3):
            for c in range(3):
                if MASKS[op][r][c] == "1":
                    grid[4 * item["row"] + r][4 * item["column"] + c] = ink
    validate_grid(grid)
    return grid


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
        raise ValueError("no base-generator overrides supported")
    return sample_profile(seed, f"base-{sample_index}", sample_index % 10)


def self_check(grid):
    try:
        validate_grid(grid)
    except (ValueError, TypeError) as error:
        return [str(error)]
    return []
