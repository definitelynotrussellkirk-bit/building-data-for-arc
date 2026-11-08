"""Input sampler for black cavities and an edge-oriented colour legend.

The self-contained builder is also retained in workspace/parametric/prototype.py
because ordinary and native executions stage different resource closures. Their
complete inputs are compared by the task's focused parity tests. This module
never derives output labels: ordinary labels come from ee_dbff022c in Racket.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "public_eval_dbff022c"
TASK_ID = "public_eval_dbff022c"
RULE_TASK_ID = "ee_dbff022c"
VERSION = "1.0.0"
RULE_HASH = "49687892c9c45277535a499eac672d70cc7ca8bd65f147a34ad39bbd0471d2a1"
SUMMARY = "Read an inward-facing edge legend to fill monochromatically enclosed black regions."
INVARIANTS = [
    "Black background, isolated dense two-line legend, unique border-to-interior direction.",
    "Every one of the 2..5 legend owners encloses at least one four-connected zero region.",
    "Repeated same-owner cavities include unequal areas; teaching profiles include maximum ties.",
    "Unmapped closed contours and mapped open contours remain visible distractors.",
    "Rectangles, diagonal enclosures, notches and multiple chambers are separated by black moats.",
]
AXES = {
    "owner_count": {
        "type": "int", "default": "rng 2..5", "valid": "2..5",
        "doc": "Number of distinct legend keys, all realized as enclosing owner colours.",
    },
    "legend_edge": {
        "type": "enum", "default": "profile", "valid": "top|right|bottom|left",
        "doc": "Grid edge containing the outward key line; the value line lies immediately inward.",
    },
}
EDGES = ("top", "right", "bottom", "left")
CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
ADJACENT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def validate_grid(grid):
    """Reject malformed ARC grids without coercing booleans or other numbers."""
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colours 0..9")


def _read_legend(grid):
    height, width = len(grid), len(grid[0])
    seen, candidates = set(), []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack, cells = [(row, col)], []
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ADJACENT:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
            r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
            bh, bw = r1 - r0 + 1, c1 - c0 + 1
            if (len(cells) != bh * bw or min(bh, bw) != 2
                    or len({grid[r][c] for r, c in cells}) < 2):
                continue
            edges = []
            if bh == 2:
                if r0 == 0:
                    edges.append("top")
                if r1 == height - 1:
                    edges.append("bottom")
            if bw == 2:
                if c0 == 0:
                    edges.append("left")
                if c1 == width - 1:
                    edges.append("right")
            if len(edges) != 1:
                continue
            edge = edges[0]
            if edge == "top":
                pairs = [(grid[r0][c], grid[r1][c]) for c in range(c0, c1 + 1)]
            elif edge == "bottom":
                pairs = [(grid[r1][c], grid[r0][c]) for c in range(c0, c1 + 1)]
            elif edge == "left":
                pairs = [(grid[r][c0], grid[r][c1]) for r in range(r0, r1 + 1)]
            else:
                pairs = [(grid[r][c1], grid[r][c0]) for r in range(r0, r1 + 1)]
            if len({key for key, _ in pairs}) == len(pairs):
                candidates.append({"edge": edge, "pairs": pairs, "mapping": dict(pairs),
                                   "bbox": (r0, c0, r1, c1)})
    if len(candidates) != 1:
        raise ValueError("grid needs one unambiguous isolated edge legend")
    return candidates[0]


def analyze(grid):
    """Enumerate eligible cavities and each owner's maximum enclosed area.

    A mixed-colour boundary does not define an owner and is left out. Bboxes are
    inclusive. Hole cell coordinates are sorted so evidence is deterministic.
    """
    validate_grid(grid)
    legend = _read_legend(grid)
    height, width = len(grid), len(grid[0])
    seen, holes, maxima = set(), [], {}
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            stack, cells, boundary = [(row, col)], [], set()
            seen.add((row, col))
            touches_edge = False
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                touches_edge |= r in (0, height - 1) or c in (0, width - 1)
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if grid[nr][nc] != 0:
                        boundary.add(grid[nr][nc])
                    elif (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if not touches_edge and len(boundary) == 1:
                owner = next(iter(boundary))
                area = len(cells)
                holes.append({"cells": sorted(cells), "owner": owner, "area": area})
                maxima[owner] = max(area, maxima.get(owner, 0))
    return {"legend": legend, "holes": holes, "maxima": maxima}


def _ring(height, width, *, dividers=(), open_top=False):
    mask = [[int(r in (0, height - 1) or c in (0, width - 1) or c in dividers)
             for c in range(width)] for r in range(height)]
    if open_top:
        mask[0][width // 2] = 0
    return mask


def _diamond(radius):
    return [[int(abs(r - radius) + abs(c - radius) == radius)
             for c in range(2 * radius + 1)] for r in range(2 * radius + 1)]


def _contour(interior):
    boundary = {(r + dr, c + dc) for r, c in interior for dr, dc in CARDINAL} - interior
    r0, c0 = min(r for r, _ in boundary), min(c for _, c in boundary)
    r1, c1 = max(r for r, _ in boundary), max(c for _, c in boundary)
    return [[int((r, c) in boundary) for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def _notch(height, width, depth=1):
    return _contour({(r, c) for r in range(height) for c in range(width)
                     if not (r < depth and c < 2)})


def _stair(size):
    return _contour({(r, c) for r in range(size) for c in range(r + 2)})


def _turn(grid, count):
    for _ in range(count):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _pieces(ctx, owners, distractor, profile, stress):
    """Fixed semantic witnesses with varied geometry, palette and placement."""
    a, b = owners[:2]
    s = int(stress)
    if profile == 0:
        pieces = [(a, _ring(5 + 2*s, 7 + 2*s, dividers=(3+s,))),
                  (a, _ring(3+s, 3+s)), (b, _diamond(2+s)),
                  (b, _ring(3+s, 4+s))]
    elif profile == 1:
        # Area and coloured-perimeter ranking disagree: 8<9 but 22>16.
        pieces = [(a, _ring(3, 10 + 4*s)), (a, _ring(5+s, 5+s)),
                  (b, _diamond(2+s)), (b, _ring(3+s, 4+s))]
    elif profile == 2:
        pieces = [(a, _ring(5 + 2*s, 10 + 2*s, dividers=(3+s,))),
                  (a, _ring(3+s, 3+s)), (b, _notch(3+s, 4+s)),
                  (b, _diamond(1+s))]
    elif profile == 3:
        pieces = [(a, _notch(4+s, 5+s, 2)), (a, _ring(3+s, 5+s)),
                  (b, _ring(4 + 2*s, 7 + 2*s, dividers=(3+s,))),
                  (b, _ring(3+s, 3+s))]
    elif profile == 4:
        pieces = [(a, _diamond(2+s)), (a, _ring(3+s, 3+s)),
                  (b, _ring(4 + 2*s, 5+s)), (b, _ring(4 + 2*s, 5+s)),
                  (b, _ring(3+s, 3+s))]
    else:
        pieces = [(a, _stair(3+s)), (a, _ring(3+s, 5 + 2*s)),
                  (b, _ring(5 + 2*s, 5 + 2*s)), (b, _ring(3+s, 4+s))]
    for i, owner in enumerate(owners[2:]):
        kind = ctx.draw_choice(f"extra_shape_{i}", ("rectangle", "notch", "diamond", "stair"))
        if kind == "rectangle":
            mask = _ring(4+s, 4+s + ctx.draw_int(f"extra_width_{i}", 0, 2))
        elif kind == "notch":
            mask = _notch(3+s, 3+s)
        elif kind == "diamond":
            mask = _diamond(2+s)
        else:
            mask = _stair(3+s)
        pieces.append((owner, mask))
    pieces += [(distractor, _ring(4+s, 5+s)),
               (ctx.draw_choice("open_owner", owners), _ring(4+s, 6+s, open_top=True))]
    # The long rectangle keeps its compact horizontal packing; whole-scene
    # rotation still presents it in both orientations.
    return [(owner, _turn(mask, ctx.draw_int(f"piece_rotation_{i}", 0, 3))
             if max(len(mask), len(mask[0])) <= 9 else mask)
            for i, (owner, mask) in enumerate(pieces)]


def _pack(ctx, pieces, height, width):
    """Place full footprints with black clearance; never remove a hard object."""
    order = sorted(range(len(pieces)),
                   key=lambda i: (len(pieces[i][1]) * len(pieces[i][1][0]),
                                  max(len(pieces[i][1]), len(pieces[i][1][0]))), reverse=True)
    for attempt in range(32):
        occupied = [0] * height
        placements = []
        for i in order:
            owner, mask = pieces[i]
            ph, pw = len(mask), len(mask[0])
            feasible = []
            for r in range(3, height - ph):
                for c in range(1, width - pw):
                    halo = ((1 << (pw + 2)) - 1) << (c - 1)
                    if not any(occupied[rr] & halo for rr in range(r - 1, r + ph + 1)):
                        feasible.append((r, c))
            if not feasible:
                break
            r, c = ctx.draw_choice(f"place_{height}_{width}_{attempt}_{i}", feasible)
            footprint = ((1 << pw) - 1) << c
            for rr in range(r, r + ph):
                occupied[rr] |= footprint
            placements.append((owner, mask, r, c))
        else:
            grid = [[0] * width for _ in range(height)]
            for owner, mask, r, c in placements:
                for dr, row in enumerate(mask):
                    for dc, cell in enumerate(row):
                        if cell:
                            grid[r + dr][c + dc] = owner
            return grid
    return None


def _scene(seed, index, stress, owner_count=None, legend_edge=None, difficulty=None):
    if type(seed) is not int or type(index) is not int or index < 0:
        raise ValueError("seed must be an integer and index a nonnegative integer")
    if type(stress) is not bool:
        raise TypeError("stress must be boolean")
    ctx = gen_ctx(seed=seed, sample_index=index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty,
                  overrides={"owner_count": owner_count, "legend_edge": legend_edge})
    count = ctx.draw_int_strict("owner_count", 2, 5)
    palette = ctx.draw_distinct_colors("palette", n=9, exclude={0})
    owners = palette[:count]
    shift = ctx.draw_int("value_shift", 1, 8)
    values = [palette[(i + shift) % 9] for i in range(count)]
    is_stress = stress or (index >= 100 and index % 2 == 0)
    pieces = _pieces(ctx, owners, palette[-1], index % 6, is_stress)
    height = 30 if is_stress else ctx.draw_int("canvas_rows", 23, 29)
    width = 30 if is_stress else ctx.draw_int("canvas_columns", 23, 29)
    grid = _pack(ctx, pieces, height, width)
    if grid is None and (height, width) != (30, 30):
        height = width = 30
        grid = _pack(ctx, pieces, height, width)
    if grid is None:
        raise ValueError("could not place the unchanged contour set with black clearance")
    col = ctx.draw_int("legend_position", 1, width - count - 1)
    grid[0][col:col + count] = list(owners)
    grid[1][col:col + count] = values
    if ctx.draw_choice("mirror_columns", (False, True)):
        grid = [row[::-1] for row in grid]
    phase_ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID)
    phase = phase_ctx.draw_choice("inward_demo_phase", (1, 2))
    if index < 6:
        rotation = (phase + (0, 2, 1, 3, 0, 2)[index]) % 4
    elif index >= 100:
        rotation = (phase + index - 100) % 4
    else:
        rotation = (phase + index) % 4
    edge = ctx.draw_choice("legend_edge", EDGES if legend_edge is not None else (EDGES[rotation],))
    grid = _turn(grid, EDGES.index(edge))
    validate_grid(grid)
    return grid


def scene(seed: int, index: int, stress: bool = False, *, owner_count: int | None = None):
    """Setting-independent input stream; even query indices also exercise 30x30."""
    return _scene(seed, index, stress, owner_count)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown generator overrides: {sorted(unknown)}")
    return _scene(seed, sample_index, False, overrides.get("owner_count"),
                  overrides.get("legend_edge"), difficulty)


def observe_overrides(grid):
    validate_grid(grid)
    legend = _read_legend(grid)
    return {"owner_count": len(legend["mapping"]), "legend_edge": legend["edge"]}


def self_check(grid, *, difficulty=None, meta=None):
    try:
        info = analyze(grid)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    mapping = info["legend"]["mapping"]
    owners = {hole["owner"] for hole in info["holes"]}
    issues = []
    if not 2 <= len(mapping) <= 5 or not set(mapping) <= owners:
        issues.append("every one of 2..5 legend owners must enclose a cavity")
    if not owners - set(mapping):
        issues.append("missing unmapped closed-contour distractor")
    if not any(hole["owner"] in mapping and hole["area"] < info["maxima"][hole["owner"]]
               for hole in info["holes"]):
        issues.append("missing unequal same-owner cavity sizes")
    return issues
