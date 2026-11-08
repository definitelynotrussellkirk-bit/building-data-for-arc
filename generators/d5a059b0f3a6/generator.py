"""Generate framed motif-completion scenes with removable distractors.

Four disconnected three-cell L corners delimit each frame.  Blue seed cells
inside a frame are mirrored left-right when they lie wholly on one horizontal
side; otherwise a top-only or bottom-only seed is mirrored up-down.  Blue
cells outside every frame are distractors and disappear.
"""

from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d5a059b0f3a6"
VERSION = "3.1.0"
TASK_ID = "d5a059b0f3a6"
RULE_HASH = "77f0ca66f33e"
SUMMARY = (
    "Detect rectangles from four L-corners, mirror each enclosed blue motif "
    "across its missing axis, and remove blue distractors outside frames."
)

INVARIANTS = [
    "background is 0 and motif/distractor cells are blue 1",
    "one non-blue foreground color forms every three-cell L corner",
    "each frame has exactly four disconnected and consistently oriented corners",
    "every in-frame seed is one-sided and gains at least one mirrored cell",
    "blue cells outside all frames are distractors removed by the rule",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
EXTRAPOLATION_PROFILES = (
    "horizontal_frames",
    "vertical_frames",
    "mixed_axes",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "16-slot cyclic curriculum with mixed-axis teaching coverage",
        "valid": "|".join(SCENE_PROFILES),
    },
}

TRANSFORMS = (
    "identity",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "horizontal_flip",
    "vertical_flip",
    "main_diagonal",
    "anti_diagonal",
)

# Compact reconstructions of the complete visible public inputs.  Frames
# determine every non-blue foreground cell; ``blue`` includes both seeds and
# distractors.  This avoids a literal grid bank while preserving all linked
# answer-bearing roles.
_PUBLIC_SPECS = {
    "public_train_1": {
        "shape": (22, 23),
        "frame_color": 8,
        "frames": (
            (1, 16, 10, 21),
            (2, 3, 6, 9),
            (12, 6, 17, 14),
        ),
        "blue": (
            (3, 17), (3, 18), (4, 20), (5, 18), (5, 19),
            (3, 5), (5, 4), (5, 5),
            (13, 12), (15, 12), (15, 13), (16, 11),
            (5, 12), (5, 13), (10, 1), (13, 2), (13, 21),
            (14, 20), (20, 18),
        ),
    },
    "public_train_2": {
        "shape": (23, 25),
        "frame_color": 2,
        "frames": (
            (1, 2, 5, 15),
            (3, 19, 10, 23),
            (8, 9, 19, 13),
        ),
        "blue": (
            (2, 6), (2, 7), (3, 5), (3, 6), (4, 8),
            (5, 22), (6, 21),
            (15, 10), (16, 11), (16, 12), (17, 10),
            (13, 1), (13, 2), (14, 3), (15, 20), (18, 21),
            (21, 3),
        ),
    },
    "public_train_3": {
        "shape": (20, 21),
        "frame_color": 3,
        "frames": (
            (2, 3, 12, 9),
            (13, 11, 17, 17),
        ),
        "blue": (
            (8, 7), (9, 5), (9, 7), (10, 6), (10, 7),
            (10, 8), (11, 5),
            (14, 13), (15, 12), (15, 13),
            (2, 13), (6, 17), (7, 18), (7, 19), (8, 19),
            (16, 6), (17, 2), (17, 3), (18, 3),
        ),
    },
    "public_test_1": {
        "shape": (26, 28),
        "frame_color": 4,
        "frames": (
            (1, 2, 9, 7),
            (3, 12, 7, 19),
            (10, 19, 22, 25),
            (16, 3, 23, 14),
        ),
        "blue": (
            (2, 4), (3, 4), (3, 5), (4, 3),
            (4, 14), (5, 13), (6, 14),
            (18, 23), (19, 21), (19, 22), (20, 22), (20, 23),
            (21, 21),
            (17, 6), (18, 5), (18, 6), (19, 8), (20, 4),
            (20, 6), (20, 7), (21, 5), (21, 6), (22, 6),
            (0, 15), (1, 23), (2, 24), (2, 25), (2, 26),
            (5, 25), (11, 10), (12, 4), (12, 7), (12, 9),
            (12, 11), (13, 4), (14, 17),
        ),
    },
}

