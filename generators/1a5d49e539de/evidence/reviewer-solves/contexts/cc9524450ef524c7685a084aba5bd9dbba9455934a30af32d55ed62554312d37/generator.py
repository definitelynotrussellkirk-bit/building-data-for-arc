"""Generator for the unique left-right-asymmetric object crop task.

Canonical rule
--------------
Treat equal-coloured nonzero cells as 8-connected objects, scan objects in
row-major discovery order, and return the bounding-box crop of the first object
whose shape is not symmetric under a left-right reflection.

The teaching grammar deliberately keeps the canonical structural facts visible:
20--23 square grids, one shared foreground colour, four separated objects, three
left-right-symmetric decoys, and exactly one asymmetric target.  A deterministic
three-example schedule varies the target's size rank, while a four-example
schedule varies its position, so lessons refute fixed colour, size, and position
shortcuts instead of merely producing individually valid grids.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1a5d49e539de"
TASK_ID = "1a5d49e539de"
VERSION = "3.0.1"
RULE_HASH = "71d6cfb99295"
SUMMARY = (
    "A square grid contains four separated monochrome objects. Exactly three "
    "objects are left-right symmetric and exactly one is not; crop the unique "
    "left-right-asymmetric object to its bounding box."
)

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("target_small", "target_middle", "target_large")
MIN_STRICT_FRAC = 0.80

INVARIANTS = [
    "the grid is square with side length 20..23",
    "all four nonzero 8-connected objects use one shared foreground colour",
    "exactly three objects are left-right symmetric",
    "exactly one object is left-right asymmetric and determines the output crop",
    "objects are separated under 8-connectivity and have nontrivial, non-solid shapes",
    "the four 8-connected objects contain 8..13 four-connected fragments, matching canonical diagonal joins",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "keyed rng 20..23",
        "valid": "20..23",
    },
    "color": {
        "type": "int",
        "default": "keyed rng 1..9",
        "valid": "1..9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Grid = list[list[int]]
Component = tuple[int, list[tuple[int, int]]]


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for label in AXES:
        if label in overrides and overrides[label] is not None and type(overrides[label]) is not int:
            raise TypeError(f"{label} override must be an integer (not bool)")


def _components8(grid: Grid) -> list[Component]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[Component] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append((color, cells))
    return components


def _normalize(cells: list[tuple[int, int]] | set[tuple[int, int]]) -> list[tuple[int, int]]:
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return sorted((row - row0, col - col0) for row, col in cells)


def _shape_dims(cells: list[tuple[int, int]] | set[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize(cells)
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _is_lr_symmetric(cells: list[tuple[int, int]] | set[tuple[int, int]]) -> bool:
    normalized = set(_normalize(cells))
    width = max(col for _, col in normalized) + 1
    return all((row, width - 1 - col) in normalized for row, col in normalized)


def _count_4_components(cells: list[tuple[int, int]] | set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _crop_component(grid: Grid, component: Component) -> Grid:
    _, cells = component
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [row[col0:col1 + 1] for row in grid[row0:row1 + 1]]


def _analysis(grid) -> tuple[list[str], dict[str, Any] | None]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-list grid"], None
    if any(not isinstance(row, list) for row in grid):
        return ["rows must be lists"], None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"], None

    height = len(grid)
    errors: list[str] = []
    if height != width or not 20 <= height <= 23:
        errors.append(f"expected a 20..23 square grid, got {height}x{width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colours 0..9 (not bool)")
        return errors, None

    nonzero_colors = {value for row in grid for value in row if value != 0}
    if len(nonzero_colors) != 1:
        errors.append(
            f"expected exactly one shared nonzero colour, found {sorted(nonzero_colors)}"
        )

    components = _components8(grid)
    if len(components) != 4:
        errors.append(f"expected exactly four 8-connected objects, found {len(components)}")

    symmetric: list[int] = []
    asymmetric: list[int] = []
    for index, (_, cells) in enumerate(components):
        height_i, width_i = _shape_dims(cells)
        if len(cells) < 5:
            errors.append(f"object {index} is too small ({len(cells)} cells)")
        if height_i < 2 or width_i < 2:
            errors.append(f"object {index} has a degenerate {height_i}x{width_i} box")
        if len(cells) == height_i * width_i:
            errors.append(f"object {index} is a solid rectangle and hides shape evidence")
        if _is_lr_symmetric(cells):
            symmetric.append(index)
        else:
            asymmetric.append(index)

    if len(symmetric) != 3 or len(asymmetric) != 1:
        errors.append(
            "expected exactly three LR-symmetric objects and one LR-asymmetric "
            f"object, found {len(symmetric)} symmetric / {len(asymmetric)} asymmetric"
        )

    four_connected_count = sum(_count_4_components(cells) for _, cells in components)
    if not 8 <= four_connected_count <= 13:
        errors.append(
            "expected 8..13 four-connected fragments inside the four diagonal-connected "
            f"objects, found {four_connected_count}"
        )

    analysis = {
        "height": height,
        "width": width,
        "color": next(iter(nonzero_colors)) if len(nonzero_colors) == 1 else None,
        "components": components,
        "symmetric_indices": symmetric,
        "asymmetric_indices": asymmetric,
        "target_index": asymmetric[0] if len(asymmetric) == 1 else None,
        "four_connected_count": four_connected_count,
    }
    return errors, analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full legal teaching grammar, not merely non-emptiness."""
    del difficulty, meta
    errors, _ = _analysis(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the structural manifold shared by all official examples."""
    errors, _ = _analysis(grid)
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover both advertised axes exactly from a valid returned grid."""
    errors, analysis = _analysis(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {"grid_size": analysis["height"], "color": analysis["color"]}


def rule_mirror(grid: Grid) -> Grid:
    """Pure-Python mirror of the pinned canonical Racket rule."""
    if not grid or not grid[0]:
        raise ValueError("outside rule domain: empty grid")
    for component in _components8(grid):
        if not _is_lr_symmetric(component[1]):
            return _crop_component(grid, component)
    raise ValueError("outside rule domain: no LR-asymmetric object")


def _frontier(
    cells: set[tuple[int, int]],
    height: int,
    width: int,
    *,
    diagonals: bool = False,
) -> list[tuple[int, int]]:
    candidates: set[tuple[int, int]] = set()
    directions = (
        tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
        if diagonals
        else ((-1, 0), (1, 0), (0, -1), (0, 1))
    )
    for row, col in cells:
        for dr, dc in directions:
            rr, cc = row + dr, col + dc
            if 0 <= rr < height and 0 <= cc < width and (rr, cc) not in cells:
                candidates.add((rr, cc))
    return sorted(candidates)


def _make_lr_symmetric(rng, size: int, *, fragments: int) -> list[tuple[int, int]]:
    """Build an exact-size, connected, irregular LR-symmetric shape in <=7x7."""
    minimum_center = 3 if fragments == 1 else 1
    center_options = [
        count
        for count in range(minimum_center, min(7, size) + 1)
        if count % 2 == size % 2 and 1 <= (size - count) // 2 <= 18
    ]
    if not center_options:
        raise ValueError(f"cannot construct symmetric shape of size {size}")

    for _ in range(200):
        center_count = rng.choice(center_options)
        half_extra = (size - center_count) // 2
        height = rng.randint(max(3, center_count), 7)
        start = rng.randint(0, height - center_count)
        half: set[tuple[int, int]] = {
            (row, 0) for row in range(start, start + center_count)
        }
        while len(half) < center_count + half_extra:
            candidates = [
                cell
                for cell in _frontier(half, height, 4, diagonals=fragments > 1)
                if cell[1] > 0
            ]
            if not candidates:
                break
            # Prefer boundary growth only mildly; keyed randomness still yields
            # many distinct silhouettes without creating detached mirror halves.
            half.add(rng.choice(candidates))
        if len(half) != center_count + half_extra:
            continue

        full = set(half)
        full.update((row, -col) for row, col in half if col > 0)
        normalized = _normalize(full)
        shape_h, shape_w = _shape_dims(normalized)
        if (
            len(normalized) == size
            and shape_h >= 3
            and shape_w >= 3
            and shape_h <= 7
            and shape_w <= 7
            and len(normalized) < shape_h * shape_w
            and _is_lr_symmetric(normalized)
            and _count_4_components(normalized) == fragments
        ):
            return normalized
    raise RuntimeError(f"failed to construct LR-symmetric shape of size {size}")


def _make_asymmetric(rng, size: int, *, fragments: int) -> list[tuple[int, int]]:
    """Build an exact-size connected, irregular, verified LR-asymmetric blob."""
    for _ in range(300):
        cells: set[tuple[int, int]] = {(rng.randint(2, 4), rng.randint(2, 4))}
        while len(cells) < size:
            candidates = _frontier(cells, 7, 7, diagonals=True)
            if not candidates:
                break
            cells.add(rng.choice(candidates))
        if len(cells) != size:
            continue
        normalized = _normalize(cells)
        shape_h, shape_w = _shape_dims(normalized)
        if (
            shape_h >= 3
            and shape_w >= 3
            and len(normalized) < shape_h * shape_w
            and not _is_lr_symmetric(normalized)
            and _count_4_components(normalized) == fragments
        ):
            return normalized
    raise RuntimeError(f"failed to construct LR-asymmetric shape of size {size}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive indices always cover all target-size roles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _sizes_for_profile(profile: str, difficulty: str | None, rng) -> tuple[int, list[int]]:
    band_offset = {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    if profile == "target_small":
        target = 8 + band_offset
        decoys = [target + 3, target + 6, target + 10]
    elif profile == "target_middle":
        target = 13 + band_offset
        decoys = [target - 4, target + 3, target + 7]
    elif profile == "target_large":
        target = 20 + min(band_offset, 2)
        decoys = [9 + band_offset, 13 + band_offset, 17 + band_offset]
    else:  # pragma: no cover - internal schedule is closed
        raise ValueError(f"unknown schedule profile: {profile}")
    rng.shuffle(decoys)
    return target, decoys


def _slot_boxes(size: int) -> list[tuple[int, int, int, int]]:
    """Four 8+-cell quadrants separated by two blank rows and columns."""
    middle = size // 2
    top = (1, middle - 2)
    bottom = (middle + 1, size - 2)
    left = (1, middle - 2)
    right = (middle + 1, size - 2)
    return [
        (top[0], top[1], left[0], left[1]),
        (top[0], top[1], right[0], right[1]),
        (bottom[0], bottom[1], left[0], left[1]),
        (bottom[0], bottom[1], right[0], right[1]),
    ]


def _place_shapes(grid: Grid, shapes: list[list[tuple[int, int]]], color: int, rng) -> None:
    boxes = _slot_boxes(len(grid))
    dims = [_shape_dims(shape) for shape in shapes]

    # Shared row origins within each pair guarantee stable row-major component
    # indices: top-left, top-right, bottom-left, bottom-right.
    row_origins: dict[int, int] = {}
    for pair_start in (0, 2):
        row0, row1, _, _ = boxes[pair_start]
        max_height = max(dims[pair_start][0], dims[pair_start + 1][0])
        row_origins[pair_start] = rng.randint(row0, row1 - max_height + 1)

    for slot, (shape, (shape_h, shape_w), box) in enumerate(zip(shapes, dims, boxes)):
        row0, row1, col0, col1 = box
        origin_row = row_origins[0 if slot < 2 else 2]
        origin_col = rng.randint(col0, col1 - shape_w + 1)
        if origin_row + shape_h - 1 > row1:
            raise RuntimeError("internal placement row overflow")
        for dr, dc in shape:
            row, col = origin_row + dr, origin_col + dc
            if grid[row][col] != 0:
                raise RuntimeError("internal object overlap")
            grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size = ctx.draw_int_strict("grid_size", 20, 23)
    color = ctx.draw_int_strict("color", 1, 9)
    shape_rng = ctx.draw_rng("shape_family")
    layout_rng = ctx.draw_rng("layout")

    profile = schedule_profile(seed, sample_index, difficulty)
    target_size, decoy_sizes = _sizes_for_profile(profile, difficulty, shape_rng)
    target_shape = _make_asymmetric(shape_rng, target_size, fragments=3)
    decoy_fragment_counts = [1, 3, 3]
    shape_rng.shuffle(decoy_fragment_counts)
    decoy_shapes = [
        _make_lr_symmetric(shape_rng, count, fragments=fragment_count)
        for count, fragment_count in zip(decoy_sizes, decoy_fragment_counts)
    ]

    target_slot = sample_index % 4
    shapes: list[list[tuple[int, int]]] = []
    decoy_iter = iter(decoy_shapes)
    for slot in range(4):
        shapes.append(target_shape if slot == target_slot else next(decoy_iter))

    grid = full_grid(size, size, 0)
    _place_shapes(grid, shapes, color, layout_rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator defect: {errors}")
    return grid


def _components_if_possible(grid) -> list[Component]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return []
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return []
    return _components8(grid)


def _crop_selected(grid, selector: Callable[[list[Component]], int]) -> Grid:
    components = _components_if_possible(grid)
    if not components:
        return []
    return _crop_component(grid, components[selector(components)])


def _first_object(grid):
    return _crop_selected(grid, lambda components: 0)


def _last_object(grid):
    return _crop_selected(grid, lambda components: len(components) - 1)


def _smallest_object(grid):
    return _crop_selected(
        grid,
        lambda components: min(range(len(components)), key=lambda i: (len(components[i][1]), i)),
    )


def _second_smallest_object(grid):
    return _crop_selected(
        grid,
        lambda components: sorted(range(len(components)), key=lambda i: (len(components[i][1]), i))[
            min(1, len(components) - 1)
        ],
    )


def _largest_object(grid):
    return _crop_selected(
        grid,
        lambda components: max(range(len(components)), key=lambda i: (len(components[i][1]), -i)),
    )


def _leftmost_object(grid):
    return _crop_selected(
        grid,
        lambda components: min(
            range(len(components)),
            key=lambda i: (min(col for _, col in components[i][1]), i),
        ),
    )


def _rightmost_object(grid):
    return _crop_selected(
        grid,
        lambda components: max(
            range(len(components)),
            key=lambda i: (max(col for _, col in components[i][1]), -i),
        ),
    )


def _unique_component_color(grid):
    """Old-distribution shortcut: choose the object whose colour is rarest."""
    components = _components_if_possible(grid)
    if not components:
        return []
    counts = Counter(color for color, _ in components)
    index = min(range(len(components)), key=lambda i: (counts[components[i][0]], i))
    return _crop_component(grid, components[index])


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "first_object": _first_object,
    "last_object": _last_object,
    "smallest_object": _smallest_object,
    "second_smallest_object": _second_smallest_object,
    "largest_object": _largest_object,
    "leftmost_object": _leftmost_object,
    "rightmost_object": _rightmost_object,
    "unique_component_color": _unique_component_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid) -> dict[str, Any] | None:
    errors, analysis = _analysis(grid)
    return analysis if not errors else None


def _target_rank(grid) -> int | None:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return None
    target = analysis["target_index"]
    sizes = [len(component[1]) for component in analysis["components"]]
    return sum(size < sizes[target] for size in sizes)


def _target_not_first(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["target_index"] != 0


def _target_not_last(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["target_index"] != 3


def _target_not_smallest(grid) -> bool:
    rank = _target_rank(grid)
    return rank is not None and rank != 0


def _target_not_second_smallest(grid) -> bool:
    rank = _target_rank(grid)
    return rank is not None and rank != 1


def _target_not_largest(grid) -> bool:
    rank = _target_rank(grid)
    return rank is not None and rank != 3


def _target_not_leftmost(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    components = analysis["components"]
    leftmost = min(
        range(len(components)),
        key=lambda i: (min(col for _, col in components[i][1]), i),
    )
    return analysis["target_index"] != leftmost


def _target_not_rightmost(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    components = analysis["components"]
    rightmost = max(
        range(len(components)),
        key=lambda i: (max(col for _, col in components[i][1]), -i),
    )
    return analysis["target_index"] != rightmost


def _all_objects_same_color(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and len({color for color, _ in analysis["components"]}) == 1


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "target_not_first": _target_not_first,
    "target_not_last": _target_not_last,
    "target_not_smallest": _target_not_smallest,
    "target_not_second_smallest": _target_not_second_smallest,
    "target_not_largest": _target_not_largest,
    "target_not_leftmost": _target_not_leftmost,
    "target_not_rightmost": _target_not_rightmost,
    "all_objects_same_color": _all_objects_same_color,
}
WITNESS_RIVALS = {
    "target_not_first": ["first_object", "unique_component_color"],
    "target_not_last": ["last_object"],
    "target_not_smallest": ["smallest_object"],
    "target_not_second_smallest": ["second_smallest_object"],
    "target_not_largest": ["largest_object"],
    "target_not_leftmost": ["leftmost_object"],
    "target_not_rightmost": ["rightmost_object"],
}
BRANCH_WITNESSES = ("all_objects_same_color",)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared shortcut fits demos but changes query."""
    reasons: list[str] = []
    if len(demos) != EXAMPLES_NEEDED:
        reasons.append(f"expected {EXAMPLES_NEEDED} demonstrations, found {len(demos)}")

    for index, pair in enumerate(demos):
        errors = self_check(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} is outside the rule domain: {'; '.join(errors)}")
            continue
        if rule_mirror(pair["input"]) != pair.get("output"):
            reasons.append(f"demo {index} output disagrees with the asymmetric-object crop rule")

    query_errors = self_check(query.get("input"))
    if query_errors:
        reasons.append("query is outside the rule domain: " + "; ".join(query_errors))
        return reasons
    query_answer = rule_mirror(query["input"])
    if query.get("output") != query_answer:
        reasons.append("query label disagrees with the asymmetric-object crop rule")

    # Identifiability is extensional: a lesson is acceptable when every declared
    # competitor is contradicted by its demonstrations.  Schedule-profile
    # coverage is a generator-distribution property, not a requirement on every
    # query rotation of an otherwise unambiguous four-pair lesson.

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair.get("output")
            for pair in demos
            if not self_check(pair.get("input"))
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons
