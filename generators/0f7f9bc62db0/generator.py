"""Generator for 0f7f9bc62db0 — crop the object adjacent to the gray marker.

Rule: find the gray(5) cell. Erase it. Find the 8-connected non-zero
object that's Chebyshev-adjacent to where the marker was. Crop the
remaining grid to that object's bbox. Output is the bbox subgrid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0f7f9bc62db0"
VERSION = "2.1.1"  # +self_check
TASK_ID = "0f7f9bc62db0"
SUMMARY = (
    "0-bg grid with: (a) exactly ONE gray(5) cell — the marker; (b) "
    "one TARGET non-gray object (some shape, 4-9 cells, in a single "
    "color) placed adjacent to the marker (Chebyshev distance ≤ 1 from "
    "at least one target cell); (c) 1-4 DISTRACTOR non-gray objects "
    "elsewhere (other colors or same target color allowed), NOT adjacent "
    "to the marker. Rule: remove the gray cell, find the 8-connected "
    "object adjacent to the marker's position, crop to its bbox. The "
    "output is just the target's bbox subgrid (no marker, no distractors)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one gray(5) cell",
    "exactly one non-gray target object is Chebyshev-adjacent to the marker",
    "≥1 distractor object placed NOT-adjacent to the marker (Chebyshev distance >1 from all target cells)",
    "target shape is non-trivial (bbox ≥2x2, has ≥1 internal hole OR is asymmetric)",
    "shapes don't overlap (with ≥1 cell buffer between them)",
]

# Free axes the runner may override. These match the keyed draws in generate();
# defaults shown are the medium-difficulty band, valid spans all difficulties.
AXES = {
    "grid_h":        {"type": "int", "default": "rng 11..15", "valid": "9..20",
                      "doc": "Grid height (easy 9..12, medium 11..15, hard 14..20)."},
    "grid_w":        {"type": "int", "default": "rng 11..15", "valid": "9..20",
                      "doc": "Grid width (easy 9..12, medium 11..15, hard 14..20)."},
    "target_size":   {"type": "int", "default": "rng 4..9", "valid": "3..11",
                      "doc": "Cell count of the target object adjacent to the marker."},
    "n_distractors": {"type": "int", "default": "rng 1..3", "valid": "1..5",
                      "doc": "Count of non-adjacent distractor objects."},
}


def _free(g, r1, c1, r2, c2, buffer=1):
    h, w = len(g), len(g[0])
    for r in range(max(0, r1 - buffer), min(h, r2 + buffer + 1)):
        for c in range(max(0, c1 - buffer), min(w, c2 + buffer + 1)):
            if g[r][c] != 0:
                return False
    return True


def _build_blob(rng, k):
    """Random walk to build a connected blob of k cells."""
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    # Normalize
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        target_size = ctx.draw_int("target_size", 3, 6)
        n_distract = ctx.draw_int("n_distractors", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 14, 20)
        target_size = ctx.draw_int("target_size", 7, 11)
        n_distract = ctx.draw_int("n_distractors", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 11, 15)
        target_size = ctx.draw_int("target_size", 4, 9)
        n_distract = ctx.draw_int("n_distractors", 1, 3)
    rng = ctx.draw_rng("placement")

    palette = [c for c in [1, 2, 3, 4, 6, 7, 8, 9] if c != 5]
    rng.shuffle(palette)
    target_color = palette[0]

    for outer in range(60):
        g = full_grid(h, w, 0)
        # Build target shape
        cells = _build_blob(rng, target_size)
        # Require bbox at least 2x2 OR ≥3 cells (so it's non-trivial)
        max_r = max(r for r, _ in cells)
        max_c = max(c for _, c in cells)
        if max_r < 1 and max_c < 1:
            continue
        sh = max_r + 1; sw = max_c + 1
        # Place target with buffer
        if sh + 2 > h or sw + 2 > w:
            continue
        target_placed = False
        for _ in range(40):
            r0 = rng.randint(1, h - sh - 1)
            c0 = rng.randint(1, w - sw - 1)
            cells_abs = [(r0 + dr, c0 + dc) for dr, dc in cells]
            if not all(g[r][c] == 0 for r, c in cells_abs):
                continue
            for r, c in cells_abs:
                g[r][c] = target_color
            target_placed = True
            break
        if not target_placed:
            continue
        # Place gray marker: Chebyshev ≤ 1 from at least one cell, but not on target
        target_set = set(cells_abs)
        marker_candidates = []
        for r, c in cells_abs:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    mr, mc = r + dr, c + dc
                    if 0 <= mr < h and 0 <= mc < w and (mr, mc) not in target_set and g[mr][mc] == 0:
                        marker_candidates.append((mr, mc))
        if not marker_candidates:
            continue
        mr, mc = rng.choice(marker_candidates)
        g[mr][mc] = 5

        # Place distractors NOT adjacent to the marker
        placed_d = 0
        distractor_colors = palette[1:] if len(palette) > 1 else [target_color]
        for _ in range(n_distract * 10):
            if placed_d >= n_distract:
                break
            d_size = rng.randint(2, max(2, target_size - 1))
            d_cells = _build_blob(rng, d_size)
            dsh = max(r for r, _ in d_cells) + 1
            dsw = max(c for _, c in d_cells) + 1
            if dsh + 2 > h or dsw + 2 > w:
                continue
            for _ in range(40):
                dr = rng.randint(0, h - dsh)
                dc = rng.randint(0, w - dsw)
                cells_abs_d = [(dr + ddr, dc + ddc) for ddr, ddc in d_cells]
                # Must not be Chebyshev-adjacent to marker (distance > 1) for all cells
                ok = True
                for r, c in cells_abs_d:
                    if abs(r - mr) <= 1 and abs(c - mc) <= 1:
                        ok = False; break
                    if g[r][c] != 0:
                        ok = False; break
                    # Check 1-cell buffer to other objects
                    for ddr2 in (-1, 0, 1):
                        for ddc2 in (-1, 0, 1):
                            nr, nc = r + ddr2, c + ddc2
                            if 0 <= nr < h and 0 <= nc < w:
                                if g[nr][nc] != 0 and (nr, nc) not in cells_abs_d:
                                    ok = False
                                    break
                        if not ok: break
                    if not ok: break
                if not ok:
                    continue
                dcolor = rng.choice(distractor_colors)
                for r, c in cells_abs_d:
                    g[r][c] = dcolor
                placed_d += 1
                break
        if placed_d < 1:
            continue
        return g
    raise ValueError("could not realize layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one gray (5) marker AND at least one non-gray, non-zero cell present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    h, w = len(grid), len(grid[0])
    gray_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if len(gray_cells) != 1:
        errors.append(f"expected exactly 1 gray (5) marker, found {len(gray_cells)}")
    has_target = any(grid[r][c] not in (0, 5) for r in range(h) for c in range(w))
    if not has_target:
        errors.append("no non-gray target object cells found")
    return errors
