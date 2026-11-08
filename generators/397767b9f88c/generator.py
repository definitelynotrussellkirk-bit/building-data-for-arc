"""Semantic generator for ARC task ``397767b9f88c``.

The rule ignores object colors.  It binarizes every nonzero cell, extracts
4-connected components in top-left reading order, and emits a square matrix
whose entries are red(2) exactly when the two component masks are equivalent
under a rotation or reflection.

The curriculum deliberately breaks tempting shortcuts.  Every ordinary draw
contains a matching pair that specifically requires a diagonal reflection, plus
a non-matching pair with the same area, the same D4-invariant bounding-box
dimensions, and the same color histogram.  Thus neither rotations plus only
horizontal/vertical reflections, size, box shape, exact orientation, nor color
statistics can stand in for the true eight-transform dihedral relation.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "397767b9f88c"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "b36e2b403189"

SUMMARY = (
    "Treat every 4-connected nonzero component as a color-blind shape, order "
    "the components by top-left position, and output an N×N grid with red(2) "
    "where two masks are equivalent under any of the eight dihedral "
    "transforms and 0 otherwise. Generated scenes use canonical canvas/palette "
    "profiles and include explicit same-area/same-bbox/color-histogram "
    "near-misses plus reflection-only positive matches."
)

INVARIANTS = [
    "background is 0 and all nonzero colors are object-mask cells",
    "objects are 4-connected components ordered by top-left bounding-box position",
    "output depends only on component masks, not on the colors painted inside them",
    "matrix entry (i,j) is 2 iff object i and object j are equivalent under D4",
]

# All profiles use an exact canonical (height, width, palette-size) triple.
# The added object/class counts vary the relation matrix without drifting away
# from the task's observed canvas/palette envelope.  Each 5-tuple is unique, so
# ``scene_profile`` is recoverable from the returned grid.
_PROFILE_ROWS = (
    ("p01_7x15_c3_n3_k2", 7, 15, 3, 3, 2),
    ("p02_7x15_c3_n4_k2", 7, 15, 3, 4, 2),
    ("p03_8x16_c4_n6_k5", 8, 16, 4, 6, 5),
    ("p04_8x16_c4_n4_k3", 8, 16, 4, 4, 3),
    ("p05_8x17_c3_n3_k2", 8, 17, 3, 3, 2),
    ("p06_8x17_c3_n5_k3", 8, 17, 3, 5, 3),
    ("p07_8x17_c4_n4_k2", 8, 17, 4, 4, 2),
    ("p08_8x17_c4_n5_k3", 8, 17, 4, 5, 3),
    ("p09_9x18_c3_n3_k2", 9, 18, 3, 3, 2),
    ("p10_9x18_c3_n4_k3", 9, 18, 3, 4, 3),
    ("p11_9x18_c3_n5_k4", 9, 18, 3, 5, 4),
    ("p12_9x18_c3_n6_k4", 9, 18, 3, 6, 4),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {row[1:]: row[0] for row in _PROFILE_ROWS}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic keyed draw over canonical-profile scene families",
        "valid": "p01_7x15_c3_n3_k2|p02_7x15_c3_n4_k2|p03_8x16_c4_n6_k5|p04_8x16_c4_n4_k3|p05_8x17_c3_n3_k2|p06_8x17_c3_n5_k3|p07_8x17_c4_n4_k2|p08_8x17_c4_n5_k3|p09_9x18_c3_n3_k2|p10_9x18_c3_n4_k3|p11_9x18_c3_n5_k4|p12_9x18_c3_n6_k4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

# L4 and T4 deliberately have the same area and unordered bounding-box
# dimensions while remaining distinct D4 classes.  Pairing L4 transform 0 with
# transform 5 requires a diagonal reflection and directly refutes the previously
# surviving six-transform rule (rotations plus horizontal/vertical reflections).
# I3 and P5
# add size-3 and size-5 components seen in the canonical examples, preventing a
# fixed-object-size curriculum from becoming an accidental shortcut.
_SHAPES = {
    "L4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "I3": ((0, 0), (0, 1), (0, 2)),
    "P5": ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    "X5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
}
_CLASSES_BY_COUNT = {
    2: ("L4", "T4"),
    3: ("L4", "T4", "I3"),
    4: ("L4", "T4", "I3", "P5"),
    5: ("L4", "T4", "I3", "P5", "X5"),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return tuple(sorted((r - rmin, c - cmin) for r, c in cells))


def _dihedral(
    cells: Sequence[tuple[int, int]], transform: int
) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for r, c in cells:
        if transform == 0:
            out.append((r, c))
        elif transform == 1:
            out.append((c, -r))
        elif transform == 2:
            out.append((-r, -c))
        elif transform == 3:
            out.append((-c, r))
        elif transform == 4:
            out.append((r, -c))
        elif transform == 5:
            out.append((-c, -r))
        elif transform == 6:
            out.append((-r, c))
        elif transform == 7:
            out.append((c, r))
        else:
            raise ValueError(f"unknown dihedral transform {transform}")
    return _norm(out)


def _d4_key(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_dihedral(cells, transform) for transform in range(8))


def _rotation_key(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_dihedral(cells, transform) for transform in range(4))


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC dimensions: {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _mask_components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    """Extract the same color-blind 4-connected mask components as the Racket."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    parts: list[dict[str, Any]] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rmin = min(r for r, _ in cells)
            cmin = min(c for _, c in cells)
            rmax = max(r for r, _ in cells)
            cmax = max(c for _, c in cells)
            shape = _norm(cells)
            color_hist = tuple(sorted(Counter(grid[r][c] for r, c in cells).items()))
            parts.append(
                {
                    "cells": tuple(sorted(cells)),
                    "shape": shape,
                    "d4_key": _d4_key(shape),
                    "rotation_key": _rotation_key(shape),
                    "size": len(cells),
                    "bbox": (rmax - rmin + 1, cmax - cmin + 1),
                    "bbox_unordered": tuple(sorted((rmax - rmin + 1, cmax - cmin + 1))),
                    "color_hist": color_hist,
                    "top_left": (rmin, cmin),
                }
            )
    parts.sort(key=lambda obj: obj["top_left"])
    return parts


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    parts = _mask_components(grid)
    palette_size = len({value for row in grid for value in row})
    class_count = len({obj["d4_key"] for obj in parts})
    profile = _PROFILE_BY_SIGNATURE.get(
        (height, width, palette_size, len(parts), class_count)
    )
    return {
        "errors": [],
        "height": height,
        "width": width,
        "palette_size": palette_size,
        "parts": parts,
        "n_objects": len(parts),
        "n_classes": class_count,
        "scene_profile": profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical grammar and reject malformed/rule-hiding masks."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    parts = analysis["parts"]
    if 0 not in {value for row in grid for value in row}:
        errors.append("background color 0 must be present")
    if not 3 <= len(parts) <= 6:
        errors.append(f"expected 3..6 nonzero mask objects, found {len(parts)}")
    for index, obj in enumerate(parts):
        if not 3 <= obj["size"] <= 6:
            errors.append(
                f"object {index} must contain 3..6 mask cells, found {obj['size']}"
            )
        if obj["bbox"][0] > 3 or obj["bbox"][1] > 3:
            errors.append(
                f"object {index} bbox {obj['bbox']} exceeds the task's 3x3 object envelope"
            )

    requested = _meta_overrides(meta).get("scene_profile")
    if requested is not None:
        observed = observe_overrides(grid).get("scene_profile")
        if observed != requested:
            errors.append(
                f"override scene_profile={requested!r} realized as {observed!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact declared scene profile from a generated grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _slot_anchors(height: int, width: int) -> list[tuple[int, int]]:
    """Six disjoint 3x3 slots with at least one background line between rows."""
    row_starts = (0, height - 3)
    col_starts = (0, (width - 3) // 2, width - 3)
    return [(r, c) for r in row_starts for c in col_starts]


def _paint_object(
    grid: list[list[int]],
    cells: Sequence[tuple[int, int]],
    r0: int,
    c0: int,
    palette: Sequence[int],
    rng,
    *,
    multicolor: bool,
) -> None:
    # Most objects stay a single solid color, matching the canonical component
    # statistics.  Exactly the reflected L witness is multicolor and uses every
    # nonzero palette color: it proves that component extraction is color-blind.
    # A monochrome L and monochrome T still share the exact same color
    # histogram, so color statistics also fail as a negative-pair shortcut.
    if not multicolor:
        colors = [palette[0]] * len(cells)
    elif len(palette) == 2:
        colors = [palette[0], palette[0], palette[1], palette[1]]
    elif len(palette) == 3:
        colors = [palette[0], palette[0], palette[1], palette[2]]
    else:
        raise ValueError(f"unexpected nonzero palette size {len(palette)}")
    rng.shuffle(colors)
    for (r, c), color in zip(sorted(cells), colors):
        grid[r0 + r][c0 + c] = color


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
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    height, width, palette_size, n_objects, n_classes = _PROFILE_BY_NAME[profile]
    palette = ctx.draw_distinct_colors("palette", n=palette_size - 1, exclude=[0])
    # Include difficulty in the layout salt without turning it into an AXIS;
    # the task semantics stay identical while the three requested bands do not
    # collapse to byte-identical same-seed layouts.
    band = "medium" if difficulty is None else str(difficulty)
    rng = ctx.draw_rng(f"layout:{band}")

    classes = list(_CLASSES_BY_COUNT[n_classes])
    # Profiles always have n_objects > n_classes.  Repeat L4 first so every
    # scene contains a positive pair that we can force to reflection-only.
    assignments = classes + ["L4"]
    while len(assignments) < n_objects:
        assignments.append(rng.choice(classes))
    rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    anchors = _slot_anchors(height, width)
    chosen_slots = sorted(rng.sample(range(len(anchors)), n_objects))
    l4_seen = 0
    for class_name, slot_index in zip(assignments, chosen_slots):
        base = _SHAPES[class_name]
        multicolor = False
        if class_name == "L4" and l4_seen == 0:
            transform = 0
            l4_seen += 1
        elif class_name == "L4" and l4_seen == 1:
            transform = 5
            l4_seen += 1
            multicolor = True
        else:
            transform = rng.randint(0, 7)
            if class_name == "L4":
                l4_seen += 1
        cells = _dihedral(base, transform)
        box_h = max(r for r, _ in cells) + 1
        box_w = max(c for _, c in cells) + 1
        slot_r, slot_c = anchors[slot_index]
        r0 = slot_r + rng.randint(0, 3 - box_h)
        c0 = slot_c + rng.randint(0, 3 - box_w)
        _paint_object(grid, cells, r0, c0, palette, rng, multicolor=multicolor)

    # This should be construction-invariant; fail loudly rather than silently
    # emitting a mislabeled axis value if a future edit breaks the profile.
    observed = observe_overrides(grid).get("scene_profile")
    if observed != profile:
        raise RuntimeError(f"constructed scene_profile {profile!r} observed as {observed!r}")
    return grid


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror used only for semantic tests/rivals."""
    parts = _mask_components(grid)
    return [
        [2 if left["d4_key"] == right["d4_key"] else 0 for right in parts]
        for left in parts
    ]


def strict_canonical_like(grid) -> list[str]:
    """Task-linked structural predicate that also accepts every canonical input."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"], analysis["palette_size"]) not in {
        (7, 15, 3),
        (8, 16, 4),
        (8, 17, 3),
        (8, 17, 4),
        (9, 18, 3),
    }:
        errors.append("canvas/palette profile is outside the canonical support")
    return errors


def _pairwise_matrix(grid, predicate: Callable[[dict[str, Any], dict[str, Any]], bool]):
    parts = _mask_components(grid)
    return [
        [2 if predicate(left, right) else 0 for right in parts]
        for left in parts
    ]


def _rival_diagonal_only(grid):
    parts = _mask_components(grid)
    return [[2 if i == j else 0 for j in range(len(parts))] for i in range(len(parts))]


def _rival_all_equivalent(grid):
    n = len(_mask_components(grid))
    return [[2 for _ in range(n)] for _ in range(n)]


def _rival_same_area(grid):
    return _pairwise_matrix(grid, lambda a, b: a["size"] == b["size"])


def _rival_same_bbox(grid):
    return _pairwise_matrix(
        grid, lambda a, b: a["bbox_unordered"] == b["bbox_unordered"]
    )


def _rival_rotation_only(grid):
    return _pairwise_matrix(grid, lambda a, b: a["rotation_key"] == b["rotation_key"])


def _rival_exact_shape(grid):
    return _pairwise_matrix(grid, lambda a, b: a["shape"] == b["shape"])


_AXIS_TRANSFORMS = (0, 1, 2, 3, 4, 6)


def _axis_transform_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return any(_dihedral(left["shape"], transform) == right["shape"]
               for transform in _AXIS_TRANSFORMS)


def _rival_axis_reflections_only(grid):
    return _pairwise_matrix(grid, _axis_transform_match)


def _rival_same_color_histogram(grid):
    return _pairwise_matrix(grid, lambda a, b: a["color_hist"] == b["color_hist"])


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "diagonal_only": _rival_diagonal_only,
    "all_equivalent": _rival_all_equivalent,
    "same_area": _rival_same_area,
    "same_bbox_dimensions": _rival_same_bbox,
    "rotation_only": _rival_rotation_only,
    "exact_orientation_only": _rival_exact_shape,
    "rotations_and_axis_reflections_only": _rival_axis_reflections_only,
    "same_color_histogram": _rival_same_color_histogram,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _offdiag_match(grid) -> bool:
    matrix = rule_mirror(grid)
    return any(matrix[i][j] == 2 for i in range(len(matrix)) for j in range(len(matrix)) if i != j)


def _offdiag_mismatch(grid) -> bool:
    matrix = rule_mirror(grid)
    return any(matrix[i][j] == 0 for i in range(len(matrix)) for j in range(len(matrix)) if i != j)


def _same_feature_negative(grid, feature: str) -> bool:
    parts = _mask_components(grid)
    for i, left in enumerate(parts):
        for j, right in enumerate(parts):
            if i >= j:
                continue
            if left[feature] == right[feature] and left["d4_key"] != right["d4_key"]:
                return True
    return False


def _reflection_needed(grid) -> bool:
    parts = _mask_components(grid)
    for i, left in enumerate(parts):
        for j, right in enumerate(parts):
            if i >= j or left["d4_key"] != right["d4_key"]:
                continue
            if left["rotation_key"] != right["rotation_key"]:
                return True
    return False


def _diagonal_reflection_needed(grid) -> bool:
    parts = _mask_components(grid)
    for i, left in enumerate(parts):
        for j, right in enumerate(parts):
            if i >= j or left["d4_key"] != right["d4_key"]:
                continue
            if not _axis_transform_match(left, right):
                return True
    return False


SEMANTIC_WITNESSES = {
    "off_diagonal_positive": _offdiag_match,
    "off_diagonal_negative": _offdiag_mismatch,
    "same_area_but_not_equivalent": lambda grid: _same_feature_negative(grid, "size"),
    "same_bbox_but_not_equivalent": lambda grid: _same_feature_negative(
        grid, "bbox_unordered"
    ),
    "same_color_histogram_but_not_equivalent": lambda grid: _same_feature_negative(
        grid, "color_hist"
    ),
    "reflection_required_for_positive_pair": _reflection_needed,
    "diagonal_reflection_required": _diagonal_reflection_needed,
}
WITNESS_RIVALS = {
    "off_diagonal_positive": ["diagonal_only"],
    "off_diagonal_negative": ["all_equivalent"],
    "same_area_but_not_equivalent": ["same_area"],
    "same_bbox_but_not_equivalent": ["same_bbox_dimensions"],
    "same_color_histogram_but_not_equivalent": ["same_color_histogram"],
    "reflection_required_for_positive_pair": [
        "rotation_only",
        "exact_orientation_only",
    ],
    "diagonal_reflection_required": ["rotations_and_axis_reflections_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named shortcut can still change the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the dihedral-equivalence rule")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the dihedral-equivalence rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives_demos = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives_demos and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
