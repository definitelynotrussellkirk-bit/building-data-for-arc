"""Semantic generator for ARC task ``4b57f748d763``.

Each nonzero color marks exactly three corners of its own axis-aligned
rectangle.  The output preserves the input and paints the complete outline of
each rectangle in that rectangle's color.  Two or three rectangles are always
present, so color independence is visible rather than an optional edge case.

The default distribution keeps all five public input profiles as linked units
(up to translation, color renaming, and D4 symmetry) and mixes them with four
generalized profiles.  Generalized scenes vary border contact, rectangle count,
and aspect ratio while retaining non-overlapping boxes and nontrivial interiors.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4b57f748d763"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b6d88eaf0a3f"
MIN_STRICT_FRAC = 0.20
EXAMPLES_NEEDED = 3

SUMMARY = (
    "For each nonzero color independently, infer the axis-aligned rectangle "
    "whose three marked corners are present, then paint that rectangle's full "
    "one-cell-thick border in the same color."
)

INVARIANTS = [
    "background is 0 and every foreground value is an ARC color 1..9",
    "each foreground color occurs exactly three times",
    "the three cells of each color are exactly three corners of a nondegenerate bbox",
    "the absent fourth corner is background in the input",
    "rectangle bounding boxes are pairwise disjoint",
    "every rectangle is at least 3x3, so outline and filled-box rules disagree",
    "the output preserves all input cells and paints every bbox-border cell",
]

COUNTER_HYPOTHESES = [
    "add only the absent fourth corner",
    "fill each rectangle solid instead of drawing its border",
    "draw only the horizontal or only the vertical sides",
    "complete only the first/reading-order color",
    "collapse every rectangle to one foreground color",
    "memorize a public grid size, rectangle size, missing corner, or position",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "interior_two",
    "edge_two",
    "three_rects",
    "mixed_aspect",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "linked public-profile prior plus generalized curriculum",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# A single scene-profile axis has no cross-axis incompatibilities. Declare the
# empty contract explicitly so exact override evidence is not labeled legacy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

# Complete public geometry, extracted from all four train inputs and the held-out
# test input. Rectangle tuples are (r0, c0, r1, c1, missing_corner_index), with
# corner order TL, TR, BL, BR. Colors are nuisance and sampled independently.
_PUBLIC_SPECS = {
    "public_train_1": (
        (8, 11),
        ((1, 1, 4, 5, 0), (2, 7, 6, 9, 3)),
    ),
    "public_train_2": (
        (9, 12),
        ((0, 2, 3, 6, 1), (4, 8, 7, 10, 2)),
    ),
    "public_train_3": (
        (10, 10),
        ((2, 1, 6, 4, 2), (1, 6, 4, 8, 0)),
    ),
    "public_train_4": (
        (8, 13),
        ((1, 3, 5, 7, 3), (2, 9, 6, 11, 1)),
    ),
    "public_test_1": (
        (9, 12),
        ((2, 7, 7, 10, 0), (1, 1, 5, 4, 2)),
    ),
}

# 5/13 = 38.5% strict whole-profile support before finite-sample variation.
_DEFAULT_PROFILE_POOL = (
    *PUBLIC_PROFILES,
    "interior_two", "interior_two",
    "edge_two", "edge_two",
    "three_rects", "three_rects",
    "mixed_aspect", "mixed_aspect",
)

_TRANSFORMS = (
    "identity",
    "rotate_cw",
    "rotate_180",
    "rotate_ccw",
    "flip_lr",
    "flip_ud",
    "transpose",
    "anti_transpose",
)


def _clone(grid):
    return [list(row) for row in grid]


def _corners(box):
    r0, c0, r1, c1 = box
    return ((r0, c0), (r0, c1), (r1, c0), (r1, c1))


def _transform(grid, name):
    if name == "identity":
        return _clone(grid)
    if name == "rotate_cw":
        return [list(row) for row in zip(*reversed(grid))]
    if name == "rotate_180":
        return [list(reversed(row)) for row in reversed(grid)]
    if name == "rotate_ccw":
        return [list(row) for row in reversed(list(zip(*grid)))]
    if name == "flip_lr":
        return [list(reversed(row)) for row in grid]
    if name == "flip_ud":
        return [list(row) for row in reversed(grid)]
    if name == "transpose":
        return [list(row) for row in zip(*grid)]
    if name == "anti_transpose":
        return [list(reversed(row)) for row in reversed(list(zip(*grid)))]
    raise ValueError(f"unknown transform: {name}")


def _boxes_overlap(left, right):
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _analysis(grid: Any) -> dict[str, Any]:
    """Recover all answer-bearing geometry from a returned input grid."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be nonempty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if height > 30 or width > 30:
        return {
            "height": height,
            "width": width,
            "errors": [f"grid exceeds ARC bounds: {height}x{width}"],
        }

    errors: list[str] = []
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
            elif value:
                by_color.setdefault(value, []).append((r, c))
    if errors:
        return {"height": height, "width": width, "errors": errors}
    if not by_color:
        return {
            "height": height,
            "width": width,
            "errors": ["no rectangle-corner colors present"],
        }

    rectangles: list[dict[str, Any]] = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 3:
            errors.append(f"color {color} occurs {len(cells)} times, not 3")
            continue
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(rows) != 2 or len(cols) != 2:
            errors.append(f"color {color} does not span exactly two rows and two columns")
            continue
        box = (rows[0], cols[0], rows[1], cols[1])
        corners = _corners(box)
        if any(cell not in corners for cell in cells):
            errors.append(f"color {color} has a non-corner marker")
            continue
        missing = [index for index, point in enumerate(corners) if point not in cells]
        if len(missing) != 1:
            errors.append(f"color {color} is not exactly three bbox corners")
            continue
        rect_h = box[2] - box[0] + 1
        rect_w = box[3] - box[1] + 1
        if rect_h < 3 or rect_w < 3:
            errors.append(
                f"color {color} rectangle must be at least 3x3, found {rect_h}x{rect_w}"
            )
            continue
        missing_point = corners[missing[0]]
        if grid[missing_point[0]][missing_point[1]] != 0:
            errors.append(f"color {color}'s absent fourth corner is occupied")
            continue
        rectangles.append(
            {
                "color": color,
                "cells": tuple(sorted(cells)),
                "box": box,
                "missing": missing[0],
                "missing_point": missing_point,
                "rect_h": rect_h,
                "rect_w": rect_w,
            }
        )

    rectangles.sort(key=lambda item: (*item["box"], item["color"]))
    for i, left in enumerate(rectangles):
        for right in rectangles[i + 1 :]:
            if _boxes_overlap(left["box"], right["box"]):
                errors.append(
                    f"rectangle boxes overlap: {left['box']} and {right['box']}"
                )
    return {
        "height": height,
        "width": width,
        "rectangles": rectangles,
        "colors": tuple(sorted(by_color)),
        "errors": errors,
    }