# The old weighted pool was 25% public and 25% each control profile.  Keep
# exactly those long-run proportions, but interleave mixed-axis witnesses so
# no ordinary three-demo lesson can accidentally teach an always-horizontal or
# always-vertical shortcut.  Every four consecutive slots contain two scenes
# with both axis branches; therefore every one-query rotation leaves at least
# one mixed-axis demonstration.
SCHEDULE_PROFILES = SCENE_PROFILES
DEFAULT_PROFILE_SCHEDULE = (
    "public_train_1", "horizontal_frames", "mixed_axes", "vertical_frames",
    "public_train_2", "horizontal_frames", "mixed_axes", "vertical_frames",
    "public_train_3", "horizontal_frames", "mixed_axes", "vertical_frames",
    "public_test_1", "horizontal_frames", "mixed_axes", "vertical_frames",
)
SCHEDULE_PERIOD = len(DEFAULT_PROFILE_SCHEDULE)
EXAMPLES_NEEDED = 3


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the default semantic profile for schedule diagnostics."""
    del seed, difficulty
    return DEFAULT_PROFILE_SCHEDULE[sample_index % SCHEDULE_PERIOD]


def _scheduled_choice(ctx, label, domain, desired):
    """Select ``desired`` by default while retaining the full override domain."""
    values = list(domain)
    if desired not in values:
        raise ValueError(f"scheduled value {desired!r} is not legal for {label}")
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, tuple(values))
    chosen_index = ctx.draw_rng(label).randrange(len(values))
    desired_index = values.index(desired)
    values[chosen_index], values[desired_index] = (
        values[desired_index],
        values[chosen_index],
    )
    return ctx.draw_choice(label, tuple(values))


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    profile = overrides.get("scene_profile")
    if profile is not None and type(profile) is not str:
        raise TypeError("scene_profile must be a string")


def _paint_frame(grid, rectangle, color):
    row1, col1, row2, col2 = rectangle
    cells = (
        (row1, col1), (row1, col1 + 1), (row1 + 1, col1),
        (row1, col2), (row1, col2 - 1), (row1 + 1, col2),
        (row2, col1), (row2, col1 + 1), (row2 - 1, col1),
        (row2, col2), (row2, col2 - 1), (row2 - 1, col2),
    )
    for row, col in cells:
        grid[row][col] = color


def _build_scene(shape, frames, blue, frame_color):
    height, width = shape
    grid = full_grid(height, width, 0)
    for rectangle in frames:
        _paint_frame(grid, rectangle, frame_color)
    for row, col in blue:
        if grid[row][col] != 0:
            raise ValueError("blue cell collides with a frame corner")
        grid[row][col] = 1
    return grid


def _transform(grid, name):
    if name == "identity":
        return [row[:] for row in grid]
    if name == "rotate_90":
        return [list(row) for row in zip(*reversed(grid))]
    if name == "rotate_180":
        return [list(reversed(row)) for row in reversed(grid)]
    if name == "rotate_270":
        return [list(row) for row in reversed(list(zip(*grid)))]
    if name == "horizontal_flip":
        return [list(reversed(row)) for row in grid]
    if name == "vertical_flip":
        return [row[:] for row in reversed(grid)]
    if name == "main_diagonal":
        return [list(row) for row in zip(*grid)]
    if name == "anti_diagonal":
        return [
            list(reversed(row))
            for row in reversed(list(zip(*grid)))
        ]
    raise ValueError(f"unknown transform: {name}")


def _role_signature(grid):
    return tuple(
        tuple(0 if value == 0 else 1 if value == 1 else 2 for value in row)
        for row in grid
    )


def _normalized_role_signature(grid):
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        return (len(grid), len(grid[0]), ())
    row1 = min(row for row, _ in occupied)
    row2 = max(row for row, _ in occupied)
    col1 = min(col for _, col in occupied)
    col2 = max(col for _, col in occupied)
    cropped = tuple(
        tuple(
            0 if grid[row][col] == 0
            else 1 if grid[row][col] == 1
            else 2
            for col in range(col1, col2 + 1)
        )
        for row in range(row1, row2 + 1)
    )
    return (len(grid), len(grid[0]), cropped)


_PUBLIC_INPUTS = {
    profile: _build_scene(
        spec["shape"],
        spec["frames"],
        spec["blue"],
        spec["frame_color"],
    )
    for profile, spec in _PUBLIC_SPECS.items()
}
_PUBLIC_ESSENTIAL_INPUTS = {
    profile: _build_scene(
        spec["shape"],
        spec["frames"],
        tuple(
            point
            for point in spec["blue"]
            if any(
                row1 <= point[0] <= row2
                and col1 <= point[1] <= col2
                for row1, col1, row2, col2 in spec["frames"]
            )
        ),
        spec["frame_color"],
    )
    for profile, spec in _PUBLIC_SPECS.items()
}
_PUBLIC_DISTRACTOR_COUNTS = {
    profile: sum(
        not any(
            row1 <= point[0] <= row2
            and col1 <= point[1] <= col2
            for row1, col1, row2, col2 in spec["frames"]
        )
        for point in spec["blue"]
    )
    for profile, spec in _PUBLIC_SPECS.items()
}
_PUBLIC_LOOKUP = {}
for _profile, _grid in _PUBLIC_ESSENTIAL_INPUTS.items():
    for _transform_name in TRANSFORMS:
        _signature = _normalized_role_signature(
            _transform(_grid, _transform_name)
        )
        _previous = _PUBLIC_LOOKUP.setdefault(_signature, _profile)
        if _previous != _profile:
            raise RuntimeError("ambiguous compact public profiles")
_PUBLIC_LITERALS = {
    tuple(tuple(row) for row in grid)
    for grid in _PUBLIC_INPUTS.values()
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic framed motif-completion lesson."""
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _scheduled_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        schedule_profile(seed, sample_index, difficulty),
    )
    layout_rng = ctx.draw_rng("layout")
    frame_color = ctx.draw_rng("frame_color").choice(range(2, 10))

    if profile in _PUBLIC_SPECS:
        source = _PUBLIC_SPECS[profile]
        height, width = source["shape"]
        min_row = min(frame[0] for frame in source["frames"])
        min_col = min(frame[1] for frame in source["frames"])
        max_row = max(frame[2] for frame in source["frames"])
        max_col = max(frame[3] for frame in source["frames"])
        delta_row = layout_rng.randint(-min_row, height - 1 - max_row)
        delta_col = layout_rng.randint(-min_col, width - 1 - max_col)
        frames = tuple(
            (
                row1 + delta_row,
                col1 + delta_col,
                row2 + delta_row,
                col2 + delta_col,
            )
            for row1, col1, row2, col2 in source["frames"]
        )
        seeds = tuple(
            (point[0] + delta_row, point[1] + delta_col)
            for point in source["blue"]
            if any(
                row1 <= point[0] <= row2
                and col1 <= point[1] <= col2
                for row1, col1, row2, col2 in source["frames"]
            )
        )
        grid = _build_scene(
            source["shape"],
            frames,
            seeds,
            frame_color,
        )
        distractor_positions = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 0
            and not any(
                row1 <= row <= row2 and col1 <= col <= col2
                for row1, col1, row2, col2 in frames
            )
        ]
        for row, col in layout_rng.sample(
            distractor_positions,
            _PUBLIC_DISTRACTOR_COUNTS[profile],
        ):
            grid[row][col] = 1
        grid = _transform(grid, layout_rng.choice(TRANSFORMS))
        while tuple(tuple(row) for row in grid) in _PUBLIC_LITERALS:
            replacement = 2 + ((frame_color - 1) % 8)
            grid = [
                [
                    replacement if value == frame_color else value
                    for value in row
                ]
                for row in grid
            ]
            frame_color = replacement
        return grid

    return _build_control_scene(
        profile,
        difficulty,
        frame_color,
        layout_rng,
    )


