"""Generator for arc_additional_puzzle_bank_volume8:M53.

Rule: BFS from the color-2 seed through cells with value 0 or 2; every
reached 0-cell becomes color 8.

Combinatorial axes: grid size, the number / size / position of the
color-5 rooms, which room holds the seed, and the decorations elsewhere.
Degenerates: no_seed, no_walls, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "17f474e4fb99"
VERSION = "2.2.0"  # seed room must have interior area >=2 (a 3x3 room held only the seed -> nothing to flood -> identity demo)
TASK_ID = "17f474e4fb99"
SUMMARY = (
    "0-bg grid (size varies). Several closed COLOR-5 (gray) ROOMS "
    "(hollow rectangles, >=3x3), placed apart. ONE room holds a single "
    "color-2 (red) SEED; the other rooms hold color-6 (magenta) "
    "DECORATIONS. Rule: flood-fill from the seed through 0/2 cells "
    "(4-connected); every reached empty cell becomes COLOR 8 (cyan). "
    "Because the seed's room is closed, only that room's interior fills; "
    "the other rooms and the outside are unreachable and unchanged. The "
    "grid size, the number / size / position of the rooms, which room is "
    "seeded, and the decorations all vary freely (was a fixed two-"
    "compartment layout)."
)

INVARIANTS = [
    "closed color-5 rooms partition the grid",
    "exactly one color-2 seed in one room",
    "other rooms hold unreachable color-6 decorations",
    "the seeded room's interior fills with color 8",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seed", "no_walls", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_seed|no_walls|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  task_id=TASK_ID, version=VERSION,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nr, smax = (10, 12), (10, 12), (2, 2), 5
    elif difficulty == "hard":
        hr, wr, nr, smax = (14, 18), (14, 18), (3, 4), 7
    else:
        hr, wr, nr, smax = (11, 14), (11, 14), (2, 3), 6

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        rooms = []

        def _reserve(top, left, bh, bw):
            for r in range(top - 1, top + bh + 1):
                for c in range(left - 1, left + bw + 1):
                    if 0 <= r < h and 0 <= c < w and occ[r][c]:
                        return False
            for r in range(top, top + bh):
                for c in range(left, left + bw):
                    occ[r][c] = True
            return True

        for _ in range(rng.randint(*nr)):
            for _t in range(30):
                bh = rng.randint(3, min(smax, h)); bw = rng.randint(3, min(smax, w))
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _reserve(top, left, bh, bw):
                    rooms.append((top, left, top + bh - 1, left + bw - 1))
                    break
        if len(rooms) < 2:
            continue

        g = full_grid(h, w, 0)
        for (r0, c0, r1, c1) in rooms:
            draw_frame(g, r0, c0, r1, c1, 5)

        # Seed in one room; decorations in the others. The seed room MUST have an
        # interior of >=2 cells, otherwise the seed occupies the only interior cell
        # and the flood paints nothing (output == input, an identity demo).
        seed_candidates = [i for i, (r0, c0, r1, c1) in enumerate(rooms)
                           if (r1 - r0 - 1) * (c1 - c0 - 1) >= 2]
        if not seed_candidates:
            continue
        si = rng.choice(seed_candidates)
        sr0, sc0, sr1, sc1 = rooms[si]
        g[rng.randint(sr0 + 1, sr1 - 1)][rng.randint(sc0 + 1, sc1 - 1)] = 2
        for j, (r0, c0, r1, c1) in enumerate(rooms):
            if j == si:
                continue
            for _ in range(rng.randint(1, 2)):
                rr = rng.randint(r0 + 1, r1 - 1); cc = rng.randint(c0 + 1, c1 - 1)
                if g[rr][cc] == 0:
                    g[rr][cc] = 6
        return g

    raise ValueError("could not realize at least two closed rooms")


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_seed":
        draw_frame(g, 1, 1, 5, 5, 5)
        g[8][6] = 6
        return g
    if name == "no_walls":
        g[4][4] = 2
        g[8][6] = 6
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 5
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    from puzzle_generators.helpers.selfcheck import components, interior_cells, is_full_frame_component
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    frames = [c for c in components(grid, colors={5}, same_color=True)
              if is_full_frame_component(c, color=5, min_size=3)]
    if len(frames) < 2:
        msgs.append(f"expected at least two closed color-5 rooms, got {len(frames)}")
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(seeds) != 1:
        msgs.append(f"expected exactly one color-2 seed, got {len(seeds)}")
    seeded_rooms = 0
    decorated_unseeded = 0
    for frame in frames:
        inside = set(interior_cells(frame["bbox"]))
        nseed = sum((r, c) in inside for r, c in seeds)
        ndecor = sum(grid[r][c] == 6 for r, c in inside)
        if nseed:
            seeded_rooms += 1
        elif ndecor:
            decorated_unseeded += 1
    if seeds and seeded_rooms != 1:
        msgs.append("seed is not strictly inside exactly one closed room")
    if len(frames) >= 2 and decorated_unseeded < len(frames) - 1:
        msgs.append("not every unseeded room has unreachable color-6 decoration")
    return msgs
