"""Generate frame-filling lessons controlled by the cue's full bbox edges."""

from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "c130e51c4310"
TASK_ID = "c130e51c4310"
VERSION = "3.0.0"
RULE_HASH = "3d57c85d52e8"
SUMMARY = (
    "Erase a colored cue outside a purple frame, then copy the cue's "
    "full bounding-box edges to the corresponding inner frame edges; "
    "if all four cue edges are full, fill the complete frame interior."
)

PUBLIC_PROFILES = (
    "public_solid_2x2",
    "public_singleton",
    "public_bottom_left_l",
    "public_top_right_l",
)
EXTRAPOLATION_PROFILES = (
    "single_edge",
    "adjacent_edges",
    "opposite_edges",
    "three_edges",
    "all_edges",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng across complete linked and edge profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
}

INVARIANTS = [
    "the unique modal background is color 7 and no color 0 is present",
    "one exact hollow rectangular color-6 frame has dimensions 3..8",
    "one connected single-color cue lies wholly outside the frame bbox",
    "at least one cue bounding-box edge is completely filled",
    "the output erases the cue and paints the matching inner frame edges",
]

_LEGAL_CUE_COLORS = (1, 2, 3, 4, 5, 8, 9)
_TRANSFORMS = (
    "identity",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "horizontal_flip",
    "vertical_flip",
    "main_diagonal",
    "anti_diagonal",
)
_WEIGHTED_PROFILES = {
    band: (
        *PUBLIC_PROFILES,
        *(("single_edge",) * 3),
        *(("adjacent_edges",) * 3),
        *(("opposite_edges",) * 2),
        *(("three_edges",) * 2),
        *(("all_edges",) * 2),
    )
    for band in ("easy", "medium", "hard")
}

_EDGE_OPTIONS = {
    "single_edge": (
        (True, False, False, False),
        (False, True, False, False),
        (False, False, True, False),
        (False, False, False, True),
    ),
    "adjacent_edges": (
        (True, False, True, False),
        (True, False, False, True),
        (False, True, True, False),
        (False, True, False, True),
    ),
    "opposite_edges": (
        (True, True, False, False),
        (False, False, True, True),
    ),
    "three_edges": (
        (False, True, True, True),
        (True, False, True, True),
        (True, True, False, True),
        (True, True, True, False),
    ),
    "all_edges": ((True, True, True, True),),
}


def _decode(*encoded):
    width = len(encoded[0])
    if any(len(row) != width for row in encoded):
        raise RuntimeError("public profile encoding must be rectangular")
    return [[int(value) for value in row] for row in encoded]


_PUBLIC_ROLE_GRIDS = {
    "public_solid_2x2": _decode(
        "7777777777",
        "7666667777",
        "7677767777",
        "7677767777",
        "7677767777",
        "7666667777",
        "7777777777",
        "7117777777",
        "7117777777",
        "7777777777",
    ),
    "public_singleton": _decode(
        "7777777777",
        "7666777777",
        "7676777777",
        "7666777777",
        "7777777777",
        "7777777777",
        "7777777777",
        "7777777777",
        "7777777717",
        "7777777777",
    ),
    "public_bottom_left_l": _decode(
        "7177777777",
        "7117777777",
        "7777777777",
        "7666666777",
        "7677776777",
        "7677776777",
        "7677776777",
        "7677776777",
        "7666666777",
        "7777777777",
    ),
    "public_top_right_l": _decode(
        "7777777711",
        "7777777771",
        "6666666677",
        "6777777677",
        "6777777677",
        "6777777677",
        "6777777677",
        "6777777677",
        "6777777677",
        "6666666677",
    ),
}

_PUBLIC_ORIGINAL_COLORS = {
    "public_solid_2x2": 5,
    "public_singleton": 2,
    "public_bottom_left_l": 8,
    "public_top_right_l": 9,
}


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
    raise KeyError(name)


def _role_signature(grid):
    cue_colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (6, 7)
        }
    )
    if len(cue_colors) != 1:
        return ()
    cue_color = cue_colors[0]
    return tuple(
        tuple(1 if value == cue_color else value for value in row)
        for row in grid
    )


_PUBLIC_LOOKUP = {
    _role_signature(grid): profile
    for profile, grid in _PUBLIC_ROLE_GRIDS.items()
}


