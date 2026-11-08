"""Generator for ARC task e1d2900e / rule family 0bd65c18b34c.

Every red object is an exact 2x2 square.  Each blue dot chooses the nearest
red square by Chebyshev distance to that square's cells (row-major square
order breaks ties).  A dot aligned with one of the nearest square's two rows
or columns teleports to the corresponding outside edge; a dot unaligned with
its nearest square stays put.  All original blue cells are cleared before the
targets are painted.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0bd65c18b34c"
TASK_ID = "0bd65c18b34c"
VERSION = "3.0.0"
RULE_HASH = "9cd282956b9a"

SUMMARY = (
    "On the demonstrated compact or 30x30 scene, move each blue dot only "
    "when it shares a row or column with its nearest exact 2x2 red square. "
    "The dot teleports to hug that square; unaligned dots stay, and a "
    "two-square distance tie uses the first square in row-major order."
)

INVARIANTS = [
    "the palette is exactly 0, 1, 2 and every red object is an exact 2x2 square",
    "the complete compact/two-square/four-square public movement profile is preserved",
    "both moving and unaligned-staying blue dots occur in every scene",
    "all snap targets are in bounds, outside red squares, and pairwise unique",
    "the four-square balanced profile contains the published nearest-square tie lesson",
]

SCENE_PROFILES = (
    "large_two",
    "large_four_balanced",
    "compact_two",
    "large_four_stay",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform over four published profiles",
        "valid": (
            "large_two|large_four_balanced|compact_two|large_four_stay"
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
_CARDINAL_MODES = ("left", "right", "up", "down")

# Requirements are indexed by row-major square order.  These are the linked
# nearest-square/movement counts in the four unique public inputs.
_PROFILE_REQUIREMENTS = {
    "large_two": (
        {"up": 1, "left": 1, "right": 1, "down": 1},
        {"up": 1, "right": 1, "down": 1, "stay": 4},
    ),
    "large_four_balanced": (
        {"left": 1, "right": 1, "down": 1},
        {"up": 1, "left": 1, "right": 1, "down": 1, "stay": 1},
        {"up": 1, "left": 1, "right": 1, "stay": 1},
        {"up": 1, "down": 1},
    ),
    "compact_two": (
        {"right": 1, "stay": 1},
        {"left": 1},
    ),
    "large_four_stay": (
        {"up": 1, "right": 1, "down": 1, "stay": 1},
        {"up": 1, "left": 1, "right": 1, "stay": 1},
        {"up": 1, "left": 1, "right": 1, "stay": 2},
        {"left": 1, "stay": 1},
    ),
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    width = len(grid[0]) if isinstance(grid[0], (list, tuple)) else 0
    if width == 0:
        return None, ["grid must have nonempty rows"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in (0, 1, 2)
            ):
                errors.append("all cells must be integer colors 0, 1, or 2")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _squares_of(grid):
    height = len(grid)
    width = len(grid[0])
    return [
        (row, col)
        for row in range(height - 1)
        for col in range(width - 1)
        if all(
            grid[rr][cc] == 2
            for rr in (row, row + 1)
            for cc in (col, col + 1)
        )
    ]


def _exact_square_cover(grid, squares):
    red_cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    cover = Counter(
        (row, col)
        for top, left in squares
        for row in (top, top + 1)
        for col in (left, left + 1)
    )
    return set(cover) == red_cells and all(
        count == 1 for count in cover.values()
    )


def _cheby_distance(row, col, square_row, square_col):
    row_delta = max(
        0,
        square_row - row,
        row - (square_row + 1),
    )
    col_delta = max(
        0,
        square_col - col,
        col - (square_col + 1),
    )
    return max(row_delta, col_delta)


def _dot_info(height, width, squares, row, col):
    distances = [
        _cheby_distance(row, col, square_row, square_col)
        for square_row, square_col in squares
    ]
    if not distances:
        return None
    minimum = min(distances)
    nearest_index = distances.index(minimum)
    tied_indices = tuple(
        index
        for index, distance in enumerate(distances)
        if distance == minimum
    )
    square_row, square_col = squares[nearest_index]
    if square_row <= row <= square_row + 1:
        if col < square_col:
            mode = "left"
            target = row, square_col - 1
        else:
            mode = "right"
            target = row, square_col + 2
    elif square_col <= col <= square_col + 1:
        if row < square_row:
            mode = "up"
            target = square_row - 1, col
        else:
            mode = "down"
            target = square_row + 2, col
    else:
        mode = "stay"
        target = row, col
    in_bounds = (
        0 <= target[0] < height and 0 <= target[1] < width
    )
    move_length = max(
        abs(target[0] - row),
        abs(target[1] - col),
    )
    return {
        "nearest_index": nearest_index,
        "distance": minimum,
        "tied_indices": tied_indices,
        "tie_count": len(tied_indices),
        "mode": mode,
        "target": target,
        "in_bounds": in_bounds,
        "move_length": move_length,
    }


def _profile_name(height, width, squares, dot_infos):
    n_squares = len(squares)
    n_dots = len(dot_infos)
    modes = Counter(info["mode"] for info in dot_infos)
    cardinal_counts = sorted(
        modes[mode] for mode in _CARDINAL_MODES
    )
    nearest_counts = sorted(
        Counter(
            info["nearest_index"] for info in dot_infos
        ).values()
    )
    tied_dots = sum(info["tie_count"] == 2 for info in dot_infos)
    higher_ties = any(info["tie_count"] > 2 for info in dot_infos)
    normalized_shape = tuple(sorted((height, width)))
    signature = (
        normalized_shape,
        n_squares,
        n_dots,
        modes["stay"],
        tuple(cardinal_counts),
        tuple(nearest_counts),
        tied_dots,
        higher_ties,
    )
    signatures = {
        (
            (30, 30),
            2,
            11,
            4,
            (1, 2, 2, 2),
            (4, 7),
            0,
            False,
        ): "large_two",
        (
            (30, 30),
            4,
            14,
            2,
            (3, 3, 3, 3),
            (2, 3, 4, 5),
            2,
            False,
        ): "large_four_balanced",
        (
            (10, 13),
            2,
            3,
            1,
            (0, 0, 1, 1),
            (1, 2),
            0,
            False,
        ): "compact_two",
        (
            (30, 30),
            4,
            15,
            5,
            (1, 3, 3, 3),
            (2, 4, 4, 5),
            0,
            False,
        ): "large_four_stay",
    }
    return signatures.get(signature)


def _scene_analysis(grid):
    coerced, errors = _coerce_grid(grid)
    if coerced is None:
        return None, {}, errors
    height = len(coerced)
    width = len(coerced[0])
    palette = {
        value for row in coerced for value in row
    }
    if palette != {0, 1, 2}:
        errors.append("palette must contain exactly colors 0, 1, and 2")
    if (height, width) not in ((30, 30), (10, 13), (13, 10)):
        errors.append(
            "shape must be 30x30 or a D4 orientation of 10x13"
        )

    squares = _squares_of(coerced)
    if not _exact_square_cover(coerced, squares):
        errors.append("red cells must form disjoint exact 2x2 squares")
    if len(squares) not in (2, 4):
        errors.append("scene must contain exactly two or four red squares")

    blues = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] == 1
    ]
    dot_infos = []
    targets = []
    red_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] == 2
    }
    for row, col in blues:
        info = _dot_info(
            height,
            width,
            squares,
            row,
            col,
        )
        if info is None:
            continue
        dot_infos.append(info)
        if not info["in_bounds"]:
            errors.append("every blue target must be in bounds")
        if info["target"] in red_cells:
            errors.append("blue targets must remain outside red squares")
        targets.append(info["target"])
    if len(targets) != len(set(targets)):
        errors.append("blue targets must be pairwise unique")
    if not any(info["mode"] == "stay" for info in dot_infos):
        errors.append("scene must include an unaligned staying dot")
    if not any(info["mode"] != "stay" for info in dot_infos):
        errors.append("scene must include an aligned moving dot")

    profile_name = _profile_name(
        height,
        width,
        squares,
        dot_infos,
    )
    if profile_name is None:
        errors.append(
            "returned scene must match a complete published movement profile"
        )
    features = {
        "height": height,
        "width": width,
        "squares": tuple(squares),
        "n_squares": len(squares),
        "blues": tuple(blues),
        "n_blues": len(blues),
        "dot_infos": tuple(dot_infos),
        "targets": tuple(targets),
        "mode_counts": Counter(
            info["mode"] for info in dot_infos
        ),
        "nearest_counts": Counter(
            info["nearest_index"] for info in dot_infos
        ),
        "tie_dots": sum(
            info["tie_count"] > 1 for info in dot_infos
        ),
        "scene_profile": profile_name,
        "profile_index": (
            SCENE_PROFILES.index(profile_name)
            if profile_name is not None
            else None
        ),
    }
    return coerced, features, errors


def self_check(grid, *, difficulty=None, meta=None):
    """Return strict returned-grid curriculum errors."""
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    """Recover the exact declared profile axis from a returned grid."""
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"scene_profile": features["scene_profile"]}


def _render_rule(grid, squares, blues):
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    for row, col in blues:
        output[row][col] = 0
    for row, col in blues:
        info = _dot_info(
            height,
            width,
            squares,
            row,
            col,
        )
        target_row, target_col = info["target"]
        output[target_row][target_col] = 1
    return output


def rule_mirror(grid):
    """Apply the canonical rule beyond the stricter curriculum profile."""
    coerced, errors = _coerce_grid(grid)
    if coerced is None:
        raise ValueError(
            "invalid blue-square input: " + "; ".join(errors)
        )
    squares = _squares_of(coerced)
    if not squares:
        raise ValueError("invalid blue-square input: no red square")
    blues = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 1
    ]
    height = len(coerced)
    width = len(coerced[0])
    for row, col in blues:
        info = _dot_info(
            height,
            width,
            squares,
            row,
            col,
        )
        if not info["in_bounds"]:
            raise ValueError(
                "invalid blue-square input: target out of bounds"
            )
    return _render_rule(coerced, squares, blues)


def canonical_profile_index(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    return features["profile_index"]


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _paint_squares(height, width, squares):
    grid = full_grid(height, width, 0)
    for top, left in squares:
        for row in (top, top + 1):
            for col in (left, left + 1):
                grid[row][col] = 2
    return grid


def _layout(profile_name, rng):
    if profile_name == "large_two":
        first = rng.randint(5, 9), rng.randint(5, 9)
        second = rng.randint(17, 21), rng.randint(16, 21)
        return 30, 30, tuple(sorted((first, second))), ()
    if profile_name == "large_four_balanced":
        first_row = rng.randint(2, 5)
        first = first_row, rng.randint(3, 7)
        second = (
            first_row + rng.randint(0, 2),
            rng.randint(18, 22),
        )
        base_row = rng.randint(14, 16)
        base_col = rng.randint(7, 9)
        delta = rng.randint(6, 8)
        third = base_row, base_col
        fourth = (
            base_row + delta,
            base_col + delta + 3,
        )
        squares = tuple(sorted((first, second, third, fourth)))
        if squares[2:] != (third, fourth):
            raise AssertionError("balanced layout changed tie-square order")
        forced = (
            (base_row, base_col + delta + 1, 2, "right"),
            (base_row + delta + 1, base_col + 3, 2, "stay"),
        )
        return 30, 30, squares, forced
    if profile_name == "compact_two":
        row = rng.randint(2, 4)
        first = row, rng.randint(0, 2)
        second = row, rng.randint(9, 11)
        return 10, 13, (first, second), ()
    if profile_name == "large_four_stay":
        first = rng.randint(4, 7), rng.randint(4, 7)
        middle_row = rng.randint(14, 16)
        second = middle_row, rng.randint(7, 10)
        third = (
            middle_row + rng.randint(0, 1),
            rng.randint(17, 20),
        )
        fourth = rng.randint(24, 26), rng.randint(22, 25)
        return 30, 30, tuple(sorted((
            first,
            second,
            third,
            fourth,
        ))), ()
    raise ValueError(f"unknown scene profile: {profile_name}")


def _candidate_catalog(height, width, squares):
    red_cells = {
        (row, col)
        for top, left in squares
        for row in (top, top + 1)
        for col in (left, left + 1)
    }
    catalog = []
    for row in range(height):
        for col in range(width):
            if (row, col) in red_cells:
                continue
            info = _dot_info(
                height,
                width,
                squares,
                row,
                col,
            )
            if (
                info["in_bounds"]
                and info["target"] not in red_cells
                and info["distance"] >= 2
                and (
                    info["mode"] == "stay"
                    or info["move_length"] > 0
                )
            ):
                catalog.append((row, col, info))
    return catalog


def _requirement_tokens(profile_name):
    tokens = []
    for square_index, requirements in enumerate(
        _PROFILE_REQUIREMENTS[profile_name]
    ):
        for mode, count in requirements.items():
            tokens.extend((square_index, mode) for _index in range(count))
    return tokens


def _choose_dots(
    profile_name,
    height,
    width,
    squares,
    forced,
    rng,
):
    catalog = _candidate_catalog(height, width, squares)
    tokens = _requirement_tokens(profile_name)
    forced_cells = []
    for row, col, square_index, mode in forced:
        info = _dot_info(
            height,
            width,
            squares,
            row,
            col,
        )
        if (
            info["nearest_index"] != square_index
            or info["mode"] != mode
            or info["tie_count"] != 2
            or not info["in_bounds"]
        ):
            return None
        forced_cells.append((row, col, info))
        tokens.remove((square_index, mode))

    for _attempt in range(80):
        chosen = list(forced_cells)
        source_cells = {
            (row, col) for row, col, _info in chosen
        }
        targets = {
            info["target"] for _row, _col, info in chosen
        }
        remaining = list(tokens)
        rng.shuffle(remaining)
        remaining.sort(
            key=lambda token: sum(
                info["nearest_index"] == token[0]
                and info["mode"] == token[1]
                and info["tie_count"] == 1
                for _row, _col, info in catalog
            )
        )
        success = True
        for square_index, mode in remaining:
            candidates = [
                (row, col, info)
                for row, col, info in catalog
                if info["nearest_index"] == square_index
                and info["mode"] == mode
                and info["tie_count"] == 1
                and (row, col) not in source_cells
                and info["target"] not in targets
                and (
                    info["target"] == (row, col)
                    or info["target"] not in source_cells
                )
                and (
                    (row, col) == info["target"]
                    or (row, col) not in targets
                )
            ]
            if not candidates:
                success = False
                break
            row, col, info = rng.choice(candidates)
            chosen.append((row, col, info))
            source_cells.add((row, col))
            targets.add(info["target"])
        if success:
            return tuple(
                (row, col) for row, col, _info in chosen
            )
    return None


def _transform_grid(grid, transform):
    transformed = [row[:] for row in grid]
    if transform >= 4:
        transformed = [
            list(reversed(row)) for row in transformed
        ]
    for _turn in range(transform % 4):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


def _draw_scene(profile_name, rng):
    for _attempt in range(240):
        height, width, squares, forced = _layout(
            profile_name,
            rng,
        )
        dots = _choose_dots(
            profile_name,
            height,
            width,
            squares,
            forced,
            rng,
        )
        if dots is None:
            continue
        grid = _paint_squares(height, width, squares)
        for row, col in dots:
            grid[row][col] = 1
        # Stable scan-order tie behavior is not invariant under every D4
        # transform, so the published tie profile keeps its constructed
        # ordering.  No-tie profiles safely use all eight transforms.
        transform = (
            0
            if profile_name == "large_four_balanced"
            else rng.randrange(8)
        )
        grid = _transform_grid(grid, transform)
        _coerced, features, errors = _scene_analysis(grid)
        if not errors and features["scene_profile"] == profile_name:
            return grid, features
    raise ValueError(
        f"could not realize strict scene profile {profile_name!r}"
    )


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            "compact_two",
            "compact_two",
            "large_two",
            "large_four_balanced",
            "large_four_stay",
        )
    if difficulty == "hard":
        return (
            "compact_two",
            "large_two",
            "large_four_balanced",
            "large_four_balanced",
            "large_four_stay",
            "large_four_stay",
        )
    return SCENE_PROFILES


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, fresh, semantically checked input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    grid, features = _draw_scene(
        profile_name,
        ctx.draw_rng("scene"),
    )
    if features["scene_profile"] != profile_name:
        raise AssertionError(
            "returned profile does not match the requested profile"
        )
    return grid
