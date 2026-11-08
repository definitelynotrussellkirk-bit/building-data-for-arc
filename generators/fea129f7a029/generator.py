"""Generator for 845d6e51.

Rule: 5-divider; non-3 non-5 key shapes above; 3-shapes below; for
each 3-shape, find a key with same size and bbox dims and recolor.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_pairs,
shape_variant.
Degenerates: no_keys, no_targets, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fea129f7a029"
VERSION = "2.0.1"  # random polyomino keys/targets, key!=target shapes (signature match), more pairs, decoys + unmatched, wider grids
TASK_ID = "fea129f7a029"
SUMMARY = (
    "0-bg grid split by ONE full-width row of 5s (the "
    "divider). ABOVE it: 'key' shapes, each a random "
    "polyomino (2-6 cells) in a distinct non-{3,5} color. "
    "BELOW it: 'target' shapes in color 3. Each target is "
    "paired to one key by SIGNATURE = (cell count, sorted "
    "bbox dims {min,max}) — orientation-independent — and "
    "the key/target shapes may DIFFER (e.g. transposed) so "
    "long as the signature matches. Key signatures are "
    "pairwise distinct so each match is unique. The grid "
    "may also include DECOY keys (signature used by no "
    "target) and UNMATCHED targets (signature matched by no "
    "key). Rule: for each color-3 object, find the "
    "non-{3,5} key with equal size and equal sorted bbox "
    "dims; if found, recolor the 3-object to that key's "
    "color, else leave it as 3."
)

INVARIANTS = [
    "exactly one full-width row of 5s as the divider",
    "key shapes above the divider in non-3 non-5 colors",
    "target shapes (color 3) below the divider",
    "every key has a distinct (size, sorted-bbox) signature so matches are unique",
    "all color-3 objects are mutually non-adjacent (stay separate components)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_keys", "no_targets", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "11-14 easy / 12-18 med / 16-22 hard", "valid": "10..24"},
    "grid_w":         {"type": "int", "default": "12-15 easy / 13-18 med / 15-20 hard", "valid": "12..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "2-3 easy / 3-5 med / 4-6 hard", "valid": "1..6"},
    "n_decoy_keys":   {"type": "int", "default": "0 easy / 0-1 med / 0-2 hard", "valid": "0..2"},
    "n_unmatched":    {"type": "int", "default": "0-4 easy / 0-5 med / 0-7 hard", "valid": "0..7"},
    "shape_size":     {"type": "int", "default": "random polyomino 2..6 cells", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "= distinct key colors", "valid": "1..7"},
    "n_distinct_colors": {"type": "int", "default": "= number of keys", "valid": "1..7"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _components_where(grid, predicate):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or not predicate(grid[r0][c0], r0, c0):
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _sig(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    bh = max(rs) - min(rs) + 1; bw = max(cs) - min(cs) + 1
    return (len(cells), min(bh, bw), max(bh, bw))


def self_check(grid, *, difficulty=None, meta=None):
    """Verify divider, unique key signatures, and at least one matched 3-target."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    h = len(grid)
    w = len(grid[0])
    five_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    if len(five_rows) != 1:
        errors.append(f"expected exactly one full-5 divider row; found {five_rows}")
        return errors
    div = five_rows[0]
    keys = _components_where(grid, lambda v, r, c: r < div and v not in (0, 3, 5))
    targets = _components_where(grid, lambda v, r, c: r > div and v == 3)
    if not keys:
        errors.append("no key shapes above the divider")
    if not targets:
        errors.append("no color-3 target shapes below the divider")
    key_sigs = {}
    for color, cells in keys:
        sig = _sig(cells)
        if sig in key_sigs:
            errors.append(f"duplicate key signature {sig}; match would be ambiguous")
        key_sigs[sig] = color
    if targets and key_sigs:
        matched = [cells for _, cells in targets if _sig(cells) in key_sigs]
        if not matched:
            errors.append("no color-3 target has a matching key signature")
    return errors


