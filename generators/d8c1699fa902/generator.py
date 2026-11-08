"""Generator for arc_puzzle_bank_21_set23_bundle:medium_p04 — ranked-component transform.

Rule: (0, 0) holds rank-key (1-indexed by size asc); (0, w-1) holds tf-key
(4=identity, 5=rotate-cw, 6=flip-lr, else=rotate-180). Sort body components by
size asc; pick the rank-key-th; apply the transform to its crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes (≥2 components share size → "rank-key-th by
size asc" is ambiguous, tie-break decides), no_rank (cell (0,0) is bg →
rule's rank selector returns nothing, no component chosen),
identity_transform (tf-key = 4 → rule's transform is identity, output
equals cropped target with no transformation).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d8c1699fa902"
VERSION = "3.0.0"  # WRONG-DOCSTRING/discriminator bug: docstring claimed rank-key/tf-key/transform but the canonical rule just counts color-2 cells in ROW 0 (=k) -> outputs the k-th component by column, cropped (no transform). Old gen placed a single rank_key so k~0/1, selection barely varied (distinct 38). Now place k color-2 cells in row 0 + n components in column bands. Raise -> graceful fallback.
TASK_ID = "d8c1699fa902"

SUMMARY = (
    "0-bg grid (h~9-11, w~"
    "12-14) with: (a) "
    "RANK-KEY at (0, 0) — "
    "a color encoding "
    "rank ∈ {1, 2, 3} "
    "(1-indexed size rank "
    "ascending); (b) "
    "TF-KEY at (0, w-1) — "
    "a color encoding "
    "transform ∈ {4, 5, 6, "
    "7}: 4=IDENTITY, "
    "5=ROTATE CW, "
    "6=FLIP LR, "
    "else=ROTATE 180; "
    "(c) BODY (rows ≥1) — "
    "3 CONNECTED "
    "COMPONENTS in DISTINCT "
    "SIZES (2..6) drawn "
    "from a shape bank "
    "in 3 distinct BODY "
    "COLORS (excluding "
    "rank-key and tf-key "
    "colors). Components "
    "are non-touching with "
    "1-cell padding. Rule "
    "(SORT BODY COMPONENTS "
    "BY SIZE ASC, PICK "
    "RANK-KEY-TH, APPLY "
    "TF-KEY TRANSFORM): "
    "identify the 2 corner "
    "key cells. SORT all "
    "body components by "
    "CELL COUNT ASC. PICK "
    "the rank-key-th "
    "(1-indexed). CROP "
    "that component to "
    "its BBOX. APPLY the "
    "TF-KEY transform "
    "(identity / cw90 / "
    "flip-lr / rot180) to "
    "the crop. OUTPUT is "
    "the transformed crop. "
    "Net: rank-key selects "
    "which size-ranked "
    "blob to pull, tf-key "
    "selects how to "
    "rotate/flip it."
)

INVARIANTS = [
    "background is 0",
    "row 0 holds exactly k color-2 cells (k = which component to select, 1..N)",
    "N components live in distinct column bands (rows >= 1), none coloured 2",
    "output = the k-th component (by column) cropped to its bbox",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "no_rank", "identity_transform")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "n_components":      {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":      {"type": "int", "default": "= n_components", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "row0_2count_plus_column_bands",
                          "valid": "row0_2count_plus_column_bands"},
    "n_distinct_colors": {"type": "int", "default": "= n_components", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES_BY_SIZE = {
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (0, 1), (0, 2)], [(0, 0), (0, 1), (1, 0)]],
    4: [[(0, 0), (0, 1), (0, 2), (1, 1)], [(0, 0), (0, 1), (1, 0), (1, 1)]],
    5: [[(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)], [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)]],
    6: [[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]],
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # The rule counts color-2 cells in ROW 0 -> k, removes them, then outputs the
    # k-th component (sorted by column) cropped. The old gen put a single rank_key
    # at (0,0) so k was almost always 0/1 -> selection barely varied (distinct 38).
    # Build it correctly: place k color-2 cells in row 0 + n components in column bands.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_components", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 15, 18)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_components", 3, 4)
    rng = ctx.draw_rng("layout")
    k = rng.randint(1, n)                       # which component (by column) to select
    band_w = w // n
    colors = rng.sample([c for c in [1, 3, 4, 5, 6, 7, 8, 9]], n)   # never color 2
    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for j in range(n):                     # one component per column band -> distinct obj-c1
            sz = rng.choice([2, 3, 4, 5, 6])
            shape = rng.choice(_SHAPES_BY_SIZE[sz])
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            lo = j * band_w; hi = min(w - sw, (j + 1) * band_w - sw)
            if hi < lo:
                hi = lo
            placed = False
            for _ in range(80):
                r0 = rng.randint(1, h - sh); c0 = rng.randint(lo, max(lo, hi))
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = colors[j]
                placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue
        # place exactly k color-2 cells in row 0 (distinct columns) -> drives selection
        for c in rng.sample(range(w), k):
            g[0][c] = 2
        return g
    return g   # graceful fallback (last attempt); never raise


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # Two components share size — rank-by-size-asc is ambiguous.
        g[0][0] = 2
        g[0][w - 1] = 5
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][1 + dc] = 7
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][6 + dc] = 8   # tied with prev
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]:
            g[7 + dr][3 + dc] = 9
        return g
    if name == "no_rank":
        # (0,0) is bg — rule's rank selector returns nothing.
        g[0][w - 1] = 5
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][1 + dc] = 7
        for dr, dc in [(0, 0), (1, 0), (2, 0)]:
            g[5 + dr][5 + dc] = 8
        return g
    if name == "identity_transform":
        # tf-key = 4 (identity) — rule's transform is identity;
        # output equals cropped target.
        g[0][0] = 1
        g[0][w - 1] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][2 + dc] = 7
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[6 + dr][6 + dc] = 8
        return g
    return g
