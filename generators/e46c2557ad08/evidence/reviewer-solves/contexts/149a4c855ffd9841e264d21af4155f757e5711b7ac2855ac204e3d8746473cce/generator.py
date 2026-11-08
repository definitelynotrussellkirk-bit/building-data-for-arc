"""Generator for Horizontal Gray Dominoes (task e46c2557ad08).

The input contains separated gray components.  Exactly-horizontal 1x2 gray
components are the targets; the unchanged Racket authority recolors those cyan.
Vertical dominoes, longer horizontal bars, vertical bars, and 2x2 blocks are
lawful distractors and remain gray.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e46c2557ad08"
TASK_ID = GENERATOR_ID
RULE_HASH = "bba257d19e2b"
VERSION = "2.0.0"
SUMMARY = (
    "Recolor each gray horizontal 1x2 connected component cyan; vertical "
    "dominoes and larger gray components remain gray."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and every foreground cell is gray (5)",
    "gray components are separated under 4-connectivity",
    "at least one component is exactly a horizontal 1x2 domino",
    "at least one non-target gray component supplies contrast",
    "ordinary generated inputs include both a vertical domino and a longer horizontal bar",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10x11 anchor every fifth sample; otherwise weighted by difficulty",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "10x11 anchor every fifth sample; otherwise weighted by difficulty",
        "valid": "11..16",
    },
    "domino_count": {
        "type": "int",
        "default": "1..6, weighted upward with difficulty",
        "valid": "1..6",
    },
    "distractor_count": {
        "type": "int",
        "default": "2..4, weighted upward with difficulty",
        "valid": "2..4",
    },
}

# The constructive placer realizes every declared cross-product, including the
# smallest 10x11 canvas with six targets and four distractors.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, str]] = []

_H_DOMINO = ((0, 0), (0, 1))
_V_DOMINO = ((0, 0), (1, 0))
_H_TRIO = ((0, 0), (0, 1), (0, 2))
_V_TRIO = ((0, 0), (1, 0), (2, 0))
_H_QUAD = ((0, 0), (0, 1), (0, 2), (0, 3))
_BLOCK_2X2 = ((0, 0), (0, 1), (1, 0), (1, 1))
_EXTRA_DISTRACTORS = (_V_TRIO, _H_QUAD, _BLOCK_2X2)
_ALLOWED_SHAPES = frozenset(
    frozenset(shape)
    for shape in (_H_DOMINO, _V_DOMINO, _H_TRIO, _V_TRIO, _H_QUAD, _BLOCK_2X2)
)
_DIFFICULTIES = (None, "easy", "medium", "hard")
_PROFILE_PERIOD = 5


def _draw_axis(
    ctx,
    name: str,
    lo: int,
    hi: int,
    *,
    overrides: dict,
    preferred: tuple[int, ...],
    anchor: int | None = None,
    force_anchor: bool = False,
) -> int:
    """Draw a weighted integer while keeping the full exact override domain."""
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if force_anchor:
        if anchor is None:
            raise ValueError(f"{name} has no anchor")
        return ctx.draw_choice(name, (anchor,))
    choices = list(range(lo, hi + 1))
    choices.extend(preferred * 5)
    return ctx.draw_choice(name, choices)


@lru_cache(maxsize=256)
def _candidate_cells(
    height: int, width: int, shape: tuple[tuple[int, int], ...]
) -> tuple[tuple[tuple[int, int], ...], ...]:
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(column for _, column in shape) + 1
    return tuple(
        tuple((top + row, left + column) for row, column in shape)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
    )


def _touches_existing(
    cells: tuple[tuple[int, int], ...], occupied: set[tuple[int, int]]
) -> bool:
    for row, column in cells:
        if any(
            point in occupied
            for point in (
                (row, column),
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            )
        ):
            return True
    return False


def _place_components(ctx, height: int, width: int, targets: int, distractors: int):
    rng = ctx.draw_rng("layout")
    shapes: list[tuple[tuple[int, int], ...]] = [_H_DOMINO] * targets
    # Every generated example directly distinguishes orientation and exact length.
    shapes.extend((_V_DOMINO, _H_TRIO))
    shapes.extend(rng.choice(_EXTRA_DISTRACTORS) for _ in range(distractors - 2))

    for _attempt in range(96):
        # Larger objects first; random keys diversify equal-sized placements.
        ordered = [(rng.random(), index, shape) for index, shape in enumerate(shapes)]
        ordered.sort(key=lambda item: (-len(item[2]), item[0]))
        occupied: set[tuple[int, int]] = set()
        placed: dict[int, tuple[tuple[int, int], ...]] = {}

        for _tie, index, shape in ordered:
            candidates = list(_candidate_cells(height, width, shape))
            rng.shuffle(candidates)
            chosen = next(
                (cells for cells in candidates if not _touches_existing(cells, occupied)),
                None,
            )
            if chosen is None:
                break
            placed[index] = chosen
            occupied.update(chosen)
        else:
            grid = full_grid(height, width, 0)
            for cells in placed.values():
                for row, column in cells:
                    grid[row][column] = 5
            return grid

    raise ValueError(
        "could not realize requested separated components; "
        "this is an implementation defect for a declared-compatible override tuple"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be a Python int, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    band = "medium" if difficulty is None else difficulty
    preferences = {
        "easy": {
            "grid_h": (10, 10, 11),
            "grid_w": (11, 11, 12),
            "domino_count": (1, 1, 2),
            "distractor_count": (2, 2),
        },
        "medium": {
            "grid_h": (10, 11, 12),
            "grid_w": (11, 12, 13, 14),
            "domino_count": (2, 3, 4),
            "distractor_count": (2, 3),
        },
        "hard": {
            "grid_h": (12, 13, 14),
            "grid_w": (14, 15, 16),
            "domino_count": (4, 5, 6),
            "distractor_count": (3, 4),
        },
    }[band]

    anchor_slot = sample_index % _PROFILE_PERIOD == 0
    height = _draw_axis(
        ctx,
        "grid_h",
        10,
        14,
        overrides=overrides,
        preferred=preferences["grid_h"],
        anchor=10,
        force_anchor=anchor_slot and overrides.get("grid_h") is None,
    )
    width = _draw_axis(
        ctx,
        "grid_w",
        11,
        16,
        overrides=overrides,
        preferred=preferences["grid_w"],
        anchor=11,
        force_anchor=anchor_slot and overrides.get("grid_w") is None,
    )
    domino_count = _draw_axis(
        ctx,
        "domino_count",
        1,
        6,
        overrides=overrides,
        preferred=preferences["domino_count"],
    )
    distractor_count = _draw_axis(
        ctx,
        "distractor_count",
        2,
        4,
        overrides=overrides,
        preferred=preferences["distractor_count"],
    )
    return _place_components(ctx, height, width, domino_count, distractor_count)


def _components(grid, color: int = 5) -> list[set[tuple[int, int]]]:
    remaining = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == color
    }
    found: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        todo = [start]
        component = {start}
        while todo:
            row, column = todo.pop()
            for point in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    todo.append(point)
        found.append(component)
    return found


def _normalized(component: set[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    top = min(row for row, _ in component)
    left = min(column for _, column in component)
    return frozenset((row - top, column - left) for row, column in component)


def _is_horizontal_domino(component: set[tuple[int, int]]) -> bool:
    return _normalized(component) == frozenset(_H_DOMINO)


def _is_vertical_domino(component: set[tuple[int, int]]) -> bool:
    return _normalized(component) == frozenset(_V_DOMINO)


def _is_long_horizontal(component: set[tuple[int, int]]) -> bool:
    return len({row for row, _ in component}) == 1 and len(component) >= 3


def _paint_selected(grid, predicate) -> list[list[int]]:
    output = [list(row) for row in grid]
    for component in _components(grid):
        if predicate(component):
            for row, column in component:
                output[row][column] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket authority."""
    return _paint_selected(grid, _is_horizontal_domino)


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    components = _components(grid)
    targets = sum(_is_horizontal_domino(component) for component in components)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "domino_count": targets,
        "distractor_count": len(components) - targets,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if not 8 <= len(grid) <= 14 or not 9 <= width <= 16:
        return [f"grid shape {len(grid)}x{width} outside supported task envelope"]
    if any(type(value) is not int or value not in (0, 5) for row in grid for value in row):
        return ["input cells must be integer colors 0 or 5"]

    components = _components(grid)
    errors: list[str] = []
    if not components:
        return ["expected gray components"]
    for index, component in enumerate(components):
        normalized = _normalized(component)
        if normalized not in _ALLOWED_SHAPES:
            errors.append(
                f"component {index} has unsupported normalized shape {sorted(normalized)}"
            )
    targets = sum(_is_horizontal_domino(component) for component in components)
    if targets < 1:
        errors.append("expected at least one horizontal gray domino")
    if len(components) - targets < 1:
        errors.append("expected at least one non-target gray distractor")
    return errors


