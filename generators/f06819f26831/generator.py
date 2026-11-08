"""Generator for 72322fa7.

Rule: each multicolor connected template is copied onto every isolated
single-cell partial whose color matches one of the template's cells,
aligned so the matching-color cell coincides with the partial.

Canonical scene: one to three 2-color templates (bar-3, plus-5, or
diamond-5 shapes) with globally disjoint color pairs, plus 3..7 isolated
single-cell partials, each matching one of the template colors. Stamps
always fit in-bounds and never overlap.

Combinatorial axes (5): grid_h/w, n_templates, partial_count,
palette_kind, texture. Degenerates: no_template, no_partials, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f06819f26831"
VERSION = "3.0.0"
TASK_ID = "f06819f26831"
RULE_HASH = "f962984a2a44"
SUMMARY = (
    "0-bg grid with 1..3 two-color TEMPLATES (bar3/plus5/diamond5, disjoint "
    "color pairs) and isolated single-cell PARTIALS matching template "
    "colors. Rule: stamp each template onto each partial of its color."
)

INVARIANTS = [
    "background is 0",
    "every multicolor component is a canonical template shape (bar3, plus5, "
    "or diamond5) with exactly two colors; color pairs are globally disjoint",
    "every single-cell component is isolated and matches one template color",
    "each partial's stamp fits in-bounds on empty cells, disjoint from others",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_partials", "full_grid")
PARTIAL_KINDS = ("P2", "P3")

AXES = {
    "grid_h":        {"type": "int", "default": "band rng 11..20",
                      "valid": "9..24"},
    "grid_w":        {"type": "int", "default": "band rng 12..22",
                      "valid": "10..26"},
    "n_templates":   {"type": "int", "default": "band 1..2 easy/medium, "
                      "2..3 hard", "valid": "1..3"},
    "partial_count": {"type": "int", "default": "band rng 3..7",
                      "valid": "2..8"},
    "palette_kind":  {"type": "str", "default": "rng helpful",
                      "valid": "|".join(PALETTE_KINDS)},
    "texture":       {"type": "str", "default": "alias for partial_count",
                      "valid": "|".join(PARTIAL_KINDS + DEGENERATE_TEXTURES)},
}

# Canonical template shapes: (name, cells with A/B color roles).
_SHAPES = {
    "bar3h":    ([(0, 0, "A"), (0, 1, "B"), (0, 2, "A")], 1, 3),
    "bar3v":    ([(0, 0, "A"), (1, 0, "B"), (2, 0, "A")], 3, 1),
    "plus5":    ([(0, 1, "A"), (1, 0, "A"), (1, 1, "B"),
                  (1, 2, "A"), (2, 1, "A")], 3, 3),
    "diamond5": ([(0, 0, "A"), (0, 2, "A"), (1, 1, "B"),
                  (2, 0, "A"), (2, 2, "A")], 3, 3),
}

# The four official forms:
# (h, w, ((shape, colorA, colorB), ...), partial colors in reading order)
_CANONICAL_FORMS = (
    (13, 12, (("bar3h", 4, 8),), (8, 4, 4, 8)),
    (13, 22, (("plus5", 8, 6), ("diamond5", 1, 3)), (3, 6, 6)),
    (14, 19, (("bar3h", 8, 2), ("bar3v", 1, 3)), (8, 8, 2, 3)),
    (19, 19, (("bar3h", 3, 7), ("plus5", 2, 4), ("bar3v", 1, 8)),
              (8, 4, 3, 3, 8, 7, 4)),
)

_POOLS = {
    "warm":    [2, 3, 4, 9, 7, 6],
    "cool":    [1, 5, 8, 6, 3, 9],
    "broad":   [1, 2, 3, 4, 5, 6, 7, 8, 9],
    "primary": [1, 2, 3, 4, 5, 8],
}


def _components8(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack, cells = [(r, c)], set()
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w
                                and not seen[nr][nc] and grid[nr][nc] != 0):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all four canonical pairs
    satisfy them): rectangular grid inside the declared 9..24 x 10..26
    envelope; every 8-connected component is either a canonical template
    shape (bar3/plus5/diamond5) with exactly two colors, or an isolated
    single cell; template color pairs are globally disjoint; every single
    cell's color appears in at least one template. The declared degenerates
    are special-cased: no_template (zero multicolor components),
    no_partials (templates but zero singles), full_grid (one solid color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
        return errs
    if not (9 <= h <= 24 and 10 <= w <= 26):
        errs.append(f"dims {h}x{w} outside the declared 9..24 x 10..26 envelope")
        return errs
    flat = [v for row in grid for v in row]
    if len(set(flat)) == 1:
        return errs  # full_grid degenerate (declared)
    comps = _components8(grid)
    templates = []
    singles = []
    distractors = 0
    for cells in comps:
        colors = {grid[r][c] for r, c in cells}
        if len(cells) == 1:
            singles.append(next(iter(cells)))
            continue
        if len(colors) == 1:
            # single-color multi-cell distractor object: the rule ignores
            # it (not a template, not a single-cell partial). Canonical
            # carries small ones (dominoes, 4-cell diamonds).
            if not 2 <= len(cells) <= 5:
                errs.append(f"single-color object of {len(cells)} cells is "
                            "outside the distractor grammar (2..5)")
            distractors += 1
            continue
        if len(colors) != 2:
            errs.append(f"component of {len(cells)} cells has {len(colors)} "
                        "colors (templates are exactly two-color)")
            continue
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        shape = tuple(sorted((r - min(rs), c - min(cs)) for r, c in cells))
        roles = {}
        for name, (scells, th, tw) in _SHAPES.items():
            if tuple(sorted((r, c) for r, c, _ in scells)) == shape:
                roles[name] = scells
        if not roles:
            errs.append(f"multicolor component at {sorted(cells)[0]} is not "
                        "a canonical template shape")
        else:
            templates.append(cells)
    if not templates:
        return errs  # no_template degenerate (declared)
    if not singles:
        return errs  # no_partials degenerate (declared)
    pair_colors = set()
    for cells in templates:
        cs = {grid[r][c] for r, c in cells}
        if pair_colors & cs:
            errs.append("template color pairs are not globally disjoint")
        pair_colors |= cs
    for r, c in singles:
        if grid[r][c] not in pair_colors:
            errs.append(f"single at ({r},{c}) color {grid[r][c]} matches no "
                        "template color")
        if any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)
               if (dr, dc) != (0, 0)):
            errs.append(f"single at ({r},{c}) is not isolated (8-neighbor "
                        "content adjacent)")
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): n_templates counts multicolor
    components; partial_count counts isolated singles."""
    comps = _components8(grid)
    n_templates = sum(1 for cells in comps
                      if len(cells) > 1 and
                      len({grid[r][c] for r, c in cells}) >= 2)
    n_partials = sum(1 for cells in comps if len(cells) == 1)
    return {"n_templates": n_templates, "partial_count": n_partials}


