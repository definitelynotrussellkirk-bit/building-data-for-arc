"""Generator for ARC task 85de426e8683 — recolor diagonal-object centers.

The rule acts on *whole* gray(5) 8-connected objects: an object is a target
only when it consists of exactly three cells arranged on a 45-degree diagonal.
Only the middle cell of each such object becomes yellow(4).

The lesson schedule deliberately includes larger gray objects that contain a
three-cell diagonal run.  Those are not targets because the complete object is
larger than three cells.  This component-scope witness is the central ambiguity
in the canonical examples and was absent from the imported generator.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85de426e8683"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "810181a298c8"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Recolor the middle cell of every whole gray(5) 8-connected object that "
    "is exactly a three-cell diagonal; larger gray near-misses and unrelated "
    "colored distractors remain unchanged."
)

INVARIANTS = [
    "background color 0 is present",
    "every target is a whole color-5 8-connected component of exactly three diagonal cells",
    "both diagonal slopes occur in every four-example lesson",
    "ordinary lessons contain a larger color-5 object with an embedded diagonal run that must remain unchanged",
    "non-gray distractors may include the output color 4 and remain unchanged",
]

SCENE_PROFILES = (
    "canonical_clean",
    "long_diagonal_decoy",
    "branched_decoy",
    "axis_decoys",
)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded deterministic draw",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded deterministic draw",
        "valid": "9..11",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-profile cyclic curriculum",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_MAIN = ((0, 0), (1, 1), (2, 2))
_ANTI = ((0, 2), (1, 1), (2, 0))
_LONG_MAIN = tuple((i, i) for i in range(5))
_LONG_ANTI = tuple((i, 4 - i) for i in range(5))
# Two overlapping diagonal runs inside one five-cell object, matching the
# canonical task's decisive "larger object" counterexample family.
_BRANCH = ((0, 3), (1, 0), (1, 2), (2, 1), (3, 2))
_ROW3 = ((0, 0), (0, 1), (0, 2))
_COL3 = ((0, 0), (1, 0), (2, 0))
_TARGET_SHAPES = {_MAIN, _ANTI}
_LONG_SHAPES = {_LONG_MAIN, _LONG_ANTI}
_AXIS_SHAPES = {_ROW3, _COL3}
_ALLOWED_OVERRIDES = frozenset(AXES)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the cyclic curriculum slot; every four starts cover all slots."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _grid_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"], 0, 0
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"], len(grid), 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["all cells must be literal ARC integers 0..9"], h, w
    return [], h, w


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _components8_of_color(
    grid: Sequence[Sequence[int]], color: int
) -> list[tuple[tuple[int, int], ...]]:
    """Return same-color 8-connected components without traversing background."""
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components: list[tuple[tuple[int, int], ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIRS8:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    component.append(neighbor)
        components.append(tuple(sorted(component)))
    return components


def _is_target_component(cells: Iterable[tuple[int, int]]) -> bool:
    return _normalize(cells) in _TARGET_SHAPES


def _classify_profile(
    targets: Sequence[tuple[tuple[int, int], ...]],
    decoys: Sequence[tuple[tuple[int, int], ...]],
) -> str | None:
    shapes = sorted(_normalize(component) for component in decoys)
    if not shapes and len(targets) == 2:
        return "canonical_clean"
    if len(shapes) == 1 and shapes[0] in _LONG_SHAPES and len(targets) == 1:
        return "long_diagonal_decoy"
    if shapes == [_BRANCH] and len(targets) == 2:
        return "branched_decoy"
    if shapes == sorted(_AXIS_SHAPES) and len(targets) == 2:
        return "axis_decoys"
    return None


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors, h, w = _grid_errors(grid)
    if errors:
        return {"errors": errors, "grid_h": h, "grid_w": w}
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")

    gray_components = _components8_of_color(grid, 5)
    targets = [component for component in gray_components if _is_target_component(component)]
    decoys = [component for component in gray_components if not _is_target_component(component)]
    if not targets:
        errors.append("need at least one exact three-cell diagonal color-5 component")

    slopes = {
        "main" if _normalize(component) == _MAIN else "anti"
        for component in targets
    }
    non_gray_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "gray_components": gray_components,
        "targets": targets,
        "decoys": decoys,
        "slopes": slopes,
        "non_gray_cells": non_gray_cells,
        "scene_profile": _classify_profile(targets, decoys),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical gray decoys while requiring at least one real target."""
    del difficulty, meta
    return list(_analyze_scene(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover each declared exact axis from a generated scene."""
    facts = _analyze_scene(grid)
    if facts["errors"] or facts.get("scene_profile") is None:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "scene_profile": facts["scene_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Broad empirical manifold containing every published canonical input."""
    facts = _analyze_scene(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if not (8 <= facts["grid_h"] <= 10 and 9 <= facts["grid_w"] <= 11):
        reasons.append("canonical-linked scenes use heights 8..10 and widths 9..11")
    if not (1 <= len(facts["targets"]) <= 2):
        reasons.append("canonical-linked scenes contain one or two targets")
    if len(facts["decoys"]) > 1:
        reasons.append("canonical-linked scenes contain at most one gray decoy object")
    if facts["decoys"] and len(facts["decoys"][0]) not in (5, 6):
        reasons.append("canonical gray decoys have five or six cells")
    colors = {value for _, _, value in facts["non_gray_cells"]}
    if len(colors) != 1 or not (1 <= len(facts["non_gray_cells"]) <= 2):
        reasons.append("canonical inputs contain one unrelated color in one or two cells")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror used only for tests and named-rival diagnostics."""
    errors, _, _ = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in grid]
    for component in _components8_of_color(grid, 5):
        if _is_target_component(component):
            r, c = sorted(component)[1]
            output[r][c] = 4
    return output


def _motifs_for_profile(profile: str, rng) -> list[tuple[str, int, tuple[tuple[int, int], ...]]]:
    if profile == "canonical_clean":
        gray = [("target_main", 5, _MAIN), ("target_anti", 5, _ANTI)]
        distractor_color = rng.choice((2, 6, 7))
    elif profile == "long_diagonal_decoy":
        target = _MAIN if rng.choice((False, True)) else _ANTI
        long_shape = _LONG_MAIN if rng.choice((False, True)) else _LONG_ANTI
        gray = [("target", 5, target), ("long_decoy", 5, long_shape)]
        distractor_color = rng.choice((1, 2, 6, 7))
    elif profile == "branched_decoy":
        gray = [
            ("target_main", 5, _MAIN),
            ("target_anti", 5, _ANTI),
            ("branch_decoy", 5, _BRANCH),
        ]
        distractor_color = rng.choice((2, 6, 7, 9))
    elif profile == "axis_decoys":
        gray = [
            ("target_main", 5, _MAIN),
            ("target_anti", 5, _ANTI),
            ("row_decoy", 5, _ROW3),
            ("col_decoy", 5, _COL3),
        ]
        distractor_color = 4
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    return gray + [("colored_distractor", distractor_color, ((0, 0),))]


def _candidate_origins(
    h: int, w: int, offsets: Sequence[tuple[int, int]], rng
) -> list[tuple[int, int]]:
    height = max(r for r, _ in offsets) + 1
    width = max(c for _, c in offsets) + 1
    candidates = [
        (r0, c0)
        for r0 in range(h - height + 1)
        for c0 in range(w - width + 1)
    ]
    rng.shuffle(candidates)
    return candidates


def _place_motifs(
    h: int,
    w: int,
    motifs: Sequence[tuple[str, int, tuple[tuple[int, int], ...]]],
    rng,
) -> list[tuple[str, int, tuple[tuple[int, int], ...]]]:
    """Backtrack over translations, keeping all objects one cell apart."""
    ordered = sorted(
        motifs,
        key=lambda item: (
            -(max(r for r, _ in item[2]) + 1) * (max(c for _, c in item[2]) + 1),
            -len(item[2]),
            item[0],
        ),
    )
    candidates = {
        name: _candidate_origins(h, w, offsets, rng)
        for name, _, offsets in ordered
    }
    placed: list[tuple[str, int, tuple[tuple[int, int], ...]]] = []
    occupied: set[tuple[int, int]] = set()

    def recurse(index: int) -> bool:
        if index == len(ordered):
            return True
        name, color, offsets = ordered[index]
        for r0, c0 in candidates[name]:
            cells = tuple((r0 + r, c0 + c) for r, c in offsets)
            if any(
                abs(r - rr) <= 1 and abs(c - cc) <= 1
                for r, c in cells
                for rr, cc in occupied
            ):
                continue
            placed.append((name, color, cells))
            occupied.update(cells)
            if recurse(index + 1):
                return True
            for cell in cells:
                occupied.remove(cell)
            placed.pop()
        return False

    if not recurse(0):
        raise RuntimeError(f"could not place profile motifs in {h}x{w}")
    return placed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "scene_profile", schedule_profile(seed, sample_index, difficulty)
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    h = ctx.draw_int_diff("grid_h", 8, 10)
    w = ctx.draw_int_diff("grid_w", 9, 11)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    rng = ctx.draw_rng("layout")

    motifs = _motifs_for_profile(profile, rng)
    placements = _place_motifs(h, w, motifs, rng)
    grid = full_grid(h, w, 0)
    for _, color, cells in placements:
        for r, c in cells:
            grid[r][c] = color

    facts = _analyze_scene(grid)
    if facts["errors"] or facts["scene_profile"] != profile:
        raise RuntimeError(
            f"generated invalid {profile} scene: errors={facts['errors']} "
            f"observed={facts.get('scene_profile')}"
        )
    return grid


def _rival_any_diagonal_window(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: recolor every local gray 3-run, ignoring whole components."""
    output = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 5:
                continue
            if (
                grid[r - 1][c - 1] == 5 == grid[r + 1][c + 1]
                or grid[r - 1][c + 1] == 5 == grid[r + 1][c - 1]
            ):
                output[r][c] = 4
    return output


def _rival_one_slope(grid: list[list[int]], shape) -> list[list[int]]:
    output = [row[:] for row in grid]
    for component in _components8_of_color(grid, 5):
        if _normalize(component) == shape:
            r, c = sorted(component)[1]
            output[r][c] = 4
    return output


def _rival_first_target_only(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    targets = [
        component
        for component in _components8_of_color(grid, 5)
        if _is_target_component(component)
    ]
    if targets:
        r, c = sorted(targets[0])[1]
        output[r][c] = 4
    return output


LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "local_diagonal_window_ignores_component_size": _rival_any_diagonal_window,
    "main_slope_only": lambda grid: _rival_one_slope(grid, _MAIN),
    "anti_slope_only": lambda grid: _rival_one_slope(grid, _ANTI),
    "first_target_only": _rival_first_target_only,
}


def lesson_identifiable(demos, query=None) -> list[str]:
    """Require the visible demonstrations to refute every named shortcut."""
    del query
    errors: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(item["input"]) == item["output"] for item in demos):
            errors.append(f"lesson does not refute competitor {name}")
    return errors
