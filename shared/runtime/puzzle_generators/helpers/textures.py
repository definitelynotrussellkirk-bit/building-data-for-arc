"""Reusable cell-fill textures for puzzle generators.

Per CLAUDE.md generator-upgrades guide: each generator picks which
helpful textures it uses (`HELPFUL_TEXTURES = (...)`); the texture is
chosen via `ctx.draw_choice("texture", HELPFUL_TEXTURES)` and rendered
via `fill_texture(name, h, w, palette, rng, ...)`.

Every texture function returns a fresh `list[list[int]]` of shape h×w.
Cells use values from `palette` (a list of color ints); `palette[0]`
is treated as background by convention but textures may override it
(e.g., monochrome).
"""
from __future__ import annotations

from puzzle_generators.helpers.grid import full_grid


# ---------------------------------------------------------------------
#  Helpful textures — clear distribution of cell content. All return
#  a fresh grid; no rule-specific awareness.
# ---------------------------------------------------------------------

def t_noise(h, w, palette, rng):
    """Fully random per cell over the palette."""
    g = full_grid(h, w, palette[0])
    for r in range(h):
        for c in range(w):
            g[r][c] = rng.choice(palette)
    return g


def t_sparse(h, w, palette, rng, density=None):
    """Background dominant; ~density fraction of cells take a non-bg color.
    `density` defaults to a per-call random in [0.10, 0.35]."""
    if density is None:
        density = rng.uniform(0.10, 0.35)
    g = full_grid(h, w, palette[0])
    fgs = palette[1:] if len(palette) > 1 else palette
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(fgs)
    return g


def t_blob(h, w, palette, rng, n_blobs=None):
    """1-3 solid-color rectangles planted on background."""
    if n_blobs is None:
        n_blobs = rng.randint(1, max(1, min(3, max(1, len(palette) - 1))))
    g = full_grid(h, w, palette[0])
    fgs = palette[1:] if len(palette) > 1 else palette
    for _ in range(n_blobs):
        color = rng.choice(fgs)
        bh = rng.randint(1, max(1, h // 2))
        bw = rng.randint(1, max(1, w // 2))
        r0 = rng.randint(0, h - bh)
        c0 = rng.randint(0, w - bw)
        for rr in range(r0, r0 + bh):
            for cc in range(c0, c0 + bw):
                g[rr][cc] = color
    return g


def t_stripes(h, w, palette, rng, horizontal=None):
    """Solid-color horizontal or vertical bands."""
    if horizontal is None:
        horizontal = rng.random() < 0.5
    g = full_grid(h, w, palette[0])
    if horizontal:
        for r in range(h):
            color = rng.choice(palette)
            for c in range(w):
                g[r][c] = color
    else:
        for c in range(w):
            color = rng.choice(palette)
            for r in range(h):
                g[r][c] = color
    return g


def t_gradient(h, w, palette, rng):
    """Linear gradient along a random axis; cell color indexes by position
    along the axis modulo palette size. Same texture before and after a
    transform reveals which axis the rule operated on."""
    axis = rng.choice(["row", "col", "diag", "antidiag"])
    g = full_grid(h, w, palette[0])
    n = len(palette)
    for r in range(h):
        for c in range(w):
            if axis == "row":
                idx = r * n // max(1, h)
            elif axis == "col":
                idx = c * n // max(1, w)
            elif axis == "diag":
                idx = (r + c) * n // max(1, h + w)
            else:  # antidiag
                idx = (r - c + w) * n // max(1, h + w)
            g[r][c] = palette[idx % n]
    return g


def t_checkerboard(h, w, palette, rng):
    """Two-color alternating checker. Choose two distinct colors from
    palette."""
    if len(palette) < 2:
        return t_noise(h, w, palette, rng)
    a, b = rng.sample(palette, 2)
    g = full_grid(h, w, a)
    for r in range(h):
        for c in range(w):
            g[r][c] = a if (r + c) % 2 == 0 else b
    return g


def t_frame(h, w, palette, rng):
    """Border cells one color, interior another. Tests that transforms
    preserve framing structure."""
    if len(palette) < 2:
        return t_noise(h, w, palette, rng)
    border, interior = rng.sample(palette, 2)
    g = full_grid(h, w, interior)
    for c in range(w):
        g[0][c] = border
        g[h - 1][c] = border
    for r in range(h):
        g[r][0] = border
        g[r][w - 1] = border
    return g


def t_ring(h, w, palette, rng):
    """Concentric rings (border, then 1-cell-in border, etc.) of cycling
    colors."""
    g = full_grid(h, w, palette[0])
    n = len(palette)
    layers = (min(h, w) + 1) // 2
    for layer in range(layers):
        color = palette[layer % n]
        for r in range(layer, h - layer):
            for c in range(layer, w - layer):
                if r == layer or r == h - layer - 1 or c == layer or c == w - layer - 1:
                    g[r][c] = color
    return g


def t_plus(h, w, palette, rng):
    """A plus-shape (full middle row + full middle col) on a bg, with
    optional accent corners."""
    if len(palette) < 2:
        return t_noise(h, w, palette, rng)
    bg, fg = palette[0], rng.choice(palette[1:])
    g = full_grid(h, w, bg)
    mid_r = h // 2
    mid_c = w // 2
    for c in range(w):
        g[mid_r][c] = fg
    for r in range(h):
        g[r][mid_c] = fg
    return g


# ---------------------------------------------------------------------
#  Cross-cutting modifiers — apply over a base texture.
# ---------------------------------------------------------------------

def apply_bg_density(g, palette, rng, target_bg_fraction):
    """Resample cells so ~target_bg_fraction of them become bg (palette[0]).
    Useful for biasing a texture toward sparse / dense regimes."""
    for r in range(len(g)):
        for c in range(len(g[0])):
            if rng.random() < target_bg_fraction:
                g[r][c] = palette[0]
    return g


def apply_noise_overlay(g, palette, rng, fraction):
    """Perturb `fraction` of cells with a random palette color. Adds
    realistic-looking noise to clean structured patterns."""
    for r in range(len(g)):
        for c in range(len(g[0])):
            if rng.random() < fraction:
                g[r][c] = rng.choice(palette)
    return g


def apply_border(g, palette, rng, mode):
    """Force border cells to a specific color regime.
      mode == 'always_bg' : border = palette[0]
      mode == 'always_fg' : border = a non-bg color uniform around the edge
      mode == 'free'      : leave as-is
    """
    if mode == "free":
        return g
    h, w = len(g), len(g[0])
    if mode == "always_bg":
        color = palette[0]
    else:  # always_fg
        color = rng.choice(palette[1:]) if len(palette) > 1 else palette[0]
    for c in range(w):
        g[0][c] = color
        g[h - 1][c] = color
    for r in range(h):
        g[r][0] = color
        g[r][w - 1] = color
    return g


# ---------------------------------------------------------------------
#  Texture dispatcher
# ---------------------------------------------------------------------

_TEXTURES = {
    "noise":        t_noise,
    "sparse":       t_sparse,
    "blob":         t_blob,
    "stripes":      t_stripes,
    "gradient":     t_gradient,
    "checkerboard": t_checkerboard,
    "frame":        t_frame,
    "ring":         t_ring,
    "plus":         t_plus,
}


def fill_texture(name, h, w, palette, rng):
    """Render a named helpful texture. Unknown names fall back to noise."""
    fn = _TEXTURES.get(name, t_noise)
    return fn(h, w, palette, rng)


def all_helpful_names():
    """List of all helpful texture names registered in this module."""
    return tuple(_TEXTURES.keys())
