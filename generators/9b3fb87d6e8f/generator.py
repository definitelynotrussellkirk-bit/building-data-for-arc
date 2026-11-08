"""Generator for arc_additional_puzzle_bank_volume15:H100.

Rule: a ray leaves the color-1 source moving right; color-3 cells bounce
it like '/', color-4 like '\\', a color-5 wall stops it; every 0-cell it
traverses is painted color 8.

Combinatorial axes: grid size, source position, the number / placement /
type of deflectors (turn points), and the wall position — all derived by
tracing the intended path so the ray provably hits them.
Degenerates: no_source, no_wall, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9b3fb87d6e8f"
VERSION = "3.0.1"  # diversity: traced random ray path (source/deflectors/wall) (was 1 fixed config + padding)
TASK_ID = "9b3fb87d6e8f"
SUMMARY = (
    "0-bg grid (size varies). A color-1 (blue) SOURCE on the left emits a "
    "ray moving RIGHT. 1-3 single-cell DEFLECTORS (color-3 '/' or color-4 "
    "'\\') sit at the ray's TURN POINTS, and a color-5 (gray) WALL sits "
    "where the ray finally stops. Rule: trace the ray from the source — "
    "'/' turns right->up / up->right etc., '\\' turns right->down / "
    "down->right etc., the wall stops it — and paint every traversed "
    "0-cell COLOR 8 (cyan). The whole path is built by tracing forward so "
    "every deflector is actually hit and the ray ends at the wall; grid "
    "size, source position, deflector count/placement/type and wall "
    "position all vary freely (was one fixed ray config + padding)."
)

INVARIANTS = [
    "exactly one 1-source",
    "1-3 deflectors (color 3 or 4) on the ray's path",
    "one 5-wall terminates the ray",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_source", "no_wall", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_source|no_wall|full_grid"},
}


def _bounce(d, kind):
    dr, dc = d
    if kind == 3:                 # slash '/'
        return (-dc, -dr)
    return (dc, dr)               # backslash '\\'


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  task_id=TASK_ID, version=VERSION,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, ndr = (8, 10), (9, 12), (1, 1)
    elif difficulty == "hard":
        hr, wr, ndr = (12, 16), (13, 16), (2, 3)
    else:
        hr, wr, ndr = (9, 13), (11, 14), (1, 2)

    for _attempt in range(200):
        h = rng.randint(*hr); w = rng.randint(*wr)
        sr = rng.randint(0, h - 1); sc = rng.randint(0, max(0, w // 3))
        source = (sr, sc)
        used = {source}
        roles = {}                      # pos -> ('defl', kind) | 'wall'
        path = []                       # 0-cells the ray paints

        def free(p):
            r, c = p
            return 0 <= r < h and 0 <= c < w and p not in used and p != source

        pos = (sr, sc + 1); d = (0, 1)
        n_def = rng.randint(*ndr)
        ok = True
        for _i in range(n_def):
            seg = rng.randint(1, 4)
            for _s in range(seg):
                if not free(pos):
                    ok = False; break
                path.append(pos); used.add(pos); pos = (pos[0] + d[0], pos[1] + d[1])
            if not ok:
                break
            if not free(pos):
                ok = False; break
            kind = rng.choice([3, 4])
            roles[pos] = ('defl', kind); used.add(pos)
            d = _bounce(d, kind)
            pos = (pos[0] + d[0], pos[1] + d[1])
        if not ok:
            continue
        # Final segment, then the wall.
        seg = rng.randint(1, 4)
        for _s in range(seg):
            if not free(pos):
                ok = False; break
            path.append(pos); used.add(pos); pos = (pos[0] + d[0], pos[1] + d[1])
        if not ok or not free(pos) or not path:
            continue
        wall = pos

        g = full_grid(h, w, 0)
        g[sr][sc] = 1
        for (pr, pc), role in roles.items():
            g[pr][pc] = role[1]
        g[wall[0]][wall[1]] = 5
        return g

    # Fallback: the original known-valid fixed layout.
    g = full_grid(8, 10, 0)
    g[6][1] = 1; g[6][4] = 3; g[3][4] = 4; g[3][7] = 5
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "no_source":
        g[3][7] = 5
        return g
    if name == "no_wall":
        g[6][1] = 1
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(10):
                g[r][c] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: exactly one color-1 source; at least one deflector (3 or 4); exactly one color-5 wall."""
    msgs = []
    h, w = len(grid), len(grid[0])
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    deflectors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (3, 4)]
    if len(ones) != 1:
        msgs.append(f"expected exactly 1 color-1 source, got {len(ones)}")
    if len(fives) != 1:
        msgs.append(f"expected exactly 1 color-5 wall, got {len(fives)}")
    if len(deflectors) < 1:
        msgs.append("no deflectors (color 3 or 4) found")
    return msgs
