"""Semantic generator for ARC task 36b22ff07a2e.

A dominant field color encloses a rectangular matrix of background-colored
rooms.  A room is either empty or contains one solid marker rectangle.  The
answer compresses the scene to one cell per room: the marker color when one is
present, otherwise the border/background color.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "36b22ff07a2e"
TASK_ID = "36b22ff07a2e"
VERSION = "4.0.0"
RULE_HASH = "24e4023e7c9d"
SUMMARY = (
    "Find the dominant outer-border color and the dominant non-border field "
    "color.  The field encloses a rectangular matrix of rooms.  Replace each "
    "room by its unique marker color, or by the outer-border color when the "
    "room is empty, preserving the room matrix's row/column order."
)
INVARIANTS = [
    "the outer border is a single background color",
    "one dominant, different field color separates every enclosed room",
    "the enclosed components form a complete rectangular room matrix",
    "each room is empty or contains one solid rectangle of one marker color",
    "both empty and marked rooms occur, so the background fallback is taught",
]

LATTICE_SHAPES = ("2x2", "2x3", "3x2", "3x3")
SCENE_PROFILES = (
    "sparse_uniform",
    "mixed_rows",
    "mixed_columns",
    "dense_varied",
)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "lattice_shape": {
        "type": "str",
        "default": "difficulty-weighted exact room-matrix shape",
        "valid": "|".join(LATTICE_SHAPES),
    },
    "scene_profile": {
        "type": "str",
        "default": "recoverable marker-density/room-variation profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "background_color": {
        "type": "color",
        "default": "keyed color draw",
        "valid": "0..9",
    },
    "frame_color": {
        "type": "color",
        "default": "keyed color draw distinct from background_color",
        "valid": "0..9",
    },
}


def _validate_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        errors.append("grid dimensions must be between 5 and 30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be literal ARC colors 0..9")
    return errors


def _border_values(grid):
    height, width = len(grid), len(grid[0])
    return (
        list(grid[0])
        + list(grid[height - 1])
        + [grid[row][0] for row in range(height)]
        + [grid[row][width - 1] for row in range(height)]
    )


def _components_excluding(grid, excluded):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == excluded:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == col_delta == 0:
                            continue
                        next_row = current_row + row_delta
                        next_col = current_col + col_delta
                        if not (0 <= next_row < height and 0 <= next_col < width):
                            continue
                        if (next_row, next_col) in seen:
                            continue
                        if grid[next_row][next_col] == excluded:
                            continue
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            components.append(cells)
    return components


def _filled_rectangle(cells):
    if not cells:
        return False
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return len(cells) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _analysis(grid):
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "output": None}

    height, width = len(grid), len(grid[0])
    border_counts = Counter(_border_values(grid))
    background = border_counts.most_common(1)[0][0]
    if any(value != background for value in _border_values(grid)):
        errors.append("the full outer border must use one background color")

    non_background_counts = Counter(
        value for row in grid for value in row if value != background
    )
    if not non_background_counts:
        errors.append("no non-background field color found")
        return {"errors": errors, "facts": None, "output": None}
    frame, frame_count = non_background_counts.most_common(1)[0]
    if frame == background:
        errors.append("frame color must differ from the background color")

    components = _components_excluding(grid, frame)
    outside = []
    rooms = []
    for cells in components:
        bordering = any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        )
        (outside if bordering else rooms).append(cells)
    if len(outside) != 1:
        errors.append(f"expected one outside component, found {len(outside)}")
    if len(rooms) < 4:
        errors.append(f"expected at least four enclosed rooms, found {len(rooms)}")

    room_records = []
    for cells in rooms:
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        if not _filled_rectangle(cells):
            errors.append(f"room at {bbox} is not a filled rectangle")
        marker_cells = [
            (row, col)
            for row, col in cells
            if grid[row][col] != background
        ]
        marker_colors = {grid[row][col] for row, col in marker_cells}
        if len(marker_colors) > 1:
            errors.append(f"room at {bbox} contains multiple marker colors")
        if marker_cells and not _filled_rectangle(marker_cells):
            errors.append(f"marker in room at {bbox} is not a solid rectangle")
        marker = next(iter(marker_colors), background)
        room_records.append(
            {
                "bbox": bbox,
                "height": bbox[2] - bbox[0] + 1,
                "width": bbox[3] - bbox[1] + 1,
                "marker": marker,
                "marker_size": len(marker_cells),
            }
        )

    row_starts = sorted({record["bbox"][0] for record in room_records})
    col_starts = sorted({record["bbox"][1] for record in room_records})
    by_position = {
        (record["bbox"][0], record["bbox"][1]): record
        for record in room_records
    }
    expected_positions = {
        (row_start, col_start)
        for row_start in row_starts
        for col_start in col_starts
    }
    if set(by_position) != expected_positions:
        errors.append("enclosed rooms do not form a complete rectangular matrix")

    row_heights = []
    for row_start in row_starts:
        heights = {
            record["height"]
            for (candidate_row, _), record in by_position.items()
            if candidate_row == row_start
        }
        if len(heights) != 1:
            errors.append(f"rooms in matrix row {row_start} have inconsistent heights")
        row_heights.append(next(iter(heights), 0))
    col_widths = []
    for col_start in col_starts:
        widths = {
            record["width"]
            for (_, candidate_col), record in by_position.items()
            if candidate_col == col_start
        }
        if len(widths) != 1:
            errors.append(f"rooms in matrix column {col_start} have inconsistent widths")
        col_widths.append(next(iter(widths), 0))

    output = [
        [by_position[(row_start, col_start)]["marker"] for col_start in col_starts]
        for row_start in row_starts
        if all((row_start, col_start) in by_position for col_start in col_starts)
    ]
    marker_sizes = [record["marker_size"] for record in room_records if record["marker_size"]]
    marker_count = len(marker_sizes)
    empty_count = len(room_records) - marker_count
    if marker_count == 0:
        errors.append("at least one room must contain a marker")
    if empty_count == 0:
        errors.append("at least one room must be empty to teach the background fallback")
    if frame_count <= max((count for color, count in non_background_counts.items() if color != frame), default=0):
        errors.append("field color is not the dominant non-background color")

    lattice_shape = (
        f"{len(row_starts)}x{len(col_starts)}"
        if row_starts and col_starts
        else None
    )
    room_rows_vary = len(set(row_heights)) > 1
    room_cols_vary = len(set(col_widths)) > 1
    total_rooms = len(room_records)
    scene_profile = None
    if (
        not room_rows_vary
        and not room_cols_vary
        and marker_count == 1
        and marker_sizes == [1]
    ):
        scene_profile = "sparse_uniform"
    elif (
        room_rows_vary
        and not room_cols_vary
        and marker_count == (total_rooms + 1) // 2
        and marker_sizes
        and all(size > 1 for size in marker_sizes)
    ):
        scene_profile = "mixed_rows"
    elif (
        not room_rows_vary
        and room_cols_vary
        and marker_count == (total_rooms + 1) // 2
        and 1 in marker_sizes
        and any(size > 1 for size in marker_sizes)
    ):
        scene_profile = "mixed_columns"
    elif (
        room_rows_vary
        and room_cols_vary
        and marker_count == total_rooms - 1
        and 1 in marker_sizes
        and any(size > 1 for size in marker_sizes)
    ):
        scene_profile = "dense_varied"

    facts = {
        "background_color": background,
        "frame_color": frame,
        "lattice_shape": lattice_shape,
        "scene_profile": scene_profile,
        "row_heights": row_heights,
        "col_widths": col_widths,
        "room_count": total_rooms,
        "marked_room_count": marker_count,
        "empty_room_count": empty_count,
        "marker_sizes": marker_sizes,
        "room_records": room_records,
    }
    return {"errors": errors, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed lesson scenes while accepting every canonical input."""
    return _analysis(grid)["errors"]


def rule_mirror(grid):
    """Independent Python mirror used only for focused validation tests."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis["output"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    facts = analysis["facts"]
    if analysis["errors"] or not facts or facts["scene_profile"] not in SCENE_PROFILES:
        return {}
    return {
        "lattice_shape": facts["lattice_shape"],
        "scene_profile": facts["scene_profile"],
        "background_color": facts["background_color"],
        "frame_color": facts["frame_color"],
    }


def _weighted_shapes(difficulty):
    if difficulty == "easy":
        return ("2x2", "2x2", "2x2", "2x3", "3x2", "3x3")
    if difficulty == "hard":
        return ("2x2", "2x3", "3x2", "3x3", "3x3", "3x3")
    return ("2x2", "2x3", "3x2", "3x3")


def _room_dimensions(profile, room_rows, room_cols, rng):
    base_height = rng.randint(3, 5)
    base_width = rng.randint(3, 5)
    row_heights = [base_height] * room_rows
    col_widths = [base_width] * room_cols
    if profile in ("mixed_rows", "dense_varied"):
        row_heights = [base_height + (index % 2) for index in range(room_rows)]
    if profile in ("mixed_columns", "dense_varied"):
        col_widths = [base_width + (index % 2) for index in range(room_cols)]
    return row_heights, col_widths


def _marker_count(profile, total_rooms):
    if profile == "sparse_uniform":
        return 1
    if profile in ("mixed_rows", "mixed_columns"):
        return (total_rooms + 1) // 2
    return total_rooms - 1


def _marker_size(profile, marker_index, room_height, room_width, rng):
    if profile == "sparse_uniform":
        return 1, 1
    if profile == "mixed_rows":
        return rng.choice(((1, 2), (2, 1), (2, 2)))
    if profile == "mixed_columns":
        if marker_index == 0:
            return 1, 1
        return rng.choice(((1, 2), (2, 1), (2, 2)))
    if marker_index % 2 == 0:
        return 1, 1
    return rng.choice(((1, 2), (2, 1), (2, 2)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    shape = ctx.draw_choice("lattice_shape", _weighted_shapes(difficulty))
    profile_options = (
        SCENE_PROFILES
        if overrides.get("scene_profile") is not None
        else (SCENE_PROFILES[sample_index % len(SCENE_PROFILES)],)
    )
    profile = ctx.draw_choice("scene_profile", profile_options)
    if overrides.get("frame_color") is not None and overrides.get("background_color") is None:
        frame = ctx.draw_color("frame_color")
        background = ctx.draw_color("background_color", exclude=(frame,))
    else:
        background = ctx.draw_color("background_color")
        frame = ctx.draw_color("frame_color", exclude=(background,))
    room_rows, room_cols = (int(value) for value in shape.split("x"))

    layout_rng = ctx.draw_rng("layout")
    row_heights, col_widths = _room_dimensions(
        profile, room_rows, room_cols, layout_rng
    )
    separator = layout_rng.randint(1, 2)
    field_border = layout_rng.randint(1, 2)
    margin_top = layout_rng.randint(1, 2)
    margin_bottom = layout_rng.randint(1, 2)
    margin_left = layout_rng.randint(1, 2)
    margin_right = layout_rng.randint(1, 2)

    field_height = (
        2 * field_border
        + sum(row_heights)
        + separator * (room_rows - 1)
    )
    field_width = (
        2 * field_border
        + sum(col_widths)
        + separator * (room_cols - 1)
    )
    grid = full_grid(
        margin_top + field_height + margin_bottom,
        margin_left + field_width + margin_right,
        background,
    )
    for row in range(margin_top, margin_top + field_height):
        for col in range(margin_left, margin_left + field_width):
            grid[row][col] = frame

    room_boxes = []
    current_row = margin_top + field_border
    for room_height in row_heights:
        current_col = margin_left + field_border
        row_boxes = []
        for room_width in col_widths:
            for row in range(current_row, current_row + room_height):
                for col in range(current_col, current_col + room_width):
                    grid[row][col] = background
            row_boxes.append((current_row, current_col, room_height, room_width))
            current_col += room_width + separator
        room_boxes.append(row_boxes)
        current_row += room_height + separator

    total_rooms = room_rows * room_cols
    marked_count = _marker_count(profile, total_rooms)
    marked_positions = set(layout_rng.sample(range(total_rooms), marked_count))
    legal_markers = [
        color for color in range(10) if color not in (background, frame)
    ]
    marker_colors = layout_rng.sample(legal_markers, marked_count)
    marker_index = 0
    for flat_index in range(total_rooms):
        if flat_index not in marked_positions:
            continue
        room_row, room_col = divmod(flat_index, room_cols)
        top, left, room_height, room_width = room_boxes[room_row][room_col]
        marker_height, marker_width = _marker_size(
            profile, marker_index, room_height, room_width, layout_rng
        )
        marker_top = top + layout_rng.randint(0, room_height - marker_height)
        marker_left = left + layout_rng.randint(0, room_width - marker_width)
        marker_color = marker_colors[marker_index]
        for row in range(marker_top, marker_top + marker_height):
            for col in range(marker_left, marker_left + marker_width):
                grid[row][col] = marker_color
        marker_index += 1

    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError("constructed invalid scene: " + "; ".join(analysis["errors"]))
    observed = observe_overrides(grid)
    expected = {
        "lattice_shape": shape,
        "scene_profile": profile,
        "background_color": background,
        "frame_color": frame,
    }
    if observed != expected:
        raise AssertionError(f"constructed scene observed as {observed}, expected {expected}")
    return grid
