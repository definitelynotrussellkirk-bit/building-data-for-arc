"""Generate lessons for ARC task 0d87d2a6: edge-marked cross lines.

Paired blue cells on opposite canvas edges identify complete vertical or
horizontal lines.  Draw those lines blue.  Every solid red object intersecting
or lying one cell from any marked line is then recolored blue; other red
objects remain unchanged.

Defaults retain all four complete public input profiles as linked units under
D4 symmetry.  Generalized profiles isolate vertical, horizontal, cross,
multi-line, adjacency-only, and edge-object behavior without invalid lessons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "19c5f15066d3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1ffa1234962c"
SUMMARY = (
    "Paired blue edge markers define full rows/columns; recolor every red "
    "object intersecting or one cell from a marked line blue."
)

INVARIANTS = [
    "inputs use only background 0, blue 1, and red 2",
    "every active vertical/horizontal line has blue markers on both opposite edges",
    "all input blue cells are paired boundary markers, never interior line cells",
    "red components are separated solid rectangles",
    "at least one red object is touched and at least one remains untouched",
    "touch means line intersection or one-cell row/column distance",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
GENERAL_PROFILES = (
    "vertical_only",
    "horizontal_only",
    "cross",
    "multi_lines",
    "adjacent_touch",
    "edge_objects",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "linked public-profile prior plus generalized curriculum",
        "valid": "|".join(SCENE_PROFILES),
    },
}

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

# Complete public inputs reconstructed as solid red bboxes and unique marked
# lines.  Outputs are never stored; the live rule derives them.  A rectangle is
# (row_min, col_min, row_max, col_max), inclusive.
_PUBLIC_SPECS = {
    "public_train_1": {
        "shape": (10, 20),
        "vcols": (6,),
        "hrows": (),
        "rectangles": (
            (2, 3, 5, 7),
            (2, 14, 3, 17),
            (5, 9, 7, 11),
            (5, 16, 7, 19),
            (7, 2, 8, 3),
        ),
    },
    "public_train_2": {
        "shape": (20, 20),
        "vcols": (7,),
        "hrows": (8,),
        "rectangles": (
            (0, 14, 2, 17),
            (2, 6, 5, 10),
            (7, 2, 9, 5),
            (8, 11, 10, 14),
            (13, 2, 15, 5),
            (16, 14, 17, 18),
        ),
    },
    "public_train_3": {
        "shape": (13, 14),
        "vcols": (7,),
        "hrows": (2,),
        "rectangles": (
            (0, 2, 3, 4),
            (2, 7, 3, 9),
            (5, 0, 6, 1),
            (5, 4, 9, 9),
            (7, 11, 11, 13),
            (11, 1, 12, 5),
        ),
    },
    "public_test_1": {
        "shape": (23, 25),
        "vcols": (5,),
        "hrows": (4, 11),
        "rectangles": (
            (0, 9, 3, 11),
            (1, 19, 4, 22),
            (3, 4, 5, 6),
            (3, 13, 7, 17),
            (6, 22, 8, 23),
            (9, 9, 11, 10),
            (10, 1, 13, 5),
            (16, 5, 20, 13),
            (16, 21, 18, 23),
            (18, 17, 19, 18),
        ),
    },
}

# 4/13 = 30.77% whole-profile prior.
_DEFAULT_PROFILE_POOL = (
    *PUBLIC_PROFILES,
    "vertical_only", "vertical_only",
    "horizontal_only",
    "cross", "cross",
    "multi_lines", "multi_lines",
    "adjacent_touch",
    "edge_objects",
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
    return [row[:] for row in grid]


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
        return [row[:] for row in reversed(grid)]
    if name == "transpose":
        return [list(row) for row in zip(*grid)]
    if name == "anti_transpose":
        return [
            list(reversed(row))
            for row in reversed(list(zip(*grid)))
        ]
    raise ValueError(f"unknown transform: {name}")


def _paint_rect(grid, box, color=2):
    row0, col0, row1, col1 = box
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            if grid[row][col] != 0:
                raise ValueError("red rectangle collides with another role")
            grid[row][col] = color


def _build_grid(shape, vcols, hrows, rectangles):
    height, width = shape
    grid = full_grid(height, width, 0)
    for box in rectangles:
        _paint_rect(grid, box)
    for col in vcols:
        if col in (0, width - 1):
            raise ValueError("vertical marker may not occupy a corner")
        if grid[0][col] or grid[height - 1][col]:
            raise ValueError("vertical marker collides with red")
        grid[0][col] = grid[height - 1][col] = 1
    for row in hrows:
        if row in (0, height - 1):
            raise ValueError("horizontal marker may not occupy a corner")
        if grid[row][0] or grid[row][width - 1]:
            raise ValueError("horizontal marker collides with red")
        grid[row][0] = grid[row][width - 1] = 1
    return grid


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            cells = []
            queue = [(row, col)]
            seen.add((row, col))
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (current_row + delta_row, current_col + delta_col)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        queue.append(point)
            components.append(cells)
    return components


def _analysis(grid):
    """Recover paired lines, red objects, and touch modes from an input."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a nonempty matrix"]}
    height, width = len(grid), len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return {"height": height, "width": width, "errors": ["ragged grid"]}
    errors = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC bounds: {height}x{width}")
    blues = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in (0, 1, 2)
            ):
                errors.append(f"invalid input cell ({row},{col})={value!r}")
            elif value == 1:
                blues.append((row, col))
    if errors:
        return {"height": height, "width": width, "errors": errors}
    if not blues:
        return {
            "height": height,
            "width": width,
            "errors": ["no blue boundary markers"],
        }
    if any(
        row not in (0, height - 1) and col not in (0, width - 1)
        for row, col in blues
    ):
        errors.append("blue input cells must all lie on the canvas boundary")
    if any(
        row in (0, height - 1) and col in (0, width - 1)
        for row, col in blues
    ):
        errors.append("corner markers ambiguously define two line axes")

    vcols = sorted({
        col for row, col in blues if row in (0, height - 1)
    })
    hrows = sorted({
        row for row, col in blues if col in (0, width - 1)
    })
    for col in vcols:
        if grid[0][col] != 1 or grid[height - 1][col] != 1:
            errors.append(f"vertical line {col} lacks paired opposite markers")
    for row in hrows:
        if grid[row][0] != 1 or grid[row][width - 1] != 1:
            errors.append(f"horizontal line {row} lacks paired opposite markers")
    if len(blues) != 2 * (len(vcols) + len(hrows)):
        errors.append("blue marker set is not exactly the paired line endpoints")

    red_objects = []
    red_cells = sum(value == 2 for values in grid for value in values)
    for cells in _components(grid, 2):
        rows = [point[0] for point in cells]
        cols = [point[1] for point in cells]
        box = (min(rows), min(cols), max(rows), max(cols))
        area = (box[2] - box[0] + 1) * (box[3] - box[1] + 1)
        if len(cells) != area:
            errors.append(f"red component at {box} is not a solid rectangle")
        intersects = any(
            col in vcols or row in hrows for row, col in cells
        )
        touched = any(
            col in vcols
            or col - 1 in vcols
            or col + 1 in vcols
            or row in hrows
            or row - 1 in hrows
            or row + 1 in hrows
            for row, col in cells
        )
        red_objects.append({
            "box": box,
            "cells": tuple(sorted(cells)),
            "intersects": intersects,
            "adjacent_only": touched and not intersects,
            "touched": touched,
        })
    red_objects.sort(key=lambda item: item["box"])
    if not red_cells:
        errors.append("no red objects")
    if red_objects and not any(item["touched"] for item in red_objects):
        errors.append("no red object is touched by a marked line")
    if red_objects and not any(not item["touched"] for item in red_objects):
        errors.append("no untouched red object witnesses selective recoloring")
    return {
        "height": height,
        "width": width,
        "vcols": tuple(vcols),
        "hrows": tuple(hrows),
        "red_objects": red_objects,
        "errors": errors,
    }


