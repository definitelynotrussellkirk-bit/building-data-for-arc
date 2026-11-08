"""Semantic generator for ARC task 3194379886a5.

Three prototype panels precede one query panel.  Exactly one prototype matches
the query up to translation and a dihedral transform.  The answer is the
matched prototype in its original panel position, recolored by the query.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3194379886a5"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "510cf694b614"
SUMMARY = (
    "Split the input at three full-height gray columns into three square "
    "prototype panels and one query panel. Match the query occupancy to "
    "exactly one prototype under translation and the eight dihedral "
    "transforms, then return that prototype in its original position "
    "recolored with the query color."
)
EXAMPLES_NEEDED = 3

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "exact public input or a novel lawful four-panel scene",
    },
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

INVARIANTS = [
    "three full-height color-5 separators divide four equal square panels",
    "each panel contains one nonzero non-divider color and one connected shape",
    "the three prototypes occupy distinct dihedral equivalence classes",
    "the query matches exactly one prototype under translation and dihedral symmetry",
    "the query color differs from every prototype color",
    "the answer preserves the matched prototype position and uses the query color",
    "generalized scenes include a projection-signature collision so D4 matching is taught",
]

_PUBLIC_PROTOTYPES = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
)
_PUBLIC_QUERIES = (
    (7, ((0, 3), (1, 2), (1, 3), (2, 1), (2, 2))),
    (4, ((0, 3), (1, 3), (2, 2), (2, 3))),
    (8, ((1, 0), (2, 0), (2, 1), (2, 2), (3, 0))),
)


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot normalize an empty shape")
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset(
        (row - min_row, col - min_col) for row, col in cells
    )


def _transforms(cells):
    normalized = _normalize(cells)
    forms = set()
    current = normalized
    for _ in range(4):
        forms.add(_normalize(current))
        forms.add(_normalize((row, -col) for row, col in current))
        current = _normalize((col, -row) for row, col in current)
    return tuple(sorted(forms, key=lambda form: tuple(sorted(form))))


def _key(cells):
    return min(tuple(sorted(form)) for form in _transforms(cells))


def _public_grid(query_spec):
    query_color, query_cells = query_spec
    size = 4
    grid = full_grid(size, 4 * size + 3, 0)
    for panel, cells in enumerate(_PUBLIC_PROTOTYPES):
        left = panel * (size + 1)
        for row, col in cells:
            grid[row][left + col] = 1
    query_left = 3 * (size + 1)
    for row, col in query_cells:
        grid[row][query_left + col] = query_color
    for panel in range(3):
        separator = panel * (size + 1) + size
        for row in range(size):
            grid[row][separator] = 5
    return grid


_PUBLIC_INPUTS = tuple(_public_grid(spec) for spec in _PUBLIC_QUERIES)
_PUBLIC_KEYS = tuple(_key(cells) for cells in _PUBLIC_PROTOTYPES)


# These connected shapes have the same unordered row/column population vectors
# but are not dihedrally equivalent.  They directly defeat the retained
# projection-signature shortcut while preserving the intended D4 reasoning.
_PROJECTION_COLLISION_A = _normalize(
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0))
)
_PROJECTION_COLLISION_B = _normalize(
    ((0, 0), (1, 0), (2, 0), (2, 1), (3, 0))
)
assert _key(_PROJECTION_COLLISION_A) != _key(_PROJECTION_COLLISION_B)



def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty sequences"]
    if len({len(row) for row in grid}) != 1:
        return ["grid must be rectangular"]
    errors = []
    if not 3 <= len(grid) <= 6:
        errors.append("panel height must be 3..6")
    if len(grid[0]) != 4 * len(grid) + 3:
        errors.append("width must encode four square panels and three separators")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    return errors


def _component_count(cells):
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _analyze(grid):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}
    size = len(grid)
    separator_cols = tuple(
        panel * (size + 1) + size for panel in range(3)
    )
    actual_full_fives = tuple(
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 5 for row in range(size))
    )
    if actual_full_fives != separator_cols:
        errors.append("expected exactly three color-5 separator columns")

    panel_cells = []
    panel_colors = []
    for panel in range(4):
        left = panel * (size + 1)
        values = {
            grid[row][left + col]
            for row in range(size)
            for col in range(size)
            if grid[row][left + col] != 0
        }
        if len(values) != 1 or 5 in values:
            errors.append(
                f"panel {panel} must contain exactly one non-divider color"
            )
            panel_colors.append(None)
            panel_cells.append(frozenset())
            continue
        color = next(iter(values))
        cells = frozenset(
            (row, col)
            for row in range(size)
            for col in range(size)
            if grid[row][left + col] == color
        )
        if len(cells) < 3:
            errors.append(f"panel {panel} shape must contain at least three cells")
        elif _component_count(cells) != 1:
            errors.append(f"panel {panel} shape must be 4-connected")
        panel_colors.append(color)
        panel_cells.append(cells)

    facts = None
    if not errors:
        prototype_keys = tuple(_key(cells) for cells in panel_cells[:3])
        if len(set(prototype_keys)) != 3:
            errors.append("prototype shapes must be dihedrally distinct")
        query_key = _key(panel_cells[3])
        matches = tuple(
            index
            for index, prototype_key in enumerate(prototype_keys)
            if prototype_key == query_key
        )
        if len(matches) != 1:
            errors.append("query must match exactly one prototype")
        if panel_colors[3] in panel_colors[:3]:
            errors.append("query color must differ from every prototype color")
        if not errors:
            frozen = tuple(map(tuple, grid))
            profile = None
            for index, public in enumerate(_PUBLIC_INPUTS):
                if frozen == tuple(map(tuple, public)):
                    profile = f"public_{index + 1}"
                    break
            linked_morphology = (
                size == 4
                and tuple(_key(cells) for cells in panel_cells[:3])
                == _PUBLIC_KEYS
                and len(set(panel_colors[:3])) == 1
            )
            facts = {
                "panel_size": size,
                "prototype_cells": tuple(panel_cells[:3]),
                "query_cells": panel_cells[3],
                "prototype_colors": tuple(panel_colors[:3]),
                "query_color": panel_colors[3],
                "match_index": matches[0],
                "canonical_profile": profile,
                "scene_family": (
                    "linked" if linked_morphology else "generalized"
                ),
            }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["scene_family"]}


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    if facts["canonical_profile"]:
        return facts["canonical_profile"]
    if facts["scene_family"] == "linked":
        return f"linked_morphology:{facts['match_index']}"
    return (
        f"generalized:{facts['panel_size']}:{facts['match_index']}:"
        f"{facts['prototype_colors']}:{facts['query_color']}"
    )


def rule_mirror(grid):
    """Independent Python mirror for focused parity checks."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    output = full_grid(facts["panel_size"], facts["panel_size"], 0)
    for row, col in facts["prototype_cells"][facts["match_index"]]:
        output[row][col] = facts["query_color"]
    return output


