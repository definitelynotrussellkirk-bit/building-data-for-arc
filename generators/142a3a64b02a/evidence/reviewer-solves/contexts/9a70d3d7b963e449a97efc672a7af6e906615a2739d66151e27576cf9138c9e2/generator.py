"""Generator for ``142a3a64b02a`` — cap whole straight red objects.

The selected Racket rule enumerates 4-connected non-background objects.  A red
(color 2) object is changed only when the *entire component* lies in one row or
one column; its two extrema become yellow (4).  Non-straight red objects are
left untouched.  Every ordinary generated lesson contains both a positive
straight object and a negative non-straight object so that the curriculum
refutes the tempting shortcut "cap every maximal horizontal/vertical run".
"""
from __future__ import annotations

import copy
from collections import Counter, deque
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "142a3a64b02a"
TASK_ID = "142a3a64b02a"
# 3.0.0 restores the held-out whole-component boundary, pins rule authority,
# replaces misleading axes with exact observable controls, and adds an
# executable semantic contract plus task-local regressions.
VERSION = "3.0.0"
RULE_HASH = "ffb5719ce1e2"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Generate a sparse 0-background grid with one isolated straight red (2) "
    "component, one isolated non-straight red tree, and a one- or two-cell "
    "non-red decoy. Recolor only the two extrema of each red component whose "
    "whole 4-connected object is horizontal or vertical; leave every "
    "non-straight red component and every non-red object unchanged. A "
    "three-step schedule cycles T, L, and stair-shaped negative witnesses."
)

INVARIANTS = [
    "0 is the strictly modal background",
    "ordinary draws contain a straight red component of length at least three",
    "ordinary draws contain one isolated non-straight acyclic red component",
    "the non-red decoy uses one additional color and has one or two cells",
    "only whole straight red components receive yellow endpoint caps",
]

SCENE_PROFILES = ("tee", "ell", "stair")
SCHEDULE_PROFILES = SCENE_PROFILES
CANONICAL_SHAPES = ((7, 9), (8, 8), (7, 10), (9, 9), (8, 10))
DECOY_COLORS = (3, 4, 6, 7, 9)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-step canonical-shape schedule",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "five-step canonical-shape schedule",
        "valid": "8..13",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index mod 3 schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# Canonical representatives.  Dihedral variants are generated at placement
# time; observe_overrides recovers the profile modulo translation/rotation/
# reflection from the returned grid itself.
_MOTIFS: dict[str, tuple[tuple[int, int], ...]] = {
    "tee": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "ell": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "stair": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fresh teaching input for the selected rule."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    offset = {None: 1, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    scheduled_h, scheduled_w = CANONICAL_SHAPES[(int(sample_index) + offset) % len(CANONICAL_SHAPES)]
    height = _draw_scheduled_int(ctx, overrides, "grid_h", scheduled_h, 7, 12)
    width = _draw_scheduled_int(ctx, overrides, "grid_w", scheduled_w, 8, 13)

    scheduled_profile = SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]
    profile_options = SCENE_PROFILES if overrides.get("scene_profile") is not None else (scheduled_profile,)
    profile = str(ctx.draw_choice("scene_profile", profile_options))

    layout_rng = ctx.draw_rng("layout")
    decoy_color = int(ctx.draw_choice("decoy_color", DECOY_COLORS))
    grid = _construct_scene(
        height,
        width,
        profile,
        difficulty=difficulty,
        sample_index=int(sample_index),
        rng=layout_rng,
        decoy_color=decoy_color,
    )
    problems = self_check(grid, difficulty=difficulty)
    if problems:
        raise RuntimeError("constructed invalid endpoint lesson: " + "; ".join(problems))
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "scene_profile": profile}
    if observed != expected:
        raise RuntimeError(f"override observer mismatch: expected {expected}, got {observed}")
    if rule_mirror(grid) == grid:
        raise RuntimeError("constructed identity lesson despite a straight red object")
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    """Declared default schedule used by the semantic gate."""
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from an ordinary generated grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    nonstraight = [component for component in _red_components(grid) if not _is_straight(component)]
    if len(nonstraight) != 1:
        raise ValueError(f"expected one non-straight red component, found {len(nonstraight)}")
    signature = _shape_signature(nonstraight[0])
    profile = _PROFILE_BY_SIGNATURE.get(signature)
    if profile is None:
        raise ValueError("non-straight red component is outside the declared profile catalog")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "scene_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical-like input grammar, including the held-out T."""
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    nonzero_counts = [count for value, count in counts.items() if value != 0]
    if counts.get(0, 0) <= max(nonzero_counts, default=0):
        errors.append("background 0 must be strictly modal")

    red_components = _red_components(grid)
    if not red_components:
        errors.append("need at least one red component")
    if len(red_components) > 4:
        errors.append(f"too many red components for the sparse grammar: {len(red_components)}")

    for index, component in enumerate(red_components):
        if _is_straight(component):
            if len(component) < 3:
                errors.append(
                    f"red component {index} is a straight segment shorter than three cells"
                )
            continue
        if len(component) < 4:
            errors.append(f"non-straight red component {index} is too small")
            continue
        edge_count, degrees = _component_graph(component)
        if edge_count != len(component) - 1:
            errors.append(f"non-straight red component {index} must be acyclic")
        if max(degrees, default=0) > 3:
            errors.append(f"non-straight red component {index} branches more than a T")

    decoy_colors = sorted(value for value in counts if value not in (0, 2))
    if len(decoy_colors) != 1:
        errors.append(f"need exactly one non-red decoy color, found {len(decoy_colors)}")
    elif not 1 <= counts[decoy_colors[0]] <= 2:
        errors.append("the non-red decoy must contain one or two cells")
    elif len(_components_of_color(grid, decoy_colors[0])) != 1:
        errors.append("the non-red decoy cells must form one component")

    # Keep diagnostics stable when called with a malformed difficulty hint, but
    # do not make canonical acceptance depend on difficulty.
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be None, 'easy', 'medium', or 'hard'")
    if height < 1 or width < 1:  # unreachable after _grid_errors; documents shape dependency
        errors.append("grid dimensions must be positive")
    return errors


