"""Generator for 21b:hard_146 — select object by border-touch signature, scale 2x.

Rule: top row holds codes in {1, 2, 3, 4} = {top, right, bottom, left}.
Of the body components (rows 1+), find one whose bbox touches exactly
the borders named (1=row 1 top edge, 2=last col, 3=last row, 4=col 0).
Scale 2x.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_codes (row 0 empty → rule has no signature);
no_objects (codes but no body components → selector has no
candidates); no_match (codes specify a signature no body component
satisfies → selector returns nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "23e6fb027242"
VERSION = "2.3.0"  # the random-walk target could still close into a solid rectangle -> scaled output a single-color block (all_background_output). Require a bbox hole so every target shows real shape. Adds self_check.
TASK_ID = "23e6fb027242"

SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) with: (a) ROW 0 contains "
    "1-2 distinct CODE cells in {1, 2, 3, 4} at random "
    "columns — encoding a border SIGNATURE (1=top edge, "
    "2=right edge, 3=bottom edge, 4=left edge); (b) ROWS "
    "1+ contain 2-3 BODY rectangular components in "
    "distinct colors, exactly ONE of which has a bbox "
    "that touches PRECISELY the set of borders named in "
    "the code. Rule: read codes (sorted set). Find the "
    "body component whose border-touch signature matches "
    "the code set exactly. Crop it to its bbox and "
    "UPSCALE by 2× (each cell → 2×2 block). Output: that "
    "2× scaled crop."
)

INVARIANTS = [
    "background is 0",
    "row 0 holds 1-2 distinct codes in {1, 2, 3, 4} (border-touch signature)",
    "body (rows 1+) holds 2-3 components; exactly one's bbox touches the named borders",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_codes", "no_objects", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":            {"type": "int", "default": "rng 9..11", "valid": "8..15"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "row0_codes_with_target_at_border",
                          "valid": "row0_codes_with_target_at_border"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_codes|no_objects|no_match"},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, k):
    # random-walk polyomino, normalised so min-row = min-col = 0 (bbox touches all
    # four of its own edges). The selected target is cropped + scaled 2x; making it
    # a polyomino instead of a solid rectangle makes the output vary by SHAPE.
    # A normalised poly whose bbox is COMPLETELY filled would scale to a single
    # solid block (all_background_output), so retry until it has >=1 bbox hole.
    for _ in range(200):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice(_CARD)
            nb = (r + dr, c + dc)
            if nb not in seen:
                cells.append(nb); seen.add(nb)
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        bh = max(r for r, _ in norm) + 1; bw = max(c for _, c in norm) + 1
        if bh * bw > k:  # non-rectangular → has a hole
            return norm
    return norm


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row 0 codes name a border signature; exactly one body component's bbox must
    match it, and that target must be non-rectangular so the 2x-scaled crop is not
    a solid single-color block (all_background_output)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    codes = sorted({grid[0][c] for c in range(w) if grid[0][c] in (1, 2, 3, 4)})
    errors = []
    if not (1 <= len(codes) <= 2):
        errors.append(f"row 0 must hold 1-2 distinct codes, got {codes}")
    # body components (rows 1+), 4-connected by color
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(1, h):
        for sc in range(w):
            if grid[sr][sc] == 0 or seen[sr][sc]:
                continue
            col = grid[sr][sc]; stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == col:
                        seen[nr][nc] = True; stack.append((nr, nc))
            comps.append(cells)

    def sig(cells):
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        s = []
        if min(rs) == 1: s.append(1)
        if max(cs) == w - 1: s.append(2)
        if max(rs) == h - 1: s.append(3)
        if min(cs) == 0: s.append(4)
        return sorted(s)

    matches = [cells for cells in comps if sig(cells) == codes]
    if len(matches) != 1:
        errors.append(f"expected exactly 1 body component matching signature {codes}, "
                      f"found {len(matches)}")
        return errors
    cells = matches[0]
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    bh = max(rs) - min(rs) + 1; bw = max(cs) - min(cs) + 1
    if bh * bw == len(cells):
        errors.append("target component is a solid rectangle — scaled output would "
                      "be a single-color block")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 15)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    # A 2-4 sized rectangle in an 8-10 grid can't touch two OPPOSITE borders, so
    # signatures {1,3} (top+bottom) and {2,4} (left+right) are unrealizable — the
    # target loop would exhaust its retries and raise (~17%). Resample those out.
    n_codes = rng.randint(1, 2)
    code_set = sorted(rng.sample([1, 2, 3, 4], n_codes))
    while code_set in ([1, 3], [2, 4]):
        code_set = sorted(rng.sample([1, 2, 3, 4], n_codes))
    g = full_grid(h, w, 0)  # codes go in LAST (see end of the retry loop)

    def touches_signature(r1, c1, r2, c2):
        sig = []
        if r1 == 1: sig.append(1)
        if c2 == w - 1: sig.append(2)
        if r2 == h - 1: sig.append(3)
        if c1 == 0: sig.append(4)
        return sorted(sig)
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    if difficulty == "hard":
        tk = (6, 10)
    elif difficulty == "easy":
        tk = (4, 6)
    else:
        tk = (4, 8)
    for outer in range(40):
        gg = [row[:] for row in g]
        # TARGET = a random connected polyomino (was a solid rectangle -> dup 44%).
        # Its BBOX must touch exactly the coded borders; a normalised polyomino always
        # has a cell on each bbox edge, so positioning the bbox is enough. The rule
        # crops the actual cells (0 elsewhere) and scales 2x, so the output now varies
        # by SHAPE, not just bbox-size + colour.
        poly = _rand_poly(rng, rng.randint(*tk))
        sh = max(r for r, _ in poly) + 1; sw = max(c for _, c in poly) + 1
        if sh > h - 2 or sw > w - 2: continue
        r1_options = [1] if 1 in code_set else list(range(1, h - sh))
        c1_options = [0] if 4 in code_set else list(range(1, w - sw))
        if 3 in code_set:
            r1_options = [h - sh]
        if 2 in code_set:
            c1_options = [w - sw]
        if not r1_options or not c1_options: continue
        r0 = rng.choice(r1_options); c0 = rng.choice(c1_options)
        r2_target, c2_target = r0 + sh - 1, c0 + sw - 1
        if touches_signature(r0, c0, r2_target, c2_target) != code_set:
            continue
        if not _free(gg, r0, c0, r2_target, c2_target): continue
        for r, c in poly:
            gg[r0 + r][c0 + c] = palette[0]
        n_others = rng.randint(1, 2)
        ok = True
        for color in palette[1:1 + n_others]:
            placed = False
            for _ in range(60):
                osh = rng.randint(2, 3); osw = rng.randint(2, 3)
                or0 = rng.randint(2, h - osh - 2)
                oc0 = rng.randint(2, w - osw - 2)
                if or0 < 2 or oc0 < 2: continue
                or2 = or0 + osh - 1; oc2 = oc0 + osw - 1
                if touches_signature(or0, oc0, or2, oc2): continue
                if not _free(gg, or0, oc0, or2, oc2): continue
                for r in range(or0, or2 + 1):
                    for c in range(oc0, oc2 + 1):
                        gg[r][c] = color
                placed = True; break
            if not placed: ok = False; break
        if not ok:
            continue
        # Codes go in row 0 LAST, in columns clear of any top-edge body cell
        # (the target when it touches row 1) and its 1-cell horizontal ring —
        # so codes never abut/merge with the target and the target's border
        # ring stays clean. Placing codes first (fixed cols) made every retry
        # fail whenever a code happened to sit above a top-touching target.
        forbidden = set()
        for c in range(w):
            if gg[1][c] != 0:
                forbidden.update((c - 1, c, c + 1))
        avail = [c for c in range(w) if c not in forbidden]
        if len(avail) < len(code_set):
            continue
        for c, code in zip(rng.sample(avail, len(code_set)), code_set):
            gg[0][c] = code
        return gg
    raise ValueError("could not lay out target with border signature")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_codes":
        # Row 0 empty — rule has no signature.
        for r in range(2):
            for c in range(2):
                g[3 + r][3 + c] = 4
        for r in range(2):
            for c in range(2):
                g[6 + r][7 + c] = 5
        return g
    if name == "no_objects":
        # Codes but no body components.
        g[0][2] = 1; g[0][6] = 4
        return g
    if name == "no_match":
        # Codes specify "left+right" but no component touches both.
        g[0][2] = 4; g[0][6] = 2
        # Object touches neither left nor right.
        for r in range(2):
            for c in range(2):
                g[3 + r][3 + c] = 4
        for r in range(2):
            for c in range(2):
                g[6 + r][5 + c] = 5
        return g
    return g
