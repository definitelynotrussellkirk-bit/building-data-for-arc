"""Generator for 9f4676d350e7 — concentric-palette transfer.

Rule: given a multi-layered colored template shape (left) and a
single-colored target shape (right, all color-1), the output colors
the target shape's onion layers with the template's layer palette
(outermost layer gets outermost color, etc.).

Canonical pair structure:
  Input:  [colored template] ... gap ... [target blob, all 1s]
  Output: template unchanged; target colored by palette

Template kinds: concentric-square, concentric-diamond
Target kinds:   solid-rectangle, solid-diamond

Combinatorial axes (7): template_kind, target_kind, n_layers,
palette, target_h, target_w, gap.
Degenerates: single_layer (only 1 layer in template), tiny_target
  (1x1 target), all_same_palette (all palette colors identical).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9f4676d350e7"
VERSION = "1.2.0"
TASK_ID = "9f4676d350e7"

SUMMARY = (
    "Colored concentric template + uncolored target; "
    "output colors the target's onion layers with the template palette."
)

INVARIANTS = [
    "background is 0",
    "exactly two non-zero connected components in input",
    "left component = concentric-layer template (colors 1-8, never 9)",
    "right component = solid blob of color 1",
    "gap >= 2 between components",
]

AXES = {
    "template_kind": {
        "type": "str", "default": "rng square|diamond",
        "valid": "square|diamond",
    },
    "target_kind": {
        "type": "str", "default": "rng rect|diamond",
        "valid": "rect|diamond",
    },
    "n_layers": {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette":  {"type": "str", "default": "rng", "valid": "any 2..8 non-9 color list"},
    "target_h": {"type": "int", "default": "rng 3..7", "valid": "1..10"},
    "target_w": {"type": "int", "default": "rng 3..7", "valid": "1..10"},
    "gap":      {"type": "int", "default": "rng 2..4", "valid": "2..6"},
}

DEGENERATE_TEXTURES = ("single_layer", "tiny_target", "all_same_palette")


# ---------------------------------------------------------------------------
# Template builders
# ---------------------------------------------------------------------------

def _concentric_square(n_layers, palette):
    """Return a (2n-1)×(2n-1) grid: concentric square rings.

    palette[0] = outermost ring, palette[-1] = center cell.
    """
    size = 2 * n_layers - 1
    g = full_grid(size, size, 0)
    center = n_layers - 1
    for i, color in enumerate(palette):
        dist = n_layers - 1 - i  # outermost has largest dist
        for r in range(size):
            for c in range(size):
                if max(abs(r - center), abs(c - center)) == dist:
                    g[r][c] = color
    return g


def _concentric_diamond(n_layers, palette):
    """Return a (2n-1)×(2n-1) grid: concentric diamond rings.

    palette[0] = outermost ring, palette[-1] = center cell.
    """
    size = 2 * n_layers - 1
    g = full_grid(size, size, 0)
    center = n_layers - 1
    for i, color in enumerate(palette):
        dist = n_layers - 1 - i
        for r in range(size):
            for c in range(size):
                if abs(r - center) + abs(c - center) == dist:
                    g[r][c] = color
    return g


# ---------------------------------------------------------------------------
# Target builders (all cells = color 1)
# ---------------------------------------------------------------------------

def _solid_rect(h, w, color=1):
    return [[color] * w for _ in range(h)]


def _solid_diamond(n, color=1):
    """Solid diamond blob of radius n (Manhattan distance < n from center).

    Returns a (2n-1)×(2n-1) grid.
    """
    size = 2 * n - 1
    center = n - 1
    g = full_grid(size, size, 0)
    for r in range(size):
        for c in range(size):
            if abs(r - center) + abs(c - center) < n:
                g[r][c] = color
    return g


# ---------------------------------------------------------------------------
# Grid composition
# ---------------------------------------------------------------------------

def _paste(canvas, sub, r0, c0):
    """Paste non-zero cells of sub into canvas at offset (r0, c0)."""
    for dr, row in enumerate(sub):
        for dc, v in enumerate(row):
            if v:
                canvas[r0 + dr][c0 + dc] = v


def _compose(template, target, gap, margin=2):
    """Build the full input grid: template (left) ... gap ... target (right)."""
    th, tw = len(template), len(template[0])
    tt_h, tt_w = len(target), len(target[0])
    grid_h = max(th, tt_h) + 2 * margin
    grid_w = tw + gap + tt_w + 2 * margin
    g = full_grid(grid_h, grid_w, 0)
    # Place template: vertically centered, left side
    tr0 = (grid_h - th) // 2
    tc0 = margin
    _paste(g, template, tr0, tc0)
    # Place target: vertically centered, right side
    tg_r0 = (grid_h - tt_h) // 2
    tg_c0 = margin + tw + gap
    _paste(g, target, tg_r0, tg_c0)
    return g


# ---------------------------------------------------------------------------
# Main generate
# ---------------------------------------------------------------------------

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index,
        version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )

    texture = overrides.get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return _draw_degenerate(texture)

    rng = ctx.draw_rng("layout")

    # --- n_layers ---
    if difficulty == "easy":
        n_layers = ctx.draw_int("n_layers", 2, 3)
    elif difficulty == "hard":
        n_layers = ctx.draw_int("n_layers", 3, 5)
    else:
        n_layers = ctx.draw_int("n_layers", 2, 4)

    # --- palette (all distinct, in range 1-8, never 9) ---
    pool = [1, 2, 3, 4, 5, 6, 7, 8]
    palette = rng.sample(pool, n_layers)

    # --- template kind ---
    template_kind = overrides.get("template_kind", rng.choice(["square", "diamond"]))
    if template_kind == "square":
        template = _concentric_square(n_layers, palette)
    else:
        template = _concentric_diamond(n_layers, palette)

    # --- target kind + size ---
    target_kind = overrides.get("target_kind", rng.choice(["rect", "diamond"]))
    if target_kind == "rect":
        if difficulty == "easy":
            tr_h = ctx.draw_int("target_h", 3, 5)
            tr_w = ctx.draw_int("target_w", 3, 5)
        elif difficulty == "hard":
            tr_h = ctx.draw_int("target_h", 5, 8)
            tr_w = ctx.draw_int("target_w", 5, 8)
        else:
            tr_h = ctx.draw_int("target_h", 3, 7)
            tr_w = ctx.draw_int("target_w", 3, 7)
        target = _solid_rect(tr_h, tr_w)
    else:
        if difficulty == "easy":
            tr_n = ctx.draw_int("target_n", 2, 3)
        elif difficulty == "hard":
            tr_n = ctx.draw_int("target_n", 3, 5)
        else:
            tr_n = ctx.draw_int("target_n", 2, 4)
        target = _solid_diamond(tr_n)

    gap = ctx.draw_int("gap", 2, 4)
    return _compose(template, target, gap)


# ---------------------------------------------------------------------------
# Degenerate modes (for branch coverage)
# ---------------------------------------------------------------------------

def _draw_degenerate(name):
    margin = 2
    if name == "single_layer":
        # Template has only 1 layer (just a colored blob, no rings).
        template = [[3, 3, 3], [3, 3, 3], [3, 3, 3]]
        target = _solid_rect(3, 4)
        return _compose(template, target, gap=3)
    if name == "tiny_target":
        # Target is 1x1 — the rule trivially colors it with the outermost palette color.
        template = _concentric_square(2, [2, 5])
        target = [[1]]
        return _compose(template, target, gap=2)
    if name == "all_same_palette":
        # All palette entries are the same color — output target is uniform.
        template = _concentric_square(3, [4, 4, 4])
        target = _solid_rect(5, 4)
        return _compose(template, target, gap=3)
    # Fallback
    template = _concentric_square(2, [2, 7])
    target = _solid_rect(4, 4)
    return _compose(template, target, gap=2)


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------

def self_check(grid, *, difficulty=None, meta=None):
    """Verify structural invariants of generated inputs."""
    errors = []
    h, w = len(grid), len(w := grid[0]) if grid else (0, 0)
    h, w = len(grid), (len(grid[0]) if grid else 0)

    # All values in 0..9
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if not (0 <= v <= 9):
                errors.append(f"cell ({r},{c}) = {v} out of range")

    # Color 9 must NOT appear (excluded by rule's keep-cell? filter)
    nines = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if nines:
        errors.append(f"color 9 found at {nines[:3]} — rule excludes it, would merge components")

    # Exactly 2 connected components of non-zero cells (using BFS, 4-connectivity)
    visited = [[False] * w for _ in range(h)]
    components = []

    def bfs(sr, sc):
        queue = [(sr, sc)]
        visited[sr][sc] = True
        cells = [(sr, sc)]
        while queue:
            r, c = queue.pop()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] != 0:
                    visited[nr][nc] = True
                    queue.append((nr, nc))
                    cells.append((nr, nc))
        return cells

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                components.append(bfs(r, c))

    if len(components) != 2:
        errors.append(f"expected exactly 2 components, got {len(components)}")
        return errors  # further checks are meaningless

    # Sort by leftmost column
    components.sort(key=lambda cells: min(c for _, c in cells))
    template_cells, target_cells = components[0], components[1]

    # Template (left) must have 2+ distinct colors
    t_colors = set(grid[r][c] for r, c in template_cells)
    if len(t_colors) < 2:
        errors.append(f"template has only {len(t_colors)} distinct color(s); expected 2+")

    # Target (right) must be all one color
    tg_colors = set(grid[r][c] for r, c in target_cells)
    if len(tg_colors) != 1:
        errors.append(f"target has {len(tg_colors)} colors; expected exactly 1")

    # Gap: no non-zero cell in the column range between template and target
    t_max_col = max(c for _, c in template_cells)
    tg_min_col = min(c for _, c in target_cells)
    gap = tg_min_col - t_max_col - 1
    if gap < 2:
        errors.append(f"gap between components is {gap} columns; expected >= 2")

    return errors
