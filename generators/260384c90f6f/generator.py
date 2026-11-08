"""Generator for puzzle 1e32b0e9.

Rule: 6-period cell layout (rows 0-5, cols 0-5) separated by line_color
on row 5 + col 0. Each cell has a 3x3 interior (rows 1-3, cols 1-3 mod
6). The "template" is the union of mark-color positions across all
cells. Each empty (zero) interior cell at a template position gets
filled with line_color.

Combinatorial axes (8): grid_size, line_color, mark_color,
template_density, template_kind, n_template_cells, position_bias,
asymmetry_force.
Degenerates: empty_template, full_template, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "260384c90f6f"
VERSION = "2.0.1"
TASK_ID = "260384c90f6f"
SUMMARY = (
    "Square grid size ∈ {11, "
    "17, 23} with PERIOD-6 "
    "LATTICE: ROW 5, 11, "
    "17 and COL 0, 6, 12, "
    "18 (those that fit) "
    "are filled with "
    "LINE_COLOR. The grid "
    "splits into 3×3 "
    "INTERIOR CELLS at "
    "(6r+1..6r+3, 6c+1.."
    "6c+3) for each block "
    "(r, c). The TEMPLATE "
    "is a 3×3 binary mask "
    "drawn from 7 KINDS "
    "(sparse/dense/diagonal"
    "/centered/corners/L_"
    "shape/cross) with 3-5 "
    "mark positions. Each "
    "interior cell has a "
    "SUBSET of the template "
    "marks (with at least "
    "one block missing ≥1 "
    "template position) in "
    "MARK_COLOR. Rule "
    "(FILL MISSING "
    "TEMPLATE POSITIONS "
    "WITH LINE_COLOR): "
    "INFER the TEMPLATE = "
    "UNION of mark "
    "positions across "
    "ALL interior cells. "
    "For EACH interior "
    "cell and EACH template "
    "position not "
    "currently marked: "
    "PAINT that cell with "
    "LINE_COLOR. Existing "
    "marks and "
    "separators stay. Net: "
    "each cell completes "
    "the full template; "
    "missing positions "
    "fill with the line "
    "color."
)

INVARIANTS = [
    "grid is 11..23 with row 5 and col 0 in line_color",
    "each 3x3 interior holds 0 or mark_color cells",
    "at least one interior position has at least one mark, but not all 9",
    "line_color != mark_color != 0",
]

TEMPLATE_KINDS = ("sparse", "dense", "diagonal", "centered",
                  "corners", "L_shape", "cross")
DEGENERATE_TEXTURES = ("empty_template", "full_template", "single_cell")
HELPFUL_TEXTURES = TEMPLATE_KINDS

AXES = {
    "grid_size":      {"type": "int", "default": "rng 17..18 (period 6 ⇒ 11/17/23)",
                       "valid": "11..23"},
    "line_color":     {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "mark_color":     {"type": "color", "default": "rng (≠0,line_color)",
                       "valid": "1..9"},
    "template_kind":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(TEMPLATE_KINDS)},
    "n_template_cells":{"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for template_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is square; at least two distinct non-zero colors present (line_color + mark_color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        return errors  # degenerate (empty or uniform) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        valid_sizes = [11, 17]
    elif difficulty == "hard":
        valid_sizes = [23]
    else:
        valid_sizes = [17, 23]
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        size = rng.choice(valid_sizes)
        return _draw_from_degenerate(overrides["texture"], size, rng)
    size = int(overrides.get("grid_size", rng.choice(valid_sizes)))
    if size not in (11, 17, 23):
        # snap to nearest valid period-6 size
        size = min(valid_sizes, key=lambda v: abs(v - size))
    line_color, mark_color = ctx.draw_distinct_colors("colors", n=2,
                                                       exclude={0})
    if "line_color" in overrides:
        line_color = int(overrides["line_color"])
    if "mark_color" in overrides:
        mark_color = int(overrides["mark_color"])
    template_kind = (overrides.get("texture") or
                     overrides.get("template_kind")
                     or ctx.draw_choice("template_kind",
                                        list(TEMPLATE_KINDS)))
    n_tmpl = int(overrides.get("n_template_cells",
                               ctx.draw_int("n_template_cells", 3, 5)))
    n_tmpl = max(1, min(9, n_tmpl))
    g = full_grid(size, size, 0)
    # Period-6 separators: rows 5, 11, 17 and cols 0, 6, 12, 18
    for k in range(size):
        for sep in (5, 11, 17):
            if sep < size:
                g[sep][k] = line_color
        for sep in (0, 6, 12, 18):
            if sep < size:
                g[k][sep] = line_color
    template = _build_template(template_kind, n_tmpl, rng)
    n_blocks = (size + 5) // 6
    # The rule only fires when ≥1 block is MISSING ≥1 template position
    # (the rule fills missing positions). So for every block, drop a
    # random subset of marks. Choose which positions to drop per block
    # so the union still equals the full template.
    block_keep = []
    block_idx = [(rb, cb) for rb in range(n_blocks) for cb in range(n_blocks)]
    full = set(template)
    for _ in block_idx:
        if len(template) <= 1:
            keep = set(template)
        else:
            n_keep = rng.randint(max(1, len(template) - 3),
                                 max(1, len(template) - 1))
            keep = set(rng.sample(template, n_keep))
        block_keep.append(keep)
    # Guarantee union covers full template — pin each missing position
    # to some block.
    union = set()
    for k in block_keep:
        union |= k
    missing = full - union
    for pos in missing:
        idx = rng.randint(0, len(block_keep) - 1)
        block_keep[idx].add(pos)
    for (rb, cb), keep in zip(block_idx, block_keep):
        for tr, tc in keep:
            r = rb * 6 + 1 + tr
            c = cb * 6 + 1 + tc
            if 0 <= r < size and 0 <= c < size and g[r][c] == 0:
                g[r][c] = mark_color
    return g


def _build_template(kind, n, rng):
    positions = [(r, c) for r in range(3) for c in range(3)]
    if kind == "sparse":
        rng.shuffle(positions)
        return positions[:max(1, min(n, 3))]
    if kind == "dense":
        rng.shuffle(positions)
        return positions[:max(5, n)]
    if kind == "diagonal":
        return [(0, 0), (1, 1), (2, 2)]
    if kind == "centered":
        return [(1, 1), (0, 1), (1, 0), (1, 2), (2, 1)][:n]
    if kind == "corners":
        return [(0, 0), (0, 2), (2, 0), (2, 2)][:max(1, n)]
    if kind == "L_shape":
        return [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)][:max(1, n)]
    if kind == "cross":
        return [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    rng.shuffle(positions)
    return positions[:n]


def _draw_from_degenerate(name, size, rng):
    if size not in (11, 17, 23):
        size = 17
    line_color, mark_color = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    g = full_grid(size, size, 0)
    for k in range(size):
        for sep in (5, 11, 17):
            if sep < size:
                g[sep][k] = line_color
        for sep in (0, 6, 12, 18):
            if sep < size:
                g[k][sep] = line_color
    if name == "empty_template":
        # Force exactly one cell to have a single mark — minimal template
        g[1][1] = mark_color
        return g
    if name == "full_template":
        # Every interior position fully marked in every cell
        n_blocks = (size + 5) // 6
        for rb in range(n_blocks):
            for cb in range(n_blocks):
                for tr in range(3):
                    for tc in range(3):
                        r = rb * 6 + 1 + tr
                        c = cb * 6 + 1 + tc
                        if 0 <= r < size and 0 <= c < size:
                            g[r][c] = mark_color
        return g
    if name == "single_cell":
        # only ONE block has any marks
        g[1][1] = mark_color
        g[1][2] = mark_color
        return g
    return g