def _profile_signature_from_analysis(info):
    if info.get("errors"):
        return None
    rectangles = info["rectangles"]
    min_row = min(item["box"][0] for item in rectangles)
    min_col = min(item["box"][1] for item in rectangles)
    normalized = tuple(
        (
            item["box"][0] - min_row,
            item["box"][1] - min_col,
            item["box"][2] - min_row,
            item["box"][3] - min_col,
            item["missing"],
        )
        for item in rectangles
    )
    return (info["height"], info["width"], normalized)


def canonical_profile_signature(grid):
    """Strict linked public profile, ignoring only color and group translation."""
    return _profile_signature_from_analysis(_analysis(grid))


def _build_grid(shape, rectangles, colors):
    grid = full_grid(shape[0], shape[1], 0)
    boxes = []
    for spec, color in zip(rectangles, colors):
        r0, c0, r1, c1, missing = spec
        box = (r0, c0, r1, c1)
        if any(_boxes_overlap(box, previous) for previous in boxes):
            raise ValueError("rectangle boxes overlap")
        boxes.append(box)
        for index, (r, c) in enumerate(_corners(box)):
            if index != missing:
                if grid[r][c] != 0:
                    raise ValueError("rectangle corner collision")
                grid[r][c] = color
    return grid


def _translate_specs(shape, rectangles, rng):
    min_row = min(spec[0] for spec in rectangles)
    min_col = min(spec[1] for spec in rectangles)
    max_row = max(spec[2] for spec in rectangles)
    max_col = max(spec[3] for spec in rectangles)
    dr = rng.randint(-min_row, shape[0] - 1 - max_row)
    dc = rng.randint(-min_col, shape[1] - 1 - max_col)
    return tuple(
        (r0 + dr, c0 + dc, r1 + dr, c1 + dc, missing)
        for r0, c0, r1, c1, missing in rectangles
    )


