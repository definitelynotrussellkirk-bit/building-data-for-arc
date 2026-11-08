"""Constructive generator for ARC task 4179e1ac3cf7.

Rule
----
The lone color-1 component is a shape template.  On a fresh zero grid,
each color-3 component with exactly the same translation-normalized shape is
painted in color 8 together with its horizontal reflection inside its own
bounding box.  Nonmatching color-3 components disappear.

The generator is deliberately constructive: the largest valid override request
(template + three matches + two distractors) always fits in six isolated 3x3
slots, so no requested object can be silently dropped.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4179e1ac3cf7"
TASK_ID = "4179e1ac3cf7"
VERSION = "3.1.0"
RULE_HASH = "1cfd3e1c42af"

SUMMARY = (
    "A 10..14 by 12..16 zero grid contains one connected color-1 template, "
    "one to three exact translated color-3 copies, and zero to two nonmatching "
    "color-3 distractors.  The template has 3..5 cells, fits a 3x3 box, and is "
    "not horizontally symmetric.  Output starts empty; every exact green copy "
    "is recolored 8 and completed with its horizontal reflection inside its "
    "own bounding box, while all nonmatches are erased."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0 and the input palette is exactly drawn from {0,1,3}",
    "there is exactly one connected 3..5-cell color-1 template",
    "the template is horizontally asymmetric and fits inside a 3x3 box",
    "there are 1..3 exact translated color-3 copies of the template",
    "there are 0..2 connected color-3 components with different normalized shapes",
]

# Every declared axis is exact, consumed by GenCtx, and recoverable from pixels
# through observe_overrides().  There are no decorative aliases or dead axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted choice over 10..14",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted choice over 12..16",
        "valid": "12..16",
    },
    "n_matches": {
        "type": "int",
        "default": "difficulty-weighted choice over 1..3",
        "valid": "1..3",
    },
    "n_distractors": {
        "type": "int",
        "default": "difficulty-weighted choice over 0..2",
        "valid": "0..2",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-weighted choice over 3..5",
        "valid": "3..5",
    },
}

# The six-slot construction realizes every Cartesian product in AXES.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

# Default sequential lessons reserve one of every four sample indices for a
# wrong-rule counterexample.  Explicit overrides always take precedence.
SCHEDULE_PROFILES = ("counterexample_slot", "ordinary")


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return (
        "counterexample_slot"
        if sample_index % EXAMPLES_NEEDED == 0
        else "ordinary"
    )

_AXIS_BOUNDS = {
    "grid_h": (10, 14),
    "grid_w": (12, 16),
    "n_matches": (1, 3),
    "n_distractors": (0, 2),
    "shape_size": (3, 5),
}

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _mirror(shape: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Horizontal reflection in the shape's own normalized bounding box."""
    normalized = _normalize(shape)
    if not normalized:
        return ()
    width = max(col for _, col in normalized) + 1
    return tuple(sorted((row, width - 1 - col) for row, col in normalized))


def _connected(shape: Sequence[tuple[int, int]]) -> bool:
    points = set(shape)
    if not points:
        return False
    pending = [next(iter(points))]
    seen = {pending[0]}
    while pending:
        row, col = pending.pop()
        for dr, dc in _NEIGHBORS:
            nxt = (row + dr, col + dc)
            if nxt in points and nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return seen == points


def _build_shape_bank() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """All connected, horizontally asymmetric 3x3 polyominoes of size 3..5."""
    cells = tuple((row, col) for row in range(3) for col in range(3))
    bank: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(3, 6):
        shapes = {
            _normalize(candidate)
            for candidate in combinations(cells, size)
            if _connected(candidate)
        }
        asymmetric = tuple(sorted(shape for shape in shapes if shape != _mirror(shape)))
        if len(asymmetric) < 3:
            raise RuntimeError(f"shape bank for size {size} is unexpectedly small")
        bank[size] = asymmetric
    return bank


