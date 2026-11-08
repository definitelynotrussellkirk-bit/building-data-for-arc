"""Generator for arc_additional_puzzle_bank_volume18:M123.

Rule: count objects of colors 2, 3, and 4, then emit grouped color
runs separated by zeros.

Combinatorial axes (8): grid_h, grid_w, palette_kind, count_spread,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_color, equal_counts, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a92bb76c10ef"
VERSION = "2.2.0"  # dup-outputs: output = 1x(n2+n3+n4+2) count-bar; counts capped 1..3 -> exactly 27 combos. Raise to 1..5 (up to 125) + wider grid -> distinct 27->83, flag cleared."
TASK_ID = "a92bb76c10ef"
SUMMARY = (
    "0-bg grid (h~8-11, w~10-14) with "
    "OBJECTS of THREE FIXED COLORS (2, "
    "3, 4): for each color c ∈ {2, 3, "
    "4}, place counts[c] (1-5) "
    "INSTANCES at slot positions from a "
    "fixed slot list (sparse rows × "
    "sparse cols). Each instance is a "
    "single cell, with 35% probability "
    "extended to a 2-cell horizontal "
    "pair by painting the cell to its "
    "right. Counts per color are "
    "INDEPENDENT and may vary 1-5. "
    "Rule (COUNT OBJECTS OF COLORS 2, "
    "3, 4 — EMIT GROUPED COLOR RUNS "
    "SEPARATED BY ZEROS): COUNT the "
    "number of 4-CONNECTED color-2 "
    "components → n2. Same for color-3 "
    "→ n3 and color-4 → n4. PRODUCE a "
    "SINGLE-ROW OUTPUT: emit n2 cells "
    "of COLOR 2, then a bg-0 "
    "separator, then n3 cells of COLOR "
    "3, then bg-0, then n4 cells of "
    "COLOR 4. Output length = n2 + n3 "
    "+ n4 + 2 (the separators). Net: "
    "the input's scattered colored "
    "objects collapse into a single-"
    "row count encoding. Flagged "
    "intrinsic-low (uniq_out=20): "
    "bounded by 5³ count combinations."
)

INVARIANTS = [
    "only colors 2, 3, and 4 matter",
    "same-color objects are separated so counts are visible",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_color", "equal_counts", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "count_spread":   {"type": "str", "default": "varied", "valid": "varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "spread_slots",
                       "valid": "spread_slots"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|missing_color|equal_counts|no_objects"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the three counted colors are present as separated components."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    bad = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 2, 3, 4)]
    if bad:
        errs.append(f"expected only values 0/2/3/4; found others at {bad[:3]}")
    for color in (2, 3, 4):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if not cells:
            errs.append(f"normal instance is missing counted color {color}")
    for color in (2, 3, 4):
        seen: set[tuple[int, int]] = set()
        comps = 0
        for r0 in range(h):
            for c0 in range(w):
                if grid[r0][c0] != color or (r0, c0) in seen:
                    continue
                comps += 1
                stack = [(r0, c0)]
                seen.add((r0, c0))
                while stack:
                    r, c = stack.pop()
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
        if comps == 0:
            continue
        if not (1 <= comps <= 5):
            errs.append(f"color {color} has {comps} components; expected 1..5")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = 1 x (n2+n3+n4+2) bar of the three object counts -> distinct = combos
    # of (n2,n3,n4). v1.x capped each at 1..3 -> exactly 27. Raise count range
    # (1..5 -> up to 125 combos) + widen grid for slots.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13); c_hi = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 15, 18); c_hi = 5
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 12, 18); c_hi = 5
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    counts = {2: rng.randint(1, c_hi), 3: rng.randint(1, c_hi), 4: rng.randint(1, c_hi)}
    slots = [(r, c) for r in range(1, h, 2) for c in range(1, w, 3)]
    rng.shuffle(slots)
    idx = 0
    for color in [2, 3, 4]:
        for _ in range(counts[color]):
            r, c = slots[idx]
            idx += 1
            g[r][c] = color
            if rng.random() < 0.35 and c + 1 < w:
                g[r][c + 1] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "missing_color":
        # one of {2,3,4} has count 0 → its run in the output is empty
        slots = [(1, 1), (3, 4), (5, 8)]
        for (r, c), color in zip(slots, [2, 4, 4]):
            g[r][c] = color
        return g
    if name == "equal_counts":
        # all three counts equal → output run-lengths are identical, no rank signal
        for (r, c), color in [((1, 1), 2), ((1, 5), 2),
                              ((3, 1), 3), ((3, 5), 3),
                              ((5, 1), 4), ((5, 5), 4)]:
            g[r][c] = color
        return g
    if name == "no_objects":
        # empty grid → all counts zero, output collapses to zeros
        return g
    return g