def _edge_mask(box, height, width):
    return (
        (1 if box[0] == 0 else 0)
        | (2 if box[2] == height - 1 else 0)
        | (4 if box[1] == 0 else 0)
        | (8 if box[3] == width - 1 else 0)
    )


def _feature_signature(info):
    if info.get("errors"):
        return None
    features = tuple(sorted(
        (
            item["box"][2] - item["box"][0] + 1,
            item["box"][3] - item["box"][1] + 1,
            _edge_mask(item["box"], info["height"], info["width"]),
            item["touched"],
            item["intersects"],
        )
        for item in info["red_objects"]
    ))
    return (
        info["height"],
        info["width"],
        len(info["vcols"]),
        len(info["hrows"]),
        features,
    )


def canonical_profile_signature(grid):
    """Return a strict complete linked public feature-profile match."""
    return _PUBLIC_SIGNATURE_LOOKUP.get(_feature_signature(_analysis(grid)))


def _public_literal(profile):
    spec = _PUBLIC_SPECS[profile]
    return _build_grid(
        spec["shape"],
        spec["vcols"],
        spec["hrows"],
        spec["rectangles"],
    )


def _marker_collision(box, shape, vcols, hrows):
    row0, col0, row1, col1 = box
    height, width = shape
    return (
        (row0 == 0 and any(col0 <= col <= col1 for col in vcols))
        or (row1 == height - 1 and any(col0 <= col <= col1 for col in vcols))
        or (col0 == 0 and any(row0 <= row <= row1 for row in hrows))
        or (col1 == width - 1 and any(row0 <= row <= row1 for row in hrows))
    )


