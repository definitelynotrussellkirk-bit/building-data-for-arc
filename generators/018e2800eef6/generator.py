"""Generator for arc_puzzle_bank_21_set11_bundle:hard_k19 (task 018e2800eef6).

THE RULE (what a solver must learn to see):
  Two hollow rectangular frames in colors {6, 7}. One frame's interior
  holds a motif; the other is empty. An external key cell — the first
  scan-order cell colored 1, 2 or 3 — selects a transform (1=flip-lr,
  2=flip-ud, 3=rot-180; no key = copy unchanged). Output: blank canvas
  + both frames repainted + the TRANSFORMED motif in the empty frame's
  interior. The source motif and the key are erased. Interior cells
  colored 6/7 count as holes (dropped from the copy).

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - everything that was hardcoded now varies: grid size, frame
    positions (horizontal OR vertical arrangement), which side is the
    source, frame colors (6/7, 7/6, even 6/6 or 7/7), interior size
    (3x3..4x5), random motifs, key position
    (the old generator had 12 possible inputs total: 3 keys x 4 motifs
    on one fixed 11x15 layout — smoke showed unique_in=12)
  - holes_67 boards: a 6/7 cell INSIDE the source motif is dropped by
    the copy — previously unreachable
  - no_key boards: the motif copies unchanged (identity branch)

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - conflicting_keys  two key cells: scan order silently decides
  (both_frames_filled / no_target_frame are NOT offered — both CRASH
  the rule at (first '()) when no empty/filled frame exists)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "018e2800eef6"
VERSION = "2.0.2"
TASK_ID = "018e2800eef6"
SUMMARY = (
    "Two same-interior hollow frames in colors from {6,7} at varied "
    "positions/arrangements; one holds a random motif (colors 4/5/8/9, "
    "optionally with 6/7 hole cells the copy drops), the other is "
    "empty; a key cell (1=flip-lr, 2=flip-ud, 3=rot-180, absent=copy) "
    "sits on the background. Rule: repaint frames on a blank canvas "
    "and place the transformed motif in the empty frame."
)

# Rivals: 'copy unchanged' refuted by keyed demos. 'key color is
# decoration' refuted by transform varying with key. 'keep the source
# motif' refuted (it is erased). 'frames always left-source' refuted
# by right/bottom-source demos. 'interior 6/7 cells copy too' refuted
# by holes_67 demos. 4 demos: all 3 keys + >=1 no_key or holes board.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly two hollow frames, colors in {6,7}, equal interior dims",
    "exactly one frame interior holds a motif; the other is empty",
    "motif colors avoid {1,2,3} (would hijack the key) and use {4,5,8,9}",
    "at most one key cell on the background (helpful path)",
    "frames and key never touch each other",
]

DEGENERATE_TEXTURES = ("conflicting_keys",)
HELPFUL_TEXTURES = ("plain", "no_key", "holes_67")

AXES = {
    "grid_h":      {"type": "int", "default": "rng 10..13 (hard 12..15)",
                    "valid": "9..16", "doc": "Grid height."},
    "grid_w":      {"type": "int", "default": "rng 13..17 (hard 15..20)",
                    "valid": "11..22", "doc": "Grid width."},
    "key":         {"type": "int", "default": "rng 1..3", "valid": "1..3",
                    "doc": "1=flip-lr 2=flip-ud 3=rot-180."},
    "interior_h":  {"type": "int", "default": "rng 3..4", "valid": "2..5",
                    "doc": "Frame interior height."},
    "interior_w":  {"type": "int", "default": "rng 3..5", "valid": "2..5",
                    "doc": "Frame interior width."},
    "arrangement": {"type": "enum", "default": "rng", "valid": "horizontal|vertical",
                    "doc": "Side-by-side or stacked frames."},
    "src_first":   {"type": "bool", "default": "rng", "valid": "0|1",
                    "doc": "Whether the scan-first frame holds the motif."},
    "texture":     {"type": "str", "default": "rng plain|no_key|holes_67",
                    "valid": "plain|no_key|holes_67|conflicting_keys",
                    "doc": "Set to a degenerate name to build a rule-hiding input."},
}

_MOTIF_COLORS = (4, 5, 8, 9)
_FRAME_COLORS = (6, 7)


def _random_motif(rng, ih, iw, hole_color):
    """Interior grid (ih x iw): >=2 motif cells, asymmetric enough that
    flips/rotations visibly change it. hole_color (or None) plants one
    frame-palette cell the copy will drop — it must DIFFER from the
    host frame's color, else it merges with the ring and the frame?
    predicate rejects the whole frame (rule crash)."""
    for _ in range(60):
        cells = {}
        n = rng.randint(max(2, (ih * iw) // 3), max(3, (ih * iw) * 2 // 3))
        spots = [(r, c) for r in range(ih) for c in range(iw)]
        rng.shuffle(spots)
        for r, c in spots[:n]:
            cells[(r, c)] = rng.choice(_MOTIF_COLORS)
        grid = [[cells.get((r, c), 0) for c in range(iw)] for r in range(ih)]
        mirrored = [row[::-1] for row in grid]
        upended = grid[::-1]
        rotated = [row[::-1] for row in grid[::-1]]
        if grid in (mirrored, upended, rotated):
            continue  # symmetric: the key transform would be invisible
        if hole_color is not None:
            r, c = spots[0]
            grid[r][c] = hole_color
        return grid
    # near-impossible fallback: corner-anchored asymmetric pair
    grid = [[0] * iw for _ in range(ih)]
    grid[0][0] = 4
    if iw > 1:
        grid[ih - 1][1] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture",
                                  ("plain", "plain", "plain", "no_key", "holes_67"))

    key = int(overrides.get("key", ctx.draw_int("key", 1, 3)))
    ih = int(overrides.get("interior_h", ctx.draw_int("interior_h", 3, 4)))
    iw = int(overrides.get("interior_w", ctx.draw_int("interior_w", 3, 5)))
    arrangement = overrides.get(
        "arrangement", ctx.draw_choice("arrangement", ("horizontal", "vertical")))
    src_first = bool(int(overrides.get("src_first", ctx.draw_int("src_first", 0, 1))))
    rng = ctx.draw_rng("layout")

    fh, fw = ih + 2, iw + 2
    if arrangement == "horizontal":
        min_h, min_w = fh + 3, 2 * fw + 3
    else:
        min_h, min_w = 2 * fh + 3, fw + 3
    if difficulty == "hard":
        h = ctx.draw_int("grid_h", max(min_h, 12), max(min_h, 15))
        w = ctx.draw_int("grid_w", max(min_w, 15), max(min_w, 20))
    else:
        h = ctx.draw_int("grid_h", min_h, min_h + 3)
        w = ctx.draw_int("grid_w", min_w, min_w + 4)
    h, w = min(h, 22), min(w, 28)

    g = full_grid(h, w, 0)
    # frame placement: random within halves, never touching
    if arrangement == "horizontal":
        r1 = rng.randint(1, h - fh - 1)
        r2 = rng.randint(1, h - fh - 1)
        c1 = rng.randint(0, (w - 1) // 2 - fw)
        c2 = rng.randint((w + 1) // 2 + 1, w - fw)
    else:
        c1 = rng.randint(1, w - fw - 1)
        c2 = rng.randint(1, w - fw - 1)
        r1 = rng.randint(0, (h - 1) // 2 - fh)
        r2 = rng.randint((h + 1) // 2 + 1, h - fh)
    col_a = rng.choice(_FRAME_COLORS)
    col_b = rng.choice(_FRAME_COLORS)
    draw_frame(g, r1, c1, r1 + fh - 1, c1 + fw - 1, col_a)
    draw_frame(g, r2, c2, r2 + fh - 1, c2 + fw - 1, col_b)

    # motif into the chosen source frame; the hole cell (if any) must
    # not share the source frame's color or it merges with the ring
    src_frame_color = col_a if src_first else col_b
    hole_color = None
    if texture == "holes_67":
        hole_color = 7 if src_frame_color == 6 else 6
    motif = _random_motif(rng, ih, iw, hole_color)
    sr, sc = (r1, c1) if src_first else (r2, c2)
    for r in range(ih):
        for c in range(iw):
            if motif[r][c]:
                g[sr + 1 + r][sc + 1 + c] = motif[r][c]

    # key: one cell of color `key` on free bg, not adjacent to frames
    # and NEVER inside a frame bbox (a key in the empty frame's interior
    # makes both frames 'patterned' and crashes the rule)
    if texture != "no_key":
        boxes = ((r1, c1, r1 + fh - 1, c1 + fw - 1),
                 (r2, c2, r2 + fh - 1, c2 + fw - 1))
        for _ in range(120):
            kr, kc = rng.randrange(h), rng.randrange(w)
            if any(b[0] <= kr <= b[2] and b[1] <= kc <= b[3] for b in boxes):
                continue
            if all(g[rr][cc] == 0
                   for rr in range(max(0, kr - 1), min(h, kr + 2))
                   for cc in range(max(0, kc - 1), min(w, kc + 2))):
                g[kr][kc] = key
                break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Two equal hollow frames; exactly one has a motif; key is unique/optional."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    frames = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            for r1 in range(r0 + 2, h):
                for c1 in range(c0 + 2, w):
                    border = (
                        [(r0, c) for c in range(c0, c1 + 1)]
                        + [(r1, c) for c in range(c0, c1 + 1)]
                        + [(r, c0) for r in range(r0 + 1, r1)]
                        + [(r, c1) for r in range(r0 + 1, r1)]
                    )
                    colors = {grid[r][c] for r, c in border}
                    if len(colors) == 1 and next(iter(colors)) in (6, 7):
                        interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
                        if all(grid[r][c] != next(iter(colors)) for r, c in interior):
                            frames.append((r0, c0, r1, c1, interior))
    # Keep maximal rectangles only, so sub-rectangles of a frame are ignored.
    maximal = []
    for fr in frames:
        r0, c0, r1, c1, _ = fr
        if not any(or0 <= r0 and oc0 <= c0 and or1 >= r1 and oc1 >= c1 and (or0, oc0, or1, oc1) != (r0, c0, r1, c1)
                   for or0, oc0, or1, oc1, _ in frames):
            maximal.append(fr)
    if len(maximal) != 2:
        errors.append(f"expected exactly two hollow frames, found {len(maximal)}")
    else:
        dims = {(r1 - r0 - 1, c1 - c0 - 1) for r0, c0, r1, c1, _ in maximal}
        if len(dims) != 1:
            errors.append(f"frame interiors must have equal dims, found {sorted(dims)}")
        motif_counts = [sum(1 for r, c in interior if grid[r][c] in _MOTIF_COLORS)
                        for *_, interior in maximal]
        if sorted(x > 0 for x in motif_counts) != [False, True]:
            errors.append(f"expected exactly one patterned frame, motif counts={motif_counts}")
    key_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2, 3)]
    if len(key_cells) > 1:
        errors.append(f"expected at most 1 key cell, found {len(key_cells)}")
    return errors


def _draw_from_degenerate(name, ctx):
    """conflicting_keys — two different key cells; the rule silently
    uses the first in scan order. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    g = generate(seed=ctx.seed if hasattr(ctx, "seed") else 1,
                 sample_index=rng.randint(0, 10**6), texture="plain")
    h, w = len(g), len(g[0])
    keys = rng.sample([1, 2, 3], 2)
    # grid-border cells can never be inside a frame's interior, so the
    # extra key stays rule-safe there
    border = ([(0, c) for c in range(w)] + [(h - 1, c) for c in range(w)]
              + [(r, 0) for r in range(1, h - 1)] + [(r, w - 1) for r in range(1, h - 1)])
    rng.shuffle(border)
    for kr, kc in border:
        if all(g[rr][cc] == 0
               for rr in range(max(0, kr - 1), min(h, kr + 2))
               for cc in range(max(0, kc - 1), min(w, kc + 2))):
            g[kr][kc] = keys[1]
            break
    return g
