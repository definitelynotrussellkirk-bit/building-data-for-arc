"""Generator for arc_puzzle_bank_21_set6_s:S6_E6 — wire-length-strip output.

A red marker selects one blue wire; output is a color-6 strip of its length.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (no red marker → rule's selector returns
nothing), no_attached_wire (red marker isolated from any blue cell →
rule's wire-from-marker selector finds nothing, length undefined),
zero_length_wire (marker exists but adjacent wire is degenerate
single-cell → rule's length output is 1, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5fbb6efffb19"
VERSION = "3.0.0"  # distinct=5: output is a 1xL magenta strip (L=wire length); the 5-path bank gave only 5 lengths. Output is intrinsically 1xL monochrome so distinct = #distinct lengths. Now grow RANDOM non-branching wires of varied length (2..15) attached to the marker -> distinct = length range (~14).
TASK_ID = "5fbb6efffb19"

SUMMARY = (
    "0-bg grid (h ∈ 6-10, w ∈ 8-13) with: "
    "(a) ONE COLOR-2 RED MARKER placed "
    "at a random interior position; "
    "(b) ONE NON-BRANCHING BLUE (COLOR "
    "1) WIRE drawn from _PATHS bank (5 "
    "snake-like paths of length 4-8 "
    "cells), attached to the red marker "
    "via cell (0, 1) of the path "
    "anchoring next to the marker; "
    "(c) STRAY_COUNT ∈ 0-2 ISOLATED "
    "BLUE COMPONENTS — small 2-4 cell "
    "color-1 distractor blocks placed "
    "non-adjacent to the marker or its "
    "wire (1-cell padding). Rule "
    "(LOCATE THE RED MARKER, FIND "
    "THE BLUE WIRE ATTACHED TO IT, "
    "MEASURE ITS LENGTH, OUTPUT A "
    "COLOR-6 STRIP OF THAT LENGTH): "
    "FIND the unique COLOR-2 "
    "marker cell. WALK from the "
    "marker into the orthogonally "
    "adjacent COLOR-1 cell; follow "
    "the non-branching blue wire "
    "(each step picks the unique "
    "next-cell that isn't where we "
    "came from). COUNT the wire's "
    "TOTAL LENGTH L. STRAY BLUE "
    "components (not attached to "
    "marker) are IGNORED. OUTPUT a "
    "FRESH 1×L GRID painted "
    "uniformly in COLOR 6 "
    "(magenta). Net: the red "
    "marker selects which wire to "
    "measure; output is a "
    "magenta strip of that wire's "
    "length. Flagged intrinsic-"
    "low (uniq_out=5): wire "
    "lengths 4-8 × single color "
    "= ~5 canonical outputs."
)

INVARIANTS = [
    "background is 0",
    "there is exactly one red start marker",
    "the marker has exactly one orthogonally adjacent blue wire",
    "the marked blue wire is non-branching",
    "stray blue components, if present, are unattached distractors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_attached_wire", "zero_length_wire")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 6..10", "valid": "5..16"},
    "grid_w":            {"type": "int", "default": "rng 8..13", "valid": "6..18"},
    "wire_shape":        {"type": "choice", "default": "rng 0..4", "valid": "0..4"},
    "stray_count":       {"type": "int", "default": "rng 0..2", "valid": "0..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "marker_attached_wire_plus_strays",
                          "valid": "marker_attached_wire_plus_strays"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_marker|no_attached_wire|zero_length_wire"},
}

_PATHS = [
    [(0, 1), (0, 2), (1, 2), (2, 2), (2, 3)],
    [(0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 4)],
    [(1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (3, 3), (3, 4)],
    [(0, 1), (1, 1), (1, 2), (1, 3)],
    [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (3, 3), (3, 4), (3, 5)],
]

_STRAYS = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0)],
]


def _place_shape(g, rng, cells, occupied):
    h = len(g)
    w = len(g[0])
    max_r = max(r for r, _ in cells)
    max_c = max(c for _, c in cells)
    for _ in range(200):
        r0 = rng.randint(0, h - max_r - 1)
        c0 = rng.randint(0, w - max_c - 1)
        placed = [(r0 + r, c0 + c) for r, c in cells]
        if any(g[r][c] != 0 for r, c in placed):
            continue
        if any(abs(r - rr) + abs(c - cc) <= 1 for r, c in placed for rr, cc in occupied):
            continue
        for r, c in placed:
            g[r][c] = 1
        occupied.update(placed)
        return
    raise ValueError("could not place stray component")


_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _grow_wire(rng, h, w, marker, target):
    """A non-branching 1-wide blue wire attached to the marker, length up to
    `target`. The marker has EXACTLY ONE adjacent wire cell (the start); every
    other wire cell stays non-adjacent to the marker so the wire is the only
    blue thing the rule's walk follows."""
    mr, mc = marker
    starts = [(mr + dr, mc + dc) for dr, dc in _DIRS
              if 0 <= mr + dr < h and 0 <= mc + dc < w]
    rng.shuffle(starts)
    for s in starts:
        path = [s]; seen = {s, marker}
        for _ in range(target - 1):
            cur = path[-1]; cands = []
            for dr, dc in _DIRS:
                nr, nc = cur[0] + dr, cur[1] + dc
                if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                    continue
                if sum((nr + a, nc + b) in seen for a, b in _DIRS) != 1:
                    continue  # touches only `cur` -> stays 1-wide / non-branching
                if abs(nr - mr) + abs(nc - mc) == 1:
                    continue  # never adjacent to the marker (keeps start unique)
                cands.append((nr, nc))
            if not cands:
                break
            nxt = rng.choice(cands); path.append(nxt); seen.add(nxt)
        if len(path) >= 2:
            return path
    return None


