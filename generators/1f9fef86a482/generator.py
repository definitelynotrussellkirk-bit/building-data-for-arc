"""Generate answer-identifying lessons for "Header Chooses the Degree".

The first row is a legend: the number ``k`` of blue cells (colour 1) is the
requested contact degree.  Below a blank separator row, non-zero same-colour
4-connected components form vertices of a graph; two vertices are adjacent
when any of their cells touch cardinally.  The output keeps exactly the
components whose graph degree is ``k``, recoloured cyan (8), and erases every
other cell.

Ordinary sample indices cycle through three observable scene profiles.  The
canonical-linked ``chain`` and ``star`` profiles preserve the public examples.
The ``all_degrees`` profile contains degrees 0, 1, 2, 3, and 4 at once, with a
component above the requested degree.  That scheduled counterexample prevents
the canonical-fitting shortcut "paint the maximum-degree component" from
surviving a complete three-example lesson.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1f9fef86a482"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "dfe6e5f597b6"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

SUMMARY = (
    "Count the blue cells in row 0 to obtain k. Below the blank separator, "
    "find same-colour 4-connected components and their cardinal-contact graph. "
    "Repaint every component of degree exactly k with 8 and erase the rest."
)
INVARIANTS = [
    "row 0 contains exactly two or three blue (1) legend cells and zeros",
    "row 1 is an all-zero separator",
    "body objects are same-colour 4-connected components using colours 2..7 or 9",
    "cardinal contact between different components defines graph adjacency",
    "at least one component has degree exactly equal to the legend count",
    "ordinary three-example windows contain chain, star, and all-degrees evidence",
]

SCENE_PROFILES = ("chain", "star", "all_degrees")
HEADER_STYLES = ("contiguous", "spaced")
SCHEDULE_PROFILES = (
    "chain_k2",
    "all_degrees_k2",
    "star_k3",
    "all_degrees_k3",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile-linked canonical anchor",
        "valid": "8..15",
    },
    "grid_w": {
        "type": "int",
        "default": "profile-linked canonical anchor",
        "valid": "11..17",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule: chain|star|all_degrees",
        "valid": "chain|star|all_degrees",
    },
    "header_style": {
        "type": "str",
        "default": "sample-index schedule: contiguous|spaced",
        "valid": "contiguous|spaced",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

BACKGROUND = 0
HEADER_COLOR = 1
OUTPUT_COLOR = 8
BODY_COLORS = (2, 3, 4, 5, 6, 7, 9)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_SCHEDULE = (
    ("chain", 2),
    ("all_degrees", 2),
    ("star", 3),
    ("all_degrees", 3),
)
_HEADER_SCHEDULE = HEADER_STYLES

Grid = list[list[int]]
Cell = tuple[int, int]
Group = tuple[Cell, ...]

# Canonical-linked contact graphs.  Group order is intentional: it identifies
# the target group for colour assignment and is preserved by D4 transforms.
_CHAIN_GROUPS: tuple[Group, ...] = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 2), (0, 3), (1, 2), (1, 3)),
    ((0, 4), (1, 4), (1, 5)),
    ((4, 6), (4, 7), (5, 6), (5, 7)),
)
_STAR_GROUPS: tuple[Group, ...] = (
    ((1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 1),),
    ((1, 3),),
    ((3, 2),),
    ((0, 6), (0, 7), (1, 6), (1, 7)),
)

# A grid-tree with exact degree support 0,1,2,3,4.  Repeated colour slots never
# occur across an edge, so each listed singleton remains its own component.
_ALL_DEGREE_GROUPS: tuple[Group, ...] = (
    ((3, 3),),  # degree 4
    ((2, 3),),  # degree 2
    ((1, 3),),  # degree 3
    ((0, 3),),  # degree 1
    ((1, 4),),  # degree 1
    ((4, 3),),  # degree 1
    ((3, 2),),  # degree 1
    ((3, 4),),  # degree 1
    ((0, 0),),  # degree 0
)
_ALL_DEGREE_COLOR_SLOTS = (0, 1, 2, 0, 1, 2, 3, 2, 0)
_ALL_DEGREES = (0, 1, 1, 1, 1, 1, 2, 3, 4)

# Public linked signatures: (h, w, palette size, k, profile).  The exact graph
# and object-size signatures are checked independently before this table.
_CANONICAL_SIGNATURES = {
    (8, 11, 6, 2, "chain"),
    (9, 12, 6, 2, "chain"),
    (9, 12, 7, 3, "star"),
}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    for name, lo, hi in (("grid_h", 8, 15), ("grid_w", 11, 17)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value!r} is outside {lo}..{hi}")

    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    style = overrides.get("header_style")
    if style is not None and style not in HEADER_STYLES:
        raise ValueError(f"unknown header_style: {style!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the named curriculum slot used at this position."""
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_header_style(sample_index: int) -> str:
    return _HEADER_SCHEDULE[int(sample_index) % len(_HEADER_SCHEDULE)]