def _grow_in_box(rng, size, bh, bw, tries=120):
    """Random 4-connected polyomino of exactly `size` cells whose bbox is exactly
    bh x bw. Returns normalized (min row/col = 0) sorted cell list, or None."""
    if size > bh * bw or size < max(bh, bw):
        return None
    for _ in range(tries):
        cells = {(rng.randrange(bh), rng.randrange(bw))}
        frontier = list(cells)
        while len(cells) < size and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= cr + dr < bh and 0 <= cc + dc < bw
                    and (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc))
                continue
            nc = rng.choice(opts)
            cells.add(nc)
            frontier.append(nc)
        if len(cells) != size:
            continue
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        if max(rs) - min(rs) + 1 == bh and max(cs) - min(cs) + 1 == bw:
            return sorted((r, c) for r, c in cells)
    return None


def _make_key_target(rng, size, mn, mx):
    """Build a (key_cells, target_cells) pair sharing signature (size, {mn,mx}) but
    with deliberately DIFFERENT shapes (transposed bbox when mn!=mx; otherwise a
    distinct random fill). Returns None if a shape can't be realized."""
    key = _grow_in_box(rng, size, mn, mx)
    if key is None:
        return None
    if mn != mx:
        target = _grow_in_box(rng, size, mx, mn)   # transposed bbox -> different shape
    else:
        target = None
        for _ in range(20):
            cand = _grow_in_box(rng, size, mn, mx)
            if cand is not None and cand != key:
                target = cand
                break
        if target is None:
            target = _grow_in_box(rng, size, mn, mx)
    if target is None:
        return None
    return key, target


def _signature_pool():
    """All feasible (size, mn, mx) signatures with mn<=mx that a connected polyomino
    can realize (size between max-dim and mn*mx; 1-wide bbox must be a full line)."""
    sigs = []
    for size in range(2, 7):
        for mn in range(1, size + 1):
            for mx in range(mn, size + 1):
                if mn * mx < size or size < mx:
                    continue
                if mn == 1 and mx != size:
                    continue
                sigs.append((size, mn, mx))
    return sigs


