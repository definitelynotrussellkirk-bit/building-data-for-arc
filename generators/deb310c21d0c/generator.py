"""Generator for b74ca5d1: swap motif colors and stamp core-matched corners.

Each 30x30 input has a strict modal background, four or five sparse 5x5
motifs, and two or three colored corner markers.  A motif has a majority
body color and one core cell.  The rule swaps body/core roles, with a
centered congruent twin resolving an off-center core's return color, then
stamps every motif at the corner whose marker matches its core.  Enclosing
motifs stamp only the loop around their hole.

The five public scene grammars are stored as compact role templates rather
than literal grids.  Default draws preserve every demonstrated relationship
while independently varying the palette, motif orientations, positions, and
marker corners.  A small explicit rehearsal branch reconstructs a published
input exactly; all other outputs are recomputed by the canonical rule.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "deb310c21d0c"
TASK_ID = "deb310c21d0c"
VERSION = "3.0.0"
RULE_HASH = "1c0db0725563"

SUMMARY = (
    "Build a 30x30 modal-background scene from one of five demonstrated "
    "multi-motif grammars. Each 5x5 motif has a majority body and singleton "
    "core; corner markers select core-matched motifs for stamping after the "
    "body/core swap. Palettes, D4 orientations, positions, and marker "
    "corners vary independently, with a bounded literal-public prior."
)

EXAMPLES_NEEDED = 3
EXPECTED_OUTPUT_CODOMAIN = 1_000_000
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 200_000,
    "medium": 400_000,
    "hard": 400_000,
    None: 1_000_000,
}

INVARIANTS = [
    "the input and output are 30x30 with one strict modal background",
    "the scene contains one of five demonstrated four/five-motif grammars",
    "each motif fits a 5x5 box and has one singleton core plus a majority body",
    "each distinct core color has exactly one same-colored corner marker",
    "motifs are separated so unrelated 5x5 groups cannot merge",
    "palette, motif D4 form, position, and marker corner are nuisance variables",
]

SCENE_PROFILES = (
    "five_offcenter_three_markers",
    "five_mixed_two_markers",
    "four_centered_hole_two_markers",
    "five_frame_two_markers",
    "five_twin_three_markers",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted demonstrated motif grammar",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Exact D4-invariant grouping of motif role shapes by shared core "
            "color, including marker/core correspondence."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

# A motif entry is:
#   (public_top, public_left, public_body, public_core, 5 role rows)
# where B is a body cell, C is the singleton core, and . is background.
_PROFILES = {
    "five_offcenter_three_markers": {
        "background": 2,
        "markers": (((0, 0), 9), ((0, 29), 5), ((29, 29), 1)),
        "motifs": (
            (3, 11, 4, 5, ("....B", "....B", "....B", "...CB", "BBBBB")),
            (11, 14, 0, 5, ("..BBB", "...CB", "..B.B", ".B...", "B....")),
            (19, 3, 3, 9, ("B.B..", "BBB..", "..C..", "..BBB", "..B.B")),
            (20, 20, 6, 9, ("..B..", "BBCBB", "..B..", "..B..", "..B..")),
            (22, 12, 8, 1, ("..B..", "..C..", ".B.B.", ".B.B.", "B...B")),
        ),
    },
    "five_mixed_two_markers": {
        "background": 4,
        "markers": (((0, 0), 6), ((0, 29), 3)),
        "motifs": (
            (4, 5, 1, 3, ("B...B", "...B.", "...CB", "...B.", "B...B")),
            (4, 19, 2, 3, ("..B..", ".....", "BBCBB", ".....", "..B..")),
            (14, 14, 5, 3, ("B....", "B....", "CBBBB", "B....", "B....")),
            (21, 20, 9, 6, ("B..BC", "....B", ".....", ".....", "B...B")),
            (23, 4, 8, 6, ("B....", ".B...", "B.B..", ".C.B.", "B.B.B")),
        ),
    },
    "four_centered_hole_two_markers": {
        "background": 8,
        "markers": (((0, 29), 4), ((29, 0), 7)),
        "motifs": (
            (3, 4, 2, 4, ("B...B", ".B.B.", "..C..", ".B.B.", "B...B")),
            (6, 17, 3, 4, ("BBBBB", "B...B", "BBCBB", "..B..", "..B..")),
            (17, 18, 5, 7, ("..B..", ".B.B.", "B.C.B", "..B..", "..B..")),
            (18, 4, 6, 7, ("BBBBB", "B....", "BBC..", "B....", "BBBBB")),
        ),
    },
    "five_frame_two_markers": {
        "background": 0,
        "markers": (((0, 0), 7), ((0, 29), 8)),
        "motifs": (
            (6, 7, 2, 7, ("BBBBB", "B...B", "C...B", "B...B", "BBBBB")),
            (7, 21, 5, 8, ("B.B.B", ".B.B.", "B.B.B", ".C.B.", "B.B.B")),
            (16, 14, 3, 7, ("..B..", "..B..", "CBBBB", "..B..", "..B..")),
            (17, 4, 4, 7, ("B...B", ".B.C.", "..B..", ".B.B.", "B...B")),
            (23, 19, 6, 8, ("BBBBB", ".....", "..C..", ".....", "BBBBB")),
        ),
    },
    "five_twin_three_markers": {
        "background": 5,
        "markers": (((0, 0), 0), ((0, 29), 2), ((29, 29), 9)),
        "motifs": (
            (3, 17, 4, 2, ("B.B.B", "B.B.B", "B.C.B", "B.B.B", "B.B.B")),
            (4, 5, 3, 0, ("B....", ".B...", "..C..", "...B.", "....B")),
            (11, 11, 6, 2, ("BBBBB", ".....", "BBBBC", ".....", "BBBBB")),
            (17, 19, 8, 9, ("..BBB", "..B..", "..BB.", ".C...", "B.B..")),
            (20, 4, 7, 9, ("..B..", ".....", "..B..", ".C.B.", "B..BB")),
        ),
    },
}

_CORNERS = ((0, 0), (0, 29), (29, 0), (29, 29))
_PLACEMENT_WINDOWS = (
    (4, 6, 4, 6),
    (4, 6, 20, 22),
    (12, 14, 12, 14),
    (20, 22, 4, 6),
    (20, 22, 20, 22),
)


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    converted = []
    errors = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _blank(height, width, color):
    return [
        [color for _col in range(width)]
        for _row in range(height)
    ]


def _mode_first_seen(values):
    counts = Counter(values)
    if not counts:
        return None
    best_count = max(counts.values())
    return next(
        value
        for value in values
        if counts[value] == best_count
    )


def _bbox(cells):
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def _normalize_tagged(cells):
    min_row = min(row for row, _col, _tag in cells)
    min_col = min(col for _row, col, _tag in cells)
    return tuple(sorted(
        (
            row - min_row,
            col - min_col,
            tag,
        )
        for row, col, tag in cells
    ))


def _transform_tagged(cells, transform):
    normalized = _normalize_tagged(cells)
    height = max(row for row, _col, _tag in normalized) + 1
    width = max(col for _row, col, _tag in normalized) + 1
    current = list(normalized)
    if transform >= 4:
        current = [
            (row, width - 1 - col, tag)
            for row, col, tag in current
        ]
        transform -= 4
    for _rotation in range(transform):
        current = [
            (col, height - 1 - row, tag)
            for row, col, tag in current
        ]
        height, width = width, height
    return _normalize_tagged(current)


def _canonical_tagged_key(cells):
    return min(
        _transform_tagged(cells, transform)
        for transform in range(8)
    )


def _pattern_cells(pattern):
    role = {".": 0, "B": 1, "C": 2}
    return tuple(
        (row, col, role[value])
        for row, pattern_row in enumerate(pattern)
        for col, value in enumerate(pattern_row)
        if value != "."
    )


def _canonical_shape_key(cells):
    tagged = [
        (row, col, 1)
        for row, col in cells
    ]
    return tuple(
        (row, col)
        for row, col, _tag in _canonical_tagged_key(tagged)
    )


def _components8(grid, background, *, same_color=False):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if (
                grid[row][col] == background
                or (row, col) in seen
            ):
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            component_color = grid[row][col]
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row in (-1, 0, 1):
                    for delta_col in (-1, 0, 1):
                        candidate = (
                            current_row + delta_row,
                            current_col + delta_col,
                        )
                        if (
                            (delta_row or delta_col)
                            and 0 <= candidate[0] < height
                            and 0 <= candidate[1] < width
                            and candidate not in seen
                            and grid[candidate[0]][candidate[1]]
                            != background
                            and (
                                not same_color
                                or grid[candidate[0]][candidate[1]]
                                == component_color
                            )
                        ):
                            seen.add(candidate)
                            queue.append(candidate)
            components.append(cells)
    return components


def _fits5(cells):
    top, left, bottom, right = _bbox(cells)
    return bottom - top < 5 and right - left < 5


def _merge_pass(groups):
    if not groups:
        return False, []
    first = groups[0]
    partner = next(
        (
            group
            for group in groups[1:]
            if _fits5(first + group)
        ),
        None,
    )
    if partner is not None:
        remaining = list(groups[1:])
        remaining.remove(partner)
        return True, [first + partner] + remaining
    changed, tail = _merge_pass(groups[1:])
    return changed, [first] + tail


def _merge_motifs(groups):
    while True:
        changed, groups = _merge_pass(groups)
        if not changed:
            return groups


def _blueprint_signature(profile):
    core_groups = {}
    for _top, _left, _body, core, pattern in profile["motifs"]:
        core_groups.setdefault(core, []).append(
            _canonical_tagged_key(
                _pattern_cells(pattern)
            )
        )
    return tuple(sorted(
        tuple(sorted(keys))
        for keys in core_groups.values()
    ))


_PROFILE_SIGNATURES = {
    name: _blueprint_signature(profile)
    for name, profile in _PROFILES.items()
}
_SIGNATURE_TO_PROFILE = {
    signature: name
    for name, signature in _PROFILE_SIGNATURES.items()
}
if len(_SIGNATURE_TO_PROFILE) != len(_PROFILES):
    raise RuntimeError("scene-profile signatures must be unique")


def _render_public(profile_name):
    profile = _PROFILES[profile_name]
    grid = _blank(30, 30, profile["background"])
    for (row, col), color in profile["markers"]:
        grid[row][col] = color
    for top, left, body, core, pattern in profile["motifs"]:
        for row, col, role in _pattern_cells(pattern):
            grid[top + row][left + col] = (
                body if role == 1 else core
            )
    return grid


_PUBLIC_GRIDS = {
    name: tuple(
        tuple(row)
        for row in _render_public(name)
    )
    for name in SCENE_PROFILES
}
_PUBLIC_GRID_TO_PROFILE = {
    grid: profile
    for profile, grid in _PUBLIC_GRIDS.items()
}


def _analyze_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors or len(original) != 30 or len(original[0]) != 30:
        return None
    flat = [
        value
        for row in original
        for value in row
    ]
    counts = Counter(flat)
    background = _mode_first_seen(flat)
    if any(
        counts[color] >= counts[background]
        for color in counts
        if color != background
    ):
        return None
    markers = [
        (row, col, original[row][col])
        for row, col in _CORNERS
        if original[row][col] != background
    ]
    cleared = [row[:] for row in original]
    for row, col, _color in markers:
        cleared[row][col] = background
    groups = _merge_motifs(
        _components8(cleared, background)
    )
    motifs = []
    body_colors = set()
    core_groups = {}
    for cells in groups:
        if not _fits5(cells):
            return None
        first_order = {}
        motif_counts = Counter()
        for index, (row, col) in enumerate(cells):
            color = original[row][col]
            motif_counts[color] += 1
            first_order.setdefault(color, index)
        if (
            len(motif_counts) != 2
            or min(motif_counts.values()) != 1
            or max(motif_counts.values()) <= 1
        ):
            return None
        ordered = sorted(
            motif_counts,
            key=lambda color: (
                -motif_counts[color],
                first_order[color],
            ),
        )
        body = ordered[0]
        core = ordered[-1]
        if (
            body == background
            or core == background
            or body in body_colors
        ):
            return None
        body_colors.add(body)
        tagged = [
            (
                row,
                col,
                1 if original[row][col] == body else 2,
            )
            for row, col in cells
        ]
        key = _canonical_tagged_key(tagged)
        core_groups.setdefault(core, []).append(key)
        motif_bbox = _bbox(cells)
        core_cell = next(
            (row, col)
            for row, col in cells
            if original[row][col] == core
        )
        center = (
            (motif_bbox[0] + motif_bbox[2]) // 2,
            (motif_bbox[1] + motif_bbox[3]) // 2,
        )
        motifs.append({
            "cells": cells,
            "body": body,
            "core": core,
            "core_cell": core_cell,
            "bbox": motif_bbox,
            "centered": core_cell == center,
            "role_key": key,
        })
    marker_colors = [
        color
        for _row, _col, color in markers
    ]
    if (
        len(marker_colors) != len(set(marker_colors))
        or set(marker_colors) != set(core_groups)
        or body_colors & set(core_groups)
    ):
        return None
    signature = tuple(sorted(
        tuple(sorted(keys))
        for keys in core_groups.values()
    ))
    profile = _SIGNATURE_TO_PROFILE.get(signature)
    if profile is None:
        return None
    frozen = tuple(tuple(row) for row in original)
    return {
        "scene_profile": profile,
        "background": background,
        "markers": markers,
        "motifs": motifs,
        "palette_size": len(counts),
        "exact_public": frozen in _PUBLIC_GRID_TO_PROFILE,
    }


def observe_overrides(grid):
    """Recover every declared semantic axis from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
    }


