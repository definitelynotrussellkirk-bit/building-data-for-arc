"""Generator for arc_puzzle_bank_21_set24_bundle:medium_p01 — select-by-key-color and crop.

Rule: key = color at (0,0). Among the objects of that color (excluding the
one containing (0,0) itself), take the first by bbox order and crop it to
its bbox. Output is that cropped object.

This generator draws: an isolated key marker at (0,0) in the key color,
ONE key-colored object somewhere in the body, and several distractor
objects in OTHER colors (which the rule ignores).

Combinatorial axes: grid size, key color, the key object's shape/size,
distractor objects.
Degenerates: no_key (cell (0,0) is bg -> no key), no_object (key marker
but no key-colored object), single_object (only the key object).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0e37f2aee589"
VERSION = "2.0.2"  # strengthen executable invariant: exactly one body key-colored component
TASK_ID = "0e37f2aee589"

SUMMARY = "Key marker at (0,0) sets a color; one key-colored object + distractor objects; rule crops the key object."

INVARIANTS = [
    "background is 0",
    "(0,0) holds the key color as an isolated marker",
    "exactly one key-colored object in the body (not touching (0,0))",
    "distractor objects use colors different from the key",
    "objects are isolated from each other",
]

DEGENERATE_TEXTURES = ("no_key", "no_object", "single_object")

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "grid_w":            {"type": "int", "default": "rng 12..16", "valid": "9..20"},
    "key_color":         {"type": "color", "default": "rng (!=0)", "valid": "1..9"},
    "obj_size":          {"type": "int", "default": "rng 3..9", "valid": "2..12"},
    "n_distract":        {"type": "int", "default": "rng 1..3", "valid": "0..5"},
    "texture":           {"type": "str", "default": "n/a (degenerates only)",
                          "valid": "|".join(DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _poly(rng, size):
    """Random connected polyomino of `size` cells, normalized."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _place(rng, g, shape, color, h, w, r_lo=1):
    sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
    if sh >= h or sw >= w:
        return False
    for _ in range(120):
        r0 = rng.randint(r_lo, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for r, c in shape:
            g[r0 + r][c0 + c] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        os_lo, os_hi, nd_lo, nd_hi = 3, 5, 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 15, 19)
        os_lo, os_hi, nd_lo, nd_hi = 5, 10, 2, 4
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        os_lo, os_hi, nd_lo, nd_hi = 3, 9, 1, 3

    for outer in range(40):
        g = full_grid(h, w, 0)
        key = int(overrides.get("key_color", rng.randint(1, 9)))
        g[0][0] = key  # isolated key marker (row 1+ is clear of it)

        # the key-colored object (rule crops this)
        osize = int(overrides.get("obj_size", rng.randint(os_lo, os_hi)))
        if not _place(rng, g, _poly(rng, osize), key, h, w, r_lo=1):
            continue

        # distractor objects in OTHER colors (rule ignores them)
        n_d = int(overrides.get("n_distract", rng.randint(nd_lo, nd_hi)))
        others = [c for c in range(1, 10) if c != key]
        for _ in range(n_d):
            dcol = rng.choice(others)
            _place(rng, g, _poly(rng, rng.randint(2, 6)), dcol, h, w, r_lo=1)
        return g
    raise ValueError("could not realize layout")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify isolated key marker and exactly one body component of that color."""
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    key = grid[0][0]
    if key == 0:
        msgs.append("(0,0) is 0 — no key color; rule has no color to search for")
        return msgs
    # Flood-fill key-colored components, separating the marker component from
    # the actual object selected by the canonical rule.
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != key or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == key:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    marker = [comp for comp in comps if (0, 0) in comp]
    if len(marker) != 1 or len(marker[0]) != 1:
        msgs.append("the (0,0) key marker is not an isolated single cell")
    body = [comp for comp in comps if (0, 0) not in comp]
    if len(body) != 1:
        msgs.append(
            f"expected exactly one body component of key color {key}, found {len(body)}"
        )
    elif len(body[0]) < 2:
        msgs.append("key-colored body object is a singleton; crop rule is under-demonstrated")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_key":
        # (0,0) is bg -> rule has no key color.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 4
        return g
    if name == "no_object":
        # key marker but no key-colored object in body.
        g[0][0] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][5 + dc] = 6  # distractor only
        return g
    if name == "single_object":
        g[0][0] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1), (0, 1)]:
            g[5 + dr][5 + dc] = 4
        return g
    return g
