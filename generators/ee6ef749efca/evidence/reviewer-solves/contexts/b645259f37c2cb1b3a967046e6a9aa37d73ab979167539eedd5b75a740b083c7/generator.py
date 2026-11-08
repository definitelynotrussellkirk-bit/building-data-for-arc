"""Generator for arc_additional_puzzles_21_set3:H17.

Rule: the largest color-6 (magenta) 4-connected blob is a template; its cells
are normalized relative to its bbox top-left; the output is a BLANK grid with
the template stamped in color 6 at every color-2 (red) marker cell (the
marker is the stamp's top-left anchor; out-of-bounds stamp cells clip). The
input template is not preserved in the output.

Combinatorial axes (4): grid_h/w, n_markers, decoy, texture.  Branches
exercised: template shape variety (4-5 cell tetromino/pentomino shapes), an
optional strictly smaller 6-blob decoy (the oracle's largest-selection
branch), marker counts 1..4 with position jitter (every demonstrated stamp
fits in-bounds; the clipping semantics of the rule are a fallback, not a
demonstrated branch, so they are not advertised as witnessed).
Textures: no_markers, no_decoy, packed_markers (all rule-valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee6ef749efca"
VERSION = "2.5.0"  # truthful texture provenance, strict bools/defaults, and clipping-aware self-check
# structural self_check + pinned RULE_HASH added; marker shortfall fallback now
# deterministic; SUMMARY corrected (output is a blank grid, template not preserved);
# degenerate no_template/full_grid crashed or degenerated the oracle -> rule-valid
# textures no_markers/no_decoy/packed_markers.
TASK_ID = "ee6ef749efca"
RULE_HASH = "49ca623dd9a1"
SUMMARY = "Blank-grid output: largest 6-blob stamped in 6 at each isolated 2-marker."

INVARIANTS = [
    "background 0 is the modal color; the palette is exactly {0, 2, 6}",
    "the largest color-6 component is unique and has at least 3 cells; an "
    "optional strictly smaller 6-blob decoy exercises largest-selection",
    "color-2 markers are singleton cells 8-separated from every other input "
    "object, and their stamps fit in-bounds",
    "the output is a blank grid with the template stamped in 6 at every "
    "marker; the input template is not preserved",
]

DEGENERATE_TEXTURES = ("no_markers", "no_decoy", "packed_markers")

AXES = {
    "grid_h":    {"type": "int", "default": "band rng 8..14", "valid": "8..14"},
    "grid_w":    {"type": "int", "default": "band rng 11..16", "valid": "11..16"},
    "n_markers": {"type": "int", "default": "band 1..2 easy, 2..3 medium, "
                      "3..4 hard; 0 only when explicitly requested or through "
                      "texture=no_markers", "valid": "0..4"},
    "decoy":     {"type": "bool", "default": "band rng (p 0.25 easy, 0.5 "
                      "medium, 0.75 hard)", "valid": "true|false"},
    "texture":   {"type": "str", "default": "none (plain draw)",
                  "valid": "|".join(("none",) + DEGENERATE_TEXTURES)},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TEMPLATES = [
    [(0, 0), (0, 1), (1, 1), (1, 2)],                  # S-tetromino (canonical)
    [(0, 0), (1, 0), (2, 0), (2, 1)],                  # L-tetromino (canonical)
    [(0, 1), (1, 0), (1, 1), (1, 2)],                  # T-tetromino (canonical)
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],          # U-pentomino (canonical)
    [(0, 0), (1, 0), (1, 1), (2, 1)],                  # Z-tetromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],                  # T pointing down
    [(0, 0), (1, 0), (1, 1), (1, 2)],                  # J-tetromino
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],          # P-pentomino
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],          # plus pentomino
]

_CANONICAL_FORMS = (
    (10, 12, 2, ((0, 0), (0, 1), (1, 1), (1, 2))),  # S4
    (11, 11, 2, ((0, 0), (1, 0), (2, 0), (2, 1))),  # L4
    (12, 12, 3, ((0, 1), (1, 0), (1, 1), (1, 2))),  # T4
    (11, 13, 2, ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))),  # U5
    (12, 13, 3, ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))),  # P5
)
CANONICAL_PROFILE_SIGNATURES = frozenset(
    (h, w, n_markers, template, False)
    for h, w, n_markers, template in _CANONICAL_FORMS
)


def _components(grid, val):
    """4-connected components of color `val` -> list of (r, c) cell lists."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != val or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == val):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside the
    declared 8..14 x 11..16 envelope, colors 0..9 with palette exactly within
    {0, 2, 6}; 0 is modal; at least one 6-component exists and the largest is
    UNIQUE with >= 3 cells (an unambiguous template for the oracle's
    largest-selection); every color-2 component is an isolated singleton
    marker that is 8-separated from every other nonzero input cell and whose
    complete template stamp fits in-bounds. Zero markers is the declared
    no_markers degenerate (the output is a blank grid) and is accepted."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
    if not (8 <= h <= 14 and 11 <= w <= 16):
        errs.append(f"dims {h}x{w} outside the declared 8..14 x 11..16 envelope")
    freq = {}
    for row in grid:
        for v in row:
            freq[v] = freq.get(v, 0) + 1
    if set(freq) - {0, 2, 6}:
        errs.append(f"palette outside {{0, 2, 6}}: {sorted(set(freq) - {0, 2, 6})}")
    if sum(1 for row in grid for v in row if v == 0) * 2 <= h * w:
        errs.append("background 0 is not modal")
    comps6 = _components(grid, 6)
    if not comps6:
        errs.append("no color-6 template blob: the oracle has no largest object")
    else:
        sizes = sorted((len(c) for c in comps6), reverse=True)
        if sizes[0] < 3:
            errs.append(f"largest 6-blob has {sizes[0]} cells (< 3)")
        if len(sizes) > 1 and sizes[0] == sizes[1]:
            errs.append(f"tie for largest 6-blob ({sizes[0]} cells): "
                        "template selection is ambiguous")
        template = max(comps6, key=len)
        template_h = max(r for r, _ in template) - min(r for r, _ in template) + 1
        template_w = max(c for _, c in template) - min(c for _, c in template) + 1
        clipping_markers = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == 2
            and (r + template_h > h or c + template_w > w)
        ]
        if clipping_markers:
            errs.append(
                f"{len(clipping_markers)} marker stamp(s) clip the grid edge; "
                f"first at {clipping_markers[0]} for a "
                f"{template_h}x{template_w} template"
            )
    for cells in _components(grid, 2):
        if len(cells) > 1:
            errs.append(f"color-2 component of {len(cells)} cells is not an "
                        f"isolated marker at {cells[0]}")
    touching_markers = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] != 0
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            ):
                touching_markers.append((r, c))
    if touching_markers:
        errs.append(
            f"{len(touching_markers)} marker(s) touch another nonzero input "
            f"cell under 8-connectivity; first at {touching_markers[0]}"
        )
    return errs