def canonical_profile_index(grid):
    """Return the demonstrated scene-profile index, or ``None``."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return SCENE_PROFILES.index(
        analysis["scene_profile"]
    )


def exact_public_profile_index(grid):
    """Return the literal public-input index, or ``None``."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    profile = _PUBLIC_GRID_TO_PROFILE.get(
        tuple(tuple(row) for row in original)
    )
    return (
        SCENE_PROFILES.index(profile)
        if profile is not None
        else None
    )


def self_check(grid, *, difficulty=None, meta=None):
    """Strictly recognize the five calibrated public motif grammars."""
    _original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return [
            "difficulty must be easy, medium, hard, or None"
        ]
    analysis = _analyze_scene(grid)
    if analysis is None:
        return [
            "expected a 30x30 strict-mode scene whose separated 5x5 "
            "body/core motifs and corner/core groups match one demonstrated "
            "D4-invariant grammar"
        ]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        requested_profile = requested.get("scene_profile")
        if (
            requested_profile is not None
            and requested_profile
            != analysis["scene_profile"]
        ):
            errors.append(
                f"scene_profile requested {requested_profile!r}, "
                f"observed {analysis['scene_profile']!r}"
            )
    return errors


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            "unknown override(s): " + ", ".join(unknown)
        )
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError("unknown scene_profile")