def _default_dimensions(profile: str, band: str, sample_index: int) -> tuple[int, int]:
    if profile == "chain":
        return (8, 11) if (int(sample_index) // 3) % 2 == 0 else (9, 12)
    if profile == "star":
        return 9, 12
    return {
        "easy": (8, 11),
        "medium": (10, 13),
        "hard": (12, 15),
    }[band]


def _transform_cell(cell: Cell, variant: int) -> Cell:
    row, col = cell
    if variant == 0:
        return row, col
    if variant == 1:
        return col, -row
    if variant == 2:
        return -row, -col
    if variant == 3:
        return -col, row
    if variant == 4:
        return row, -col
    if variant == 5:
        return col, row
    if variant == 6:
        return -row, col
    return -col, -row


def _d4_variants(groups: tuple[Group, ...]) -> tuple[tuple[Group, ...], ...]:
    variants: list[tuple[Group, ...]] = []
    seen: set[tuple[Group, ...]] = set()
    for variant in range(8):
        transformed = [
            [_transform_cell(cell, variant) for cell in group]
            for group in groups
        ]
        min_row = min(row for group in transformed for row, _col in group)
        min_col = min(col for group in transformed for _row, col in group)
        normalized: tuple[Group, ...] = tuple(
            tuple(sorted((row - min_row, col - min_col) for row, col in group))
            for group in transformed
        )
        if normalized not in seen:
            seen.add(normalized)
            variants.append(normalized)
    return tuple(variants)


def _extent(groups: tuple[Group, ...]) -> tuple[int, int]:
    return (
        max(row for group in groups for row, _col in group) + 1,
        max(col for group in groups for _row, col in group) + 1,
    )


def _place_groups(
    grid: Grid,
    groups: tuple[Group, ...],
    colors: tuple[int, ...],
    rng,
) -> None:
    body_height = len(grid) - 2
    width = len(grid[0])
    fitting = [
        variant
        for variant in _d4_variants(groups)
        if _extent(variant)[0] <= body_height and _extent(variant)[1] <= width
    ]
    if not fitting:
        raise ValueError(
            f"profile does not fit body {body_height}x{width}; "
            f"template extents={[ _extent(v) for v in _d4_variants(groups) ]}"
        )
    placed = rng.choice(fitting)
    profile_h, profile_w = _extent(placed)
    top = rng.randint(2, len(grid) - profile_h)
    left = rng.randint(0, width - profile_w)
    for group, color in zip(placed, colors):
        for row, col in group:
            grid[top + row][left + col] = color


def _distinct_profile_colors(count: int, target_index: int, rng) -> tuple[int, ...]:
    colors = list(rng.sample(BODY_COLORS, count))
    if colors[target_index] == 3:
        swap_index = next(index for index in range(count) if index != target_index)
        colors[target_index], colors[swap_index] = colors[swap_index], colors[target_index]
    return tuple(colors)


def _all_degree_colors(rng) -> tuple[int, ...]:
    safe = [color for color in BODY_COLORS if color != 3]
    slot_colors = tuple(rng.sample(safe, 3)) + (3,)
    return tuple(slot_colors[slot] for slot in _ALL_DEGREE_COLOR_SLOTS)


def _header_positions(style: str, width: int, target_degree: int, rng) -> tuple[int, ...]:
    if style == "contiguous":
        start = rng.randint(0, width - target_degree)
        return tuple(range(start, start + target_degree))
    candidates = [
        positions
        for positions in combinations(range(width), target_degree)
        if positions != tuple(range(positions[0], positions[0] + target_degree))
    ]
    if not candidates:
        raise ValueError(f"cannot realize spaced header with width={width}, k={target_degree}")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid."""
    _validate_call(difficulty, overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    scheduled_target: int | None = None
    if overrides.get("scene_profile") is None:
        profile_name, scheduled_target = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
        profile = ctx.draw_choice("scene_profile", (profile_name,))
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)

    if overrides.get("header_style") is None:
        style = ctx.draw_choice(
            "header_style", (_scheduled_header_style(sample_index),)
        )
    else:
        style = ctx.draw_choice("header_style", HEADER_STYLES)

    default_h, default_w = _default_dimensions(profile, band, sample_index)
    height_options = tuple(range(8, 16)) if overrides.get("grid_h") is not None else (default_h,)
    width_options = tuple(range(11, 18)) if overrides.get("grid_w") is not None else (default_w,)
    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", width_options)

    if profile == "chain":
        target_degree = 2
        groups = _CHAIN_GROUPS
        colors = _distinct_profile_colors(4, 1, ctx.draw_rng("colors:chain"))
    elif profile == "star":
        target_degree = 3
        groups = _STAR_GROUPS
        colors = _distinct_profile_colors(5, 0, ctx.draw_rng("colors:star"))
    else:
        target_degree = (
            scheduled_target
            if scheduled_target is not None
            else 2 + ((int(sample_index) // 3) % 2)
        )
        groups = _ALL_DEGREE_GROUPS
        colors = _all_degree_colors(ctx.draw_rng("colors:all_degrees"))

    grid = full_grid(height, width, BACKGROUND)
    for col in _header_positions(
        style, width, target_degree, ctx.draw_rng("header")
    ):
        grid[0][col] = HEADER_COLOR
    _place_groups(grid, groups, colors, ctx.draw_rng(f"layout:{profile}"))

    expected = {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
        "header_style": style,
    }
    errors = self_check(grid, difficulty=band, meta=expected)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 8 <= len(grid) <= 15 or not 11 <= width <= 17:
        return [f"teaching grid dimensions must be 8..15 by 11..17, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    found: list[dict[str, Any]] = []
    for row in range(2, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        2 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            ordered = tuple(sorted(cells))
            found.append(
                {
                    "color": color,
                    "cells": ordered,
                    "cell_set": frozenset(ordered),
                    "size": len(ordered),
                    "top_left": ordered[0],
                }
            )
    found.sort(key=lambda obj: obj["top_left"])
    return found


def _contact_graph(components: list[dict[str, Any]]) -> tuple[frozenset[int], ...]:
    graph = [set() for _ in components]
    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second = components[second_index]["cell_set"]
            if any(
                (row + dr, col + dc) in second
                for row, col in first["cells"]
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                graph[first_index].add(second_index)
                graph[second_index].add(first_index)
    return tuple(frozenset(neighbors) for neighbors in graph)


def _classify_profile(facts: dict[str, Any]) -> str | None:
    degrees = tuple(sorted(facts["degrees"]))
    sizes = tuple(sorted(obj["size"] for obj in facts["components"]))
    if degrees == (0, 1, 1, 2) and sizes == (3, 4, 4, 4):
        return "chain"
    if degrees == (0, 1, 1, 1, 3) and sizes == (1, 1, 1, 4, 4):
        return "star"
    if degrees == _ALL_DEGREES and sizes == (1,) * 9:
        return "all_degrees"
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "facts": {}}

    height, width = len(grid), len(grid[0])
    if any(value not in (0, 1) for value in grid[0]):
        errors.append("row 0 must contain only legend colour 1 and background 0")
    header_positions = tuple(col for col, value in enumerate(grid[0]) if value == 1)
    target_degree = len(header_positions)
    if target_degree not in (2, 3):
        errors.append(f"legend count must be 2 or 3, found {target_degree}")
    if any(value != 0 for value in grid[1]):
        errors.append("row 1 must be an all-zero separator")

    illegal_body = sorted(
        {
            grid[row][col]
            for row in range(2, height)
            for col in range(width)
            if grid[row][col] not in (0, *BODY_COLORS)
        }
    )
    if illegal_body:
        errors.append(f"body contains forbidden colours {illegal_body}")
    if not any(grid[row][col] == 0 for row in range(height) for col in range(width)):
        errors.append("background colour 0 must be present")

    if errors:
        return {"errors": errors, "facts": {}}

    components = _components(grid)
    if not components:
        errors.append("body must contain at least one non-zero component")
        return {"errors": errors, "facts": {}}
    graph = _contact_graph(components)
    degrees = tuple(len(neighbors) for neighbors in graph)
    profile = _classify_profile({"degrees": degrees, "components": components})
    if profile is None:
        errors.append("scene is outside the chain, star, or all_degrees grammar")

    matching = [index for index, degree in enumerate(degrees) if degree == target_degree]
    if len(matching) != 1:
        errors.append(
            f"expected exactly one component of legend degree {target_degree}, found {len(matching)}"
        )
    expected_target = {"chain": 2, "star": 3}.get(profile)
    if expected_target is not None and target_degree != expected_target:
        errors.append(
            f"{profile} profile requires legend degree {expected_target}, found {target_degree}"
        )

    colors = [obj["color"] for obj in components]
    if profile in ("chain", "star") and len(set(colors)) != len(colors):
        errors.append(f"{profile} profile requires a distinct colour for every component")
    if profile == "all_degrees":
        if len(set(colors)) != 4:
            errors.append("all_degrees profile requires exactly four body colours")
        color_degrees: dict[int, set[int]] = defaultdict(set)
        for obj, degree in zip(components, degrees):
            color_degrees[obj["color"]].add(degree)
        if not any(len(values) >= 3 for values in color_degrees.values()):
            errors.append("all_degrees must reuse one colour across at least three degrees")

    output = full_grid(height, width, 0)
    for obj, degree in zip(components, degrees):
        if degree == target_degree:
            for row, col in obj["cells"]:
                output[row][col] = OUTPUT_COLOR

    facts = {
        "height": height,
        "width": width,
        "header_positions": header_positions,
        "target_degree": target_degree,
        "components": components,
        "graph": graph,
        "degrees": degrees,
        "profile": profile,
        "palette_size": len({value for row in grid for value in row}),
        "output": output,
        "nonzero_cells": sum(value != 0 for row in grid for value in row),
    }
    return {"errors": errors, "facts": facts}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete generated teaching grammar."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover all exact declared controls from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    positions = facts["header_positions"]
    contiguous = positions == tuple(range(positions[0], positions[0] + len(positions)))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "scene_profile": facts["profile"],
        "header_style": "contiguous" if contiguous else "spaced",
    }


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid is outside the exact public joint manifold."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    facts = analysis["facts"]
    signature = (
        facts["height"],
        facts["width"],
        facts["palette_size"],
        facts["target_degree"],
        facts["profile"],
    )
    if signature not in _CANONICAL_SIGNATURES:
        return [f"joint canonical signature not observed: {signature!r}"]
    return []


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (
        facts["height"],
        facts["width"],
        facts["palette_size"],
        facts["target_degree"],
        facts["profile"],
    )


def semantic_signature(grid) -> dict[str, Any]:
    """Expose graph and curriculum observables to review tooling."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        **observe_overrides(grid),
        "target_degree": facts["target_degree"],
        "degree_histogram": dict(Counter(facts["degrees"])),
        "object_sizes": tuple(sorted(obj["size"] for obj in facts["components"])),
        "palette_size": facts["palette_size"],
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror for tests; the canonical Racket rule is authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return deepcopy(analysis["facts"]["output"])


def _paint_selected(grid: Grid, predicate) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    output = full_grid(facts["height"], facts["width"], 0)
    for obj, degree in zip(facts["components"], facts["degrees"]):
        if predicate(obj, degree, facts):
            for row, col in obj["cells"]:
                output[row][col] = OUTPUT_COLOR
    return output


def _maximum_degree(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    maximum = max(analysis["facts"]["degrees"])
    return _paint_selected(grid, lambda _obj, degree, _facts: degree == maximum)


def _fixed_degree_two(grid: Grid) -> Grid:
    return _paint_selected(grid, lambda _obj, degree, _facts: degree == 2)


def _color_three(grid: Grid) -> Grid:
    return _paint_selected(grid, lambda obj, _degree, _facts: obj["color"] == 3)


def _higher_degree_distractor(grid: Grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    facts = analysis["facts"]
    return (
        facts["target_degree"] in facts["degrees"]
        and max(facts["degrees"]) > facts["target_degree"]
    )


def _degree_three_header(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["facts"]["target_degree"] == 3


def _target_not_color_three(grid: Grid) -> bool:
    try:
        return _color_three(grid) != rule_mirror(grid)
    except ValueError:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "higher_degree_distractor": _higher_degree_distractor,
    "degree_three_header": _degree_three_header,
    "target_not_color_three": _target_not_color_three,
}
SEMANTIC_RIVALS = {
    "maximum_degree": _maximum_degree,
    "fixed_degree_two": _fixed_degree_two,
    "color_three": _color_three,
}
WITNESS_RIVALS = {
    "higher_degree_distractor": ["maximum_degree"],
    "degree_three_header": ["fixed_degree_two"],
    "target_not_color_three": ["color_three"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"maximum_degree": _maximum_degree}


def lesson_identifiable(demos, query) -> list[str]:
    """Require three demonstrations to eliminate all declared shortcut rules."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the teaching grammar")

    valid_demos: list[dict[str, Any]] = []
    profiles: set[str] = set()
    target_degrees: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not exact-degree filtering")
            continue
        signature = semantic_signature(demo["input"])
        profiles.add(signature["scene_profile"])
        target_degrees.add(signature["target_degree"])
        valid_demos.append(demo)

    if not any(_higher_degree_distractor(demo["input"]) for demo in valid_demos):
        reasons.append("demos need a component whose degree exceeds the legend count")
    if not {2, 3}.issubset(target_degrees):
        reasons.append(f"demos must demonstrate legend degrees 2 and 3, found {sorted(target_degrees)}")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
