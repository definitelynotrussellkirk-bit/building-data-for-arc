"""Generator for v3_rich_schema:medium_05_stamp_exemplar_at_targets — stamp color-3 exemplar at color-1 markers.

Rule: a color-3 exemplar shape (3-5 cells) + 1-3 single-cell color-1 markers.
The exemplar's relative offsets are stamped (in color 3) at each marker.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_exemplar (no color-3 motif → rule has no template);
no_targets (exemplar present but no target markers → rule has no
destinations); single_cell_exemplar (exemplar is just 1 cell → all
stamps trivial, no shape contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "761a24339019"
VERSION = "2.0.2"  # FIX: reserve each target's complete translated motif footprint so generated stamps never clip, overwrite source content, or overlap another target stamp.
TASK_ID = "761a24339019"

SUMMARY = ("An EXEMPLAR blob (a colour-1 anchor 4-connected to a colour-3 shape) plus isolated "
           "colour-1 TARGET markers. Rule: stamp the exemplar's colour-3 shape (offset from the "
           "anchor) at every target. Exemplar shape, target count and positions vary.")

INVARIANTS = [
    "background is 0",
    "one exemplar blob: a colour-1 anchor 4-adjacent to a connected colour-3 motif (one region with both colours)",
    "1-3 isolated colour-1 target markers elsewhere",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_exemplar", "no_targets", "single_cell_exemplar")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":            {"type": "int", "default": "rng 10..12", "valid": "8..16"},
    "n_targets":         {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_exemplar|no_targets|single_cell_exemplar"},
}


def _nonzero_components(grid):
    """Return 4-connected components of non-background cells."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            component = {(sr, sc)}
            seen.add((sr, sc))
            frontier = [(sr, sc)]
            while frontier:
                r, c = frontier.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0):
                        seen.add((nr, nc))
                        component.add((nr, nc))
                        frontier.append((nr, nc))
            components.append(component)
    return components


def _stamp_contract(grid):
    """Analyse the canonical input domain and every planned stamp footprint."""
    result = {"anchor": None, "offsets": (), "targets": (), "footprints": (), "errors": []}
    errors = result["errors"]
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("empty grid")
        return result
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        errors.append("grid rows must be non-empty sequences")
        return result
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    h = len(grid)
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    invalid = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or value not in (0, 1, 3)
    ]
    if invalid:
        errors.append(f"expected only integer colours 0, 1, 3; found {invalid[0]}")
        return result

    components = _nonzero_components(grid)
    exemplars = [
        component
        for component in components
        if {grid[r][c] for r, c in component} == {1, 3}
    ]
    if len(exemplars) != 1:
        errors.append(f"expected exactly one mixed colour-1/3 exemplar blob, got {len(exemplars)}")
        return result
    exemplar = exemplars[0]
    anchors = [(r, c) for r, c in exemplar if grid[r][c] == 1]
    if len(anchors) != 1:
        errors.append(f"expected exactly one colour-1 anchor in exemplar, got {len(anchors)}")
        return result
    anchor = anchors[0]
    offsets = tuple(sorted(
        (r - anchor[0], c - anchor[1])
        for r, c in exemplar
        if grid[r][c] == 3
    ))
    targets = tuple(sorted(
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 1 and (r, c) != anchor
    ))
    result.update(anchor=anchor, offsets=offsets, targets=targets)
    if not offsets:
        errors.append("exemplar has no colour-3 motif cells")
    if not 1 <= len(targets) <= 4:
        errors.append(f"expected 1..4 colour-1 targets, got {len(targets)}")

    component_by_cell = {
        cell: component
        for component in components
        for cell in component
    }
    for target in targets:
        if len(component_by_cell[target]) != 1:
            errors.append(f"target {target} is not an isolated colour-1 marker")

    footprints = []
    for target_r, target_c in targets:
        footprint = {(target_r + dr, target_c + dc) for dr, dc in offsets}
        footprints.append(frozenset(footprint))
        outside = sorted(
            (r, c) for r, c in footprint
            if not (0 <= r < h and 0 <= c < w)
        )
        if outside:
            errors.append(
                f"target {(target_r, target_c)} has an incomplete stamp outside bounds: {outside}"
            )
        occupied = sorted(
            (r, c) for r, c in footprint
            if 0 <= r < h and 0 <= c < w and grid[r][c] != 0
        )
        if occupied:
            errors.append(
                f"target {(target_r, target_c)} stamp overwrites input content: {occupied}"
            )
    for left in range(len(footprints)):
        for right in range(left + 1, len(footprints)):
            overlap = sorted(footprints[left] & footprints[right])
            if overlap:
                errors.append(
                    f"target stamps {targets[left]} and {targets[right]} overlap: {overlap}"
                )
    result["footprints"] = tuple(footprints)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject inputs outside the complete, non-overlapping stamp domain."""
    return list(_stamp_contract(grid)["errors"])


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_targets", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_targets", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n_targets", 1, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        cells = _build_motif(rng, rng.randint(3, 5))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        placed = False
        for _ in range(80):
            r0 = rng.randint(0, max(0, h // 2 - sh - 1))
            c0 = rng.randint(0, max(0, w // 2 - sw - 1))
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
            motif_abs = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
            for ar, ac in motif_abs:
                g[ar][ac] = 3
            # color-1 anchor: a guaranteed empty 4-neighbour of a motif cell, so the
            # anchor + motif form ONE connected blob with both colours (the exemplar).
            mset = set(motif_abs)
            spots = [(ar + dr, ac + dc) for (ar, ac) in motif_abs
                     for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                     if 0 <= ar + dr < h and 0 <= ac + dc < w
                     and (ar + dr, ac + dc) not in mset and g[ar + dr][ac + dc] == 0]
            if not spots:
                continue           # retry whole placement
            aR, aC = rng.choice(spots)
            g[aR][aC] = 1
            placed = True; break
        if not placed:
            continue
        offsets = [(r - aR, c - aC) for r, c in motif_abs]
        reserved = set()
        ok = True
        for _ in range(n):
            placed_t = False
            for _t in range(80):
                r = rng.randint(h // 2, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0:
                    continue
                if any(g[r + dr][c + dc] != 0 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                       if 0 <= r + dr < h and 0 <= c + dc < w):
                    continue
                footprint = {(r + dr, c + dc) for dr, dc in offsets}
                if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in footprint):
                    continue
                if any(g[rr][cc] != 0 for rr, cc in footprint):
                    continue
                claimed = footprint | {(r, c)}
                if claimed & reserved:
                    continue
                g[r][c] = 1
                reserved.update(claimed)
                placed_t = True
                break
            if not placed_t:
                ok = False
                break
        if ok and not self_check(g):
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_exemplar":
        # No color-3 motif — rule has no template.
        g[6][3] = 1; g[7][8] = 1
        return g
    if name == "no_targets":
        # Exemplar but no target markers — rule has no destinations.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 3
        return g
    if name == "single_cell_exemplar":
        # 1-cell exemplar — all stamps are trivial single cells.
        g[2][2] = 3
        g[1][1] = 1
        g[6][3] = 1; g[7][8] = 1
        return g
    return g
