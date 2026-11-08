"""Generator for ARC task 8be77c9e.

Rule: output is 2h x w with the input on top and its up-down mirror on
the bottom (`vconcat g (flip-ud g)`).

Combinatorial axes (5): grid_h, grid_w, palette_size, texture,
ud_asymmetric.  Degenerates: single_row (h=1 — mirror is a duplicate,
the ambiguity case), ud_symmetric (mirror == tile, the other ambiguity
case).  Both ambiguity textures are opt-in only; default draws are
always UD-asymmetric so 'tile the input twice' never fits the demos.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import fill_texture

GENERATOR_ID = "7f181d3b0012"
RULE_HASH = "738584ea6289"  # canonical rule this generator was verified against
VERSION = "3.1.1"  # Reject unknown overrides; align the canonical mixture; declare lesson rivals.
TASK_ID = "7f181d3b0012"

SUMMARY = (
    "Small colored grid (canonical: 3x3 binary {0,1} with 2, 4, or 5 "
    "one-cells, UD- and LR-asymmetric; generated: h 1..15 x w 2..30, "
    "2-6 colors, with an explicit ~30% canonical-family mixture in "
    "default draws plus small/large generalization branches). Rule: "
    "output is a fresh grid of 2H x W. Top half = input verbatim. "
    "Bottom half = input mirrored vertically (flip-ud). Equivalently, "
    "output = vconcat(g, flip-ud(g)). Default draws are always "
    "UD-asymmetric so the mirror is distinguishable from plain "
    "duplication."
)

# Rivals: 'output is input' refuted by 2H dims. 'tile input vertically'
# refuted by UD-asymmetric content in every default demo. 'mirror LR
# then concat right' refuted by output width == input width. 'output is
# just flip-ud' refuted by the verbatim top half. 'rot180 on bottom'
# refuted by LR-asymmetric content in the bottom half.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input dims h 1..15 x w 2..30 so doubled output fits ARC's 30x30 limit",
    ">=2 distinct colors so the mirror is visible",
    "default draws are NOT UD-symmetric (mirror != duplication)",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("single_row", "ud_symmetric")

AXES = {
    "grid_h":        {"type": "int", "default": "rng small-biased triangular 2..9 (band-skewed)",
                      "valid": "1..15"},
    "grid_w":        {"type": "int", "default": "rng small-biased triangular 2..11 (band-skewed)",
                      "valid": "2..30"},
    "palette_size":  {"type": "int", "default": "rng 2..6 skewed to 2 (canonical is binary)",
                      "valid": "2..6"},
    "texture":       {"type": "str", "default": "rng helpful",
                      "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "ud_asymmetric": {"type": "bool", "default": "true",
                      "valid": "true|false"},
}


def _is_ud_sym(g):
    h = len(g)
    return all(g[r] == g[h - 1 - r] for r in range(h))


def _is_lr_sym(g):
    w = len(g[0])
    return all(row[c] == row[w - 1 - c] for row in g for c in range(w))


def _duplicate_vertical(grid):
    return [list(row) for row in grid] + [list(row) for row in grid]


def _rotate180_bottom(grid):
    return ([list(row) for row in grid]
            + [list(reversed(row)) for row in reversed(grid)])


# Lawful symmetric inputs remain available. Materialized lessons must refute
# these rivals whenever they would give a different query answer.
LESSON_COMPETITORS = {
    "duplicate_vertical": _duplicate_vertical,
    "rotate180_bottom": _rotate180_bottom,
}


def _canonical_family(rng):
    """The strict demonstrated family (pre-audit target: >=25% pooled default
    draws): 3x3, palette exactly {0,1}, 2, 4, or 5 one-cells, UD- and
    LR-asymmetric so neither 'tile twice' nor 'mirror LR' fits."""
    for _ in range(200):
        k = rng.choice((2, 4, 5))
        g = [[0] * 3 for _ in range(3)]
        for r, c in rng.sample([(r, c) for r in range(3) for c in range(3)], k):
            g[r][c] = 1
        if not _is_ud_sym(g) and not _is_lr_sym(g):
            return g
    return [[0, 0, 0], [1, 0, 1], [1, 1, 0]]  # deterministic valid fallback


def _tri(rng, lo, hi, mode):
    return max(lo, min(hi, int(round(rng.triangular(lo, hi + 0.999, mode)))))


def _draw_dim(ctx, rng, name, lo, hi, mode, band):
    """Exact when overridden (validated against the full declared range),
    otherwise a small-biased triangular draw so the canonical 3x3 prior
    stays the center of mass."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        vmin, vmax = (1, 15) if name == "grid_h" else (2, 30)
        return ctx.draw_int(name, vmin, vmax)
    if band == "easy":
        return _tri(rng, lo, min(hi, 6 if name == "grid_h" else 7), 3)
    if band == "hard":
        return _tri(rng, max(lo, 3), hi + (4 if name == "grid_h" else 5),
                    6 if name == "grid_h" else 7)
    return _tri(rng, lo, hi, mode)


