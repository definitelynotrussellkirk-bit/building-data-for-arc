"""Input sampler for Mark the Leaf Components; labels come from Racket.

A vertex is a four-connected monochrome foreground component. Edges join
cardinally touching components, counted once regardless of contact length.
Recolor exactly degree-one vertices to 8; preserve every other cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9f05dcdedf35"
TASK_ID = GENERATOR_ID
RULE_HASH = "85fa63b64c3c"
VERSION = "1.4.1"
SUMMARY = (
    "Recolor whole degree-one monochrome components to 8. Construct chains or "
    "branches with isolated contrasts, repeated colors and lawful input 8; "
    "two of every four default samples distinguish ten explicit rivals."
)
INVARIANTS = [
    "background is 0; foreground components are monochrome and four-connected",
    "count distinct cardinally touching components, not pixels or boundary contacts",
    "a non-8 leaf changes, an interior component stays, and an isolated component stays",
    "input 8 and disconnected components of the same color are lawful",
    "default teaching branches include degrees zero, one, two and three",
]
AXES = {
    "height": {"type": "int", "default": "core profile or weighted 8..14", "valid": "8..14"},
    "width": {"type": "int", "default": "core profile or weighted 8..16", "valid": "8..16"},
    "palette_size": {"type": "int", "default": "5..6 distinct foreground colors", "valid": "5..6"},
    "chain_orientation": {"type": "str", "default": "horizontal|vertical; branch stem axis", "valid": "horizontal|vertical"},
    "graph_shape": {"type": "str", "default": "teaching branch; ordinary chain|branch", "valid": "chain|branch"},
    "component_span": {"type": "int", "default": "teaching 2; ordinary 1..2; main components only", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DIAGONAL = _CARDINAL + ((1, 1), (1, -1), (-1, 1), (-1, -1))
_CORE_PROFILES = ((9, 11, 5), (8, 12, 5), (10, 12, 6))
_INT_BOUNDS = {"height": (8, 14), "width": (8, 16), "palette_size": (5, 6), "component_span": (1, 2)}
_ENUMS = {"chain_orientation": ("horizontal", "vertical"), "graph_shape": ("chain", "branch")}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_BOUNDS:
            lo, hi = _INT_BOUNDS[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in [{lo}, {hi}], not bool or coerced text")
        elif type(value) is not str or value not in _ENUMS[name]:
            raise ValueError(f"{name} must be one of {_ENUMS[name]}")


def _choose(ctx, name, options, *, default=None):
    # A schedule may fix a default, but every validated explicit value wins.
    # The actual choice goes through GenCtx, retaining observable provenance.
    choices = options if default is None or ctx.overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, choices)


def _size_options(lo, hi, difficulty):
    all_sizes = list(range(lo, hi + 1))
    favored = all_sizes[:3] if difficulty == "easy" else (all_sizes[-3:] if difficulty == "hard" else [])
    return all_sizes + favored


def _touches(a, b, deltas=_CARDINAL):
    return any((r + dr, c + dc) in b for r, c in a for dr, dc in deltas)


def _edges(groups):
    return {(i, j) for i in range(len(groups)) for j in range(i + 1, len(groups))
            if _touches(groups[i], groups[j])}


def _main_groups(shape, span):
    if shape == "chain":
        origins = [(0, i * span) for i in range(4)]
    else:
        # Degree-3 center, two side leaves, degree-2 stem, and its end leaf.
        origins = [(0, span), (0, 0), (0, 2 * span), (span, span), (2 * span, span)]
    return [{(r + dr, c + dc) for dr in range(span) for dc in range(span)} for r, c in origins]


def _shape_ordinary(groups, span, rng):
    if span == 1:
        return groups
    expected = _edges(groups)
    result = [set(cells) for cells in groups]
    # At most one corner per tile is removed. An L stays connected and has
    # the same 2x2 box. Test the graph before accepting each shape variation.
    for i, cells in enumerate(result):
        if rng.choice((False, True)):
            candidates = []
            for point in sorted(cells):
                trial = result[:]
                trial[i] = cells - {point}
                if _edges(trial) == expected:
                    candidates.append(point)
            if candidates:
                result[i] = cells - {rng.choice(candidates)}
    return result


def _colors(ctx, n_main, n_isolates, palette_size, teaching, shape):
    rng = ctx.draw_rng("component_colors")
    leaf = 0 if shape == "chain" else 1
    if teaching:
        pool = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], palette_size - 1)
        # Both palettes repeat center color at the nonadjacent end. The stem
        # then touches TWO components of ONE color, separating component degree
        # from distinct-neighbor-color count. Palette 6 uses an extra isolate.
        main = ([pool[0], pool[1], pool[2], pool[3], pool[0]] if shape == "branch"
                else [pool[i] for i in range(n_main)])
        isolates = [main[leaf], 8]
        unused = [color for color in pool if color not in main]
        isolates.extend(unused)
        while len(isolates) < n_isolates:
            isolates.append(rng.choice(pool))
    else:
        pool = rng.sample(list(range(1, 10)), palette_size)
        main = pool[:n_main]
        isolates = pool[n_main:]
        if len(isolates) < n_isolates:
            isolates.append(main[leaf])
        while len(isolates) < n_isolates:
            isolates.append(rng.choice(pool))
    if len(isolates) != n_isolates:
        raise RuntimeError("palette construction cannot realize the selected object count")
    return main + isolates


def _with_isolates(groups, count, size):
    height = max(r for cells in groups for r, _ in cells) + 1
    result = [set(cells) for cells in groups]
    # A full empty row and a full empty column separate all isolates.
    for i in range(count):
        c0 = i * (size + 1)
        result.append({(height + 1 + dr, c0 + dc) for dr in range(size) for dc in range(size)})
    return result


def _transform_groups(groups, transpose, flip_r, flip_c):
    if transpose:
        groups = [{(c, r) for r, c in cells} for cells in groups]
    height = max(r for cells in groups for r, _ in cells) + 1
    width = max(c for cells in groups for _, c in cells) + 1
    return [{(height - 1 - r if flip_r else r, width - 1 - c if flip_c else c)
             for r, c in cells} for cells in groups], height, width


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    role = sample_index % LESSON_SCHEDULE_PERIOD
    teaching, core = role < 2, role in (0, 2)
    profile = ctx.draw_choice("core_profile", _CORE_PROFILES)
    h = _choose(ctx, "height", _size_options(8, 14, difficulty), default=profile[0] if core else None)
    w = _choose(ctx, "width", _size_options(8, 16, difficulty), default=profile[1] if core else None)
    palette_size = _choose(ctx, "palette_size", (5, 6), default=profile[2] if core else None)
    shape = _choose(ctx, "graph_shape", ("chain", "branch"), default="branch" if teaching else None)
    span = _choose(ctx, "component_span", (1, 2), default=2 if teaching else None)
    orientation = ctx.draw_choice("chain_orientation", ("horizontal", "vertical"))
    groups = _main_groups(shape, span)
    n_main = len(groups)
    if teaching:
        total = 8 if shape == "branch" and palette_size == 6 else 7
    else:
        total = ctx.draw_choice("object_count", tuple(range(max(n_main + 1, palette_size), 8)))
        groups = _shape_ordinary(groups, span, ctx.draw_rng("ordinary_shapes"))
    n_isolates = total - n_main
    colors = _colors(ctx, n_main, n_isolates, palette_size, teaching, shape)
    transpose = (shape == "chain" and orientation == "vertical") or (shape == "branch" and orientation == "horizontal")
    layout = ctx.draw_rng("layout")
    flip_r, flip_c = layout.choice((False, True)), layout.choice((False, True))
    feasible = []
    for isolate_size in (1, 2):
        candidate = _with_isolates(groups, n_isolates, isolate_size)
        candidate, mh, mw = _transform_groups(candidate, transpose, flip_r, flip_c)
        if mh <= h and mw <= w:
            feasible.append((candidate, mh, mw))
    if not feasible:
        raise RuntimeError("constructive motif does not fit the advertised grid")
    groups, mh, mw = ctx.draw_rng("isolate_shape").choice(feasible)
    r0, c0 = layout.randint(0, h - mh), layout.randint(0, w - mw)
    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, groups):
        for r, c in cells:
            if grid[r + r0][c + c0] != 0:
                raise RuntimeError("component placement collided")
            grid[r + r0][c + c0] = color
    return grid


def _objects(grid):
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack, cells = [(r, c)], set()
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _graph(grid, deltas=_CARDINAL):
    objs = _objects(grid)
    neighbors = [set() for _ in objs]
    for i, (_, cells) in enumerate(objs):
        for j in range(i + 1, len(objs)):
            if _touches(cells, objs[j][1], deltas):
                neighbors[i].add(j)
                neighbors[j].add(i)
    return objs, neighbors


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= len(grid[0]) <= 30:
        return ["grid dimensions must be in [1, 30]"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, not bool"]
    objs, neighbors = _graph(grid)
    errors = []
    if not any(len(adj) == 1 and objs[i][0] != 8 for i, adj in enumerate(neighbors)):
        errors.append("expected a degree-one component with a visible recolor to 8")
    if not any(len(adj) >= 2 for adj in neighbors):
        errors.append("expected an interior component touching at least two others")
    if not any(len(adj) == 0 for adj in neighbors):
        errors.append("expected an isolated component as a degree-zero contrast")
    return errors


def strict_canonical_like(grid):
    """Semantic teaching domain, broader than the constructive sampled shapes."""
    return self_check(grid)


def _box(cells):
    rs, cs = zip(*cells)
    return min(rs), min(cs), max(rs), max(cs)


def observe_overrides(grid):
    """Recover exact controls from pixels; do not read RNG metadata."""
    objs, neighbors = _graph(grid)
    main = [i for i, adj in enumerate(neighbors) if adj]
    degrees = [len(adj) for adj in neighbors]
    boxes = {i: _box(objs[i][1]) for i in main}
    shape = "branch" if max(degrees) == 3 else "chain"
    if shape == "branch":
        center = degrees.index(3)
        stem = next(i for i in neighbors[center] if degrees[i] == 2)
        a, b = boxes[center], boxes[stem]
        dr, dc = (b[0] + b[2]) - (a[0] + a[2]), (b[1] + b[3]) - (a[1] + a[3])
    else:
        dr = max(b[2] for b in boxes.values()) - min(b[0] for b in boxes.values())
        dc = max(b[3] for b in boxes.values()) - min(b[1] for b in boxes.values())
    return {
        "height": len(grid), "width": len(grid[0]),
        "palette_size": len({color for color, _ in objs}),
        "graph_shape": shape,
        "chain_orientation": "horizontal" if abs(dc) > abs(dr) else "vertical",
        "component_span": max(max(b[2] - b[0] + 1, b[3] - b[1] + 1) for b in boxes.values()),
    }


def _paint(grid, objs, selected):
    out = [list(row) for row in grid]
    for i in selected:
        for r, c in objs[i][1]:
            out[r][c] = 8
    return out


# All functions below are deliberately wrong competitors, never label authority.
def _pixel_degree(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            degree = sum(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0
                         for dr, dc in _CARDINAL)
            if value != 0 and degree == 1:
                out[r][c] = 8
    return out


def _contact_counts(objs):
    owner = {point: i for i, (_, cells) in enumerate(objs) for point in cells}
    return [sum(owner.get((r + dr, c + dc), i) != i for r, c in cells for dr, dc in _CARDINAL)
            for i, (_, cells) in enumerate(objs)]


def _contact_edges(grid):
    objs = _objects(grid)
    return _paint(grid, objs, [i for i, count in enumerate(_contact_counts(objs)) if count == 1])


def _nonmax_degree(grid):
    objs, neighbors = _graph(grid)
    degrees = [len(adj) for adj in neighbors]
    return _paint(grid, objs, [i for i, degree in enumerate(degrees) if 0 < degree < max(degrees, default=0)])


def _degree_le_one(grid):
    objs, neighbors = _graph(grid)
    return _paint(grid, objs, [i for i, adj in enumerate(neighbors) if len(adj) <= 1])


def _all_touching(grid):
    objs, neighbors = _graph(grid)
    return _paint(grid, objs, [i for i, adj in enumerate(neighbors) if adj])


def _leaf_colors_globally(grid):
    objs, neighbors = _graph(grid)
    colors = {objs[i][0] for i, adj in enumerate(neighbors) if len(adj) == 1}
    return _paint(grid, objs, [i for i, (color, _) in enumerate(objs) if color in colors])


def _neighbor_colors(grid):
    objs, neighbors = _graph(grid)
    return _paint(grid, objs, [i for i, adj in enumerate(neighbors)
                               if len({objs[j][0] for j in adj}) == 1])


def _delete_input8(grid):
    objs, neighbors = _graph(grid)
    out = _paint(grid, objs, [i for i, adj in enumerate(neighbors) if len(adj) == 1])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 8:
                out[r][c] = 0
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _diagonal_contacts(grid):
    objs, neighbors = _graph(grid, _DIAGONAL)
    return _paint(grid, objs, [i for i, adj in enumerate(neighbors) if len(adj) == 1])


def _whole_leaf(grid):
    objs, neighbors = _graph(grid)
    return any(len(adj) == 1 and color != 8 and len(cells) > 1
               for (color, cells), adj in zip(objs, neighbors))


def _wide_contact(grid):
    objs, neighbors = _graph(grid)
    return any(len(adj) == 1 and objs[i][0] != 8 and count > 1
               for i, (adj, count) in enumerate(zip(neighbors, _contact_counts(objs))))


def _middle_degree(grid):
    objs, neighbors = _graph(grid)
    degrees = [len(adj) for adj in neighbors]
    return any(1 < degree < max(degrees, default=0) and objs[i][0] != 8 for i, degree in enumerate(degrees))


def _non8_isolate(grid):
    objs, neighbors = _graph(grid)
    return any(not adj and objs[i][0] != 8 for i, adj in enumerate(neighbors))


def _non8_interior(grid):
    objs, neighbors = _graph(grid)
    return any(len(adj) > 1 and objs[i][0] != 8 for i, adj in enumerate(neighbors))


def _shared_color_roles(grid):
    objs, neighbors = _graph(grid)
    leaves = {objs[i][0] for i, adj in enumerate(neighbors) if len(adj) == 1 and objs[i][0] != 8}
    return any(len(adj) != 1 and objs[i][0] in leaves for i, adj in enumerate(neighbors))


def _same_color_neighbors(grid):
    objs, neighbors = _graph(grid)
    return any(len(adj) > 1 and objs[i][0] != 8
               and len({objs[j][0] for j in adj}) == 1
               for i, adj in enumerate(neighbors))


def _preserved_input8(grid):
    return any(value == 8 for row in grid for value in row)


def _changing_leaf(grid):
    objs, neighbors = _graph(grid)
    return any(len(adj) == 1 and objs[i][0] != 8 for i, adj in enumerate(neighbors))


def _diagonal_decoy(grid):
    objs, cardinal = _graph(grid)
    _, diagonal = _graph(grid, _DIAGONAL)
    return any((len(a) == 1) != (len(b) == 1) and objs[i][0] != 8
               for i, (a, b) in enumerate(zip(cardinal, diagonal)))


SEMANTIC_RIVALS = {
    "pixel_degree": _pixel_degree, "contact_edges": _contact_edges,
    "nonmax_degree": _nonmax_degree, "degree_le_one": _degree_le_one,
    "all_touching": _all_touching, "leaf_colors_globally": _leaf_colors_globally,
    "neighbor_colors": _neighbor_colors,
    "delete_input8": _delete_input8, "identity": _identity,
    "diagonal_contacts": _diagonal_contacts,
}
SEMANTIC_WITNESSES = {
    "whole_leaf": _whole_leaf, "wide_contact": _wide_contact,
    "middle_degree": _middle_degree, "non8_isolate": _non8_isolate,
    "non8_interior": _non8_interior, "shared_color_roles": _shared_color_roles,
    "same_color_neighbors": _same_color_neighbors,
    "preserved_input8": _preserved_input8, "changing_leaf": _changing_leaf,
    "diagonal_decoy": _diagonal_decoy,
}
WITNESS_RIVALS = {
    "whole_leaf": ["pixel_degree"], "wide_contact": ["contact_edges"],
    "middle_degree": ["nonmax_degree"], "non8_isolate": ["degree_le_one"],
    "non8_interior": ["all_touching"], "shared_color_roles": ["leaf_colors_globally"],
    "same_color_neighbors": ["neighbor_colors"],
    "preserved_input8": ["delete_input8"], "changing_leaf": ["identity"],
    "diagonal_decoy": ["diagonal_contacts"],
}
CANONICAL_SHORTCUTS = {"nonmax_degree": _nonmax_degree, "neighbor_colors": _neighbor_colors}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
