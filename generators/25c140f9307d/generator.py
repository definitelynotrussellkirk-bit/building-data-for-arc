"""Generator for ARC training task 97a05b5b.

The input contains one large red plate with several interior polyomino holes and
one detached key object per hole.  A key's red cells are the teeth that match a
hole up to rotation; its two non-red cells are payload colors copied onto the
red rim when the canonical Racket rule stamps the matching key.

Meaningful exact controls:
- ``rect_size``: square plate size, integer 9..14.
- ``n_keys``: number of distinct hole/key shape pairs, integer 2..4.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

GENERATOR_ID = "25c140f9307d"
RULE_HASH = "fafb0679bd1e"
VERSION = "2.2.0"
TASK_ID = "25c140f9307d"
SUMMARY = (
    "A large red plate contains 2-4 separated four-cell polyomino holes. "
    "Detached 3x3 key objects each contain a distinct red tooth shape matching "
    "one hole up to rotation plus two colored payload cells. The canonical "
    "rule rotates and stamps the matching key into each hole, returning the "
    "cropped decorated plate."
)

INVARIANTS = [
    "background is 0 and the largest nonzero object is the red plate",
    "there are 2-4 separated interior hole components with distinct free-polyomino shapes",
    "there is one detached key object per hole; key red teeth match hole shapes up to rotation",
    "each key has exactly two non-red payload cells that lie on the red rim when stamped",
]

DEGENERATE_TEXTURES = ("no_hole", "no_key", "full_grid")

AXES = {
    "rect_size": {
        "type": "int",
        "default": "unset; difficulty-specific rectangular plate",
        "valid": "9..14 exact square override",
    },
    "n_keys": {
        "type": "int",
        "default": "easy=2, medium/none=2..3, hard=4",
        "valid": "2..4",
    },
    "rect_h": {
        "type": "int",
        "default": "difficulty-specific",
        "valid": "9..14",
    },
    "rect_w": {
        "type": "int",
        "default": "difficulty-specific",
        "valid": "9..14",
    },
    "texture": {
        "type": "str",
        "default": "normal",
        "valid": "normal|" + "|".join(DEGENERATE_TEXTURES),
    },
}

# Every template occupies a 3x3 frame.  Teeth are four red cells; body cells
# are payload positions.  The tooth shapes are pairwise distinct under rotation.
_KEY_TEMPLATES = (
    (
        "square",
        frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
        frozenset({(0, 2), (2, 0)}),
    ),
    (
        "ell",
        frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
        frozenset({(0, 2), (1, 2)}),
    ),
    (
        "tee",
        frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
        frozenset({(2, 0), (2, 2)}),
    ),
    (
        "zigzag",
        frozenset({(0, 1), (0, 2), (1, 0), (1, 1)}),
        frozenset({(2, 0), (2, 2)}),
    ),
)


def _has_override(overrides, label: str) -> bool:
    return label in overrides and overrides[label] is not None


def _draw_dimension(ctx, label: str, band: tuple[int, int], overrides) -> int:
    if _has_override(overrides, label):
        return ctx.draw_int_strict(label, 9, 14)
    return ctx.draw_int_strict(label, *band)


def _draw_geometry(ctx, difficulty, overrides) -> tuple[int, int, int]:
    if _has_override(overrides, "rect_size"):
        if _has_override(overrides, "rect_h") or _has_override(overrides, "rect_w"):
            raise ValueError("rect_size cannot be combined with rect_h or rect_w")
        size = ctx.draw_int_strict("rect_size", 9, 14)
        rh = rw = size
    elif difficulty == "easy":
        rh = _draw_dimension(ctx, "rect_h", (9, 10), overrides)
        rw = _draw_dimension(ctx, "rect_w", (9, 11), overrides)
    elif difficulty == "hard":
        rh = _draw_dimension(ctx, "rect_h", (12, 14), overrides)
        rw = _draw_dimension(ctx, "rect_w", (11, 14), overrides)
    else:
        rh = _draw_dimension(ctx, "rect_h", (10, 12), overrides)
        rw = _draw_dimension(ctx, "rect_w", (10, 13), overrides)

    if _has_override(overrides, "n_keys"):
        n_keys = ctx.draw_int_strict("n_keys", 2, 4)
    elif difficulty == "easy":
        n_keys = ctx.draw_int_strict("n_keys", 2, 2)
    elif difficulty == "hard":
        n_keys = ctx.draw_int_strict("n_keys", 4, 4)
    else:
        n_keys = ctx.draw_int_strict("n_keys", 2, 3)
    return rh, rw, n_keys


def _rotate_cells(cells, turns: int):
    result = set(cells)
    for _ in range(turns % 4):
        result = {(c, 2 - r) for r, c in result}
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, rng)
    if texture not in (None, "normal"):
        raise ValueError(
            f"texture: override {texture!r} not in normal|{'|'.join(DEGENERATE_TEXTURES)}"
        )

    rh, rw, n_keys = _draw_geometry(ctx, difficulty, overrides)
    h = max(rh + 2, 4 * n_keys + 1)
    w = rw + 8
    g = full_grid(h, w, 0)
    r0 = c0 = 1
    fill_box(g, r0, c0, r0 + rh - 1, c0 + rw - 1, 2)

    anchors = [
        (1, 1),
        (1, rw - 4),
        (rh - 4, 1),
        (rh - 4, rw - 4),
    ]
    rng.shuffle(anchors)
    templates = list(_KEY_TEMPLATES)
    rng.shuffle(templates)
    selected = []
    for i in range(n_keys):
        name, teeth, body = templates[i]
        hole_turns = rng.randrange(4)
        key_turns = rng.randrange(4)
        hole_teeth = _rotate_cells(teeth, hole_turns)
        key_teeth = _rotate_cells(teeth, key_turns)
        key_body = _rotate_cells(body, key_turns)
        ar, ac = anchors[i]
        for dr, dc in hole_teeth:
            g[r0 + ar + dr][c0 + ac + dc] = 0
        selected.append((name, key_teeth, key_body))

    key_c = c0 + rw + 3
    payload_colors = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], 2 * n_keys)
    for i, (_name, teeth, body) in enumerate(selected):
        key_r = 1 + 4 * i
        for dr, dc in teeth:
            g[key_r + dr][key_c + dc] = 2
        for j, (dr, dc) in enumerate(sorted(body)):
            g[key_r + dr][key_c + dc] = payload_colors[2 * i + j]
    return g


def _components(grid, predicate, *, eight=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if eight:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or not predicate(grid[sr][sc]):
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in steps:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and predicate(grid[nr][nc])
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _components_of_color(grid, color):
    return _components(grid, lambda value: value == color)


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _shape_signature(cells):
    points = {(r, c) for r, c in cells}
    variants = []
    for _ in range(4):
        min_r = min(r for r, _ in points)
        min_c = min(c for _, c in points)
        variants.append(
            tuple(sorted((r - min_r, c - min_c) for r, c in points))
        )
        points = {(c, -r) for r, c in points}
    return min(variants)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact structural contract consumed by the canonical rule."""
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    errs = []
    colors = {value for row in grid for value in row}
    if 0 not in colors or 2 not in colors:
        errs.append("expected both bg=0 and red=2")

    red = sorted(_components_of_color(grid, 2), key=len, reverse=True)
    if not red:
        return errs + ["no red components"]
    plate = red[0]
    if len(plate) < 40:
        errs.append("largest red component too small for the main plate")
    r0, c0, r1, c1 = _bbox(plate)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    holes = _components(crop, lambda value: value == 0, eight=True)
    if not holes:
        errs.append("expected at least one interior hole")

    objects = sorted(
        _components(grid, lambda value: value != 0, eight=True),
        key=len,
        reverse=True,
    )
    keys = objects[1:] if objects else []
    if len(keys) != len(holes):
        errs.append(
            f"expected one detached key object per hole ({len(holes)}), found {len(keys)}"
        )

    key_signatures = []
    for key in keys:
        values = [grid[r][c] for r, c in key]
        teeth = [(r, c) for r, c in key if grid[r][c] == 2]
        payload = [value for value in values if value not in (0, 2)]
        if not teeth:
            errs.append("each detached key must have at least one red tooth")
        if not payload:
            errs.append("each detached key must have at least one payload cell")
        if teeth:
            key_signatures.append(_shape_signature(teeth))

    hole_signatures = [_shape_signature(hole) for hole in holes if hole]
    if len(set(hole_signatures)) != len(hole_signatures):
        errs.append("hole tooth shapes must be distinct up to rotation")
    if sorted(key_signatures) != sorted(hole_signatures):
        errs.append("detached key tooth shapes do not match the hole shapes")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 12, 0)
    if name == "no_hole":
        fill_box(g, 1, 1, 5, 5, 2)
        fill_box(g, 1, 9, 2, 10, 2)
        return g
    if name == "no_key":
        fill_box(g, 1, 1, 5, 5, 2)
        fill_box(g, 2, 2, 3, 3, 0)
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