def _canonical_answer_profile(grid):
    for transform in _TRANSFORMS:
        profile = _PUBLIC_LOOKUP.get(
            _role_signature(_transform(grid, transform))
        )
        if profile is not None:
            return profile
    return None


def _components(cells):
    remaining = set(cells)
    groups = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        group = {start}
        while stack:
            row, col = stack.pop()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    stack.append(neighbor)
        groups.append(group)
    return groups


def _bbox(cells):
    return (
        min(row for row, col in cells),
        min(col for row, col in cells),
        max(row for row, col in cells),
        max(col for row, col in cells),
    )


def _frame_info(grid):
    six_cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    }
    groups = _components(six_cells)
    if len(groups) != 1:
        return None
    cells = groups[0]
    row1, col1, row2, col2 = _bbox(cells)
    border = {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
        if row in (row1, row2) or col in (col1, col2)
    }
    if cells != border:
        return None
    return {
        "bbox": (row1, col1, row2, col2),
        "height": row2 - row1 + 1,
        "width": col2 - col1 + 1,
        "cells": len(cells),
    }


def _cue_info(grid):
    cells_with_color = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (6, 7)
    ]
    colors = {value for _, _, value in cells_with_color}
    if len(colors) != 1:
        return None
    color = next(iter(colors))
    cells = {(row, col) for row, col, _ in cells_with_color}
    if not cells:
        return None
    row1, col1, row2, col2 = _bbox(cells)
    height = row2 - row1 + 1
    width = col2 - col1 + 1
    mask = tuple(
        tuple((row1 + row, col1 + col) in cells for col in range(width))
        for row in range(height)
    )
    edges = (
        all(mask[0][col] for col in range(width)),
        all(mask[-1][col] for col in range(width)),
        all(mask[row][0] for row in range(height)),
        all(mask[row][-1] for row in range(height)),
    )
    return {
        "color": color,
        "cells_set": cells,
        "cells": len(cells),
        "bbox": (row1, col1, row2, col2),
        "height": height,
        "width": width,
        "mask": mask,
        "edges": edges,
        "component_count": len(_components(cells)),
    }


def _edge_label(edges):
    top, bottom, left, right = edges
    count = sum(edges)
    if count == 1:
        return "single_edge"
    if count == 2:
        if (top and bottom) or (left and right):
            return "opposite_edges"
        return "adjacent_edges"
    if count == 3:
        return "three_edges"
    if count == 4:
        return "all_edges"
    return None


def solve_python(grid):
    """Input-pure mirror of the authoritative cue-edge Racket rule."""
    frame = _frame_info(grid)
    cue = _cue_info(grid)
    if frame is None or cue is None:
        raise ValueError("missing exact frame or cue")
    output = [row[:] for row in grid]
    for row, col in cue["cells_set"]:
        output[row][col] = 7
    row1, col1, row2, col2 = frame["bbox"]
    inner_row1, inner_col1 = row1 + 1, col1 + 1
    inner_row2, inner_col2 = row2 - 1, col2 - 1
    top, bottom, left, right = cue["edges"]
    if all(cue["edges"]):
        for row in range(inner_row1, inner_row2 + 1):
            for col in range(inner_col1, inner_col2 + 1):
                output[row][col] = cue["color"]
        return output
    if top:
        for col in range(inner_col1, inner_col2 + 1):
            output[inner_row1][col] = cue["color"]
    if bottom:
        for col in range(inner_col1, inner_col2 + 1):
            output[inner_row2][col] = cue["color"]
    if left:
        for row in range(inner_row1, inner_row2 + 1):
            output[row][inner_col1] = cue["color"]
    if right:
        for row in range(inner_row1, inner_row2 + 1):
            output[row][inner_col2] = cue["color"]
    return output


