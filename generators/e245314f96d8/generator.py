"""Generate answer-identifying contact-degree recoloring lessons.

The Racket oracle finds same-color 4-connected nonzero objects, forms a graph
whose edges are cardinal contacts between different objects, and recolors each
whole object by graph degree: 0 -> 3, 1 -> 4, 2 -> 6, and 3 or more -> 8.

Ordinary sample indices cycle through three observable scene profiles.  The
``chain`` and ``star`` profiles preserve the public joint morphology; the
``all_degrees`` profile contains degrees 0, 1, 2, 3, and 4 at once and reuses
input colors across different degrees so color-lookup and size-lookup shortcuts
cannot explain the outputs.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e245314f96d8"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "12d5c7d2dc6c"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.60

SUMMARY = (
    "Find same-color 4-connected nonzero objects, count how many other objects "
    "touch each one cardinally, and recolor the whole object by degree: "
    "0->3, 1->4, 2->6, and 3+->8."
)
INVARIANTS = [
    "background is black (0) and output shape equals input shape",
    "object identity is same-color 4-connectivity",
    "contact means direct cardinal adjacency between distinct objects",
    "ordinary three-example lessons jointly demonstrate degrees 0, 1, 2, 3, and 4",
    "the generalized profile reuses input colors across different output classes",
]

SCENE_PROFILES = ("chain", "star", "all_degrees")
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule: chain|star|all_degrees",
        "valid": "chain|star|all_degrees",
    },
}

BACKGROUND = 0
INPUT_COLORS = tuple(range(1, 10))
DEGREE_COLORS = {0: 3, 1: 4, 2: 6}
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PROFILE_SCHEDULE = SCENE_PROFILES

# Public linked signatures: (height, width, palette size including background,
# sorted contact degrees, sorted component sizes).
_CANONICAL_SIGNATURES = {
    (8, 12, 5, (0, 1, 1, 2), (3, 4, 4, 4)): "chain",
    (9, 13, 6, (0, 1, 1, 1, 3), (1, 1, 1, 3, 4)): "star",
    (10, 13, 6, (0, 1, 1, 1, 3), (1, 3, 4, 4, 4)): "star",
}
_ALL_DEGREES = (0, 1, 1, 1, 1, 1, 2, 3, 4)
_ALL_DEGREE_DIMS = {(10, 13), (12, 15), (14, 18)}

# The strict templates are the public object morphologies, expressed without
# colors or absolute placement.  D4 transforms and translation preserve them.
_CHAIN_GROUPS = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 2), (0, 3), (1, 2), (1, 3)),
    ((0, 4), (1, 4), (1, 5)),
    ((4, 6), (4, 7), (5, 6), (5, 7)),
)
_STAR_TRAIN_GROUPS = (
    ((2, 2), (2, 3), (3, 2), (3, 3)),
    ((1, 2),),
    ((2, 1),),
    ((2, 4),),
    ((0, 7), (1, 7), (2, 7)),
)
_STAR_TEST_GROUPS = (
    ((2, 2), (2, 3), (3, 2), (3, 3)),
    ((2, 0), (2, 1), (3, 0), (3, 1)),
    ((2, 4), (2, 5), (3, 4), (3, 5)),
    ((1, 2),),
    ((6, 7), (7, 7), (7, 8)),
)

# Three non-isomorphic trees share the target degree multiset.  Object indices
# are semantic: 0/1/2 have degrees 4/3/2, 3..7 are leaves, and 8 is isolated.
# Random lawful growth below changes morphology while preserving each graph.
_ALL_DEGREE_TEMPLATES: tuple[tuple[Group, ...], ...] = (
    (
        ((3, 3),),
        ((1, 3),),
        ((2, 3),),
        ((0, 3),),
        ((1, 4),),
        ((4, 3),),
        ((3, 2),),
        ((3, 4),),
        ((0, 0),),
    ),
    (
        ((4, 3),),
        ((2, 3), (3, 3)),
        ((1, 3),),
        ((0, 3),),
        ((2, 4),),
        ((5, 3),),
        ((4, 2),),
        ((4, 4),),
        ((0, 0),),
    ),
    (
        ((3, 3), (3, 4)),
        ((3, 2),),
        ((3, 5),),
        ((2, 2),),
        ((4, 2),),
        ((3, 6),),
        ((2, 4),),
        ((4, 4),),
        ((0, 7),),
    ),
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

Grid = list[list[int]]
Cell = tuple[int, int]
Group = tuple[Cell, ...]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is None:
        scheduled = _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)

    rng = ctx.draw_rng(f"scene:{profile}:{band}")
    if profile == "chain":
        grid = _build_chain(rng, sample_index)
    elif profile == "star":
        grid = _build_star(rng, sample_index, band)
    else:
        grid = _build_all_degrees(rng, sample_index, band)

    errors = self_check(
        grid,
        difficulty=band,
        meta={"scene_profile": profile, "overrides": dict(overrides)},
    )
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete lawful teaching grammar and reject impostors."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if profile is None:
        errors.append(
            "scene does not match the chain, star, or all_degrees contact-graph grammar"
        )
        return errors

    if facts["nonzero_cells"] > facts["height"] * facts["width"] // 4:
        errors.append("objects occupy more than one quarter of the canvas")
    if len(set(facts["degrees"])) < 3:
        errors.append("scene must expose at least three distinct degree values")
    if facts["output"] == grid:
        errors.append("degree recoloring is an identity transformation")

    if profile == "all_degrees":
        if tuple(sorted(facts["degrees"])) != _ALL_DEGREES:
            errors.append("all_degrees must contain exact degree support 0,1,2,3,4")
        color_degree_sets: dict[int, set[int]] = defaultdict(set)
        color_output_sets: dict[int, set[int]] = defaultdict(set)
        for obj, degree in zip(facts["components"], facts["degrees"]):
            color_degree_sets[obj["color"]].add(degree)
            color_output_sets[obj["color"]].add(_degree_color(degree))
        if not any(len(values) >= 3 for values in color_degree_sets.values()):
            errors.append("one repeated input color must span at least three degrees")
        if not any(len(values) >= 3 for values in color_output_sets.values()):
            errors.append("one repeated input color must span at least three outputs")
    else:
        if facts["palette_size"] != len(facts["components"]) + 1:
            errors.append("canonical-linked profiles require distinct object colors")

    requested = None
    if isinstance(meta, dict):
        requested = meta.get("scene_profile")
        if requested is None and isinstance(meta.get("overrides"), dict):
            requested = meta["overrides"].get("scene_profile")
    if requested is not None and requested != profile:
        errors.append(f"scene_profile requested {requested!r}, observed {profile!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid is outside the exact public joint manifold."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    signature = _linked_signature(analysis["facts"])
    if signature not in _CANONICAL_SIGNATURES:
        return [f"joint canonical signature not observed: {signature!r}"]
    return []


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact public override from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    profile = _classify_profile(analysis["facts"])
    return {"scene_profile": profile} if profile is not None else {}


def canonical_profile_signature(grid):
    """Expose the strict joint signature for review tooling."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return _linked_signature(analysis["facts"])