def _profile_options(difficulty):
    if difficulty == "easy":
        weights = (3, 5, 6, 4, 2)
    elif difficulty == "hard":
        weights = (4, 2, 3, 5, 6)
    else:
        weights = (4, 4, 4, 4, 4)
    return tuple(
        profile
        for profile, weight in zip(
            SCENE_PROFILES,
            weights,
        )
        for _repeat in range(weight)
    )


def _generalized_grid(profile_name, context):
    profile = _PROFILES[profile_name]
    original_palette = sorted({
        profile["background"],
        *(
            color
            for _position, color in profile["markers"]
        ),
        *(
            color
            for _top, _left, body, core, _pattern
            in profile["motifs"]
            for color in (body, core)
        ),
    })
    palette = context.draw_distinct_colors(
        "palette",
        n=len(original_palette),
    )
    color_map = dict(zip(original_palette, palette))
    grid = _blank(
        30,
        30,
        color_map[profile["background"]],
    )
    layout_rng = context.draw_rng("layout")
    windows = list(_PLACEMENT_WINDOWS)
    layout_rng.shuffle(windows)
    for motif_index, motif in enumerate(profile["motifs"]):
        _old_top, _old_left, body, core, pattern = motif
        min_row, max_row, min_col, max_col = windows[
            motif_index
        ]
        top = layout_rng.randint(min_row, max_row)
        left = layout_rng.randint(min_col, max_col)
        transform = context.draw_choice(
            f"motif_transform_{motif_index}",
            tuple(range(8)),
        )
        cells = _transform_tagged(
            _pattern_cells(pattern),
            transform,
        )
        for row, col, role in cells:
            grid[top + row][left + col] = (
                color_map[body]
                if role == 1
                else color_map[core]
            )
    corners = list(_CORNERS)
    marker_colors = [
        color_map[color]
        for _position, color in profile["markers"]
    ]
    layout_rng.shuffle(corners)
    layout_rng.shuffle(marker_colors)
    for (row, col), color in zip(
        corners,
        marker_colors,
    ):
        grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    literal_rng = context.draw_rng("literal_public")
    if literal_rng.randrange(20) == 0:
        grid = [
            list(row)
            for row in _PUBLIC_GRIDS[profile]
        ]
    else:
        grid = _generalized_grid(profile, context)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid calibrated scene: "
            + "; ".join(errors)
        )
    return grid