def strict_canonical_like(grid):
    """All ordinary draws and all five canonical inputs lie on this manifold."""
    return self_check(grid)


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; selected Racket remains label authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("invalid input grid: " + "; ".join(errors))
    out = [list(row) for row in grid]
    for component in _red_components(grid):
        if not _is_straight(component):
            continue
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        row0, row1 = min(rows), max(rows)
        col0, col1 = min(cols), max(cols)
        if row0 == row1:
            out[row0][col0] = 4
            out[row0][col1] = 4
        else:
            out[row0][col0] = 4
            out[row1][col0] = 4
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _recolor_each_maximal_run(grid):
    """Wrong rival: cap every maximal red row/column run independently."""
    errors = _grid_errors(grid)
    if errors:
        return []
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        col = 0
        while col < width:
            if grid[row][col] != 2:
                col += 1
                continue
            end = col
            while end + 1 < width and grid[row][end + 1] == 2:
                end += 1
            if end - col + 1 >= 2:
                out[row][col] = 4
                out[row][end] = 4
            col = end + 1
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 2:
                row += 1
                continue
            end = row
            while end + 1 < height and grid[end + 1][col] == 2:
                end += 1
            if end - row + 1 >= 2:
                out[row][col] = 4
                out[end][col] = 4
            row = end + 1
    return out


def _safe_components(grid):
    return [] if _grid_errors(grid) else _red_components(grid)


def _has_straight_change(grid):
    components = _safe_components(grid)
    return bool(components and any(_is_straight(component) for component in components))


