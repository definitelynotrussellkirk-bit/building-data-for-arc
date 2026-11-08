"""Generate lessons for ARC task E145, "Fourth Corner".

Every non-background color appears exactly three times at three corners of
its own axis-aligned bounding rectangle.  The answer adds the absent fourth
corner in the same color.  Several colors may be completed independently in
one grid.

Defaults retain every complete public input profile as a linked unit while
varying color, translation, and D4 orientation.  Generalized profiles teach
single, thin, edge-touching, disjoint multi-color, and overlapping-bbox cases.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "14042d4b8317"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "af34f04ae393"
SUMMARY = (
    "For each nonzero color independently, add the missing fourth corner of "
    "the axis-aligned rectangle determined by its three input cells."
)

INVARIANTS = [
    "background is 0 and every foreground color is an ARC color 1..9",
    "each foreground color occurs exactly three times",
    "those three cells are three distinct corners of their color's bbox",
    "all absent fourth corners are background in the input",
    "the output adds one cell per foreground color and preserves all input cells",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "single_general",
    "thin_general",
    "edge_general",
    "multi_disjoint",
    "multi_overlap",
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

# Five complete input profiles, independently reconstructed from all four
# training pairs and the held-out input.  Rectangle tuples are
# (row_min, col_min, row_max, col_max, missing_corner_index), with corners in
# TL, TR, BL, BR order.  Colors are nuisance and are sampled at generation.
_PUBLIC_SPECS = {
    "public_train_1": ((7, 9), ((1, 1, 4, 5, 3),)),
    "public_train_2": (
        (8, 10),
        ((1, 8, 5, 9, 2), (2, 2, 6, 7, 0)),
    ),
    "public_train_3": ((6, 8), ((0, 1, 3, 4, 1),)),
    "public_train_4": (
        (9, 9),
        ((1, 6, 4, 8, 1), (2, 2, 7, 7, 2)),
    ),
    "public_test_1": (
        (8, 11),
        ((1, 1, 5, 6, 0), (2, 8, 6, 10, 3)),
    ),
}

# 5/16 = 31.25% strict whole-profile prior.  Public tuples are never rebuilt
# by independently sampling their dimensions, rectangle sizes, and directions.
_DEFAULT_PROFILE_POOL = (
    *PUBLIC_PROFILES,
    "single_general", "single_general",
    "thin_general", "thin_general",
    "edge_general",
    "multi_disjoint", "multi_disjoint", "multi_disjoint",
    "multi_overlap", "multi_overlap", "multi_overlap",
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


def _corners(box):
    row0, col0, row1, col1 = box
    return (
        (row0, col0),
        (row0, col1),
        (row1, col0),
        (row1, col1),
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


def _analysis(grid):
    """Recover answer-bearing geometry solely from a returned input grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a nonempty matrix"]}
    height, width = len(grid), len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return {"height": height, "width": width, "errors": ["ragged grid"]}
    if height > 30 or width > 30:
        return {
            "height": height,
            "width": width,
            "errors": [f"grid exceeds ARC bounds: {height}x{width}"],
        }

    by_color = {}
    errors = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"invalid cell ({row},{col})={value!r}")
            elif value:
                by_color.setdefault(value, []).append((row, col))
    if errors:
        return {"height": height, "width": width, "errors": errors}
    if not by_color:
        return {
            "height": height,
            "width": width,
            "errors": ["no foreground rectangles"],
        }

    rectangles = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 3:
            errors.append(f"color {color} occurs {len(cells)} times, not 3")
            continue
        rows = [point[0] for point in cells]
        cols = [point[1] for point in cells]
        box = (min(rows), min(cols), max(rows), max(cols))
        corners = _corners(box)
        missing = [index for index, point in enumerate(corners) if point not in cells]
        if box[0] == box[2] or box[1] == box[3] or len(missing) != 1:
            errors.append(f"color {color} is not exactly three bbox corners")
            continue
        missing_point = corners[missing[0]]
        if grid[missing_point[0]][missing_point[1]] != 0:
            errors.append(f"color {color}'s missing corner is occupied")
            continue
        rectangles.append(
            {
                "color": color,
                "box": box,
                "missing": missing[0],
                "missing_point": missing_point,
            }
        )

    rectangles.sort(key=lambda item: (*item["box"], item["color"]))
    return {
        "height": height,
        "width": width,
        "rectangles": rectangles,
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
    """Strict linked profile, ignoring only color and group translation."""
    return _profile_signature_from_analysis(_analysis(grid))


def _build_grid(shape, rectangles, colors):
    grid = full_grid(shape[0], shape[1], 0)
    reserved = set()
    for spec, color in zip(rectangles, colors):
        row0, col0, row1, col1, missing = spec
        corners = _corners((row0, col0, row1, col1))
        if any(point in reserved for point in corners):
            raise ValueError("rectangle corners collide")
        reserved.update(corners)
        for index, (row, col) in enumerate(corners):
            if index != missing:
                grid[row][col] = color
    return grid


def _translate_specs(shape, rectangles, rng):
    min_row = min(spec[0] for spec in rectangles)
    min_col = min(spec[1] for spec in rectangles)
    max_row = max(spec[2] for spec in rectangles)
    max_col = max(spec[3] for spec in rectangles)
    delta_row = rng.randint(-min_row, shape[0] - 1 - max_row)
    delta_col = rng.randint(-min_col, shape[1] - 1 - max_col)
    return tuple(
        (
            row0 + delta_row,
            col0 + delta_col,
            row1 + delta_row,
            col1 + delta_col,
            missing,
        )
        for row0, col0, row1, col1, missing in rectangles
    )


def _public_grid(profile, rng, color_rng, transform_rng):
    shape, rectangles = _PUBLIC_SPECS[profile]
    rectangles = _translate_specs(shape, rectangles, rng)
    colors = color_rng.sample(range(1, 10), len(rectangles))
    grid = _build_grid(shape, rectangles, colors)
    return _transform(grid, transform_rng.choice(_TRANSFORMS))


def _random_box(height, width, rng, *, edge=False, thin=False):
    if edge:
        side = rng.choice(("top", "bottom", "left", "right"))
    else:
        side = None
    if thin and rng.choice((False, True)):
        box_h = 2
        box_w = rng.randint(3, min(8, width - 2))
    elif thin:
        box_h = rng.randint(3, min(8, height - 2))
        box_w = 2
    else:
        box_h = rng.randint(3, min(8, height - 2))
        box_w = rng.randint(3, min(8, width - 2))

    if side == "top":
        row0 = 0
    elif side == "bottom":
        row0 = height - box_h
    else:
        row0 = rng.randint(1, height - box_h - 1)
    if side == "left":
        col0 = 0
    elif side == "right":
        col0 = width - box_w
    else:
        col0 = rng.randint(1, width - box_w - 1)
    return (row0, col0, row0 + box_h - 1, col0 + box_w - 1)


def _general_shape(difficulty, rng):
    if difficulty == "easy":
        return rng.randint(10, 12), rng.randint(12, 14)
    if difficulty == "hard":
        return rng.randint(17, 22), rng.randint(18, 24)
    if difficulty == "medium":
        return rng.randint(13, 17), rng.randint(15, 19)
    return rng.randint(10, 22), rng.randint(12, 24)


def _boxes_overlap(first, second):
    return not (
        first[2] < second[0]
        or second[2] < first[0]
        or first[3] < second[1]
        or second[3] < first[1]
    )


def _general_rectangles(profile, shape, rng):
    height, width = shape
    if profile in ("single_general", "thin_general", "edge_general"):
        box = _random_box(
            height,
            width,
            rng,
            edge=profile == "edge_general",
            thin=profile == "thin_general",
        )
        return ((*box, rng.randrange(4)),)

    if profile == "multi_overlap":
        row0 = rng.randint(1, height - 8)
        col0 = rng.randint(1, width - 9)
        boxes = [
            (row0, col0, row0 + 4, col0 + 5),
            (row0 + 1, col0 + 2, row0 + 6, col0 + 7),
        ]
    else:
        count = rng.choice((2, 3))
        row_split = height // 2
        col_split = width // 2
        zones = (
            (1, row_split - 1, 1, col_split - 1),
            (1, row_split - 1, col_split + 1, width - 2),
            (row_split + 1, height - 2, 1, col_split - 1),
        )
        boxes = []
        for row_min, row_max, col_min, col_max in zones[:count]:
            box_h = rng.randint(3, row_max - row_min + 1)
            box_w = rng.randint(3, col_max - col_min + 1)
            row0 = rng.randint(row_min, row_max - box_h + 1)
            col0 = rng.randint(col_min, col_max - box_w + 1)
            boxes.append(
                (row0, col0, row0 + box_h - 1, col0 + box_w - 1)
            )
    return tuple((*box, rng.randrange(4)) for box in boxes)


def _general_grid(profile, difficulty, rng, color_rng):
    shape = _general_shape(difficulty, rng)
    rectangles = _general_rectangles(profile, shape, rng)
    colors = color_rng.sample(range(1, 10), len(rectangles))
    return _build_grid(shape, rectangles, colors)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, semantically complete fourth-corner lesson."""
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
    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    if profile in _PUBLIC_SPECS:
        return _public_grid(
            profile,
            layout_rng,
            color_rng,
            ctx.draw_rng("transform"),
        )
    return _general_grid(profile, difficulty, layout_rng, color_rng)


def _classify_general(info):
    rectangles = info["rectangles"]
    height, width = info["height"], info["width"]
    if any(
        box["box"][0] == 0
        or box["box"][1] == 0
        or box["box"][2] == height - 1
        or box["box"][3] == width - 1
        for box in rectangles
    ):
        return "edge_general"
    if any(
        box["box"][2] - box["box"][0] + 1 == 2
        or box["box"][3] - box["box"][1] + 1 == 2
        for box in rectangles
    ):
        return "thin_general"
    if len(rectangles) == 1:
        return "single_general"
    overlap = any(
        _boxes_overlap(rectangles[left]["box"], rectangles[right]["box"])
        for left in range(len(rectangles))
        for right in range(left + 1, len(rectangles))
    )
    return "multi_overlap" if overlap else "multi_disjoint"


def observe_overrides(grid):
    """Recover the exact declared profile from the returned grid."""
    info = _analysis(grid)
    if info.get("errors"):
        return {}
    signature = _profile_signature_from_analysis(info)
    public = _PUBLIC_SIGNATURE_LOOKUP.get(signature)
    return {"scene_profile": public or _classify_general(info)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject every input outside the exact fourth-corner lesson grammar."""
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
        raise ValueError("invalid fourth-corner input: " + "; ".join(info["errors"]))
    output = _clone(grid)
    for rectangle in info["rectangles"]:
        row, col = rectangle["missing_point"]
        output[row][col] = rectangle["color"]
    return output


def _public_literal(profile):
    shape, rectangles = _PUBLIC_SPECS[profile]
    return _build_grid(shape, rectangles, range(1, len(rectangles) + 1))


_PUBLIC_SIGNATURE_LOOKUP = {}
for _profile_name in PUBLIC_PROFILES:
    _literal = _public_literal(_profile_name)
    for _transform_name in _TRANSFORMS:
        _signature = canonical_profile_signature(
            _transform(_literal, _transform_name)
        )
        _previous = _PUBLIC_SIGNATURE_LOOKUP.setdefault(_signature, _profile_name)
        if _previous != _profile_name:
            raise RuntimeError("ambiguous public fourth-corner profiles")
