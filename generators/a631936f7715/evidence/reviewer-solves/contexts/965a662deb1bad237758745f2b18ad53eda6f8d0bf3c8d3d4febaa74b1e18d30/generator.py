"""Generator for a631936f7715.

Rule: magenta (6) 4-connected components are recolored to the color of their
one adjacent label cell; label cells and solo marker cells are removed to the
orange background (7); magenta components with no adjacent label keep color 6.

Combinatorial axes (4): grid_h/w, component_count, palette_kind, texture.
Branches exercised: labeled components (recolored), unlabeled components
(keep magenta), solo markers (removed to background), varied shapes, sizes,
positions, and label sides.
Degenerates: no_components, no_labels, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a631936f7715"
VERSION = "1.8.0"
TASK_ID = "a631936f7715"
RULE_HASH = "8097fabedcc2"
SUMMARY = "Magenta components recolored by adjacent label cells; labels removed."

INVARIANTS = [
    "background is color 7",
    "source components use color 6",
    "each labeled component has exactly one adjacent label cell; label "
    "colors are distinct so every labeled component gets a unique recolor",
    "a component with no adjacent label keeps color 6",
    "solo markers (non-6, non-7 cells not adjacent to any component) are "
    "allowed and are removed by the rule",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_components", "no_labels", "full_grid")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
HELPFUL_TEXTURES = PALETTE_KINDS
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

_ENV_LO, _ENV_HI = 4, 16   # envelope bounds; AXES valid strings below must match
AXES = {
    "grid_h":         {"type": "int", "default": "band rng 5..14",
                       "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "band rng 5..14",
                       "valid": "4..16"},
    "component_count":{"type": "int", "default": "band 2..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    # Helpful textures are palette aliases and therefore cannot disagree with
    # an independently requested palette kind.
    {"texture": texture, "palette_kind": palette}
    for texture in HELPFUL_TEXTURES
    for palette in PALETTE_KINDS
    if texture != palette
] + [
    # These degenerate probes have fixed content; the named override would be
    # inert rather than exact.
    {"texture": texture, "palette_kind": None}
    for texture in ("no_labels", "full_grid")
] + [
    {"texture": texture, "component_count": None}
    for texture in DEGENERATE_TEXTURES
] + [
    # Some endpoint canvas/component combinations are geometrically
    # infeasible.  The generator rejects rather than silently changing an
    # exact override; pair declarations make those refusals falsifiable.
    ("grid_h", "grid_w"),
    ("grid_h", "component_count"),
    ("grid_w", "component_count"),
]

_BG = 7
_SRC = 6
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _validate_request(seed, sample_index, difficulty, overrides):
    """Reject malformed requests before permissive RNG helpers coerce them."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool/float/string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an exact integer (not bool/float/string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    if any(value is None for value in overrides.values()):
        raise ValueError("explicit override values may not be None")

    for name, lo, hi in (
        ("grid_h", _ENV_LO, _ENV_HI),
        ("grid_w", _ENV_LO, _ENV_HI),
        ("component_count", 2, 5),
    ):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")

    palette_kind = overrides.get("palette_kind")
    if palette_kind is not None and (
        type(palette_kind) is not str or palette_kind not in PALETTE_KINDS
    ):
        raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    texture = overrides.get("texture")
    allowed_textures = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
    if texture is not None and (
        type(texture) is not str or texture not in allowed_textures
    ):
        raise ValueError(f"texture must be one of {allowed_textures}")


def _components(grid):
    """Maximal 4-connected components of color 6 -> list of (r, c) lists."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != _SRC or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == _SRC):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _adjacent_label_colors(grid, cells):
    """Distinct non-6 non-7 colors 4-adjacent to a component's cells."""
    h, w = len(grid), len(grid[0])
    colors = set()
    for r, c in cells:
        for dr, dc in _DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (_BG, _SRC):
                colors.add(grid[nr][nc])
    return colors


