"""Generator for arc_puzzle_bank_21_set5_e:hard_e04 — key-row transform script.

Rule: row 0 is a program key containing codes 1, 2, 3.  Ignore row 1,
crop the nonzero body below row 1, then apply the key left-to-right:
1 = rotate clockwise, 2 = flip left/right, 3 = flip up/down.

Combinatorial axes (8): grid_h, grid_w, key_len, key_codes, object_shape,
object_palette, object_position, texture.
Degenerates: no_key, no_body, identity_script.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d57d5daa0895"
VERSION = "3.0.0"  # rewrite wrong motif-gallery generator to match canonical key-row transform rule
TASK_ID = "d57d5daa0895"

SUMMARY = (
    "Top row contains a left-to-right transform script using codes 1,2,3. "
    "Row 1 is blank.  The body below contains one connected multicolor object "
    "in colors 4..9, offset from the origin.  The canonical rule crops the "
    "body object and applies the script: 1 rotate-cw, 2 flip-lr, 3 flip-ud."
)

INVARIANTS = [
    "row 0 contains a nonempty transform key over {1,2,3}",
    "row 1 is blank separator",
    "body contains exactly one nonzero connected object",
    "the key visibly changes the cropped body object",
]

PALETTE_KINDS = ("default", "short_script", "long_script", "multicolor")
DEGENERATE_TEXTURES = ("no_key", "no_body", "identity_script")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "5..16"},
    "key_len":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "key_codes":      {"type": "str", "default": "rng over 1|2|3", "valid": "1|2|3"},
    "object_shape":   {"type": "str", "default": "random connected", "valid": "asymmetric connected"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "body_below_blank_row", "valid": "body_below_blank_row"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|short_script|long_script|multicolor|no_key|no_body|identity_script"},
}

_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _norm(cells):
    mr = min(r for r, _c, _v in cells); mc = min(c for _r, c, _v in cells)
    return [(r - mr, c - mc, v) for r, c, v in cells]


def _rand_obj(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    colors = [4, 5, 6, 7, 8, 9]
    rng.shuffle(colors)
    return _norm([(r, c, colors[i % len(colors)]) for i, (r, c) in enumerate(sorted(cells))])


def _crop_from_cells(cells):
    norm = _norm(cells)
    h = max(r for r, _c, _v in norm) + 1
    w = max(c for _r, c, _v in norm) + 1
    g = full_grid(h, w, 0)
    for r, c, v in norm:
        g[r][c] = v
    return g


def _rotate_cw(g):
    return [[g[len(g) - 1 - r][c] for r in range(len(g))] for c in range(len(g[0]))]


def _flip_lr(g):
    return [list(reversed(row)) for row in g]


def _flip_ud(g):
    return list(reversed([list(row) for row in g]))


def _apply_codes(g, codes):
    cur = [list(row) for row in g]
    for code in codes:
        if code == 1:
            cur = _rotate_cw(cur)
        elif code == 2:
            cur = _flip_lr(cur)
        elif code == 3:
            cur = _flip_ud(cur)
    return cur


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        key_lo, key_hi = 1, 2; size_lo, size_hi = 4, 5
    elif difficulty == "hard":
        key_lo, key_hi = 3, 5; size_lo, size_hi = 6, 9
    else:
        key_lo, key_hi = 2, 4; size_lo, size_hi = 5, 7

    for _attempt in range(120):
        key = [rng.choice([1, 2, 3]) for _ in range(rng.randint(key_lo, key_hi))]
        obj = _rand_obj(rng, rng.randint(size_lo, size_hi))
        crop = _crop_from_cells(obj)
        if _apply_codes(crop, key) == crop:
            continue
        oh, ow = len(crop), len(crop[0])
        h = rng.randint(max(5, 2 + oh + 1), max(6, 2 + oh + 5))
        w = rng.randint(max(5, len(key) + 1, ow + 2), max(7, len(key) + 4, ow + 6))
        g = full_grid(h, w, 0)
        for c, code in enumerate(key):
            g[0][c] = code
        top = rng.randint(2, h - oh)
        left = rng.randint(0, w - ow)
        for r, c, v in obj:
            g[top + r][left + c] = v
        return g
    raise ValueError("could not realize visible transform script")


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 8, 0)
    if name == "no_key":
        for r, c, v in [(0, 0, 4), (0, 1, 5), (1, 0, 6)]:
            g[3 + r][3 + c] = v
        return g
    if name == "no_body":
        g[0][0] = 1; g[0][1] = 2
        return g
    if name == "identity_script":
        # Four rotations compose to identity, so the transform branch is hidden.
        for i in range(4):
            g[0][i] = 1
        for r, c, v in [(0, 0, 4), (0, 1, 5), (1, 0, 6)]:
            g[3 + r][3 + c] = v
        return g
    return g


def _body_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(2, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc, grid[rr][cc]))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    h, w = len(grid), len(grid[0])
    key = [v for v in grid[0] if v in {1, 2, 3}]
    if not key:
        errs.append("missing row-0 transform key")
    if any(v not in {0, 1, 2, 3} for v in grid[0]):
        errs.append("row 0 contains non-key foreground")
    if h < 3 or any(v != 0 for v in grid[1]):
        errs.append("row 1 must be a blank separator")
    comps = _body_components(grid)
    if len(comps) != 1:
        errs.append(f"expected exactly one body object, saw {len(comps)}")
        return errs
    if any(v in {1, 2, 3} for _r, _c, v in comps[0]):
        errs.append("body object uses key colors 1..3")
    crop = _crop_from_cells(comps[0])
    if key and _apply_codes(crop, key) == crop:
        errs.append("transform key leaves the body crop unchanged")
    return errs
