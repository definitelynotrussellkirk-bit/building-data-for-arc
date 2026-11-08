"""Generator for 20b:m137 — match prototype under rotation and recolor.

Rule: prototype at subgrid (0,0)-(4,4); candidate panels at fixed cols
[6, 12, 18] (also rows 0-4). Target color at (5, 0). Find the panel
whose normalized binary matches the prototype under any rotation;
output is that panel's crop, recolored to target.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: rotation_symmetric_proto (prototype invariant under
rotation → all 3 candidates can match, rule's "find the one" is
ambiguous), all_match (every candidate is a rotation of prototype →
selector finds 3 valid panels), no_match (no candidate matches →
selector finds nothing, output undefined).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dec3e35da2bc"
VERSION = "2.1.0"  # input is rule-intrinsically fixed 6x23 (proto + 3 panels at cols 6/12/18 + target at (5,0)) so shape-lock-in is unavoidable; but shapes came from a FIXED 4-bank -> uniq 52%. Now RANDOM polyominoes (proto + rotation match + 2 non-equiv others) -> far more distinct outputs."
TASK_ID = "dec3e35da2bc"

SUMMARY = (
    "Fixed 6×23 grid, 0-bg. PROTOTYPE shape drawn at "
    "(0..4, 0..4) — a small polyomino in some color "
    "proto_color. THREE CANDIDATE PANELS at columns "
    "[6..10, 12..16, 18..22] each spanning rows "
    "0..4, in distinct candidate colors. EXACTLY ONE "
    "candidate's shape is a ROTATION (90°/180°/270°) "
    "of the prototype; the other two are unrelated "
    "shapes. A TARGET COLOR is placed at (5, 0). "
    "Rule: find the candidate panel whose normalized "
    "binary mask matches the prototype under some "
    "rotation (0°/90°/180°/270°). CROP that "
    "candidate, RECOLOR all its cells to the TARGET "
    "COLOR at (5, 0). Output: the small recolored "
    "crop. Net: prototype + rotation-match selector "
    "+ target color → output is the matching panel "
    "recolored."
)

INVARIANTS = [
    "background is 0",
    "grid is 6 rows tall and 23 cols wide",
    "prototype panel at rows 0..4 cols 0..4 (single color)",
    "3 candidate panels at rows 0..4 cols [6..10, 12..16, 18..22]",
    "exactly one candidate is rotation-equivalent to the prototype",
    "the other candidates are different shapes (not rotation-equivalent)",
    "cell (5,0) is the target color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("rotation_symmetric_proto", "all_match", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "fixed_proto_3candidates",
                       "valid": "fixed_proto_3candidates"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "fixed_layout", "valid": "fixed_layout"},
    "grid_h":         {"type": "int", "default": "6", "valid": "6..6"},
    "grid_w":         {"type": "int", "default": "23", "valid": "23..23"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rotate_cw(shape):
    rs = [r for r, _ in shape]
    h = max(rs) + 1
    return sorted([(c, h - 1 - r) for r, c in shape])


def _norm(shape):
    rmin = min(r for r, _ in shape); cmin = min(c for _, c in shape)
    return tuple(sorted((r - rmin, c - cmin) for r, c in shape))


def _rotations(shape):
    out = set(); s = shape
    for _ in range(4):
        out.add(_norm(s)); s = _rotate_cw(s)
    return out


def _rand_poly(rng, k, s=5):
    """Random connected k-cell polyomino fitting in s x s."""
    for _ in range(60):
        cells = [(0, 0)]; seen = {(0, 0)}
        for _ in range(200):
            if len(cells) >= k:
                break
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                cand = cells + [(nr, nc)]
                rs = [a for a, _ in cand]; cs = [b for _, b in cand]
                if max(rs) - min(rs) < s and max(cs) - min(cs) < s:
                    cells.append((nr, nc)); seen.add((nr, nc))
        if len(cells) == k:
            return list(_norm(cells))
    return [(0, 0), (0, 1), (1, 0)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    h = 6; w = 23   # rule-intrinsic fixed layout (proto + 3 panels at cols 6/12/18)
    # RANDOM prototype (asymmetric so a rotation differs); matching candidate is a
    # rotation; the other two are NOT rotation-equivalent to the prototype.
    proto_shape = _rand_poly(rng, rng.randint(3, 5))
    for _ in range(40):
        if len(_rotations(proto_shape)) >= 2:
            break
        proto_shape = _rand_poly(rng, rng.randint(3, 5))
    proto_rots = _rotations(proto_shape)
    rotated = list(proto_shape)
    for _ in range(rng.randint(1, 3)):
        rotated = list(_norm(_rotate_cw(rotated)))
    others = []
    for _ in range(200):
        if len(others) >= 2:
            break
        cand = _rand_poly(rng, rng.randint(3, 5))
        nc = _norm(cand)
        if nc not in proto_rots and all(nc != _norm(o) for o in others):
            others.append(cand)
    while len(others) < 2:
        others.append([(0, 0), (1, 0), (2, 0), (2, 1)])
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 5)
    proto_color = palette[0]
    cand_colors = palette[1:4]
    target_color = palette[4]
    g = full_grid(h, w, 0)
    for dr, dc in proto_shape:
        g[dr][dc] = proto_color
    panel_starts = [6, 12, 18]
    cand_shapes = [rotated] + others
    rng.shuffle(cand_shapes)
    for c0, color, shape in zip(panel_starts, cand_colors, cand_shapes):
        for dr, dc in shape:
            if 0 <= dr < 5 and 0 <= dc < 5:
                g[dr][c0 + dc] = color
    g[5][0] = target_color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 23
    g = full_grid(h, w, 0)
    panel_starts = [6, 12, 18]
    if name == "rotation_symmetric_proto":
        # Prototype is a single cell — invariant under all rotations.
        # All 3 candidates can match; rule's selector is ambiguous.
        proto = [(0, 0)]
        for dr, dc in proto: g[dr][dc] = 1
        for c0, color in zip(panel_starts, [3, 4, 5]):
            for dr, dc in [(0, 0), (1, 0)]:
                g[dr][c0 + dc] = color
        g[5][0] = 7
        return g
    if name == "all_match":
        # Every candidate is a rotation of the prototype — selector
        # finds 3 matches; rule's "the one" branch ambiguous.
        proto = [(0, 0), (0, 1), (1, 0)]
        for dr, dc in proto: g[dr][dc] = 1
        rotations = [proto, _rotate_cw(proto), _rotate_cw(_rotate_cw(proto))]
        for c0, color, shape in zip(panel_starts, [3, 4, 5], rotations):
            for dr, dc in shape:
                g[dr][c0 + dc] = color
        g[5][0] = 7
        return g
    if name == "no_match":
        # No candidate matches the prototype under any rotation —
        # selector finds nothing; output undefined.
        proto = [(0, 0), (0, 1), (1, 0)]
        for dr, dc in proto: g[dr][dc] = 1
        non_matching = [
            [(0, 0), (1, 0), (2, 0), (3, 0)],
            [(0, 0), (0, 1), (0, 2), (0, 3)],
            [(0, 0), (1, 1), (2, 2), (3, 3)],
        ]
        for c0, color, shape in zip(panel_starts, [3, 4, 5], non_matching):
            for dr, dc in shape:
                if 0 <= dr < h and 0 <= c0 + dc < w:
                    g[dr][c0 + dc] = color
        g[5][0] = 7
        return g
    return g


def _panel_shape(grid, c0):
    return [(r, c) for r in range(5) for c in range(5) if grid[r][c0 + c] != 0]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the prototype/rotated-candidate selector."""
    if len(grid) != 6 or any(len(row) != 23 for row in grid):
        return ["grid is not the rule-intrinsic 6x23 layout"]
    errs: list[str] = []
    if grid[5][0] == 0:
        errs.append("target color cell (5,0) is background")
    proto = [(r, c) for r in range(5) for c in range(5) if grid[r][c] != 0]
    if not proto:
        errs.append("prototype panel is empty")
        proto_rots = set()
    else:
        proto_colors = {grid[r][c] for r, c in proto}
        if len(proto_colors) != 1:
            errs.append(f"prototype uses multiple colors: {sorted(proto_colors)}")
        proto_rots = _rotations(proto)
    matches = 0
    shapes = []
    for c0 in (6, 12, 18):
        shape = _panel_shape(grid, c0)
        if not shape:
            errs.append(f"candidate panel at col {c0} is empty")
            continue
        cand_colors = {grid[r][c0 + c] for r, c in shape}
        if len(cand_colors) != 1:
            errs.append(f"candidate panel at col {c0} uses multiple colors: {sorted(cand_colors)}")
        norm = _norm(shape)
        shapes.append(norm)
        if norm in proto_rots:
            matches += 1
    if matches != 1:
        errs.append(f"expected exactly one rotation-equivalent candidate, got {matches}")
    if len(shapes) != len(set(shapes)):
        errs.append("candidate panel shapes are not distinct")
    return errs
