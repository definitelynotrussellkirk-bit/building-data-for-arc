"""Generate isolated yellow objects whose bounding-box corners are marked blue.

The ordinary generator exposes exact, observable controls for canvas size,
target count, distractor count, and distractor palette.  Negative texture
fixtures remain explicit opt-ins and are never selected by default.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc5f4c1fd7c2"
TASK_ID = "fc5f4c1fd7c2"
VERSION = "2.2.2"
RULE_HASH = "ee5da7203b6e"
SUMMARY = (
    "A zero-background grid contains isolated connected yellow (4) target "
    "objects with nondegenerate bounding boxes and optional isolated nonyellow "
    "distractors.  Mark the four bounding-box corners of every yellow object "
    "blue (1); leave distractors unchanged."
)

INVARIANTS = [
    "background is 0",
    "every color-4 target is connected and has a bbox spanning at least two rows and columns",
    "distractors use colors other than 0, 1, and 4",
    "all objects are separated by a one-cell halo",
    "accepted numeric overrides equal the realized canvas and object counts",
]

HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("solid_rects", "line_motifs", "single_cell_motifs")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
AXES = {
    "grid_h": {"type": "int", "default": "7..9 easy / 10..14 medium / 13..20 hard", "valid": "5..24"},
    "grid_w": {"type": "int", "default": "9..12 easy / 11..16 medium / 14..22 hard", "valid": "6..26"},
    "n": {"type": "int", "default": "1..2 easy / 2..4 medium / 3..6 hard targets", "valid": "1..6"},
    "n_distractor": {"type": "int", "default": "0..1 easy / 1..3 medium / 2..5 hard", "valid": "0..5"},
    "texture": {"type": "str", "default": "keyed helpful palette", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_PALETTES = {
    "default": (2, 3, 5, 6, 7, 8, 9),
    "warm": (2, 3, 5, 9),
    "cool": (5, 6, 7, 8),
    "varied": (9, 8, 7, 6, 5, 3, 2),
}


def _incompatible(message: str, *axes: str):
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _exact_int(ctx, name: str, lo: int, hi: int, defaults: tuple[int, int]) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        value = ctx.overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            _incompatible(f"{name} must be an exact integer in {lo}..{hi}", name)
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, *defaults)


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    return cells


def _place(g, rng, cells, color):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1
    sw = max(cs) - min(cs) + 1
    if sh < 2 or sw < 2:
        return False
    # Ordinary motifs are deliberately irregular.  Solid rectangles remain
    # available only through the explicitly-labelled ``solid_rects`` fixture,
    # so self_check can reject shape-blind impostors without rejecting a
    # documented negative fixture.
    if len(set(cells)) == sh * sw:
        return False
    h, w = len(g), len(g[0])
    if sh > h or sw > w:
        return False
    for _ in range(180):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for r, c in cells:
            g[r0 + r - min(rs)][c0 + c - min(cs)] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}; supported: {sorted(AXES)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    if "texture" in overrides and overrides["texture"] is not None:
        if type(overrides["texture"]) is not str or overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture {overrides['texture']!r}")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture_options = HELPFUL_TEXTURES + DEGENERATE_TEXTURES if overrides.get("texture") is not None else HELPFUL_TEXTURES
    texture = ctx.draw_choice("texture", texture_options)

    if difficulty == "easy":
        hr, wr, nr, ndr, kr = (7, 9), (9, 12), (1, 2), (0, 1), (3, 5)
    elif difficulty == "hard":
        hr, wr, nr, ndr, kr = (13, 20), (14, 22), (3, 6), (2, 5), (4, 8)
    else:
        hr, wr, nr, ndr, kr = (10, 14), (11, 16), (2, 4), (1, 3), (3, 7)

    h = _exact_int(ctx, "grid_h", 5, 24, hr)
    w = _exact_int(ctx, "grid_w", 6, 26, wr)
    n = _exact_int(ctx, "n", 1, 6, nr)
    nd = _exact_int(ctx, "n_distractor", 0, 5, ndr)

    if texture in DEGENERATE_TEXTURES:
        if any(name in overrides for name in ("n", "n_distractor")):
            _incompatible("negative texture fixtures have fixed object counts", "texture", "n", "n_distractor")
        return _draw_from_degenerate(texture, h=h, w=w)

    rng = ctx.draw_rng("layout")
    colors = _PALETTES[texture]
    for _outer in range(80):
        g = full_grid(h, w, 0)
        placed_targets = 0
        for _ in range(max(1, n) * 16):
            if placed_targets >= n:
                break
            k_hi = max(3, min(kr[1], max(3, (h + w) // 4)))
            k_lo = min(kr[0], k_hi)
            if _place(g, rng, _build_motif(rng, rng.randint(k_lo, k_hi)), 4):
                placed_targets += 1
        if placed_targets != n:
            continue

        placed_distractors = 0
        for _ in range(max(1, nd) * 16):
            if placed_distractors >= nd:
                break
            k_hi = max(3, min(kr[1], max(3, (h + w) // 4)))
            k_lo = min(kr[0], k_hi)
            if _place(g, rng, _build_motif(rng, rng.randint(k_lo, k_hi)), rng.choice(colors)):
                placed_distractors += 1
        if placed_distractors != nd:
            continue
        return g

    involved = tuple(name for name in ("grid_h", "grid_w", "n", "n_distractor") if name in overrides)
    _incompatible("requested object counts could not be packed with a one-cell halo", *(involved or ("grid_h", "grid_w", "n", "n_distractor")))


def _components_by_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def observe_overrides(grid):
    distractors = sum(len(_components_by_color(grid, color)) for color in range(2, 10) if color != 4)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n": len(_components_by_color(grid, 4)),
        "n_distractor": distractors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    bad = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if type(v) is not int or not 0 <= v <= 9]
    if bad:
        r, c, v = bad[0]
        errors.append(f"out-of-range value {v} at ({r},{c})")
    if any(v == 1 for row in grid for v in row):
        errors.append("input must not already contain color 1; color 1 is the output marker")

    target_comps = _components_by_color(grid, 4)
    explicit_negative = (meta or {}).get("texture") in DEGENERATE_TEXTURES
    if not target_comps and not explicit_negative:
        errors.append("expected at least one color-4 target component")
    occupied = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    for comp in target_comps:
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        if len(set(rs)) < 2 or len(set(cs)) < 2:
            if not explicit_negative:
                errors.append("color-4 target component has degenerate bbox (<2 rows or <2 cols)")
            break
        bbox_area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if len(comp) == bbox_area and not explicit_negative:
            errors.append(
                "color-4 target component is a solid rectangle; ordinary grammar requires an irregular target"
            )
            break
        for r, c in comp:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in comp:
                        continue
                    if (nr, nc) in occupied:
                        errors.append("color-4 target is not separated from another motif by a zero halo")
                        return errors
    return errors


def _draw_from_degenerate(name, rng=None, *, h=7, w=9):
    h, w = max(h, 7), max(w, 9)
    g = full_grid(h, w, 0)
    if name == "solid_rects":
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][c] = 4
        for r in range(h - 2, h):
            for c in range(w - 4, w - 1):
                g[r][c] = 6
        return g
    if name == "line_motifs":
        for c in range(1, 6):
            g[2][c] = 4
        for r in range(3, 6):
            g[r][w - 1] = 6
        return g
    if name == "single_cell_motifs":
        g[2][2] = 4
        g[h - 2][w - 2] = 6
        return g
    raise ValueError(f"unknown negative texture {name!r}")