def semantic_signature(grid) -> dict[str, Any]:
    """Return linked task observables used by the review census."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    color_degrees: dict[int, set[int]] = defaultdict(set)
    for obj, degree in zip(facts["components"], facts["degrees"]):
        color_degrees[obj["color"]].add(degree)
    return {
        "scene_profile": _classify_profile(facts),
        "height": facts["height"],
        "width": facts["width"],
        "palette_size": facts["palette_size"],
        "object_count": len(facts["components"]),
        "degree_histogram": dict(Counter(facts["degrees"])),
        "object_sizes": tuple(sorted(obj["size"] for obj in facts["components"])),
        "repeated_color_degrees": {
            str(color): tuple(sorted(values))
            for color, values in sorted(color_degrees.items())
            if len(values) > 1
        },
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python test mirror; the Racket rule remains the output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return deepcopy(analysis["facts"]["output"])


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave named shortcut rules consistent."""
    reasons: list[str] = []
    demo_rows: list[dict[str, int]] = []
    demo_profiles: set[str] = set()
    for index, pair in enumerate(demos):
        rows, profile, pair_errors = _pair_component_rows(pair)
        if pair_errors:
            reasons.extend(f"demo {index}: {error}" for error in pair_errors)
            continue
        demo_rows.extend(rows)
        demo_profiles.add(profile)

    query_rows, _, query_errors = _pair_component_rows(query)
    reasons.extend(f"query: {error}" for error in query_errors)
    if reasons:
        return reasons

    required_profiles = set(SCENE_PROFILES)
    if demo_profiles != required_profiles:
        reasons.append(
            f"demos must contain profiles {sorted(required_profiles)}, found {sorted(demo_profiles)}"
        )

    demonstrated_degrees = {row["degree"] for row in demo_rows}
    for degree in (0, 1, 2, 3, 4):
        if degree not in demonstrated_degrees:
            reasons.append(f"degree {degree} is not demonstrated")
    query_degrees = {row["degree"] for row in query_rows}
    unsupported = sorted(query_degrees - demonstrated_degrees)
    if unsupported:
        reasons.append(f"query uses unsupported degrees {unsupported}")

    expected = {0: 3, 1: 4, 2: 6, 3: 8, 4: 8}
    observed_map: dict[int, set[int]] = defaultdict(set)
    for row in demo_rows:
        observed_map[min(row["degree"], 4)].add(row["output_color"])
    for degree, color in expected.items():
        if observed_map.get(degree) != {color}:
            reasons.append(
                f"degree {degree} mapping is not uniquely demonstrated as color {color}"
            )

    if not _feature_conflicted(demo_rows, "input_color"):
        reasons.append("input-color lookup remains consistent with all demos")
    if not _feature_conflicted(demo_rows, "size"):
        reasons.append("component-size lookup remains consistent with all demos")
    if not _feature_conflicted(demo_rows, "reading_rank"):
        reasons.append("fixed reading-order rank remains consistent with all demos")
    return reasons