def _free_rect(used, r0, c0, th, tw, h, w):
    if r0 < 0 or c0 < 0 or r0 + th > h or c0 + tw > w:
        return False
    for r in range(r0 - 1, r0 + th + 1):
        for c in range(c0 - 1, c0 + tw + 1):
            if (r, c) in used:
                return False
    return True


def _rand_blob(rng, size):
    """Small random 4-connected polyomino of `size` cells, normalized to a
    zero-origin bbox (unclamped growth would otherwise let negative
    coordinates wrap to the opposite grid edge when painted)."""
    cells = [(0, 0)]
    while len(cells) < size:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        nxt = (r + dr, c + dc)
        if nxt not in cells:
            cells.append(nxt)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _reserve(used, r0, c0, th, tw):
    for r in range(r0 - 1, r0 + th + 1):
        for c in range(c0 - 1, c0 + tw + 1):
            used.add((r, c))


def _place_scene(rng, h, w, templates, partial_colors, distractors=()):
    """Place templates, distractors, and partials with the stamp-feasibility
    reservation."""
    g = full_grid(h, w, 0)
    used = set()
    for shape_name, color_a, color_b in templates:
        scells, th, tw = _SHAPES[shape_name]
        placed = False
        for _try in range(200):
            R = rng.randint(0, h - th)
            C = rng.randint(0, w - tw)
            if _free_rect(used, R, C, th, tw, h, w):
                for dr, dc, role in scells:
                    g[R + dr][C + dc] = color_a if role == "A" else color_b
                _reserve(used, R, C, th, tw)
                placed = True
                break
        if not placed:
            return None
    # Single-color distractor blobs (2..5 cells): random small 4-connected
    # polyominoes, reserved with the same 1-ring rule.
    for dcolor, dsize in distractors:
        blob = _rand_blob(rng, dsize)
        bh = max(r for r, _ in blob) + 1
        bw = max(c for _, c in blob) + 1
        placed = False
        for _try in range(200):
            R = rng.randint(0, h - bh)
            C = rng.randint(0, w - bw)
            if _free_rect(used, R, C, bh, bw, h, w):
                for dr, dc in blob:
                    g[R + dr][C + dc] = dcolor
                _reserve(used, R, C, bh, bw)
                placed = True
                break
        if not placed:
            return None
    # Partials: isolated singles whose stamp CELLS (the template shape at the
    # partial's offset) stay in-bounds and clear of other content; the stamp
    # bbox itself may be approached (canonical stamps can be near-neighbors).
    all_tcells = [(shape_name, scells, th, tw, color_a, color_b)
                  for shape_name, color_a, color_b in templates
                  for (scells, th, tw) in [_SHAPES[shape_name]]]
    for color in partial_colors:
        candidates = [(name, cells, th, tw, a, b, dr, dc, role)
                      for name, cells, th, tw, a, b in all_tcells
                      for dr, dc, role in cells
                      if (a if role == "A" else b) == color]
        placed = False
        for _try in range(300):
            name, cells, th, tw, a, b, dr, dc, role = \
                candidates[rng.randrange(len(candidates))]
            R = rng.randint(0, h - 1)
            C = rng.randint(0, w - 1)
            # the stamp rect must fit in-bounds
            r0, c0 = R - dr, C - dc
            if not (0 <= r0 and 0 <= c0 and r0 + th <= h and c0 + tw <= w):
                continue
            stamp_cells = {(r0 + sr, c0 + sc) for sr, sc, _ in cells}
            # partial cell isolated; stamp cells clear of existing content
            if (R, C) in used:
                continue
            if any((R + ar, C + ac) in used
                   for ar in (-1, 0, 1) for ac in (-1, 0, 1)):
                continue
            if stamp_cells & used:
                continue
            g[R][C] = color
            used |= stamp_cells | {(R, C)}
            _reserve(used, R, C, 1, 1)
            placed = True
            break
        if not placed:
            return None
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    tex = overrides.get("texture")
    if tex in DEGENERATE_TEXTURES:
        extra = sorted(k for k, v in overrides.items()
                       if k != "texture" and v is not None)
        if extra:
            raise ValueError(
                f"degenerate texture {tex!r} is a fixed diagnostic layout; "
                f"it takes no other overrides, got {extra}")
        return _draw_from_degenerate(tex, rng)
    if tex is not None and tex not in PARTIAL_KINDS:
        raise ValueError(f"unknown texture {tex!r}; valid: "
                         f"{PARTIAL_KINDS + DEGENERATE_TEXTURES}")

    # Canonical-form prior (KRF-0003): ~30% of fully-unoverridden draws pin
    # one of the four official forms (dims + template shapes + partial
    # colors); positions vary as nuisance.
    if not any(k in overrides for k in
               ("grid_h", "grid_w", "n_templates", "partial_count")):
        if ctx.draw_rng("canonical_prior").random() < 0.30:
            ch, cw, ctemplates, cpartials = ctx.draw_choice(
                "canonical_form", _CANONICAL_FORMS)
            for label, value in (("grid_h", ch), ("grid_w", cw),
                                 ("n_templates", len(ctemplates)),
                                 ("partial_count", len(cpartials))):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
            g = _place_scene(rng, ch, cw, list(ctemplates), list(cpartials))
            if g is not None:
                return g
            # placement exhausted: fall through to the general path

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, nt, pc_lo, pc_hi = 11, 13, 12, 15, (1, 2), 3, 5
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, nt, pc_lo, pc_hi = 16, 20, 18, 24, (2, 3), 5, 7
    else:
        h_lo, h_hi, w_lo, w_hi, nt, pc_lo, pc_hi = 13, 16, 14, 20, (1, 2), 3, 6
    # Feasible domain BEFORE the draws (pause-wave drift class): pinned
    # counts set a capacity floor the free dims must meet; free counts are
    # drawn from ranges the drawn canvas can host.
    need_t = overrides.get("n_templates") or nt[1]
    need_p = overrides.get("partial_count") or pc_lo
    area_need = 30 * need_t + 20 * need_p
    counts_pinned = (overrides.get("n_templates") is not None
                     or overrides.get("partial_count") is not None)
    h_hi_eff = 24 if counts_pinned else h_hi
    w_hi_eff = 26 if counts_pinned else w_hi
    if overrides.get("grid_h") is None and h_lo * w_lo < area_need:
        h_lo = min(24, max(h_lo, (area_need + w_hi_eff - 1) // w_hi_eff))
    if overrides.get("grid_w") is None and h_lo * w_lo < area_need:
        w_lo = min(26, max(w_lo, (area_need + h_hi_eff - 1) // h_hi_eff))
    if overrides.get("grid_h") is None and h_lo > h_hi_eff or \
            overrides.get("grid_w") is None and w_lo > w_hi_eff:
        raise ValueError(
            f"pinned counts n_templates={need_t}, partial_count={need_p} "
            f"exceed the {h_hi_eff}x{w_hi_eff} envelope")
    h = ctx.draw_int("grid_h", *( (9, 24) if overrides.get("grid_h") is not None
                                  else (h_lo, h_hi_eff)))
    if overrides.get("grid_w") is None and h * w_lo < area_need:
        # joint feasible domain: the drawn height sets the width floor
        w_lo = min(26, max(w_lo, (area_need + h - 1) // h))
    if overrides.get("grid_w") is None and w_lo > w_hi_eff:
        raise ValueError(
            f"pinned counts n_templates={need_t}, partial_count={need_p} "
            f"cannot fit any width on grid_h={h} within the envelope")
    w = ctx.draw_int("grid_w", *( (10, 26) if overrides.get("grid_w") is not None
                                  else (w_lo, w_hi_eff)))
    # Feasible domain (pause-wave drift class): free counts are drawn from
    # ranges the drawn canvas can actually host (reservation budgets), so a
    # small pinned canvas shrinks the plan rather than crashing placement.
    cap_t = max(1, min(3, (h * w) // 80))
    if overrides.get("n_templates") is None and nt[1] > cap_t:
        nt = (min(nt[0], cap_t), cap_t)
    n_templates = ctx.draw_int("n_templates", *nt) \
        if overrides.get("n_templates") is None \
        else ctx.draw_int("n_templates", 1, 3)
    cap_p = max(2, (h * w - 30 * n_templates) // 20)
    pc_eff_lo = pc_lo if pc_lo <= cap_p else 2
    pc = ctx.draw_int("partial_count", pc_eff_lo,
                      min(pc_hi, max(pc_eff_lo, cap_p))) \
        if overrides.get("partial_count") is None and tex is None \
        else ctx.draw_int("partial_count", 2, 8)
    if tex in PARTIAL_KINDS:
        if overrides.get("partial_count") is not None and \
                int(overrides["partial_count"]) != int(tex[1]):
            raise ValueError(
                f"texture={tex!r} forces partial_count={tex[1]} but the "
                f"override asks for {overrides['partial_count']}; drop one "
                "of the two")
        pc = int(tex[1])
    palette_kind = (overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = list(_POOLS[palette_kind])
    rng.shuffle(pool)
    shape_names = list(_SHAPES)
    templates = []
    for i in range(n_templates):
        color_a, color_b = pool[2 * i], pool[2 * i + 1]
        templates.append((shape_names[rng.randrange(len(shape_names))],
                          color_a, color_b))
    partial_colors = []
    for _ in range(pc):
        t = templates[rng.randrange(len(templates))]
        partial_colors.append(t[1 + rng.randrange(2)])
    # Single-color distractor objects (rule ignores them; canonical carries
    # small 2..5-cell blobs, sometimes sharing template colors).
    n_distractors = 1 if rng.random() < 0.25 else 0
    distractors = []
    for _ in range(n_distractors):
        dcolor = pool[rng.randrange(len(pool))]
        dsize = rng.randint(2, 5)
        distractors.append((dcolor, dsize))
    g = None
    for _layout in range(6):
        # The distractor is an unkeyed nuisance choice: drop it after three
        # whole-layout retries rather than shedding any KEYED count.
        g = _place_scene(rng, h, w, templates, partial_colors,
                         distractors if _layout < 3 else ())
        if g is not None:
            break
    if g is None:
        raise ValueError(
            f"cannot place {n_templates} templates + {pc} partials with "
            f"stamp feasibility on {h}x{w} (infeasible combination)")
    errs = self_check(g)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 12, 0)
    tmpl = [(0, 0, 4), (0, 1, 8), (0, 2, 4)]
    if name == "no_template":
        g[1][7] = 8
        return g
    if name == "no_partials":
        for dr, dc, v in tmpl:
            g[1 + dr][1 + dc] = v
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(12):
                g[r][c] = 3
        return g
    return g