def _public_grid(profile, layout_rng, colors, transform_rng):
    shape, rectangles = _PUBLIC_SPECS[profile]
    translated = _translate_specs(shape, rectangles, layout_rng)
    return _transform(
        _build_grid(shape, translated, colors),
        transform_rng.choice(_TRANSFORMS),
    )


def _general_shape(band, rng):
    if band == "easy":
        return rng.randint(11, 13), rng.randint(12, 15)
    if band == "hard":
        return rng.randint(17, 21), rng.randint(18, 22)
    return rng.randint(14, 17), rng.randint(15, 19)


def _random_box(height, width, rng, *, edge=False, aspect=None):
    if aspect == "tall":
        rect_h = rng.randint(6, min(8, height - 2))
        rect_w = rng.randint(3, min(4, width - 2))
    elif aspect == "wide":
        rect_h = rng.randint(3, min(4, height - 2))
        rect_w = rng.randint(6, min(8, width - 2))
    else:
        rect_h = rng.randint(3, min(6, height - 2))
        rect_w = rng.randint(3, min(6, width - 2))

    if edge:
        side = rng.choice(("top", "bottom", "left", "right"))
        r0 = (
            0 if side == "top"
            else height - rect_h if side == "bottom"
            else rng.randint(1, height - rect_h - 1)
        )
        c0 = (
            0 if side == "left"
            else width - rect_w if side == "right"
            else rng.randint(1, width - rect_w - 1)
        )
    else:
        r0 = rng.randint(1, height - rect_h - 1)
        c0 = rng.randint(1, width - rect_w - 1)
    return (r0, c0, r0 + rect_h - 1, c0 + rect_w - 1)


def _sample_disjoint_boxes(height, width, rng, specs):
    boxes = []
    for spec in specs:
        for _ in range(512):
            box = _random_box(height, width, rng, **spec)
            if not any(_boxes_overlap(box, previous) for previous in boxes):
                boxes.append(box)
                break
        else:
            raise ValueError(f"unable to place disjoint rectangles for {specs!r}")
    return boxes