def observe_overrides(grid):
    """Report per-draw realized values of exact semantic axes (KRF-0002).

    Derived from the grid itself, never from request metadata, so accepted
    overrides cannot silently clamp or fall back. Dimensions are checked
    universally by the contract gate; the only exact semantic axis here is
    component_count (palette_kind/texture are distribution controls)."""
    return {"component_count": len(_components(grid))}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular 0..9 grid with
    background 7 the most frequent color; no 6-component has more than one
    adjacent label color (the oracle's pick would be order-dependent); label
    colors are unique per component; source components have at least two
    cells; no label/marker cell touches two different components (one label
    would serve two).

    Impostor narrowing (minimal-impostor probe): every grid must carry
    task content the rule can act on. Normal grids require at least one
    source component AND at least one adjacent label cell (the rule's
    firing condition); the three declared degenerates are accepted ONLY in
    their narrow declared forms:
      full_grid     — every cell is 6;
      no_components — zero components with exactly two solo markers of
                      distinct colors at non-adjacent positions;
      no_labels     — exactly one unlabeled L-triomino (no labels/markers).
    Comp-only grids of other shapes (solid 2x2, straight lines), comp+marker
    grids without labels, and all-background grids are rejected."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if not (_ENV_LO <= h <= _ENV_HI and _ENV_LO <= w <= _ENV_HI):
        errs.append(f"grid {h}x{w} outside the declared {_ENV_LO}..{_ENV_HI} envelope")
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
    flat = [v for row in grid for v in row]
    if len(set(flat)) == 1:
        if flat[0] not in (_SRC, _BG):
            errs.append("single-color grid without task content")
    elif flat.count(_BG) <= max((flat.count(v) for v in set(flat) if v != _BG),
                                default=0):
        errs.append("background 7 is not the most frequent color")
    comps = _components(grid)
    comp_id = {}
    for idx, cells in enumerate(comps):
        for cell in cells:
            comp_id[cell] = idx
    label_cells, marker_cells = [], []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (_BG, _SRC):
                continue
            touched = {comp_id[(r + dr, c + dc)] for dr, dc in _DIRS4
                       if (r + dr, c + dc) in comp_id}
            if len(touched) > 1:
                errs.append(f"cell ({r},{c}) touches {len(touched)} components")
            (label_cells if touched else marker_cells).append((r, c))
    # Impostor narrowing: declared degenerate forms only; otherwise the grid
    # must contain a component plus an adjacent label (the rule's trigger).
    if all(v == _SRC for v in flat):
        pass  # full_grid degenerate (declared)
    elif not comps:
        if label_cells:
            errs.append("no source components but label cells present")
        elif not marker_cells:
            errs.append("all-background: nothing for the rule to act on")
        elif len(marker_cells) != 2:
            # KRF-0005: no_components is exactly the two-marker grammar;
            # "some marker content" is not a declared form.
            errs.append(f"marker-only grid with {len(marker_cells)} marker(s) "
                        "outside the declared no_components grammar "
                        "(exactly two)")
        else:
            # The declared branch is narrower than any two markers: the
            # generator always draws two DISTINCT palette colors at
            # non-adjacent positions. Same-color pairs and 4-adjacent
            # (domino) pairs are nearest-invalid shapes and rejected.
            (r1, c1), (r2, c2) = marker_cells
            if grid[r1][c1] == grid[r2][c2]:
                errs.append("no_components markers must use two distinct "
                            "colors (same-color pair is not the declared "
                            "form)")
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                errs.append("no_components markers must be non-adjacent "
                            "(a marker domino is not the declared form)")
        # exactly two distinct, separated markers: no_components (declared)
    elif not label_cells:
        if marker_cells:
            errs.append("components with markers but no labels is not a "
                        "declared form")
        else:
            cells = [cell for comp in comps for cell in comp]
            rows_ = {r for r, _ in cells}
            cols_ = {c for _, c in cells}
            straight = len(rows_) == 1 or len(cols_) == 1
            if not (len(comps) == 1 and len(comps[0]) == 3 and not straight):
                errs.append("comp-only grid outside the declared no_labels "
                            "probe shape (one L-triomino)")
    seen_label_colors = {}
    for idx, cells in enumerate(comps):
        if len(cells) < 2:
            errs.append(f"singleton source component at {cells[0]}")
        labels = _adjacent_label_colors(grid, cells)
        if len(labels) > 1:
            errs.append(
                f"component at {cells[0]} has {len(labels)} adjacent label colors")
        for color in labels:
            if color in seen_label_colors:
                errs.append(
                    f"label color {color} shared by components "
                    f"{seen_label_colors[color]} and {idx}")
            else:
                seen_label_colors[color] = idx
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, n_default, label_p, max_markers = 5, 9, 2, 1.0, 0
    elif band == "hard":
        h_lo, h_hi, n_default, label_p, max_markers = 8, 14, 4, 0.7, 2
    else:
        h_lo, h_hi, n_default, label_p, max_markers = 6, 11, 3, 0.75, 1
    # Canonical-form prior (KRF-0003): the official demos must occur at a
    # substantial joint rate in every band, not by accident of a wide
    # envelope. ~30% of fully-unoverridden draws pin a canonical form BEFORE
    # any dimension is drawn, so the recorded draws ARE the returned
    # geometry (no default keyed-axis drift). Each form also pins the EXACT
    # official linked component-size profile (semantic re-review): 5x5 has
    # sizes (2,5), 6x4 has (4,4), 7x7 has (3,4,5) — the archetype constructor
    # below realizes those sizes exactly; the narrow constructor's dominoes
    # can never produce the 6x4 (4,4) profile.
    witness_slot = (
        not overrides
        and sample_index % LESSON_SCHEDULE_PERIOD in (0, 2)
    )
    pinned_form = None
    if (not witness_slot
            and not any(k in overrides for k in
                        ("grid_h", "grid_w", "component_count"))):
        # Half of unoverridden samples are reserved for the two teaching
        # witness phases below.  Doubling the prior on the other half keeps
        # the long-run canonical-form rate near the existing 30% contract.
        canonical_prior = 0.60 if not overrides else 0.30
        if ctx.draw_rng("canonical_prior").random() < canonical_prior:
            pinned_form = ctx.draw_choice(
                "canonical_form", [(5, 5, (2, 5), 1.0, 0, False, False),
                                   (6, 4, (4, 4), 1.0, 1, True, True),
                                   (7, 7, (3, 4, 5), 1.0, 1, False, True)])
    one_unlabeled = False
    markers_exact = False
    sizes = None
    if pinned_form:
        (h, w, sizes, label_p, max_markers, one_unlabeled,
         markers_exact) = pinned_form
        n_default = len(sizes)
        # KRF-0004 provenance: record the pinned exact values under their
        # declared axis labels — the canonical early return must not bypass
        # grid_h/grid_w/component_count provenance. Injecting into
        # ctx.overrides makes the typed draws record exactly these values.
        ctx.overrides["grid_h"] = h
        ctx.overrides["grid_w"] = w
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.overrides["component_count"] = n_default
        ctx.draw_int("component_count", n_default, n_default)
    else:
        # Feasible-domain dimensions (pause-wave drift class): the canvas
        # must fit components + labels + markers, so draw the width from a
        # range that is feasible BEFORE the draw — never grow/shrink/replace
        # a recorded value afterwards. Feasibility is measured against the
        # CONSTRUCTIVE fallback's lattice capacity (the old density-only
        # formula called 5x8 feasible for 5 components, but the staggered
        # lattice holds only 4 dominoes there) plus the density budget that
        # keeps background strictly modal.
        n_est = int(overrides.get("component_count") or n_default)
        h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _ENV_LO, _ENV_HI)
        w_need = None
        for cw in range(h_lo, h_hi + 1):
            if (_narrow_capacity(max(h, cw), min(h, cw)) >= n_est
                    and 3 * n_est + max_markers <= int(h * cw * 0.45)):
                w_need = cw
                break
        if w_need is None:
            raise ValueError(
                f"infeasible geometry: {n_est} components + {max_markers} "
                f"markers cannot fit h={h} within the band's width range")
        w = _banded_int(ctx, overrides, "grid_w", w_need, h_hi, _ENV_LO, _ENV_HI)
    # Mixed-override contract (wave-4): no inert combinations. A helpful
    # texture IS a palette alias, so texture+palette_kind must agree;
    # degenerate textures with no palette-dependent cells must reject an
    # explicit palette override outright (no_components uses it, see below).
    tex = overrides.get("texture")
    pk = overrides.get("palette_kind")
    if tex in PALETTE_KINDS and pk is not None and pk != tex:
        raise ValueError(
            f"conflicting palette directives: texture={tex!r} is itself a "
            f"palette alias and palette_kind={pk!r} disagrees")
    if tex in DEGENERATE_TEXTURES and pk is not None and tex != "no_components":
        raise ValueError(
            f"palette_kind has no lawful effect under texture={tex!r}; "
            "drop one of the two overrides")
    if tex in DEGENERATE_TEXTURES and overrides.get("component_count") is not None:
        raise ValueError(
            f"component_count has no lawful effect under texture={tex!r} "
            "(degenerate probes have fixed structure); drop one of the two "
            "overrides")
    if tex in DEGENERATE_TEXTURES:
        # Degenerate textures honor exact dimension overrides too (KRF-0001):
        # the texture is drawn on the requested canvas, never a fixed one.
        palette_kind = pk or ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
        rng = ctx.draw_rng("layout")
        return _draw_from_degenerate(tex, rng, h, w,
                                     _build_palette(palette_kind, rng))
    # KRF-0004 provenance: an undrawn component_count must still be RECORDED
    # under its declared axis label. Inject the band default into
    # ctx.overrides so the typed draw below records exactly the realized
    # value (caller overrides are validated against the AXES 2..5 envelope).
    if ctx.overrides.get("component_count") is None:
        ctx.overrides["component_count"] = n_default
    n_comp = ctx.draw_int("component_count", 2, 5)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    rng = ctx.draw_rng("layout")
    pool = _build_palette(palette_kind, rng)
    if len(pool) < n_comp:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 8, 9] if c not in pool]
    if witness_slot:
        grid = _connectivity_witness_grid(rng, h, w, n_comp, pool)
        errors = self_check(grid)
        if errors:
            raise RuntimeError(
                "connectivity witness constructor produced an invalid grid: "
                + "; ".join(errors)
            )
        return grid
    if sizes is not None:
        # Canonical archetype: realize the pinned official size profile
        # exactly (role structure/markers come from the same pinned form).
        # Falls through to the general placement only if the exact sizes
        # cannot be placed (observed ~1/624 pinned draws on 6x4; the leak
        # lands on canonical dims with generalized sizes, never a crash).
        grid = _place_archetype(rng, h, w, sizes, pool,
                                one_unlabeled=one_unlabeled,
                                n_markers=max_markers)
        if grid is not None:
            return grid
    # Boundary-override contract (KRF-0001): a caller-supplied dimension is
    # EXACT — never silently grown, shrunk, or replaced by a fallback, and
    # default draws are drawn from a feasible range in the first place.
    # Narrow/tight canvases use the constructive band/lattice layout; random
    # placement is primary elsewhere, with the constructive layout as the
    # guaranteed-feasible fallback before any loud failure.
    if min(h, w) <= 4:
        grid = _place_narrow(rng, h, w, n_comp, label_p, max_markers, pool,
                             one_unlabeled=one_unlabeled,
                             markers_exact=markers_exact)
        if grid is not None:
            return grid
    for attempt in range(60):
        grid = _place_layout(rng, h, w, n_comp, label_p, max_markers, pool,
                             one_unlabeled=one_unlabeled,
                             markers_exact=markers_exact)
        if grid is not None:
            return grid
    grid = _place_narrow(rng, h, w, n_comp, label_p, max_markers, pool,
                         one_unlabeled=one_unlabeled,
                         markers_exact=markers_exact)
    if grid is not None:
        return grid
    raise ValueError(
        f"cannot place {n_comp} labeled components on the drawn canvas "
        f"{h}x{w} after 60 attempts and the constructive fallback")


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute on any band, per the AXES contract)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 9]
    elif kind == "cool":
        pool = [1, 5, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 8, 9]
    pool = [c for c in pool if c not in (0, 6, 7)]
    rng.shuffle(pool)
    return pool


