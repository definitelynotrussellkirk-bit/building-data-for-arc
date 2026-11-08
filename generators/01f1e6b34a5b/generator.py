"""Generator for arc_additional_puzzles_21_set9:M60 — Code-driven motif transforms.

Rule: top row has 2-4 codes from {1,2,3,4} indicating transforms (none,
rotate-cw, rotate-180, flip-ud) applied to motif (rows 1+ cropped).
Output: side-by-side transformed motifs separated by 0-cols.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_codes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_codes, no_motif, code_out_of_range.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "01f1e6b34a5b"
VERSION = "2.1.1"
TASK_ID = "01f1e6b34a5b"
SUMMARY = (
    "0-bg grid (h~4-7, w~3-6) with: (a) TOP ROW "
    "(row 0): 2-4 TRANSFORM CODE CELLS at random "
    "distinct columns, each painted with a value "
    "from {1, 2, 3, 4} encoding (1=identity, 2="
    "rotate-CW 90°, 3=rotate 180°, 4=flip-UD). "
    "Other top-row cells are 0; (b) ROWS 1..h-1: "
    "MOTIF with 3-N scattered non-0 cells (where "
    "N is roughly (h-1)*w//2) — usually red, "
    "sometimes another color or 2-color mixed, "
    "at random distinct positions. "
    "The motif is asymmetric so each "
    "transform produces a distinct output. Rule "
    "(APPLY EACH CODE'S TRANSFORM TO THE MOTIF, "
    "OUTPUT SIDE-BY-SIDE): extract the MOTIF "
    "(non-0 cells in rows 1..h-1, all color 2), "
    "CROP to its bbox. read the TOP-ROW CODES in "
    "left-to-right column order. For EACH code C: "
    "APPLY the corresponding TRANSFORM to the "
    "cropped motif: 1=identity (no change), 2=rot-"
    "CW 90°, 3=rot 180°, 4=flip-UD. PRODUCE an "
    "OUTPUT where the transformed motifs are "
    "STACKED LEFT-TO-RIGHT in the order their "
    "codes appeared on the top row, separated by "
    "single bg-0 columns. Net: each transform "
    "code spawns one transformed copy of the "
    "motif in the output gallery."
)

# Rivals: 'apply only first code' refuted by multi-code demos.
# 'everything is red' refuted by multicolor/other-color motifs.
# 'row-0 values 5-9 are codes too' refuted by decoy demos where they
# spawn no panel. 'codes sorted by value' refuted by order-dependent
# galleries. 4 demos covering codes {1,2,3,4} + >=1 decoy/multicolor.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "row 0: 2-4 cells with values in {1,2,3,4} (codes), optional decoys 5-9",
    "rows 1+: motif with >=3 non-zero cells (color varies; may be multicolor)",
    "motif is asymmetric under cw/180/flip-ud (enforced, was only claimed)",
    ">=1 valid code always present (an empty code list crashes the rule)",
]

DEGENERATE_TEXTURES = ("single_code", "symmetric_motif")
HELPFUL_TEXTURES = ("red", "other_color", "multicolor", "decoy_row0")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 5..6 (easy 4..5, hard 6..8)",
                "valid": "3..8", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 4..5 (easy 3..4, hard 5..6)",
                "valid": "3..6", "doc": "Grid width."},
    "n_codes": {"type": "int", "default": "rng 2..4 (capped at w)",
                "valid": "1..4", "doc": "Transform codes in row 0."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "red|other_color|multicolor|decoy_row0|"
                         "single_code|symmetric_motif",
                "doc": "Motif palette flavor or a degenerate name."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has >=2 codes from {1,2,3,4}; rows 1+ have >=3 non-zero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    codes = [grid[0][c] for c in range(w) if grid[0][c] in (1, 2, 3, 4)]
    if len(codes) < 2:
        errs.append(f"row 0 has {len(codes)} valid code(s) in {{1..4}}; need >=2")
    motif_nz = sum(1 for r in range(1, h) for c in range(w) if grid[r][c] != 0)
    if motif_nz < 3:
        errs.append(f"motif (rows 1+) has {motif_nz} cells; need >=3")
    return errs


def _motif_variants(cells):
    """Normalized cell-color sets for identity/cw/180/flip-ud."""
    def norm(cs):
        mr = min(r for r, _, _ in cs)
        mc = min(c for _, c, _ in cs)
        return sorted((r - mr, c - mc, v) for r, c, v in cs)
    base = norm(cells)
    mh = max(r for r, _, _ in base) + 1
    mw = max(c for _, c, _ in base) + 1
    cw = norm([(c, mh - 1 - r, v) for r, c, v in base])
    r180 = norm([(mh - 1 - r, mw - 1 - c, v) for r, c, v in base])
    ud = norm([(mh - 1 - r, c, v) for r, c, v in base])
    return base, (cw, r180, ud)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("red", "red", "other_color", "multicolor", "decoy_row0"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 4, 5)
    rng = ctx.draw_rng("layout")

    if texture == "multicolor":
        palette = rng.sample(range(1, 10), 2)
    elif texture == "other_color":
        palette = [rng.choice([1, 3, 4, 5, 6, 7, 8, 9])]
    else:
        palette = [2]

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        n_codes = rng.randint(2, min(4, w))
        code_cols = rng.sample(range(w), n_codes)
        for c in code_cols:
            g[0][c] = rng.choice([1, 2, 3, 4])
        if texture == "decoy_row0":
            # row-0 values outside {1..4} are IGNORED by the rule —
            # they spawn no panel in the gallery
            free = [c for c in range(w) if g[0][c] == 0]
            for c in rng.sample(free, min(len(free), rng.randint(1, 2))):
                g[0][c] = rng.choice([5, 6, 7, 8, 9])
        n_motif = rng.randint(3, max(3, (h - 1) * w // 2))
        cells = []
        for _ in range(60):
            if len(cells) >= n_motif:
                break
            r = rng.randint(1, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0 and not any(rr == r and cc == c for rr, cc, _ in cells):
                v = rng.choice(palette)
                cells.append((r, c, v))
        if len(cells) < 3:
            continue
        base, variants = _motif_variants(cells)
        if base in variants:
            continue  # symmetric: panels would be indistinguishable
        for r, c, v in cells:
            g[r][c] = v
        return g
    raise ValueError("could not realize asymmetric motif")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (>=1 code, motif exists).

    single_code     — one panel only: multi-panel structure hidden.
    symmetric_motif — 2x2 block: all transforms look identical.
    """
    h = ctx.draw_int("grid_h", 4, 6)
    w = ctx.draw_int("grid_w", 4, 5)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "single_code":
        g[0][rng.randrange(w)] = rng.choice([1, 2, 3, 4])
        for _ in range(4):
            g[rng.randint(1, h - 1)][rng.randrange(w)] = 2
        return g
    # symmetric_motif: 2x2 solid block + 2 codes
    for c in rng.sample(range(w), 2):
        g[0][c] = rng.choice([1, 2, 3, 4])
    r0 = rng.randint(1, h - 2)
    c0 = rng.randint(0, w - 2)
    color = rng.choice([2, 3, 5, 6])
    for dr in range(2):
        for dc in range(2):
            g[r0 + dr][c0 + dc] = color
    return g