def _general_rectangles(profile, shape, rng):
    """Construct mutually-classifiable profiles without placement retries."""
    height, width = shape
    if profile == "interior_two":
        size1 = rng.randint(3, 4)
        size2 = rng.randint(3, 4)
        r0a = 1 + rng.randint(0, 1)
        c0a = 1 + rng.randint(0, 1)
        r0b = height - size2 - 1 - rng.randint(0, 1)
        c0b = width - size2 - 1 - rng.randint(0, 1)
        boxes = [
            (r0a, c0a, r0a + size1 - 1, c0a + size1 - 1),
            (r0b, c0b, r0b + size2 - 1, c0b + size2 - 1),
        ]
    elif profile == "edge_two":
        size1 = rng.randint(3, 5)
        size2 = rng.randint(3, 4)
        side = rng.choice(("top", "bottom", "left", "right"))
        if side == "top":
            first = (0, 1, size1 - 1, size1)
            second = (height - size2 - 1, width - size2 - 1, height - 2, width - 2)
        elif side == "bottom":
            first = (height - size1, width - size1 - 1, height - 1, width - 2)
            second = (1, 1, size2, size2)
        elif side == "left":
            first = (1, 0, size1, size1 - 1)
            second = (height - size2 - 1, width - size2 - 1, height - 2, width - 2)
        else:
            first = (height - size1 - 1, width - size1, height - 2, width - 1)
            second = (1, 1, size2, size2)
        boxes = [first, second]
    elif profile == "three_rects":
        # Three 3x3 boxes occupy separate quadrants; one-cell jitter keeps
        # positions live while preserving disjointness on the minimum canvas.
        boxes = [
            (1, 1 + rng.randint(0, 1), 3, 3 + rng.randint(0, 1)),
            (1 + rng.randint(0, 1), width - 4, 3 + rng.randint(0, 1), width - 2),
            (height - 4, 1 + rng.randint(0, 1), height - 2, 3 + rng.randint(0, 1)),
        ]
        # Keep each bbox exactly 3x3 after independent jitter.
        boxes = [(r0, c0, r0 + 2, c0 + 2) for r0, c0, _r1, _c1 in boxes]
    elif profile == "mixed_aspect":
        # Opposite corners guarantee a gap even on the minimum 11x12 canvas.
        # The two one-cell jitters move the group inward without allowing the
        # tall and wide boxes to touch.
        tall_r0 = 1
        tall_c0 = 1 + rng.randint(0, 1)
        wide_r0 = height - 4
        wide_c0 = width - 7 - rng.randint(0, 1)
        boxes = [
            (tall_r0, tall_c0, tall_r0 + 5, tall_c0 + 2),
            (wide_r0, wide_c0, wide_r0 + 2, wide_c0 + 5),
        ]
    else:
        raise ValueError(f"unknown generalized profile: {profile}")
    if any(_boxes_overlap(left, right) for i, left in enumerate(boxes) for right in boxes[i + 1:]):
        raise ValueError(f"internal profile placement overlap for {profile}: {boxes}")
    return tuple((*box, rng.randrange(4)) for box in boxes)


def _classify_general(info):
    rectangles = info["rectangles"]
    height, width = info["height"], info["width"]
    if len(rectangles) == 3:
        return "three_rects"
    if any(
        item["box"][0] == 0
        or item["box"][1] == 0
        or item["box"][2] == height - 1
        or item["box"][3] == width - 1
        for item in rectangles
    ):
        return "edge_two"
    aspects = {
        "tall" if item["rect_h"] > item["rect_w"]
        else "wide" if item["rect_w"] > item["rect_h"]
        else "square"
        for item in rectangles
    }
    if len(rectangles) == 2 and "tall" in aspects and "wide" in aspects:
        return "mixed_aspect"
    return "interior_two"


def _validate_difficulty(difficulty):
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fully observable rectangle-outline input."""
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    band = _validate_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", _DEFAULT_PROFILE_POOL)
    layout_rng = ctx.draw_rng("layout")
    transform_rng = ctx.draw_rng("transform")
    if profile in _PUBLIC_SPECS:
        colors = ctx.draw_distinct_colors("colors", n=2, exclude={0})
        grid = _public_grid(profile, layout_rng, colors, transform_rng)
    else:
        shape = _general_shape(band, layout_rng)
        rectangles = _general_rectangles(profile, shape, layout_rng)
        colors = ctx.draw_distinct_colors("colors", n=len(rectangles), exclude={0})
        grid = _build_grid(shape, rectangles, colors)

    errors = self_check(grid, meta={"overrides": {"scene_profile": profile}})
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    return grid


def observe_overrides(grid):
    """Recover the exact declared scene profile from the returned grid."""
    info = _analysis(grid)
    if info.get("errors"):
        return {}
    public = _PUBLIC_SIGNATURE_LOOKUP.get(_profile_signature_from_analysis(info))
    return {"scene_profile": public or _classify_general(info)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes, including nearest impostors."""
    del difficulty
    errors = list(_analysis(grid).get("errors", ()))
    if errors:
        return errors
    info = _analysis(grid)
    if len(info["rectangles"]) not in (2, 3):
        errors.append(
            f"expected two or three independent rectangles, found {len(info['rectangles'])}"
        )
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", {})
        if "scene_profile" in requested:
            observed = observe_overrides(grid).get("scene_profile")
            if observed != requested["scene_profile"]:
                errors.append(
                    f"scene_profile observed {observed!r}, requested "
                    f"{requested['scene_profile']!r}"
                )
    return errors