def _random_shape(rng, h, w, size):
    """One random 4-connected polyomino of `size` cells as (r, c) list."""
    cells = [(rng.randrange(h), rng.randrange(w))]
    while len(cells) < size:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = _DIRS4[rng.randrange(4)]
        nxt = (r + dr, c + dc)
        if nxt not in cells:
            cells.append(nxt)
    return cells


def _label_component(rng, g, occupied, comp_halo, comps, idx, label_colors, pool):
    """Place component idx's single label on a free halo cell that touches
    only this component. Returns True when a label was placed."""
    h, w = len(g), len(g[0])
    cells = comps[idx]
    slots = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in _DIRS4
                    if 0 <= r + dr < h and 0 <= c + dc < w
                    and (r + dr, c + dc) not in occupied
                    and comp_halo.get((r + dr, c + dc), {idx}) == {idx}})
    if not slots:
        return False
    lr, lc = slots[rng.randrange(len(slots))]
    color = pool[len(label_colors) % len(pool)]
    g[lr][lc] = color
    occupied.add((lr, lc))
    label_colors.append(color)
    return True


def _narrow_capacity(H, W):
    """Number of domino slots in _place_narrow's staggered lattice for an
    H x W (post-transpose) canvas: two-apart row bands, columns phase-
    staggered (even bands from col 0, odd bands from col 2, step 4)."""
    total = 0
    for bi, br in enumerate(range(0, H, 2)):
        c = 0 if bi % 2 == 0 else 2
        while c + 1 < W:
            total += 1
            c += 4
    return total