def observe_overrides(grid):
    """Report per-draw realized values of exact semantic axes (KRF-0002),
    derived from the grid itself: n_markers counts isolated color-2
    singletons; decoy is True when a strictly smaller second 6-blob exists
    beside the unique largest template."""
    comps2 = _components(grid, 2)
    comps6 = _components(grid, 6)
    sizes = sorted((len(c) for c in comps6), reverse=True)
    return {"n_markers": sum(1 for c in comps2 if len(c) == 1),
            "decoy": len(sizes) > 1}


def profile_signature(grid):
    """Complete linked official-profile signature derived from a returned grid.

    The signature keeps dimensions, marker count, exact normalized template
    morphology, and decoy presence linked. Malformed/tied templates return
    ``None`` rather than being counted as canonical-like.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    comps6 = _components(grid, 6)
    comps2 = _components(grid, 2)
    if not comps6 or any(len(cells) != 1 for cells in comps2):
        return None
    sizes = sorted((len(cells) for cells in comps6), reverse=True)
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        return None
    template = max(comps6, key=len)
    r0 = min(r for r, _ in template)
    c0 = min(c for _, c in template)
    normalized = tuple(sorted((r - r0, c - c0) for r, c in template))
    return (
        len(grid),
        len(grid[0]),
        len(comps2),
        normalized,
        len(comps6) > 1,
    )


def rule_mirror(grid):
    """Independent Python mirror of the canonical Racket rule."""
    h, w = len(grid), len(grid[0])
    comps6 = _components(grid, 6)
    if not comps6:
        raise ValueError("cannot stamp without a color-6 template")
    template = max(comps6, key=len)
    r0 = min(r for r, _ in template)
    c0 = min(c for _, c in template)
    rel = [(r - r0, c - c0) for r, c in template]
    out = full_grid(h, w, 0)
    for marker_r in range(h):
        for marker_c in range(w):
            if grid[marker_r][marker_c] != 2:
                continue
            for dr, dc in rel:
                r, c = marker_r + dr, marker_c + dc
                if 0 <= r < h and 0 <= c < w:
                    out[r][c] = 6
    return out


def _small_blob(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = _DIRS4[rng.randrange(4)]
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _cells_clear(g, cells, pad=1):
    h, w = len(g), len(g[0])
    for (r, c) in cells:
        for dr in range(-pad, pad + 1):
            for dc in range(-pad, pad + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def _place_decoy(g, rng, tpl_size):
    """Strictly smaller isolated 6-blob decoy; False when nothing fits."""
    h, w = len(g), len(g[0])
    for _ in range(40):
        dsz = rng.randint(1, tpl_size - 1)
        rel = _small_blob(rng, dsz)
        dh = max(r for r, _ in rel) + 1
        dw = max(c for _, c in rel) + 1
        if dh > h or dw > w:
            continue
        r0 = rng.randint(0, h - dh)
        c0 = rng.randint(0, w - dw)
        cells = [(r0 + a, c0 + b) for a, b in rel]
        if _cells_clear(g, cells):
            for r, c in cells:
                g[r][c] = 6
            return True
    # Deterministic fallback: a single isolated 6 cell anywhere.
    for r in range(h):
        for c in range(w):
            if _cells_clear(g, [(r, c)]):
                g[r][c] = 6
                return True
    return False


def _place_markers(g, rng, n_markers, th, tw):
    """Isolated singleton 2-markers on empty cells with the stamp fitting
    in-bounds; markers are 8-separated from every other nonzero input object.
    Exact count or ValueError."""
    h, w = len(g), len(g[0])

    def free(mr, mc):
        return _cells_clear(g, [(mr, mc)])

    placed = 0
    for _ in range(120):
        if placed >= n_markers:
            return
        mr = rng.randint(0, h - th)
        mc = rng.randint(0, w - tw)
        if free(mr, mc):
            g[mr][mc] = 2
            placed += 1
    for mr in range(0, h - th + 1):
        for mc in range(0, w - tw + 1):
            if placed >= n_markers:
                return
            if free(mr, mc):
                g[mr][mc] = 2
                placed += 1
    raise ValueError(
        f"cannot place {n_markers} isolated markers with a {th}x{tw} stamp "
        f"on a {h}x{w} grid")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = dict(overrides)
    if overrides.get("texture") == "none":
        overrides.pop("texture")
    if overrides.get("decoy") is not None:
        raw_decoy = overrides["decoy"]
        if isinstance(raw_decoy, bool):
            overrides["decoy"] = raw_decoy
        elif (
            isinstance(raw_decoy, str)
            and raw_decoy.strip().lower() in ("true", "false")
        ):
            overrides["decoy"] = raw_decoy.strip().lower() == "true"
        else:
            raise ValueError(
                "decoy must be bool or the string 'true'/'false'"
            )
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi, m_lo, m_hi, decoy_p = 8, 10, 11, 13, 1, 2, 0.25
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi, m_lo, m_hi, decoy_p = 11, 14, 13, 16, 3, 4, 0.75
    else:
        h_lo, h_hi, w_lo, w_hi, m_lo, m_hi, decoy_p = 9, 12, 12, 15, 2, 3, 0.5

    # Canonical-form prior (KRF-0003 + morphology residual): ~25% of
    # fully-unoverridden draws pin one of the five COMPLETE official linked
    # profiles (h, w, n_markers, exact template shape) through keyed draws;
    # template position, decoy coin, and marker positions stay random.
    # Generalized templates/decoys remain on the general path.
    canon_template = None
    if (
        texture is None
        and not any(
            k in overrides
            for k in ("grid_h", "grid_w", "n_markers", "decoy")
        )
    ):
        if ctx.draw_rng("canonical_prior").random() < 0.25:
            ch, cw, cn, ctpl = ctx.draw_choice(
                "canonical_form",
                _CANONICAL_FORMS,
            )
            for label, value in (("grid_h", ch), ("grid_w", cw)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
            overrides["n_markers"] = cn
            ctx.overrides["n_markers"] = cn
            ctx.draw_int("n_markers", cn, cn)
            canon_template = [tuple(cell) for cell in ctpl]
    # Exact overrides execute over the full declared valid range (or reject
    # loudly); band ranges apply to plain draws only.
    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", 8, 14)
    else:
        h = ctx.draw_int("grid_h", h_lo, h_hi)
    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", 11, 16)
    else:
        w = ctx.draw_int("grid_w", w_lo, w_hi)
    if texture == "no_markers":
        n_markers = ctx.draw_int("n_markers", 0, 0)
    elif texture == "packed_markers":
        n_markers = ctx.draw_int("n_markers", 4, 4)
    elif overrides.get("n_markers") is not None:
        n_markers = ctx.draw_int("n_markers", 0, 4)
    else:
        n_markers = ctx.draw_int("n_markers", m_lo, m_hi)
    if texture == "no_decoy":
        want_decoy = ctx.draw_choice("decoy", [False])
    elif overrides.get("decoy") is not None:
        want_decoy = ctx.draw_choice("decoy", [False, True])
    elif canon_template is not None:
        # official profiles carry exactly one 6-component: no decoy
        want_decoy = False
        ctx.overrides["decoy"] = False
        ctx.draw_choice("decoy", [False])
    else:
        want_decoy = rng.random() < decoy_p
        # KRF-0004 provenance: record the realized band-weighted outcome
        # under its declared exact axis label.
        ctx.overrides["decoy"] = want_decoy
        ctx.draw_choice("decoy", [want_decoy])

    g = full_grid(h, w, 0)
    tpl = canon_template if canon_template is not None else rng.choice(_TEMPLATES)
    th = max(r for r, _ in tpl) + 1
    tw = max(c for _, c in tpl) + 1
    tr = rng.randint(0, h - th)
    tc = rng.randint(0, w - tw)
    for dr, dc in tpl:
        g[tr + dr][tc + dc] = 6
    if want_decoy and not _place_decoy(g, rng, len(tpl)):
        raise ValueError(f"no room for a decoy blob on a {h}x{w} grid")
    if n_markers:
        _place_markers(g, rng, n_markers, th, tw)
    return g