def _random_connected_shape(rng, size, cell_count):
    cells = {(0, 0)}
    while len(cells) < cell_count:
        frontier = {
            neighbor
            for row, col in cells
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            )
            if 0 <= neighbor[0] < size
            and 0 <= neighbor[1] < size
            and neighbor not in cells
        }
        if not frontier:
            raise RuntimeError("connected-shape frontier exhausted")
        cells.add(rng.choice(sorted(frontier)))
    return _normalize(cells)


def _shift_within_panel(rng, cells, size):
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    top = rng.randint(0, size - height)
    left = rng.randint(0, size - width)
    return frozenset((top + row, left + col) for row, col in cells)


def _panel_size(rng, band):
    if band == "easy":
        return 4
    if band == "hard":
        return 6
    return 5


def _prototype_palette(rng):
    colors = [1, 2, 3, 4, 6, 7, 8, 9]
    if rng.random() < 0.6:
        shared = rng.choice(colors)
        return (shared, shared, shared)
    return tuple(rng.sample(colors, 3))


def _paint_scene(
    *,
    size,
    prototypes,
    query,
    prototype_colors,
    query_color,
):
    grid = full_grid(size, 4 * size + 3, 0)
    for panel, cells in enumerate(prototypes):
        left = panel * (size + 1)
        for row, col in cells:
            grid[row][left + col] = prototype_colors[panel]
    query_left = 3 * (size + 1)
    for row, col in query:
        grid[row][query_left + col] = query_color
    for panel in range(3):
        separator = panel * (size + 1) + size
        for row in range(size):
            grid[row][separator] = 5
    return grid