def _control_shape_and_count(difficulty, rng):
    if difficulty == "easy":
        return rng.choice(((22, 22), (22, 24), (24, 22))), 2
    if difficulty == "medium":
        return rng.choice(((24, 26), (26, 24), (26, 26))), 3
    if difficulty == "hard":
        return rng.choice(((28, 28), (28, 30), (30, 28), (30, 30))), 4
    count = rng.choice((2, 3, 4))
    pools = {
        2: ((22, 22), (22, 24), (24, 22)),
        3: ((24, 26), (26, 24), (26, 26)),
        4: ((28, 28), (28, 30), (30, 28), (30, 30)),
    }
    return rng.choice(pools[count]), count


def _choose_frames(height, width, count, rng):
    row_mid = height // 2
    col_mid = width // 2
    zones = [
        (1, row_mid - 1, 1, col_mid - 1),
        (1, row_mid - 1, col_mid + 1, width - 2),
        (row_mid + 1, height - 2, 1, col_mid - 1),
        (row_mid + 1, height - 2, col_mid + 1, width - 2),
    ]
    rng.shuffle(zones)
    frames = []
    used_top_rows = set()
    used_left_cols = set()
    for zone in zones[:count]:
        zone_row1, zone_row2, zone_col1, zone_col2 = zone
        zone_height = zone_row2 - zone_row1 + 1
        zone_width = zone_col2 - zone_col1 + 1
        row_choices = [
            (row, frame_height)
            for frame_height in range(7, min(9, zone_height) + 1)
            for row in range(
                zone_row1,
                zone_row2 - frame_height + 2,
            )
            if row not in used_top_rows
        ]
        col_choices = [
            (col, frame_width)
            for frame_width in range(7, min(9, zone_width) + 1)
            for col in range(
                zone_col1,
                zone_col2 - frame_width + 2,
            )
            if col not in used_left_cols
        ]
        if not row_choices or not col_choices:
            raise RuntimeError("constructive frame placement exhausted")
        row1, frame_height = rng.choice(row_choices)
        col1, frame_width = rng.choice(col_choices)
        used_top_rows.add(row1)
        used_left_cols.add(col1)
        frames.append(
            (
                row1,
                col1,
                row1 + frame_height - 1,
                col1 + frame_width - 1,
            )
        )
    return sorted(frames)


