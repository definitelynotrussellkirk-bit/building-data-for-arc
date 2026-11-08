"""Generator for arc_additional_puzzle_bank_volume21:H147.

Rule: color 5 is a neutral wall; each 0-chamber fills with the
strict-plurality of its bordering {1,2,3} markers (the winner color
itself); a tie fills 8; no marker leaves the chamber empty.

This generator carves rectangular 0-ROOMS into a color-5 wall field and
sprinkles {1,2,3} markers on each room's ring -- usually a strict winner,
occasionally a tie.

Combinatorial axes: grid size, room count/sizes/positions, and the
per-room marker mix.
Degenerates: no_walls, no_markers, single_chamber.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d81b445f9906"
VERSION = "2.0.0"  # diversity: random rooms in a 5-wall field + per-room {1,2,3} marker mix (was fixed ~21)
TASK_ID = "d81b445f9906"
SUMMARY = (
    "Color-5 wall field (size varies) with rectangular 0-ROOMS, each ringed "
    "by sparse {1,2,3} markers. Rule: each room fills with the "
    "strict-plurality marker color (the winner itself; tie -> 8; no marker -> "
    "empty). The grid size, room count/sizes/positions and per-room marker "
    "mix vary freely (was a fixed setup, ~21 distinct)."
)

INVARIANTS = [
    "color 5 is the neutral wall, ignored by the vote",
    "each room is a 0-rectangle enclosed by wall, rings disjoint between rooms",
    "a room fills with its strict-plurality {1,2,3} color, or 8 on a tie",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_markers", "single_chamber")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_rooms":        {"type": "int", "default": "varies", "valid": "1..6"},
    "marker_mix":     {"type": "str", "default": "winner|tie", "valid": "winner|tie"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "rooms_in_wall", "valid": "rooms_in_wall"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_walls|no_markers|single_chamber"},
}


def _reserve(occ, top, left, sh, sw, h, w, margin=2):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _ring(top, left, rh, rw, h, w):
    cells = []
    for c in range(left, left + rw):
        cells.append((top - 1, c)); cells.append((top + rh, c))
    for r in range(top, top + rh):
        cells.append((r, left - 1)); cells.append((r, left + rw))
    return [(r, c) for (r, c) in cells if 0 <= r < h and 0 <= c < w]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, nr, rr = (12, 15), (12, 15), (1, 2), (3, 4)
    elif difficulty == "hard":
        hr, wr, nr, rr = (18, 24), (18, 24), (4, 6), (3, 6)
    else:
        hr, wr, nr, rr = (14, 19), (14, 19), (2, 4), (3, 5)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 5)
        occ = [[False] * w for _ in range(h)]
        rooms = []
        for _ in range(rng.randint(*nr)):
            rh = rng.randint(*rr); rw = rng.randint(*rr)
            for _t in range(40):
                top = rng.randint(1, h - rh - 1); left = rng.randint(1, w - rw - 1)
                if _reserve(occ, top, left, rh, rw, h, w):
                    for r in range(top, top + rh):
                        for c in range(left, left + rw):
                            g[r][c] = 0
                    rooms.append((top, left, rh, rw))
                    break
        if not rooms:
            continue

        filled = 0
        for (top, left, rh, rw) in rooms:
            ring = _ring(top, left, rh, rw, h, w)
            rng.shuffle(ring)
            if rng.random() < 0.78 and len(ring) >= 3:   # strict winner
                win = rng.randint(1, 3)
                nwin = rng.randint(2, min(4, len(ring) - 1))
                for (r, c) in ring[:nwin]:
                    g[r][c] = win
                if len(ring) > nwin and rng.random() < 0.5:
                    other = rng.choice([x for x in (1, 2, 3) if x != win])
                    cnt = rng.randint(1, nwin - 1)
                    for (r, c) in ring[nwin:nwin + cnt]:
                        g[r][c] = other
                filled += 1
            elif len(ring) >= 4:                          # tie -> fill 8
                a, b = rng.sample((1, 2, 3), 2)
                k = rng.randint(1, len(ring) // 2)
                for (r, c) in ring[:k]:
                    g[r][c] = a
                for (r, c) in ring[k:2 * k]:
                    g[r][c] = b
        if filled >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 5)
    for r in range(2, 5):
        for c in range(2, 5):
            g[r][c] = 0
    if name == "no_walls":
        return full_grid(9, 9, 0)
    if name == "no_markers":
        return g
    if name == "single_chamber":
        g[1][3] = 1; g[5][3] = 1; g[3][1] = 1   # winner 1
        return g
    g[1][3] = 1; g[5][3] = 2                     # tie -> 8
    return g


def _zero_rooms(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set()
    rooms = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == 0):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rooms.append(cells)
    return rooms


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    rooms = _zero_rooms(grid)
    if not rooms:
        msgs.append("normal instance should contain at least one 0-room")
    saw_strict = False
    for cells in rooms:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        top, bot, left, right = min(rs), max(rs), min(cs), max(cs)
        rect = {(r, c) for r in range(top, bot + 1) for c in range(left, right + 1)}
        if set(cells) != rect:
            msgs.append("each 0-room should be rectangular")
            break
        if top == 0 or left == 0 or bot == h - 1 or right == w - 1:
            msgs.append("room should have an in-bounds marker/wall ring")
            break
        ring = _ring(top, left, bot - top + 1, right - left + 1, h, w)
        votes = {1: 0, 2: 0, 3: 0}
        for r, c in ring:
            v = grid[r][c]
            if v in votes:
                votes[v] += 1
            elif v != 5:
                msgs.append("room ring should contain only wall 5 or markers 1/2/3")
                break
        ordered = sorted(votes.values(), reverse=True)
        if ordered[0] == 0:
            msgs.append("normal room should have at least one bordering marker")
            break
        if ordered[0] > ordered[1]:
            saw_strict = True
    if not saw_strict:
        msgs.append("at least one room should have a strict plurality winner")
    return msgs
