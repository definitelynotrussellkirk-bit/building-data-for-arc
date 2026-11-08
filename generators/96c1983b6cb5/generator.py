"""Lawful input sampler for ARC task 96c1983b6cb5.

The selected authority splits three square panels at two full cyan columns,
infers the unique D4 transform taking A to B, and applies it to C.  This module
samples inputs only; ``reference_output`` is an executable mirror used for
validation and semantic-rival probes, not a replacement authority.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "96c1983b6cb5"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "9c8ca59a982a"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Split three 3..5 square panels at full color-8 columns, infer the unique "
    "D4 transform mapping A to B, then apply it to C. Panel size, transform, "
    "foreground counts, shapes, and source/target colors all vary exactly."
)
INVARIANTS = [
    "exactly three equal 3..5 square panels are separated by two full color-8 columns",
    "A and B contain one shared source color and C contains one distinct target color",
    "A and C are fully asymmetric under D4, so A->B is unique and nonidentity transforms are visible on C",
    "the sampler covers all eight D4 transforms in canonical Racket order",
    "every three-example default lesson contains a transform absent from canonical examples",
]

# The first three are the canonical color roles.  The last two prevent a model
# from treating the source/target color mapping itself as the task.
PALETTE_PAIRS = ((2, 3), (4, 5), (6, 7), (1, 6), (5, 2))
TRANSFORM_NAMES = (
    "id",
    "rot90",
    "rot180",
    "rot270",
    "flip-h",
    "flip-v",
    "transpose",
    "anti-transpose",
)
CANONICAL_TRANSFORMS = frozenset({1, 4, 6})

AXES = {
    "panel_n": {
        "type": "int",
        "default": "difficulty-skewed schedule with canonical-size support",
        "valid": "3..5",
    },
    "transform": {
        "type": "int",
        "default": "eight-step D4 teaching schedule",
        "valid": "0..7",
    },
    "a_cells": {
        "type": "int",
        "default": "difficulty-skewed 3..6",
        "valid": "3..6",
    },
    "c_cells": {
        "type": "int",
        "default": "difficulty-skewed 3..6",
        "valid": "3..6",
    },
    "palette_id": {
        "type": "int",
        "default": "uniform over five source/target pairs",
        "valid": "0..4",
    },
}

# Every Cartesian combination above is supported.  Declaring the empty set opts
# the checker into strict classification instead of legacy warning semantics.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

# No three consecutive values lie wholly in {1,4,6}, the transforms exposed by
# the three canonical pairs.  Thus every default three-demo lesson refutes the
# named canonical-subset rival below, regardless of its start offset.
_TRANSFORM_SCHEDULE = (1, 0, 4, 2, 6, 3, 5, 7)
_PANEL_SCHEDULES = {
    None: (3, 4, 3, 5, 4),
    "easy": (3, 3, 4, 3, 5),
    "medium": (3, 4, 5, 3, 4),
    "hard": (3, 5, 4, 5, 3),
}
_COUNT_OPTIONS = {
    None: (3, 4, 5, 6),
    "easy": (3, 3, 4, 4, 5, 6),
    "medium": (3, 4, 5, 5, 6),
    "hard": (3, 4, 5, 6, 6),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    ranges = {
        "panel_n": (3, 5),
        "transform": (0, 7),
        "a_cells": (3, 6),
        "c_cells": (3, 6),
        "palette_id": (0, len(PALETTE_PAIRS) - 1),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} override must be an integer")
        lo, hi = ranges[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _draw_exact(ctx, name: str, domain: Iterable[int], defaults: Iterable[int]) -> int:
    domain_tuple = tuple(domain)
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return int(ctx.draw_choice(name, domain_tuple))
    return int(ctx.draw_choice(name, tuple(defaults)))


def _transform_cells(
    cells: Iterable[tuple[int, int]], n: int, code: int
) -> frozenset[tuple[int, int]]:
    source = frozenset(cells)
    if code == 0:
        return source
    if code == 1:  # rotate clockwise
        return frozenset((col, n - 1 - row) for row, col in source)
    if code == 2:
        return frozenset((n - 1 - row, n - 1 - col) for row, col in source)
    if code == 3:  # rotate counter-clockwise
        return frozenset((n - 1 - col, row) for row, col in source)
    if code == 4:  # flip left-right
        return frozenset((row, n - 1 - col) for row, col in source)
    if code == 5:  # flip up-down
        return frozenset((n - 1 - row, col) for row, col in source)
    if code == 6:
        return frozenset((col, row) for row, col in source)
    if code == 7:
        return frozenset((n - 1 - col, n - 1 - row) for row, col in source)
    raise ValueError(f"unknown transform code {code}")


def _transform_grid(panel: list[list[int]], code: int) -> list[list[int]]:
    n = len(panel)
    if n == 0 or any(len(row) != n for row in panel):
        raise ValueError("transform expects a nonempty square panel")
    result = [[0] * n for _ in range(n)]
    for row in range(n):
        for col in range(n):
            target = next(iter(_transform_cells(((row, col),), n, code)))
            result[target[0]][target[1]] = panel[row][col]
    return result


def _dihedral_images(
    cells: Iterable[tuple[int, int]], n: int
) -> tuple[frozenset[tuple[int, int]], ...]:
    source = frozenset(cells)
    return tuple(_transform_cells(source, n, code) for code in range(8))


def _draw_asymmetric_shape(
    rng: Any,
    n: int,
    count: int,
    *,
    forbidden: frozenset[frozenset[tuple[int, int]]] = frozenset(),
) -> frozenset[tuple[int, int]]:
    all_cells = [(row, col) for row in range(n) for col in range(n)]
    for _ in range(4096):
        candidate = frozenset(rng.sample(all_cells, count))
        images = _dihedral_images(candidate, n)
        if len(set(images)) == 8 and candidate not in forbidden:
            return candidate
    raise RuntimeError(
        f"unable to sample an asymmetric {count}-cell shape in a {n}x{n} panel"
    )


def _paint(
    grid: list[list[int]], left: int, cells: Iterable[tuple[int, int]], color: int
) -> None:
    for row, col in sorted(cells):
        grid[row][left + col] = color


def _split_panels(grid: list[list[int]], n: int) -> tuple[list[list[int]], ...]:
    return (
        [list(row[:n]) for row in grid],
        [list(row[n + 1 : 2 * n + 1]) for row in grid],
        [list(row[2 * n + 2 :]) for row in grid],
    )


def _panel_facts(panel: list[list[int]]) -> tuple[int | None, frozenset[tuple[int, int]]]:
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        return None, frozenset()
    color = next(iter(colors))
    return color, frozenset(
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value == color
    )


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"], None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], None
    if any(type(value) is not int or not 0 <= value <= 8 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..8"], None

    n = len(grid)
    errors: list[str] = []
    if not 3 <= n <= 5:
        errors.append(f"panel height {n} outside 3..5")
    if width != 3 * n + 2:
        errors.append(f"expected width 3*n+2={3 * n + 2}, got {width}")
    if errors:
        return errors, None

    expected_separators = (n, 2 * n + 1)
    actual_separators = tuple(
        col for col in range(width) if all(grid[row][col] == 8 for row in range(n))
    )
    if actual_separators != expected_separators:
        errors.append(
            f"expected full color-8 separators at {expected_separators}, got {actual_separators}"
        )
    for row in range(n):
        for col in range(width):
            if grid[row][col] == 8 and col not in expected_separators:
                errors.append(f"color 8 is reserved for separators; found at ({row},{col})")
                break
        if errors and errors[-1].startswith("color 8"):
            break

    panel_a, panel_b, panel_c = _split_panels([list(row) for row in grid], n)
    source_a, cells_a = _panel_facts(panel_a)
    source_b, cells_b = _panel_facts(panel_b)
    target, cells_c = _panel_facts(panel_c)
    if source_a is None:
        errors.append("panel A must contain exactly one nonzero color")
    if source_b is None:
        errors.append("panel B must contain exactly one nonzero color")
    if target is None:
        errors.append("panel C must contain exactly one nonzero color")
    if errors:
        return errors, None
    assert source_a is not None and source_b is not None and target is not None

    if source_a != source_b:
        errors.append(f"A/B foreground colors differ: {source_a} vs {source_b}")
    if source_a == target:
        errors.append("C foreground color must differ from A/B")
    palette = (source_a, target)
    if palette not in PALETTE_PAIRS:
        errors.append(f"source/target palette pair {palette} is outside the declared domain")
    if not 3 <= len(cells_a) <= 6:
        errors.append(f"A cell count {len(cells_a)} outside 3..6")
    if len(cells_b) != len(cells_a):
        errors.append("B must preserve A's foreground-cell count")
    if not 3 <= len(cells_c) <= 6:
        errors.append(f"C cell count {len(cells_c)} outside 3..6")
    if len(set(_dihedral_images(cells_a, n))) != 8:
        errors.append("panel A is D4-symmetric, so A->B is ambiguous")
    if len(set(_dihedral_images(cells_c, n))) != 8:
        errors.append("panel C is D4-symmetric, so the requested transform may be invisible")

    matches = [
        code
        for code in range(8)
        if _transform_cells(cells_a, n, code) == cells_b
    ]
    if len(matches) != 1:
        errors.append(f"A->B must have one exact D4 transform, found {matches}")
        transform = None
    else:
        transform = matches[0]
    if errors:
        return errors, None

    assert transform is not None
    return [], {
        "panel_n": n,
        "transform": transform,
        "a_cells": len(cells_a),
        "c_cells": len(cells_c),
        "palette_id": PALETTE_PAIRS.index(palette),
        "panels": (panel_a, panel_b, panel_c),
        "cells_a": cells_a,
        "cells_b": cells_b,
        "cells_c": cells_c,
        "source_color": source_a,
        "target_color": target,
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    errors, _ = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Return reasons outside the selected task's lawful input manifold."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {name: int(analysis[name]) for name in AXES}


def reference_output(grid: Any) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    return _transform_grid(analysis["panels"][2], analysis["transform"])


# Familiar alias used by several task-local review harnesses.
rule_mirror = reference_output


def _canonical_subset_only(grid: Any) -> list[list[int]]:
    """Plausible wrong rule that knows only transforms in canonical examples."""
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    code = analysis["transform"]
    if code not in CANONICAL_TRANSFORMS:
        code = 1
    return _transform_grid(analysis["panels"][2], code)


def _witness_noncanonical_transform(grid: Any) -> bool:
    errors, analysis = _analyze_grid(grid)
    return not errors and analysis is not None and analysis["transform"] not in CANONICAL_TRANSFORMS


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "noncanonical_transform": _witness_noncanonical_transform,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "canonical_transform_subset_only": _canonical_subset_only,
}
WITNESS_RIVALS = {
    "noncanonical_transform": ["canonical_transform_subset_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require demos to falsify every named query-changing competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    episodes = list(demos) + [query]
    for index, episode in enumerate(episodes):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{label} must contain input and output")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{label} is outside the rule domain: {errors[0]}")
            continue
        if episode["output"] != reference_output(episode["input"]):
            reasons.append(f"{label} output disagrees with the selected rule")
    if reasons:
        return reasons

    truth = reference_output(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"]
            for demo in demos
        )
        if survives and competitor(query["input"]) != truth:
            reasons.append(f"named competitor {name!r} fits every demo but changes the query")
    return reasons


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    panel_default = _PANEL_SCHEDULES[difficulty][sample_index % len(_PANEL_SCHEDULES[difficulty])]
    n = _draw_exact(ctx, "panel_n", range(3, 6), (panel_default,))
    transform_default = _TRANSFORM_SCHEDULE[sample_index % len(_TRANSFORM_SCHEDULE)]
    transform = _draw_exact(ctx, "transform", range(8), (transform_default,))
    count_options = _COUNT_OPTIONS[difficulty]
    a_cells = _draw_exact(ctx, "a_cells", range(3, 7), count_options)
    c_cells = _draw_exact(ctx, "c_cells", range(3, 7), tuple(reversed(count_options)))
    palette_id = _draw_exact(
        ctx,
        "palette_id",
        range(len(PALETTE_PAIRS)),
        range(len(PALETTE_PAIRS)),
    )

    shape_a = _draw_asymmetric_shape(ctx.draw_rng("shape_a"), n, a_cells)
    orbit_a = frozenset(_dihedral_images(shape_a, n))
    shape_c = _draw_asymmetric_shape(
        ctx.draw_rng("shape_c"), n, c_cells, forbidden=orbit_a
    )

    source_color, target_color = PALETTE_PAIRS[palette_id]
    grid = full_grid(n, 3 * n + 2, 0)
    for row in range(n):
        grid[row][n] = 8
        grid[row][2 * n + 1] = 8
    _paint(grid, 0, shape_a, source_color)
    _paint(grid, n + 1, _transform_cells(shape_a, n, transform), source_color)
    _paint(grid, 2 * n + 2, shape_c, target_color)

    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(errors))
    expected = {
        "panel_n": n,
        "transform": transform,
        "a_cells": a_cells,
        "c_cells": c_cells,
        "palette_id": palette_id,
    }
    observed = {name: analysis[name] for name in AXES}
    if observed != expected:
        raise RuntimeError(f"internal axis mismatch: expected {expected}, observed {observed}")
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-semantic near misses that the validator must reject."""
    base = generate(
        53,
        11,
        panel_n=4,
        transform=3,
        a_cells=5,
        c_cells=4,
        palette_id=0,
    )
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_separator = deepcopy(base)
    for row in missing_separator:
        row[4] = 0
    fixtures.append(("missing_separator", missing_separator))

    symmetric_demo = deepcopy(base)
    for row in range(4):
        symmetric_demo[row][0:4] = [0, 0, 0, 0]
        symmetric_demo[row][5:9] = [0, 0, 0, 0]
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2)):
        symmetric_demo[row][col] = 2
        symmetric_demo[row][col + 5] = 2
    fixtures.append(("symmetric_demo", symmetric_demo))

    empty_query = deepcopy(base)
    for row in range(4):
        empty_query[row][10:14] = [0, 0, 0, 0]
    fixtures.append(("empty_query", empty_query))

    wrong_b_color = deepcopy(base)
    for row in wrong_b_color:
        for col in range(5, 9):
            if row[col] not in (0, 8):
                row[col] = 3
    fixtures.append(("wrong_b_color", wrong_b_color))

    symmetric_query = deepcopy(base)
    for row in range(4):
        symmetric_query[row][10:14] = [0, 0, 0, 0]
    for row, col in ((1, 11), (1, 12), (2, 11), (2, 12)):
        symmetric_query[row][col] = 3
    fixtures.append(("symmetric_query", symmetric_query))
    return fixtures
