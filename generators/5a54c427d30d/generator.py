"""Generator for puzzle 54db823b.

Rule: among multi-color 8-connected components, erase the one with the
FEWEST 9-cells (replace with 0).

Combinatorial axes (8): grid_h/w, n_objs, object_shape_kind,
nine_count_distribution, palette_size, object_size_range,
inter_object_margin, decoy_density.
Degenerates: single_object, ties_for_min, no_nines.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "5a54c427d30d"
VERSION = "2.1.0"  # all-blank fix: blocks were placed only edge-margined (margin), not separated (padding), so touching blocks MERGED under the rule's 8-connectivity into ONE object -> erased -> blank grid. Now pass padding for real inter-object spacing + a valid 2-block fallback.
TASK_ID = "5a54c427d30d"
SUMMARY = (
    "0-bg grid (h, w~14-18) "
    "with 2-4 MULTI-COLOR "
    "8-CONNECTED COMPONENTS, "
    "each a SOLID "
    "RECTANGULAR BLOCK (3×3, "
    "4×4, or rect from "
    "size_range small/"
    "medium/large) in a "
    "DISTINCT MAJOR COLOR "
    "drawn from a palette "
    "excluding {0, 9}. EACH "
    "BLOCK has 1-N EMBEDDED "
    "COLOR-9 CELLS at random "
    "positions within its "
    "bbox. The NINE-COUNT "
    "per component is "
    "DISTINCT (chosen from "
    "ascending/wide-spread/"
    "tight-spread "
    "distributions), so "
    "MINIMUM is UNIQUE. "
    "Components separated "
    "by inter-object "
    "margin ≥1. Rule "
    "(ERASE THE COMPONENT "
    "WITH FEWEST 9-CELLS): "
    "find every multi-"
    "color 8-CONNECTED "
    "COMPONENT (each "
    "block + its embedded "
    "9s counts as one). "
    "COUNT the 9-cells in "
    "each. Identify the "
    "component with the "
    "UNIQUE MINIMUM "
    "9-count. ERASE (paint "
    "all its cells to 0). "
    "Other components stay "
    "unchanged. Net: the "
    "block with the fewest "
    "9-dots gets wiped; "
    "all others survive."
)

# Rivals: 'output is input' refuted by demos (one component erased).
# 'erase the largest' refuted by demos where most/fewest by 9s !=
# size order. 'erase by area only' refuted by demos with same-size
# components having different 9-counts. 'erase the most 9s' refuted
# by demos. 3 demos with ≥2 components of distinct 9-counts cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=2 multi-color 8-connected components (so the choice is real)",
    "each component has >=1 cell of color 9",
    "components have a UNIQUE minimum 9-cell count (no tie at min)",
    "components separated by margin >= 1",
]

OBJECT_SHAPE_KINDS = ("rect", "block_3x3", "block_4x4", "mixed")
NINE_DISTRIBUTIONS = ("ascending", "wide_spread", "tight_spread")
DEGENERATE_TEXTURES = ("single_object", "ties_for_min", "no_nines")
HELPFUL_TEXTURES = OBJECT_SHAPE_KINDS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":              {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_objs":              {"type": "int", "default": "rng 2..4",   "valid": "2..5"},
    "object_shape_kind":   {"type": "str", "default": "rng helpful",
                            "valid": "rect|block_3x3|block_4x4|mixed"},
    "nine_count_distribution": {"type": "str", "default": "rng helpful",
                                "valid": "ascending|wide_spread|tight_spread"},
    "palette_size":        {"type": "int", "default": "= n_objs",   "valid": "2..7"},
    "object_size_range":   {"type": "str", "default": "rng small|medium|large",
                            "valid": "small|medium|large"},
    "inter_object_margin": {"type": "int", "default": "2",          "valid": "1..3"},
    "texture":             {"type": "str", "default": "alias for object_shape_kind",
                            "valid": "rect|block_3x3|block_4x4|mixed|single_object|ties_for_min|no_nines"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 12, 14, 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 18, 22, 3, 4
    else:
        h_lo, h_hi, n_lo, n_hi = 14, 18, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_objs = int(overrides.get("n_objs", ctx.draw_int("n_objs", n_lo, n_hi)))
    n_objs = max(2, min(4, n_objs))
    palette = list(ctx.draw_distinct_colors("palette", n=n_objs, exclude={0, 9}))
    shape_kind = (overrides.get("texture") or overrides.get("object_shape_kind")
                  or ctx.draw_choice("object_shape_kind", list(OBJECT_SHAPE_KINDS)))
    nine_dist = (overrides.get("nine_count_distribution")
                 or ctx.draw_choice("nine_count_distribution", list(NINE_DISTRIBUTIONS)))
    size_range = overrides.get("object_size_range",
                               ctx.draw_choice("object_size_range",
                                               ["small", "medium", "large"]))
    margin = int(overrides.get("inter_object_margin", 2))
    margin = max(1, min(3, margin))
    s_lo, s_hi = {"small": (3, 3), "medium": (3, 4), "large": (4, 5)}[size_range]
    nine_counts = _draw_nine_counts(nine_dist, n_objs, rng)
    g = full_grid(h, w, 0)
    placed = 0
    for i, n9 in enumerate(nine_counts):
        rh, rw = _draw_shape(shape_kind, s_lo, s_hi, rng)
        cells = normalize(rect_cells(rh, rw))
        # padding>=1 is ESSENTIAL: the rule finds multi-color objects with
        # 8-CONNECTIVITY, so two blocks that merely TOUCH merge into ONE object.
        # With a single object the rule erases it -> all-blank output. `margin`
        # only pads the grid edge; `padding` keeps blocks apart. Without it,
        # touching blocks collapsed to one object and the whole grid went blank.
        pos = place_no_overlap(rng, g, cells, palette[i], bg=0,
                               margin=1, padding=max(1, margin), max_tries=60)
        if pos is None:
            continue
        rr, rc = pos
        local_cells = [(rr + dr, rc + dc) for dr in range(rh) for dc in range(rw)]
        rng.shuffle(local_cells)
        for r, c in local_cells[:min(n9, len(local_cells))]:
            g[r][c] = 9
        placed += 1
    if placed < 2:
        return _fallback_two_blocks(h, w, palette)
    return g


def _fallback_two_blocks(h, w, palette):
    """Guaranteed-valid instance: two well-separated 2x2 blocks with DISTINCT
    9-counts (1 vs 2) so the min is unique and erasing it leaves content."""
    g = full_grid(h, w, 0)
    c1 = palette[0] if palette else 1
    c2 = palette[1] if len(palette) > 1 else (c1 % 8) + 1
    # block A (1 nine) at (1,1); block B (2 nines) at (1,5) — gap of 2 cols
    g[1][1] = c1; g[1][2] = c1; g[2][1] = c1; g[2][2] = 9
    g[1][5] = c2; g[1][6] = 9; g[2][5] = 9; g[2][6] = c2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 multi-color 8-connected objects with a UNIQUE minimum 9-count, so the
    rule erases exactly one and leaves the rest (output is non-blank)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h = len(grid); w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    seen = set(); nine_counts = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 0 and (sr, sc) not in seen:
                n9 = 0; stack = [(sr, sc)]; seen.add((sr, sc))
                while stack:
                    r, c = stack.pop()
                    if grid[r][c] == 9:
                        n9 += 1
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                                    and (nr, nc) not in seen):
                                seen.add((nr, nc)); stack.append((nr, nc))
                nine_counts.append(n9)
    problems = []
    if len(nine_counts) < 2:
        problems.append(f"need >=2 multicolor objects, found {len(nine_counts)}")
    if any(n == 0 for n in nine_counts):
        problems.append("a component has no 9-cells")
    if nine_counts and nine_counts.count(min(nine_counts)) != 1:
        problems.append("minimum 9-count is tied (no unique object to erase)")
    return problems


def _draw_shape(kind, s_lo, s_hi, rng):
    if kind == "block_3x3":
        return 3, 3
    if kind == "block_4x4":
        return 4, 4
    if kind == "rect":
        return rng.randint(s_lo, s_hi), rng.randint(s_lo, s_hi)
    return rng.randint(s_lo, s_hi), rng.randint(s_lo, s_hi)


def _draw_nine_counts(dist, n_objs, rng):
    if dist == "ascending":
        start = rng.randint(1, 3)
        return [start + i for i in range(n_objs)]
    if dist == "tight_spread":
        base = rng.randint(2, 4)
        return sorted(rng.sample(range(base, base + n_objs + 2), n_objs))
    # wide_spread
    return sorted(rng.sample(range(1, 1 + n_objs * 3), n_objs))


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "single_object":
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        for r in range(3, 6):
            for c in range(3, 6):
                g[r][c] = color
        g[4][4] = 9
        return g
    if name == "ties_for_min":
        color1 = rng.choice([1, 2, 3, 4])
        color2 = rng.choice([5, 6, 7, 8])
        for r in range(3, 6):
            for c in range(3, 6):
                g[r][c] = color1
        g[3][3] = 9; g[3][5] = 9
        for r in range(8, 11):
            for c in range(8, 11):
                g[r][c] = color2
        g[8][8] = 9; g[8][10] = 9
        return g
    if name == "no_nines":
        color1, color2 = rng.choice([1, 2, 3]), rng.choice([4, 5, 6])
        for r in range(3, 6):
            for c in range(3, 6):
                g[r][c] = color1
        for r in range(8, 11):
            for c in range(8, 11):
                g[r][c] = color2
        return g
    return g