def _place_narrow(rng, h, w, n_comp, label_p, max_markers, pool,
                  one_unlabeled=False, markers_exact=False):
    """Constructive guaranteed-feasible layout: horizontal dominoes in
    two-apart row bands with phase-staggered columns (even bands from col 0,
    odd bands from col 2, step 4), each labeled directly below/above its
    domino — labels can never touch a foreign component. Used directly for
    narrow canvases and as the fallback when random placement fails.
    Transposed when tall. Lawful subset of the random layouts, rng-varied."""
    transpose = h < w
    H, W = (w, h) if transpose else (h, w)
    g = full_grid(H, W, _BG)
    slots = []
    for bi, br in enumerate(range(0, H, 2)):
        c = 0 if bi % 2 == 0 else 2
        while c + 1 < W:
            slots.append((br, c))
            c += 4
    rng.shuffle(slots)
    chosen = slots[:n_comp]
    if len(chosen) < n_comp:
        return None
    unlabeled_idx = rng.randrange(n_comp) if one_unlabeled and n_comp > 1 else -1
    label_colors = []
    occupied = set()
    for idx, (br, bc) in enumerate(chosen):
        cells = [(br, bc), (br, bc + 1)]
        for r, c in cells:
            g[r][c] = _SRC
            occupied.add((r, c))
        labeled = (idx != unlabeled_idx) and (rng.random() < label_p or one_unlabeled)
        if labeled:
            lr = br + 1 if br + 1 < H else br - 1
            color = pool[len(label_colors) % len(pool)]
            g[lr][bc] = color
            occupied.add((lr, bc))
            label_colors.append(color)
    if not label_colors and n_comp:
        # guarantee the rule fires: label the first non-pinned component
        for idx, (br, bc) in enumerate(chosen):
            if idx != unlabeled_idx:
                lr = br + 1 if br + 1 < H else br - 1
                color = pool[0]
                g[lr][bc] = color
                occupied.add((lr, bc))
                label_colors.append(color)
                break
    n_markers = max_markers if markers_exact else rng.randint(0, max_markers)
    for _ in range(n_markers):
        slots_m = [(r, c) for r in range(H) for c in range(W)
                   if (r, c) not in occupied
                   and all((r + dr, c + dc) not in occupied for dr, dc in _DIRS4)]
        if not slots_m:
            break
        mr, mc = slots_m[rng.randrange(len(slots_m))]
        g[mr][mc] = pool[rng.randrange(len(pool))]
        occupied.add((mr, mc))
    if transpose:
        return [[g[c][r] for c in range(H)] for r in range(W)]
    return g


