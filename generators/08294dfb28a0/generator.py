"""Generator for arc_puzzle_bank_21_set24_bundle:hard_p01 — pack transformed base.

Rule: row 0 holds 1-4 transform codes; rows 2..h-1 hold a base motif.
For each code, transform a crop of the base; pack the transformed pieces
left-to-right with one blank column between them.

Combinatorial axes: grid_h, grid_w, n_codes, texture
(plain|multi_motif|body_code).
Degenerates: no_codes, no_motif (both output [[0]]).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08294dfb28a0"
VERSION = "3.0.1"
TASK_ID = "08294dfb28a0"

SUMMARY = (
    "Row-0 codes (1=identity, 2=rot-cw, 3=flip-lr, 4=rot-180, "
    "duplicates allowed) drive a left-to-right gallery of transformed "
    "copies of the LARGEST non-{1-4}-colored motif (colors 5-9). "
    "Templates are asymmetric so every code is visually distinct; "
    "multi_motif boards add a smaller ignored motif; body_code boards "
    "drop a 1-4 cell into the body (neither key nor template)."
)

INVARIANTS = [
    "background is 0; row 1 stays empty so the motif never touches the code row",
    "row 0 has 1-4 codes in {1..4} at distinct columns",
    "the template's 4 code-transforms are pairwise distinct",
    "any second motif is STRICTLY smaller than the template",
]

# Rivals: 'codes do nothing' refuted by asymmetric templates whose 4
# transforms are pairwise distinct. 'use every motif' refuted by
# multi_motif (the smaller one is ignored - largest wins). 'codes can
# appear anywhere' refuted by body_code boards (a 1-4 cell in the body
# is neither key nor template). 'one use per code' refuted by repeated
# codes in row 0. 4 demos.
EXAMPLES_NEEDED = 4

DEGENERATE_TEXTURES = ("no_codes", "no_motif")
HELPFUL_TEXTURES = ("plain", "multi_motif", "body_code")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":  {"type": "int", "default": "rng 11..15", "valid": "10..18"},
    "n_codes": {"type": "int", "default": "rng 2..4", "valid": "1..4",
                "doc": "Row-0 codes 1-4 (duplicates allowed)."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|multi_motif|body_code|no_codes|no_motif",
                "doc": "multi_motif: a smaller second motif the rule "
                       "ignores; body_code: a 1-4 colored cell in the body "
                       "(neither key nor template)."},
}

_MOTIF_COLORS = (5, 6, 7, 8, 9)


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _t(grid, key):
    if key == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if key == 3:
        return [row[::-1] for row in grid]
    if key == 4:
        return [row[::-1] for row in grid[::-1]]
    return grid


def _asym(rng):
    """Template whose 4 code-transforms are pairwise distinct."""
    for _ in range(300):
        s = _grow(rng, rng.randint(4, 6))
        sh = max(r for r, _ in s) + 1
        sw = max(c for _, c in s) + 1
        grid = [[0] * sw for _ in range(sh)]
        for r, c in s:
            grid[r][c] = 1
        if len({tuple(map(tuple, _t(grid, k))) for k in (1, 2, 3, 4)}) == 4:
            return s
    return [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "multi_motif", "body_code"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        n_codes = ctx.draw_int("n_codes", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 13, 15)
        n_codes = ctx.draw_int("n_codes", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 11, 15)
        n_codes = ctx.draw_int("n_codes", 2, 4)
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        g = full_grid(h, w, 0)
        cols = sorted(rng.sample(range(w), n_codes))
        for c in cols:
            g[0][c] = rng.randint(1, 4)

        motif_color = rng.choice(_MOTIF_COLORS)
        shape = _asym(rng)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h - 2 or sw > w:
            continue
        r0 = rng.randint(2, h - sh)
        c0 = rng.randint(0, w - sw)
        for r, c in shape:
            g[r0 + r][c0 + c] = motif_color
        taken = {(r0 + r, c0 + c) for r, c in shape}
        taken |= {(r + dr, c + dc) for r, c in taken
                  for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

        if texture == "multi_motif":
            # STRICTLY smaller second motif: the largest-template
            # selection ignores it
            small = _grow(rng, rng.randint(2, len(shape) - 1))
            bh = max(r for r, _ in small) + 1
            bw = max(c for _, c in small) + 1
            color2 = rng.choice([v for v in _MOTIF_COLORS if v != motif_color])
            for _try in range(80):
                br = rng.randint(2, h - bh)
                bc = rng.randint(0, w - bw)
                spots = {(br + r, bc + c) for r, c in small}
                if spots & taken:
                    continue
                for r, c in spots:
                    g[r][c] = color2
                break
        elif texture == "body_code":
            # a code-colored cell in the body: not a key (row 0 only)
            # and not a template (colors 1-4 are filtered out)
            for _try in range(80):
                r = rng.randint(2, h - 1)
                c = rng.randrange(w)
                if g[r][c] == 0 and (r, c) not in taken:
                    g[r][c] = rng.randint(1, 4)
                    break

        # output width check: pieces pack with 1-col gaps
        pw = n_codes * max(sh, sw) + n_codes - 1
        if pw > 30:
            continue
        return g
    raise ValueError("could not realize code-gallery board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row 0 has >=1 code cell (value 1-4); >=1 motif cell (color 5-9) in row>=2."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    codes = [grid[0][c] for c in range(w) if 1 <= grid[0][c] <= 4]
    if not codes:
        errors.append("no code cells (values 1-4) found in row 0")
    motif = any(5 <= grid[r][c] <= 9 for r in range(2, h) for c in range(w))
    if not motif:
        errors.append("no motif cells (colors 5-9) found in rows 2+")
    return errors


def _draw_from_degenerate(name, ctx):
    """no_codes — motif only: keys empty, output [[0]].
    no_motif — codes only: comps empty, output [[0]]. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 8, 10)
    w = ctx.draw_int("grid_w", 11, 13)
    g = full_grid(h, w, 0)
    if name == "no_codes":
        shape = _grow(rng, rng.randint(3, 5))
        for r, c in shape:
            g[3 + r][2 + c] = rng.choice(_MOTIF_COLORS)
        return g
    for c in sorted(rng.sample(range(w), rng.randint(2, 4))):
        g[0][c] = rng.randint(1, 4)
    return g