def strict_canonical_like(grid):
    """Return per-task input-domain findings; an empty list means lawful."""
    return self_check(grid)


def _rival_all_dominoes(grid) -> list[list[int]]:
    """Wrong rule: recolor both horizontal and vertical two-cell components."""
    return _paint_selected(grid, lambda component: len(component) == 2)


def _rival_all_horizontal_lines(grid) -> list[list[int]]:
    """Wrong rule: recolor every horizontal gray line, even length three or four."""
    return _paint_selected(
        grid,
        lambda component: len({row for row, _ in component}) == 1
        and len(component) >= 2,
    )


def _has_vertical_domino(grid) -> bool:
    return not self_check(grid) and any(
        _is_vertical_domino(component) for component in _components(grid)
    )


def _has_long_horizontal(grid) -> bool:
    return not self_check(grid) and any(
        _is_long_horizontal(component) for component in _components(grid)
    )


SEMANTIC_WITNESSES = {
    "orientation_matters": _has_vertical_domino,
    "exact_length_matters": _has_long_horizontal,
}
SEMANTIC_RIVALS = {
    "all_dominoes": _rival_all_dominoes,
    "all_horizontal_lines": _rival_all_horizontal_lines,
}
WITNESS_RIVALS = {
    "orientation_matters": ["all_dominoes"],
    "exact_length_matters": ["all_horizontal_lines"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demonstrations, query) -> list[str]:
    """Report declared rivals not refuted by the visible demonstrations."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demonstrations
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            reasons.append(f"{name} failed: {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"declared rival {name!r} fits every demonstration")
    return reasons