def _rule_motifs(grid, background):
    groups = _merge_motifs(
        _components8(
            grid,
            background,
            same_color=True,
        )
    )
    motifs = []
    for cells in groups:
        first_order = {}
        counts = Counter()
        for index, (row, col) in enumerate(cells):
            color = grid[row][col]
            counts[color] += 1
            first_order.setdefault(color, index)
        if len(counts) < 2:
            continue
        ordered = sorted(
            counts,
            key=lambda color: (
                -counts[color],
                first_order[color],
            ),
        )
        body = ordered[0]
        core = ordered[-1]
        core_cell = next(
            (row, col)
            for row, col in cells
            if grid[row][col] == core
        )
        motif_bbox = _bbox(cells)
        center = (
            (motif_bbox[0] + motif_bbox[2]) // 2,
            (motif_bbox[1] + motif_bbox[3]) // 2,
        )
        motifs.append({
            "cells": cells,
            "body": body,
            "core": core,
            "core_cell": core_cell,
            "bbox": motif_bbox,
            "centered": core_cell == center,
            "shape_key": _canonical_shape_key(cells),
        })
    return motifs


def _hole_cells(motif):
    top, left, bottom, right = motif["bbox"]
    own = set(motif["cells"])
    seeds = [
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (
            (row in (top, bottom) or col in (left, right))
            and (row, col) not in own
        )
    ]
    visited = set(seeds)
    queue = list(seeds)
    for row, col in queue:
        for delta_row in (-1, 0, 1):
            for delta_col in (-1, 0, 1):
                candidate = (
                    row + delta_row,
                    col + delta_col,
                )
                if (
                    top <= candidate[0] <= bottom
                    and left <= candidate[1] <= right
                    and candidate not in own
                    and candidate not in visited
                ):
                    visited.add(candidate)
                    queue.append(candidate)
    return [
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (
            (row, col) not in own
            and (row, col) not in visited
        )
    ]