def _place_archetype(rng, h, w, sizes, pool, one_unlabeled=False, n_markers=0):
    """Canonical-form constructor: 4-connected components of the EXACT
    official linked sizes, every component labeled (one pinned unlabeled for
    the 6x4 signature), and an exact marker count. Same placement law as
    _place_layout (non-touching components, single-touch label slots, halo-
    free markers) but with no random size draw and no density cap — the
    official profiles are small enough that background stays strictly modal
    by construction. Returns None when the exact sizes cannot be placed."""
    g = full_grid(h, w, _BG)
    occupied = set()   # any non-background cell
    comp_halo = {}     # cell -> set of component indices whose halo covers it
    comps = []
    for size in sorted(sizes, reverse=True):
        placed = None
        for _try in range(200):
            cells = _random_shape(rng, h, w, size)
            if any((r, c) in occupied or (r, c) in comp_halo
                   for r, c in cells):
                continue
            if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
                continue
            placed = cells
            break
        if placed is None:
            return None
        comps.append(placed)
        for r, c in placed:
            g[r][c] = _SRC
            occupied.add((r, c))
        for r, c in placed:
            for dr, dc in _DIRS4:
                comp_halo.setdefault((r + dr, c + dc), set()).add(len(comps) - 1)
    unlabeled_idx = (rng.randrange(len(comps))
                     if one_unlabeled and len(comps) > 1 else -1)
    label_colors = []
    for idx in range(len(comps)):
        if idx == unlabeled_idx:
            continue
        if not _label_component(rng, g, occupied, comp_halo, comps, idx,
                                label_colors, pool):
            return None
    for _ in range(n_markers):
        slots = [(r, c) for r in range(h) for c in range(w)
                 if (r, c) not in occupied and not comp_halo.get((r, c))]
        if not slots:
            return None
        mr, mc = slots[rng.randrange(len(slots))]
        g[mr][mc] = pool[rng.randrange(len(pool))]
        occupied.add((mr, mc))
    return g


