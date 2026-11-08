"""Complete-divider lattices with a frame or input-derived largest-region anchor.

Python labels are claims, independently checked by the native protected-Racket
worker. The canonical production generator and reference are not modified.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random


HOME = Path(__file__).resolve().parent
ANCHORS = ("frame", "largest")
QUERY_SHAPES = ((6, 6), (13, 19), (24, 27), (30, 30))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _anchor(settings):
    if type(settings) is not dict or set(settings) != {"anchor"}:
        raise ValueError("settings must contain exactly 'anchor'")
    value = settings["anchor"]
    if type(value) is not str or value not in ANCHORS:
        raise ValueError("anchor must be 'frame' or 'largest'")
    return value


def program(settings):
    """Return the exact native rule, including original canonical whitespace."""
    anchor = _anchor(settings)
    return (HOME / ("canonical.rkt" if anchor == "frame" else "largest.rkt")).read_text()


def _validate_bands(values, name):
    if type(values) not in (list, tuple) or not 3 <= len(values) <= 6:
        raise ValueError(f"{name} needs three through six bands")
    if any(type(x) is not int or not 1 <= x <= 6 for x in values):
        raise ValueError(f"{name} widths must be exact integers in 1..6")
    if values.count(max(values)) != 1:
        raise ValueError(f"{name} must have a unique widest band")
    if sum(values) + len(values) - 1 > 30:
        raise ValueError(f"{name} would exceed thirty cells")
    return list(values)


def lattice(row_bands, col_bands):
    """Construct a validated complete lattice; no markers or padded borders."""
    rb = _validate_bands(row_bands, "row bands")
    cb = _validate_bands(col_bands, "column bands")
    height, width = sum(rb) + len(rb) - 1, sum(cb) + len(cb) - 1
    rows, cols = [], []
    for bands, dividers in ((rb, rows), (cb, cols)):
        cursor = -1
        for size in bands[:-1]:
            cursor += size + 1
            dividers.append(cursor)
    return [[3 if r in rows or c in cols else 0 for c in range(width)]
            for r in range(height)]


def analyze(grid):
    """Validate the separate parametric grammar and bind its largest region."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty list of rows, at most 30 by 30")
    height, width = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or v not in (0, 3) for row in grid for v in row):
        raise ValueError("only exact integer background 0 and divider 3 are allowed")
    dr = [r for r in range(height) if all(v == 3 for v in grid[r])]
    dc = [c for c in range(width) if all(grid[r][c] == 3 for r in range(height))]
    rr = [[a + 1, b - 1] for a, b in zip([-1] + dr, dr + [height])]
    cr = [[a + 1, b - 1] for a, b in zip([-1] + dc, dc + [width])]
    rb = _validate_bands([b - a + 1 for a, b in rr], "row bands")
    cb = _validate_bands([b - a + 1 for a, b in cr], "column bands")
    if any(grid[r][c] != (3 if r in dr or c in dc else 0)
           for r in range(height) for c in range(width)):
        raise ValueError("every green cell must belong to a complete divider")
    pivot = [rb.index(max(rb)), cb.index(max(cb))]
    return {"row_bands": rb, "col_bands": cb, "row_ranges": rr,
            "col_ranges": cr, "pivot": pivot,
            "largest_area": max(rb) * max(cb),
            "region_shape": [len(rb), len(cb)],
            "divider_rows": dr, "divider_cols": dc}


def transform(grid, anchor):
    """Input-pure Python label claim; protected Racket is the final authority."""
    _anchor({"anchor": anchor})
    facts = analyze(grid)
    nr, nc = facts["region_shape"]
    pr, pc = facts["pivot"]
    result = [row[:] for row in grid]
    for ri, (r0, r1) in enumerate(facts["row_ranges"]):
        for ci, (c0, c1) in enumerate(facts["col_ranges"]):
            if anchor == "frame":
                corners = {(0, 0): 2, (0, nc - 1): 4,
                           (nr - 1, 0): 1, (nr - 1, nc - 1): 8}
                color = corners.get((ri, ci),
                    7 if 0 < ri < nr - 1 and 0 < ci < nc - 1 else 0)
            elif ri == pr and ci == pc:
                color = 7
            elif ri == pr or ci == pc:
                color = 0
            elif ri < pr:
                color = 2 if ci < pc else 4
            else:
                color = 1 if ci < pc else 8
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    result[r][c] = color
    return result


def _rng(seed, role, index):
    # Settings and requested counts never enter input RNG streams.
    digest = hashlib.sha256(f"9c5bdbcdcd50/lattice-v1/{seed}/{role}/{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _bands(rng, count, pivot, total=None):
    """Construct a unique-maximum bounded composition without rejection loops."""
    if total is None:
        peak = rng.randint(2, 6)
        low = peak + count - 1
        high = min(peak + (count - 1) * (peak - 1), 31 - count)
        total = rng.randint(low, high)
    else:
        feasible = [p for p in range(2, 7)
                    if p + count - 1 <= total <= p + (count - 1) * (p - 1)]
        if not feasible:
            raise ValueError("no bounded unique-maximum composition at this size")
        peak = rng.choice(feasible)
    rest, remaining = [], total - peak
    for slots in range(count - 1, 0, -1):
        low = max(1, remaining - (slots - 1) * (peak - 1))
        high = min(peak - 1, remaining - (slots - 1))
        value = rng.randint(low, high)
        rest.append(value)
        remaining -= value
    rng.shuffle(rest)
    rest.insert(pivot, peak)
    return rest


def _input(seed, role, index):
    rng = _rng(seed, role, index)
    if role == "train":
        topologies = ((5, 5), (4, 4), (6, 4), (4, 6), (3, 6), (6, 3))
        nr, nc = topologies[index]
        # D1 contains every quadrant/axis color around a noncentral anchor.
        # D2 places the largest region on a boundary and changes both coordinates.
        first_pivot = (1, 3) if _rng(seed, "teaching", 0).randrange(2) == 0 else (3, 1)
        if index == 0:
            pr, pc = first_pivot
        elif index == 1:
            # A second anti-diagonal pivot would teach a false rule that
            # infers one coordinate from the other and ignores band widths.
            pr, pc = 0, 0
        else:
            pr, pc = rng.randrange(nr), rng.randrange(nc)
        rb, cb = _bands(rng, nr, pr), _bands(rng, nc, pc)
    else:
        nr, nc = ((3, 3), (4, 5), (5, 6), (6, 6))[index]
        height, width = QUERY_SHAPES[index]
        rb = _bands(rng, nr, rng.randrange(nr), height - nr + 1)
        cb = _bands(rng, nc, rng.randrange(nc), width - nc + 1)
    return lattice(rb, cb)


def generate(seed, settings, demos=3, queries=4):
    """Return one private episode; four queries are for sequential reveal.

    The first two demos constructively distinguish the settings. Extra demo
    topologies and all query topologies are disjoint, ensuring distinct inputs
    without retrying. Requests preserve prefixes across both count axes.
    """
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    anchor = _anchor(settings)
    result = {"program_solution": program(settings)}
    for role, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            grid = _input(seed, role, index)
            pairs.append({"input": grid, "output": transform(grid, anchor)})
        result[role] = pairs
    return result
