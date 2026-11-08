"""Generator for arc_puzzle_bank_21_set23_s:S23_H7.

Rule: 4 scrambled edge-coded tiles; rotate/permute to match by edge-center
connector colors; output the assembled lattice (lex-min valid orientation).

Combinatorial axes: connector + center colors (drive the output), tile
permutation, per-tile rotation.
Degenerates: no_separators, no_tiles, edges_unmatched.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "36ab914e50de"
RULE_HASH = "754c25582aff"  # canonical rule this generator was written against
VERSION = "2.1.0"  # +self_check  # diversity: random connector/center colors + random scramble (was 4 fixed tiles, 6 scrambles)
TASK_ID = "36ab914e50de"
SUMMARY = (
    "A 2x2 lattice of 3x3 tiles separated by color-9 dividers (7x7). "
    "Each tile carries EDGE-CENTER CONNECTOR colors on its inward-facing "
    "edges and a CENTER color; the solved lattice matches connectors "
    "across every internal seam (4 distinct connector colors, 4 distinct "
    "centers, all 8 colors random). The four tiles are then SCRAMBLED — "
    "permuted into the 4 slots and each randomly rotated. Rule: search "
    "permutations x rotations for the 2x2 arrangement whose touching "
    "edge-centers all match, and output that assembled lattice (lex-min "
    "valid orientation). The colors drive the OUTPUT and the scramble "
    "drives the INPUT, so both vary freely (was 4 fixed tiles with 6 "
    "hardcoded scrambles)."
)

INVARIANTS = [
    "the input is a 2x2 lattice of 3x3 tiles separated by color-9 dividers",
    "four tiles have matching edge-center connector colors under one 2x2 arrangement",
    "tiles may be permuted and rotated in the input",
    "the output is the valid assembled lattice chosen by the solver's deterministic tie-break",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "no_tiles", "edges_unmatched")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "scramble":       {"type": "int", "default": "rng (perm + rotations)", "valid": "0..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8..8"},
    "position_bias":  {"type": "str", "default": "2x2_tile_lattice",
                       "valid": "2x2_tile_lattice"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_separators|no_tiles|edges_unmatched"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 7x7 grid with color-9 dividers at rows/cols 3."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    if h != 7 or w != 7:
        errs.append(f"expected 7x7 grid (2x2 tiles + dividers), got {h}x{w}")
    else:
        if not all(grid[3][c] == 9 for c in range(7)):
            errs.append("row 3 is not all color-9 (horizontal divider missing)")
        if not all(grid[r][3] == 9 for r in range(7)):
            errs.append("col 3 is not all color-9 (vertical divider missing)")
    return errs


def _make_tile(top, left, right, bottom, center):
    """3x3 tile: edge-center connectors + center; corners stay 0."""
    return [[0, top, 0], [left, center, right], [0, bottom, 0]]


def _turn(tile):
    h = len(tile)
    return [[tile[h - 1 - r][c] for r in range(h)] for c in range(h)]


def _rot(tile, k):
    out = [row[:] for row in tile]
    for _ in range(k % 4):
        out = _turn(out)
    return out


def _paste_tile(g, tile, tile_index):
    top = (tile_index // 2) * 4
    left = (tile_index % 2) * 4
    for r in range(3):
        for c in range(3):
            g[top + r][left + c] = tile[r][c]


def _solved_tiles(a, b, c, d, centers):
    """Four tiles in solved positions TL,TR,BL,BR with connectors:
    A = top horizontal seam, B = bottom horizontal seam,
    C = left vertical seam, D = right vertical seam."""
    cTL, cTR, cBL, cBR = centers
    return [
        _make_tile(0, 0, a, c, cTL),   # TL: right=A, bottom=C
        _make_tile(0, a, 0, d, cTR),   # TR: left=A,  bottom=D
        _make_tile(c, 0, b, 0, cBL),   # BL: top=C,   right=B
        _make_tile(d, b, 0, 0, cBR),   # BR: top=D,   left=B
    ]


def _blank_lattice():
    g = full_grid(7, 7, 9)
    for r in (0, 1, 2, 4, 5, 6):
        for c in (0, 1, 2, 4, 5, 6):
            g[r][c] = 0
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    # 8 distinct colors: 4 connectors + 4 centers (all of 1..8). Distinct
    # connectors make the matching rigid → a well-posed assembly.
    cols = rng.sample(range(1, 9), 8)
    a, b, c, d = cols[:4]
    centers = cols[4:]
    tiles = _solved_tiles(a, b, c, d, centers)

    # Scramble: permute tiles into the 4 slots + rotate each. Difficulty sets
    # how aggressively (easy: at most quarter-turns; hard: derangement).
    if difficulty == "easy":
        rot_choices = [0, 1]
        perm = list(range(4)); rng.shuffle(perm)
    elif difficulty == "hard":
        rot_choices = [0, 1, 2, 3]
        perm = list(range(4))
        for _ in range(40):
            rng.shuffle(perm)
            if all(perm[i] != i for i in range(4)):   # derangement
                break
    else:
        rot_choices = [0, 1, 2, 3]
        perm = list(range(4)); rng.shuffle(perm)

    g = _blank_lattice()
    for slot in range(4):
        k = rng.choice(rot_choices)
        _paste_tile(g, _rot(tiles[perm[slot]], k), slot)
    return g


def _draw_from_degenerate(name, rng):
    tiles = _solved_tiles(6, 1, 8, 7, (2, 3, 4, 5))
    if name == "no_separators":
        # No 9-dividers — the tile-lattice precondition fails.
        h2 = full_grid(7, 7, 0)
        for slot in range(4):
            _paste_tile(h2, tiles[slot], slot)
        return h2
    if name == "no_tiles":
        # Separators but no tile content — no edge codes to match.
        return _blank_lattice()
    if name == "edges_unmatched":
        # Corrupt one connector so no global match exists.
        g = _blank_lattice()
        for slot in range(4):
            _paste_tile(g, tiles[slot], slot)
        g[1][2] = 9; g[1][4] = 9
        return g
    return _blank_lattice()