def _has_nonstraight_boundary(grid):
    components = _safe_components(grid)
    if not any(not _is_straight(component) for component in components):
        return False
    return _recolor_each_maximal_run(grid) != rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "recolor_each_maximal_run": _recolor_each_maximal_run,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "straight_component_changes": _has_straight_change,
    "whole_nonstraight_component_boundary": _has_nonstraight_boundary,
}
WITNESS_RIVALS = {
    "straight_component_changes": ["identity"],
    "whole_nonstraight_component_boundary": ["recolor_each_maximal_run"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when demonstrations leave a named rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output grids")
            continue
        input_errors = self_check(pair["input"])
        output_errors = _grid_errors(pair["output"])
        if input_errors:
            reasons.append(f"pair {index} has an invalid input: {input_errors[0]}")
            continue
        if output_errors:
            reasons.append(f"pair {index} has a malformed output: {output_errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if not _strict_grid_equal(expected, pair["output"]):
            reasons.append(f"pair {index} disagrees with the whole-component endpoint rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            _strict_grid_equal(competitor(pair["input"]), pair["output"])
            for pair in demos
        )
        if survives and not _strict_grid_equal(competitor(query["input"]), query["output"]):
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons


def mutation_fixtures():
    """Minimal must-reject grids used by defect-lint and future reviewers."""
    blank = [[0] * 8 for _ in range(7)]
    singleton = copy.deepcopy(blank)
    singleton[0][0] = 2
    short_line = copy.deepcopy(blank)
    short_line[0][0] = short_line[0][1] = 2
    solid = copy.deepcopy(blank)
    solid[0][0] = solid[0][1] = solid[1][0] = solid[1][1] = 2
    return [
        ("all_background", blank),
        ("red_singleton", singleton),
        ("red_length_two", short_line),
        ("red_solid_2x2", solid),
    ]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override axis/axes: {', '.join(unknown)}")


def _draw_scheduled_int(ctx, overrides, label: str, scheduled: int, lo: int, hi: int) -> int:
    if overrides.get(label) is not None:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, scheduled, scheduled))


def _construct_scene(height, width, profile, *, difficulty, sample_index, rng, decoy_color):
    motif_placements = _motif_placements(_MOTIFS[profile], height, width)
    rng.shuffle(motif_placements)
    lengths = {
        "easy": (3, 4),
        "medium": (3, 4, 5),
        "hard": (4, 5, 6),
        None: (3, 4, 5),
    }[difficulty]
    requested_decoy_size = 1 if (difficulty == "easy" or sample_index % 2 == 0) else 2

    for motif in motif_placements:
        line_candidates = _line_candidates(height, width, lengths, forbidden=motif)
        rng.shuffle(line_candidates)
        for line in line_candidates:
            red = set(motif) | set(line)
            sizes = (requested_decoy_size, 3 - requested_decoy_size)
            for size in sizes:
                decoy_candidates = _decoy_candidates(height, width, red, size=size)
                if not decoy_candidates:
                    continue
                decoy = rng.choice(decoy_candidates)
                grid = full_grid(height, width, 0)
                for row, col in red:
                    grid[row][col] = 2
                for row, col in decoy:
                    grid[row][col] = decoy_color
                return grid
    raise RuntimeError(
        f"no lawful layout for {height}x{width}, profile={profile}, difficulty={difficulty}"
    )


def _motif_placements(cells, height, width):
    placements: list[tuple[tuple[int, int], ...]] = []
    for variant in _dihedral_variants(cells):
        shape_h = max(row for row, _ in variant) + 1
        shape_w = max(col for _, col in variant) + 1
        if shape_h > height or shape_w > width:
            continue
        for row0 in range(height - shape_h + 1):
            for col0 in range(width - shape_w + 1):
                placements.append(tuple((row0 + row, col0 + col) for row, col in variant))
    return placements


def _line_candidates(height, width, lengths, *, forbidden):
    forbidden_set = set(forbidden)
    candidates: list[tuple[tuple[int, int], ...]] = []
    for length in lengths:
        if length <= width:
            for row in range(height):
                for col0 in range(width - length + 1):
                    cells = tuple((row, col0 + offset) for offset in range(length))
                    if _chebyshev_separated(cells, forbidden_set):
                        candidates.append(cells)
        if length <= height:
            for col in range(width):
                for row0 in range(height - length + 1):
                    cells = tuple((row0 + offset, col) for offset in range(length))
                    if _chebyshev_separated(cells, forbidden_set):
                        candidates.append(cells)
    return candidates


def _decoy_candidates(height, width, red, *, size):
    red_set = set(red)
    supports: list[tuple[tuple[int, int], ...]] = []
    if size == 1:
        raw = [((row, col),) for row in range(height) for col in range(width)]
    else:
        raw = []
        for row in range(height):
            for col in range(width):
                if col + 1 < width:
                    raw.append(((row, col), (row, col + 1)))
                if row + 1 < height:
                    raw.append(((row, col), (row + 1, col)))
    for cells in raw:
        if any(cell in red_set for cell in cells):
            continue
        if _chebyshev_separated(cells, red_set):
            supports.append(cells)
    return supports


def _chebyshev_separated(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return all(
        max(abs(row - other_row), abs(col - other_col)) > 1
        for row, col in cells
        for other_row, other_col in occupied
    )


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["every row must be a nonempty sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colors 0..9"]
    return []


def _components_of_color(grid, color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = row + drow, col + dcol
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _red_components(grid):
    return _components_of_color(grid, 2)


def _is_straight(component: set[tuple[int, int]]) -> bool:
    if not component:
        return False
    return len({row for row, _ in component}) == 1 or len({col for _, col in component}) == 1


def _component_graph(component):
    component = set(component)
    degrees = []
    twice_edges = 0
    for row, col in component:
        degree = sum(
            (row + drow, col + dcol) in component
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        degrees.append(degree)
        twice_edges += degree
    return twice_edges // 2, degrees


def _normalize_cells(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _transform_cells(cells, transform: int):
    transformed = []
    for row, col in cells:
        if transform == 0:
            point = (row, col)
        elif transform == 1:
            point = (col, -row)
        elif transform == 2:
            point = (-row, -col)
        elif transform == 3:
            point = (-col, row)
        elif transform == 4:
            point = (row, -col)
        elif transform == 5:
            point = (-row, col)
        elif transform == 6:
            point = (col, row)
        elif transform == 7:
            point = (-col, -row)
        else:  # pragma: no cover - internal finite caller
            raise ValueError(f"unknown transform {transform}")
        transformed.append(point)
    return _normalize_cells(transformed)


def _dihedral_variants(cells):
    return tuple(sorted({_transform_cells(cells, transform) for transform in range(8)}))


def _shape_signature(cells):
    normalized = _normalize_cells(cells)
    return min(_transform_cells(normalized, transform) for transform in range(8))


def _strict_grid_equal(left, right):
    return not _grid_errors(left) and not _grid_errors(right) and [list(row) for row in left] == [list(row) for row in right]


_PROFILE_BY_SIGNATURE = {
    _shape_signature(cells): name
    for name, cells in _MOTIFS.items()
}
if len(_PROFILE_BY_SIGNATURE) != len(_MOTIFS):  # import-time invariant, never data-dependent
    raise RuntimeError("scene profile motifs are not topologically distinct modulo D4")
