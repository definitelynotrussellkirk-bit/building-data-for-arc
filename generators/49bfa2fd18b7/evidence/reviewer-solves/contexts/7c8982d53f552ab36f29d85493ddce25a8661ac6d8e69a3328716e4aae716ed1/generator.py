"""Generator for arc_additional_puzzle_bank_volume8:M51.

Rule: rank the color-6 components by area, select the second-largest,
crop it to its bounding box, and repaint that shape color 2 on black.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49bfa2fd18b7"
TASK_ID = "49bfa2fd18b7"
VERSION = "3.0.0"
RULE_HASH = "5ee6c4df3ad5"

SUMMARY = (
    "A black 9..16 by 10..16 grid contains three or four separated purple "
    "(6) 4-connected components with distinct areas, plus one gray (5) "
    "domino distractor. Rank the purple components by area, take the "
    "second-largest, crop it to its bounding box, and repaint its shape red "
    "(2) on black. The selected component's size, shape, position, edge "
    "contact, number of competing components, canvas size, and distractor "
    "orientation vary; every normal lesson has both a larger and a smaller "
    "purple component so second-largest never aliases largest or smallest."
)

INVARIANTS = [
    "exactly 3..4 mutually separated color-6 components with distinct areas",
    "the second-largest color-6 component has area 4..7 and a non-rectangular 2-D bbox",
    "exactly one separated color-5 domino is present and all other cells are black",
    "at least one purple component is larger and at least one is smaller than the target",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased, with a canonical 10..12 prior",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased, with a canonical 10..12 prior",
        "valid": "10..16",
    },
    "blob_count": {
        "type": "int",
        "default": "3 most often, otherwise 4",
        "valid": "3..4",
    },
    "target_size": {
        "type": "int",
        "default": "difficulty-biased; canonical prior fixes 4",
        "valid": "4..7",
    },
    "target_on_edge": {
        "type": "bool",
        "default": "uniform",
        "valid": "true|false",
    },
    "gray_orientation": {
        "type": "str",
        "default": "horizontal in canonical-prior draws, otherwise varied",
        "valid": "horizontal|vertical",
    },
}

_ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_CANONICAL_PRIOR = 0.35


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if start in seen or grid[start_row][start_col] != color:
                continue
            seen.add(start)
            stack = [start]
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in _ORTHOGONAL:
                    neighbour = row + delta_row, col + delta_col
                    if (
                        0 <= neighbour[0] < height
                        and 0 <= neighbour[1] < width
                        and neighbour not in seen
                        and grid[neighbour[0]][neighbour[1]] == color
                    ):
                        seen.add(neighbour)
                        stack.append(neighbour)
            components.append(cells)
    return components


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalize(cells):
    top, left, _, _ = _bbox(cells)
    return sorted((row - top, col - left) for row, col in cells)


def _shape_dims(cells):
    normalized = _normalize(cells)
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _ranked_six_components(grid):
    return sorted(
        _components(grid, 6),
        key=lambda cells: (-len(cells), _bbox(cells)[0], _bbox(cells)[1]),
    )


def _chebyshev_gap(left, right):
    return min(
        max(abs(row - other_row), abs(col - other_col))
        for row, col in left
        for other_row, other_col in right
    )


def _analyze(grid):
    errors: list[str] = []
    facts = {
        "grid_h": None,
        "grid_w": None,
        "blob_count": None,
        "target_size": None,
        "target_on_edge": None,
        "gray_orientation": None,
        "ranked_sizes": [],
        "target_bbox": None,
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a nonempty rectangular list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return facts, ["grid must contain at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return facts, ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be literal ARC colors 0..9")

    height = len(grid)
    facts["grid_h"], facts["grid_w"] = height, width
    if not 9 <= height <= 16:
        errors.append("grid height must be in 9..16")
    if not 10 <= width <= 16:
        errors.append("grid width must be in 10..16")

    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 5, 6})
    if unexpected:
        errors.append(f"input may use only colors 0, 5, and 6; found {unexpected}")

    ranked = _ranked_six_components(grid)
    facts["blob_count"] = len(ranked)
    sizes = [len(cells) for cells in ranked]
    facts["ranked_sizes"] = sizes
    if len(ranked) not in (3, 4):
        errors.append("expected exactly three or four color-6 components")
    if len(sizes) != len(set(sizes)):
        errors.append("color-6 component areas must be distinct")

    if len(ranked) >= 2:
        target = ranked[1]
        target_size = len(target)
        facts["target_size"] = target_size
        top, left, bottom, right = _bbox(target)
        facts["target_bbox"] = [top, left, bottom, right]
        facts["target_on_edge"] = (
            top == 0 or left == 0 or bottom == height - 1 or right == width - 1
        )
        bbox_height = bottom - top + 1
        bbox_width = right - left + 1
        if not 4 <= target_size <= 7:
            errors.append("the second-largest color-6 component must have area 4..7")
        if bbox_height < 2 or bbox_width < 2:
            errors.append("the second-largest component must span at least two rows and columns")
        if target_size == bbox_height * bbox_width:
            errors.append("the second-largest component must not be a solid rectangle")
        if len(ranked) >= 3 and not (
            len(ranked[0]) > target_size > len(ranked[-1])
        ):
            errors.append("the target must have both a larger and a smaller competitor")

    for left_component, right_component in combinations(ranked, 2):
        if _chebyshev_gap(left_component, right_component) < 2:
            errors.append("purple components must be separated by at least one background cell")
            break

    gray_components = _components(grid, 5)
    gray_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if len(gray_components) != 1 or len(gray_cells) != 2:
        errors.append("expected exactly one two-cell gray component")
    elif len(gray_components[0]) == 2:
        first, second = gray_components[0]
        if first[0] == second[0] and abs(first[1] - second[1]) == 1:
            facts["gray_orientation"] = "horizontal"
        elif first[1] == second[1] and abs(first[0] - second[0]) == 1:
            facts["gray_orientation"] = "vertical"
        else:
            errors.append("the two gray cells must form an orthogonal domino")
        if any(_chebyshev_gap(gray_components[0], component) < 2 for component in ranked):
            errors.append("the gray distractor must be separated from every purple component")

    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict:
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "blob_count": facts["blob_count"],
        "target_size": facts["target_size"],
        "target_on_edge": facts["target_on_edge"],
        "gray_orientation": facts["gray_orientation"],
    }


def _draw_int_axis(ctx, name, default_low, default_high, valid_low, valid_high):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, valid_low, valid_high)
    return ctx.draw_int_diff(name, default_low, default_high)


def _random_polyomino(rng, size, max_height, max_width, *, target=False):
    for _ in range(512):
        cells = {(0, 0)}
        while len(cells) < size:
            row, col = rng.choice(tuple(cells))
            delta_row, delta_col = rng.choice(_ORTHOGONAL)
            cells.add((row + delta_row, col + delta_col))
        normalized = _normalize(cells)
        shape_height, shape_width = _shape_dims(normalized)
        if shape_height > max_height or shape_width > max_width:
            continue
        if target and (shape_height < 2 or shape_width < 2):
            continue
        if target and size == shape_height * shape_width:
            continue
        return normalized
    return None


def _canonical_shapes(rng):
    largest = rng.choice(
        (
            [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],
            [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
        )
    )
    target = rng.choice(
        (
            [(0, 0), (1, 0), (2, 0), (2, 1)],
            [(0, 1), (1, 0), (1, 1), (1, 2)],
        )
    )
    smallest = rng.choice(
        (
            [(0, 0), (0, 1), (0, 2)],
            [(0, 0), (1, 0), (2, 0)],
            [(0, 0), (0, 1), (1, 0)],
        )
    )
    return [largest, target, smallest]


def _candidate_positions(shape, height, width, edge_mode=None):
    shape_height, shape_width = _shape_dims(shape)
    positions = []
    for top in range(height - shape_height + 1):
        for left in range(width - shape_width + 1):
            touches_edge = (
                top == 0
                or left == 0
                or top + shape_height == height
                or left + shape_width == width
            )
            if edge_mode is True and not touches_edge:
                continue
            if edge_mode is False and touches_edge:
                continue
            positions.append((top, left))
    return positions


def _place_items(rng, height, width, items, placement_phase):
    candidate_lists = []
    for item in items:
        positions = _candidate_positions(
            item["shape"], height, width, item.get("edge_mode")
        )
        rng.shuffle(positions)
        candidate_lists.append(positions)
    # The target is item 0. Three consecutive sample indices deliberately move
    # it through opposite zones so position-based shortcut rules cannot survive
    # a normal three-demo episode. Shuffle first so equal-score ties still vary.
    if placement_phase == 0:
        candidate_lists[0].sort(key=lambda pos: (pos[0] + pos[1], pos[0], pos[1]))
    elif placement_phase == 1:
        candidate_lists[0].sort(key=lambda pos: (-(pos[0] + pos[1]), -pos[0], -pos[1]))
    else:
        center_row = (height - 1) / 2
        center_col = (width - 1) / 2
        target_shape_h, target_shape_w = _shape_dims(items[0]["shape"])
        candidate_lists[0].sort(
            key=lambda pos: abs(pos[0] + (target_shape_h - 1) / 2 - center_row)
            + abs(pos[1] + (target_shape_w - 1) / 2 - center_col)
        )
    if any(not positions for positions in candidate_lists):
        return None

    placements = []
    occupied = []
    steps = 0

    def visit(index):
        nonlocal steps
        if index == len(items):
            return True
        shape = items[index]["shape"]
        positions = candidate_lists[index]
        if items[index]["color"] == 5 and placements:
            # Phase 0 places gray near the target; phase 1 places it near the
            # largest non-target; phase 2 again favors the target. This makes
            # nearest/farthest-gray shortcuts fail within every three demos.
            reference = placements[1] if placement_phase == 1 and len(placements) > 1 else placements[0]
            ref_row, ref_col = _centroid(reference)
            ranked_positions = []
            for top, left in positions:
                cells = [(top + row, left + col) for row, col in shape]
                cell_row, cell_col = _centroid(cells)
                ranked_positions.append(
                    ((cell_row - ref_row) ** 2 + (cell_col - ref_col) ** 2, top, left)
                )
            positions = [(top, left) for _, top, left in sorted(ranked_positions)]
        for top, left in positions:
            steps += 1
            if steps > 250_000:
                return False
            cells = [(top + row, left + col) for row, col in shape]
            if any(
                max(abs(row - other_row), abs(col - other_col)) <= 1
                for row, col in cells
                for other_row, other_col in occupied
            ):
                continue
            placements.append(cells)
            occupied.extend(cells)
            if visit(index + 1):
                return True
            del occupied[-len(cells):]
            placements.pop()
        return False

    return placements if visit(0) else None



def _centroid(cells):
    return (
        sum(row for row, _ in cells) / len(cells),
        sum(col for _, col in cells) / len(cells),
    )


def _pedagogy_ok(grid, phase):
    """Make every three consecutive samples refute positional shortcuts."""
    ranked = _ranked_six_components(grid)
    target = ranked[1]
    target_key = frozenset(target)
    topmost = min(ranked, key=lambda cells: (_bbox(cells)[0], _bbox(cells)[1]))
    bottommost = max(ranked, key=lambda cells: (_bbox(cells)[2], _bbox(cells)[3]))
    leftmost = min(ranked, key=lambda cells: (_bbox(cells)[1], _bbox(cells)[0]))
    rightmost = max(ranked, key=lambda cells: (_bbox(cells)[3], _bbox(cells)[2]))
    gray = _components(grid, 5)[0]
    gray_center = _centroid(gray)
    by_distance = sorted(
        ranked,
        key=lambda cells: (
            (_centroid(cells)[0] - gray_center[0]) ** 2
            + (_centroid(cells)[1] - gray_center[1]) ** 2,
            _bbox(cells)[0],
            _bbox(cells)[1],
        ),
    )
    is_target = lambda cells: frozenset(cells) == target_key
    if phase == 0:
        return (
            not is_target(bottommost)
            and not is_target(rightmost)
            and is_target(by_distance[0])
        )
    if phase == 1:
        return (
            not is_target(topmost)
            and not is_target(leftmost)
            and not is_target(by_distance[0])
        )
    return not is_target(by_distance[-1])


def _build_scene(ctx, *, canonical_profile, placement_phase):
    if canonical_profile:
        height = ctx.draw_int("grid_h", 10, 12)
        width = ctx.draw_int("grid_w", 10, 12)
        blob_count = ctx.draw_int("blob_count", 3, 3)
        target_size = ctx.draw_int("target_size", 4, 4)
        target_on_edge = ctx.draw_choice("target_on_edge", (False, True))
        gray_orientation = ctx.draw_choice("gray_orientation", ("horizontal",))
    else:
        band_ranges = {
            "easy": ((9, 12), (10, 13), (4, 5)),
            "medium": ((10, 14), (10, 15), (4, 6)),
            "hard": ((12, 16), (12, 16), (5, 7)),
        }
        height_range, width_range, target_range = band_ranges.get(
            ctx.difficulty, ((9, 16), (10, 16), (4, 7))
        )
        height = _draw_int_axis(ctx, "grid_h", *height_range, 9, 16)
        width = _draw_int_axis(ctx, "grid_w", *width_range, 10, 16)
        blob_count = ctx.draw_int("blob_count", 3, 4)
        if "target_size" in ctx.overrides and ctx.overrides["target_size"] is not None:
            target_size = ctx.draw_int("target_size", 4, 7)
        else:
            target_size = ctx.draw_int("target_size", *target_range)
        target_on_edge = ctx.draw_choice("target_on_edge", (False, True))
        gray_orientation = ctx.draw_choice(
            "gray_orientation", ("horizontal", "vertical")
        )

    geometry_rng = ctx.draw_rng("geometry")
    if canonical_profile:
        sizes = [5, 4, 3]
    else:
        larger_choices = list(range(target_size + 1, min(9, target_size + 3) + 1))
        if not larger_choices:
            raise ValueError("target_size leaves no valid larger purple component")
        larger = geometry_rng.choice(larger_choices)
        smaller_pool = list(range(2, target_size))
        if len(smaller_pool) < blob_count - 2:
            raise ValueError("target_size is incompatible with the requested blob_count")
        smaller = geometry_rng.sample(smaller_pool, blob_count - 2)
        sizes = [larger, target_size] + sorted(smaller, reverse=True)

    gray_shape = (
        [(0, 0), (0, 1)]
        if gray_orientation == "horizontal"
        else [(0, 0), (1, 0)]
    )

    for _ in range(64):
        if canonical_profile:
            purple_shapes = _canonical_shapes(geometry_rng)
        else:
            purple_shapes = []
            for rank, size in enumerate(sizes):
                shape = _random_polyomino(
                    geometry_rng,
                    size,
                    max_height=min(4, height),
                    max_width=min(4, width),
                    target=(rank == 1),
                )
                if shape is None:
                    break
                purple_shapes.append(shape)
            if len(purple_shapes) != len(sizes):
                continue

        items = [
            {
                "shape": purple_shapes[1],
                "color": 6,
                "edge_mode": target_on_edge,
                "rank": 1,
            }
        ]
        items.extend(
            {
                "shape": purple_shapes[index],
                "color": 6,
                "edge_mode": None,
                "rank": index,
            }
            for index in [0, *range(2, len(purple_shapes))]
        )
        items.append(
            {
                "shape": gray_shape,
                "color": 5,
                "edge_mode": None,
                "rank": None,
            }
        )
        placements = _place_items(
            geometry_rng, height, width, items, placement_phase
        )
        if placements is None:
            continue

        grid = full_grid(height, width, 0)
        for item, cells in zip(items, placements):
            for row, col in cells:
                grid[row][col] = item["color"]
        errors = self_check(grid, difficulty=ctx.difficulty, meta={"canonical": canonical_profile})
        if not errors and _pedagogy_ok(grid, placement_phase):
            return grid

    raise ValueError(
        "requested dimensions/axes could not be packed into a valid separated scene"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_profile = (
        not overrides
        and ctx.draw_rng("canonical_prior").random() < _CANONICAL_PRIOR
    )
    return _build_scene(
        ctx,
        canonical_profile=canonical_profile,
        placement_phase=sample_index % 3,
    )
