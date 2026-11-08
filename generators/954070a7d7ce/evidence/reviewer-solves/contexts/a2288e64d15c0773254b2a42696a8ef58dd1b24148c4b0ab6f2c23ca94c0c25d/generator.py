"""Frame-local cross filling, with exact placement and executable checks.

Ordinary samples contain one or two separated hollow 9-frames. Each has two
matching 1..8 markers: one below its top wall, one inside its left wall. The
unchanged Racket authority extends their column and row across THAT frame's
interior. Repeated colors deliberately prevent treating color as frame identity.

Every consecutive four default indices cover a single frame, distinct-color
frames, shared-color horizontal frames, and shared-color vertical frames.
Explicit overrides take precedence over this teaching schedule. Invalid/no-op
scenes are diagnostic mutation fixtures, never ordinary generation modes.
"""
from __future__ import annotations

import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "954070a7d7ce"
TASK_ID = "954070a7d7ce"
VERSION = "2.0.2"
RULE_HASH = "285c825480d1"
SUMMARY = "One or two separated 9-frames with paired axis markers; repeated colors require frame-local crosses."
EXAMPLES_NEEDED = 4
INVARIANTS = [
    "A rectangular ARC grid has background 0 and one or two hollow rectangular 9-frames.",
    "Frame bounding boxes have a one-cell Chebyshev separation and sides of at least four cells.",
    "Each frame has exactly two matching markers in 1..8: below its top wall and inside its left wall, excluding their common corner.",
    "Every nonzero cell belongs to a complete frame wall or one of its two markers.",
    "Crosses extend to all interior cells of the marked row and column; walls and exterior stay unchanged.",
]
AXES = {
    "grid_h": {"type": "int", "default": "80% canonical-scale mixture, 20% rng 9..14", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "80% canonical-scale mixture, 20% rng 11..20", "valid": "11..20"},
    "n_frames": {"type": "int", "default": "four-profile schedule", "valid": "1..2"},
    "n_distinct_colors": {"type": "int", "default": "four-profile schedule", "valid": "1..2",
                          "doc": "Number of marker colors, excluding fixed background 0 and frame 9."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [{"n_frames": 1, "n_distinct_colors": 2}]
PALETTE_KINDS = ()
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
SCHEDULE_PROFILES = ("single", "distinct", "shared_horizontal", "shared_vertical")


def schedule_profile(seed, sample_index, difficulty=None):
    """Seed-rotated period four; no dependence on caller history or difficulty."""
    digest = hashlib.sha256(f"{TASK_ID}|{VERSION}|{seed}|schedule".encode()).digest()
    return SCHEDULE_PROFILES[(int.from_bytes(digest[:2], "big") + sample_index) % 4]


def _analyse(grid):
    """Return validated frame records (bbox, marker column/row, color) and errors."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["expected a nonempty grid"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return [], ["expected nonempty grid rows"]
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        return [], ["grid dimensions must be in 1..30"]
    if any(len(row) != w for row in grid):
        return [], ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return [], ["grid cells must be integers 0..9, not booleans"]

    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9}
    components = []
    while remaining:
        origin = min(remaining)
        remaining.remove(origin)
        pending, cells = [origin], {origin}
        while pending:
            r, c = pending.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    pending.append(nxt)
        components.append(cells)

    errors, records, boxes, accounted = [], [], [], set()
    if not 1 <= len(components) <= 2:
        errors.append(f"expected 1..2 frame components, got {len(components)}")
    for index, cells in enumerate(components):
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if r in (r0, r1) or c in (c0, c1)}
        if cells != border or r1 - r0 < 3 or c1 - c0 < 3:
            errors.append(f"frame {index}: incomplete, nonrectangular, or too small")
            continue
        boxes.append((r0, c0, r1, c1))
        marks = [(r, c, grid[r][c]) for r in range(r0 + 1, r1)
                 for c in range(c0 + 1, c1) if grid[r][c] != 0]
        top = [(r, c, v) for r, c, v in marks if r == r0 + 1 and c > c0 + 1 and 1 <= v <= 8]
        left = [(r, c, v) for r, c, v in marks if c == c0 + 1 and r > r0 + 1 and 1 <= v <= 8]
        if len(marks) != 2 or len(top) != 1 or len(left) != 1:
            errors.append(f"frame {index}: expected exactly two axis markers, excluding the common corner")
            continue
        if top[0][2] != left[0][2]:
            errors.append(f"frame {index}: axis marker colors differ")
            continue
        accounted.update((r, c) for r, c, _ in marks)
        records.append((r0, c0, r1, c1, top[0][1], left[0][0], top[0][2]))

    for i, (r0, c0, r1, c1) in enumerate(boxes):
        for a0, b0, a1, b1 in boxes[i + 1:]:
            if not (r1 + 1 < a0 or a1 + 1 < r0 or c1 + 1 < b0 or b1 + 1 < c0):
                errors.append("frame bounding boxes overlap or lack a one-cell separation")
    all_marks = {(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)}
    if all_marks != accounted:
        errors.append("unaccounted, misplaced, or mismatched marker cells")
    return records, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check geometry and marker semantics; metadata never bypasses validation."""
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    """Semantic input domain, not equality to the finite canonical sample set."""
    return self_check(grid)


def _slots(h, w, count, profile, rng):
    if count == 1:
        return [(0, 0, h, w)]
    vertical = profile == "shared_vertical" or (profile not in {"shared_horizontal"} and rng.randrange(2) == 0)
    # h>=9 and w>=11 ensure two minimum 4x4 frames plus a zero-cell gap fit
    # on either axis. Partition first: requested frames can never be dropped.
    if vertical:
        cut = rng.randint(4, h - 5)
        return [(0, 0, cut, w), (cut + 1, 0, h - cut - 1, w)]
    cut = rng.randint(4, w - 5)
    return [(0, 0, h, cut), (0, cut + 1, h, w - cut - 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}; supported: {sorted(AXES)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if type(seed) is not int or type(sample_index) is not int:
        raise ValueError("seed and sample_index must be integers")
    profile = schedule_profile(seed, sample_index, difficulty)
    # Normalize scheduled defaults before bounded draws. Only genuinely supplied
    # non-None values constrain the other count; impossible explicit pairs fail.
    effective = {key: value for key, value in overrides.items() if value is not None}
    nf = effective.get("n_frames", 1 if profile == "single" else 2)
    nc = effective.get("n_distinct_colors", 2 if profile == "distinct" else 1)
    if "n_distinct_colors" in effective and "n_frames" not in effective:
        nf = max(nf, nc)
    if "n_frames" in effective and "n_distinct_colors" not in effective:
        nc = min(nc, nf)
    if nf == 1 and nc == 2:
        raise ValueError("incompatible n_frames=1 and n_distinct_colors=2")
    effective.update(n_frames=nf, n_distinct_colors=nc)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    # Preserve substantial mass at the observed 9..12 by 11..15 scale without
    # copying any canonical grid or coupling the answer to a particular size.
    # The other fifth retains the full declared canvas domain. Explicit sizes
    # always win, even when only one dimension is supplied.
    canvas_rng = ctx.draw_rng("canvas_scale")
    if canvas_rng.randrange(5) != 0:
        ctx.overrides.setdefault("grid_h", canvas_rng.randint(9, 12))
        ctx.overrides.setdefault("grid_w", canvas_rng.randint(11, 15))
    h, w = ctx.draw_int("grid_h", 9, 14), ctx.draw_int("grid_w", 11, 20)
    count = ctx.draw_int("n_frames", 1, 2)
    n_colors = ctx.draw_int("n_distinct_colors", 1, 2)
    palette = ctx.draw_distinct_colors("mark_palette", n=n_colors, exclude=(0, 9))
    rng = ctx.draw_rng(f"layout.{difficulty or 'medium'}")
    g = full_grid(h, w, 0)
    for index, (sr, sc, sh, sw) in enumerate(_slots(h, w, count, profile, rng)):
        fh, fw = rng.randint(4, min(9, sh)), rng.randint(4, min(9, sw))
        r0, c0 = sr + rng.randint(0, sh - fh), sc + rng.randint(0, sw - fw)
        r1, c1 = r0 + fh - 1, c0 + fw - 1
        for c in range(c0, c1 + 1):
            g[r0][c] = g[r1][c] = 9
        for r in range(r0, r1 + 1):
            g[r][c0] = g[r][c1] = 9
        color = palette[index % n_colors]
        tc, lr = rng.randint(c0 + 2, c1 - 1), rng.randint(r0 + 2, r1 - 1)
        g[r0 + 1][tc] = g[lr][c0 + 1] = color
    records, errors = _analyse(g)
    if errors or len(records) != count or len({record[6] for record in records}) != n_colors:
        raise RuntimeError(f"constructed frame/count postcondition failed: {errors}")
    return g


def observe_overrides(grid):
    records, errors = _analyse(grid)
    if errors:
        return {"errors": errors}
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_frames": len(records),
            "n_distinct_colors": len({record[6] for record in records})}


def _paint_records(grid, records):
    out = [list(row) for row in grid]
    for r0, c0, r1, c1, tc, lr, color in records:
        for r in range(r0 + 1, r1):
            out[r][tc] = color
        for c in range(c0 + 1, c1):
            out[lr][c] = color
    return out


def rule_mirror(grid):
    """Diagnostic only. Training labels must still come from canonical Racket."""
    records, errors = _analyse(grid)
    return None if errors else _paint_records(grid, records)


def _one_cross_per_color(grid):
    records, errors = _analyse(grid)
    if errors:
        return [list(row) for row in grid]
    selected, seen = [], set()
    for record in records:
        if record[6] not in seen:
            selected.append(record)
            seen.add(record[6])
    return _paint_records(grid, selected)


def _first_frame_only(grid):
    records, errors = _analyse(grid)
    return [list(row) for row in grid] if errors else _paint_records(grid, records[:1])


def _shared_colors(grid):
    records, errors = _analyse(grid)
    return not errors and len(records) == 2 and records[0][6] == records[1][6]


def _multiple_frames(grid):
    records, errors = _analyse(grid)
    return not errors and len(records) == 2


SEMANTIC_RIVALS = {"one_cross_per_color": _one_cross_per_color, "first_frame_only": _first_frame_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"one_cross_per_color": _one_cross_per_color}
SEMANTIC_WITNESSES = {"shared_color_requires_frame_locality": _shared_colors,
                      "multiple_frames_require_multiple_crosses": _multiple_frames}
WITNESS_RIVALS = {"shared_color_requires_frame_locality": ["one_cross_per_color"],
                  "multiple_frames_require_multiple_crosses": ["first_frame_only"]}


def lesson_identifiable(demos, query) -> list[str]:
    """Check only declared competitors, not universal uniqueness of a rule."""
    query_grid = query.get("input") if isinstance(query, dict) else query
    expected = rule_mirror(query_grid)
    if expected is None:
        return ["query is outside the paired-frame domain"]
    reasons = []
    for index, pair in enumerate(demos):
        answer = rule_mirror(pair["input"])
        if answer is None or answer != pair.get("output"):
            reasons.append(f"demonstration {index} disagrees with paired-frame semantics")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair.get("output") for pair in demos) and rival(query_grid) != expected:
            reasons.append(f"unresolved answer-changing competitor: {name}")
    return reasons


def mutation_fixtures():
    base = generate(19, 0, n_frames=1, n_distinct_colors=1)
    (r0, c0, r1, c1, tc, lr, color), = _analyse(base)[0]
    broken = [row[:] for row in base]
    broken[r0][c0 + 1] = 0
    mismatch = [row[:] for row in base]
    mismatch[lr][c0 + 1] = color % 8 + 1
    absent = [row[:] for row in base]
    absent[r0 + 1][tc] = 0
    interior = [row[:] for row in base]
    interior[r0 + 1][c0 + 1] = color
    no_frame = full_grid(len(base), len(base[0]), 0)
    return [("broken_wall", broken), ("mismatched_marks", mismatch),
            ("missing_top_marker", absent), ("corner_marker", interior), ("no_frame", no_frame)]
