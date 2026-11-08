"""Tiny monochrome L orientations choose the enlarged border-L corners.

Odd square 5..15 with a nonzero background; one to four distinct orientations; colors may repeat across
separate 4-connected components and zero is an ordinary color. Placement is
independent of orientation. Different colors may touch or interlock. Same-color
components may not touch orthogonally. Explicit uniform diagnostic textures are
negative examples outside the default, nonidentity training distribution.
"""
from __future__ import annotations

from collections import Counter
from numbers import Integral

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "3ab9aab86992"
VERSION = "2.1.0"
RULE_HASH = "bbdf13ba2dfd"
SUMMARY = "Tiny L triomino orientations select large output corner placements."
INVARIANTS = [
    "odd square canvas 5..15 with a nonzero strict-majority background",
    "one to four monochrome 4-connected L triominoes, each in a 2x2 box",
    "each orientation occurs at most once; repeated colors remain separate objects",
    "orientation, not position or color, selects the corresponding output corner",
    "uniform no_corners/full_grid textures are explicit rejection diagnostics only",
]
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
LAYOUTS = ("scatter", "clustered", "separated")
DEGENERATE_TEXTURES = ("no_corners", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS + ("all_corners",)
AXES = {
    "canvas_size": {"type": "int", "default": "difficulty-dependent odd 5..15", "valid": "5|7|9|11|13|15"},
    "bg_color": {"type": "color", "default": "rng nonzero", "valid": "1..9"},
    "n_corners": {"type": "int", "default": "difficulty-dependent 1..4", "valid": "1..4"},
    "palette_kind": {"type": "str", "default": "rng", "valid": "|".join(PALETTE_KINDS)},
    "palette_size": {"type": "int", "default": "rng 1..n_corners", "valid": "1..4", "constraint": "<= n_corners"},
    "layout": {"type": "str", "default": "rng", "valid": "|".join(LAYOUTS)},
    "texture": {"type": "str", "default": "palette_kind", "valid": "|".join(HELPFUL_TEXTURES), "diagnostic": "|".join(DEGENERATE_TEXTURES)},
}

# The occupied vertex, not the missing vertex, is the destination corner.
_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),  # TL
    ((0, 0), (0, 1), (1, 1)),  # TR
    ((0, 0), (1, 0), (1, 1)),  # BL
    ((0, 1), (1, 0), (1, 1)),  # BR
)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SIZES = (5, 7, 9, 11, 13, 15)


