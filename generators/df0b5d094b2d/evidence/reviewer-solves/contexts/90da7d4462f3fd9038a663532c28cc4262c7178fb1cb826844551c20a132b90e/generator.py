"""Generator for training task 470c91de / df0b5d094b2d.

Against background 7, each ordinary color fills one rectangle except for
one bounding-box corner occupied by marker color 8.  The output removes all
markers and translates the complete colored rectangle one diagonal step
toward its marked corner.

The four unique public scenes contain two, three, or four rectangles with
dimensions 2..5.  Their translated output rectangles remain in-bounds and
pairwise disjoint.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "df0b5d094b2d"
VERSION = "3.0.0"
TASK_ID = "df0b5d094b2d"
RULE_HASH = "e4ccb0c97cf3"

SUMMARY = (
    "Two to four colored rectangles each have one bbox corner replaced by "
    "8; replace the markers and move every full rectangle one diagonal "
    "step toward its marked corner on background 7."
)

INVARIANTS = [
    "the background is color 7 and marker color is 8",
    "there are exactly 2..4 distinct ordinary rectangle colors",
    "each 2..5 by 2..5 rectangle is full except for one marked bbox corner",
    "source rectangle bboxes are pairwise disjoint",
    "translated full rectangles remain in-bounds and pairwise disjoint",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 10..20",
        "valid": "10..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 10..22",
        "valid": "10..22",
    },
    "shape_count": {
        "type": "int",
        "default": "difficulty-aware rng 2..4",
        "valid": "2..4",
    },
}

_VALID_H = (10, 20)
_VALID_W = (10, 22)
_VALID_COUNT = (2, 4)
_PROFILE_PRIOR = 0.08

# Object tuple: color, top, left, height, width, missing-corner index.
# Corner order is top-left, top-right, bottom-left, bottom-right.
_PROFILE_SPECS = (
    (
        10,
        10,
        (
            (1, 1, 5, 4, 3, 0),
            (5, 6, 1, 4, 5, 1),
            (9, 0, 0, 2, 2, 3),
        ),
    ),
    (
        10,
        10,
        (
            (2, 1, 1, 5, 5, 1),
            (6, 7, 5, 2, 4, 0),
        ),
    ),
    (
        11,
        11,
        (
            (2, 3, 0, 4, 4, 3),
            (3, 6, 8, 3, 3, 2),
            (9, 2, 7, 4, 3, 3),
        ),
    ),
    (
        11,
        11,
        (
            (2, 6, 6, 2, 2, 3),
            (3, 0, 8, 3, 3, 2),
            (4, 3, 4, 4, 2, 1),
            (9, 0, 0, 5, 3, 3),
        ),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _corner_cells(r0, c0, r1, c1):
    return (
        (r0, c0),
        (r0, c1),
        (r1, c0),
        (r1, c1),
    )


def _direction(corner):
    return (
        -1 if corner in (0, 1) else 1,
        -1 if corner in (0, 2) else 1,
    )


def _box_intersects(first, second):
    return (
        max(first[0], second[0]) <= min(first[2], second[2])
        and max(first[1], second[1]) <= min(first[3], second[3])
    )


def _object_record(color, r0, c0, r1, c1, corner):
    dr, dc = _direction(corner)
    return {
        "color": color,
        "r0": r0,
        "c0": c0,
        "r1": r1,
        "c1": c1,
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
        "corner": corner,
        "marker": _corner_cells(r0, c0, r1, c1)[corner],
        "dr": dr,
        "dc": dc,
        "source_box": (r0, c0, r1, c1),
        "output_box": (r0 + dr, c0 + dc, r1 + dr, c1 + dc),
    }


def _extract_objects(grid):
    colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (7, 8)
        }
    )
    rects = []
    errors = []
    for color in colors:
        cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        if not cells:
            continue
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        corners = _corner_cells(r0, c0, r1, c1)
        missing_corners = [
            index
            for index, cell in enumerate(corners)
            if cell not in cells
        ]
        if len(missing_corners) != 1:
            errors.append(
                f"color {color} must omit exactly one bbox corner"
            )
            continue
        corner = missing_corners[0]
        missing = corners[corner]
        expected = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if (r, c) != missing
        }
        if cells != expected:
            errors.append(
                f"color {color} must fill its bbox except the marked corner"
            )
        if grid[missing[0]][missing[1]] != 8:
            errors.append(
                f"color {color} missing corner must contain marker 8"
            )
        rects.append(
            _object_record(color, r0, c0, r1, c1, corner)
        )
    return rects, errors


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    rects, errors = _extract_objects(grid)
    return {
        "grid": grid,
        "h": len(grid),
        "w": len(grid[0]) if grid else 0,
        "objects": tuple(rects),
        "errors": tuple(errors),
        "markers": tuple(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 8
        ),
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 10..20")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 10..22")
    if any(
        type(value) is not int or not (0 <= value <= 9)
        for row in coerced
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
    scene = _analyze_scene(coerced)
    errors.extend(scene["errors"])
    rects = scene["objects"]
    if not (_VALID_COUNT[0] <= len(rects) <= _VALID_COUNT[1]):
        errors.append("scene must contain exactly 2..4 colored rectangles")
    for obj in rects:
        if not (
            2 <= obj["height"] <= 5
            and 2 <= obj["width"] <= 5
        ):
            errors.append(
                f"color {obj['color']} rectangle must be 2..5 by 2..5"
            )
        out = obj["output_box"]
        if not (
            0 <= out[0] <= out[2] < h
            and 0 <= out[1] <= out[3] < w
        ):
            errors.append(
                f"color {obj['color']} translated rectangle must be in-bounds"
            )
    expected_markers = {obj["marker"] for obj in rects}
    if set(scene["markers"]) != expected_markers:
        errors.append(
            "marker cells must equal the one missing corner of every rectangle"
        )
    for index, first in enumerate(rects):
        for second in rects[index + 1:]:
            if _box_intersects(
                first["source_box"],
                second["source_box"],
            ):
                errors.append("source rectangle bboxes must be disjoint")
            if _box_intersects(
                first["output_box"],
                second["output_box"],
            ):
                errors.append("translated rectangle bboxes must be disjoint")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "shape_count": len(scene["objects"]),
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = full_grid(scene["h"], scene["w"], 7)
    for obj in scene["objects"]:
        r0, c0, r1, c1 = obj["output_box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = obj["color"]
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    min_r = min(obj["r0"] for obj in scene["objects"])
    min_c = min(obj["c0"] for obj in scene["objects"])
    return (
        scene["h"],
        scene["w"],
        tuple(
            (
                obj["color"],
                obj["r0"] - min_r,
                obj["c0"] - min_c,
                obj["height"],
                obj["width"],
                obj["corner"],
            )
            for obj in scene["objects"]
        ),
    )


def _profile_signature(profile):
    h, w, specs = profile
    min_r = min(spec[1] for spec in specs)
    min_c = min(spec[2] for spec in specs)
    return (
        h,
        w,
        tuple(
            (
                color,
                r0 - min_r,
                c0 - min_c,
                rh,
                rw,
                corner,
            )
            for color, r0, c0, rh, rw, corner in specs
        ),
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _paint_specs(h, w, specs):
    grid = full_grid(h, w, 7)
    for color, r0, c0, rh, rw, corner in specs:
        missing = _corner_cells(
            r0,
            c0,
            r0 + rh - 1,
            c0 + rw - 1,
        )[corner]
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                grid[r][c] = 8 if (r, c) == missing else color
    return grid


def _profile_shifts(profile):
    h, w, specs = profile
    shifts = []
    for shift_r in range(-h, h + 1):
        for shift_c in range(-w, w + 1):
            valid = True
            for _, r0, c0, rh, rw, corner in specs:
                dr, dc = _direction(corner)
                sr0 = r0 + shift_r
                sc0 = c0 + shift_c
                sr1 = sr0 + rh - 1
                sc1 = sc0 + rw - 1
                if not (
                    0 <= sr0 <= sr1 < h
                    and 0 <= sc0 <= sc1 < w
                    and 0 <= sr0 + dr <= sr1 + dr < h
                    and 0 <= sc0 + dc <= sc1 + dc < w
                ):
                    valid = False
                    break
            if valid:
                shifts.append((shift_r, shift_c))
    return tuple(shifts)


def _draw_profile(profile, rng):
    h, w, specs = profile
    shift_r, shift_c = rng.choice(_profile_shifts(profile))
    shifted = tuple(
        (
            color,
            r0 + shift_r,
            c0 + shift_c,
            rh,
            rw,
            corner,
        )
        for color, r0, c0, rh, rw, corner in specs
    )
    return _paint_specs(h, w, shifted)


def _candidate_boxes(h, w, rh, rw, corner):
    dr, dc = _direction(corner)
    candidates = []
    for r0 in range(h - rh + 1):
        for c0 in range(w - rw + 1):
            source = (r0, c0, r0 + rh - 1, c0 + rw - 1)
            output = (
                source[0] + dr,
                source[1] + dc,
                source[2] + dr,
                source[3] + dc,
            )
            if (
                0 <= output[0] <= output[2] < h
                and 0 <= output[1] <= output[3] < w
            ):
                candidates.append((r0, c0, source, output))
    return candidates


def _place_shapes(h, w, shape_specs, rng):
    candidate_lists = []
    for rh, rw, corner in shape_specs:
        candidates = _candidate_boxes(h, w, rh, rw, corner)
        rng.shuffle(candidates)
        candidate_lists.append(candidates)
    nodes = 0

    def search(index, chosen):
        nonlocal nodes
        if index == len(candidate_lists):
            return tuple(chosen)
        for r0, c0, source, output in candidate_lists[index]:
            nodes += 1
            if nodes > 100_000:
                return None
            if any(
                _box_intersects(source, prior[2])
                or _box_intersects(output, prior[3])
                for prior in chosen
            ):
                continue
            result = search(
                index + 1,
                (*chosen, (r0, c0, source, output)),
            )
            if result is not None:
                return result
        return None

    return search(0, ())


def _fallback_specs(h, w, count):
    anchors = (
        (1, 1, 0),
        (1, w - 3, 1),
        (h - 3, 1, 2),
        (h - 3, w - 3, 3),
    )
    return tuple(
        (r0, c0, 2, 2, corner)
        for r0, c0, corner in anchors[:count]
    )


def _draw_general(h, w, count, colors, rng):
    max_dim = {2: 5, 3: 4, 4: 3}[count]
    for _ in range(24):
        shape_specs = tuple(
            (
                rng.randint(2, max_dim),
                rng.randint(2, max_dim),
                rng.randrange(4),
            )
            for _ in range(count)
        )
        placements = _place_shapes(h, w, shape_specs, rng)
        if placements is None:
            continue
        specs = tuple(
            (
                colors[index],
                placements[index][0],
                placements[index][1],
                shape_specs[index][0],
                shape_specs[index][1],
                shape_specs[index][2],
            )
            for index in range(count)
        )
        return _paint_specs(h, w, specs)
    fallback = _fallback_specs(h, w, count)
    specs = tuple(
        (
            colors[index],
            r0,
            c0,
            rh,
            rw,
            corner,
        )
        for index, (r0, c0, rh, rw, corner) in enumerate(fallback)
    )
    return _paint_specs(h, w, specs)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)
    profile = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if profile is not None:
        h, w, specs = profile
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("shape_count", len(specs), len(specs))
        grid = _draw_profile(profile, ctx.draw_rng("layout"))
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (10, 13),
                    "medium": (11, 16),
                    "hard": (14, 20),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (10, 14),
                    "medium": (11, 18),
                    "hard": (15, 22),
                }[band],
            )
        if overrides.get("shape_count") is not None:
            count = ctx.draw_int("shape_count", *_VALID_COUNT)
        else:
            count = ctx.draw_int(
                "shape_count",
                *{
                    "easy": (2, 2),
                    "medium": (2, 3),
                    "hard": (3, 4),
                }[band],
            )
        colors = ctx.draw_distinct_colors(
            "shape_colors",
            n=count,
            exclude={7, 8},
        )
        grid = _draw_general(
            h,
            w,
            count,
            colors,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