def _pair_component_rows(pair) -> tuple[list[dict[str, int]], str, list[str]]:
    errors: list[str] = []
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [], "", ["pair must contain input and output grids"]
    analysis = _analyze(pair["input"])
    if analysis["errors"]:
        return [], "", list(analysis["errors"])
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if profile is None:
        errors.append("input is outside the teaching grammar")
        return [], "", errors
    expected = facts["output"]
    if pair["output"] != expected:
        errors.append("output does not equal contact-degree recoloring")
        return [], profile, errors

    rows: list[dict[str, int]] = []
    for rank, (obj, degree) in enumerate(zip(facts["components"], facts["degrees"])):
        output_colors = {pair["output"][row][col] for row, col in obj["cells"]}
        if len(output_colors) != 1:
            errors.append(f"component {rank} is not uniformly recolored")
            continue
        rows.append(
            {
                "input_color": obj["color"],
                "size": obj["size"],
                "reading_rank": rank,
                "degree": min(degree, 4),
                "output_color": next(iter(output_colors)),
            }
        )
    return rows, profile, errors


def _feature_conflicted(rows: list[dict[str, int]], feature: str) -> bool:
    outcomes: dict[int, set[int]] = defaultdict(set)
    for row in rows:
        outcomes[row[feature]].add(row["output_color"])
    return any(len(values) > 1 for values in outcomes.values())


def _witness_degree(degree: int):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and degree in analysis["facts"]["degrees"]

    return predicate


def _witness_degree_four_plus(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        degree >= 4 for degree in analysis["facts"]["degrees"]
    )


def _witness_profile(name: str):
    def predicate(grid) -> bool:
        return observe_overrides(grid).get("scene_profile") == name

    return predicate


