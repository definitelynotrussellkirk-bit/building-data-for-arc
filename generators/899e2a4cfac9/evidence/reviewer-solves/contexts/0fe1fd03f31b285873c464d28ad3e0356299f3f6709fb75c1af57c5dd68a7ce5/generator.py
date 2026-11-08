"""Border filtering inputs, with size, color and connectivity counterexamples.

Objects are SAME-COLOR four-connected components; background is fixed zero.
The unchanged Racket rule supplies labels. Alternating simple and rich draws
retain canonical support while teaching size, color, connectivity and all edges.
Exact overrides remain lawful but can require different demonstrations.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "899e2a4cfac9"
TASK_ID = GENERATOR_ID
RULE_HASH = "50ed982b7d21"
VERSION = "2.1.0"
SUMMARY = "Remove border-touching same-color 4-components; preserve all interior components."
INVARIANTS = [
    "fixed zero background; integer colors 0..9; at least one erased and one retained object",
    "same-color four-connectivity, including separate diagonal and repeated-color objects",
    "even default indices have three separated objects, including one survivor, and three foreground colors",
    "odd default indices have seven objects, all-edge and connectivity witnesses, and a surviving singleton",
    "four consecutive default draws contain two rich examples; explicit controls can alter this curriculum",
]
AXES = {
    "grid_h": {"type": "int", "default": "6..12, with canonical-profile mixture", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "7..14, with canonical-profile mixture", "valid": "7..14"},
    "n_blobs": {"type": "int", "default": "alternates 3 and 7", "valid": "3..7"},
    "n_distinct_colors": {"type": "int", "default": "3..6 including zero; favors 4", "valid": "3..6"},
}
# Rich draws repeat a foreground color. The three-object branch can use one
# different foreground color per object, so its total palette can be four.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_blobs": 3, "n_distinct_colors": [5, 6]},
    {"n_blobs": 4, "n_distinct_colors": [5, 6]},
    {"n_blobs": 5, "n_distinct_colors": 6},
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical_support", "rich_witnesses")
MIN_STRICT_FRAC = 1.0
_ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_EIGHT = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)
_CANONICAL_PROFILES = ((7, 8), (8, 9), (9, 10))
_DOMAINS = {"grid_h": (6, 12), "grid_w": (7, 14), "n_blobs": (3, 7), "n_distinct_colors": (3, 6)}


def schedule_profile(seed, sample_index, difficulty=None):
    """Default, consecutive-index curriculum; explicit overrides may replace it."""
    return SCHEDULE_PROFILES[sample_index % 2]


def _components(grid, *, same_color=True, diagonal=False):
    """Input-domain segmentation; alternatives are used only by named rivals."""
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    steps = _EIGHT if diagonal else _ORTHOGONAL
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells, todo = [], [(r, c)]
            seen.add((r, c))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in steps:
                    p = (rr + dr, cc + dc)
                    if (0 <= p[0] < h and 0 <= p[1] < w and p not in seen
                            and grid[p[0]][p[1]] != 0
                            and (not same_color or grid[p[0]][p[1]] == color)):
                        seen.add(p)
                        todo.append(p)
            result.append(cells)
    return result


def _edges(cells, h, w):
    result = set()
    for r, c in cells:
        if r == 0:
            result.add("top")
        if r == h - 1:
            result.add("bottom")
        if c == 0:
            result.add("left")
        if c == w - 1:
            result.add("right")
    return result


def _border(cells, h, w, *, omit=None):
    return bool(_edges(cells, h, w) - {omit})


def _draw_axes(ctx, difficulty, overrides):
    anchor_h, anchor_w = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
    core = ctx.draw_choice("profile_support", (True, True, False))
    h_options, w_options = list(range(6, 13)), list(range(7, 15))
    if core:
        h_options += [anchor_h] * 200
        w_options += [anchor_w] * 200
    h = ctx.draw_choice("grid_h", h_options)
    w = ctx.draw_choice("grid_w", w_options)
    requested_colors = overrides.get("n_distinct_colors")
    simple = ctx.sample_index % 2 == 0 and requested_colors in (None, 3, 4)
    blob_options = list(range(3, 8)) if overrides.get("n_blobs") is not None else [3 if simple else 7]
    n = ctx.draw_choice("n_blobs", blob_options)
    maximum_colors = 4 if n == 3 else min(6, n)
    if requested_colors is not None and requested_colors > maximum_colors:
        raise ValueError("n_distinct_colors is incompatible with n_blobs and the component color roles")
    if n == 3 and requested_colors is None:
        color_options = [4]
    else:
        color_options = list(range(3, maximum_colors + 1)) + [4] * (40 if core else 2)
    colors = ctx.draw_choice("n_distinct_colors", color_options)
    return h, w, n, colors


def _construct_simple(ctx, h, w, n_colors):
    """Canonical-size topology with movable dominoes and L/square/T survivors."""
    transpose = ctx.draw_choice("transpose", (False, True))
    bh, bw = (w, h) if transpose else (h, w)
    grid = full_grid(bh, bw, 0)
    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), n_colors - 1)
    rng = ctx.draw_rng("simple_geometry")
    motif = rng.choice((((0, 0), (1, 0), (1, 1)),
                        ((0, 0), (0, 1), (1, 0), (1, 1)),
                        ((0, 0), (0, 1), (0, 2), (1, 1))))
    width = max(c for _, c in motif) + 1
    rr, cc = rng.randint(2, bh - 4), rng.randint(1, bw - width - 1)
    for r, c in motif:
        grid[rr + r][cc + c] = palette[-1]
    for row, color in ((0, palette[0]), (bh - 2, palette[1])):
        columns = [c for c in range(bw)
                   if all(grid[r][c] == 0
                          and all(not (0 <= r + dr < bh and 0 <= c + dc < bw)
                                  or grid[r + dr][c + dc] == 0 for dr, dc in _ORTHOGONAL)
                          for r in (row, row + 1))]
        if not columns:
            raise RuntimeError("canonical-support construction has no border anchor")
        col = rng.choice(columns)
        grid[row][col] = grid[row + 1][col] = color
    if transpose:
        grid = [list(row) for row in zip(*grid)]
    if ctx.draw_choice("reflect_rows", (False, True)):
        grid = grid[::-1]
    if ctx.draw_choice("reflect_columns", (False, True)):
        grid = [row[::-1] for row in grid]
    return grid


def _construct(ctx, h, w, n, n_colors, difficulty):
    """Grow independently shaped components without changing their border roles.

    The two seed pairs are semantic witnesses, not complete output templates.
    Extra objects, polyomino growth, all eight symmetries, palettes, anchors and
    dimensions vary. No output or reference execution is used for acceptance.
    """
    transpose = ctx.draw_choice("transpose", (False, True))
    bh, bw = (w, h) if transpose else (h, w)
    grid = full_grid(bh, bw, 0)
    owner = [[-1] * bw for _ in range(bh)]
    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), n_colors - 1)
    rng = ctx.draw_rng("polyominoes")
    a_col = ctx.draw_rng("top_anchor").randint(1, max(1, bw - 5))
    b_row = ctx.draw_rng("right_anchor").randint(2, bh - 3)
    shapes = [
        {(0, a_col), (1, a_col)},
        {(2, a_col + 1), (3, a_col + 1)},
        {(b_row, bw - 1), (b_row + 1, bw - 1)},
        {(b_row, bw - 2), (b_row - 1, bw - 2)},
    ]
    colors = [palette[0], palette[0], palette[1], palette[2] if len(palette) > 2 else palette[0]]
    edge_sets = [_edges(cells, bh, bw) for cells in shapes]

    def put(index, point):
        r, c = point
        shapes[index].add(point)
        grid[r][c], owner[r][c] = colors[index], index

    for i, cells in enumerate(shapes):
        for p in tuple(cells):
            put(i, p)

    def available(point, color, index=-1):
        r, c = point
        if not (0 <= r < bh and 0 <= c < bw) or grid[r][c] != 0:
            return False
        # Preserve the exact original edge set, including the empty interior set.
        if index >= 0 and not _edges([point], bh, bw) <= edge_sets[index]:
            return False
        return not any(0 <= r + dr < bh and 0 <= c + dc < bw
                       and grid[r + dr][c + dc] == color and owner[r + dr][c + dc] != index
                       for dr, dc in _ORTHOGONAL)

    # Introduce every requested foreground color; later extras can repeat roles.
    unused_colors = [color for color in palette if color not in colors]
    for i in range(4, n):
        color = unused_colors.pop(0) if unused_colors else rng.choice(palette)
        if i == 4:
            pool = [(r, 0) for r in range(2, bh - 1)]
        elif i == 5:
            pool = [(bh - 1, c) for c in range(1, bw - 1)]
        else:
            # A guaranteed small survivor teaches both singleton preservation
            # and retention of objects smaller than the largest interior one.
            pool = [(r, c) for r in range(1, bh - 1) for c in range(1, bw - 1)]
        candidates = [p for p in pool if available(p, color)]
        # Empty left/bottom strips make the first two placements constructive.
        if not candidates:
            raise RuntimeError("constructive component placement has no free anchor")
        point = rng.choice(candidates)
        colors.append(color)
        shapes.append(set())
        edge_sets.append(_edges([point], bh, bw))
        put(i, point)

    def frontier(index):
        points = {(r + dr, c + dc) for r, c in shapes[index] for dr, dc in _ORTHOGONAL}
        return sorted(p for p in points if available(p, colors[index], index))

    max_size = {"easy": 3, "hard": 5}.get(difficulty, 4)
    # Keep background dominant in the sampled curriculum, without a validator
    # restriction requiring it to be most frequent on every legal input.
    budget = (bh * bw - 1) // 2
    filled = sum(map(len, shapes))
    # Equal size with opposite outcomes defeats ANY rule based only on size.
    for _ in range(rng.randint(2, max_size) - 2):
        if filled + 2 > budget:
            break
        left = frontier(0)
        if not left:
            break
        p = rng.choice(left)
        put(0, p)
        right = frontier(1)
        if not right:
            shapes[0].remove(p)
            grid[p[0]][p[1]], owner[p[0]][p[1]] = 0, -1
            break
        put(1, rng.choice(right))
        filled += 2
    # Other components grow independently; never absorb a same-color peer.
    for i in range(2, n):
        if i == 6:
            continue  # Preserve the deliberately small interior witness.
        target = rng.randint(len(shapes[i]), max(max_size, len(shapes[i])))
        while len(shapes[i]) < target and filled < budget:
            options = frontier(i)
            if not options:
                break
            put(i, rng.choice(options))
            filled += 1
    if transpose:
        grid = [list(row) for row in zip(*grid)]
    if ctx.draw_choice("reflect_rows", (False, True)):
        grid = grid[::-1]
    if ctx.draw_choice("reflect_columns", (False, True)):
        grid = [row[::-1] for row in grid]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        lo, hi = _DOMAINS[name]
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, got {value!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h, w, n, colors = _draw_axes(ctx, difficulty, overrides)
    if n == 3:
        return _construct_simple(ctx, h, w, colors)
    return _construct(ctx, h, w, n, colors, difficulty)


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or any(not isinstance(row, (list, tuple)) or not row for row in grid)
            or any(len(row) != len(grid[0]) for row in grid)):
        return ["grid must be a nonempty rectangle"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not booleans)"]
    h, w = len(grid), len(grid[0])
    if not (3 <= h <= 30 and 3 <= w <= 30):
        return ["grid must fit 3..30 rows and columns"]
    if not any(0 in row for row in grid):
        return ["fixed zero background must be present"]
    groups = _components(grid)
    border = sum(_border(cells, h, w) for cells in groups)
    errors = []
    if border == 0:
        errors.append("at least one border-touching component is required")
    if border == len(groups):
        errors.append("at least one fully interior component is required")
    return errors


def strict_canonical_like(grid):
    """The mixed erased/retained component domain; canonical one-survivor cases included."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_blobs": len(_components(grid)),
            "n_distinct_colors": len({value for row in grid for value in row})}