def rule_mirror(grid):
    """Independent Python mirror of the selected canonical Racket rule."""
    info = _analysis(grid)
    if info.get("errors"):
        raise ValueError("invalid rectangle-outline input: " + "; ".join(info["errors"]))
    output = _clone(grid)
    for item in info["rectangles"]:
        r0, c0, r1, c1 = item["box"]
        color = item["color"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    output[r][c] = color
    return output


def _public_literal(profile):
    shape, rectangles = _PUBLIC_SPECS[profile]
    return _build_grid(shape, rectangles, range(1, len(rectangles) + 1))


_PUBLIC_SIGNATURE_LOOKUP = {}
for _profile_name in PUBLIC_PROFILES:
    _literal = _public_literal(_profile_name)
    for _transform_name in _TRANSFORMS:
        _signature = canonical_profile_signature(_transform(_literal, _transform_name))
        _previous = _PUBLIC_SIGNATURE_LOOKUP.setdefault(_signature, _profile_name)
        if _previous != _profile_name:
            raise RuntimeError("ambiguous public rectangle-outline profiles")


# ---------------------------------------------------------------------------
# Task-linked semantic contract and named rival rules
# ---------------------------------------------------------------------------

def strict_canonical_like(grid) -> list[str]:
    info = _analysis(grid)
    if info.get("errors"):
        return list(info["errors"])
    signature = _profile_signature_from_analysis(info)
    if signature not in _PUBLIC_SIGNATURE_LOOKUP:
        return ["not one of the five linked public geometry profiles"]
    return []


def _rival_identity(grid):
    return _clone(grid)


def _rival_missing_corner_only(grid):
    info = _analysis(grid)
    output = _clone(grid)
    for item in info.get("rectangles", []):
        r, c = item["missing_point"]
        output[r][c] = item["color"]
    return output


def _rival_filled_bbox(grid):
    info = _analysis(grid)
    output = _clone(grid)
    for item in info.get("rectangles", []):
        r0, c0, r1, c1 = item["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = item["color"]
    return output


def _rival_horizontal_sides_only(grid):
    info = _analysis(grid)
    output = _clone(grid)
    for item in info.get("rectangles", []):
        r0, c0, r1, c1 = item["box"]
        for c in range(c0, c1 + 1):
            output[r0][c] = output[r1][c] = item["color"]
    return output


def _rival_vertical_sides_only(grid):
    info = _analysis(grid)
    output = _clone(grid)
    for item in info.get("rectangles", []):
        r0, c0, r1, c1 = item["box"]
        for r in range(r0, r1 + 1):
            output[r][c0] = output[r][c1] = item["color"]
    return output


def _rival_first_color_only(grid):
    info = _analysis(grid)
    output = _clone(grid)
    rectangles = info.get("rectangles", [])
    if not rectangles:
        return output
    item = rectangles[0]
    r0, c0, r1, c1 = item["box"]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                output[r][c] = item["color"]
    return output


def _rival_monochrome_outlines(grid):
    info = _analysis(grid)
    output = _clone(grid)
    color = info.get("rectangles", [{}])[0].get("color", 1)
    for item in info.get("rectangles", []):
        r0, c0, r1, c1 = item["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    output[r][c] = color
    return output


def _rival_skip_edge_rectangles(grid):
    info = _analysis(grid)
    output = _clone(grid)
    height, width = info.get("height", 0), info.get("width", 0)
    for item in info.get("rectangles", []):
        r0, c0, r1, c1 = item["box"]
        if r0 == 0 or c0 == 0 or r1 == height - 1 or c1 == width - 1:
            continue
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    output[r][c] = item["color"]
    return output


def _rival_first_two_rectangles(grid):
    info = _analysis(grid)
    output = _clone(grid)
    for item in info.get("rectangles", [])[:2]:
        r0, c0, r1, c1 = item["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    output[r][c] = item["color"]
    return output


def _rival_square_rectangles_only(grid):
    info = _analysis(grid)
    output = _clone(grid)
    for item in info.get("rectangles", []):
        if item["rect_h"] != item["rect_w"]:
            continue
        r0, c0, r1, c1 = item["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    output[r][c] = item["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "identity": _rival_identity,
    "missing_corner_only": _rival_missing_corner_only,
    "filled_bbox": _rival_filled_bbox,
    "horizontal_sides_only": _rival_horizontal_sides_only,
    "vertical_sides_only": _rival_vertical_sides_only,
    "first_color_only": _rival_first_color_only,
    "monochrome_outlines": _rival_monochrome_outlines,
    "skip_edge_rectangles": _rival_skip_edge_rectangles,
    "first_two_rectangles": _rival_first_two_rectangles,
    "square_rectangles_only": _rival_square_rectangles_only,
}
LESSON_COMPETITORS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "identity",
        "missing_corner_only",
        "filled_bbox",
        "horizontal_sides_only",
        "vertical_sides_only",
        "first_color_only",
        "monochrome_outlines",
    )
}
CANONICAL_SHORTCUTS = {
    "missing_corner_only": _rival_missing_corner_only,
    "filled_bbox": _rival_filled_bbox,
    "first_color_only": _rival_first_color_only,
}


def _valid_info(grid):
    info = _analysis(grid)
    return None if info.get("errors") else info


def _witness_nontrivial_outline(grid):
    info = _valid_info(grid)
    return bool(info and all(item["rect_h"] >= 3 and item["rect_w"] >= 3 for item in info["rectangles"]))


def _witness_both_axes(grid):
    return _witness_nontrivial_outline(grid)


def _witness_multiple_colors(grid):
    info = _valid_info(grid)
    return bool(info and len(info["rectangles"]) >= 2)


def _witness_edge_touching(grid):
    info = _valid_info(grid)
    return bool(info and any(
        item["box"][0] == 0
        or item["box"][1] == 0
        or item["box"][2] == info["height"] - 1
        or item["box"][3] == info["width"] - 1
        for item in info["rectangles"]
    ))


def _witness_three_rectangles(grid):
    info = _valid_info(grid)
    return bool(info and len(info["rectangles"]) == 3)


def _witness_mixed_aspect(grid):
    info = _valid_info(grid)
    if not info:
        return False
    aspects = {
        "tall" if item["rect_h"] > item["rect_w"]
        else "wide" if item["rect_w"] > item["rect_h"]
        else "square"
        for item in info["rectangles"]
    }
    return "tall" in aspects and "wide" in aspects


SEMANTIC_WITNESSES = {
    "nontrivial_outline": _witness_nontrivial_outline,
    "both_axes_required": _witness_both_axes,
    "multiple_colors_independent": _witness_multiple_colors,
    "edge_touching": _witness_edge_touching,
    "three_rectangles": _witness_three_rectangles,
    "mixed_aspect": _witness_mixed_aspect,
}
WITNESS_RIVALS = {
    "nontrivial_outline": ["identity", "missing_corner_only", "filled_bbox"],
    "both_axes_required": ["horizontal_sides_only", "vertical_sides_only"],
    "multiple_colors_independent": ["first_color_only", "monochrome_outlines"],
    "edge_touching": ["skip_edge_rectangles"],
    "three_rectangles": ["first_two_rectangles"],
    "mixed_aspect": ["square_rectangles_only"],
}


def _grids_equal(left, right):
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Name every wrong rule still consistent with all demonstrations."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            )
            if not fits_demos:
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives every demo and query")
            else:
                reasons.append(f"competitor {name!r} fits every demo but disagrees on query")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