def _stamp_cells(motif):
    holes = _hole_cells(motif)
    if not holes:
        return motif["cells"]
    return [
        (row, col)
        for row, col in motif["cells"]
        if any(
            abs(row - hole_row) <= 1
            and abs(col - hole_col) <= 1
            for hole_row, hole_col in holes
        )
    ]


def rule_mirror(grid):
    """Broad, input-pure Python mirror of the canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height = len(original)
    width = len(original[0])
    flat = [
        value
        for row in original
        for value in row
    ]
    background = _mode_first_seen(flat)
    corner_positions = (
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    )
    markers = [
        (row, col, original[row][col])
        for row, col in corner_positions
        if original[row][col] != background
    ]
    cleared = [row[:] for row in original]
    for row, col, _color in markers:
        cleared[row][col] = background
    motifs = _rule_motifs(cleared, background)
    output = [row[:] for row in original]
    for motif in motifs:
        target = motif["body"]
        if not motif["centered"]:
            twin = next(
                (
                    candidate
                    for candidate in motifs
                    if candidate is not motif
                    and candidate["core"] == motif["core"]
                    and candidate["centered"]
                    and candidate["shape_key"]
                    == motif["shape_key"]
                ),
                None,
            )
            if twin is not None:
                target = twin["body"]
        for row, col in motif["cells"]:
            output[row][col] = (
                motif["core"]
                if original[row][col] == motif["body"]
                else target
            )
    for marker_row, marker_col, marker_color in markers:
        for motif in motifs:
            if motif["core"] != marker_color:
                continue
            top, left, bottom, right = motif["bbox"]
            box_height = bottom - top + 1
            box_width = right - left + 1
            base_row = (
                0
                if marker_row == 0
                else height - box_height
            )
            base_col = (
                0
                if marker_col == 0
                else width - box_width
            )
            for row, col in _stamp_cells(motif):
                output[
                    base_row + row - top
                ][
                    base_col + col - left
                ] = marker_color
    return output