def _place_shape(g, cells, color, r0_lo, r0_hi, rng, tries=80):
    """Place `cells` (normalized) in color, with top-left row r0 in [r0_lo, r0_hi].
    Enforces a 1-cell halo against ALL existing non-bg cells (so every object stays a
    separate mono-color component, incl. clearance from the divider). True if placed."""
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if r0_hi - sh < r0_lo or sw > w:
        return False
    for _ in range(tries):
        r0 = rng.randint(r0_lo, r0_hi - sh)
        c0 = rng.randint(0, w - sw)
        occ = [(r0 + dr, c0 + dc) for dr, dc in cells]
        halo = [(rr, cc) for r, c in occ
                for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)]
        if any(0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0 for rr, cc in halo):
            continue
        for r, c in occ:
            g[r][c] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 13, 16)
        np_lo, np_hi, dec_hi, unm_hi = 2, 3, 1, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22)
        w = ctx.draw_int("grid_w", 15, 20)
        np_lo, np_hi, dec_hi, unm_hi = 4, 6, 2, 7
    else:
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        np_lo, np_hi, dec_hi, unm_hi = 3, 5, 2, 5

    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, rng)
    pool = pool + [c for c in [1, 2, 4, 6, 7, 8, 9] if c not in pool]

    g = full_grid(h, w, 0)
    div = h // 2
    for c in range(w):
        g[div][c] = 5

    # Draw DISTINCT signatures for the matched keys + decoy keys (each key signature
    # must be unique so the rule's first-match is unambiguous). Then draw unmatched
    # target signatures that collide with NO key signature.
    # Cap bbox dims to what actually fits a half-grid region (top/bottom each ~h/2
    # rows after the divider gap) so keys/targets reliably place and the rule fires.
    maxdim = max(2, min(div - 1, h - div - 1, w - 1))
    all_sigs = [s for s in _signature_pool() if s[2] <= maxdim]
    rng.shuffle(all_sigs)
    # Canonical examples have many small 3-target components below the divider.
    # Prefer compact signatures so the generator reliably places several targets
    # instead of collapsing to only a few objects after halo rejection.
    all_sigs.sort(key=lambda s: (s[0] > 4, s[0], s[2], s[1]))
    n_pairs = rng.randint(np_lo, np_hi)
    n_decoy = rng.randint(0, dec_hi)
    n_unmatched = rng.randint(0, unm_hi)

    key_sigs = all_sigs[:n_pairs + n_decoy]
    matched_sigs = key_sigs[:n_pairs]
    decoy_sigs = key_sigs[n_pairs:n_pairs + n_decoy]
    key_sig_set = set(key_sigs)
    unmatched_sigs = [s for s in all_sigs[n_pairs + n_decoy:]
                      if s not in key_sig_set][:n_unmatched]

    # Top region: keys (matched + decoy) in distinct non-{3,5} colors.
    # Bottom region: targets (matched as color 3; later recolored by the rule) +
    # unmatched 3-shapes whose signature matches no key.
    rng.shuffle(pool)
    top_r0_lo, top_r0_hi = 0, div - 1           # cells stay above the divider (halo gaps it)
    bot_r0_lo, bot_r0_hi = div + 1, h           # cells stay below the divider

    color_i = 0
    matched_placed = 0
    target_repeats = 2 if difficulty == "easy" else (4 if difficulty == "hard" else 3)
    for sig in matched_sigs:
        pair = _make_key_target(rng, *sig)
        if pair is None:
            continue
        key_cells, tgt_cells = pair
        color = pool[color_i % len(pool)]
        # Only commit targets if their key actually landed.  Place several
        # same-signature targets per key: the canonical task has many green
        # components below a small key bank, and the rule recolors every matching
        # target independently.
        if _place_shape(g, key_cells, color, top_r0_lo, top_r0_hi, rng):
            color_i += 1
            for _ in range(target_repeats):
                target_pair = _make_key_target(rng, *sig)
                cells = target_pair[1] if target_pair is not None else tgt_cells
                if _place_shape(g, cells, 3, bot_r0_lo, bot_r0_hi, rng):
                    matched_placed += 1
    # Decoy keys (unreferenced): valid shapes, distinct colors, no target.
    for sig in decoy_sigs:
        cells = _grow_in_box(rng, *sig)
        if cells is None:
            continue
        color = pool[color_i % len(pool)]; color_i += 1
        _place_shape(g, cells, color, top_r0_lo, top_r0_hi, rng)
    # Unmatched targets: color-3 shapes whose signature matches no key -> stay 3.
    for sig in unmatched_sigs:
        cells = _grow_in_box(rng, *sig)
        if cells is None:
            continue
        _place_shape(g, cells, 3, bot_r0_lo, bot_r0_hi, rng)

    # Guarantee at least one real matched pair so the rule always demonstrates the
    # recolor (a 2-cell domino always fits a half-grid region's spare space).
    if matched_placed == 0:
        dom = [(0, 0), (1, 0)]
        color = pool[color_i % len(pool)]
        if _place_shape(g, dom, color, top_r0_lo, top_r0_hi, rng):
            _place_shape(g, dom, 3, bot_r0_lo, bot_r0_hi, rng)
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 4]
    else:
        pool = [1, 2, 4, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 3, 5)]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 13, 15
    g = full_grid(h, w, 0)
    div = h // 2
    for c in range(w):
        g[div][c] = 5
    domino = [(0, 0), (1, 0)]
    if name == "no_keys":
        for dr, dc in domino:
            g[div + 2 + dr][3 + dc] = 3
        return g
    if name == "no_targets":
        for dr, dc in domino:
            g[2 + dr][3 + dc] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