def _blue_component(grid, start):
    h, w = len(grid), len(grid[0])
    q = [start]
    seen = {start}
    for r, c in q:
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr, nc) not in seen:
                seen.add((nr, nc)); q.append((nr, nc))
    return seen


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Marker-selected wire: exactly one red marker, one attached non-branching blue wire."""
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    bad = sorted({v for row in grid for v in row if v not in (0, 1, 2)})
    if bad:
        errs.append(f"unexpected colors present: {bad}")
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(markers) != 1:
        errs.append(f"expected exactly one red marker, found {len(markers)}")
        return errs
    mr, mc = markers[0]
    attached = []
    for dr, dc in _DIRS:
        nr, nc = mr + dr, mc + dc
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1:
            attached.append((nr, nc))
    if len(attached) != 1:
        errs.append(f"marker must have exactly one adjacent blue wire cell, found {len(attached)}")
        return errs
    wire = _blue_component(grid, attached[0])
    if len(wire) < 2:
        errs.append("attached wire is too short to teach length measurement")
    for r, c in wire:
        deg = sum((r + dr, c + dc) in wire for dr, dc in _DIRS)
        if deg > 2:
            errs.append("attached wire branches")
            break
        if (r, c) != attached[0] and abs(r - mr) + abs(c - mc) == 1:
            errs.append("more than one wire cell touches the marker")
            break
    remaining_blue = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1} - wire
    while remaining_blue:
        cell = next(iter(remaining_blue))
        comp = _blue_component(grid, cell)
        if any(abs(r - rr) + abs(c - cc) <= 1 for r, c in comp for rr, cc in wire | {(mr, mc)}):
            errs.append("stray blue component touches the marker or selected wire")
            break
        remaining_blue -= comp
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 8, 10)
        stray_lo, stray_hi = 0, 0; L = ctx.draw_int("wire_len", 3, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 13, 18)
        stray_lo, stray_hi = 1, 3; L = ctx.draw_int("wire_len", 8, 15)
    else:
        h = ctx.draw_int("grid_h", 8, 13); w = ctx.draw_int("grid_w", 10, 15)
        stray_lo, stray_hi = 0, 2; L = ctx.draw_int("wire_len", 3, 12)
    stray_count = ctx.draw_int("stray_count", stray_lo, stray_hi)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # marker + random non-branching wire of varied length
    wire = None
    for _ in range(40):
        mr = rng.randint(1, h - 2); mc = rng.randint(1, w - 2)
        wire = _grow_wire(rng, h, w, (mr, mc), L)
        if wire is not None:
            break
    if wire is None:  # fallback: minimal length-2 wire
        mr, mc = 1, 1; g[1][1] = 2; g[1][2] = 1; g[1][3] = 1
        return g
    g[mr][mc] = 2
    occupied = {(mr, mc)}
    for (r, c) in wire:
        g[r][c] = 1
        occupied.add((r, c))
    for _ in range(stray_count):
        try:
            _place_shape(g, rng, rng.choice(_STRAYS), occupied)
        except ValueError:
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        for r, c in [(2, 2), (2, 3), (3, 3), (4, 3)]: g[r][c] = 1
        return g
    if name == "no_attached_wire":
        g[3][3] = 2
        for r, c in [(6, 7), (6, 8)]: g[r][c] = 1
        return g
    if name == "zero_length_wire":
        # Marker has exactly one adjacent blue cell (length 1) — output
        # strip is degenerate single-cell.
        g[3][3] = 2
        g[3][4] = 1
        return g
    return g
