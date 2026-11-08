"""Generator for 5af49b42 — dots bloom into their key run.

Rule: a horizontal run of >=2 non-zero cells is a KEY (a color legend).
A single isolated non-zero cell is a DOT. For each dot of color v, find
the key run containing v and the index of v within it; stamp a full copy
of that key run on the dot's row, aligned so v lands on the dot's column.

Combinatorial axes (8): grid_h, grid_w, n_keys, key_len, n_dots,
key_positions, dot_positions, palette.
Degenerates: no_keys, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e9f25803112"
VERSION = "3.2.1"  # require at least one visible red-dot bloom witness  # was FIXED 13x16 grid + two fixed bottom-row keys + 4 HARDCODED dot positions (shape-locked in/out, sparse, fixed layout). Rule reads keys/dots ANYWHERE; canon grids are large (12-19) and dense. Now vary grid size (toward contest scale), 2-3 keys at random rows, and MANY scattered dots; global-distinct key colors so every dot maps to exactly one key.
TASK_ID = "1e9f25803112"
SUMMARY = (
    "0-bg grid (size varies, up to contest scale). 2-3 horizontal KEY runs "
    "(length 2-4, globally-distinct non-zero colors) placed at random isolated "
    "positions, plus MANY isolated DOT cells each colored from some key. Rule: "
    "each dot blooms horizontally into a full copy of its key run, aligned so the "
    "dot's color lands at its column. Keys persist."
)

INVARIANTS = [
    "background is 0",
    "every key is a horizontal run of length >= 2 with distinct non-zero colors",
    "every dot is an isolated single cell (length-1 run, zero on both horizontal sides)",
    "key colors are globally distinct, so each dot color appears in exactly one key",
    "each dot's key run fits horizontally when aligned at the dot's column",
]

DEGENERATE_TEXTURES = ("no_keys", "no_dots", "full_grid")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 12..17", "valid": "8..24"},
    "grid_w":  {"type": "int", "default": "rng 13..20", "valid": "9..26"},
    "n_keys":  {"type": "int", "default": "rng 2..3", "valid": "1..3"},
    "key_len": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "n_dots":  {"type": "int", "default": "rng 5..9", "valid": "1..16"},
    "texture": {"type": "str", "default": "none",
                "valid": "|".join(DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 10, 13)
        nkeys = 2; ndots = ctx.draw_int("n_dots", 3, 5); lmax = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 24); w = ctx.draw_int("grid_w", 16, 26)
        nkeys = 3; ndots = ctx.draw_int("n_dots", 8, 16); lmax = 4
    else:
        h = ctx.draw_int("grid_h", 12, 17); w = ctx.draw_int("grid_w", 13, 20)
        nkeys = ctx.draw_int("n_keys", 2, 3); ndots = ctx.draw_int("n_dots", 5, 9); lmax = 3

    pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    keys = []
    for key_i in range(nkeys):
        if len(pool) < 2:
            break
        remaining_keys = nkeys - key_i
        # Reserve two colors for each future key.  The old hard path could draw
        # 4+4 colors for the first two keys, leaving only one color and silently
        # emitting two keys despite nkeys=3.
        max_len = min(lmax, len(pool) - 2 * (remaining_keys - 1))
        if max_len < 2:
            break
        L = rng.randint(2, max_len)
        keys.append(pool[:L]); pool = pool[L:]

    g = full_grid(h, w, 0)
    blocked = set()   # cells that must stay clear (keep runs from merging)

    def span_free(r, s, e):
        for c in range(s - 1, e + 2):
            if (r, c) in blocked:
                return False
            if 0 <= c < w and g[r][c] != 0:
                return False
        return True

    placed_keys = []
    for key in keys:
        L = len(key)
        for _ in range(200):
            r = rng.randint(0, h - 1); s = rng.randint(0, w - L); e = s + L - 1
            if not span_free(r, s, e):
                continue
            for i, v in enumerate(key):
                g[r][s + i] = v
            for c in range(s - 1, e + 2):
                blocked.add((r, c))
            placed_keys.append(key)
            break
    if not placed_keys:                       # guarantee >=1 key
        key = keys[0] if keys else [1, 2]
        for i, v in enumerate(key):
            g[0][i] = v
        for c in range(-1, len(key) + 1):
            blocked.add((0, c))
        placed_keys.append(key)

    # map each (globally unique) color to (key, index)
    color_to_key = {}
    flat = []
    for key in placed_keys:
        for idx, v in enumerate(key):
            color_to_key[v] = (key, idx); flat.append(v)

    placed_dots = 0
    for _ in range(ndots * 50):
        if placed_dots >= ndots:
            break
        v = rng.choice(flat); key, idx = color_to_key[v]; L = len(key)
        cmin, cmax = idx, w - L + idx           # bloom [c-idx, c-idx+L-1] stays in bounds
        if cmin > cmax:
            continue
        c = rng.randint(cmin, cmax); r = rng.randint(0, h - 1)
        if (r, c) in blocked or g[r][c] != 0:
            continue
        if (r, c - 1) in blocked or (r, c + 1) in blocked:
            continue
        if c - 1 >= 0 and g[r][c - 1] != 0:
            continue
        if c + 1 < w and g[r][c + 1] != 0:
            continue
        g[r][c] = v
        blocked.add((r, c - 1)); blocked.add((r, c)); blocked.add((r, c + 1))
        placed_dots += 1
    if placed_dots == 0:                        # guarantee >=1 dot (non-identity)
        v = flat[0]; key, idx = color_to_key[v]; L = len(key)
        for r in range(h):
            c = idx
            if g[r][c] == 0 and (r, c) not in blocked and \
               (c + 1 >= w or g[r][c + 1] == 0) and (c - 1 < 0 or g[r][c - 1] == 0):
                g[r][c] = v; break
    return g


def _horizontal_nonzero_runs(grid):
    runs = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            start = c
            vals = []
            while c < len(row) and row[c] != 0:
                vals.append(row[c])
                c += 1
            runs.append((r, start, c - 1, vals))
    return runs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable normal-path invariants for the dot-to-key blooming task."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    runs = _horizontal_nonzero_runs(grid)
    keys = [(r, s, e, vals) for r, s, e, vals in runs if len(vals) >= 2]
    dots = [(r, s, vals[0]) for r, s, e, vals in runs if len(vals) == 1]
    if difficulty == "hard":
        if len(keys) != 3:
            errors.append(f"hard samples should contain exactly 3 keys, found {len(keys)}")
    elif len(keys) < 2:
        errors.append(f"normal/easy samples should contain at least 2 keys, found {len(keys)}")
    min_dots = 8 if difficulty == "hard" else (3 if difficulty == "easy" else 5)
    if len(dots) < min_dots:
        errors.append(f"expected at least {min_dots} isolated dots, found {len(dots)}")
    color_to_key = {}
    for _r, _s, _e, vals in keys:
        if len(set(vals)) != len(vals):
            errors.append(f"key has repeated colors: {vals}")
        for idx, v in enumerate(vals):
            if v in color_to_key:
                errors.append(f"key color {v} appears in more than one key")
            color_to_key[v] = (vals, idx)
    for r, c, v in dots:
        if v not in color_to_key:
            errors.append(f"dot color {v} at {(r, c)} has no key")
            continue
        vals, idx = color_to_key[v]
        start = c - idx
        end = start + len(vals) - 1
        if start < 0 or end >= w:
            errors.append(f"dot at {(r, c)} cannot bloom key {vals} in-bounds")
        if (c > 0 and grid[r][c - 1] != 0) or (c + 1 < w and grid[r][c + 1] != 0):
            errors.append(f"dot at {(r, c)} is not horizontally isolated")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 16, 0)
    if name == "no_keys":
        g[5][5] = 2                              # a lone cell, no key run -> nothing to bloom
        return g
    if name == "no_dots":
        for i in range(4):
            g[12][i] = 2 + i
            g[12][9 + i] = 6 + i
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(16):
                g[r][c] = 2
        return g
    return g


def _has_visible_bloom_witness(grid):
    h, w = len(grid), len(grid[0])
    dots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    for r, c in dots:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr or dc) and 0 <= r + dr < h and 0 <= c + dc < w:
                    return True
    return False