_SHAPES = _build_shape_bank()


def _components(grid: Sequence[Sequence[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while pending:
                current = pending.pop()
                component.append(current)
                cr, cc = current
                for dr, dc in _NEIGHBORS:
                    nxt = (cr + dr, cc + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        pending.append(nxt)
            result.append(component)
    return result


def _weighted_options(axis: str, difficulty: str | None) -> tuple[int, ...]:
    """Return a full-domain weighted schedule; overrides remain legal in every band."""
    if axis == "grid_h":
        # Canonical rows are 10/11 high; retain broad support for 12..14.
        return (10, 10, 10, 11, 11, 11, 11, 11, 12, 13, 14)
    if axis == "grid_w":
        # Canonical rows are 12/13 wide; retain broad support for 14..16.
        return (12, 12, 12, 12, 12, 12, 13, 13, 13, 14, 15, 16)
    if axis == "n_matches":
        if difficulty == "easy":
            return (1, 1, 1, 2, 3)
        if difficulty == "hard":
            return (1, 2, 3, 3, 3)
        return (1, 2, 2, 3)
    if axis == "n_distractors":
        if difficulty == "easy":
            return (0, 0, 0, 1, 1, 2)
        if difficulty == "hard":
            return (0, 1, 1, 1, 2, 2)
        return (0, 1, 1, 1, 2)
    if axis == "shape_size":
        if difficulty == "easy":
            return (3, 3, 4, 5)
        if difficulty == "hard":
            return (3, 4, 5, 5)
        return (3, 4, 4, 5)
    raise KeyError(axis)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:  # bool is deliberately rejected.
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _slot_origins(height: int, width: int) -> list[tuple[int, int]]:
    """Six mutually four-neighbor-isolated 3x3 boxes."""
    rows = (0, height - 3)
    cols = (0, (width - 3) // 2, width - 3)
    slots = [(row, col) for row in rows for col in cols]
    # Smallest canvas is 10x12: its slot boxes are [0..2]/[7..9] by
    # [0..2]/[4..6]/[9..11], so at least one zero row/column separates them.
    if len(set(slots)) != 6:
        raise RuntimeError("slot construction produced duplicate boxes")
    return slots


def _paint_in_slot(
    grid: list[list[int]],
    shape: Sequence[tuple[int, int]],
    color: int,
    slot: tuple[int, int],
    rng,
) -> None:
    normalized = _normalize(shape)
    shape_h = max(row for row, _ in normalized) + 1
    shape_w = max(col for _, col in normalized) + 1
    if shape_h > 3 or shape_w > 3:
        raise RuntimeError("shape does not fit its constructive 3x3 slot")
    offset_row = rng.randint(0, 3 - shape_h)
    offset_col = rng.randint(0, 3 - shape_w)
    base_row = slot[0] + offset_row
    base_col = slot[1] + offset_col
    for row, col in normalized:
        rr, cc = base_row + row, base_col + col
        if grid[rr][cc] != 0:
            raise RuntimeError("constructive slot overlap")
        grid[rr][cc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = ctx.draw_choice("grid_h", _weighted_options("grid_h", difficulty))
    width = ctx.draw_choice("grid_w", _weighted_options("grid_w", difficulty))
    n_matches = ctx.draw_choice("n_matches", _weighted_options("n_matches", difficulty))
    if overrides.get("n_distractors") is not None:
        # Keep every exact override legal at every sample index, including the
        # curriculum-reserved counterexample slots.
        distractor_options = (0, 1, 2)
    elif schedule_profile(seed, sample_index, difficulty) == "counterexample_slot":
        # Any four consecutive demo indices contain exactly one such residue,
        # so every ordinary 4-demo lesson demonstrates that a reflected-but-
        # nonidentical green shape must be erased.
        distractor_options = (1, 1, 1, 2, 2)
    else:
        distractor_options = _weighted_options("n_distractors", difficulty)
    n_distractors = ctx.draw_choice("n_distractors", distractor_options)
    shape_size = ctx.draw_choice("shape_size", _weighted_options("shape_size", difficulty))

    template_rng = ctx.draw_rng("template_shape")
    template = template_rng.choice(_SHAPES[shape_size])

    distractors: list[tuple[tuple[int, int], ...]] = []
    if n_distractors:
        # A reflected template is a particularly important wrong-rule witness:
        # it has the right size and is congruent under reflection, but is NOT an
        # exact normalized match and therefore must disappear.
        reflected = _mirror(template)
        if reflected == template:
            raise RuntimeError("asymmetric template invariant was violated")
        distractors.append(reflected)
    if n_distractors == 2:
        alternatives = [
            shape
            for shape in _SHAPES[shape_size]
            if shape not in (template, distractors[0])
        ]
        if not alternatives:
            raise RuntimeError("no second distractor shape available")
        distractors.append(ctx.draw_rng("second_distractor_shape").choice(alternatives))

    components_to_place: list[tuple[int, tuple[tuple[int, int], ...]]] = [
        (1, template)
    ]
    components_to_place.extend((3, template) for _ in range(n_matches))
    components_to_place.extend((3, shape) for shape in distractors)

    slots = _slot_origins(height, width)
    layout_rng = ctx.draw_rng("slot_layout")
    layout_rng.shuffle(slots)
    grid = full_grid(height, width, 0)
    for index, ((color, shape), slot) in enumerate(
        zip(
            components_to_place,
            slots[: len(components_to_place)],
            strict=True,
        )
    ):
        _paint_in_slot(
            grid,
            shape,
            color,
            slot,
            ctx.draw_rng(f"object_offset_{index}"),
        )

    # This should be unreachable; retaining the assertion turns any future
    # constructive regression into a loud failure instead of poisoned data.
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generation violated its contract: {errors}")
    return grid


def _analyze(grid: Sequence[Sequence[int]]) -> dict:
    templates = _components(grid, 1)
    greens = _components(grid, 3)
    if len(templates) != 1:
        raise ValueError(f"expected one color-1 component, found {len(templates)}")
    target = _normalize(templates[0])
    green_shapes = [_normalize(component) for component in greens]
    return {
        "template_component": templates[0],
        "template": target,
        "green_components": greens,
        "green_shapes": green_shapes,
        "n_matches": green_shapes.count(target),
        "n_distractors": len(green_shapes) - green_shapes.count(target),
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact axis from returned pixels, never RNG bookkeeping."""
    analysis = _analyze(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_matches": analysis["n_matches"],
        "n_distractors": analysis["n_distractors"],
        "shape_size": len(analysis["template"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full lawful input manifold while accepting canonical rows."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 1, 3) for row in grid for value in row):
        return ["cells must be integer colors from {0,1,3}"]

    height = len(grid)
    errors: list[str] = []
    if not 10 <= height <= 14:
        errors.append(f"grid_h={height} outside [10,14]")
    if not 12 <= width <= 16:
        errors.append(f"grid_w={width} outside [12,16]")

    templates = _components(grid, 1)
    if len(templates) != 1:
        errors.append(f"expected exactly one color-1 component, found {len(templates)}")
        return errors

    template = _normalize(templates[0])
    if not 3 <= len(template) <= 5:
        errors.append(f"template has {len(template)} cells, expected 3..5")
    if template:
        template_h = max(row for row, _ in template) + 1
        template_w = max(col for _, col in template) + 1
        if template_h > 3 or template_w > 3:
            errors.append("template bounding box exceeds 3x3")
        if not _connected(template):
            errors.append("template is not four-neighbor connected")
        if template == _mirror(template):
            errors.append("template is horizontally symmetric")

    greens = _components(grid, 3)
    green_shapes = [_normalize(component) for component in greens]
    for index, shape in enumerate(green_shapes):
        if not 3 <= len(shape) <= 5:
            errors.append(f"green component {index} has {len(shape)} cells, expected 3..5")
            continue
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        if shape_h > 3 or shape_w > 3:
            errors.append(f"green component {index} bounding box exceeds 3x3")
        if not _connected(shape):
            errors.append(f"green component {index} is not four-neighbor connected")

    n_matches = green_shapes.count(template)
    n_distractors = len(green_shapes) - n_matches
    if not 1 <= n_matches <= 3:
        errors.append(f"found {n_matches} matching green components, expected 1..3")
    if not 0 <= n_distractors <= 2:
        errors.append(f"found {n_distractors} nonmatching green components, expected 0..2")
    return errors


def strict_canonical_like(grid):
    """Lawful instance of this task's declared manifold."""
    return self_check(grid)


def _blank_like(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in grid]


def _paint_component_and_reflection(
    output: list[list[int]], component: Sequence[tuple[int, int]]
) -> None:
    left = min(col for _, col in component)
    right = max(col for _, col in component)
    for row, col in component:
        output[row][col] = 8
        output[row][left + right - col] = 8


def rule_mirror(grid):
    """Pure Python semantic mirror; selected Racket remains label authority."""
    analysis = _analyze(grid)
    output = _blank_like(grid)
    for component, shape in zip(
        analysis["green_components"], analysis["green_shapes"], strict=True
    ):
        if shape == analysis["template"]:
            _paint_component_and_reflection(output, component)
    return output


def _rival_match_up_to_lr_reflection(grid):
    """Wrong rule: accepts a reflected template as though it were an exact copy."""
    analysis = _analyze(grid)
    target_orbit = {analysis["template"], _mirror(analysis["template"])}
    output = _blank_like(grid)
    for component, shape in zip(
        analysis["green_components"], analysis["green_shapes"], strict=True
    ):
        if shape in target_orbit:
            _paint_component_and_reflection(output, component)
    return output


def _rival_copy_matches_without_completion(grid):
    """Wrong rule: selects exact copies correctly but omits mirror completion."""
    analysis = _analyze(grid)
    output = _blank_like(grid)
    for component, shape in zip(
        analysis["green_components"], analysis["green_shapes"], strict=True
    ):
        if shape == analysis["template"]:
            for row, col in component:
                output[row][col] = 8
    return output


def _rival_complete_every_green(grid):
    """Wrong rule: mirror-completes distractors instead of erasing them."""
    analysis = _analyze(grid)
    output = _blank_like(grid)
    for component in analysis["green_components"]:
        _paint_component_and_reflection(output, component)
    return output


def _has_lr_mirror_distractor(grid) -> bool:
    analysis = _analyze(grid)
    target = analysis["template"]
    reflected = _mirror(target)
    return reflected != target and reflected in analysis["green_shapes"]


def _has_asymmetric_template(grid) -> bool:
    analysis = _analyze(grid)
    return analysis["template"] != _mirror(analysis["template"])


SEMANTIC_WITNESSES = {
    "lr_mirror_distractor": _has_lr_mirror_distractor,
    "asymmetric_template": _has_asymmetric_template,
}
SEMANTIC_RIVALS = {
    "match_up_to_lr_reflection": _rival_match_up_to_lr_reflection,
    "copy_matches_without_completion": _rival_copy_matches_without_completion,
    "complete_every_green": _rival_complete_every_green,
}
WITNESS_RIVALS = {
    "lr_mirror_distractor": [
        "match_up_to_lr_reflection",
        "complete_every_green",
    ],
    "asymmetric_template": ["copy_matches_without_completion"],
}
CANONICAL_SHORTCUTS = {
    "match_up_to_lr_reflection": _rival_match_up_to_lr_reflection,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named plausible wrong rule survives all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the declared rule")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the declared rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competing rule '{name}' fits every demo but changes the query answer"
                )
    return reasons