def _paint_selected(grid, groups, keep):
    out = full_grid(len(grid), len(grid[0]), 0)
    for cells in groups:
        if keep(cells):
            for r, c in cells:
                out[r][c] = grid[r][c]
    return out


def _erase_domino(grid):
    return _paint_selected(grid, _components(grid), lambda cells: len(cells) != 2)


def _keep_largest(grid):
    groups = _components(grid)
    largest = max(map(len, groups), default=0)
    return _paint_selected(grid, groups, lambda cells: len(cells) == largest)


def _border_colors_global(grid):
    h, w = len(grid), len(grid[0])
    colors = {grid[r][c] for r in range(h) for c in range(w) if _border([(r, c)], h, w)}
    return [[0 if value in colors else value for value in row] for row in grid]


def _connectivity_rival(grid, *, same_color=True, diagonal=False, omit=None):
    h, w = len(grid), len(grid[0])
    groups = _components(grid, same_color=same_color, diagonal=diagonal)
    return _paint_selected(grid, groups, lambda cells: not _border(cells, h, w, omit=omit))


def _border_cells_only(grid):
    h, w = len(grid), len(grid[0])
    return [[0 if _border([(r, c)], h, w) else grid[r][c] for c in range(w)] for r in range(h)]


def _interior_groups(grid):
    h, w = len(grid), len(grid[0])
    return [cells for cells in _components(grid) if not _border(cells, h, w)]