def _fixed_feature_candidate(shape, vcols, hrows, feature, rng):
    height, width = shape
    box_h, box_w, edge_mask, touched, intersects = feature
    row0 = (
        0 if edge_mask & 1
        else height - box_h if edge_mask & 2
        else rng.randint(1, height - box_h - 1)
    )
    col0 = (
        0 if edge_mask & 4
        else width - box_w if edge_mask & 8
        else rng.randint(1, width - box_w - 1)
    )
    candidate = (row0, col0, row0 + box_h - 1, col0 + box_w - 1)
    actual_touched, actual_intersects = _bbox_relation(
        candidate, vcols, hrows
    )
    if (actual_touched, actual_intersects) != (touched, intersects):
        return None
    if _edge_mask(candidate, height, width) != edge_mask:
        return None
    if _marker_collision(candidate, shape, vcols, hrows):
        return None
    return candidate


def _public_variant(profile, rng):
    """Relayout one complete public feature tuple without recombination."""
    literal = _public_literal(profile)
    model = _analysis(literal)
    shape = (model["height"], model["width"])
    features = [
        (
            item["box"][2] - item["box"][0] + 1,
            item["box"][3] - item["box"][1] + 1,
            _edge_mask(item["box"], model["height"], model["width"]),
            item["touched"],
            item["intersects"],
        )
        for item in model["red_objects"]
    ]
    # Constrained edge and adjacency-only roles first, then large rectangles.
    features.sort(
        key=lambda feature: (
            bool(feature[2]),
            feature[3] and not feature[4],
            feature[4],
            feature[0] * feature[1],
        ),
        reverse=True,
    )
    height, width = shape
    for _layout_attempt in range(120):
        vcols = tuple(sorted(rng.sample(
            range(1, width - 1), len(model["vcols"])
        )))
        hrows = tuple(sorted(rng.sample(
            range(1, height - 1), len(model["hrows"])
        )))
        rectangles = []
        for feature in features:
            for _ in range(2400):
                candidate = _fixed_feature_candidate(
                    shape, vcols, hrows, feature, rng
                )
                if candidate is not None and _separated(candidate, rectangles):
                    rectangles.append(candidate)
                    break
            else:
                break
        if len(rectangles) == len(features):
            grid = _build_grid(shape, vcols, hrows, rectangles)
            if canonical_profile_signature(grid) == profile:
                return grid
    # The exact compact reconstruction is a safe deterministic fallback.
    return literal