def _build_linked(rng):
    # Keep a small literal rehearsal branch so every published profile remains
    # reachable, while most linked draws vary only task-preserving nuisance
    # factors: D4 orientation, within-panel translation, and role colors.
    if rng.random() < 0.08:
        return copy.deepcopy(rng.choice(_PUBLIC_INPUTS))

    size = 4
    prototypes = tuple(
        _shift_within_panel(rng, rng.choice(_transforms(cells)), size)
        for cells in _PUBLIC_PROTOTYPES
    )
    match_index = rng.randrange(3)
    query = _shift_within_panel(
        rng,
        rng.choice(_transforms(_PUBLIC_PROTOTYPES[match_index])),
        size,
    )
    role_colors = [1, 2, 3, 4, 6, 7, 8, 9]
    prototype_color = rng.choice(role_colors)
    query_color = rng.choice(
        [color for color in role_colors if color != prototype_color]
    )
    return _paint_scene(
        size=size,
        prototypes=prototypes,
        query=query,
        prototype_colors=(prototype_color,) * 3,
        query_color=query_color,
    )


def _build_generalized(rng, band):
    size = _panel_size(rng, band)
    match_index = rng.randrange(3)

    # Randomize both members independently; the projection signature remains
    # equal under every D4 transform while their exact D4 keys stay distinct.
    decoy = rng.choice(_transforms(_PROJECTION_COLLISION_A))
    target = rng.choice(_transforms(_PROJECTION_COLLISION_B))
    prototypes = [None, None, None]
    prototypes[match_index] = target
    decoy_index = 0 if match_index != 0 else 1
    prototypes[decoy_index] = decoy

    occupied_keys = {_key(decoy), _key(target)}
    remaining_index = next(index for index, cells in enumerate(prototypes) if cells is None)
    attempts = 0
    while attempts < 400:
        attempts += 1
        max_cells = max(4, min(size * size // 2, 12))
        candidate = _random_connected_shape(
            rng,
            size,
            rng.randint(3, max_cells),
        )
        if _key(candidate) not in occupied_keys:
            prototypes[remaining_index] = candidate
            break
    if prototypes[remaining_index] is None:
        raise RuntimeError("could not construct a third distinct prototype")

    forms = _transforms(target)
    original = _normalize(target)
    changed_forms = [form for form in forms if form != original]
    query_shape = rng.choice(changed_forms or list(forms))
    placed_prototypes = tuple(
        _shift_within_panel(rng, cells, size) for cells in prototypes
    )
    placed_query = _shift_within_panel(rng, query_shape, size)

    prototype_colors = _prototype_palette(rng)
    query_choices = [
        color
        for color in (1, 2, 3, 4, 6, 7, 8, 9)
        if color not in prototype_colors
    ]
    query_color = rng.choice(query_choices)
    return _paint_scene(
        size=size,
        prototypes=placed_prototypes,
        query=placed_query,
        prototype_colors=prototype_colors,
        query_color=query_color,
    )



def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice("scene_family", SCENE_FAMILIES)
    rng = ctx.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        _build_linked(rng)
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["scene_family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['scene_family']}"
                ]
            )
        )
    return grid
