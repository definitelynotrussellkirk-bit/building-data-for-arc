"""Generator for 973bec16d719 — extrapolate the next panel in a growing-shape sequence.

Canonical task: the input is a three-panel sequence.  The first two panels contain
one or more payload colors over an identical decorative common background; the
last panel is the blank canvas.  The rule extracts the payload colors that are
not common to every panel and paints the next growth step into the blank panel.

Combinatorial axes (8): grid_h/w, panel_height, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
payload_color.
Degenerates: no_panels, no_payload, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "973bec16d719"
RULE_HASH = "51e459e89ee3"  # canonical rule this generator was written against
VERSION = "2.1.0"  # replace sparse 0-bg two-dot panels with canonical-like patterned common panels
TASK_ID = "973bec16d719"
SUMMARY = (
    "Tall grid with three equal-height vertical panels. Every panel has the "
    "same nonzero common background plus many repeated common decorative "
    "components. The top two panels contain a payload bar in one non-common "
    "color; panel 2 is panel 1 grown by one cell horizontally. The third "
    "panel has only the common pattern, so the canonical rule outputs the "
    "extrapolated next panel."
)

INVARIANTS = [
    "input is exactly three same-sized vertical panels",
    "common background/decorative colors are present in all panels",
    "at least one payload color appears in the first two panels only",
    "the second payload shape strictly extends the first shape",
    "the blank third panel preserves the common decorative pattern",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_panels", "no_payload", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varied", "valid": "varied"},
    "grid_w":         {"type": "int", "default": "varied", "valid": "varied"},
    "panel_height":   {"type": "int", "default": "rng 7..9", "valid": "7..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "payload_color":  {"type": "color", "default": "rng !{0}",
                       "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_panels|no_payload|full_grid"},
}


def _palette_for(kind: str, rng):
    palettes = {
        "warm":    [(1, 4, 8, 3), (2, 8, 4, 1), (3, 1, 6, 4)],
        "cool":    [(8, 2, 6, 4), (1, 8, 2, 6), (3, 8, 1, 6)],
        "broad":   [(1, 4, 8, 3), (2, 8, 1, 4), (3, 1, 6, 8)],
        "primary": [(2, 8, 1, 4), (1, 3, 6, 4), (8, 2, 4, 1)],
    }
    return rng.choice(palettes.get(kind, palettes["broad"]))


def _common_panel(ph: int, pw: int, bg: int, deco_a: int, deco_b: int):
    """Repeated canonical-like common pattern with many disconnected objects."""
    panel = full_grid(ph, pw, bg)

    # Four corner/edge motifs: enough disconnected common components to match the
    # object-count scale of the original panels, but leave a clear middle lane for
    # the growing payload.
    motifs = [
        [(0, 1), (1, 0), (1, 1)],
        [(0, pw - 2), (1, pw - 2), (1, pw - 1)],
        [(ph - 2, 0), (ph - 2, 1), (ph - 1, 1)],
        [(ph - 2, pw - 1), (ph - 2, pw - 2), (ph - 1, pw - 2)],
    ]
    for mot in motifs:
        for r, c in mot:
            panel[r][c] = deco_a

    # Isolated inner "registration" dots in another common color.  They appear
    # in every panel, so the Racket rule treats them as part of the background
    # canvas, not as growing payload.
    dot_cols = [2, pw - 3]
    for r in range(2, ph - 2, 2):
        for c in dot_cols:
            panel[r][c] = deco_b

    # A couple of edge ticks add canonical-style clutter without occupying the
    # central payload lane.
    for c in range(3, pw - 3, 3):
        panel[0][c] = deco_b
        panel[ph - 1][c] = deco_b
    return panel


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        ph = ctx.draw_int("panel_height", 7, 7)
        pw = 9 + rng.randint(0, 1)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_height", 9, 9)
        pw = 11 + rng.randint(0, 2)
    else:
        ph = ctx.draw_int("panel_height", 7, 9)
        pw = 9 + rng.randint(0, 4)

    palette_kind = overrides.get("palette_kind")
    if palette_kind not in PALETTE_KINDS:
        palette_kind = rng.choice(PALETTE_KINDS)
    bg, deco_a, deco_b, default_payload = _palette_for(palette_kind, rng)
    payload = ctx.draw_color("payload_color", exclude={0, bg, deco_a, deco_b})
    if payload in (bg, deco_a, deco_b, 0):
        payload = default_payload

    base = _common_panel(ph, pw, bg, deco_a, deco_b)
    panels = [[row[:] for row in base] for _ in range(3)]

    # Place a horizontal growth sequence in a clear central lane.  The canonical
    # examples include both 1->2 and 3->4 style growth; vary the starting length.
    lane_rows = [r for r in range(2, ph - 2) if r % 2 == 1] or [ph // 2]
    row = rng.choice(lane_rows)
    max_start = max(1, pw - 5)
    col = 2 + rng.randint(0, max_start - 1)
    start_len = 1 if difficulty == "easy" else rng.randint(1, 3)
    if col + start_len + 1 >= pw - 1:
        col = max(1, pw - start_len - 3)

    for dc in range(start_len):
        panels[0][row][col + dc] = payload
        panels[1][row][col + dc] = payload
    panels[1][row][col + start_len] = payload

    out = []
    for panel in panels:
        out.extend(panel)
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Verify three-panel canonical growth invariants for 973bec16d719."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h % 3 != 0:
        errs.append(f"height {h} is not divisible into three vertical panels")
        return errs
    ph = h // 3
    panels = [grid[i * ph:(i + 1) * ph] for i in range(3)]

    def colors(p):
        return {v for row in p for v in row}

    common = set.intersection(*(colors(p) for p in panels))
    all_colors = set.union(*(colors(p) for p in panels))
    payloads = all_colors - common
    if len(common) < 3:
        errs.append(f"expected >=3 common canvas colors, found {len(common)}")
    if not payloads:
        errs.append("no payload color absent from the blank panel")
        return errs
    for color in payloads:
        locs = []
        for p in panels:
            locs.append({(r, c) for r in range(ph) for c in range(w) if p[r][c] == color})
        if not locs[0]:
            errs.append(f"payload color {color} absent from first panel")
        if not locs[1]:
            errs.append(f"payload color {color} absent from second panel")
        if locs[2]:
            errs.append(f"payload color {color} leaks into blank panel")
        if locs[0] and not locs[0].issubset(locs[1]):
            errs.append(f"second panel does not preserve first payload cells for color {color}")
        if len(locs[1]) <= len(locs[0]):
            errs.append(f"second panel does not strictly grow color {color}")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(21, 8, 0)
    if name == "no_panels":
        g[5][3] = 3
        return g
    if name == "no_payload":
        for r in range(21):
            for c in range(8):
                g[r][c] = 1 if (r + c) % 3 else 8
        return g
    if name == "full_grid":
        for r in range(21):
            for c in range(8):
                g[r][c] = 3
        return g
    return g