def _place_layout(rng, h, w, n_comp, label_p, max_markers, pool,
                  one_unlabeled=False, markers_exact=False):
    """Random lawful layout; None when placement fails on this canvas.

    one_unlabeled pins the official 6x4 signature: exactly one component
    (chosen at random) stays unlabeled while the rest are labeled, so the
    canonical one-labeled/one-unlabeled branch is witnessed deliberately."""
    g = full_grid(h, w, _BG)
    occupied = set()   # any non-background cell
    comp_halo = {}     # cell -> set of component indices whose halo covers it
    # Keep the orange background dominant even on tiny canvases: source cells
    # plus every possible label and marker stay under 45% of the grid, so 7
    # remains strictly the most frequent color (canonical pairs sit near 27%).
    cell_budget = max(2, int(h * w * 0.45) - n_comp - max_markers)
    if cell_budget < 2 * n_comp:
        return None
    comp_cells = 0
    comps = []
    for idx in range(n_comp):
        size = rng.randint(2, 5)
        placed = None
        for _try in range(120):
            cells = _random_shape(rng, h, w, size)
            if comp_cells + len(cells) > cell_budget:
                continue
            if any((r, c) in occupied or (r, c) in comp_halo
                   for r, c in cells):
                continue
            if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
                continue
            placed = cells
            break
        if placed is None:
            return None
        comp_cells += len(placed)
        comps.append(placed)
        for r, c in placed:
            g[r][c] = _SRC
            occupied.add((r, c))
        for r, c in placed:
            for dr, dc in _DIRS4:
                comp_halo.setdefault((r + dr, c + dc), set()).add(idx)
    # Labels: exactly one per labeled component, on a free halo cell that
    # touches only its own component; colors drawn distinct from the pool.
    unlabeled_idx = rng.randrange(len(comps)) if one_unlabeled and len(comps) > 1 else -1
    label_colors = []
    for idx, cells in enumerate(comps):
        if idx == unlabeled_idx:
            continue  # pinned official signature: this one keeps color 6
        if rng.random() >= label_p:
            continue  # unlabeled component: keeps color 6 in the output
        if not _label_component(rng, g, occupied, comp_halo, comps, idx,
                                label_colors, pool):
            continue
    # Guarantee the rule fires: a normal draw always recolors at least one
    # component (an all-unlabeled, marker-free draw would be an identity).
    if not label_colors:
        order = [i for i in range(len(comps)) if i != unlabeled_idx]
        rng.shuffle(order)
        for idx in order:
            if _label_component(rng, g, occupied, comp_halo, comps, idx,
                                label_colors, pool):
                break
        else:
            return None
    # Solo markers: distractor cells removed by the rule; never adjacent to a
    # component (that would make them labels).
    n_markers = max_markers if markers_exact else rng.randint(0, max_markers)
    for _ in range(n_markers):
        slots = [(r, c) for r in range(h) for c in range(w)
                 if (r, c) not in occupied and not comp_halo.get((r, c))]
        if not slots:
            break
        mr, mc = slots[rng.randrange(len(slots))]
        g[mr][mc] = pool[rng.randrange(len(pool))]
        occupied.add((mr, mc))
    return g