def _analyze(grid):
    reasons = []
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {"strict": False, "reasons": ["empty_or_non_grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"strict": False, "reasons": ["ragged"]}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"strict": False, "reasons": ["invalid_arc_value"]}

    height = len(grid)
    if not 10 <= height <= 18 or not 10 <= width <= 18:
        reasons.append("dimension_range")
    counts = Counter(value for row in grid for value in row)
    max_count = max(counts.values())
    modes = [
        color for color, count in counts.items() if count == max_count
    ]
    background = modes[0]
    if len(modes) != 1 or background != 7:
        reasons.append("background_role")
    if 0 in counts:
        reasons.append("zero_present")

    frame = _frame_info(grid)
    if frame is None:
        reasons.append("exact_frame")
    elif not (
        3 <= frame["height"] <= 8
        and 3 <= frame["width"] <= 8
    ):
        reasons.append("frame_dimensions")

    cue = _cue_info(grid)
    if cue is None:
        reasons.append("exact_cue")
    else:
        if cue["color"] not in _LEGAL_CUE_COLORS:
            reasons.append("cue_color")
        if cue["component_count"] != 1:
            reasons.append("cue_connectivity")
        if not (
            1 <= cue["height"] <= 5
            and 1 <= cue["width"] <= 5
            and 1 <= cue["cells"] <= 25
        ):
            reasons.append("cue_dimensions")
        if _edge_label(cue["edges"]) is None:
            reasons.append("empty_edge_signature")
    if frame is not None and cue is not None:
        fr1, fc1, fr2, fc2 = frame["bbox"]
        if any(
            fr1 <= row <= fr2 and fc1 <= col <= fc2
            for row, col in cue["cells_set"]
        ):
            reasons.append("cue_overlaps_frame_bbox")

    try:
        output = solve_python(grid)
    except Exception as exc:
        reasons.append(f"oracle:{type(exc).__name__}")
        output = grid
    if output == grid:
        reasons.append("identity")
    answer_profile = _canonical_answer_profile(grid)
    edge_label = (
        _edge_label(cue["edges"]) if cue is not None else None
    )
    scene_profile = answer_profile or edge_label
    if scene_profile is None:
        reasons.append("unclassified_scene")
    return {
        "strict": not reasons,
        "reasons": sorted(set(reasons)),
        "height": height,
        "width": width,
        "background": background,
        "frame_height": frame["height"] if frame else None,
        "frame_width": frame["width"] if frame else None,
        "frame_bbox": frame["bbox"] if frame else None,
        "cue_color": cue["color"] if cue else None,
        "cue_height": cue["height"] if cue else None,
        "cue_width": cue["width"] if cue else None,
        "cue_cells": cue["cells"] if cue else None,
        "edge_signature": (
            "".join("1" if value else "0" for value in cue["edges"])
            if cue
            else None
        ),
        "edge_label": edge_label,
        "canonical_answer_profile": answer_profile,
        "scene_profile": scene_profile,
        "changed_cells": sum(
            first != second
            for first_row, second_row in zip(grid, output)
            for first, second in zip(first_row, second_row)
        ),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete frame/cue lesson from the returned grid."""
    return _analyze(grid)["reasons"]


def observe_overrides(grid):
    """Recover the declared semantic control from the returned grid."""
    analysis = _analyze(grid)
    if not analysis["strict"]:
        raise ValueError(f"cannot observe invalid grid: {analysis['reasons']}")
    return {"scene_profile": analysis["scene_profile"]}


def _public_grid(profile, color_rng, transform_rng):
    color = color_rng.choice(_LEGAL_CUE_COLORS)
    transform = transform_rng.choice(_TRANSFORMS)
    grid = [
        [color if value == 1 else value for value in row]
        for row in _PUBLIC_ROLE_GRIDS[profile]
    ]
    transformed = _transform(grid, transform)
    literal = [
        [
            _PUBLIC_ORIGINAL_COLORS[profile] if value == 1 else value
            for value in row
        ]
        for row in _PUBLIC_ROLE_GRIDS[profile]
    ]
    if transformed == literal:
        replacement = _LEGAL_CUE_COLORS[
            (_LEGAL_CUE_COLORS.index(color) + 1) % len(_LEGAL_CUE_COLORS)
        ]
        transformed = [
            [
                replacement if value == color else value
                for value in row
            ]
            for row in transformed
        ]
    return transformed


def _band_geometry(band, rng):
    if band == "easy":
        height = rng.randint(10, 12)
        width = rng.randint(10, 12)
        frame_range = (3, 5)
        cue_range = (3, 3)
    elif band == "hard":
        height = rng.randint(14, 18)
        width = rng.randint(14, 18)
        frame_range = (5, 8)
        cue_range = (3, 5)
    else:
        height = rng.randint(11, 15)
        width = rng.randint(11, 15)
        frame_range = (4, 7)
        cue_range = (3, 4)
    return height, width, frame_range, cue_range


def _cue_mask(height, width, edges, rng):
    top, bottom, left, right = edges
    mask = [[False for _ in range(width)] for _ in range(height)]
    if top:
        for col in range(width):
            mask[0][col] = True
    if bottom:
        for col in range(width):
            mask[-1][col] = True
    if left:
        for row in range(height):
            mask[row][0] = True
    if right:
        for row in range(height):
            mask[row][-1] = True

    count = sum(edges)
    if count == 1:
        if top or bottom:
            col = width // 2
            for row in range(height):
                mask[row][col] = True
        else:
            row = height // 2
            for col in range(width):
                mask[row][col] = True
    elif count == 2 and top and bottom:
        col = width // 2
        for row in range(height):
            mask[row][col] = True
    elif count == 2 and left and right:
        row = height // 2
        for col in range(width):
            mask[row][col] = True

    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(interior)
    extra_count = rng.randint(0, max(0, len(interior) // 3))
    for _ in range(extra_count):
        candidates = [
            (row, col)
            for row, col in interior
            if not mask[row][col]
            and any(
                mask[row + drow][col + dcol]
                for drow, dcol in (
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                )
            )
        ]
        if not candidates:
            break
        row, col = rng.choice(candidates)
        mask[row][col] = True
    return mask


def _synthetic_candidate(profile, band, rng):
    height, width, frame_range, cue_range = _band_geometry(band, rng)
    frame_height = rng.randint(*frame_range)
    frame_width = rng.randint(*frame_range)
    if profile == "all_edges" and rng.randrange(4) == 0:
        cue_height = cue_width = 1
    else:
        cue_height = rng.randint(*cue_range)
        cue_width = rng.randint(*cue_range)
    placements = []
    for frame_row in range(height - frame_height + 1):
        for frame_col in range(width - frame_width + 1):
            frame_row2 = frame_row + frame_height - 1
            frame_col2 = frame_col + frame_width - 1
            for cue_row in range(height - cue_height + 1):
                for cue_col in range(width - cue_width + 1):
                    cue_row2 = cue_row + cue_height - 1
                    cue_col2 = cue_col + cue_width - 1
                    disjoint = (
                        cue_row2 < frame_row
                        or cue_row > frame_row2
                        or cue_col2 < frame_col
                        or cue_col > frame_col2
                    )
                    if disjoint:
                        placements.append(
                            (frame_row, frame_col, cue_row, cue_col)
                        )
    if not placements:
        raise RuntimeError("no feasible frame/cue placement")
    frame_row, frame_col, cue_row, cue_col = rng.choice(placements)
    edges = rng.choice(_EDGE_OPTIONS[profile])
    cue_mask = _cue_mask(cue_height, cue_width, edges, rng)
    cue_color = rng.choice(_LEGAL_CUE_COLORS)
    grid = [[7 for _ in range(width)] for _ in range(height)]
    for row in range(frame_height):
        for col in range(frame_width):
            if row in (0, frame_height - 1) or col in (
                0,
                frame_width - 1,
            ):
                grid[frame_row + row][frame_col + col] = 6
    for row in range(cue_height):
        for col in range(cue_width):
            if cue_mask[row][col]:
                grid[cue_row + row][cue_col + col] = cue_color
    return grid


def _synthetic_grid(profile, band, rng):
    for _ in range(256):
        grid = _synthetic_candidate(profile, band, rng)
        analysis = _analyze(grid)
        if analysis["strict"] and analysis["scene_profile"] == profile:
            return grid
    raise RuntimeError(f"failed to construct profile {profile!r}")


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
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    profile = ctx.draw_choice(
        "scene_profile",
        _WEIGHTED_PROFILES[band],
    )
    if profile in PUBLIC_PROFILES:
        grid = _public_grid(
            profile,
            ctx.draw_rng("public_color"),
            ctx.draw_rng("public_transform"),
        )
    elif profile in EXTRAPOLATION_PROFILES:
        grid = _synthetic_grid(
            profile,
            band,
            ctx.draw_rng("synthetic_scene"),
        )
    else:
        raise RuntimeError(f"unhandled scene profile {profile!r}")
    analysis = _analyze(grid)
    if not analysis["strict"] or analysis["scene_profile"] != profile:
        raise RuntimeError(
            f"internal generation contract failed: {analysis['reasons']}"
        )
    return grid