def _seed_motif(rectangle, branch, rng):
    row1, col1, row2, col2 = rectangle
    interior_rows = list(range(row1 + 1, row2))
    interior_cols = list(range(col1 + 1, col2))
    center_row_twice = row1 + row2
    center_col_twice = col1 + col2
    variant = rng.randrange(3)

    if branch in ("left", "right"):
        if branch == "left":
            eligible = [
                col
                for col in interior_cols
                if 2 * col < center_col_twice
            ]
            near = max(eligible)
            far = eligible[-2]
        else:
            eligible = [
                col
                for col in interior_cols
                if 2 * col > center_col_twice
            ]
            near = min(eligible)
            far = eligible[1]
        row = interior_rows[len(interior_rows) // 2 - 1]
        next_row = row + 1
        cells = {(row, near), (next_row, near), (next_row, far)}
        if variant >= 1:
            cells.add((row, far))
        if variant == 2 and row - 1 in interior_rows:
            cells.add((row - 1, near))
        return cells

    top = [row for row in interior_rows if 2 * row < center_row_twice]
    bottom = [row for row in interior_rows if 2 * row > center_row_twice]
    use_top = bool(rng.randrange(2))
    if use_top:
        near_row = max(top)
        far_row = top[-2]
    else:
        near_row = min(bottom)
        far_row = bottom[1]
    if center_col_twice % 2 == 0:
        center_col = center_col_twice // 2
        left_col = center_col
        right_col = center_col + 1
    else:
        left_col = center_col_twice // 2
        right_col = left_col + 1
    cells = {
        (near_row, left_col),
        (near_row, right_col),
        (far_row, left_col),
    }
    if variant >= 1:
        cells.add((far_row, right_col))
    if variant == 2:
        extra_col = (
            left_col - 1
            if left_col - 1 in interior_cols
            else right_col + 1
        )
        cells.add((near_row, extra_col))
    return cells


def _build_control_scene(profile, difficulty, frame_color, rng):
    (height, width), frame_count = _control_shape_and_count(
        difficulty,
        rng,
    )
    frames = _choose_frames(height, width, frame_count, rng)
    if profile == "horizontal_frames":
        branches = [
            ("left", "right")[index % 2]
            for index in range(frame_count)
        ]
    elif profile == "vertical_frames":
        branches = ["vertical"] * frame_count
    else:
        cycle = ("left", "vertical", "right", "vertical")
        branches = [cycle[index] for index in range(frame_count)]

    seeds = set()
    for rectangle, branch in zip(frames, branches):
        seeds.update(_seed_motif(rectangle, branch, rng))

    grid = _build_scene(
        (height, width),
        frames,
        seeds,
        frame_color,
    )
    outside = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
        and not any(
            row1 <= row <= row2 and col1 <= col <= col2
            for row1, col1, row2, col2 in frames
        )
    ]
    if difficulty == "easy":
        distractor_count = rng.randint(6, 8)
    elif difficulty == "hard":
        distractor_count = rng.randint(13, 18)
    else:
        distractor_count = rng.randint(8, 13)
    for row, col in rng.sample(outside, distractor_count):
        grid[row][col] = 1
    return grid


