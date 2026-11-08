"""Generator for arc_additional_puzzles_21_set6:H39.

Rule: color-2 components with no holes become 3; hollow components
(with at least one enclosed 0-region) become 4.

Combinatorial axes (8): grid_h/w, palette_kind, num_solid, num_hollow,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_objects, all_solid, all_hollow.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect, draw_rect_outline

GENERATOR_ID = "ea56ba328a3e"
VERSION = "2.1.0"  # add multi-hole LADDERS (3/4/5 holes -> colors 6/9) -> the rule's h=3 and h>=4 branches were never exercised (gen only made h=0/1/2); canonical has h=3
TASK_ID = "ea56ba328a3e"
SUMMARY = (
    "0-bg grid with several separated color-2 components. Each "
    "component may be SOLID (no enclosed 0-regions) or have N (≥1) "
    "INTERIOR HOLES (4-conn 0-regions fully enclosed by 2-cells, "
    "not touching the grid border through 0-bg). Rule: keep only "
    "color-2 cells; compute connected components; for each component "
    "count its topological holes h; recolor its cells in the output "
    "to: h=0 → 3, h=1 → 4, h=2 → 5, h=3 → 6, h≥4 → 9. Original 2-cells "
    "are dropped (the count-based color replaces them). Empty cells "
    "stay 0."
)

# Rivals: 'output is input' refuted by demos (output has no 2s).
# 'recolor every 2 to 3' refuted by demos with ≥1 hollow component.
# 'use a single color for hollow' refuted by demos with 1-hole + 2-hole
# yielding 4 + 5. 'use the count itself as the color (1, 2)' refuted
# by demos where holes=0 gives 3 (not 0). 'count enclosed cells, not
# regions' refuted by demos with a 2-cell hole still producing color
# 4. 4 demos with components of 0, 1, 2 holes (and possibly 3) pin
# the lookup table.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "only color-2 components exist (no other non-bg colors)",
    "≥1 solid component (0 holes)",
    "≥1 hollow component with 1 hole",
    "components are separated by ≥1 bg cell (no 4-conn merging)",
    "no component touches the grid border (so its holes are correctly counted as enclosed)",
]

PALETTE_KINDS = ("default", "more_solid", "more_hollow", "balanced")
DEGENERATE_TEXTURES = ("no_objects", "all_solid", "all_hollow")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "10..26"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "10..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|more_solid|more_hollow|balanced"},
    "num_solid":      {"type": "int", "default": "2", "valid": "1..3"},
    "num_hollow":     {"type": "int", "default": "1", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|more_solid|more_hollow|balanced|no_objects|all_solid|all_hollow"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    kind = overrides.get(
        "palette_kind",
        ctx.draw_choice("palette_kind", list(PALETTE_KINDS)),
    )
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 15, 18)
        ladder_holes = [2]
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 23, 26)
        w = ctx.draw_int("grid_w", 23, 26)
        ladder_holes = [2, 3, 4, 5]
    else:
        h = ctx.draw_int("grid_h", 18, 22)
        w = ctx.draw_int("grid_w", 18, 22)
        ladder_holes = [2, 3]

    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    specs = [("solid", 0), ("hollow", 1)]
    if kind == "more_solid":
        specs.append(("solid", 0))
    elif kind == "more_hollow":
        specs.append(("hollow", 1))
    elif kind == "balanced" and difficulty == "hard":
        specs.extend([("solid", 0), ("hollow", 1)])
    specs.extend(("ladder", k) for k in ladder_holes)
    _place_components(g, specs, rng)
    return g


def _component_size(kind, n_holes):
    if kind == "solid":
        return 2, 2
    if kind == "hollow":
        return 4, 4
    return 2 * n_holes + 1, 5


def _paint_component(g, r0, c0, kind, n_holes):
    sh, sw = _component_size(kind, n_holes)
    if kind == "solid":
        draw_rect(g, r0, c0, sh, sw, 2)
        return
    draw_rect_outline(g, r0, c0, sh, sw, 2)
    if kind == "ladder":
        for k in range(1, n_holes):
            rr = r0 + 2 * k
            for c in range(c0, c0 + sw):
                g[rr][c] = 2


def _place_components(g, specs, rng):
    h, w = len(g), len(g[0])

    def footprint(r0, c0, sh, sw):
        return {(r, c)
                for r in range(r0 - 1, r0 + sh + 1)
                for c in range(c0 - 1, c0 + sw + 1)}

    def plan_once(shuffle=True):
        occupied = set()
        placements = []
        ordered = sorted(specs,
                         key=lambda s: _component_size(*s)[0] * _component_size(*s)[1],
                         reverse=True)
        for kind, n_holes in ordered:
            sh, sw = _component_size(kind, n_holes)
            candidates = [(r, c)
                          for r in range(1, h - sh)
                          for c in range(1, w - sw)]
            if shuffle:
                rng.shuffle(candidates)
            for r0, c0 in candidates:
                fp = footprint(r0, c0, sh, sw)
                if fp.isdisjoint(occupied):
                    occupied.update(fp)
                    placements.append((r0, c0, kind, n_holes))
                    break
            else:
                return None
        return placements

    placements = None
    for _ in range(80):
        placements = plan_once(shuffle=True)
        if placements is not None:
            break
    if placements is None:
        placements = plan_once(shuffle=False)
    if placements is None:
        raise RuntimeError(f"could not place {len(specs)} components in {h}x{w}")
    for r0, c0, kind, n_holes in placements:
        _paint_component(g, r0, c0, kind, n_holes)


def _color2_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _hole_count(grid, cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    seen = set()
    holes = 0
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            touches_bbox_edge = False
            while stack:
                rr, cc = stack.pop()
                if rr in (r0, r1) or cc in (c0, c1):
                    touches_bbox_edge = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (r0 <= nr <= r1 and c0 <= nc <= c1 and
                            grid[nr][nc] == 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if not touches_bbox_edge:
                holes += 1
    return holes


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    colors = {v for row in grid for v in row}
    if not colors <= {0, 2}:
        errors.append(f"expected only colors 0 and 2, got {sorted(colors)}")
    comps = _color2_components(grid)
    if not comps:
        errors.append("expected at least one color-2 component")
        return errors
    border_cells = {(r, c) for comp in comps for r, c in comp
                    if r in (0, h - 1) or c in (0, w - 1)}
    if border_cells:
        errors.append("color-2 component touches border; holes would leak to background")
    hole_counts = [_hole_count(grid, comp) for comp in comps]
    if 0 not in hole_counts:
        errors.append(f"expected at least one solid component with 0 holes; got {hole_counts}")
    if 1 not in hole_counts:
        errors.append(f"expected at least one hollow component with 1 hole; got {hole_counts}")
    if difficulty in (None, "hard") and not any(hc >= 2 for hc in hole_counts):
        errors.append(f"expected at least one multi-hole ladder component; got {hole_counts}")
    return errors

def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_objects":
        return g
    if name == "all_solid":
        # only solid blocks — no hollow components, rule produces only 3s
        draw_rect(g, 1, 1, 3, 3, 2)
        draw_rect(g, h - 4, w - 4, 3, 3, 2)
        draw_rect(g, h - 4, 1, 2, 2, 2)
        return g
    if name == "all_hollow":
        # only hollow frames — no solid components, rule produces only 4s
        draw_rect_outline(g, 1, 1, 4, 4, 2)
        draw_rect_outline(g, h - 5, w - 5, 4, 4, 2)
        return g
    return g
