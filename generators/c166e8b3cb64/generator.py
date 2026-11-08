"""Generator for arc_additional_puzzles_21_set18_bundle:E125.

Rule: crop the largest non-zero connected component (ties broken by
earliest bbox position).

Combinatorial axes (8): grid_h/w, palette_kind, large_size, small_size,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: tied_largest, only_one_component, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "c166e8b3cb64"
# 2.2.0: the largest component (the rule's pick) was a fully-filled rectangle, so
# its bbox crop was a solid single-color block (all_background_output). Make the
# winner a holed ring (full bbox, interior 0s) so its crop shows real structure,
# and keep it the strict largest by cell count. Adds self_check.
VERSION = "2.2.0"
TASK_ID = "c166e8b3cb64"
SUMMARY = (
    "0-bg grid (h, w varies by "
    "difficulty: 9×11 / 10×13 / "
    "14×16) with: N_COMPS ∈ 2-4 "
    "SEPARATED 4-CONNECTED COMPONENTS, "
    "each painted in a DISTINCT color "
    "drawn from {1..9}, each as a "
    "solid rectangle filling a "
    "subset of size cells (rectangle "
    "dimensions chosen to "
    "approximately match each "
    "component's size). The LARGEST "
    "component has size LARGE_SIZE "
    "(6-14 by difficulty); other "
    "components have strictly "
    "smaller sizes (decreasing by "
    "2 per component). Components "
    "placed with gap ≥2 between "
    "bboxes. Rule (FIND THE 4-"
    "CONNECTED COMPONENT (UNDER "
    "'NON-ZERO' PREDICATE) WITH "
    "THE LARGEST CELL COUNT; "
    "TIE-BREAK BY EARLIEST BBOX "
    "TOP-LEFT (SMALLER R, THEN "
    "SMALLER C); CROP THE INPUT "
    "TO THAT COMPONENT'S BBOX; "
    "OUTPUT THE CROP — CELLS IN "
    "THE COMPONENT PRESERVE THEIR "
    "COLORS, BBOX HOLES ARE 0): "
    "EXTRACT every non-bg "
    "component. SORT by "
    "(-cell_count, min_r, "
    "min_c). PICK first. CROP "
    "input to its bbox. OUTPUT. "
    "Net: largest component "
    "extracted with its "
    "original colors in a tight "
    "bbox crop."
)

# Rivals: 'output is input' refuted by demos (output is small crop).
# 'pick smallest' refuted by demos with a tiny component (NOT picked).
# 'pick by color' refuted by demos where size order differs from color
# order. 'pick first by position only' refuted by demos where the
# smallest component is at top but isn't picked. 'output uncropped'
# refuted by demos showing tight bbox. 'pick by sum of color values'
# refuted by demos with varied size+color combos. 3 demos with clearly
# largest component pinned, varied positions, pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 separated 4-connected non-zero components",
    "exactly one component has STRICTLY largest cell count (no ties on the primary criterion)",
    "components don't 4-touch (so each is its own component)",
]

PALETTE_KINDS = ("wide", "tall", "warm", "cool")
DEGENERATE_TEXTURES = ("tied_largest", "only_one_component", "all_same_size")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "by difficulty", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "by difficulty", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "large_size":     {"type": "choice", "default": "wide",
                       "valid": "wide|tall"},
    "small_size":     {"type": "int", "default": "4", "valid": "4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # input grid size is free (rule extracts nonzero components, output dims
    # depend on the chosen component, not the canvas). v1.x used a FIXED size
    # per difficulty -> in_shapes=1 (shape-locked-in). Now draw size from a range.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 10, 12)
        n_comps = 2
        large_size = rng.randint(6, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 15, 18)
        n_comps = rng.randint(3, 4)
        large_size = rng.randint(10, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 11, 16)
        n_comps = rng.randint(2, 3)
        large_size = rng.randint(7, 11)
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_comps)

    # WINNER = a holed ring (full bbox, interior 0s) so the rule's bbox crop is
    # never a solid block. Its cell count is the ring perimeter.
    # cap ring dims so a second component + gaps still fit the canvas.
    rh = rng.randint(3, max(3, min(5, h - 4)))
    rw = rng.randint(3, max(3, min(5, w - 4)))
    winner_rel = [(r, c) for r in range(rh) for c in range(rw)
                  if r in (0, rh - 1) or c in (0, rw - 1)]
    winner_count = len(winner_rel)
    # secondary components: solid blocks, strictly fewer cells than the winner.
    shapes = [(winner_rel, rh, rw)]
    for i in range(n_comps - 1):
        s = max(2, winner_count - 2 - i * 2)
        s = min(s, winner_count - 1)            # strictly smaller than winner
        bh = rng.randint(1, min(3, s, h))
        bw = max(1, (s + bh - 1) // bh)
        bw = min(bw, w)                         # keep within the canvas
        actual = min(s, bh * bw)                # don't exceed the block
        rel = [(r, c) for r in range(bh) for c in range(bw)][:actual]
        shapes.append((rel, bh, bw))

    for _attempt in range(30):
        g = full_grid(h, w, 0)
        placed = []  # (top, left, bh, bw)
        for (rel, bh, bw), color in zip(shapes, palette):
            for _ in range(120):
                r0 = rng.randint(0, h - bh)
                c0 = rng.randint(0, w - bw)
                collides = False
                for (pr, pc, pbh, pbw) in placed:
                    if (r0 - (pr + pbh) < 2 and pr - (r0 + bh) < 2 and
                        c0 - (pc + pbw) < 2 and pc - (c0 + bw) < 2):
                        collides = True
                        break
                if collides:
                    continue
                for dr, dc in rel:
                    g[r0 + dr][c0 + dc] = color
                placed.append((r0, c0, bh, bw))
                break
        if len(placed) == len(shapes):     # winner + all secondaries placed
            return g

    # deterministic fallback: ring at top-left + a 2-cell secondary at bottom-right
    g = full_grid(h, w, 0)
    for dr, dc in winner_rel:
        g[dr][dc] = palette[0]
    g[h - 1][w - 2] = palette[1]
    g[h - 1][w - 1] = palette[1]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """A unique strictly-largest component whose bbox crop is non-rectangular (so
    the rule's crop is not a solid single-color block)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or seen[sr][sc]:
                continue
            stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] != 0):
                        seen[nr][nc] = True; stack.append((nr, nc))
            comps.append(cells)
    if len(comps) < 2:
        return [f"expected >=2 components, found {len(comps)}"]
    counts = sorted((len(c) for c in comps), reverse=True)
    errors = []
    if counts[0] == counts[1]:
        errors.append(f"largest cell-count is tied ({counts[:2]})")
    winner = max(comps, key=len)
    rs = [r for r, _ in winner]; cs = [c for _, c in winner]
    bh = max(rs) - min(rs) + 1; bw = max(cs) - min(cs) + 1
    if bh * bw == len(winner):
        errors.append("largest component is a solid rectangle — cropped output "
                      "would be a single-color block")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "tied_largest":
        # two components tied for largest — pick is ambiguous
        draw_rect(g, 1, 1, 2, 3, 4)
        draw_rect(g, 6, 6, 2, 3, 7)
        return g
    if name == "only_one_component":
        draw_rect(g, 3, 3, 3, 4, 5)
        return g
    if name == "all_same_size":
        # all 3 components same size — no unique largest
        draw_rect(g, 1, 1, 2, 2, 3)
        draw_rect(g, 1, 8, 2, 2, 4)
        draw_rect(g, 7, 4, 2, 2, 6)
        return g
    return g