def _draw_from_degenerate(name, rng, h, w, pool):
    g = full_grid(h, w, _BG)
    if name == "no_components":
        # The only degenerate mode with palette-dependent cells: markers use
        # the requested palette's first two colors.
        g[max(1, h // 4)][max(1, w // 4)] = pool[0]
        g[min(h - 2, (3 * h) // 4)][min(w - 2, (3 * w) // 4)] = pool[1 % len(pool)]
        return g
    if name == "no_labels":
        r0, c0 = max(0, h // 4), max(0, w // 4)
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            if r0 + dr < h and c0 + dc < w:
                g[r0 + dr][c0 + dc] = 6
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 6
        return g
    return g


def _components_using(grid, directions):
    """Connected source components under an explicit neighborhood."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != _SRC or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in directions:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w
                            and grid[nr][nc] == _SRC
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _output_for_components(grid, components):
    """Apply the canonical recolor/removal rule to supplied components.

    The selected generator grammar permits at most one orthogonal label color
    per four-connected component.  The rival can merge diagonal components;
    should a foreign grid expose multiple labels after that merge, the smallest
    color is used as a deterministic, input-pure tie break.
    """
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, _BG)
    for cells in components:
        labels = sorted(_adjacent_label_colors(grid, cells))
        color = labels[0] if labels else _SRC
        for r, c in cells:
            out[r][c] = color
    return out


def _reference_output(grid):
    """Python mirror of the unchanged four-connected Racket authority."""
    return _output_for_components(grid, _components_using(grid, _DIRS4))


def _eight_connected_components(grid):
    """Plausible canonical-only shortcut: merge diagonal magenta contacts."""
    return _output_for_components(grid, _components_using(grid, _DIRS8))


def _connectivity_witness(grid):
    """True exactly when 4- and 8-connected component rules disagree."""
    return not self_check(grid) and _reference_output(grid) != _eight_connected_components(grid)


def _transform_square_cell(cell, size, mode):
    """Apply one of eight dihedral transforms inside a square canvas."""
    r, c = cell
    if mode >= 4:
        c = size - 1 - c
    for _ in range(mode % 4):
        r, c = c, size - 1 - r
    return r, c


def _connectivity_witness_grid(rng, h, w, n_comp, pool):
    """Construct a lawful labeled scene that distinguishes 4 from 8.

    The first two dominoes touch only at a corner. Every component gets its own
    label, so even the largest supported canvas demonstrates a nontrivial
    recoloring/removal fraction. Under the eight-connected rival, the diagonal
    group sees multiple labels and follows the rival's documented deterministic
    tie break; the selected four-connected rule keeps the component labels
    separate.
    """
    if n_comp not in (2, 3, 4):
        raise ValueError("scheduled connectivity witness requires 2..4 components")
    size = 4 if n_comp <= 3 else 6
    if h < size or w < size:
        raise ValueError(
            f"scheduled connectivity witness needs at least {size}x{size}, got {h}x{w}"
        )

    components = [
        ((1, 0), (1, 1)),       # labeled component
        ((2, 2), (3, 2)),       # diagonal-only contact with the first
        ((0, 3), (1, 3)),       # optional third component
        ((4, 4), (5, 4)),       # optional fourth component
    ][:n_comp]
    labels = [
        (0, 0),
        (3, 3),
        (0, 2),
        (5, 5),
    ][:n_comp]
    mode = rng.randrange(8)
    row_offset = rng.randrange(h - size + 1)
    col_offset = rng.randrange(w - size + 1)

    def place(cell):
        r, c = _transform_square_cell(cell, size, mode)
        return r + row_offset, c + col_offset

    grid = full_grid(h, w, _BG)
    for component in components:
        for r, c in map(place, component):
            grid[r][c] = _SRC
    for color, label in zip(pool, labels):
        lr, lc = place(label)
        grid[lr][lc] = color
    return grid


SEMANTIC_WITNESSES = {
    "diagonal_components_stay_separate": _connectivity_witness,
}
SEMANTIC_RIVALS = {
    "eight_connected_components": _eight_connected_components,
}
WITNESS_RIVALS = {
    "diagonal_components_stay_separate": ["eight_connected_components"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every public canonical pair lacks a diagonal-only contact, so treating
# magenta cells as eight-connected produces exactly the official answers.
CANONICAL_SHORTCUTS = {
    "eight_connected_components": _eight_connected_components,
}


def lesson_identifiable(demos, query):
    """Return named rivals that fit all demos but alter the query."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(pair["input"]):
            reasons.append(f"demo {index} input is outside the declared grammar")
        elif _reference_output(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not follow the selected rule")

    if self_check(query["input"]):
        reasons.append("query input is outside the declared grammar")
    elif _reference_output(query["input"]) != query["output"]:
        reasons.append("query output does not follow the selected rule")
    if reasons:
        return reasons

    for name, rival in sorted(LESSON_COMPETITORS.items()):
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        differs = rival(query["input"]) != query["output"]
        if survives and differs:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
