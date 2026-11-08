"""Semantic generator for ARC task 4201f3b3ea1b.

Take the first row-major color-5 cell as a source.  Every cell whose color is
not 0, 5, or 6 is part of one global motif, regardless of row, connectivity,
or color.  Translate the original motif to every color-6 anchor in row-major
order, preserve each motif cell's color, clip out-of-bounds targets, and apply
stamps sequentially so later anchors win overlaps.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "4201f3b3ea1b"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d92ee10172c2"
SUMMARY = "Stamp every non-{0,5,6} cell relative to the first 5 onto each row-major color-6 anchor."

INVARIANTS = [
    "the first row-major color-5 cell is the translation source",
    "the motif is every cell whose color is not 0, 5, or 6",
    "every color-6 cell is a destination anchor",
    "each translated cell preserves its original motif color",
    "out-of-bounds targets are clipped and later stamps overwrite earlier stamps",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_train_4", "public_test_1",
)
GENERAL_PROFILES = (
    "single_anchor",
    "four_anchors",
    "single_cell_motif",
    "six_cell_motif",
    "monochrome_motif",
    "disconnected_wide_motif",
    "row_zero_motif",
    "extra_source_marker",
    "clipped_stamp",
    "overlapping_stamps",
    "overwrite_markers",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform rng over five linked public and eleven generalized semantic lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}


# Literal 5/6 are semantic. Roles a-f are nuisance motif colors and are varied
# bijectively without storing any public output.
_PUBLIC_MASKS = {
    "public_train_1": (
        "00000000", "00a00000", "005b0060", "000c0000",
        "00000000", "00000600", "00000000", "00000000",
    ),
    "public_train_2": (
        "000000000", "000000600", "000000000", "000a00000", "0050b0000",
        "00c000000", "000000600", "000000000", "000000000",
    ),
    "public_train_3": (
        "0000000000", "0000000600", "000a000000", "00b5000000",
        "0000600000", "0000000600", "0000000000",
    ),
    "public_train_4": (
        "0000000000", "0000000000", "0000a00060", "00000b0000", "0000500000",
        "0000c00000", "0000000000", "0000000600", "0000000000",
    ),
    "public_test_1": (
        "000000000", "000000000", "00a000600", "005b00000", "0c0000000",
        "000000000", "006000600", "000000000", "000000000",
    ),
}
_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty grid"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _semantic_signature(grid):
    roles = {}
    role_names = iter("abcdefg")
    rendered = []
    for row in grid:
        values = []
        for value in row:
            if value in (0, 5, 6):
                values.append(str(value))
            else:
                if value not in roles:
                    roles[value] = next(role_names)
                values.append(roles[value])
        rendered.append("".join(values))
    return tuple(rendered)


def _projected_cells(motif, source, anchor):
    source_row, source_col = source
    anchor_row, anchor_col = anchor
    return tuple(
        (anchor_row + row - source_row, anchor_col + col - source_col, color)
        for row, col, color in motif
    )


def _rule_output(grid, source, anchors, motif):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for anchor in anchors:
        for row, col, color in _projected_cells(motif, source, anchor):
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = color
    return output


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result
    sources = tuple((row, col) for row in range(height) for col in range(width) if grid[row][col] == 5)
    anchors = tuple((row, col) for row in range(height) for col in range(width) if grid[row][col] == 6)
    motif = tuple(
        (row, col, grid[row][col])
        for row in range(height) for col in range(width)
        if grid[row][col] not in (0, 5, 6)
    )
    if len(sources) not in (1, 2):
        errors.append(f"expected one source, or two in the explicit first-source lesson, got {len(sources)}")
    if not 1 <= len(anchors) <= 4:
        errors.append(f"expected one to four anchors, got {len(anchors)}")
    if not 1 <= len(motif) <= 6:
        errors.append(f"expected one to six motif cells, got {len(motif)}")
    if errors:
        result.update({"sources": sources, "anchors": anchors, "motif": motif})
        return result

    source = sources[0]
    projections = tuple(_projected_cells(motif, source, anchor) for anchor in anchors)
    clipped = sum(
        not (0 <= row < height and 0 <= col < width)
        for projection in projections for row, col, _ in projection
    )
    in_bounds_sets = [
        {(row, col) for row, col, _ in projection if 0 <= row < height and 0 <= col < width}
        for projection in projections
    ]
    overlap = any(
        in_bounds_sets[left] & in_bounds_sets[right]
        for left in range(len(in_bounds_sets)) for right in range(left + 1, len(in_bounds_sets))
    )
    markers = set(sources) | set(anchors)
    marker_overwrites = {
        (row, col) for projection in projections for row, col, _ in projection
        if (row, col) in markers
    }
    motif_colors = tuple(dict.fromkeys(color for _, _, color in motif))
    offsets = tuple((row - source[0], col - source[1]) for row, col, _ in motif)
    max_offset = max(max(abs(dr), abs(dc)) for dr, dc in offsets)
    output = _rule_output(grid, source, anchors, motif)

    profile = _PUBLIC_SIGNATURES.get(_semantic_signature(grid))
    if profile is None:
        if any(row == 0 for row, _, _ in motif):
            profile = "row_zero_motif"
        elif len(sources) == 2:
            profile = "extra_source_marker"
        elif clipped:
            profile = "clipped_stamp"
        elif overlap:
            profile = "overlapping_stamps"
        elif marker_overwrites:
            profile = "overwrite_markers"
        elif len(anchors) == 1:
            profile = "single_anchor"
        elif len(anchors) == 4:
            profile = "four_anchors"
        elif len(motif) == 1:
            profile = "single_cell_motif"
        elif len(motif) == 6:
            profile = "six_cell_motif"
        elif len(motif_colors) == 1:
            profile = "monochrome_motif"
        elif len(motif) == 4 and max_offset >= 4:
            profile = "disconnected_wide_motif"
    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized stamping lesson {profile!r}")
    if any(not cells for cells in in_bounds_sets):
        errors.append("every anchor must receive at least one in-bounds motif cell")
    if output == [list(row) for row in grid]:
        errors.append("stamping lesson must change at least one cell")
    result.update({
        "errors": errors, "sources": sources, "source": source, "anchors": anchors,
        "motif": motif, "motif_colors": motif_colors, "relative_offsets": offsets,
        "clipped_cells": clipped, "stamps_overlap": overlap,
        "marker_overwrites": marker_overwrites, "output": output, "scene_profile": profile,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _grid_from_public(profile, colors):
    return [
        [int(role) if role in "056" else colors[ord(role) - ord("a")] for role in row]
        for row in _PUBLIC_MASKS[profile]
    ]


def _dimensions(rng, difficulty, profile):
    if difficulty == "easy":
        height, width = rng.randint(12, 14), rng.randint(13, 15)
    elif difficulty == "hard":
        height, width = rng.randint(19, 23), rng.randint(20, 24)
    else:
        height, width = rng.randint(15, 18), rng.randint(16, 19)
    if profile == "disconnected_wide_motif":
        height, width = max(height, 18), max(width, 19)
    return height, width


def _general_grid(rng, difficulty, profile, colors):
    height, width = _dimensions(rng, difficulty, profile)
    grid = _blank(height, width)
    source = (height // 2, width // 2)
    offsets = [(-1, 0), (0, 1), (1, 1)]
    motif_colors = [colors[0], colors[1], colors[2]]
    if profile == "single_cell_motif":
        offsets, motif_colors = [(0, 1)], [colors[0]]
    elif profile == "six_cell_motif":
        offsets = [(-2, 0), (-1, 1), (0, 2), (1, 1), (2, 0), (0, -2)]
        motif_colors = list(colors[:6])
    elif profile == "monochrome_motif":
        motif_colors = [colors[0]] * 3
    elif profile == "disconnected_wide_motif":
        offsets = [(-4, -3), (-2, 2), (2, -3), (4, 3)]
        motif_colors = list(colors[:4])
    elif profile == "row_zero_motif":
        source = (4, width // 2)
        offsets = [(-4, -2), (-1, 0), (0, 1)]
        motif_colors = list(colors[:3])
    elif profile == "clipped_stamp":
        offsets = [(-3, 0), (0, 1), (1, 0)]
        motif_colors = list(colors[:3])

    grid[source[0]][source[1]] = 5
    for (dr, dc), color in zip(offsets, motif_colors):
        grid[source[0] + dr][source[1] + dc] = color
    if profile == "extra_source_marker":
        grid[height - 2][0] = 5

    if profile == "clipped_stamp":
        anchors = [(1, 2), (height - 3, 2), (height - 3, width - 3)]
    elif profile == "overlapping_stamps":
        anchors = [(2, 2), (3, 3), (4, 4)]
    elif profile == "overwrite_markers":
        # The first stamp's +1-column motif cell lands on the source marker.
        anchors = [(source[0], source[1] - 1), (2, width - 3)]
    elif profile == "row_zero_motif":
        anchors = [(5, width - 4), (height - 4, 3), (height - 4, width - 4)]
    elif profile == "disconnected_wide_motif":
        anchors = [(5, width - 5), (height - 6, 4), (height - 6, width - 5)]
    elif profile == "single_anchor":
        anchors = [(2, width - 3)]
    elif profile == "four_anchors":
        anchors = [(2, width - 3), (height // 2 - 2, 2), (height - 3, 3), (height - 3, width - 3)]
    else:
        anchors = [(2, width - 3), (height - 3, 2), (height - 3, width - 3)]
    for row, col in anchors:
        if grid[row][col] != 0:
            raise RuntimeError(f"profile {profile} has an input collision at {(row, col)}")
        grid[row][col] = 6
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    colors = tuple(context.draw_distinct_colors("motif_colors", n=6, exclude={0, 5, 6}))
    rng = context.draw_rng("scene")
    grid = _grid_from_public(profile, colors) if profile in PUBLIC_PROFILES else _general_grid(rng, difficulty, profile, colors)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors
