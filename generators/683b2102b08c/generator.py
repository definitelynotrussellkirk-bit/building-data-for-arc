"""Semantic generator for ARC task 683b2102b08c.

A full yellow row separates an orange canvas. Below it, the more frequent of
two shape colors is the main shape. Clear the canvas except for the separator,
move all main-color cells to the top while preserving columns and normalized
row offsets, then place the secondary shape immediately left of the main
bounding box and vertically centered within the main height.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "683b2102b08c"
VERSION = "3.0.0"
TASK_ID = "683b2102b08c"
RULE_HASH = "0afee0287491"
SUMMARY = (
    "Below the full yellow separator, select the uniquely more frequent color "
    "as the main shape. Move its complete color mask to the top in the same "
    "columns, clear the lower half, and move the other color immediately left "
    "of and vertically centered on the main bounding box."
)
EXAMPLES_NEEDED = 4
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized (3:7)",
        "valid": "linked|generalized",
        "doc": (
            "linked preserves one complete public two-color layout; "
            "generalized varies masks, disconnected color groups, placement, "
            "and main/secondary bounding-box relations"
        ),
    },
}
INVARIANTS = [
    "background is orange (7) with exactly one full yellow (4) separator row",
    "the area above the separator is initially blank orange",
    "exactly two non-background colors occur below the separator",
    "the main color is uniquely more frequent than the secondary color",
    "main and secondary masks fit the canonical top/left placement without clipping",
]

BACKGROUND = 7
SEPARATOR = 4
COLORS = tuple(color for color in range(10) if color not in (4, 7))
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
GENERAL_PROFILES = (
    "compact",
    "split_main",
    "split_secondary",
    "tall_main",
    "wide_secondary",
    "edge_right",
    "near_left",
)

# Input-only colored coordinates relative to the row below the separator.
# In every profile the five-cell group is the main color. Outputs are computed.
PUBLIC_PROFILES = (
    (
        "public_train_1",
        ((0, 10), (1, 10), (2, 8), (2, 10), (3, 9)),
        ((0, 4), (1, 4), (1, 5)),
    ),
    (
        "public_train_2",
        ((0, 8), (1, 8), (2, 6), (2, 8), (3, 7)),
        ((2, 1), (2, 2), (3, 1), (3, 2)),
    ),
    (
        "public_train_3",
        ((0, 5), (1, 5), (2, 3), (2, 5), (3, 4)),
        ((0, 9), (1, 8)),
    ),
    (
        "public_test_1",
        ((0, 8), (1, 8), (2, 6), (2, 8), (3, 7)),
        ((1, 3), (2, 2), (3, 3)),
    ),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalized(cells):
    top, left, _, _ = _bbox(cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _component_count(cells):
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _translation_reflection_signature(main_cells, secondary_cells):
    left = min(col for _, col in main_cells + secondary_cells)
    right = max(col for _, col in main_cells + secondary_cells)
    direct = (
        tuple(sorted((row, col - left) for row, col in main_cells)),
        tuple(sorted((row, col - left) for row, col in secondary_cells)),
    )
    reflected = (
        tuple(sorted((row, right - col) for row, col in main_cells)),
        tuple(sorted((row, right - col) for row, col in secondary_cells)),
    )
    return min(direct, reflected)


def _public_signature(grid, line_row, main_cells, secondary_cells):
    if len(grid) != 11 or len(grid[0]) != 11 or line_row != 5:
        return None
    return _translation_reflection_signature(
        [(row - line_row - 1, col) for row, col in main_cells],
        [(row - line_row - 1, col) for row, col in secondary_cells],
    )


_PUBLIC_SIGNATURE_TO_PROFILE = {}
for _profile, _main, _secondary in PUBLIC_PROFILES:
    _PUBLIC_SIGNATURE_TO_PROFILE[
        _translation_reflection_signature(list(_main), list(_secondary))
    ] = _profile


def _general_profile(facts):
    if facts["main_c2"] == facts["width"] - 1:
        return "edge_right"
    if facts["target_secondary_c1"] == 0:
        return "near_left"
    if facts["main_component_count"] >= 2:
        return "split_main"
    if facts["secondary_component_count"] >= 2:
        return "split_secondary"
    if facts["main_height"] >= facts["secondary_height"] + 3:
        return "tall_main"
    if facts["secondary_width"] >= 3:
        return "wide_secondary"
    return "compact"


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {
            "errors": ["grid must be a nonempty rectangular matrix"],
            "facts": None,
        }
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"], "facts": None}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {
            "errors": ["grid must be rectangular and nonempty"],
            "facts": None,
        }
    height = len(grid)
    width = next(iter(widths))
    if not (8 <= height <= 30 and 8 <= width <= 30):
        errors.append("grid must be 8..30 rows by 8..30 columns")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cell values must be integer ARC colors 0..9")
        return {"errors": errors, "facts": None}

    separator_rows = [
        row
        for row in range(height)
        if all(grid[row][col] == SEPARATOR for col in range(width))
    ]
    if len(separator_rows) != 1:
        return {
            "errors": ["need exactly one full yellow separator row"],
            "facts": None,
        }
    line_row = separator_rows[0]
    if not 3 <= line_row <= height - 4:
        errors.append("separator must leave at least three rows on each side")
    if any(
        grid[row][col] != BACKGROUND
        for row in range(line_row)
        for col in range(width)
    ):
        errors.append("pre-separator area must be blank orange")

    cells_by_color = {}
    for row in range(line_row + 1, height):
        for col in range(width):
            value = grid[row][col]
            if value in (BACKGROUND, SEPARATOR):
                continue
            cells_by_color.setdefault(value, []).append((row, col))
    if len(cells_by_color) != 2:
        errors.append("need exactly two shape colors below the separator")
        return {"errors": errors, "facts": None}
    ranked = sorted(
        cells_by_color.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )
    if len(ranked[0][1]) == len(ranked[1][1]):
        errors.append("main color must be uniquely more frequent")
        return {"errors": errors, "facts": None}
    main_color, main_cells = ranked[0]
    secondary_color, secondary_cells = ranked[1]
    main_r1, main_c1, main_r2, main_c2 = _bbox(main_cells)
    sec_r1, sec_c1, sec_r2, sec_c2 = _bbox(secondary_cells)
    main_height = main_r2 - main_r1 + 1
    secondary_height = sec_r2 - sec_r1 + 1
    secondary_width = sec_c2 - sec_c1 + 1
    target_secondary_r1 = (main_height - secondary_height) // 2
    target_secondary_c1 = main_c1 + 1 - secondary_width
    if main_height > line_row:
        errors.append("main normalized height must fit above the separator")
    if secondary_height > main_height:
        errors.append("secondary height must not exceed main height")
    if target_secondary_c1 < 0:
        errors.append("secondary left placement must not clip")

    output = full_grid(height, width, BACKGROUND)
    for col in range(width):
        output[line_row][col] = SEPARATOR
    occupied_output = set()
    for row, col in main_cells:
        target = (row - main_r1, col)
        output[target[0]][target[1]] = main_color
        occupied_output.add(target)
    collision_count = 0
    for row, col in secondary_cells:
        target = (
            target_secondary_r1 + row - sec_r1,
            target_secondary_c1 + col - sec_c1,
        )
        if not (0 <= target[0] < height and 0 <= target[1] < width):
            errors.append("secondary normalized placement must fit the grid")
            continue
        collision_count += target in occupied_output
        output[target[0]][target[1]] = secondary_color
    public_signature = _public_signature(
        grid, line_row, main_cells, secondary_cells
    )
    linked_profile = _PUBLIC_SIGNATURE_TO_PROFILE.get(public_signature)
    facts = {
        "height": height,
        "width": width,
        "line_row": line_row,
        "main_color": main_color,
        "secondary_color": secondary_color,
        "main_cells": tuple(sorted(main_cells)),
        "secondary_cells": tuple(sorted(secondary_cells)),
        "main_count": len(main_cells),
        "secondary_count": len(secondary_cells),
        "main_bbox": (main_r1, main_c1, main_r2, main_c2),
        "secondary_bbox": (sec_r1, sec_c1, sec_r2, sec_c2),
        "main_height": main_height,
        "main_width": main_c2 - main_c1 + 1,
        "secondary_height": secondary_height,
        "secondary_width": secondary_width,
        "main_c1": main_c1,
        "main_c2": main_c2,
        "target_secondary_r1": target_secondary_r1,
        "target_secondary_c1": target_secondary_c1,
        "main_component_count": _component_count(main_cells),
        "secondary_component_count": _component_count(secondary_cells),
        "collision_count": collision_count,
        "output": output,
        "family": "linked" if linked_profile else "generalized",
        "linked_profile": linked_profile,
    }
    facts["generalized_profile"] = (
        None if linked_profile else _general_profile(facts)
    )
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return analysis["facts"]["family"]


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["family"]}


def _rand_poly(rng, max_height, max_width, target):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(600):
        if len(cells) >= target:
            break
        row, col = rng.choice(cells)
        delta_row, delta_col = rng.choice(
            ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        neighbor = (row + delta_row, col + delta_col)
        if (
            neighbor not in seen
            and 0 <= neighbor[0] < max_height
            and 0 <= neighbor[1] < max_width
        ):
            seen.add(neighbor)
            cells.append(neighbor)
    return list(_normalized(cells))


def _build_linked(rng):
    profile, raw_main, raw_secondary = rng.choice(PUBLIC_PROFILES)
    main = list(raw_main)
    secondary = list(raw_secondary)
    if rng.random() < 0.5:
        main = [(row, 10 - col) for row, col in main]
        secondary = [(row, 10 - col) for row, col in secondary]
    secondary_width = 1 + max(col for _, col in secondary) - min(
        col for _, col in secondary
    )
    scene_min = min(col for _, col in main + secondary)
    scene_max = max(col for _, col in main + secondary)
    main_min = min(col for _, col in main)
    shift_low = max(-scene_min, secondary_width - 1 - main_min)
    shift_high = 10 - scene_max
    shift = rng.randint(shift_low, shift_high)
    main = [(row, col + shift) for row, col in main]
    secondary = [(row, col + shift) for row, col in secondary]
    main_color, secondary_color = rng.sample(COLORS, 2)
    grid = full_grid(11, 11, BACKGROUND)
    for col in range(11):
        grid[5][col] = SEPARATOR
    for row, col in main:
        grid[6 + row][col] = main_color
    for row, col in secondary:
        grid[6 + row][col] = secondary_color
    analysis = _analyze(grid)
    if (
        analysis["errors"]
        or analysis["facts"]["linked_profile"] != profile
    ):
        raise RuntimeError("linked move/pack profile construction drift")
    return grid


def _shape_for_band(rng, band):
    ranges = {
        "easy": ((10, 12), (10, 13), (4, 5)),
        "medium": ((13, 16), (14, 18), (5, 7)),
        "hard": ((17, 21), (18, 23), (7, 9)),
    }
    (height_low, height_high), (width_low, width_high), line_range = (
        ranges[band]
    )
    return (
        rng.randint(height_low, height_high),
        rng.randint(width_low, width_high),
        rng.randint(*line_range),
    )


def _far_satellite(cells, height, width, rng):
    occupied = set(cells)
    for _ in range(300):
        candidate = (rng.randrange(height), rng.randrange(width))
        if candidate in occupied:
            continue
        if all(
            abs(candidate[0] - row) + abs(candidate[1] - col) >= 2
            for row, col in occupied
        ):
            return candidate
    raise ValueError("could not place disconnected satellite")


def _build_generalized(rng, band):
    profile = rng.choice(GENERAL_PROFILES)
    want_output_overlap = rng.random() < 0.7
    fallback = None
    for _ in range(300):
        height, width, line_row = _shape_for_band(rng, band)
        below_height = height - line_row - 1
        if below_height < 5:
            continue

        if profile == "tall_main":
            main_h = min(6, below_height)
            secondary_h = max(1, main_h - 3)
        else:
            main_h = rng.randint(3, min(5, below_height))
            secondary_h = rng.randint(1, main_h)
        main_w = rng.randint(3, min(6, width - 3))
        secondary_w = (
            rng.randint(3, min(5, main_w))
            if profile == "wide_secondary"
            else rng.randint(1, min(2, main_w))
        )
        main_target = rng.randint(
            max(5, main_h + 1),
            min(main_h * main_w, 12),
        )
        secondary_low = 1 if profile == "tall_main" else 2
        secondary_high = min(
            secondary_h * secondary_w, main_target - 2
        )
        if secondary_high < secondary_low:
            continue
        secondary_target = rng.randint(secondary_low, secondary_high)
        main_local = _rand_poly(rng, main_h, main_w, main_target)
        secondary_local = _rand_poly(
            rng, secondary_h, secondary_w, secondary_target
        )
        if len(main_local) <= len(secondary_local):
            continue

        if profile == "split_main":
            try:
                main_local.append(
                    _far_satellite(main_local, main_h, main_w, rng)
                )
            except ValueError:
                continue
        if profile == "split_secondary":
            try:
                secondary_local.append(
                    _far_satellite(
                        secondary_local,
                        secondary_h,
                        max(secondary_w, 3),
                        rng,
                    )
                )
            except ValueError:
                continue
            secondary_local = list(_normalized(secondary_local))
            secondary_w = max(col for _, col in secondary_local) + 1
        if len(main_local) <= len(secondary_local):
            continue

        main_local = list(_normalized(main_local))
        secondary_local = list(_normalized(secondary_local))
        actual_main_h = max(row for row, _ in main_local) + 1
        actual_main_w = max(col for _, col in main_local) + 1
        actual_secondary_h = max(row for row, _ in secondary_local) + 1
        actual_secondary_w = max(col for _, col in secondary_local) + 1
        if actual_secondary_h > actual_main_h:
            continue
        if profile == "edge_right":
            main_col = width - actual_main_w
        elif profile == "near_left":
            main_col = actual_secondary_w - 1
        else:
            low = actual_secondary_w
            high = width - actual_main_w - 1
            if high < low:
                continue
            main_col = rng.randint(low, high)
        main_row = rng.randint(
            line_row + 1,
            height - actual_main_h,
        )

        # Input placement of the secondary is deliberately unrelated to its
        # output destination. Find a non-overlapping lower-half location.
        main_absolute = {
            (main_row + row, main_col + col)
            for row, col in main_local
        }
        secondary_position = None
        for _ in range(200):
            secondary_row = rng.randint(
                line_row + 1,
                height - actual_secondary_h,
            )
            secondary_col = rng.randint(
                0, width - actual_secondary_w
            )
            candidate = {
                (secondary_row + row, secondary_col + col)
                for row, col in secondary_local
            }
            if candidate.isdisjoint(main_absolute):
                secondary_position = (
                    secondary_row,
                    secondary_col,
                )
                break
        if secondary_position is None:
            continue

        main_color, secondary_color = rng.sample(COLORS, 2)
        grid = full_grid(height, width, BACKGROUND)
        for col in range(width):
            grid[line_row][col] = SEPARATOR
        for row, col in main_absolute:
            grid[row][col] = main_color
        secondary_row, secondary_col = secondary_position
        for row, col in secondary_local:
            grid[secondary_row + row][secondary_col + col] = secondary_color

        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["family"] == "generalized"
            and analysis["facts"]["generalized_profile"] == profile
        ):
            if fallback is None:
                fallback = grid
            if (
                bool(analysis["facts"]["collision_count"])
                == want_output_overlap
            ):
                return grid
    if fallback is not None:
        return fallback
    raise RuntimeError("could not realize generalized move/pack scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family",
        (
            "linked",
            "linked",
            "linked",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
        ),
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    rng = ctx.draw_rng("scene")
    grid = (
        _build_linked(rng)
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['family']}"
                ]
            )
        )
    return grid