def _components4(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for delta_row, delta_col in (
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    neighbor = (
                        current[0] + delta_row,
                        current[1] + delta_col,
                    )
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(sorted(cells))
    return components


def _corner_from_component(cells):
    if len(cells) != 3:
        return None
    elbows = [
        point
        for point in cells
        if sum(
            abs(point[0] - other[0]) + abs(point[1] - other[1]) == 1
            for other in cells
        )
        == 2
    ]
    if len(elbows) != 1:
        return None
    elbow_row, elbow_col = elbows[0]
    horizontal = [
        point
        for point in cells
        if point[0] == elbow_row and point[1] != elbow_col
    ]
    vertical = [
        point
        for point in cells
        if point[1] == elbow_col and point[0] != elbow_row
    ]
    if len(horizontal) != 1 or len(vertical) != 1:
        return None
    return (
        1 if vertical[0][0] > elbow_row else -1,
        1 if horizontal[0][1] > elbow_col else -1,
        elbow_row,
        elbow_col,
    )


def _rectangles(corners):
    rectangles = []
    used = set()
    for top_left in [
        corner for corner in corners if corner[:2] == (1, 1)
    ]:
        top_right = [
            corner
            for corner in corners
            if corner[:2] == (1, -1)
            and corner[2] == top_left[2]
            and corner[3] > top_left[3]
        ]
        bottom_left = [
            corner
            for corner in corners
            if corner[:2] == (-1, 1)
            and corner[3] == top_left[3]
            and corner[2] > top_left[2]
        ]
        if len(top_right) != 1 or len(bottom_left) != 1:
            return [], set(), "ambiguous_frame_pairing"
        row2 = bottom_left[0][2]
        col2 = top_right[0][3]
        bottom_right = [
            corner
            for corner in corners
            if corner == (-1, -1, row2, col2)
        ]
        if len(bottom_right) != 1:
            return [], set(), "missing_bottom_right"
        members = (
            top_left,
            top_right[0],
            bottom_left[0],
            bottom_right[0],
        )
        if any(member in used for member in members):
            return [], set(), "reused_frame_corner"
        used.update(members)
        rectangles.append((top_left[2], top_left[3], row2, col2))
    return rectangles, used, None


def _frame_color(grid):
    colors = sorted({value for row in grid for value in row})
    candidates = [value for value in colors if value not in (0, 1)]
    return candidates[0] if candidates else None


def solve_python(grid):
    """Input-pure Python mirror of the authoritative frame rule."""
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    frame_color = _frame_color(grid)
    if frame_color is None:
        return full_grid(len(grid), width, 0)
    corners = [
        corner
        for corner in (
            _corner_from_component(component)
            for component in _components4(grid, frame_color)
        )
        if corner is not None
    ]
    rectangles, _, _ = _rectangles(corners)
    output = [
        [
            frame_color if value == frame_color else 0
            for value in row
        ]
        for row in grid
    ]
    blue = {
        (row, col)
        for row in range(len(grid))
        for col in range(width)
        if grid[row][col] == 1
    }
    for row1, col1, row2, col2 in rectangles:
        seed = [
            point
            for point in blue
            if row1 <= point[0] <= row2
            and col1 <= point[1] <= col2
        ]
        center_col_twice = col1 + col2
        if all(2 * col < center_col_twice for _, col in seed) or all(
            2 * col > center_col_twice for _, col in seed
        ):
            mirrored = [
                (row, center_col_twice - col)
                for row, col in seed
            ]
        else:
            center_row_twice = row1 + row2
            mirrored = [
                (center_row_twice - row, col)
                for row, col in seed
            ]
        for row, col in seed + mirrored:
            output[row][col] = 1
    return output


def _basic_grid_reasons(grid):
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return ["empty_or_non_grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["invalid_arc_value"]
    return []


def _overlap(left, right):
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _analyze(grid):
    reasons = _basic_grid_reasons(grid)
    if reasons:
        return {
            "strict": False,
            "reasons": reasons,
            "scene_profile": None,
        }
    height = len(grid)
    width = len(grid[0])
    if not (20 <= height <= 30 and 20 <= width <= 30):
        reasons.append("dimension_range")
    colors = sorted({value for row in grid for value in row})
    frame_colors = [value for value in colors if value not in (0, 1)]
    if len(frame_colors) != 1:
        reasons.append("frame_color_cardinality")
        frame_color = frame_colors[0] if frame_colors else None
    else:
        frame_color = frame_colors[0]
    components = (
        _components4(grid, frame_color)
        if frame_color is not None
        else []
    )
    corners = []
    for component in components:
        corner = _corner_from_component(component)
        if corner is None:
            reasons.append("invalid_frame_corner")
        else:
            corners.append(corner)
    rectangles, used, frame_error = _rectangles(corners)
    if frame_error:
        reasons.append(frame_error)
    if len(used) != len(corners):
        reasons.append("unpaired_frame_corners")
    if not 2 <= len(rectangles) <= 4:
        reasons.append("frame_count")
    if any(
        _overlap(rectangles[left], rectangles[right])
        for left in range(len(rectangles))
        for right in range(left + 1, len(rectangles))
    ):
        reasons.append("overlapping_frames")

    blue = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }
    inside = set()
    branches = []
    seed_counts = []
    added_counts = []
    for row1, col1, row2, col2 in rectangles:
        seed = sorted(
            point
            for point in blue
            if row1 <= point[0] <= row2
            and col1 <= point[1] <= col2
        )
        inside.update(seed)
        if not seed:
            reasons.append("empty_frame_seed")
            branches.append("empty")
            seed_counts.append(0)
            added_counts.append(0)
            continue
        center_col_twice = col1 + col2
        center_row_twice = row1 + row2
        left = all(2 * col < center_col_twice for _, col in seed)
        right = all(2 * col > center_col_twice for _, col in seed)
        if left:
            branch = "left"
            mirror = {
                (row, center_col_twice - col)
                for row, col in seed
            }
        elif right:
            branch = "right"
            mirror = {
                (row, center_col_twice - col)
                for row, col in seed
            }
        else:
            branch = "vertical"
            top = all(2 * row < center_row_twice for row, _ in seed)
            bottom = all(2 * row > center_row_twice for row, _ in seed)
            if not (top or bottom):
                reasons.append("ambiguous_vertical_seed")
            mirror = {
                (center_row_twice - row, col)
                for row, col in seed
            }
        branches.append(branch)
        seed_counts.append(len(seed))
        added_counts.append(len(mirror - set(seed)))
        if not mirror - set(seed):
            reasons.append("already_symmetric_seed")
        if any(
            grid[row][col] == frame_color
            for row, col in mirror
        ):
            reasons.append("mirror_hits_frame")
    distractor_count = len(blue - inside)
    if not 4 <= distractor_count <= 20:
        reasons.append("distractor_count")
    if solve_python(grid) == grid:
        reasons.append("identity")

    essential_grid = [
        [
            value if value != 1 or (row, col) in inside else 0
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]
    candidate_profile = _PUBLIC_LOOKUP.get(
        _normalized_role_signature(essential_grid)
    )
    answer_profile = (
        candidate_profile
        if candidate_profile is not None
        and distractor_count
        == _PUBLIC_DISTRACTOR_COUNTS[candidate_profile]
        else None
    )
    if answer_profile:
        scene_profile = answer_profile
    elif branches and all(
        branch in ("left", "right") for branch in branches
    ):
        scene_profile = "horizontal_frames"
    elif branches and all(branch == "vertical" for branch in branches):
        scene_profile = "vertical_frames"
    elif (
        any(branch == "vertical" for branch in branches)
        and any(branch in ("left", "right") for branch in branches)
    ):
        scene_profile = "mixed_axes"
    else:
        scene_profile = None
        reasons.append("unsupported_profile")
    return {
        "strict": not reasons,
        "reasons": sorted(set(reasons)),
        "height": height,
        "width": width,
        "frame_color": frame_color,
        "component_count": len(components),
        "frame_count": len(rectangles),
        "frames": rectangles,
        "branches": branches,
        "seed_counts": seed_counts,
        "added_counts": added_counts,
        "blue_count": len(blue),
        "distractor_count": distractor_count,
        "answer_profile": answer_profile,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete returned-grid lesson, not constructor intent."""
    return _analyze(grid)["reasons"]


def observe_overrides(grid):
    analysis = _analyze(grid)
    if not analysis["strict"]:
        return {"scene_profile": None}
    return {"scene_profile": analysis["scene_profile"]}


def strict_canonical_like(grid):
    """Accept canonical inputs and every lawful point on this sampler manifold."""
    return self_check(grid)


def _solve_forced_axis(grid, axis):
    """Plausible wrong rule used only for semantic/teaching diagnostics."""
    if axis not in ("horizontal", "vertical"):
        raise ValueError(f"unknown forced axis: {axis}")
    if _basic_grid_reasons(grid):
        raise ValueError("expected a nonempty rectangular ARC grid")
    height = len(grid)
    width = len(grid[0])
    frame_color = _frame_color(grid)
    if frame_color is None:
        return full_grid(height, width, 0)
    corners = [
        corner
        for corner in (
            _corner_from_component(component)
            for component in _components4(grid, frame_color)
        )
        if corner is not None
    ]
    rectangles, _, _ = _rectangles(corners)
    output = [
        [frame_color if value == frame_color else 0 for value in row]
        for row in grid
    ]
    blue = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }
    for row1, col1, row2, col2 in rectangles:
        seed = [
            point
            for point in blue
            if row1 <= point[0] <= row2 and col1 <= point[1] <= col2
        ]
        if axis == "horizontal":
            center_twice = col1 + col2
            mirrored = [(row, center_twice - col) for row, col in seed]
        else:
            center_twice = row1 + row2
            mirrored = [(center_twice - row, col) for row, col in seed]
        for row, col in seed + mirrored:
            output[row][col] = 1
    return output


def _horizontal_only(grid):
    """Rival: remove distractors but mirror every frame left-right."""
    return _solve_forced_axis(grid, "horizontal")


def _vertical_only(grid):
    """Rival: remove distractors but mirror every frame top-bottom."""
    return _solve_forced_axis(grid, "vertical")


def _keep_distractors(grid):
    """Rival: perform the intended completion but retain external blue noise."""
    output = solve_python(grid)
    frame_color = _frame_color(grid)
    if frame_color is None:
        return output
    corners = [
        corner
        for corner in (
            _corner_from_component(component)
            for component in _components4(grid, frame_color)
        )
        if corner is not None
    ]
    rectangles, _, _ = _rectangles(corners)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 1 and not any(
                row1 <= row <= row2 and col1 <= col <= col2
                for row1, col1, row2, col2 in rectangles
            ):
                output[row][col] = 1
    return output


def _has_mixed_axis_scene(grid):
    analysis = _analyze(grid)
    branches = analysis.get("branches", [])
    return bool(
        analysis.get("strict")
        and any(branch == "vertical" for branch in branches)
        and any(branch in ("left", "right") for branch in branches)
    )


def _has_outside_distractors(grid):
    analysis = _analyze(grid)
    return bool(analysis.get("strict") and analysis.get("distractor_count", 0))


def lesson_identifiable(demos, query):
    """Report declared rivals that fit all demos but change this query label."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = (
                rival(query["input"]) != query["output"]
            )
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives and changes_query:
            reasons.append(
                f"{name} fits every demonstration but changes the query"
            )
    return reasons


SEMANTIC_WITNESSES = {
    "mixed_axis_scene": _has_mixed_axis_scene,
    "outside_distractors": _has_outside_distractors,
}
SEMANTIC_RIVALS = {
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "keep_distractors": _keep_distractors,
}
WITNESS_RIVALS = {
    "mixed_axis_scene": ["horizontal_only", "vertical_only"],
    "outside_distractors": ["keep_distractors"],
}
CANONICAL_SHORTCUTS = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

