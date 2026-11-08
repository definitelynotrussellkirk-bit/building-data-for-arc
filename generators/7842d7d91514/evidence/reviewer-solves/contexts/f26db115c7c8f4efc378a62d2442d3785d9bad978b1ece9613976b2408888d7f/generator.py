"""Constructive generator for ARC task 7842d7d91514.

Rule
----
The lone color-5 component is a shape template.  Every color-2 candidate whose
translation-normalized cropped shape is exactly equal to the template (same
orientation; rotations and reflections do not count) is recolored 4.  Every
other color-2 component is recolored 1.  The background and template stay put.

Generated instances use isolated 3x3 slots.  They always include both rule
branches and a same-size rotated/reflected near miss, so position, cell count,
and dihedral-congruence shortcuts cannot explain a lesson.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7842d7d91514"
TASK_ID = "7842d7d91514"
VERSION = "2.0.0"
RULE_HASH = "9d86bc23e927"

SUMMARY = (
    "An 11..14 by 12..16 zero grid contains one connected 3..5-cell color-5 "
    "template, one or two exact translated color-2 copies, and one or two "
    "same-size color-2 distractors.  At least one distractor is a nonidentical "
    "rotation or reflection of the template.  Exact same-orientation copies "
    "become color 4; all other candidates become color 1; the template remains 5."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and the input palette is exactly {0,2,5}",
    "there is exactly one connected 3..5-cell color-5 template in a 3x3 box",
    "there are 1..2 exact translated color-2 copies and 1..2 nonmatches",
    "every generated candidate has the template's cell count",
    "at least one generated nonmatch is a distinct dihedral image of the template",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted choice over 11..14",
        "valid": "11..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted choice over 12..16",
        "valid": "12..16",
    },
    "n_matches": {
        "type": "int",
        "default": "difficulty-weighted choice over 1..2",
        "valid": "1..2",
    },
    "n_distractors": {
        "type": "int",
        "default": "difficulty-weighted choice over 1..2",
        "valid": "1..2",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-weighted choice over 3..5",
        "valid": "3..5",
    },
}

# Five objects at the largest request fit in six mutually isolated slots, so
# every Cartesian product in AXES is constructively realizable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

_AXIS_BOUNDS = {
    "grid_h": (11, 14),
    "grid_w": (12, 16),
    "n_matches": (1, 2),
    "n_distractors": (1, 2),
    "shape_size": (3, 5),
}
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


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


def _rotate_90(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(shape)
    if not normalized:
        return ()
    height = max(row for row, _ in normalized) + 1
    return _normalize((col, height - 1 - row) for row, col in normalized)


def _reflect_lr(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(shape)
    if not normalized:
        return ()
    width = max(col for _, col in normalized) + 1
    return _normalize((row, width - 1 - col) for row, col in normalized)


def _dihedral_orbit(
    shape: Iterable[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    current = _normalize(shape)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect_lr(current))
        current = _rotate_90(current)
    return tuple(sorted(variants))


def _build_shape_bank() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """All connected 3x3 polyominoes with a nontrivial dihedral orbit."""
    cells = tuple((row, col) for row in range(3) for col in range(3))
    bank: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(3, 6):
        shapes = {
            _normalize(candidate)
            for candidate in combinations(cells, size)
            if _connected(candidate)
        }
        usable = tuple(sorted(shape for shape in shapes if len(_dihedral_orbit(shape)) > 1))
        if len(usable) < 4:
            raise RuntimeError(f"shape bank for size {size} is unexpectedly small")
        bank[size] = usable
    return bank


_SHAPES = _build_shape_bank()


def _components(
    grid: Sequence[Sequence[int]], color: int
) -> list[list[tuple[int, int]]]:
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
    """Full-domain weighted choices; every override remains legal in every band."""
    if axis == "grid_h":
        if difficulty == "easy":
            return (11, 11, 11, 12, 12, 12, 13, 14)
        if difficulty == "hard":
            return (11, 12, 12, 12, 13, 13, 14, 14)
        return (11, 11, 12, 12, 12, 13, 14)
    if axis == "grid_w":
        if difficulty == "easy":
            return (12, 12, 12, 13, 13, 14, 15, 16)
        if difficulty == "hard":
            return (12, 13, 13, 13, 14, 15, 16)
        return (12, 12, 13, 13, 13, 14, 15, 16)
    if axis == "n_matches":
        return (1, 1, 1, 2) if difficulty == "easy" else (1, 1, 2, 2)
    if axis == "n_distractors":
        return (1, 1, 1, 2) if difficulty == "easy" else (1, 1, 2, 2)
    if axis == "shape_size":
        if difficulty == "easy":
            return (3, 3, 3, 4, 4, 5)
        if difficulty == "hard":
            return (3, 4, 4, 5, 5, 5)
        return (3, 3, 4, 4, 5)
    raise KeyError(axis)


def _validate_public_controls(seed, sample_index, difficulty, overrides: dict) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _slot_origins(height: int, width: int) -> list[tuple[int, int]]:
    """Six mutually four-neighbor-isolated 3x3 boxes."""
    rows = (0, height - 3)
    cols = (0, (width - 3) // 2, width - 3)
    slots = [(row, col) for row in rows for col in cols]
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
    base_row = slot[0] + rng.randint(0, 3 - shape_h)
    base_col = slot[1] + rng.randint(0, 3 - shape_w)
    for row, col in normalized:
        rr, cc = base_row + row, base_col + col
        if grid[rr][cc] != 0:
            raise RuntimeError("constructive slot overlap")
        grid[rr][cc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_public_controls(seed, sample_index, difficulty, overrides)
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
    n_distractors = ctx.draw_choice(
        "n_distractors", _weighted_options("n_distractors", difficulty)
    )
    shape_size = ctx.draw_choice("shape_size", _weighted_options("shape_size", difficulty))

    template = ctx.draw_rng("template_shape").choice(_SHAPES[shape_size])
    transformed = [shape for shape in _dihedral_orbit(template) if shape != template]
    if not transformed:
        raise RuntimeError("template unexpectedly has no distinct dihedral image")

    distractors = [ctx.draw_rng("dihedral_distractor").choice(transformed)]
    if n_distractors == 2:
        outside_orbit = [
            shape
            for shape in _SHAPES[shape_size]
            if shape != template and shape not in _dihedral_orbit(template)
        ]
        alternatives = outside_orbit or [
            shape
            for shape in _SHAPES[shape_size]
            if shape not in (template, distractors[0])
        ]
        if not alternatives:
            raise RuntimeError("no second nonmatching shape is available")
        distractors.append(ctx.draw_rng("second_distractor_shape").choice(alternatives))

    items_to_place: list[tuple[int, tuple[tuple[int, int], ...]]] = [(5, template)]
    items_to_place.extend((2, template) for _ in range(n_matches))
    items_to_place.extend((2, shape) for shape in distractors)

    slots = _slot_origins(height, width)
    ctx.draw_rng("slot_layout").shuffle(slots)
    grid = full_grid(height, width, 0)
    for index, ((color, shape), slot) in enumerate(
        zip(items_to_place, slots[: len(items_to_place)], strict=True)
    ):
        _paint_in_slot(
            grid,
            shape,
            color,
            slot,
            ctx.draw_rng(f"object_offset_{index}"),
        )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generation violated its contract: {errors}")
    return grid


def _shape_errors(shape, role: str) -> list[str]:
    errors: list[str] = []
    normalized = _normalize(shape)
    if not 3 <= len(normalized) <= 5:
        errors.append(f"{role} has {len(normalized)} cells, expected 3..5")
        return errors
    shape_h = max(row for row, _ in normalized) + 1
    shape_w = max(col for _, col in normalized) + 1
    if shape_h > 3 or shape_w > 3:
        errors.append(f"{role} bounding box exceeds 3x3")
    if not _connected(normalized):
        errors.append(f"{role} is not four-neighbor connected")
    return errors


def _analyze(grid: Sequence[Sequence[int]]) -> dict:
    templates = _components(grid, 5)
    candidates = _components(grid, 2)
    if len(templates) != 1:
        raise ValueError(f"expected one color-5 component, found {len(templates)}")
    template = _normalize(templates[0])
    candidate_shapes = [_normalize(component) for component in candidates]
    return {
        "template_component": templates[0],
        "template": template,
        "candidate_components": candidates,
        "candidate_shapes": candidate_shapes,
        "n_matches": candidate_shapes.count(template),
        "n_distractors": len(candidate_shapes) - candidate_shapes.count(template),
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised axis from pixels, never RNG bookkeeping."""
    analysis = _analyze(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_matches": analysis["n_matches"],
        "n_distractors": analysis["n_distractors"],
        "shape_size": len(analysis["template"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful task manifold while accepting every canonical input."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 2, 5) for row in grid for value in row):
        return ["cells must be integer colors from {0,2,5}"]

    height = len(grid)
    errors: list[str] = []
    if not 11 <= height <= 14:
        errors.append(f"grid_h={height} outside [11,14]")
    if not 12 <= width <= 16:
        errors.append(f"grid_w={width} outside [12,16]")

    templates = _components(grid, 5)
    if len(templates) != 1:
        errors.append(f"expected exactly one color-5 component, found {len(templates)}")
        return errors
    template = _normalize(templates[0])
    errors.extend(_shape_errors(template, "template"))

    candidates = _components(grid, 2)
    if not 2 <= len(candidates) <= 4:
        errors.append(f"found {len(candidates)} color-2 candidates, expected 2..4")
    candidate_shapes = []
    for index, component in enumerate(candidates):
        shape = _normalize(component)
        candidate_shapes.append(shape)
        errors.extend(_shape_errors(shape, f"candidate {index}"))

    n_matches = candidate_shapes.count(template)
    n_distractors = len(candidate_shapes) - n_matches
    if not 1 <= n_matches <= 2:
        errors.append(f"found {n_matches} exact matches, expected 1..2")
    if not 1 <= n_distractors <= 2:
        errors.append(f"found {n_distractors} nonmatches, expected 1..2")
    return errors


def strict_canonical_like(grid):
    """Lawful instance of the selected canonical task manifold."""
    return self_check(grid)


def _recolor_candidates(grid, predicate) -> list[list[int]]:
    analysis = _analyze(grid)
    output = [list(row) for row in grid]
    for component, shape in zip(
        analysis["candidate_components"], analysis["candidate_shapes"], strict=True
    ):
        color = 4 if predicate(shape, analysis["template"]) else 1
        for row, col in component:
            output[row][col] = color
    return output


def rule_match(grid):
    """Independent Python semantic mirror; selected Racket remains authority."""
    return _recolor_candidates(grid, lambda shape, template: shape == template)


def _rival_match_up_to_dihedral(grid):
    """Wrong rule: treats rotations and reflections as exact template matches."""
    return _recolor_candidates(
        grid, lambda shape, template: shape in _dihedral_orbit(template)
    )


def _rival_match_by_cell_count(grid):
    """Wrong rule: matches every candidate with the template's cell count."""
    return _recolor_candidates(grid, lambda shape, template: len(shape) == len(template))


def _rival_all_candidates_yellow(grid):
    """Wrong rule: recolors every candidate 4."""
    return _recolor_candidates(grid, lambda shape, template: True)


def _rival_all_candidates_blue(grid):
    """Wrong rule: recolors every candidate 1."""
    return _recolor_candidates(grid, lambda shape, template: False)


def _has_same_size_dihedral_distractor(grid) -> bool:
    analysis = _analyze(grid)
    target = analysis["template"]
    orbit = set(_dihedral_orbit(target))
    return any(
        shape != target and len(shape) == len(target) and shape in orbit
        for shape in analysis["candidate_shapes"]
    )


def _has_exact_match(grid) -> bool:
    return _analyze(grid)["n_matches"] > 0


def _has_nonmatch(grid) -> bool:
    return _analyze(grid)["n_distractors"] > 0


SEMANTIC_WITNESSES = {
    "same_size_dihedral_distractor": _has_same_size_dihedral_distractor,
    "exact_match": _has_exact_match,
    "nonmatch": _has_nonmatch,
}
BRANCH_WITNESSES = ("exact_match", "nonmatch")
SEMANTIC_RIVALS = {
    "match_up_to_dihedral": _rival_match_up_to_dihedral,
    "match_by_cell_count": _rival_match_by_cell_count,
    "all_candidates_yellow": _rival_all_candidates_yellow,
    "all_candidates_blue": _rival_all_candidates_blue,
}
WITNESS_RIVALS = {
    "same_size_dihedral_distractor": [
        "match_up_to_dihedral",
        "match_by_cell_count",
        "all_candidates_yellow",
    ],
    "exact_match": ["all_candidates_blue"],
    "nonmatch": ["all_candidates_yellow"],
}
CANONICAL_SHORTCUTS = {
    "match_up_to_dihedral": _rival_match_up_to_dihedral,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared plausible wrong rule survives its demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if rule_match(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the declared rule")
    if rule_match(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the declared rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competing rule '{name}' fits every demo but changes the query answer"
                )
    return reasons