def _symmetrize(g):
    h = len(g)
    for r in range(h // 2):
        g[h - 1 - r] = list(g[r])
    return g


def _break_symmetry(g, palette):
    h = len(g)
    if h < 2 or not _is_ud_sym(g):
        return g
    cur = g[0][0]
    alt = next((v for v in palette if v != cur), (cur + 1) % 10)
    g[0][0] = alt
    return g


def _ensure_palette_used(g, palette, rng, symmetric):
    """Stamp every missing palette color into the grid so the realized color
    count equals the palette size. Only overwrites cells whose color still
    appears elsewhere (or, symmetrically, their mirror partner), so no
    palette color is ever stamped out again — exact palette_size overrides
    cannot fall back silently."""
    h, w = len(g), len(g[0])
    for _ in range(64):
        present = {v for row in g for v in row}
        missing = [c for c in palette if c not in present]
        if not missing:
            return g
        color = missing[0]
        counts = {c: sum(row.count(c) for row in g) for c in present}
        if symmetric:
            cands = [(r, c) for r in range((h + 1) // 2) for c in range(w)
                     if counts.get(g[r][c], 0) > 1
                     and counts.get(g[h - 1 - r][c], 0) > 1]
            if not cands:
                cands = [(r, c) for r in range((h + 1) // 2) for c in range(w)]
        else:
            cands = [(r, c) for r in range(h) for c in range(w)
                     if counts.get(g[r][c], 0) > 1]
            if not cands:
                cands = [(r, c) for r in range(h) for c in range(w)]
        r, c = cands[rng.randrange(len(cands))]
        g[r][c] = color
        if symmetric:
            g[h - 1 - r][c] = color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override keys: {unknown}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    texture = overrides.get("texture")
    ud_req = overrides.get("ud_asymmetric")
    ud_req = None if ud_req is None else bool(ud_req)

    # Explicit canonical-family mixture (pre-audit target >=25% pooled
    # default draws). Default draws only: any requested exact axis takes
    # the draw through the general path instead. The family RNG is
    # band-keyed so easy/medium/hard do not share byte-identical draws.
    default_draw = not any(
        overrides.get(k) is not None
        for k in ("grid_h", "grid_w", "palette_size", "texture", "ud_asymmetric"))
    if default_draw:
        family_rng = ctx.draw_rng(f"family|{band}")
        if family_rng.random() < 0.30:
            g = _canonical_family(family_rng)
            _record_exact(ctx, 3, 3, 2, True)
            return g

    # Alias/conflict resolution between ud_asymmetric and the degenerate
    # textures (single_row forces h=1 and is always UD-symmetric).
    if texture == "single_row" and ud_req is True:
        raise ValueError("ud_asymmetric=True conflicts with texture='single_row'")
    if texture == "ud_symmetric" and ud_req is True:
        raise ValueError("ud_asymmetric=True conflicts with texture='ud_symmetric'")
    if overrides.get("grid_h") == 1 and ud_req is True:
        raise ValueError("ud_asymmetric=True cannot hold on a 1-row grid")
    symmetric = texture == "ud_symmetric" or ud_req is False

    if texture == "single_row":
        if overrides.get("grid_h") not in (None, 1):
            raise ValueError("texture='single_row' forces grid_h=1")
        h = 1
        w = ctx.draw_int("grid_w", 2, 30) if "grid_w" in overrides else _tri(rng, 2, 11, 3)
    else:
        h = _draw_dim(ctx, rng, "grid_h", 2, 9, 3, band)
        w = _draw_dim(ctx, rng, "grid_w", 2, 11, 3, band)

    # palette_size: exact when requested, else skewed to the canonical binary.
    if "palette_size" in overrides and overrides["palette_size"] is not None:
        n_colors = ctx.draw_int("palette_size", 2, 6)
        # exact-or-loud: the grid must have room to realize that many colors
        symmetric_eff = symmetric or h == 1
        capacity = ((h + 1) // 2) * w if symmetric_eff else h * w
        if capacity < n_colors:
            if "grid_h" in overrides or "grid_w" in overrides or texture == "single_row":
                raise ValueError(
                    f"palette_size={n_colors} cannot fit a {h}x{w} "
                    f"{'symmetric ' if symmetric_eff else ''}grid")
            w = max(w, (n_colors + ((h + 1) // 2) - 1) // ((h + 1) // 2)
                    if symmetric_eff else (n_colors + h - 1) // h)
            if h * w < n_colors:
                raise ValueError(f"palette_size={n_colors} cannot fit a {h}x{w} grid")
    elif band == "easy":
        n_colors = 2
    elif band == "medium":
        n_colors = 2 if rng.random() < 0.7 else 3
    else:
        n_colors = 2 if rng.random() < 0.5 else rng.randint(3, 5)
    # unrequested palette size is nuisance: clamp to what the grid can show
    symmetric_eff = symmetric or h == 1
    capacity = ((h + 1) // 2) * w if symmetric_eff else h * w
    n_colors = min(n_colors, capacity)
    if n_colors == 2 and rng.random() < 0.5:
        palette = (0, 1)  # canonical binary prior
    else:
        palette = ctx.draw_distinct_colors("palette", n=n_colors)

    if texture == "single_row":
        g = [[rng.choice(palette) for _ in range(w)]]
    else:
        if texture in HELPFUL_TEXTURES:
            kind = texture
        elif texture in DEGENERATE_TEXTURES:
            kind = rng.choice(HELPFUL_TEXTURES)  # nuisance base under the degenerate mode
        else:
            kind = ctx.draw_choice("texture", list(HELPFUL_TEXTURES))
        g = fill_texture(kind, h, w, list(palette), rng)
        if symmetric:
            g = _symmetrize(g)
        elif _is_ud_sym(g):
            g = _break_symmetry(g, palette)
    g = _ensure_palette_used(g, palette, rng, symmetric_eff)
    _record_exact(ctx, h, w, n_colors, not symmetric_eff)
    return g


def _record_exact(ctx, h, w, n_colors, ud_asym):
    """KRF-0004 keyed provenance: record the realized exact axes under their
    declared labels on every return path. Degenerate [v, v] typed draws
    return the realized value exactly and draw from per-label streams, so
    the layout/family streams (and therefore the distribution) are
    untouched."""
    ctx.draw_int("grid_h", h, h)
    ctx.draw_int("grid_w", w, w)
    ctx.draw_int("palette_size", n_colors, n_colors)
    ctx.draw_choice("ud_asymmetric", [ud_asym])


def observe_overrides(grid):
    """Realized exact semantic axes, derived from the grid itself (KRF-0002)."""
    return {
        "palette_size": len({v for row in grid for v in row}),
        "ud_asymmetric": not _is_ud_sym(grid),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Declared envelope: rectangular h 1..15 x w 2..30, colors 0..9,
    >=2 distinct colors so the mirror is visible. The task's input
    manifold is 'any rectangular colored grid', so these bounds are the
    whole structural contract (UD symmetry is a declared opt-in branch,
    not a violation)."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular with nonzero width"]
    errors = []
    if not (1 <= h <= 15 and 2 <= w <= 30):
        errors.append(f"dims {h}x{w} outside declared envelope 1..15 x 2..30")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errors.append("colors must be ints in 0..9")
    if len(set(flat)) < 2:
        errors.append("need >=2 distinct colors so the mirror is visible")
    return errors
