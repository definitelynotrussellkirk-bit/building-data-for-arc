"""Generator for bank task 343f662c728a:E106 / e5887c52e323.

Recolor only the elbow of each red three-cell L component to yellow.  Red
non-L components and components of every other color remain unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e5887c52e323"
VERSION = "3.0.0"
TASK_ID = "e5887c52e323"
RULE_HASH = "bf76323192ad"

SUMMARY = (
    "Place one to six separated red L-triominoes in all orientations, plus "
    "optional red non-L and non-red shape distractors. Recolor only each "
    "qualifying red L's elbow yellow."
)

INVARIANTS = [
    "background is 0 and color 4 is output-only",
    "there are exactly 1..6 red three-cell L targets",
    "red distractors are recognized non-L shapes of one to four cells",
    "non-red distractors use recognized shapes and colors other than 0, 2, 4",
    "all components remain distinct under 4-connectivity",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 7..20",
        "valid": "7..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 8..20",
        "valid": "8..20",
    },
    "n_l_shapes": {
        "type": "int",
        "default": "difficulty-aware rng 1..6",
        "valid": "1..6",
    },
    "distractor_mode": {
        "type": "str",
        "default": "rng none|red_only|color_only|mixed",
        "valid": "none|red_only|color_only|mixed",
    },
}

_VALID_H = (7, 20)
_VALID_W = (8, 20)
_VALID_TARGETS = (1, 6)
_DISTRACTOR_MODES = ("none", "red_only", "color_only", "mixed")
_PROFILE_PRIOR = 0.08
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DECOY_COLORS = (1, 3, 5, 6, 7, 8, 9)

_SINGLE = ((0, 0),)
_DOMINO = ((0, 0), (0, 1))
_LINE3 = ((0, 0), (0, 1), (0, 2))
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_L4 = ((0, 0), (1, 0), (1, 1), (1, 2))
_CORNERS = ((0, 0), (0, 1), (1, 0), (1, 1))
_L_ORIENTATIONS = tuple(
    tuple(cell for cell in _CORNERS if cell != missing)
    for missing in _CORNERS
)
_RED_DISTRACTOR_SHAPES = (_SINGLE, _DOMINO, _LINE3, _SQUARE, _L4)
_NONRED_SHAPES = (
    _SINGLE,
    _DOMINO,
    _LINE3,
    _SQUARE,
    _L4,
    _L_ORIENTATIONS[0],
)

# Height, width, target count, then (color, rotation-normalized shape)
# distractors. Target orientation and all positions are nuisance variables.
_PROFILE_SPECS = (
    (7, 8, 2, ((2, _DOMINO), (7, _DOMINO))),
    (8, 9, 2, ((5, _L4),)),
    (7, 10, 2, ((2, _LINE3), (6, _DOMINO))),
    (9, 9, 2, ((2, _SINGLE), (3, _DOMINO))),
    (8, 10, 3, ((5, _LINE3),)),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "n_l_shapes"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    mode = overrides.get("distractor_mode")
    if mode is not None and type(mode) is not str:
        raise ValueError("distractor_mode must be a string")


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


def _norm(cells):
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells):
    cells = _norm(cells)
    height = max(r for r, _ in cells) + 1
    return _norm((c, height - 1 - r) for r, c in cells)


def _rotate(cells, turns):
    current = _norm(cells)
    for _ in range(turns % 4):
        current = _rotate_cw(current)
    return current


def _rotation_key(cells):
    rotations = []
    current = _norm(cells)
    for _ in range(4):
        rotations.append(current)
        current = _rotate_cw(current)
    return min(rotations)


def _shape_dimensions(cells):
    cells = _norm(cells)
    return (
        max(r for r, _ in cells) + 1,
        max(c for _, c in cells) + 1,
    )


_RED_DISTRACTOR_KEYS = frozenset(
    _rotation_key(shape) for shape in _RED_DISTRACTOR_SHAPES
)
_NONRED_KEYS = frozenset(
    _rotation_key(shape) for shape in _NONRED_SHAPES
)


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cell_r, cell_c = stack.pop()
                cells.append((cell_r, cell_c))
                for dr, dc in _CARDINALS:
                    neighbor = (cell_r + dr, cell_c + dc)
                    if (
                        0 <= neighbor[0] < h
                        and 0 <= neighbor[1] < w
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": _norm(cells),
                    "rotation_key": _rotation_key(cells),
                }
            )
    return tuple(components)


def _is_l_shape(cells):
    shape = _norm(cells)
    return (
        len(shape) == 3
        and max(r for r, _ in shape) == 1
        and max(c for _, c in shape) == 1
    )


def _is_target(component):
    return component["color"] == 2 and _is_l_shape(component["cells"])


def _elbow(cells):
    cells = tuple(cells)
    for r, c in cells:
        neighbors = sum(
            abs(r - other_r) + abs(c - other_c) == 1
            for other_r, other_c in cells
        )
        if neighbors == 2:
            return r, c
    return None


def _mode(red_distractors, color_distractors):
    if red_distractors and color_distractors:
        return "mixed"
    if red_distractors:
        return "red_only"
    if color_distractors:
        return "color_only"
    return "none"


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    components = _components(grid) if grid and grid[0] else ()
    targets = tuple(component for component in components if _is_target(component))
    red_distractors = tuple(
        component
        for component in components
        if component["color"] == 2 and not _is_target(component)
    )
    color_distractors = tuple(
        component
        for component in components
        if component["color"] != 2
    )
    return {
        "grid": grid,
        "h": len(grid),
        "w": len(grid[0]) if grid else 0,
        "components": components,
        "targets": targets,
        "red_distractors": red_distractors,
        "color_distractors": color_distractors,
        "distractor_mode": _mode(red_distractors, color_distractors),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 7..20")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 8..20")
    allowed = {0, 1, 2, 3, 5, 6, 7, 8, 9}
    if any(
        type(value) is not int or value not in allowed
        for row in coerced
        for value in row
    ):
        errors.append(
            "input values must be integer colors 0..9 with color 4 reserved"
        )

    scene = _analyze_scene(coerced)
    if not (
        _VALID_TARGETS[0]
        <= len(scene["targets"])
        <= _VALID_TARGETS[1]
    ):
        errors.append("scene must contain exactly 1..6 red L-triominoes")
    if len(scene["red_distractors"]) > 2:
        errors.append("scene may contain at most two red distractors")
    if len(scene["color_distractors"]) > 2:
        errors.append("scene may contain at most two non-red distractors")
    for component in scene["red_distractors"]:
        if component["rotation_key"] not in _RED_DISTRACTOR_KEYS:
            errors.append("red distractors must use recognized non-L shapes")
    for component in scene["color_distractors"]:
        if (
            component["color"] not in _DECOY_COLORS
            or component["rotation_key"] not in _NONRED_KEYS
        ):
            errors.append(
                "non-red distractors must use recognized colors and shapes"
            )

    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "n_l_shapes": len(scene["targets"]),
        "distractor_mode": scene["distractor_mode"],
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = [row[:] for row in scene["grid"]]
    for component in scene["targets"]:
        elbow = _elbow(component["cells"])
        if elbow is None:
            raise AssertionError("target L has no elbow")
        output[elbow[0]][elbow[1]] = 4
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    distractors = tuple(
        sorted(
            (component["color"], component["rotation_key"])
            for component in (
                *scene["red_distractors"],
                *scene["color_distractors"],
            )
        )
    )
    return (
        scene["h"],
        scene["w"],
        len(scene["targets"]),
        distractors,
    )


def _profile_signature(profile):
    h, w, n_targets, distractors = profile
    return (
        h,
        w,
        n_targets,
        tuple(
            sorted(
                (color, _rotation_key(shape))
                for color, shape in distractors
            )
        ),
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _boxes_separated(first, second):
    return (
        first[2] + 1 < second[0]
        or second[2] + 1 < first[0]
        or first[3] + 1 < second[1]
        or second[3] + 1 < first[1]
    )


def _random_placements(h, w, components, rng):
    boxes = []
    for _color, shape in components:
        shape_h, shape_w = _shape_dimensions(shape)
        options = [
            (r, c, r + shape_h - 1, c + shape_w - 1)
            for r in range(h - shape_h + 1)
            for c in range(w - shape_w + 1)
        ]
        rng.shuffle(options)
        chosen = next(
            (
                box
                for box in options
                if all(_boxes_separated(box, prior) for prior in boxes)
            ),
            None,
        )
        if chosen is None:
            return None
        boxes.append(chosen)
    return tuple(boxes)


def _paint_components(h, w, components, placements):
    grid = full_grid(h, w, 0)
    for (color, shape), box in zip(components, placements):
        for dr, dc in shape:
            grid[box[0] + dr][box[1] + dc] = color
    return grid


def _draw_components(h, w, components, rng):
    components = list(components)
    rng.shuffle(components)
    placements = _random_placements(h, w, components, rng)
    if placements is None:
        return None
    return _paint_components(h, w, components, placements)


def _mode_for_profile(profile):
    red = any(color == 2 for color, _shape in profile[3])
    other = any(color != 2 for color, _shape in profile[3])
    return _mode(red, other)


def _profile_components(profile, rng):
    _h, _w, n_targets, distractors = profile
    components = [
        (2, rng.choice(_L_ORIENTATIONS))
        for _ in range(n_targets)
    ]
    components.extend(
        (color, _rotate(shape, rng.randrange(4)))
        for color, shape in distractors
    )
    return tuple(components)


def _general_components(n_targets, mode, rng):
    components = [
        (2, rng.choice(_L_ORIENTATIONS))
        for _ in range(n_targets)
    ]
    if mode in ("red_only", "mixed"):
        for _ in range(rng.randint(1, 2)):
            shape = rng.choice(_RED_DISTRACTOR_SHAPES)
            components.append((2, _rotate(shape, rng.randrange(4))))
    if mode in ("color_only", "mixed"):
        for _ in range(rng.randint(1, 2)):
            shape = rng.choice(_NONRED_SHAPES)
            components.append(
                (
                    rng.choice(_DECOY_COLORS),
                    _rotate(shape, rng.randrange(4)),
                )
            )
    return tuple(components)


def _fallback_scene(h, w, n_targets, mode):
    grid = full_grid(h, w, 0)
    anchors = ((0, 0), (0, 3), (0, 6), (3, 0), (3, 3), (3, 6))
    for index, (top, left) in enumerate(anchors[:n_targets]):
        for dr, dc in _L_ORIENTATIONS[index % 4]:
            grid[top + dr][left + dc] = 2
    if mode in ("red_only", "mixed"):
        grid[6][0] = 2
        grid[6][1] = 2
    if mode in ("color_only", "mixed"):
        grid[6][3] = 5
        grid[6][4] = 5
    return grid


def _draw_general(h, w, n_targets, mode, rng):
    for _ in range(20):
        components = _general_components(n_targets, mode, rng)
        grid = _draw_components(h, w, components, rng)
        if grid is not None:
            return grid
    return _fallback_scene(h, w, n_targets, mode)


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
        h, w, n_targets, _distractors = profile
        mode = _mode_for_profile(profile)
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("n_l_shapes", n_targets, n_targets)
        ctx.draw_choice("distractor_mode", (mode,))
        rng = ctx.draw_rng("layout")
        grid = None
        for _ in range(20):
            grid = _draw_components(
                h,
                w,
                _profile_components(profile, rng),
                rng,
            )
            if grid is not None:
                break
        if grid is None:
            raise AssertionError("public profile unexpectedly could not fit")
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (7, 10),
                    "medium": (9, 15),
                    "hard": (14, 20),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (8, 11),
                    "medium": (9, 15),
                    "hard": (14, 20),
                }[band],
            )
        if overrides.get("n_l_shapes") is not None:
            n_targets = ctx.draw_int(
                "n_l_shapes",
                *_VALID_TARGETS,
            )
        else:
            n_targets = ctx.draw_int(
                "n_l_shapes",
                *{
                    "easy": (1, 2),
                    "medium": (2, 4),
                    "hard": (4, 6),
                }[band],
            )
        mode = ctx.draw_choice("distractor_mode", _DISTRACTOR_MODES)
        grid = _draw_general(
            h,
            w,
            n_targets,
            mode,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
