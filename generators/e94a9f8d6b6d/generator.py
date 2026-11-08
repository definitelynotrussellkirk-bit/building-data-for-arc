"""Generator for arc_puzzle_bank_21_set22_s:S22_H6 — source-frame motif to target-frame motif lookup.

Rule: each source frame (L-marker 2/3/4) carries a color-8 KEY motif in
its local coords; each target frame (5/6/7) carries a color-8/9 VALUE
motif. The first two source/target pairs define a lookup; the third
source repeats one key and the (blank) third target is filled with the
matching value.

Combinatorial axes: the two key motifs, the two value motifs, and which
key the query repeats.
Degenerates: no_query, identical_keys, blank_targets.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e94a9f8d6b6d"
RULE_HASH = "858e9bcd489c"  # canonical rule this generator was written against
VERSION = "3.1.0"  # 3.1.0: add executable frame/lookup self-check; was shape-locked 25x24 + all frames in ONE fixed orientation (canonical uses rotated/flipped frames). Add per-frame random orientation (lookup-invariant: motifs read in local coords) + vary grid size/frame positions
TASK_ID = "e94a9f8d6b6d"
SUMMARY = (
    "A 25x24 grid with three SOURCE frames (L-marker colors 2,3,4 in a "
    "left column) and three TARGET frames (colors 5,6,7, right column). "
    "Each source frame holds a RANDOM color-8 KEY motif in its local "
    "coordinates; each of the first two target frames holds a RANDOM "
    "color-8/9 VALUE motif. The two keys are distinct, defining a lookup "
    "A->valueA, B->valueB. The third source repeats one of the two keys "
    "and the third target starts BLANK. Rule: learn the key->value map "
    "from the first two pairs and paint the third target with the value "
    "for the third source's key. The two key motifs, the two value "
    "motifs and which key the query repeats all vary freely (was 4 "
    "hardcoded key/value sets)."
)

INVARIANTS = [
    "three source frames with marker colors 2, 3, 4",
    "three target frames with marker colors 5, 6, 7",
    "the first two source/target pairs define the lookup table",
    "the third source repeats one key and the third target starts blank",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_query", "identical_keys", "blank_targets")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "query_key":         {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "variant":           {"type": "int", "default": "n/a (random motifs)", "valid": "0..3"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "6", "valid": "6..6"},
    "position_bias":     {"type": "str", "default": "fixed_3x3_grid",
                          "valid": "fixed_3x3_grid"},
    "n_distinct_colors": {"type": "int", "default": "6", "valid": "6..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_query|identical_keys|blank_targets"},
}

# Local (u,v) cells within Chebyshev radius 3, excluding the three marker
# cells (u,v): (0,0)=a, (1,0)=b (at +vx), (0,1)=c (at +vy).
_LOCAL_CELLS = [(u, v) for u in range(-3, 4) for v in range(-3, 4)
                if (u, v) not in ((0, 0), (1, 0), (0, 1))]

# 8 frame orientations: (vx, vy) perpendicular cardinal unit vectors.
# b sits at origin+vx, c at origin+vy; the rule reads motifs in this basis.
_CARDINALS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
ORIENTATIONS = [(vx, vy) for vx in _CARDINALS for vy in _CARDINALS
                if vx[0] * vy[0] + vx[1] * vy[1] == 0]


def _gpos(origin, vx, vy, u, v):
    return (origin[0] + u * vx[0] + v * vy[0],
            origin[1] + u * vx[1] + v * vy[1])


def _frame(g, origin, vx, vy, colors):
    r, c = origin
    g[r][c] = colors[0]
    br, bc = _gpos(origin, vx, vy, 1, 0)   # b at +vx
    cr, cc = _gpos(origin, vx, vy, 0, 1)   # c at +vy
    g[br][bc] = colors[1]
    g[cr][cc] = colors[2]


def _paint_local(g, origin, vx, vy, pts, color=8):
    for u, v in pts:
        r, c = _gpos(origin, vx, vy, u, v)
        g[r][c] = color


def _paint_values(g, origin, vx, vy, pts):
    for (u, v), color in pts:
        r, c = _gpos(origin, vx, vy, u, v)
        g[r][c] = color


def _rand_key(rng, size):
    return rng.sample(_LOCAL_CELLS, size)


def _rand_value(rng, size):
    cells = rng.sample(_LOCAL_CELLS, size)
    return [((u, v), rng.choice([8, 9])) for u, v in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        query_key = 0; kr = (2, 3); vr = (2, 3)
    elif difficulty == "hard":
        query_key = 1; kr = (3, 5); vr = (3, 5)
    else:
        query_key = rng.randint(0, 1); kr = (2, 4); vr = (2, 4)

    # Two DISTINCT key motifs (distinct canonical sets so the lookup is sound).
    key_a = _rand_key(rng, rng.randint(*kr))
    for _ in range(40):
        key_b = _rand_key(rng, rng.randint(*kr))
        if set(key_b) != set(key_a):
            break
    values = [_rand_value(rng, rng.randint(*vr)), _rand_value(rng, rng.randint(*vr))]
    keys = [key_a, key_b]

    # Vary grid size + frame positions (rule scans the whole grid; layout is
    # 3 source frames stacked on the left, 3 target frames on the right).
    top = ctx.draw_int("top", 3, 5)
    row_gap = ctx.draw_int("row_gap", 7, 9)
    src_col = ctx.draw_int("src_col", 3, 6)
    col_gap = ctx.draw_int("col_gap", 8, 12)
    tgt_col = src_col + col_gap
    h = min(30, top + 2 * row_gap + 4 + ctx.draw_int("pad_h", 0, 2))
    w = min(30, tgt_col + 4 + ctx.draw_int("pad_w", 0, 2))
    source_origins = [(top + i * row_gap, src_col) for i in range(3)]
    target_origins = [(top + i * row_gap, tgt_col) for i in range(3)]

    # Each frame gets an INDEPENDENT random orientation. Motifs are stored and
    # read in local (vx,vy) coords, so the lookup is orientation-invariant and
    # the radius-3 motif always stays within Chebyshev 3 of its origin.
    g = full_grid(h, w, 0)
    for idx, origin in enumerate(source_origins):
        vx, vy = rng.choice(ORIENTATIONS)
        _frame(g, origin, vx, vy, (2, 3, 4))
        _paint_local(g, origin, vx, vy, keys[idx] if idx < 2 else keys[query_key])
    for idx, origin in enumerate(target_origins):
        vx, vy = rng.choice(ORIENTATIONS)
        _frame(g, origin, vx, vy, (5, 6, 7))
        if idx < 2:
            _paint_values(g, origin, vx, vy, values[idx])
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(25, 24, 0)
    vx, vy = (0, 1), (1, 0)                 # standard orientation for degenerates
    source_origins = [(3, 4), (11, 4), (19, 4)]
    target_origins = [(3, 16), (11, 16), (19, 16)]
    keys = [[(1, -1), (2, -1), (2, 0)], [(1, -2), (2, -2), (2, -1)]]
    values = [[((1, 1), 8), ((1, 2), 9)], [((1, 1), 9), ((2, 1), 8)]]
    if name == "no_query":
        for idx, origin in enumerate(source_origins[:2]):
            _frame(g, origin, vx, vy, (2, 3, 4)); _paint_local(g, origin, vx, vy, keys[idx])
        for idx, origin in enumerate(target_origins[:2]):
            _frame(g, origin, vx, vy, (5, 6, 7)); _paint_values(g, origin, vx, vy, values[idx])
        return g
    if name == "identical_keys":
        for origin in source_origins:
            _frame(g, origin, vx, vy, (2, 3, 4)); _paint_local(g, origin, vx, vy, keys[0])
        for idx, origin in enumerate(target_origins):
            _frame(g, origin, vx, vy, (5, 6, 7))
            if idx < 2:
                _paint_values(g, origin, vx, vy, values[0])
        return g
    if name == "blank_targets":
        for idx, origin in enumerate(source_origins):
            _frame(g, origin, vx, vy, (2, 3, 4))
            _paint_local(g, origin, vx, vy, keys[idx if idx < 2 else 0])
        for origin in target_origins:
            _frame(g, origin, vx, vy, (5, 6, 7))
        return g
    return g

def _find_marker_frames(grid, a, b, c):
    h = len(grid); w = len(grid[0]) if h else 0
    frames = []
    for r in range(h):
        for col in range(w):
            if grid[r][col] != a:
                continue
            for vx, vy in ORIENTATIONS:
                br, bc = _gpos((r, col), vx, vy, 1, 0)
                cr, cc = _gpos((r, col), vx, vy, 0, 1)
                if 0 <= br < h and 0 <= bc < w and 0 <= cr < h and 0 <= cc < w:
                    if grid[br][bc] == b and grid[cr][cc] == c:
                        frames.append(((r, col), vx, vy))
    return frames


def _local_value_count(grid, origin, vx, vy, allowed):
    h = len(grid); w = len(grid[0]) if h else 0
    cnt = 0
    for u, v in _LOCAL_CELLS:
        r, c = _gpos(origin, vx, vy, u, v)
        if 0 <= r < h and 0 <= c < w and grid[r][c] in allowed:
            cnt += 1
    return cnt


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    counts = {color: sum(v == color for row in grid for v in row) for color in (2, 3, 4, 5, 6, 7)}
    for color, cnt in counts.items():
        if cnt != 3:
            msgs.append(f"expected exactly three marker cells of color {color}, got {cnt}")
    src = _find_marker_frames(grid, 2, 3, 4)
    tgt = _find_marker_frames(grid, 5, 6, 7)
    if len(src) != 3:
        msgs.append(f"expected three source L-frames, got {len(src)}")
    if len(tgt) != 3:
        msgs.append(f"expected three target L-frames, got {len(tgt)}")
    if len(src) == 3:
        for frame in src:
            if _local_value_count(grid, *frame, allowed={8}) == 0:
                msgs.append("source frame has no key motif cells")
                break
    if len(tgt) == 3:
        tgt_sorted = sorted(tgt, key=lambda fr: fr[0][0])
        filled = [_local_value_count(grid, *fr, allowed={8, 9}) for fr in tgt_sorted]
        if filled[0] == 0 or filled[1] == 0:
            msgs.append("first two target frames must carry value motifs")
        if filled[2] != 0:
            msgs.append("third/query target frame should start blank")
    return msgs
