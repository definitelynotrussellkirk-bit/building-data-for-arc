"""Semantic generator for ARC task b7ad0d8d96f6.

Each input is divided by color-0 separators into two equal-width panel columns
and two to four row bands.  Every panel has a modal nonzero background and one
monochrome non-background mask.  Independently in every row band, the two masks
exchange panels at unchanged panel-relative coordinates.  Before painting, both
panels are reset to their own backgrounds; the incoming mask is painted with
its SOURCE panel's background color, so input foreground colors are irrelevant.

Version 3 replaces the old equal-background prohibition, shared-foreground
assumption, fake texture aliases, and 1--3-band scale drift with twelve exact,
observable profiles.  Each difficulty band cycles through four complementary
lesson phases: ordinary distinct backgrounds, a same-background collapse, an
opposite-background foreground trap, and a shared-foreground trap.  Any four
consecutive draws therefore expose all key semantic branches.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b7ad0d8d96f6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "fcca49befb05"

SUMMARY = (
    "A color-0 grid contains exactly two equal-width panel columns and 2--4 "
    "row bands. Each panel has a modal nonzero background and one monochrome "
    "non-background mask. In every row band, reset both panels to their own "
    "backgrounds, move the right mask to the same relative coordinates in "
    "the left panel painted with the RIGHT background, and move the left mask "
    "to the right painted with the LEFT background. Foreground input colors "
    "are ignored; equal panel backgrounds can make both swapped masks vanish."
)

INVARIANTS = [
    "literal color 0 occurs only in complete separator rows and columns",
    "there are exactly two equal-width panel columns and 2--4 equal-height row bands",
    "every panel has a unique modal nonzero background and one monochrome interior mask",
    "the two masks in every row band differ and are not filled bounding boxes",
    "masks swap at unchanged panel-relative coordinates after both panels are reset",
    "each incoming mask is painted with its source panel background, never its foreground color",
    "the returned grid realizes one exact observable scene_profile",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# Profile schema:
#   geometry = (row_group_count, row_group_height, panel_width, separator_cols)
#   palette_size counts color 0 as the separator color
#   roles contains (left_bg, right_bg, left_fg, right_fg) SYMBOLS per band;
#         symbols are mapped to a keyed random nonzero ARC palette
#   shape_sizes contains exact (left_mask_cells, right_mask_cells) per band
#
# A/B/C/D are deliberately cyclic teaching phases.  The role equalities encode:
#   A: no within-band color-role shortcut
#   B: one same-background band (the true output erases both masks there)
#   C: one left foreground equal to the right background
#   D: one shared foreground color across the two panels
SCENE_SPECS: dict[str, dict[str, Any]] = {
    "easy_A_distinct": {
        "geometry": (2, 8, 8, 1), "palette_size": 8,
        "roles": ((0, 1, 2, 3), (4, 5, 6, 0)),
        "shape_sizes": ((6, 9), (8, 11)),
    },
    "easy_B_same_background": {
        "geometry": (2, 8, 8, 1), "palette_size": 8,
        "roles": ((0, 0, 1, 2), (3, 4, 5, 6)),
        "shape_sizes": ((7, 10), (9, 12)),
    },
    "easy_C_opposite_fg_trap": {
        "geometry": (2, 8, 8, 1), "palette_size": 8,
        "roles": ((0, 1, 1, 2), (3, 4, 5, 6)),
        "shape_sizes": ((8, 11), (10, 13)),
    },
    "easy_D_shared_foreground": {
        "geometry": (2, 8, 8, 1), "palette_size": 8,
        "roles": ((0, 1, 2, 2), (3, 4, 5, 6)),
        "shape_sizes": ((9, 12), (11, 14)),
    },
    "medium_A_distinct": {
        "geometry": (3, 7, 8, 1), "palette_size": 7,
        "roles": ((0, 1, 2, 3), (4, 5, 0, 1), (2, 3, 4, 5)),
        "shape_sizes": ((6, 9), (8, 11), (10, 13)),
    },
    "medium_B_same_background": {
        "geometry": (3, 7, 8, 1), "palette_size": 6,
        "roles": ((0, 0, 1, 2), (3, 4, 1, 2), (3, 4, 0, 1)),
        "shape_sizes": ((7, 10), (9, 12), (11, 14)),
    },
    "medium_C_opposite_fg_trap": {
        "geometry": (3, 7, 8, 1), "palette_size": 7,
        "roles": ((0, 1, 1, 2), (3, 4, 5, 0), (2, 3, 4, 5)),
        "shape_sizes": ((8, 12), (10, 14), (6, 11)),
    },
    "medium_D_shared_foreground": {
        "geometry": (3, 7, 8, 1), "palette_size": 6,
        "roles": ((0, 1, 2, 2), (3, 4, 0, 1), (2, 3, 4, 0)),
        "shape_sizes": ((9, 13), (11, 15), (7, 12)),
    },
    "hard_A_distinct": {
        "geometry": (4, 6, 7, 2), "palette_size": 10,
        "roles": ((0, 1, 2, 3), (4, 5, 6, 7), (8, 0, 1, 2), (3, 4, 5, 6)),
        "shape_sizes": ((5, 8), (7, 10), (9, 12), (11, 14)),
    },
    "hard_B_same_background": {
        "geometry": (4, 6, 7, 2), "palette_size": 10,
        "roles": ((0, 0, 1, 2), (3, 4, 5, 6), (7, 8, 1, 2), (3, 4, 5, 6)),
        "shape_sizes": ((6, 9), (8, 11), (10, 13), (12, 15)),
    },
    "hard_C_opposite_fg_trap": {
        "geometry": (4, 6, 7, 2), "palette_size": 10,
        "roles": ((0, 1, 1, 2), (3, 4, 5, 6), (7, 8, 0, 2), (3, 4, 5, 6)),
        "shape_sizes": ((7, 11), (9, 13), (5, 10), (12, 16)),
    },
    "hard_D_shared_foreground": {
        "geometry": (4, 6, 7, 2), "palette_size": 10,
        "roles": ((0, 1, 2, 2), (3, 4, 5, 6), (7, 8, 0, 1), (3, 4, 5, 6)),
        "shape_sizes": ((8, 12), (10, 14), (6, 11), (13, 17)),
    },
}

EASY_PROFILES = (
    "easy_A_distinct",
    "easy_B_same_background",
    "easy_C_opposite_fg_trap",
    "easy_D_shared_foreground",
)
MEDIUM_PROFILES = (
    "medium_A_distinct",
    "medium_B_same_background",
    "medium_C_opposite_fg_trap",
    "medium_D_shared_foreground",
)
HARD_PROFILES = (
    "hard_A_distinct",
    "hard_B_same_background",
    "hard_C_opposite_fg_trap",
    "hard_D_shared_foreground",
)
SCENE_PROFILES = EASY_PROFILES + MEDIUM_PROFILES + HARD_PROFILES
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-linked deterministic four-phase sample-index cycle",
        "valid": "easy_A_distinct|easy_B_same_background|easy_C_opposite_fg_trap|easy_D_shared_foreground|medium_A_distinct|medium_B_same_background|medium_C_opposite_fg_trap|medium_D_shared_foreground|hard_A_distinct|hard_B_same_background|hard_C_opposite_fg_trap|hard_D_shared_foreground",
    }
}

# (height, width) -> (groups, group_h, panel_w, sep_rows, sep_cols, palettes)
_MECHANICAL_PROFILES = {
    (18, 17): (2, 8, 8, 2, 1, frozenset({8})),
    (25, 17): (3, 7, 8, 2, 1, frozenset({6, 7})),
    (30, 16): (4, 6, 7, 2, 2, frozenset({10})),
}


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _nonzero_runs(zero_flags: list[bool]) -> list[tuple[int, int]]:
    """Half-open runs of indices that are not complete-zero separators."""
    runs: list[tuple[int, int]] = []
    index = 0
    while index < len(zero_flags):
        if zero_flags[index]:
            index += 1
            continue
        end = index + 1
        while end < len(zero_flags) and not zero_flags[end]:
            end += 1
        runs.append((index, end))
        index = end
    return runs


def _bbox(mask: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = list(mask)
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    return min(rows), min(cols), max(rows), max(cols)


def _panel_info(grid, row_run, col_run) -> tuple[dict[str, Any] | None, list[str]]:
    row_start, row_end = row_run
    col_start, col_end = col_run
    height, width = row_end - row_start, col_end - col_start
    values = [
        grid[row][col]
        for row in range(row_start, row_end)
        for col in range(col_start, col_end)
    ]
    counts = Counter(values)
    if 0 in counts:
        return None, ["color 0 may occur only in complete separator rows/columns"]
    if len(counts) != 2:
        return None, [f"each panel must contain exactly two nonzero colors, got {sorted(counts)}"]
    ranked = counts.most_common()
    if ranked[0][1] == ranked[1][1]:
        return None, ["panel background must be a unique modal color"]
    background = ranked[0][0]
    foreground = ranked[1][0]
    mask = frozenset(
        (row - row_start, col - col_start)
        for row in range(row_start, row_end)
        for col in range(col_start, col_end)
        if grid[row][col] != background
    )
    if not mask:
        return None, ["every panel needs a nonempty foreground mask"]
    if len(mask) < 4:
        return None, ["foreground masks must contain at least four cells"]
    if len(mask) >= height * width / 2:
        return None, ["foreground mask must be smaller than its modal background"]
    if any(row in (0, height - 1) or col in (0, width - 1) for row, col in mask):
        return None, ["foreground masks must stay strictly inside panel borders"]
    r0, c0, r1, c1 = _bbox(mask)
    if len(mask) == (r1 - r0 + 1) * (c1 - c0 + 1):
        return None, ["foreground masks must not be filled bounding boxes"]
    return {
        "row_start": row_start,
        "row_end": row_end,
        "col_start": col_start,
        "col_end": col_end,
        "height": height,
        "width": width,
        "background": background,
        "foreground": foreground,
        "mask": mask,
        "bbox": (r0, c0, r1, c1),
    }, []


def _analyze_scene(grid) -> tuple[dict[str, Any] | None, list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return None, errors
    height, width = len(grid), len(grid[0])
    zero_rows = [all(value == 0 for value in row) for row in grid]
    zero_cols = [all(grid[row][col] == 0 for row in range(height)) for col in range(width)]
    row_runs = _nonzero_runs(zero_rows)
    col_runs = _nonzero_runs(zero_cols)

    if len(row_runs) not in (2, 3, 4):
        errors.append(f"expected 2--4 row bands, got {len(row_runs)}")
    if len(col_runs) != 2:
        errors.append(f"expected exactly two panel columns, got {len(col_runs)}")
    if not row_runs or row_runs[0][0] != 0 or row_runs[-1][1] != height:
        errors.append("row bands must touch the top and bottom grid edges")
    if not col_runs or col_runs[0][0] != 0 or col_runs[-1][1] != width:
        errors.append("panel columns must touch the left and right grid edges")
    if errors:
        return None, errors

    row_heights = {end - start for start, end in row_runs}
    panel_widths = {end - start for start, end in col_runs}
    if len(row_heights) != 1:
        errors.append("all row bands must have equal height")
    if len(panel_widths) != 1:
        errors.append("the two panel columns must have equal width")
    row_gaps = [row_runs[i + 1][0] - row_runs[i][1] for i in range(len(row_runs) - 1)]
    col_gap = col_runs[1][0] - col_runs[0][1]
    if any(gap != 2 for gap in row_gaps):
        errors.append(f"row bands must be separated by exactly two zero rows, got {row_gaps}")
    if col_gap not in (1, 2):
        errors.append(f"panel columns must be separated by one or two zero columns, got {col_gap}")
    if errors:
        return None, errors

    group_height = next(iter(row_heights))
    panel_width = next(iter(panel_widths))
    expected = _MECHANICAL_PROFILES.get((height, width))
    palette_size = len({value for row in grid for value in row})
    actual_mechanics = (
        len(row_runs), group_height, panel_width,
        row_gaps[0] if row_gaps else 0, col_gap,
    )
    if expected is None:
        errors.append(f"grid size {(height, width)} is outside the declared canonical-scale profiles")
    else:
        exp_groups, exp_group_h, exp_panel_w, exp_row_gap, exp_col_gap, palettes = expected
        if actual_mechanics != (exp_groups, exp_group_h, exp_panel_w, exp_row_gap, exp_col_gap):
            errors.append(
                "mechanical profile mismatch: "
                f"got {actual_mechanics}, expected "
                f"{(exp_groups, exp_group_h, exp_panel_w, exp_row_gap, exp_col_gap)}"
            )
        if palette_size not in palettes:
            errors.append(
                f"palette size {palette_size} is outside the allowed set {sorted(palettes)} "
                f"for grid size {(height, width)}"
            )
    if errors:
        return None, errors

    groups: list[dict[str, Any]] = []
    for group_index, row_run in enumerate(row_runs):
        panels = []
        for side, col_run in zip(("left", "right"), col_runs):
            panel, panel_errors = _panel_info(grid, row_run, col_run)
            if panel_errors:
                errors.extend(
                    f"row band {group_index} {side} panel: {message}"
                    for message in panel_errors
                )
            else:
                panels.append(panel)
        if len(panels) == 2:
            left, right = panels
            if left["mask"] == right["mask"]:
                errors.append(f"row band {group_index}: left and right masks must differ")
            groups.append({"left": left, "right": right})
    if errors:
        return None, errors
    if not any(group["left"]["background"] != group["right"]["background"] for group in groups):
        return None, ["at least one row band must have distinct panel backgrounds so the rule is visible"]

    return {
        "height": height,
        "width": width,
        "palette_size": palette_size,
        "row_runs": row_runs,
        "col_runs": col_runs,
        "separator_cols": col_gap,
        "groups": groups,
    }, []


def _scene_profile_signature(scene: dict[str, Any]) -> tuple[Any, ...]:
    return (
        scene["height"],
        scene["width"],
        scene["palette_size"],
        tuple(
            (len(group["left"]["mask"]), len(group["right"]["mask"]))
            for group in scene["groups"]
        ),
    )


def _spec_profile_signature(spec: dict[str, Any]) -> tuple[Any, ...]:
    group_count, group_height, panel_width, separator_cols = spec["geometry"]
    height = group_count * group_height + (group_count - 1) * 2
    width = panel_width * 2 + separator_cols
    return height, width, spec["palette_size"], tuple(spec["shape_sizes"])


_SIGNATURE_TO_PROFILE = {
    _spec_profile_signature(spec): profile for profile, spec in SCENE_SPECS.items()
}
if len(_SIGNATURE_TO_PROFILE) != len(SCENE_SPECS):
    raise AssertionError("scene profile signatures must be unique")


def _profile_of(grid) -> str | None:
    scene, errors = _analyze_scene(grid)
    if errors or scene is None:
        return None
    return _SIGNATURE_TO_PROFILE.get(_scene_profile_signature(scene))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, and shortcut-hiding panel scenes."""
    del difficulty
    scene, errors = _analyze_scene(grid)
    if errors:
        return errors
    assert scene is not None
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is not None:
        observed = _SIGNATURE_TO_PROFILE.get(_scene_profile_signature(scene))
        if observed != requested:
            return [f"scene profile drifted from {requested!r} to {observed!r}"]
    return []


