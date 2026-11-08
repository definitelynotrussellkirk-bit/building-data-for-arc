"""Generator for H137 — infer a transform, then self-merge with conflicts.

The input is three fixed 3x3 panels separated by full color-8 columns:
A, B = transform(A), and a query Q.  The canonical rule infers the A-to-B
D4 transform, applies it to Q, then overlays Q with the transformed copy.
A nonzero/nonzero collision becomes color 9; otherwise the present nonzero
color is retained.

Normal draws use connected, asymmetric A and Q supports.  Consequently the
demonstration transform is uniquely identifiable, the query visibly changes,
and every output exercises both the conflict and non-conflict merge branches.
The two-color, three-cell boundary reproduces the canonical five-object input
profile without fixing the actual masks or colors.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "863627ccef26"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "92960ea4379d"
SUMMARY = (
    "Infer the unique non-identity D4 transform mapping panel A to panel B, "
    "apply it to query panel Q, and overlay Q with that transformed copy; "
    "nonzero collisions become color 9."
)

INVARIANTS = [
    "the input is 3x11 with three 3x3 panels separated by color-8 columns",
    "exactly one D4 transform maps panel A to panel B, and it is non-identity",
    "A and Q have connected asymmetric supports with 3..7 nonzero cells",
    "A and Q jointly expose exactly 2..6 nonzero colors on disjoint palettes",
    "Q overlaps but is not equal to its transformed support, exercising both merge branches",
    "input panels exclude reserved separator color 8 and conflict color 9",
]

# Canonical transform priority.  The oracle checks identity first, followed by
# the seven non-identity transforms in this order.  Normal generated examples
# intentionally draw only from TRANSFORMS and require a unique match.
ALL_TRANSFORMS = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
TRANSFORMS = ALL_TRANSFORMS[1:]

DEGENERATE_TEXTURES = (
    "identity_transform",
    "empty_query",
    "broken_separators",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "transform": {
        "type": "str",
        "default": "uniform over the seven non-identity D4 transforms",
        "valid": "r1|r2|r3|fh|fv|tr|atr",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "difficulty-aware draw across the full range",
        "valid": "2..6",
    },
    "exemplar_cells": {
        "type": "int",
        "default": "difficulty-aware draw across the full range",
        "valid": "3..7",
    },
    "query_cells": {
        "type": "int",
        "default": "difficulty-aware draw across the full range",
        "valid": "3..7",
    },
}

_CELLS = tuple((row, col) for row in range(3) for col in range(3))
_CANONICAL_SIGNATURES = frozenset({
    (("fh",), 3, 3, 2),
    (("r2", "atr"), 3, 3, 2),
    (("tr",), 3, 3, 2),
})

# Stable poison fixtures used only by the defect-lint probes.
_A = [
    [1, 0, 0],
    [1, 2, 0],
    [0, 0, 3],
]
_Q = [
    [4, 4, 0],
    [4, 0, 0],
    [0, 0, 6],
]


def _clone(grid):
    return [row[:] for row in grid]


def _xform_grid(grid, code):
    """Return one D4 transform without mutating ``grid``."""
    h = len(grid)
    w = len(grid[0])
    if code == "id":
        return _clone(grid)
    if code == "r1":
        return [[grid[h - 1 - row][col] for row in range(h)] for col in range(w)]
    if code == "r2":
        return [row[::-1] for row in grid[::-1]]
    if code == "r3":
        return [[grid[row][w - 1 - col] for row in range(h)] for col in range(w)]
    if code == "fh":
        return [row[::-1] for row in grid]
    if code == "fv":
        return [row[:] for row in grid[::-1]]
    if code == "tr":
        return [[grid[row][col] for row in range(h)] for col in range(w)]
    if code == "atr":
        return [
            [grid[h - 1 - col][w - 1 - row] for col in range(w)]
            for row in range(h)
        ]
    raise ValueError(f"unknown transform {code!r}")


def _panel_key(grid):
    return tuple(tuple(row) for row in grid)


def _support(panel):
    return frozenset(
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value != 0
    )


def _support_grid(support):
    grid = full_grid(3, 3, 0)
    for row, col in support:
        grid[row][col] = 1
    return grid


def _xform_support(support, code):
    return _support(_xform_grid(_support_grid(support), code))


def _orbit_size_support(support):
    return len({_xform_support(support, code) for code in ALL_TRANSFORMS})


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = set()
    todo = [next(iter(cells))]
    while todo:
        row, col = todo.pop()
        if (row, col) in seen or (row, col) not in cells:
            continue
        seen.add((row, col))
        todo.extend(
            ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
        )
    return seen == cells


def _enumerate_supports():
    by_size = {}
    for size in range(3, 8):
        supports = []
        for candidate in combinations(_CELLS, size):
            support = frozenset(candidate)
            if _connected(support) and _orbit_size_support(support) == 8:
                supports.append(support)
        by_size[size] = tuple(sorted(supports, key=lambda item: tuple(sorted(item))))
    return by_size


_SUPPORTS_BY_SIZE = _enumerate_supports()
_QUERY_SUPPORTS = {
    (size, transform): tuple(
        support
        for support in _SUPPORTS_BY_SIZE[size]
        if 0 < len(support & _xform_support(support, transform)) < size
    )
    for size in range(3, 8)
    for transform in TRANSFORMS
}


def _random_spanning_tree(support, rng):
    """Return randomized spanning-tree edges for a connected support."""
    start = rng.choice(sorted(support))
    seen = {start}
    stack = [start]
    edges = []
    while stack:
        row, col = stack[-1]
        neighbors = [
            neighbor
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            )
            if neighbor in support and neighbor not in seen
        ]
        if not neighbors:
            stack.pop()
            continue
        nxt = rng.choice(neighbors)
        seen.add(nxt)
        edges.append((stack[-1], nxt))
        stack.append(nxt)
    if seen != set(support):
        raise ValueError("support unexpectedly disconnected")
    return edges


def _connected_coloring(support, colors, rng):
    """Partition a support into one connected component per supplied color."""
    if not 1 <= len(colors) <= len(support):
        raise ValueError("color count must fit the support")
    tree_edges = _random_spanning_tree(support, rng)
    cut_count = len(colors) - 1
    cuts = set(rng.sample(tree_edges, cut_count)) if cut_count else set()
    adjacency = {cell: set() for cell in support}
    for left, right in tree_edges:
        if (left, right) in cuts:
            continue
        adjacency[left].add(right)
        adjacency[right].add(left)

    components = []
    remaining = set(support)
    while remaining:
        component = set()
        todo = [min(remaining)]
        while todo:
            cell = todo.pop()
            if cell in component:
                continue
            component.add(cell)
            todo.extend(adjacency[cell] - component)
        remaining -= component
        components.append(component)
    if len(components) != len(colors):
        raise ValueError("tree partition did not realize every color")

    color_order = list(colors)
    component_order = list(components)
    rng.shuffle(color_order)
    rng.shuffle(component_order)
    panel = full_grid(3, 3, 0)
    for color, component in zip(color_order, component_order):
        for row, col in component:
            panel[row][col] = color
    return panel


def _paste_panel(out, panel_index, panel):
    left = panel_index * 4
    for row, values in enumerate(panel):
        out[row][left:left + 3] = values[:]


def _panels(grid):
    return tuple(
        [row[left:left + 3] for row in grid]
        for left in (0, 4, 8)
    )


def _matching_transforms(panel_a, panel_b):
    return [
        code
        for code in ALL_TRANSFORMS
        if _xform_grid(panel_a, code) == panel_b
    ]


def _merge_query(query, code):
    transformed = _xform_grid(query, code)
    return [
        [
            9
            if query[row][col] != 0 and transformed[row][col] != 0
            else query[row][col] or transformed[row][col]
            for col in range(3)
        ]
        for row in range(3)
    ]


def _valid_arc_grid(grid):
    return (
        isinstance(grid, list)
        and bool(grid)
        and all(isinstance(row, list) for row in grid)
        and len({len(row) for row in grid}) == 1
        and len(grid[0]) > 0
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _color_is_connected(panel, color):
    return _connected(
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value == color
    )


def profile_signature(grid):
    if not _valid_arc_grid(grid) or len(grid) != 3 or len(grid[0]) != 11:
        return None
    panel_a, panel_b, query = _panels(grid)
    candidates = tuple(_matching_transforms(panel_a, panel_b))
    colors = {
        value
        for panel in (panel_a, query)
        for row in panel
        for value in row
        if value != 0
    }
    return (
        candidates,
        len(_support(panel_a)),
        len(_support(query)),
        len(colors),
    )


def canonical_profile_signature(grid):
    signature = profile_signature(grid)
    return signature if signature in _CANONICAL_SIGNATURES else None


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def observe_overrides(grid):
    """Recover every declared exact axis from the returned grid."""
    if not _valid_arc_grid(grid) or len(grid) != 3 or len(grid[0]) != 11:
        return {}
    panel_a, panel_b, query = _panels(grid)
    matches = _matching_transforms(panel_a, panel_b)
    if len(matches) != 1 or matches[0] == "id":
        return {}
    colors = {
        value
        for panel in (panel_a, query)
        for row in panel
        for value in row
        if value != 0
    }
    return {
        "transform": matches[0],
        "n_distinct_colors": len(colors),
        "exemplar_cells": len(_support(panel_a)),
        "query_cells": len(_support(query)),
    }


def rule_mirror(grid):
    """Independent Python mirror of the current priority-ordered Racket rule."""
    if not _valid_arc_grid(grid) or len(grid) != 3 or len(grid[0]) != 11:
        raise ValueError("rule input must be a rectangular 3x11 ARC grid")
    panel_a, panel_b, query = _panels(grid)
    matches = _matching_transforms(panel_a, panel_b)
    if not matches:
        raise ValueError("no D4 transform maps panel A to panel B")
    return _merge_query(query, matches[0])


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the full generated grammar, not merely shape and palette."""
    if not _valid_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC-color matrix"]
    if len(grid) != 3 or len(grid[0]) != 11:
        return ["expected a 3x11 grid with three fixed 3x3 panels"]

    errors = []
    if any(grid[row][col] != 8 for row in range(3) for col in (3, 7)):
        errors.append("separator columns 3 and 7 must be full color 8")
    panel_a, panel_b, query = _panels(grid)
    for index, panel in enumerate((panel_a, panel_b, query)):
        if any(value in (8, 9) for row in panel for value in row):
            errors.append(
                f"panel {index} contains reserved separator/conflict color 8 or 9"
            )

    matches = _matching_transforms(panel_a, panel_b)
    if len(matches) != 1:
        errors.append(
            "A-to-B transform must be unique across all D4 operations; "
            f"matching transforms={matches}"
        )
    elif matches[0] == "id":
        errors.append("A-to-B transform must be non-identity")

    for label, panel in (("A", panel_a), ("Q", query)):
        support = _support(panel)
        if not 3 <= len(support) <= 7:
            errors.append(f"panel {label} must contain 3..7 nonzero cells")
        if not _connected(support):
            errors.append(f"panel {label} nonzero support must be 4-connected")
        if support and _orbit_size_support(support) != 8:
            errors.append(f"panel {label} support must have a full eight-element D4 orbit")
        if len(support) == 9:
            errors.append(f"panel {label} must retain background cells")
        for color in {
            value for row in panel for value in row if value != 0
        }:
            if not _color_is_connected(panel, color):
                errors.append(
                    f"panel {label} color {color} must form one connected component"
                )

    a_colors = {value for row in panel_a for value in row if value != 0}
    q_colors = {value for row in query for value in row if value != 0}
    if a_colors & q_colors:
        errors.append("panels A and Q must use disjoint nonzero palettes")
    if not 2 <= len(a_colors | q_colors) <= 6:
        errors.append("panels A and Q must jointly expose 2..6 nonzero colors")
    if not a_colors or not q_colors:
        errors.append("panels A and Q must each contain at least one nonzero color")

    if len(matches) == 1 and matches[0] != "id":
        q_support = _support(query)
        transformed_support = _xform_support(q_support, matches[0])
        overlap = len(q_support & transformed_support)
        if overlap == 0:
            errors.append("Q and transform(Q) must overlap so color-9 conflicts occur")
        if overlap == len(q_support):
            errors.append("Q and transform(Q) must differ so non-conflict merge cells remain")

    requested = (
        (meta or {}).get("overrides", {})
        if isinstance(meta, dict)
        else {}
    )
    if requested:
        observed = observe_overrides(grid)
        for name in AXES:
            if name in requested and observed.get(name) != requested[name]:
                errors.append(
                    f"override {name}={requested[name]!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    texture = overrides.pop("texture", None)
    if texture is not None:
        if texture in DEGENERATE_TEXTURES and not overrides:
            return _draw_from_degenerate(texture)
        if texture in DEGENERATE_TEXTURES:
            raise ValueError("degenerate texture probes cannot be combined with normal axes")
        raise ValueError(f"unknown texture override {texture!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    transform = ctx.draw_choice("transform", TRANSFORMS)
    n_colors = ctx.draw_int_diff("n_distinct_colors", 2, 6)
    exemplar_cells = ctx.draw_int_diff("exemplar_cells", 3, 7)
    query_cells = ctx.draw_int_diff("query_cells", 3, 7)

    a_support = ctx.draw_rng("exemplar_support").choice(
        _SUPPORTS_BY_SIZE[exemplar_cells]
    )
    query_options = _QUERY_SUPPORTS[(query_cells, transform)]
    if not query_options:
        raise ValueError(
            "no connected asymmetric query support realizes the requested transform"
        )
    q_support = ctx.draw_rng("query_support").choice(query_options)

    min_a_colors = max(1, n_colors - query_cells)
    max_a_colors = min(exemplar_cells, n_colors - 1)
    if min_a_colors > max_a_colors:
        raise ValueError("requested color/cell combination is not realizable")
    a_color_count = ctx.draw_rng("color_allocation").randint(
        min_a_colors, max_a_colors
    )
    colors = list(
        ctx.draw_distinct_colors(
            "foreground_colors",
            n=n_colors,
            exclude=(0, 8, 9),
        )
    )
    panel_a = _connected_coloring(
        a_support,
        colors[:a_color_count],
        ctx.draw_rng("exemplar_coloring"),
    )
    query = _connected_coloring(
        q_support,
        colors[a_color_count:],
        ctx.draw_rng("query_coloring"),
    )
    panel_b = _xform_grid(panel_a, transform)

    grid = full_grid(3, 11, 0)
    for row in range(3):
        grid[row][3] = 8
        grid[row][7] = 8
    for panel_index, panel in enumerate((panel_a, panel_b, query)):
        _paste_panel(grid, panel_index, panel)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise ValueError("constructed invalid transform board: " + "; ".join(errors))
    return grid


def _draw_from_degenerate(name):
    grid = full_grid(3, 11, 0)
    for row in range(3):
        grid[row][3] = 8
        grid[row][7] = 8
    if name == "identity_transform":
        for panel_index, panel in enumerate((_A, _A, _Q)):
            _paste_panel(grid, panel_index, panel)
        return grid
    if name == "empty_query":
        empty = full_grid(3, 3, 0)
        for panel_index, panel in enumerate((_A, _xform_grid(_A, "fh"), empty)):
            _paste_panel(grid, panel_index, panel)
        return grid
    if name == "broken_separators":
        for panel_index, panel in enumerate((_A, _xform_grid(_A, "fh"), _Q)):
            _paste_panel(grid, panel_index, panel)
        grid[1][3] = 0
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")