def _witness_color_independence(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    outcomes: dict[int, set[int]] = defaultdict(set)
    for obj, degree in zip(
        analysis["facts"]["components"], analysis["facts"]["degrees"]
    ):
        outcomes[obj["color"]].add(_degree_color(degree))
    return any(len(values) >= 3 for values in outcomes.values())


SEMANTIC_WITNESSES = {
    "degree_0_to_3": _witness_degree(0),
    "degree_1_to_4": _witness_degree(1),
    "degree_2_to_6": _witness_degree(2),
    "degree_3_to_8": _witness_degree(3),
    "degree_4_plus_to_8": _witness_degree_four_plus,
    "canonical_chain": _witness_profile("chain"),
    "canonical_star": _witness_profile("star"),
    "color_independence": _witness_color_independence,
}


def _build_chain(rng, sample_index: int) -> Grid:
    groups = _transform_groups(_CHAIN_GROUPS, (int(sample_index) + rng.randrange(8)) % 8)
    colors = rng.sample(INPUT_COLORS, len(groups))
    return _paint_groups(8, 12, groups, colors, rng)


def _build_star(rng, sample_index: int, band: str) -> Grid:
    if band == "easy":
        groups, height, width = _STAR_TRAIN_GROUPS, 9, 13
    elif band == "hard":
        groups, height, width = _STAR_TEST_GROUPS, 10, 13
    elif rng.random() < 0.5:
        groups, height, width = _STAR_TRAIN_GROUPS, 9, 13
    else:
        groups, height, width = _STAR_TEST_GROUPS, 10, 13
    transformed = _transform_groups(groups, (int(sample_index) + rng.randrange(8)) % 8)
    colors = rng.sample(INPUT_COLORS, len(transformed))
    return _paint_groups(height, width, transformed, colors, rng)


def _build_all_degrees(rng, sample_index: int, band: str) -> Grid:
    height, width = {
        "easy": (10, 13),
        "medium": (12, 15),
        "hard": (14, 18),
    }[band]
    step_ranges = {"easy": (4, 10), "medium": (7, 14), "hard": (10, 18)}
    for attempt in range(160):
        template_index = (int(sample_index) + rng.randrange(3) + attempt) % 3
        base = _ALL_DEGREE_TEMPLATES[template_index]
        graph = _groups_contact_graph(base)
        if tuple(sorted(len(neighbors) for neighbors in graph)) != _ALL_DEGREES:
            raise AssertionError("all_degrees template has the wrong contact graph")

        low, high = step_ranges[band]
        groups = _grow_groups_preserving_graph(
            rng,
            base,
            graph,
            steps=rng.randint(low, high),
            max_height=height,
            max_width=width,
        )
        groups = _transform_groups(
            groups, (int(sample_index) + rng.randrange(8)) % 8
        )
        if _group_extent(groups)[0] > height or _group_extent(groups)[1] > width:
            continue
        colors = _proper_repeated_colors(rng, graph)
        grid = _paint_groups(height, width, groups, colors, rng)
        facts = _analyze(grid)["facts"]
        if (
            facts is not None
            and len(facts["components"]) == 9
            and tuple(sorted(facts["degrees"])) == _ALL_DEGREES
        ):
            return grid
    raise RuntimeError("failed to construct a varied all_degrees scene")


def _groups_contact_graph(groups) -> tuple[frozenset[int], ...]:
    cell_sets = [frozenset(group) for group in groups]
    neighbors = [set() for _ in groups]
    for first_index, first in enumerate(cell_sets):
        for second_index in range(first_index + 1, len(cell_sets)):
            second = cell_sets[second_index]
            if any(
                (row + delta_row, col + delta_col) in second
                for row, col in first
                for delta_row, delta_col in _CARDINAL
            ):
                neighbors[first_index].add(second_index)
                neighbors[second_index].add(first_index)
    return tuple(frozenset(values) for values in neighbors)


def _group_extent(groups) -> tuple[int, int]:
    rows = [row for group in groups for row, _ in group]
    cols = [col for group in groups for _, col in group]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _normalize_groups(groups) -> tuple[Group, ...]:
    min_row = min(row for group in groups for row, _ in group)
    min_col = min(col for group in groups for _, col in group)
    return tuple(
        tuple(sorted((row - min_row, col - min_col) for row, col in group))
        for group in groups
    )


def _grow_groups_preserving_graph(
    rng,
    groups,
    graph,
    *,
    steps: int,
    max_height: int,
    max_width: int,
) -> tuple[Group, ...]:
    """Add morphology without introducing a contact edge.

    One leaf remains a singleton, as do the unique degree-2 vertex and enough
    high/zero-degree vertices to keep size lookup visibly contradictory.
    """
    mutable = [3, 4, 5, 6, 7]
    protected_leaf = rng.choice(mutable)
    mutable.remove(protected_leaf)
    grown = [set(group) for group in groups]
    occupied = {cell: index for index, group in enumerate(grown) for cell in group}

    for _ in range(steps):
        candidates: list[tuple[int, Cell]] = []
        for object_index in mutable:
            boundary = {
                (row + delta_row, col + delta_col)
                for row, col in grown[object_index]
                for delta_row, delta_col in _CARDINAL
                if (row + delta_row, col + delta_col) not in occupied
            }
            for candidate in boundary:
                touching = {
                    occupied[neighbor]
                    for delta_row, delta_col in _CARDINAL
                    if (neighbor := (candidate[0] + delta_row, candidate[1] + delta_col))
                    in occupied
                }
                if any(
                    other != object_index and other not in graph[object_index]
                    for other in touching
                ):
                    continue
                trial_rows = [cell[0] for cell in occupied] + [candidate[0]]
                trial_cols = [cell[1] for cell in occupied] + [candidate[1]]
                if (
                    max(trial_rows) - min(trial_rows) + 1 > max_height
                    or max(trial_cols) - min(trial_cols) + 1 > max_width
                ):
                    continue
                candidates.append((object_index, candidate))
        if not candidates:
            break
        object_index, candidate = rng.choice(candidates)
        grown[object_index].add(candidate)
        occupied[candidate] = object_index

    normalized = _normalize_groups(grown)
    if _groups_contact_graph(normalized) != graph:
        raise AssertionError("morphology growth changed the intended contact graph")
    return normalized


def _proper_repeated_colors(rng, graph) -> list[int]:
    """Use four colors while one nonadjacent color spans degrees 0, 1 and 2."""
    degree_two = next(index for index, neighbors in enumerate(graph) if len(neighbors) == 2)
    leaf = next(
        index
        for index, neighbors in enumerate(graph)
        if len(neighbors) == 1 and index not in graph[degree_two]
    )
    isolate = next(index for index, neighbors in enumerate(graph) if not neighbors)
    slots: dict[int, int] = {degree_two: 0, leaf: 0, isolate: 0}
    remaining = sorted(
        (index for index in range(len(graph)) if index not in slots),
        key=lambda index: len(graph[index]),
        reverse=True,
    )

    def assign(position: int) -> bool:
        if position == len(remaining):
            return set(slots.values()) == {0, 1, 2, 3}
        index = remaining[position]
        choices = [0, 1, 2, 3]
        rng.shuffle(choices)
        choices.sort(key=lambda slot: slot in slots.values())
        for slot in choices:
            if any(slots.get(neighbor) == slot for neighbor in graph[index]):
                continue
            slots[index] = slot
            if assign(position + 1):
                return True
            del slots[index]
        return False

    if not assign(0):
        raise RuntimeError("failed to color the all_degrees contact graph")
    palette = rng.sample(INPUT_COLORS, 4)
    return [palette[slots[index]] for index in range(len(graph))]


def _transform_groups(groups, transform_index: int) -> tuple[Group, ...]:
    turns = int(transform_index) % 4
    reflect = int(transform_index) >= 4
    transformed: list[list[Cell]] = []
    for group in groups:
        cells: list[Cell] = []
        for row, col in group:
            if reflect:
                col = -col
            for _ in range(turns):
                row, col = col, -row
            cells.append((row, col))
        transformed.append(cells)
    min_row = min(row for group in transformed for row, _ in group)
    min_col = min(col for group in transformed for _, col in group)
    return tuple(
        tuple(sorted((row - min_row, col - min_col) for row, col in group))
        for group in transformed
    )


def _paint_groups(height: int, width: int, groups, colors, rng) -> Grid:
    shape_height = max(row for group in groups for row, _ in group) + 1
    shape_width = max(col for group in groups for _, col in group) + 1
    if shape_height > height or shape_width > width:
        raise ValueError(
            f"scene {shape_height}x{shape_width} does not fit {height}x{width}"
        )
    top = rng.randint(0, height - shape_height)
    left = rng.randint(0, width - shape_width)
    grid = full_grid(height, width, BACKGROUND)
    for group, color in zip(groups, colors):
        for row, col in group:
            target = (top + row, left + col)
            if grid[target[0]][target[1]] != BACKGROUND:
                raise ValueError(f"overlapping object cells at {target}")
            grid[target[0]][target[1]] = color
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}
    height = len(grid)
    width = len(grid[0])
    components = _components(grid)
    if not components:
        return {"errors": ["grid contains no nonzero objects"], "facts": None}
    graph = _contact_graph(components)
    degrees = tuple(len(neighbors) for neighbors in graph)
    output = full_grid(height, width, BACKGROUND)
    for obj, degree in zip(components, degrees):
        color = _degree_color(degree)
        for row, col in obj["cells"]:
            output[row][col] = color
    facts = {
        "height": height,
        "width": width,
        "palette_size": len({value for row in grid for value in row}),
        "components": tuple(components),
        "graph": graph,
        "degrees": degrees,
        "output": output,
        "nonzero_cells": sum(obj["size"] for obj in components),
    }
    return {"errors": [], "facts": facts}


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list or tuple of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a list or tuple"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or 0 in widths:
        return ["grid must be rectangular and nonempty"]
    height = len(grid)
    width = next(iter(widths))
    errors: list[str] = []
    if not (6 <= height <= 30 and 6 <= width <= 30):
        errors.append(f"grid dimensions must be 6..30, found {height}x{width}")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
    if not any(value == BACKGROUND for row in grid for value in row):
        errors.append("black background color 0 must be present")
    return errors


