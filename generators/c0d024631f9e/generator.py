"""Generator for ARC task 3194b014.

Rule: find the 3rd-most-common non-bg color (by descending count).
Output is a 3 × 3 grid filled with that color.

Combinatorial axes (8):
  * grid_h / grid_w     — outer canvas size
  * n_colors            — distinct non-bg colors (≥3)
  * count_progression   — linear / exponential / random_distinct
                          (controls how the counts are spaced)
  * placement_pattern   — random / clustered / striped / quadrants /
                          banded
  * bg_density          — fraction of bg cells
  * gap_between_ranks   — minimum count difference between adjacent ranks
                          (ensures stable rank order)
  * 3rd_color_pick      — which color gets the rank-3 slot
                          (random / specific_color)
  * caller-opt-in degenerates: ties_for_3rd (rule's pick ambiguous),
                              fewer_than_3_colors (rule fails),
                              all_equal_counts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c0d024631f9e"
# 1.2.0: make the promised strict frequency ranking executable.  The old
# count cap could collapse the tail to ties (e.g. counts 9, 4, 1, 1), making
# the "3rd-most-common colour" ambiguous even though self_check only required
# >=3 colours.  Counts are now synthesized from a strictly-descending baseline
# and self_check rejects ties.  The 3x3 solid output remains intrinsic.
VERSION = "1.2.0"
TASK_ID = "c0d024631f9e"
SUMMARY = "Grid with distinct color frequencies; rule outputs 3 × 3 of the 3rd-ranked color."

INVARIANTS = [
    "background is 0",
    "≥3 distinct non-bg colors",
    "color counts are strictly distinct so rank-3 is unambiguous",
]

PROGRESSIONS = ("linear", "exponential", "random_distinct")
PLACEMENTS = ("random", "clustered", "striped", "quadrants", "banded")
DEGENERATE_TEXTURES = ("ties_for_3rd", "fewer_than_3_colors", "all_equal_counts")
HELPFUL_TEXTURES = ("random",)

AXES = {
    "grid_h":             {"type": "int", "default": "rng 12..20", "valid": "8..24"},
    "grid_w":             {"type": "int", "default": "rng 12..20", "valid": "8..24"},
    "n_colors":           {"type": "int", "default": "rng 3..6", "valid": "3..9"},
    "count_progression":  {"type": "str", "default": "rng helpful",
                           "valid": "linear|exponential|random_distinct"},
    "placement_pattern":  {"type": "str", "default": "rng random",
                           "valid": "random|clustered|striped|quadrants|banded"},
    "bg_density":         {"type": "float", "default": "rng 0.1..0.4", "valid": "0..0.8"},
    "gap_between_ranks":  {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "third_color_pick":   {"type": "str", "default": "rng random|specific",
                           "valid": "random|specific"},
    "texture":            {"type": "str", "default": "alias for placement_pattern",
                           "valid": "random|clustered|striped|quadrants|banded|ties_for_3rd|fewer_than_3_colors|all_equal_counts"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 12, 16, 3, 4
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 18, 24, 5, 7
    else:
        h_lo, h_hi, n_lo, n_hi = 14, 20, 3, 6
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_colors = int(overrides.get("n_colors", ctx.draw_int("n_colors", n_lo, n_hi)))
    n_colors = max(3, min(9, n_colors))
    progression = overrides.get("count_progression",
                                ctx.draw_choice("count_progression", list(PROGRESSIONS)))
    placement = overrides.get("placement_pattern",
                              ctx.draw_choice("placement_pattern", list(HELPFUL_TEXTURES)))
    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.1, 0.4)))
    gap = int(overrides.get("gap_between_ranks",
                            ctx.draw_int("gap_between_ranks", 2, 5)))
    palette = list(ctx.draw_distinct_colors("palette", n=n_colors, exclude={0}))
    counts = _make_counts(progression, n_colors, h * w, bg_d, gap, rng)
    g = _place_with_pattern(placement, h, w, palette, counts, rng)
    return g


def _make_counts(progression, n_colors, total, bg_d, gap, rng):
    """Return a strictly descending count vector.

    The canonical rule sorts colors by frequency and takes index 2.  A tie at
    that rank turns the task into an arbitrary implementation detail, so the
    generator must preserve strict counts even after fitting the requested
    background density/canvas size.
    """
    gap = max(1, int(gap))
    avail = max(n_colors, int(total * (1 - bg_d)))

    # Minimum strictly-descending ladder with the requested gap:
    # n=4,gap=2 -> [7,5,3,1].
    mins = [1 + gap * (n_colors - i - 1) for i in range(n_colors)]
    if sum(mins) > avail:
        # Very small override grids cannot host the requested gap.  Keep the
        # rank order strict rather than silently introducing ambiguity.
        gap = 1
        mins = [n_colors - i for i in range(n_colors)]
        avail = max(avail, sum(mins))

    extra = max(0, avail - sum(mins))
    counts = list(mins)

    if progression == "linear":
        # Add the same base to every rank, with any remainder on higher ranks.
        base, rem = divmod(extra, n_colors)
        counts = [c + base + (1 if i < rem else 0) for i, c in enumerate(counts)]
    elif progression == "exponential":
        # Put more mass on high ranks while preserving the strict tail.
        weights = [2 ** (n_colors - i - 1) for i in range(n_colors)]
        denom = sum(weights)
        adds = [(extra * w) // denom for w in weights]
        leftover = extra - sum(adds)
        for i in range(leftover):
            adds[i % n_colors] += 1
        counts = [c + a for c, a in zip(counts, adds)]
        # Adding to low ranks can narrow a gap; repair from the bottom up.
        for i in range(n_colors - 2, -1, -1):
            counts[i] = max(counts[i], counts[i + 1] + gap)
    else:  # random_distinct
        # Randomly distribute surplus, then repair strictness.
        for _ in range(extra):
            counts[rng.randrange(n_colors)] += 1
        for i in range(n_colors - 2, -1, -1):
            counts[i] = max(counts[i], counts[i + 1] + 1)

    # Final clamp: if a repair overshot the available budget, fall back to the
    # minimal strict ladder.  This is rare and only affects tiny override grids.
    if sum(counts) > total:
        counts = [n_colors - i for i in range(n_colors)]
    return counts


def _place_with_pattern(pattern, h, w, palette, counts, rng):
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(h) for c in range(w)]
    if pattern == "random":
        rng.shuffle(cells)
    elif pattern == "clustered":
        cr = rng.randint(0, h - 1); cc = rng.randint(0, w - 1)
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
    elif pattern == "striped":
        cells = [(r, c) for r in range(0, h, 1) for c in range(w)]
        # Group by row: cells of color i go to row i
    elif pattern == "quadrants":
        cells.sort(key=lambda rc: (rc[0] >= h // 2, rc[1] >= w // 2))
    elif pattern == "banded":
        cells.sort(key=lambda rc: rc[0])
    cursor = 0
    n = len(palette)
    for idx, (color, count) in enumerate(zip(palette, counts)):
        # reserve >=1 cell for every still-unplaced colour so a large top count
        # can't consume the whole grid and starve the rank-3 colour (the rule
        # needs >=3 distinct colours present)
        remaining_after = n - idx - 1
        room = len(cells) - cursor - remaining_after
        place = max(1, min(count, room)) if room >= 1 else 0
        for _ in range(place):
            if cursor >= len(cells):
                break
            r, c = cells[cursor]
            g[r][c] = color
            cursor += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """The rule needs an unambiguous rank-3 colour: at least three non-bg
    colours and no frequency ties.  (The single-colour 3x3 OUTPUT is intrinsic
    to this rule, not an all-background defect.)"""
    from collections import Counter
    counts = Counter(v for row in grid for v in row if v != 0)
    if len(counts) < 3:
        return [f"only {len(counts)} non-bg colors (rule has no rank-3)"]
    freqs = list(counts.values())
    if len(freqs) != len(set(freqs)):
        return [f"frequency tie makes rank-3 ambiguous: {counts.most_common()}"]

    # Canonical examples are salted fields with many same-colour components, not
    # row bands or quadrant blobs.  Count 4-connected non-bg components using 0
    # as the background.
    h, w = len(grid), len(grid[0])
    seen = set(); components = 0
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] == 0:
                continue
            components += 1
            color = grid[sr][sc]
            stack = [(sr, sc)]; seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
    if components < 20:
        return [f"too few same-colour components for canonical salted field: {components}"]
    return []


def _draw_from_degenerate(name, h, w, rng):
    palette = list(range(1, 10))
    rng.shuffle(palette)
    g = full_grid(h, w, 0)
    if name == "ties_for_3rd":
        # 4 colors with ranks: 10, 7, 5, 5 — rank-3 and rank-4 tie.
        positions = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(positions)
        for color, n in zip(palette[:4], [10, 7, 5, 5]):
            for _ in range(n):
                if not positions: break
                r, c = positions.pop()
                g[r][c] = color
        return g
    if name == "fewer_than_3_colors":
        # Only 2 distinct non-bg colors — rule has no rank-3.
        positions = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(positions)
        for color in palette[:2]:
            for _ in range(8):
                if not positions: break
                r, c = positions.pop()
                g[r][c] = color
        return g
    if name == "all_equal_counts":
        # 4 colors with equal counts — ambiguous rank.
        positions = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(positions)
        for color in palette[:4]:
            for _ in range(5):
                if not positions: break
                r, c = positions.pop()
                g[r][c] = color
        return g
    return g