def _components(grid, bg):
    """Same-color, four-connected objects; matches the reference DSL contract."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == bg or (r, c) in seen:
                continue
            todo, cells = [(r, c)], []
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                cells.append((y, x))
                for dy, dx in _NEIGHBORS:
                    yy, xx = y + dy, x + dx
                    if (0 <= yy < h and 0 <= xx < w and
                            (yy, xx) not in seen and grid[yy][xx] == color):
                        seen.add((yy, xx))
                        todo.append((yy, xx))
            result.append((color, cells))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, merged, non-L, or conflicting-orientation components."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid or unsupported grid container"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["empty or malformed row"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != w or h not in _SIZES:
        return ["canvas must be an odd square of side 5..15"]
    if any(isinstance(v, bool) or not isinstance(v, Integral) or not 0 <= v <= 9
           for row in grid for v in row):
        return ["cells must be integer colors 0..9 (not booleans)"]
    counts = Counter(v for row in grid for v in row)
    bg, count = counts.most_common(1)[0]
    if bg == 0:
        return ["background must be nonzero because Racket mode excludes zero"]
    if count * 2 <= h * w:
        return ["background must occupy a strict majority"]
    if len(counts) == 1:
        return ["uniform grid has no L evidence; diagnostic only"]
    objs = _components(grid, bg)
    errors = []
    if not 1 <= len(objs) <= 4:
        errors.append("expected one to four L components")
    orientations = set()
    for color, cells in objs:
        y = min(r for r, c in cells)
        x = min(c for r, c in cells)
        shape = frozenset((r-y, c-x) for r, c in cells)
        if len(cells) != 3 or shape not in tuple(map(frozenset, _SHAPES)):
            errors.append(f"color {color} component at ({y},{x}) is not a 2x2 L triomino")
        elif shape in orientations:
            errors.append("duplicate orientation would compete for an output corner")
        orientations.add(shape)
    return errors


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    # Reject lossy coercion and bool-as-int before the shared context converts.
    for key in ("canvas_size", "bg_color", "n_corners", "palette_size"):
        value = overrides.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, Integral)):
            raise ValueError(f"{key} must be an integer")
    for key, legal in (("layout", LAYOUTS), ("palette_kind", PALETTE_KINDS),
                       ("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)):
        value = overrides.get(key)
        if value is not None and value not in legal:
            raise ValueError(f"invalid {key}: {value!r}")
    for key, lo, hi in (("bg_color", 1, 9), ("n_corners", 1, 4), ("palette_size", 1, 4)):
        value = overrides.get(key)
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{key} must be in {lo}..{hi}")
    if overrides.get("canvas_size") is not None and overrides["canvas_size"] not in _SIZES:
        raise ValueError("canvas_size must be odd and in 5..15")
    texture, kind = overrides.get("texture"), overrides.get("palette_kind")
    if texture in PALETTE_KINDS and kind is not None and texture != kind:
        raise ValueError("texture and palette_kind select conflicting palettes")
    if texture == "all_corners" and overrides.get("n_corners") not in (None, 4):
        raise ValueError("all_corners requires n_corners=4")
    if (overrides.get("palette_size") is not None and overrides.get("n_corners") is not None
            and overrides["palette_size"] > overrides["n_corners"]):
        raise ValueError("palette_size must not exceed n_corners")


def _already_solved(grid, size, bg, orientations, colors):
    # For side >=7, output Ls have more than three cells, so identity is impossible.
    if size != 5:
        return False
    expected = full_grid(size, size, bg)
    for orient, color in zip(orientations, colors):
        r0, c0 = ((0, 0), (0, 3), (3, 0), (3, 3))[orient]
        for dr, dc in _SHAPES[orient]:
            expected[r0+dr][c0+dc] = color
    return grid == expected


def _anchored_grid(size, bg, orientations, colors, anchors, rng):
    anchors = list(anchors)
    rng.shuffle(anchors)
    # Cyclic reassignment preserves separation and destroys an identity layout.
    for shift in range(4):
        grid = full_grid(size, size, bg)
        places = anchors[shift:] + anchors[:shift]
        for orient, color, (r0, c0) in zip(orientations, colors, places):
            for dr, dc in _SHAPES[orient]:
                grid[r0+dr][c0+dc] = color
        if not _already_solved(grid, size, bg, orientations, colors):
            return grid
    raise RuntimeError("constructive placement failed to avoid identity")


def observe_overrides(grid):
    counts = Counter(v for row in grid for v in row)
    bg = counts.most_common(1)[0][0]
    objs = _components(grid, bg)
    return {"canvas_size": len(grid), "bg_color": bg, "n_corners": len(objs),
            "palette_size": len({color for color, _ in objs})}


def strict_canonical_like(grid):
    """Lawful orientation family; does not assert unique lesson identifiability."""
    return self_check(grid)


def rule_mirror(grid):
    """Geometry oracle, independently cross-checked against unchanged Racket."""
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    size = len(grid)
    k = (size-1)//2
    out = full_grid(size, size, bg)
    for color, cells in _components(grid, bg):
        r0 = min(r for r, c in cells); c0 = min(c for r, c in cells)
        shape = frozenset((r-r0, c-c0) for r, c in cells)
        orientation = tuple(map(frozenset, _SHAPES)).index(shape)
        bottom, right = orientation >= 2, orientation % 2 == 1
        rr, cc = size-1 if bottom else 0, size-1 if right else 0
        for offset in range(k):
            out[rr + (-offset if bottom else offset)][cc] = color
            out[rr][cc + (-offset if right else offset)] = color
    return out


def _incomplete_corner_set(grid):
    return not self_check(grid) and observe_overrides(grid)["n_corners"] < 4


def _complete_all_corners(grid):
    out = rule_mirror(grid)
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    foreground = sorted({v for row in grid for v in row if v != bg})
    if not foreground:
        return out
    size = len(grid); k = (size-1)//2
    for rr, cc in ((0, 0), (0, size-1), (size-1, 0), (size-1, size-1)):
        if out[rr][cc] == bg:
            for offset in range(k):
                out[rr + (offset if rr == 0 else -offset)][cc] = foreground[0]
                out[rr][cc + (offset if cc == 0 else -offset)] = foreground[0]
    return out


SEMANTIC_WITNESSES = {"incomplete_corner_set": _incomplete_corner_set}
SEMANTIC_RIVALS = {"complete_all_corners": _complete_all_corners}
WITNESS_RIVALS = {"incomplete_corner_set": ["complete_all_corners"]}
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _place(size, bg, orientations, colors, layout, rng):
    """Bounded randomized search, then a count-preserving constructive fallback.

    Unlike the previous halo test, legality is checked on actual occupied cells.
    An exact fallback exists even for four same-colored Ls on a 5x5 canvas.
    """
    grid = full_grid(size, size, bg)
    origin_r = rng.randrange(size - 4) if layout == "clustered" else 0
    origin_c = rng.randrange(size - 4) if layout == "clustered" else 0
    extent = 5 if layout == "clustered" else size
    anchors = [(origin_r, origin_c), (origin_r, origin_c + extent-2),
               (origin_r + extent-2, origin_c), (origin_r + extent-2, origin_c + extent-2)]
    if layout == "separated":
        return _anchored_grid(size, bg, orientations, colors, anchors, rng)
    candidates = []
    for orient in orientations:
        positions = [(origin_r+r, origin_c+c) for r in range(extent-1) for c in range(extent-1)]
        rng.shuffle(positions)
        candidates.append([[(r+dr, c+dc) for dr, dc in _SHAPES[orient]] for r, c in positions])
    budget = 10000

    def search(index):
        nonlocal budget
        if index == len(orientations):
            return not _already_solved(grid, size, bg, orientations, colors)
        color = colors[index]
        for cells in candidates[index]:
            if budget <= 0:
                return False
            budget -= 1
            if any(grid[r][c] != bg for r, c in cells):
                continue
            if any(0 <= r+dr < size and 0 <= c+dc < size and grid[r+dr][c+dc] == color
                   for r, c in cells for dr, dc in _NEIGHBORS):
                continue
            for r, c in cells:
                grid[r][c] = color
            if search(index+1):
                return True
            for r, c in cells:
                grid[r][c] = bg
        return False

    if search(0):
        return grid
    # The failed search has unwound all writes. Preserve every requested object.
    return _anchored_grid(size, bg, orientations, colors, anchors, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    band = {"easy": (5, 7), "hard": (11, 13, 15)}.get(difficulty, (7, 9, 11))
    size = ctx.draw_choice("canvas_size", _SIZES if overrides.get("canvas_size") is not None else band)
    bg = ctx.draw_color("bg_color", exclude={0})
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES) if overrides.get("texture") is not None else None
    # Rejection diagnostics ignore layout/cardinality, not malformed values.
    if texture in DEGENERATE_TEXTURES:
        return full_grid(size, size, bg)
    n_options = {"easy": (1, 2, 4, 4), "hard": (3, 4, 4)}.get(difficulty, (1, 2, 3, 4, 4, 4))
    if texture == "all_corners":
        n = ctx.draw_choice("n_corners", (4,))
    else:
        # A palette_size pin requires enough components, not a random rejection.
        minimum = overrides.get("palette_size") or 1
        options = tuple(n for n in n_options if n >= minimum) or tuple(range(minimum, 5))
        n = ctx.draw_choice("n_corners", (1, 2, 3, 4) if overrides.get("n_corners") is not None else options)
    palette_size = ctx.draw_choice("palette_size", tuple(range(1, n+1)) + (n, n))
    kind = ctx.draw_choice("palette_kind", (texture,) if texture in PALETTE_KINDS else PALETTE_KINDS)
    layout_options = (("separated",) if texture == "all_corners" and overrides.get("layout") is None else LAYOUTS)
    layout = ctx.draw_choice("layout", layout_options)
    color_rng = ctx.draw_rng("colors")
    pools = {"warm": (0, 2, 3, 4, 6, 9), "cool": (0, 1, 5, 7, 8),
             "primary": (0, 1, 2, 3, 4), "broad": tuple(range(10))}
    pool = [c for c in pools[kind] if c != bg]
    chosen = color_rng.sample(pool, palette_size)
    colors = chosen + [color_rng.choice(chosen) for _ in range(n-palette_size)]
    color_rng.shuffle(colors)
    orientations = ctx.draw_rng("orientations").sample(range(4), n)
    return _place(size, bg, orientations, colors, layout, ctx.draw_rng("placement"))