def strict_canonical_like(grid) -> list[str]:
    """All generated grids and every public canonical input share this grammar."""
    return list(self_check(grid))


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError("valid grid does not realize a declared generated profile")
    return {"scene_profile": profile}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    if difficulty == "easy":
        profiles = EASY_PROFILES
    elif difficulty == "hard":
        profiles = HARD_PROFILES
    else:
        profiles = MEDIUM_PROFILES
    return profiles[int(sample_index) % len(profiles)]


def semantic_signature(grid) -> dict[str, Any]:
    scene, errors = _analyze_scene(grid)
    if errors or scene is None:
        raise ValueError("; ".join(errors))
    groups = scene["groups"]
    return {
        "scene_profile": _SIGNATURE_TO_PROFILE.get(_scene_profile_signature(scene)),
        "height": scene["height"],
        "width": scene["width"],
        "row_groups": len(groups),
        "separator_cols": scene["separator_cols"],
        "palette_size": scene["palette_size"],
        "shape_size_pairs": tuple(
            (len(group["left"]["mask"]), len(group["right"]["mask"]))
            for group in groups
        ),
        "same_background_groups": sum(
            group["left"]["background"] == group["right"]["background"]
            for group in groups
        ),
        "opposite_foreground_traps": sum(
            group["left"]["foreground"] == group["right"]["background"]
            or group["right"]["foreground"] == group["left"]["background"]
            for group in groups
        ),
        "shared_foreground_groups": sum(
            group["left"]["foreground"] == group["right"]["foreground"]
            for group in groups
        ),
        "visible_anchor_mismatch_groups": sum(
            group["left"]["background"] != group["right"]["background"]
            and group["left"]["bbox"][:2] != group["right"]["bbox"][:2]
            for group in groups
        ),
    }


def _copy_grid(grid) -> list[list[int]]:
    return [list(row) for row in grid]


def _fill_panel(output, panel, color: int) -> None:
    for row in range(panel["row_start"], panel["row_end"]):
        for col in range(panel["col_start"], panel["col_end"]):
            output[row][col] = color


def _paint_relative_mask(output, panel, mask, color: int) -> None:
    for rel_row, rel_col in mask:
        if 0 <= rel_row < panel["height"] and 0 <= rel_col < panel["width"]:
            output[panel["row_start"] + rel_row][panel["col_start"] + rel_col] = color


def _validated_scene(grid) -> dict[str, Any]:
    scene, errors = _analyze_scene(grid)
    if errors or scene is None:
        raise ValueError("; ".join(errors))
    return scene


def _true_for_group(output, group) -> None:
    left, right = group["left"], group["right"]
    _fill_panel(output, left, left["background"])
    _fill_panel(output, right, right["background"])
    _paint_relative_mask(output, left, right["mask"], right["background"])
    _paint_relative_mask(output, right, left["mask"], left["background"])


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python mirror for tests; Racket remains output authority."""
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        _true_for_group(output, group)
    return output


def _identity(grid):
    _validated_scene(grid)
    return _copy_grid(grid)


def _erase_shapes(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        for panel in (group["left"], group["right"]):
            _fill_panel(output, panel, panel["background"])
    return output


def _recolor_in_place_to_opposite_background(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        left, right = group["left"], group["right"]
        _fill_panel(output, left, left["background"])
        _fill_panel(output, right, right["background"])
        _paint_relative_mask(output, left, left["mask"], right["background"])
        _paint_relative_mask(output, right, right["mask"], left["background"])
    return output


def _swap_masks_keep_foreground_colors(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        left, right = group["left"], group["right"]
        _fill_panel(output, left, left["background"])
        _fill_panel(output, right, right["background"])
        _paint_relative_mask(output, left, right["mask"], right["foreground"])
        _paint_relative_mask(output, right, left["mask"], left["foreground"])
    return output


def _swap_entire_panels(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        left, right = group["left"], group["right"]
        for rel_row in range(left["height"]):
            for rel_col in range(left["width"]):
                output[left["row_start"] + rel_row][left["col_start"] + rel_col] = (
                    grid[right["row_start"] + rel_row][right["col_start"] + rel_col]
                )
                output[right["row_start"] + rel_row][right["col_start"] + rel_col] = (
                    grid[left["row_start"] + rel_row][left["col_start"] + rel_col]
                )
    return output


def _normalized(mask) -> frozenset[tuple[int, int]]:
    r0, c0, _, _ = _bbox(mask)
    return frozenset((row - r0, col - c0) for row, col in mask)


def _paint_at_anchor(output, panel, mask, anchor, color: int) -> None:
    normalized = _normalized(mask)
    anchor_row, anchor_col = anchor
    shifted = ((anchor_row + row, anchor_col + col) for row, col in normalized)
    _paint_relative_mask(output, panel, shifted, color)


def _swap_normalized_shapes_at_destination_anchor(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        left, right = group["left"], group["right"]
        _fill_panel(output, left, left["background"])
        _fill_panel(output, right, right["background"])
        _paint_at_anchor(output, left, right["mask"], left["bbox"][:2], right["background"])
        _paint_at_anchor(output, right, left["mask"], right["bbox"][:2], left["background"])
    return output


def _process_first_group_only(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    _true_for_group(output, scene["groups"][0])
    return output


def _ignore_same_background_groups(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        if group["left"]["background"] != group["right"]["background"]:
            _true_for_group(output, group)
    return output


def _swap_without_resetting_old_masks(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        left, right = group["left"], group["right"]
        _paint_relative_mask(output, left, right["mask"], right["background"])
        _paint_relative_mask(output, right, left["mask"], left["background"])
    return output


def _paint_bbox(output, panel, bbox, color: int) -> None:
    r0, c0, r1, c1 = bbox
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            output[panel["row_start"] + row][panel["col_start"] + col] = color


def _swap_bounding_boxes(grid):
    scene = _validated_scene(grid)
    output = _copy_grid(grid)
    for group in scene["groups"]:
        left, right = group["left"], group["right"]
        _fill_panel(output, left, left["background"])
        _fill_panel(output, right, right["background"])
        _paint_bbox(output, left, right["bbox"], right["background"])
        _paint_bbox(output, right, left["bbox"], left["background"])
    return output


SEMANTIC_RIVALS = {
    "identity_input": _identity,
    "erase_both_masks": _erase_shapes,
    "recolor_masks_in_place": _recolor_in_place_to_opposite_background,
    "swap_masks_keep_foreground_colors": _swap_masks_keep_foreground_colors,
    "swap_entire_panels": _swap_entire_panels,
    "normalize_to_destination_anchor": _swap_normalized_shapes_at_destination_anchor,
    "process_first_row_band_only": _process_first_group_only,
    "ignore_same_background_bands": _ignore_same_background_groups,
    "swap_without_resetting_old_masks": _swap_without_resetting_old_masks,
    "swap_filled_bounding_boxes": _swap_bounding_boxes,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _scene_or_none(grid) -> dict[str, Any] | None:
    scene, errors = _analyze_scene(grid)
    return None if errors else scene


def _valid(grid) -> bool:
    return _scene_or_none(grid) is not None


def _has_same_background_band(grid) -> bool:
    scene = _scene_or_none(grid)
    return bool(scene) and any(
        group["left"]["background"] == group["right"]["background"]
        for group in scene["groups"]
    )


def _has_opposite_foreground_trap(grid) -> bool:
    scene = _scene_or_none(grid)
    return bool(scene) and any(
        group["left"]["background"] != group["right"]["background"]
        and (
            group["left"]["foreground"] == group["right"]["background"]
            or group["right"]["foreground"] == group["left"]["background"]
        )
        for group in scene["groups"]
    )


def _has_shared_foreground_band(grid) -> bool:
    scene = _scene_or_none(grid)
    return bool(scene) and any(
        group["left"]["foreground"] == group["right"]["foreground"]
        for group in scene["groups"]
    )


def _has_visible_anchor_mismatch(grid) -> bool:
    scene = _scene_or_none(grid)
    return bool(scene) and any(
        group["left"]["background"] != group["right"]["background"]
        and group["left"]["bbox"][:2] != group["right"]["bbox"][:2]
        for group in scene["groups"]
    )


def _has_uncovered_old_mask_cell(grid) -> bool:
    scene = _scene_or_none(grid)
    return bool(scene) and any(
        group["left"]["background"] != group["right"]["background"]
        and (
            bool(group["left"]["mask"] - group["right"]["mask"])
            or bool(group["right"]["mask"] - group["left"]["mask"])
        )
        for group in scene["groups"]
    )


def _has_visible_nonrectangular_mask(grid) -> bool:
    scene = _scene_or_none(grid)
    if not scene:
        return False
    for group in scene["groups"]:
        if group["left"]["background"] == group["right"]["background"]:
            continue
        for panel in (group["left"], group["right"]):
            r0, c0, r1, c1 = panel["bbox"]
            if len(panel["mask"]) < (r1 - r0 + 1) * (c1 - c0 + 1):
                return True
    return False


SEMANTIC_WITNESSES = {
    "masks_exchange_sides_not_just_colors": lambda grid: _valid(grid),
    "foreground_input_colors_are_ignored": lambda grid: _valid(grid),
    "same_background_band_collapses_to_background": _has_same_background_band,
    "opposite_background_foreground_trap": _has_opposite_foreground_trap,
    "shared_foreground_is_not_the_output_color": _has_shared_foreground_band,
    "all_row_bands_are_processed": lambda grid: _valid(grid),
    "panel_relative_coordinates_are_preserved": _has_visible_anchor_mismatch,
    "old_masks_are_reset_before_incoming_masks": _has_uncovered_old_mask_cell,
    "exact_masks_not_filled_bounding_boxes": _has_visible_nonrectangular_mask,
}

WITNESS_RIVALS = {
    "masks_exchange_sides_not_just_colors": ["recolor_masks_in_place", "identity_input"],
    "foreground_input_colors_are_ignored": ["swap_masks_keep_foreground_colors"],
    "same_background_band_collapses_to_background": ["ignore_same_background_bands"],
    "opposite_background_foreground_trap": ["recolor_masks_in_place"],
    "shared_foreground_is_not_the_output_color": ["swap_masks_keep_foreground_colors"],
    "all_row_bands_are_processed": ["process_first_row_band_only"],
    "panel_relative_coordinates_are_preserved": ["normalize_to_destination_anchor"],
    "old_masks_are_reset_before_incoming_masks": ["swap_without_resetting_old_masks"],
    "exact_masks_not_filled_bounding_boxes": ["swap_filled_bounding_boxes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo lesson to eliminate all named plausible rivals."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output does not match the mask-exchange rule")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
        return reasons

    if len(valid_demos) < EXAMPLES_NEEDED:
        reasons.append(f"lesson needs {EXAMPLES_NEEDED} valid demonstrations")
    profiles = {_profile_of(demo["input"]) for demo in valid_demos}
    if None in profiles or len(profiles) < 4:
        reasons.append("demonstrations do not cover four distinct observable scene profiles")
    if not any(_has_same_background_band(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not show the same-background collapse branch")
    if not any(_has_opposite_foreground_trap(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not prove that foreground colors are ignored")
    if not any(_has_shared_foreground_band(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not refute a shared-shape-color rule")
    if not any(_has_visible_anchor_mismatch(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not distinguish exact coordinates from anchor normalization")

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons


def _grow_normalized_shape(rng, interior_h: int, interior_w: int, size: int):
    if not 4 <= size < interior_h * interior_w:
        raise ValueError(
            f"shape size {size} cannot form a nonrectangular interior mask in "
            f"{interior_h}x{interior_w}"
        )
    all_cells = [(row, col) for row in range(interior_h) for col in range(interior_w)]
    for _ in range(512):
        cells = {rng.choice(all_cells)}
        while len(cells) < size:
            frontier = sorted({
                neighbor
                for row, col in cells
                for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                if 0 <= neighbor[0] < interior_h
                and 0 <= neighbor[1] < interior_w
                and neighbor not in cells
            })
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != size:
            continue
        r0, c0, r1, c1 = _bbox(cells)
        normalized = frozenset((row - r0, col - c0) for row, col in cells)
        bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if bbox_area == size:
            continue
        return normalized, r1 - r0 + 1, c1 - c0 + 1
    raise RuntimeError(f"could not construct nonrectangular shape of size {size}")


def _anchored_shape(rng, panel_h: int, panel_w: int, size: int, anchor: str,
                    *, require_nonzero_offset: bool = False):
    interior_h, interior_w = panel_h - 2, panel_w - 2
    for _ in range(512):
        normalized, shape_h, shape_w = _grow_normalized_shape(
            rng, interior_h, interior_w, size
        )
        max_row_offset = interior_h - shape_h
        max_col_offset = interior_w - shape_w
        if anchor == "tl":
            row_offset, col_offset = 0, 0
        elif anchor == "tr":
            row_offset, col_offset = 0, max_col_offset
        elif anchor == "bl":
            row_offset, col_offset = max_row_offset, 0
        elif anchor == "br":
            row_offset, col_offset = max_row_offset, max_col_offset
        else:
            row_offset = rng.randint(0, max_row_offset)
            col_offset = rng.randint(0, max_col_offset)
        if require_nonzero_offset and row_offset == 0 and col_offset == 0:
            continue
        return frozenset(
            (row + 1 + row_offset, col + 1 + col_offset)
            for row, col in normalized
        )
    raise RuntimeError(
        f"could not place shape size={size} anchor={anchor!r} with requested offset"
    )


def _role_colors(rng, spec: dict[str, Any]) -> list[tuple[int, int, int, int]]:
    role_symbols = tuple(tuple(group) for group in spec["roles"])
    symbols = sorted({symbol for group in role_symbols for symbol in group})
    expected_nonzero = int(spec["palette_size"]) - 1
    if len(symbols) != expected_nonzero:
        raise AssertionError(
            f"profile declares palette {spec['palette_size']} but realizes "
            f"{len(symbols) + 1} colors"
        )
    chosen = rng.sample(range(1, 10), len(symbols))
    mapping = dict(zip(symbols, chosen))
    roles = [tuple(mapping[symbol] for symbol in group) for group in role_symbols]
    for left_bg, right_bg, left_fg, right_fg in roles:
        if left_bg == left_fg or right_bg == right_fg:
            raise AssertionError("a foreground color collided with its own panel background")
    return roles


def _paint_shape(grid, row_start: int, col_start: int, mask, color: int) -> None:
    for rel_row, rel_col in mask:
        grid[row_start + rel_row][col_start + rel_col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the selected Racket rule owns outputs."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
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
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    spec = SCENE_SPECS[profile]
    group_count, group_height, panel_width, separator_cols = spec["geometry"]
    separator_rows = 2
    height = group_count * group_height + (group_count - 1) * separator_rows
    width = panel_width * 2 + separator_cols
    grid = full_grid(height, width, 0)

    rng = ctx.draw_rng(f"layout:{profile}")
    roles = _role_colors(rng, spec)
    anchors = (("tl", "br"), ("tr", "bl"), ("bl", "tr"), ("br", "tl"))
    row_start = 0
    for group_index, ((left_bg, right_bg, left_fg, right_fg), sizes) in enumerate(
        zip(roles, spec["shape_sizes"])
    ):
        right_col_start = panel_width + separator_cols
        for rel_row in range(group_height):
            for rel_col in range(panel_width):
                grid[row_start + rel_row][rel_col] = left_bg
                grid[row_start + rel_row][right_col_start + rel_col] = right_bg

        left_anchor, right_anchor = anchors[group_index % len(anchors)]
        left_mask = _anchored_shape(
            rng, group_height, panel_width, int(sizes[0]), left_anchor
        )
        right_mask = _anchored_shape(
            rng, group_height, panel_width, int(sizes[1]), right_anchor,
            require_nonzero_offset=(group_index == 0),
        )
        _paint_shape(grid, row_start, 0, left_mask, left_fg)
        _paint_shape(grid, row_start, right_col_start, right_mask, right_fg)
        row_start += group_height + separator_rows

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"scene_profile": profile}},
    )
    if errors:
        raise RuntimeError(f"constructed invalid scene for {profile}: {errors}")
    return _copy_grid(grid)