def _components(grid: Grid) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == BACKGROUND or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_cell = (current[0] + delta_row, current[1] + delta_col)
                    if (
                        0 <= next_cell[0] < height
                        and 0 <= next_cell[1] < width
                        and next_cell not in seen
                        and grid[next_cell[0]][next_cell[1]] == color
                    ):
                        seen.add(next_cell)
                        stack.append(next_cell)
            ordered = tuple(sorted(cells))
            components.append(
                {
                    "color": color,
                    "cells": ordered,
                    "cell_set": frozenset(ordered),
                    "size": len(ordered),
                    "top_left": ordered[0],
                }
            )
    components.sort(key=lambda obj: obj["top_left"])
    return components


def _contact_graph(components) -> tuple[frozenset[int], ...]:
    neighbors = [set() for _ in components]
    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second_cells = components[second_index]["cell_set"]
            touching = any(
                (row + delta_row, col + delta_col) in second_cells
                for row, col in first["cells"]
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if touching:
                neighbors[first_index].add(second_index)
                neighbors[second_index].add(first_index)
    return tuple(frozenset(values) for values in neighbors)


def _degree_color(degree: int) -> int:
    return DEGREE_COLORS.get(degree, 8)


def _linked_signature(facts) -> tuple[Any, ...]:
    return (
        facts["height"],
        facts["width"],
        facts["palette_size"],
        tuple(sorted(facts["degrees"])),
        tuple(sorted(obj["size"] for obj in facts["components"])),
    )


def _classify_profile(facts) -> str | None:
    signature = _linked_signature(facts)
    if signature in _CANONICAL_SIGNATURES:
        return _CANONICAL_SIGNATURES[signature]
    dims = (facts["height"], facts["width"])
    sizes = tuple(sorted(obj["size"] for obj in facts["components"]))
    if (
        dims in _ALL_DEGREE_DIMS
        and facts["palette_size"] == 5
        and tuple(sorted(facts["degrees"])) == _ALL_DEGREES
        and len(facts["components"]) == 9
    ):
        return "all_degrees"
    return None