def _general_shape(difficulty, rng):
    if difficulty == "easy":
        return rng.randint(14, 16), rng.randint(16, 19)
    if difficulty == "hard":
        return rng.randint(23, 28), rng.randint(25, 30)
    if difficulty == "medium":
        return rng.randint(18, 22), rng.randint(21, 25)
    return rng.randint(14, 28), rng.randint(16, 30)


def _marked_lines(profile, shape, rng):
    height, width = shape
    vertical = width // 2 + rng.choice((-1, 0, 1))
    horizontal = height // 2 + rng.choice((-1, 0, 1))
    if profile in ("vertical_only", "adjacent_touch"):
        return (vertical,), ()
    if profile == "horizontal_only":
        return (), (horizontal,)
    if profile == "multi_lines":
        if rng.choice((False, True)):
            return (width // 3, 2 * width // 3), (horizontal,)
        return (vertical,), (height // 3, 2 * height // 3)
    return (vertical,), (horizontal,)


def _bbox_relation(box, vcols, hrows):
    row0, col0, row1, col1 = box
    intersects = any(col0 <= col <= col1 for col in vcols) or any(
        row0 <= row <= row1 for row in hrows
    )
    touched = any(col0 - 1 <= col <= col1 + 1 for col in vcols) or any(
        row0 - 1 <= row <= row1 + 1 for row in hrows
    )
    return touched, intersects


def _separated(candidate, rectangles):
    row0, col0, row1, col1 = candidate
    return all(
        row1 + 1 < other[0]
        or other[2] + 1 < row0
        or col1 + 1 < other[1]
        or other[3] + 1 < col0
        for other in rectangles
    )


def _candidate_box(shape, vcols, hrows, relation, rng):
    height, width = shape
    box_h = rng.randint(2, min(6, height - 2))
    box_w = rng.randint(2, min(9, width - 2))
    if relation == "intersect":
        axes = (
            tuple(("v", col) for col in vcols)
            if vcols and not hrows
            else tuple(("h", row) for row in hrows)
            if hrows and not vcols
            else tuple(("v", col) for col in vcols)
            + tuple(("h", row) for row in hrows)
        )
        axis = rng.choice(axes)
        if axis[0] == "v":
            col0 = rng.randint(max(1, axis[1] - box_w + 1), min(axis[1], width - box_w - 1))
            row0 = rng.randint(1, height - box_h - 1)
        else:
            row0 = rng.randint(max(1, axis[1] - box_h + 1), min(axis[1], height - box_h - 1))
            col0 = rng.randint(1, width - box_w - 1)
    elif relation == "adjacent":
        vertical = rng.choice(vcols)
        if rng.choice((False, True)):
            col0 = vertical + 1
        else:
            col0 = vertical - box_w
        row0 = rng.randint(1, height - box_h - 1)
    else:
        if relation == "edge_untouched":
            side = rng.choice(("top", "bottom", "left", "right"))
        else:
            side = "interior"
        row0 = (
            0 if side == "top"
            else height - box_h if side == "bottom"
            else rng.randint(1, height - box_h - 1)
        )
        col0 = (
            0 if side == "left"
            else width - box_w if side == "right"
            else rng.randint(1, width - box_w - 1)
        )
    return (row0, col0, row0 + box_h - 1, col0 + box_w - 1)


def _general_rectangles(profile, shape, vcols, hrows, difficulty, rng):
    count = 4 if difficulty == "easy" else 6 if difficulty == "hard" else 5
    if difficulty not in ("easy", "medium", "hard"):
        count = rng.choice((4, 5, 6))
    if profile == "adjacent_touch":
        relations = ["adjacent", "intersect"]
    elif profile == "edge_objects":
        relations = ["edge_untouched", "intersect", "intersect"]
    elif profile == "multi_lines":
        relations = ["intersect", "intersect", "intersect"]
    else:
        relations = ["intersect", "intersect"]
    relations.extend(["untouched"] * (count - len(relations)))

    for _layout_attempt in range(80):
        rectangles = []
        complete = True
        for relation in relations:
            placed = False
            for _ in range(800):
                candidate = _candidate_box(shape, vcols, hrows, relation, rng)
                if not (
                    0 <= candidate[0] <= candidate[2] < shape[0]
                    and 0 <= candidate[1] <= candidate[3] < shape[1]
                ):
                    continue
                touched, intersects = _bbox_relation(candidate, vcols, hrows)
                if relation == "intersect" and not intersects:
                    continue
                if relation == "adjacent" and not (touched and not intersects):
                    continue
                if relation in ("untouched", "edge_untouched") and touched:
                    continue
                is_edge = (
                    candidate[0] == 0
                    or candidate[1] == 0
                    or candidate[2] == shape[0] - 1
                    or candidate[3] == shape[1] - 1
                )
                if relation == "edge_untouched" and not is_edge:
                    continue
                if relation != "edge_untouched" and is_edge:
                    continue
                if not _separated(candidate, rectangles):
                    continue
                rectangles.append(candidate)
                placed = True
                break
            if not placed:
                complete = False
                break
        if complete:
            return tuple(rectangles)
    raise RuntimeError(f"constructive placement exhausted for {profile}")


def _general_grid(profile, difficulty, layout_rng):
    shape = _general_shape(difficulty, layout_rng)
    vcols, hrows = _marked_lines(profile, shape, layout_rng)
    rectangles = _general_rectangles(
        profile, shape, vcols, hrows, difficulty, layout_rng
    )
    return _build_grid(shape, vcols, hrows, rectangles)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic edge-line/object-recolor lesson."""
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
    profile = ctx.draw_choice("scene_profile", _DEFAULT_PROFILE_POOL)
    if profile in _PUBLIC_SPECS:
        public_rng = ctx.draw_rng("public_layout")
        literal = _public_variant(profile, public_rng)
        return _transform(
            literal,
            public_rng.choice(_TRANSFORMS),
        )
    return _general_grid(profile, difficulty, ctx.draw_rng("layout"))


def _classify_general(info):
    if any(
        box["box"][0] == 0
        or box["box"][1] == 0
        or box["box"][2] == info["height"] - 1
        or box["box"][3] == info["width"] - 1
        for box in info["red_objects"]
    ):
        return "edge_objects"
    if any(box["adjacent_only"] for box in info["red_objects"]):
        return "adjacent_touch"
    if len(info["vcols"]) + len(info["hrows"]) >= 3:
        return "multi_lines"
    if info["vcols"] and not info["hrows"]:
        return "vertical_only"
    if info["hrows"] and not info["vcols"]:
        return "horizontal_only"
    return "cross"


def observe_overrides(grid):
    """Recover the exact declared scene profile from the returned input."""
    info = _analysis(grid)
    if info.get("errors"):
        return {}
    public = canonical_profile_signature(grid)
    return {"scene_profile": public or _classify_general(info)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject every input outside the exact paired-marker lesson grammar."""
    errors = list(_analysis(grid).get("errors", ()))
    if errors:
        return errors
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
    """Independent Python mirror of the canonical Racket rule."""
    info = _analysis(grid)
    if info.get("errors"):
        raise ValueError("invalid edge-line input: " + "; ".join(info["errors"]))
    output = _clone(grid)
    for row in info["hrows"]:
        for col in range(info["width"]):
            output[row][col] = 1
    for col in info["vcols"]:
        for row in range(info["height"]):
            output[row][col] = 1
    for obj in info["red_objects"]:
        if obj["touched"]:
            for row, col in obj["cells"]:
                output[row][col] = 1
    return output


_PUBLIC_SIGNATURE_LOOKUP = {}
for _profile_name in PUBLIC_PROFILES:
    _literal = _public_literal(_profile_name)
    for _transform_name in _TRANSFORMS:
        _key = _feature_signature(
            _analysis(_transform(_literal, _transform_name))
        )
        _previous = _PUBLIC_SIGNATURE_LOOKUP.setdefault(_key, _profile_name)
        if _previous != _profile_name:
            raise RuntimeError("ambiguous public edge-line profiles")
