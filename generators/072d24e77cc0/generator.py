"""Generator for v2_meta_puzzles:H7 — row-0 count + recolor matching size.

Rule: row 0 has 1-3 color-1 markers; the count = target-size. Each color-3
component of that exact size is recolored to 8.

Combinatorial axes: grid_h, grid_w, n_markers, texture
(plain|multi_match|body_one|other_color).
Degenerates: no_markers (identity), no_matching_motif (only the row-0
erasure happens).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "072d24e77cc0"
VERSION = "3.1.1"  # fail-closed with more layout retries for helpful body_one/other_color witnesses
TASK_ID = "072d24e77cc0"

SUMMARY = (
    "Row 0 holds N color-1 count markers; the rule ERASES them (row-0 "
    "1s are set to 0 in the output) and recolors EVERY color-3 "
    "component of size exactly N to 8. Multiple matches all recolor; "
    "1-cells below row 0 are neither counted nor erased; non-3 blobs "
    "are ignored. (Old doc claimed the markers stay - wrong - and the "
    "generator never showed multi-match, body 1s, or other-color "
    "decoys.)"
)

# Rivals: 'markers stay' refuted by every demo (row 0 cleared).
# 'recolor THE matching motif' refuted by multi_match (two motifs of
# size N both turn 8). 'count all 1s anywhere' refuted by body_one
# boards. 'any blob of size N recolors' refuted by other_color blobs
# that stay. 3 demos incl. >=1 multi_match or body_one.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1-5 color-1 markers on row 0 at distinct columns (main path)",
    "exactly one motif of size N unless texture=multi_match (then two)",
    "motifs sit in rows >= 2 and never touch each other",
]

DEGENERATE_TEXTURES = ("no_markers", "no_matching_motif")
HELPFUL_TEXTURES = ("plain", "multi_match", "body_one", "other_color")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "grid_w":    {"type": "int", "default": "rng 9..12", "valid": "7..14"},
    "n_markers": {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|multi_match|body_one|other_color|"
                           "no_markers|no_matching_motif",
                  "doc": "multi_match: two size-N motifs both recolor; "
                         "body_one: a 1-cell below row 0 (ignored by the "
                         "count AND kept); other_color: size-N blob in a "
                         "non-3 color that stays."},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _place_motif(g, rng, size, color, r_lo=2):
    h, w = len(g), len(g[0])
    for _ in range(120):
        cells = _build_motif(rng, size)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1
        sw = max(cs) - min(cs) + 1
        if r_lo + sh > h or sw > w:
            continue
        r0 = rng.randint(r_lo, h - sh)
        c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for r, c in cells:
            g[r0 + r - min(rs)][c0 + c - min(cs)] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "multi_match", "body_one",
                        "other_color"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n_markers = ctx.draw_int("n_markers", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
        n_markers = ctx.draw_int("n_markers", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n_markers = ctx.draw_int("n_markers", 2, 5)
    rng = ctx.draw_rng("layout")

    for _outer in range(240):
        g = full_grid(h, w, 0)
        cols = rng.sample(range(w), n_markers)
        for c in cols:
            g[0][c] = 1
        # decoy sizes around N, never equal to N
        lo = max(2, n_markers - 1)
        decoys = [s for s in (lo, n_markers + 1, n_markers + 2) if s != n_markers]
        rng.shuffle(decoys)
        sizes = [n_markers] + decoys[:2]
        if texture == "multi_match":
            sizes = [n_markers, n_markers, n_markers + 1]
        rng.shuffle(sizes)
        ok = all(_place_motif(g, rng, s, 3) for s in sizes)
        if not ok:
            continue
        if texture == "body_one":
            # a 1-cell BELOW row 0: not counted, not erased, stays.  If the
            # witness cannot be placed, resample instead of silently degrading to
            # a plain case.
            placed_body_one = False
            for _ in range(60):
                r = rng.randint(2, h - 1)
                c = rng.randint(0, w - 1)
                if _free(g, r, c, r, c):
                    g[r][c] = 1
                    placed_body_one = True
                    break
            if not placed_body_one:
                continue
        elif texture == "other_color":
            # a size-N blob in a non-3 color: the rule ignores it.  Keep the
            # branch honest by requiring the decoy to actually exist.
            if not _place_motif(g, rng, n_markers,
                                rng.choice([2, 4, 5, 6, 7, 9])):
                continue
        return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_markers        — empty row 0: count 0, nothing matches, identity.
    no_matching_motif — N markers but no size-N motif: the only change
                        is row 0 being ERASED.
    (all_same_size was promoted into the multi_match texture.)
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    if name == "no_markers":
        for s in rng.sample([2, 3, 4, 5], 2):
            _place_motif(g, rng, s, 3)
        return g
    # no_matching_motif
    n = rng.randint(3, 5)
    for c in rng.sample(range(w), n):
        g[0][c] = 1
    for s in (n - 1, n + 1):
        _place_motif(g, rng, s, 3)
    return g

def _components(grid, *, colors=None):
    h, w = len(grid), len(grid[0])
    color_set = set(colors) if colors is not None else None
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            if color_set is not None and grid[r][c] not in color_set:
                continue
            color = grid[r][c]
            q = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in q:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color
                            and (color_set is None or grid[nr][nc] in color_set)):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    n = sum(1 for v in grid[0] if v == 1)
    if n < 1:
        errs.append("row 0 must contain at least one count marker")
    if any(v == 1 for row in grid[1:] for v in row):
        # Body 1s are a helpful texture, but they must not touch color-3 motifs.
        pass
    c3 = _components(grid, colors={3})
    matches = [cells for _, cells in c3 if len(cells) == n]
    if len(matches) < 1:
        errs.append("expected at least one color-3 motif whose size matches the row-0 count")
    all_cells = {cell: i for i, (_, cells) in enumerate(_components(grid)) for cell in cells}
    for (r, c), i in all_cells.items():
        if r < 2 and grid[r][c] == 3:
            errs.append("motifs must sit in rows >= 2")
            break
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                j = all_cells.get((r + dr, c + dc))
                if j is not None and j != i:
                    errs.append("motifs/decoys touch; component sizes become ambiguous")
                    return errs
    return errs
