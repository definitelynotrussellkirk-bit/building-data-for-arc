"""Generator for ``4c33979d9cc2`` — recolor the largest orange component.

The input contains two to five separated 4-connected orange(7) components and
one component has a unique greatest cell count.  The canonical rule preserves
the full input grid and recolors only that component red(2).

The five-example schedule deliberately rebuts the canonical shortcuts "choose
the last component" and "choose the largest bounding box" while also varying
component count, winner position, edge contact, repeated non-winning sizes, and
diagonal-only contact.  Output authority remains the canonical Racket rule;
``rule_mirror`` exists only for task-local semantic tests and rival audits.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c33979d9cc2"
TASK_ID = "4c33979d9cc2"
VERSION = "3.0.0"
RULE_HASH = "4a8c0ad5c512"

SUMMARY = (
    "A background-0 grid contains 2-5 separated orange(7) components with a "
    "unique largest cell count. Recolor only the largest component red(2); "
    "preserve every smaller orange component and every background cell."
)

INVARIANTS = [
    "the rectangular grid uses only background 0 and orange 7, with 0 modal",
    "there are 2-5 four-connected orange components",
    "exactly one component has the greatest cell count",
    "smaller components may tie in size and different components may touch only diagonally",
    "component cell count, not reading order, location, or bounding-box area, selects the winner",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-example schedule anchors 6/7/9; otherwise band rng",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "five-example schedule anchors 7/8/9; otherwise band rng",
        "valid": "7..14",
    },
    "n_components": {
        "type": "int",
        "default": "scheduled/band rng over 2..5",
        "valid": "2..5",
    },
}

_VALID_H = (6, 12)
_VALID_W = (7, 14)
_VALID_N = (2, 5)
_MAX_COMPONENT_SIZE = 8

SCHEDULE_PROFILES = (
    "largest_first_edge",
    "largest_last_interior",
    "bbox_area_decoy",
    "nonlargest_tie_diagonal",
    "two_components",
)
EXAMPLES_NEEDED = len(SCHEDULE_PROFILES)
MIN_STRICT_FRAC = 1.0

# Connected polyominoes with compact and sparse alternatives.  D4 transforms
# provide orientation diversity without changing cell count or connectivity.
_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    5: (
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
}


def _normalize(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_variants(cells):
    variants = set()
    points = tuple(cells)
    for reflect in (False, True):
        for turns in range(4):
            transformed = []
            for row, col in points:
                x, y = row, -col if reflect else col
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            variants.add(_normalize(transformed))
    return tuple(sorted(variants))


def _components(grid, *, diagonal: bool = False):
    height = len(grid)
    width = len(grid[0]) if height else 0
    directions = (
        (
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        )
        if diagonal
        else ((1, 0), (-1, 0), (0, 1), (0, -1))
    )
    seen = set()
    found = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 7 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for d_row, d_col in directions:
                    neighbor = row + d_row, col + d_col
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == 7
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            found.append(tuple(sorted(cells)))
    return found


def _bbox(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(component):
    row0, col0, row1, col1 = _bbox(component)
    return (row1 - row0 + 1) * (col1 - col0 + 1)


def _reading_order(components):
    return sorted(components, key=lambda component: min(component))


def _touches_edge(component, height, width):
    return any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in component
    )


def _components_touch_diagonally(left, right):
    right_cells = set(right)
    return any(
        (row + d_row, col + d_col) in right_cells
        for row, col in left
        for d_row, d_col in ((-1, -1), (-1, 1), (1, -1), (1, 1))
    )


def _analysis(grid):
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    components = _components(grid)
    ordered = _reading_order(components)
    largest = max(components, key=len)
    largest_rank = ordered.index(largest)
    smaller = [component for component in components if component is not largest]
    size_counts = Counter(len(component) for component in smaller)
    largest_bbox_area = _bbox_area(largest)
    return {
        "errors": [],
        "components": components,
        "largest": largest,
        "largest_rank": largest_rank,
        "largest_first": largest_rank == 0,
        "largest_last": largest_rank == len(ordered) - 1,
        "bbox_area_decoy": any(
            _bbox_area(component) > largest_bbox_area for component in smaller
        ),
        "nonlargest_size_tie": any(count >= 2 for count in size_counts.values()),
        "diagonal_only_contact": any(
            _components_touch_diagonally(largest, component) for component in smaller
        ),
        "edge_largest": _touches_edge(largest, len(grid), len(grid[0])),
        "interior_largest": not _touches_edge(largest, len(grid), len(grid[0])),
        "edge_decoy": any(
            _touches_edge(component, len(grid), len(grid[0])) for component in smaller
        ),
        "interior_decoy": any(
            not _touches_edge(component, len(grid), len(grid[0]))
            for component in smaller
        ),
        "two_components": len(components) == 2,
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_components": len(_components(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical manifold and reject ambiguous or hidden-rule inputs."""
    del difficulty, meta
    if not grid or not grid[0]:
        return ["grid must be nonempty"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]

    height, width = len(grid), len(grid[0])
    errors = []
    if not (_VALID_H[0] <= height <= _VALID_H[1]):
        errors.append(f"grid height {height} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= width <= _VALID_W[1]):
        errors.append(f"grid width {width} outside {_VALID_W[0]}..{_VALID_W[1]}")

    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int)
            or isinstance(value, bool)
            or value not in (0, 7)
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"palette must be exactly within {{0, 7}}, got {bad_values}")
        return errors

    components = _components(grid)
    if not (_VALID_N[0] <= len(components) <= _VALID_N[1]):
        errors.append(
            f"expected {_VALID_N[0]}..{_VALID_N[1]} orange components, "
            f"found {len(components)}"
        )
    sizes = [len(component) for component in components]
    if any(size < 1 or size > _MAX_COMPONENT_SIZE for size in sizes):
        errors.append(
            f"component sizes must lie in 1..{_MAX_COMPONENT_SIZE}, got {sorted(sizes)}"
        )
    if sizes and sizes.count(max(sizes)) != 1:
        errors.append(f"expected a unique largest component, got sizes {sorted(sizes)}")

    if sum(sizes) * 2 >= height * width:
        errors.append("background 0 must be strictly modal")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Generated lessons are a strict extension of all three canonical inputs."""
    return self_check(grid)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _choose_component_count(ctx, profile, difficulty, overrides):
    if "n_components" in overrides:
        return ctx.draw_int("n_components", *_VALID_N)
    if profile == "two_components":
        return ctx.draw_int("n_components", 2, 2)
    if profile == "nonlargest_tie_diagonal":
        low, high = (3, 3) if difficulty == "easy" else ((3, 4) if difficulty != "hard" else (3, 5))
        return ctx.draw_int("n_components", low, high)
    if difficulty == "easy":
        return ctx.draw_int("n_components", 2, 3)
    if difficulty == "hard":
        return ctx.draw_int("n_components", 3, 5)
    return ctx.draw_int("n_components", 2, 4)


def _choose_sizes(rng, count, profile):
    if profile == "bbox_area_decoy":
        return {
            2: [5, 6],
            3: [2, 5, 6],
            4: [1, 3, 5, 6],
            5: [1, 2, 3, 5, 6],
        }[count]

    largest = rng.randint(max(4, count), _MAX_COMPONENT_SIZE)
    if profile == "nonlargest_tie_diagonal" and count >= 3:
        tied = rng.randint(1, min(3, largest - 1))
        smaller = [tied, tied]
        while len(smaller) < count - 1:
            smaller.append(rng.randint(1, largest - 1))
    else:
        smaller = [rng.randint(1, largest - 1) for _ in range(count - 1)]
    return sorted(smaller + [largest])


def _shape_for(rng, size, profile, *, is_largest):
    if profile == "bbox_area_decoy" and size == 5 and not is_largest:
        base = _BASE_SHAPES[5][0]  # sparse 3x3 L: bbox area 9
    elif profile == "bbox_area_decoy" and size == 6 and is_largest:
        base = _BASE_SHAPES[6][0]  # compact 2x3: bbox area 6
    else:
        base = rng.choice(_BASE_SHAPES[size])
    return rng.choice(_shape_variants(base))


def _orthogonally_clear(cells, occupied):
    for row, col in cells:
        if (row, col) in occupied:
            return False
        for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (row + d_row, col + d_col) in occupied:
                return False
    return True


def _diagonally_adjacent(cells, target):
    return any(
        (row + d_row, col + d_col) in target
        for row, col in cells
        for d_row, d_col in ((-1, -1), (-1, 1), (1, -1), (1, 1))
    )


def _translated_candidates(shape, height, width):
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    return [
        tuple((row0 + row, col0 + col) for row, col in shape)
        for row0 in range(height - shape_height + 1)
        for col0 in range(width - shape_width + 1)
    ]


def _layout_once(rng, height, width, sizes, profile):
    largest_size = max(sizes)
    records = []
    largest_taken = False
    for size in sorted(sizes, reverse=True):
        is_largest = size == largest_size and not largest_taken
        if is_largest:
            largest_taken = True
        records.append(
            {
                "size": size,
                "largest": is_largest,
                "shape": _shape_for(rng, size, profile, is_largest=is_largest),
            }
        )

    placed: list[tuple[tuple[int, int], ...]] = []
    occupied: set[tuple[int, int]] = set()
    largest_cells: tuple[tuple[int, int], ...] | None = None

    def search(index):
        nonlocal largest_cells
        if index == len(records):
            return True
        record = records[index]
        candidates = _translated_candidates(record["shape"], height, width)
        rng.shuffle(candidates)

        if record["largest"] and profile == "largest_first_edge":
            candidates.sort(key=lambda cells: min(cells))
        elif record["largest"] and profile == "largest_last_interior":
            candidates.sort(key=lambda cells: min(cells), reverse=True)

        for cells in candidates:
            touches_edge = _touches_edge(cells, height, width)
            if record["largest"]:
                if profile == "largest_first_edge" and not touches_edge:
                    continue
                if profile == "largest_last_interior" and touches_edge:
                    continue
            elif index == 1:
                if profile == "largest_first_edge" and touches_edge:
                    continue
                if profile == "largest_last_interior" and not touches_edge:
                    continue
                if profile == "nonlargest_tie_diagonal" and not _diagonally_adjacent(
                    cells, set(largest_cells or ())
                ):
                    continue

            if largest_cells is not None and not record["largest"]:
                if profile == "largest_first_edge" and min(cells) <= min(largest_cells):
                    continue
                if profile == "largest_last_interior" and min(cells) >= min(largest_cells):
                    continue
            if not _orthogonally_clear(cells, occupied):
                continue

            previous_largest = largest_cells
            if record["largest"]:
                largest_cells = cells
            placed.append(cells)
            occupied.update(cells)
            if search(index + 1):
                return True
            for cell in cells:
                occupied.remove(cell)
            placed.pop()
            largest_cells = previous_largest
        return False

    if not search(0):
        return None

    grid = full_grid(height, width, 0)
    for component in placed:
        for row, col in component:
            grid[row][col] = 7
    return grid


def _profile_satisfied(grid, profile, *, count_was_overridden):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    if profile == "largest_first_edge":
        return (
            analysis["largest_first"]
            and analysis["edge_largest"]
            and analysis["interior_decoy"]
        )
    if profile == "largest_last_interior":
        return (
            analysis["largest_last"]
            and analysis["interior_largest"]
            and analysis["edge_decoy"]
        )
    if profile == "bbox_area_decoy":
        return analysis["bbox_area_decoy"]
    if profile == "nonlargest_tie_diagonal":
        return analysis["diagonal_only_contact"] and (
            analysis["nonlargest_size_tie"] or count_was_overridden
        )
    if profile == "two_components":
        return analysis["two_components"] or count_was_overridden
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    profile = schedule_profile(seed, sample_index, difficulty)
    if band == "easy":
        height_range, width_range = (6, 8), (7, 10)
    elif band == "hard":
        height_range, width_range = (9, 12), (10, 14)
    else:
        height_range, width_range = (7, 10), (8, 12)

    # One slot in every five-example lesson anchors the empirical canonical
    # (height, width, palette-size) profile for its difficulty band.  This is
    # curriculum ordering rather than a hidden axis: explicit dimension
    # overrides always win, and every other slot keeps the wider band range.
    canonical_anchor = {"easy": (6, 7), "medium": (7, 8), "hard": (9, 9)}[band]
    use_anchor = profile == "two_components" and not (
        {"grid_h", "grid_w"} & overrides.keys()
    )
    height = (
        ctx.draw_int("grid_h", *_VALID_H)
        if "grid_h" in overrides
        else ctx.draw_int("grid_h", canonical_anchor[0], canonical_anchor[0])
        if use_anchor
        else ctx.draw_int("grid_h", *height_range)
    )
    width = (
        ctx.draw_int("grid_w", *_VALID_W)
        if "grid_w" in overrides
        else ctx.draw_int("grid_w", canonical_anchor[1], canonical_anchor[1])
        if use_anchor
        else ctx.draw_int("grid_w", *width_range)
    )
    count = _choose_component_count(ctx, profile, band, overrides)
    rng = ctx.draw_rng("layout")

    for _ in range(120):
        sizes = _choose_sizes(rng, count, profile)
        grid = _layout_once(rng, height, width, sizes, profile)
        if grid is None:
            continue
        if not _profile_satisfied(
            grid, profile, count_was_overridden="n_components" in overrides
        ):
            continue
        errors = self_check(grid)
        if errors:
            continue
        return grid
    raise RuntimeError(
        f"could not place profile={profile!r}, dims={height}x{width}, "
        f"n_components={count}"
    )


def _recolor_components(grid, selected):
    output = [row[:] for row in grid]
    for component in selected:
        for row, col in component:
            output[row][col] = 2
    return output


def rule_mirror(grid):
    """Python mirror used only by task-local tests and semantic rivals."""
    components = _components(grid)
    return _recolor_components(grid, [max(components, key=len)])


def _rival_first(grid):
    return _recolor_components(grid, [_reading_order(_components(grid))[0]])


def _rival_last(grid):
    return _recolor_components(grid, [_reading_order(_components(grid))[-1]])


def _rival_smallest(grid):
    return _recolor_components(grid, [min(_components(grid), key=len)])


def _rival_largest_bbox(grid):
    components = _components(grid)
    chosen = max(components, key=lambda component: (_bbox_area(component), min(component)))
    return _recolor_components(grid, [chosen])


def _rival_all(grid):
    return _recolor_components(grid, _components(grid))


def _rival_repeated_sizes(grid):
    components = _components(grid)
    counts = Counter(len(component) for component in components)
    selected = [component for component in components if counts[len(component)] > 1]
    return _recolor_components(grid, selected)


def _rival_largest_8_connected(grid):
    components = _components(grid, diagonal=True)
    return _recolor_components(grid, [max(components, key=len)])


def _rival_ignore_edge(grid):
    components = _components(grid)
    interior = [
        component
        for component in components
        if not _touches_edge(component, len(grid), len(grid[0]))
    ]
    return _recolor_components(grid, [max(interior, key=len)] if interior else [])


def _rival_prefer_edge(grid):
    components = _components(grid)
    edge = [
        component
        for component in components
        if _touches_edge(component, len(grid), len(grid[0]))
    ]
    return _recolor_components(grid, [max(edge, key=len)] if edge else [])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_in_reading_order": _rival_first,
    "last_in_reading_order": _rival_last,
    "smallest_component": _rival_smallest,
    "largest_bbox_area": _rival_largest_bbox,
    "recolor_all": _rival_all,
    "recolor_repeated_sizes": _rival_repeated_sizes,
    "largest_8_connected": _rival_largest_8_connected,
    "ignore_edge_components": _rival_ignore_edge,
    "prefer_edge_components": _rival_prefer_edge,
}

CANONICAL_SHORTCUTS = {
    # Both reproduce all three public pairs; generated witnesses must break them.
    "last_in_reading_order": _rival_last,
    "largest_bbox_area": _rival_largest_bbox,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(name):
    def predicate(grid):
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[name])

    return predicate


def _edge_witness(grid):
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["edge_largest"]
        and analysis["interior_decoy"]
    )


def _interior_witness(grid):
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["interior_largest"]
        and analysis["edge_decoy"]
    )


SEMANTIC_WITNESSES = {
    "largest_first": _witness("largest_first"),
    "largest_last": _witness("largest_last"),
    "bbox_area_decoy": _witness("bbox_area_decoy"),
    "nonlargest_size_tie": _witness("nonlargest_size_tie"),
    "diagonal_only_contact": _witness("diagonal_only_contact"),
    "edge_largest": _edge_witness,
    "interior_largest": _interior_witness,
    "two_components": _witness("two_components"),
}

WITNESS_RIVALS = {
    "largest_first": ["last_in_reading_order"],
    "largest_last": ["first_in_reading_order"],
    "bbox_area_decoy": ["largest_bbox_area"],
    "nonlargest_size_tie": ["recolor_repeated_sizes"],
    "diagonal_only_contact": ["largest_8_connected"],
    "edge_largest": ["ignore_edge_components"],
    "interior_largest": ["prefer_edge_components"],
    "two_components": ["recolor_all"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared rival that survives every demo but misses the query."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but predicts a "
                    "different query output"
                )
    return reasons
