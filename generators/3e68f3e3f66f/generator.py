"""Semantic generator for ARC task 3e68f3e3f66f.

Read every nonzero top-row value as an ordered legend.  Sort color-6
destination anchors row-major.  Around the first color-5 source, take every
nonzero cell below row 0 except colors 5 and 6 as the motif.  Translate that
whole motif to each destination and recolor copy i with legend color i,
clipping out-of-bounds cells.  Copies are applied in destination order.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "3e68f3e3f66f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4f92f2063a9e"
SUMMARY = "Broadcast the source-relative motif to row-major color-6 anchors, recolored by the top-row legend."

INVARIANTS = [
    "the ordered legend is every nonzero value in row 0",
    "the first row-major color-5 cell is the translation source",
    "the motif is every nonzero non-{5,6} cell below row 0",
    "color-6 destinations are paired row-major with legend colors",
    "translated motif cells are clipped to the canvas and later copies overwrite earlier ones",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "single_broadcast",
    "four_broadcasts",
    "noncontiguous_legend",
    "multicolor_motif",
    "disconnected_motif",
    "legend_colored_motif",
    "clipped_copy",
    "overlapping_copies",
    "extra_source_marker",
    "sparse_wide_motif",
    "row_major_counterexample",
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


# Roles a-d are ordered legend colors; x is the public motif color.  Colors 5
# and 6 remain literal because the executable rule treats them semantically.
_PUBLIC_MASKS = {
    "public_train_1": (
        "ab00000000", "0000000000", "0000000060", "0000000000",
        "00x0000000", "005x000000", "000x000000", "0000000000",
        "0000000600", "0000000000",
    ),
    "public_train_2": (
        "abc00000000", "00000000000", "00000000600", "00000000000",
        "0000x000000", "00050x00000", "000x0000000", "00000000000",
        "00060000600", "00000000000", "00000000000",
    ),
    "public_train_3": (
        "ab000000000", "00000000000", "00000000060", "0000x000000",
        "00000x00000", "00005000000", "0000x000000", "00000000000",
        "00000000600", "00000000000",
    ),
    "public_train_4": (
        "abc0000000", "0000000000", "0000000600", "0000000000",
        "0000000000", "00x0000000", "005x000000", "0x00000000",
        "0060000600", "0000000000", "0000000000",
    ),
    "public_test_1": (
        "abc00000000", "00000000000", "00000000600", "00000000000",
        "000x0000000", "0005x000000", "0000x000000", "00000000000",
        "00060000600", "00000000000", "00000000000",
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
    legend = [value for value in grid[0] if value != 0]
    legend_roles = {value: chr(ord("a") + index) for index, value in enumerate(legend)}
    other_roles = {}
    next_role = iter("xyzuvw")
    rows = []
    for row_index, row in enumerate(grid):
        rendered = []
        for value in row:
            if value == 0:
                rendered.append("0")
            elif value in (5, 6):
                rendered.append(str(value))
            elif value in legend_roles:
                rendered.append(legend_roles[value])
            else:
                if value not in other_roles:
                    other_roles[value] = next(next_role)
                rendered.append(other_roles[value])
        rows.append("".join(rendered))
    return tuple(rows)


def _projected_cells(motif, source, anchor):
    source_row, source_col = source
    anchor_row, anchor_col = anchor
    return tuple(
        (anchor_row + row - source_row, anchor_col + col - source_col)
        for row, col, _ in motif
    )


def _rule_output(grid, legend, source, anchors, motif):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for index, anchor in enumerate(anchors):
        color = legend[index]
        for row, col in _projected_cells(motif, source, anchor):
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = color
    return output


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result

    legend_positions = tuple(col for col, value in enumerate(grid[0]) if value != 0)
    legend = tuple(grid[0][col] for col in legend_positions)
    sources = tuple((row, col) for row in range(height) for col in range(width) if grid[row][col] == 5)
    anchors = tuple(sorted((row, col) for row in range(height) for col in range(width) if grid[row][col] == 6))
    motif = tuple(
        (row, col, grid[row][col])
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] not in (0, 5, 6)
    )
    if not 1 <= len(legend) <= 4:
        errors.append(f"expected one to four legend colors, got {len(legend)}")
    if len(set(legend)) != len(legend) or any(value in (5, 6) for value in legend):
        errors.append(f"legend must use distinct non-{{0,5,6}} colors: {legend}")
    if len(sources) not in (1, 2):
        errors.append(f"expected one source, or the explicit extra-source lesson, got {len(sources)}")
    if not anchors or len(anchors) != len(legend):
        errors.append(f"anchor count {len(anchors)} must equal legend size {len(legend)}")
    if not motif:
        errors.append("motif must contain at least one eligible cell below row 0")
    if errors:
        result.update({"legend": legend, "legend_positions": legend_positions, "sources": sources, "anchors": anchors, "motif": motif})
        return result

    source = sources[0]
    projections = tuple(_projected_cells(motif, source, anchor) for anchor in anchors)
    clipped = sum(
        not (0 <= row < height and 0 <= col < width)
        for projection in projections for row, col in projection
    )
    in_bounds_sets = [
        {(row, col) for row, col in projection if 0 <= row < height and 0 <= col < width}
        for projection in projections
    ]
    overlap = any(
        in_bounds_sets[left] & in_bounds_sets[right]
        for left in range(len(in_bounds_sets))
        for right in range(left + 1, len(in_bounds_sets))
    )
    motif_colors = tuple(dict.fromkeys(value for _, _, value in motif))
    relative_offsets = tuple((row - source[0], col - source[1]) for row, col, _ in motif)
    max_offset = max(max(abs(dr), abs(dc)) for dr, dc in relative_offsets)
    output = _rule_output(grid, legend, source, anchors, motif)

    profile = _PUBLIC_SIGNATURES.get(_semantic_signature(grid))
    contiguous = legend_positions == tuple(range(len(legend_positions)))
    if profile is None:
        if not contiguous:
            profile = "noncontiguous_legend"
        elif len(sources) == 2:
            profile = "extra_source_marker"
        elif any(color in legend for color in motif_colors):
            profile = "legend_colored_motif"
        elif len(motif_colors) > 1:
            profile = "multicolor_motif"
        elif clipped:
            profile = "clipped_copy"
        elif overlap:
            profile = "overlapping_copies"
        elif len(legend) == 1:
            profile = "single_broadcast"
        elif len(legend) == 4:
            profile = "four_broadcasts"
        elif len(legend) == 2:
            profile = "row_major_counterexample"
        elif len(motif) == 2 and max_offset >= 3:
            profile = "disconnected_motif"
        elif len(motif) == 4 and max_offset >= 4:
            profile = "sparse_wide_motif"
    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized broadcast lesson {profile!r}")
    if any(not cells for cells in in_bounds_sets):
        errors.append("every destination must receive at least one in-bounds motif cell")
    result.update({
        "errors": errors,
        "legend": legend,
        "legend_positions": legend_positions,
        "sources": sources,
        "source": source,
        "anchors": anchors,
        "motif": motif,
        "motif_colors": motif_colors,
        "relative_offsets": relative_offsets,
        "clipped_cells": clipped,
        "copies_overlap": overlap,
        "output": output,
        "scene_profile": profile,
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
    legend_count = sum(role in "abcd" for role in _PUBLIC_MASKS[profile][0])
    role_colors = {chr(ord("a") + index): colors[index] for index in range(legend_count)}
    role_colors["x"] = colors[legend_count]
    return [
        [int(role) if role in "056" else role_colors[role] for role in row]
        for row in _PUBLIC_MASKS[profile]
    ]


def _dimensions(rng, difficulty, profile):
    if difficulty == "easy":
        height, width = rng.randint(12, 14), rng.randint(13, 15)
    elif difficulty == "hard":
        height, width = rng.randint(19, 23), rng.randint(20, 24)
    else:
        height, width = rng.randint(15, 18), rng.randint(16, 19)
    if profile == "sparse_wide_motif":
        height, width = max(height, 18), max(width, 19)
    return height, width


def _general_grid(rng, difficulty, profile, colors):
    height, width = _dimensions(rng, difficulty, profile)
    grid = _blank(height, width)
    legend_count = 1 if profile == "single_broadcast" else 4 if profile == "four_broadcasts" else 2 if profile == "row_major_counterexample" else 3
    legend_positions = (0, 2, 5) if profile == "noncontiguous_legend" else tuple(range(legend_count))
    legend = colors[:legend_count]
    for position, color in zip(legend_positions, legend):
        grid[0][position] = color

    source = (height // 2, width // 2)
    offsets = [(-1, 0), (0, 1), (1, 0)]
    motif_colors = [colors[4]] * len(offsets)
    if profile == "multicolor_motif":
        motif_colors = [colors[4], colors[5], colors[4]]
    elif profile == "disconnected_motif":
        offsets = [(-3, -2), (3, 2)]
        motif_colors = [colors[4]] * 2
    elif profile == "legend_colored_motif":
        motif_colors = [legend[1], legend[1], legend[1]]
    elif profile == "clipped_copy":
        offsets = [(-3, 0), (0, 1), (1, 0)]
        motif_colors = [colors[4]] * 3
    elif profile == "sparse_wide_motif":
        offsets = [(-4, -3), (-1, 0), (0, 2), (4, 3)]
        motif_colors = [colors[4]] * 4

    grid[source[0]][source[1]] = 5
    for (dr, dc), color in zip(offsets, motif_colors):
        grid[source[0] + dr][source[1] + dc] = color
    if profile == "extra_source_marker":
        grid[height - 2][0] = 5

    if profile == "clipped_copy":
        anchors = [(1, 2), (height - 3, 2), (height - 3, width - 3)]
    elif profile == "overlapping_copies":
        anchors = [(2, 2), (3, 3), (4, 4)]
    elif profile in ("disconnected_motif", "sparse_wide_motif"):
        anchors = [(5, width - 5), (height - 6, 4), (height - 6, width - 5)]
    elif legend_count == 1:
        anchors = [(2, width - 3)]
    elif legend_count == 2:
        # Row-major order alternates right then left, defeating column-order pairing.
        anchors = [(2, width - 3), (height - 3, 2)]
    elif legend_count == 4:
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
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    colors = tuple(context.draw_distinct_colors("semantic_colors", n=6, exclude={0, 5, 6}))
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
    if not errors and info["output"] == [list(row) for row in grid]:
        errors.append("broadcast lesson must change at least one cell")
    return errors