def _drop_interior_singletons(grid):
    return _paint_selected(grid, _interior_groups(grid), lambda cells: len(cells) > 1)


def _largest_interior_only(grid):
    groups = _interior_groups(grid)
    largest = max(map(len, groups), default=0)
    return _paint_selected(grid, groups, lambda cells: len(cells) == largest)


def _small_and_large_interiors(grid):
    sizes = {len(cells) for cells in _interior_groups(grid)}
    return 1 in sizes and any(size > 1 for size in sizes)


def _same_size_roles(grid):
    h, w = len(grid), len(grid[0])
    groups = _components(grid)
    outside = {len(c) for c in groups if _border(c, h, w)}
    inside = {len(c) for c in groups if not _border(c, h, w)}
    return bool(outside & inside)


def _repeated_color_roles(grid):
    h, w = len(grid), len(grid[0])
    groups = _components(grid)
    outside = {grid[c[0][0]][c[0][1]] for c in groups if _border(c, h, w)}
    inside = {grid[c[0][0]][c[0][1]] for c in groups if not _border(c, h, w)}
    return bool(outside & inside)


def _bridge_witness(grid, *, same_color=True, diagonal=False):
    h, w = len(grid), len(grid[0])
    retained = {p for c in _components(grid) if not _border(c, h, w) for p in c}
    return any(_border(c, h, w) and bool(retained.intersection(c))
               for c in _components(grid, same_color=same_color, diagonal=diagonal))


def _border_tail(grid):
    h, w = len(grid), len(grid[0])
    return any(_border(c, h, w) and any(not _border([p], h, w) for p in c) for c in _components(grid))


def _edge_witness(grid, edge):
    h, w = len(grid), len(grid[0])
    return any(_border(c, h, w) and not _border(c, h, w, omit=edge) for c in _components(grid))


SEMANTIC_RIVALS = {
    "erase_domino": _erase_domino,
    "keep_largest": _keep_largest,
    "border_colors_global": _border_colors_global,
    "same_color_8": lambda grid: _connectivity_rival(grid, diagonal=True),
    "nonzero_4": lambda grid: _connectivity_rival(grid, same_color=False),
    "border_cells_only": _border_cells_only,
    "drop_interior_singletons": _drop_interior_singletons,
    "largest_interior_only": _largest_interior_only,
}
SEMANTIC_WITNESSES = {
    "equal_size_opposite_roles": _same_size_roles,
    "repeated_color_opposite_roles": _repeated_color_roles,
    "same_color_diagonal_bridge": lambda grid: _bridge_witness(grid, diagonal=True),
    "different_color_orthogonal_bridge": lambda grid: _bridge_witness(grid, same_color=False),
    "border_component_has_interior_cells": _border_tail,
    "small_and_large_interiors": _small_and_large_interiors,
}
WITNESS_RIVALS = {
    "equal_size_opposite_roles": ["erase_domino", "keep_largest"],
    "repeated_color_opposite_roles": ["border_colors_global"],
    "same_color_diagonal_bridge": ["same_color_8"],
    "different_color_orthogonal_bridge": ["nonzero_4"],
    "border_component_has_interior_cells": ["border_cells_only"],
    "small_and_large_interiors": ["drop_interior_singletons", "largest_interior_only"],
}
# Edge omission is a plausible generalization even when canonical examples
# already refute it. Bind one witness to the precise edge it demonstrates.
for _edge in ("top", "bottom", "left", "right"):
    SEMANTIC_RIVALS["omit_" + _edge] = lambda grid, edge=_edge: _connectivity_rival(grid, omit=edge)
    SEMANTIC_WITNESSES["isolated_" + _edge + "_contact"] = lambda grid, edge=_edge: _edge_witness(grid, edge)
    WITNESS_RIVALS["isolated_" + _edge + "_contact"] = ["omit_" + _edge]
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("erase_domino", "keep_largest", "border_colors_global", "same_color_8", "nonzero_4", "omit_left",
                        "drop_interior_singletons", "largest_interior_only")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite named-rival check, not a proof against arbitrary hypotheses."""
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
