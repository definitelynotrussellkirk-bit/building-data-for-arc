"""Constructive sampler for selecting a keyed object and scaling it 2x.

The bottom-left cell is a color key.  After clearing that key cell, the
unchanged Racket authority selects the largest connected object of the keyed
color, crops its bounding box from the input, and doubles both axes.  The
sampler mixes canonical-like single-match scenes with deliberate two-match
scenes that refute the shortcut "crop every pixel of the keyed color".
"""
from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "82b2be9b4f4e"
TASK_ID = GENERATOR_ID
RULE_HASH = "eff131529ace"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "A bottom-left key selects the largest of one or two isolated matching-"
    "color objects. Crop that object's pure bounding box and upscale it 2x. "
    "Two or three differently colored distractor objects vary independently; "
    "a four-slot schedule with two discriminator slots keeps every three-demo "
    "lesson identifiable even under cyclic query rotation."
)

INVARIANTS = [
    "background is 0 and the bottom-left key is an isolated nonzero cell",
    "one or two keyed-color components have distinct sizes and a unique largest object",
    "the selected object's bbox contains only background and the keyed color",
    "two or three single-component distractor colors are isolated from every other object",
    "the selected object is non-rectangular so cropping and 2x scaling remain visible",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8..16; canonical schedule uses 8..10",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "11..17; canonical schedule uses 11..13",
        "valid": "11..17",
    },
    "key_color": {
        "type": "int",
        "default": "uniform 1..9",
        "valid": "1..9",
    },
    "n_key_blobs": {
        "type": "int",
        "default": "1..2; two of every four lesson slots force 2",
        "valid": "1..2",
    },
    "n_distractors": {
        "type": "int",
        "default": "2..3; canonical schedule forces 2",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = ("canonical", "discriminator", "broad", "discriminator")

# All shapes are normalized connected polyominoes.  Winner shapes have a real
# background hole in their bbox (bbox area > cell count), so the output cannot
# collapse to a solid-color rectangle.
_WINNER_SHAPES = {
    "l3": ((0, 0), (1, 0), (1, 1)),
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "s4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "u5": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "p5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "plus5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "stair5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "c7": (
        (0, 0), (0, 1), (0, 2),
        (1, 0),
        (2, 0), (2, 1), (2, 2),
    ),
    "ring8": (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
}
_LOSER_SHAPES = {
    "domino": ((0, 0), (0, 1)),
    "l3": _WINNER_SHAPES["l3"],
}
_DISTRACTOR_SHAPES = {
    "domino": ((0, 0), (0, 1)),
    "i3": ((0, 0), (0, 1), (0, 2)),
    "l3": _WINNER_SHAPES["l3"],
    "square4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "t4": _WINNER_SHAPES["t4"],
    "p5": _WINNER_SHAPES["p5"],
}

_AXIS_BOUNDS = {
    "grid_h": (8, 16),
    "grid_w": (11, 17),
    "key_color": (1, 9),
    "n_key_blobs": (1, 2),
    "n_distractors": (2, 3),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Any three of four consecutive examples retain a discriminator slot."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_int(ctx, name, choices):
    """Draw from a default subset while keeping the full override domain exact."""
    lo, hi = _AXIS_BOUNDS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, tuple(choices))


def _broad_dimension_choices(name, difficulty):
    lo, hi = _AXIS_BOUNDS[name]
    values = list(range(lo, hi + 1))
    if name == "grid_h":
        favored = {
            "easy": range(8, 11),
            "medium": range(10, 14),
            "hard": range(13, 17),
            None: range(8, 17),
        }[difficulty]
    else:
        favored = {
            "easy": range(11, 14),
            "medium": range(12, 16),
            "hard": range(15, 18),
            None: range(11, 18),
        }[difficulty]
    return values + list(favored) * 4


def _axis_values(ctx, profile, difficulty):
    if profile == "canonical":
        h_choices = range(8, 11)
        w_choices = range(11, 14)
        key_count_choices = (1,)
        distractor_choices = (2,)
    elif profile == "discriminator":
        h_choices = _broad_dimension_choices("grid_h", difficulty)
        w_choices = _broad_dimension_choices("grid_w", difficulty)
        key_count_choices = (2,)
        distractor_choices = (2, 2, 3)
    else:
        h_choices = _broad_dimension_choices("grid_h", difficulty)
        w_choices = _broad_dimension_choices("grid_w", difficulty)
        if difficulty == "easy":
            key_count_choices = (1, 1, 2)
            distractor_choices = (2, 2, 3)
        elif difficulty == "hard":
            key_count_choices = (1, 2, 2)
            distractor_choices = (2, 3, 3)
        else:
            key_count_choices = (1, 2)
            distractor_choices = (2, 3)

    return {
        "grid_h": _draw_int(ctx, "grid_h", h_choices),
        "grid_w": _draw_int(ctx, "grid_w", w_choices),
        "key_color": _draw_int(ctx, "key_color", range(1, 10)),
        "n_key_blobs": _draw_int(ctx, "n_key_blobs", key_count_choices),
        "n_distractors": _draw_int(ctx, "n_distractors", distractor_choices),
    }


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


@lru_cache(maxsize=None)
def _transforms(shape):
    variants = set()
    current = tuple(shape)
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((r, -c) for r, c in current))
        current = tuple((c, -r) for r, c in current)
    return tuple(sorted(variants))


def _orthogonal_halo(cells, h, w):
    blocked = set(cells)
    for r, c in tuple(cells):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                blocked.add((nr, nc))
    return blocked


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_cells(cells):
    r0, c0, r1, c1 = _bbox(cells)
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


@lru_cache(maxsize=None)
def _candidate_templates(shape, h, w):
    result = []
    for variant in _transforms(shape):
        shape_h = max(r for r, _ in variant) + 1
        shape_w = max(c for _, c in variant) + 1
        for top in range(h - shape_h + 1):
            for left in range(w - shape_w + 1):
                result.append(frozenset((top + r, left + c) for r, c in variant))
    # Immutable cache entries cannot be corrupted by the per-draw shuffle.
    return tuple(dict.fromkeys(result))


def _candidates(shape, h, w):
    return list(_candidate_templates(tuple(shape), h, w))


def _place_roles(h, w, roles, key_cell, rng):
    """Backtracking placement; never drops or shortens a requested object."""
    base_blocked = _orthogonal_halo({key_cell}, h, w)
    candidate_lists = []
    for name, _color, shape, _protect_bbox in roles:
        candidates = _candidates(shape, h, w)
        rng.shuffle(candidates)
        candidate_lists.append((name, candidates))

    states = 0

    def search(index, blocked, placed):
        nonlocal states
        states += 1
        if states > 200_000:
            return None
        if index == len(roles):
            return placed
        name, _color, _shape, protect_bbox = roles[index]
        _candidate_name, candidates = candidate_lists[index]
        for cells in candidates:
            if cells & blocked:
                continue
            occupied = _bbox_cells(cells) if protect_bbox else set(cells)
            next_blocked = blocked | _orthogonal_halo(occupied, h, w)
            answer = search(index + 1, next_blocked, placed + [(name, cells)])
            if answer is not None:
                return answer
        return None

    placed = search(0, base_blocked, [])
    if placed is None:
        raise RuntimeError(
            f"constructive placement failed for {h}x{w} with {len(roles)} objects"
        )
    return dict(placed)


def _shape_plan(ctx, profile, sample_index, h, w, n_key_blobs, n_distractors):
    rng = ctx.draw_rng("shape_plan")
    tight = h <= 9 or w <= 12 or (n_key_blobs + n_distractors) >= 5

    if n_key_blobs == 2:
        winner_names = ["l4", "t4", "s4", "u5", "p5", "plus5", "stair5"]
    elif profile == "canonical":
        # Canonical demonstrations use keyed objects of size 4 or 7.  Pin every
        # other canonical slot to the compact C-heptomino so the small default
        # census cannot silently lose the larger canonical component family.
        winner_names = ["c7"] if sample_index % 8 == 0 else ["l4", "t4", "s4"]
    else:
        winner_names = list(_WINNER_SHAPES)
    if tight and profile != "canonical":
        winner_names = [name for name in winner_names if len(_WINNER_SHAPES[name]) <= 5]
    winner_name = rng.choice(winner_names)
    winner = _WINNER_SHAPES[winner_name]

    key_shapes = [winner]
    if n_key_blobs == 2:
        loser_names = [
            name for name, shape in _LOSER_SHAPES.items()
            if len(shape) < len(winner)
        ]
        key_shapes.append(_LOSER_SHAPES[rng.choice(loser_names)])

    distractor_names = list(_DISTRACTOR_SHAPES)
    if tight:
        distractor_names = [
            name for name in distractor_names
            if len(_DISTRACTOR_SHAPES[name]) <= 3
        ]
    distractor_shapes = [
        _DISTRACTOR_SHAPES[rng.choice(distractor_names)]
        for _ in range(n_distractors)
    ]
    return key_shapes, distractor_shapes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    axes = _axis_values(ctx, profile, difficulty)
    h, w = axes["grid_h"], axes["grid_w"]
    key_color = axes["key_color"]
    n_key_blobs = axes["n_key_blobs"]
    n_distractors = axes["n_distractors"]

    other_colors = [color for color in range(1, 10) if color != key_color]
    distractor_colors = ctx.draw_rng("distractor_colors").sample(
        other_colors, n_distractors
    )
    key_shapes, distractor_shapes = _shape_plan(
        ctx, profile, sample_index, h, w, n_key_blobs, n_distractors
    )

    roles = [("winner", key_color, key_shapes[0], True)]
    if n_key_blobs == 2:
        roles.append(("key_loser", key_color, key_shapes[1], False))
    roles.extend(
        (f"distractor_{index}", color, shape, False)
        for index, (color, shape) in enumerate(
            zip(distractor_colors, distractor_shapes, strict=True)
        )
    )

    key_cell = (h - 1, 0)
    placements = _place_roles(
        h, w, roles, key_cell, ctx.draw_rng("object_placement")
    )
    grid = full_grid(h, w, 0)
    grid[key_cell[0]][key_cell[1]] = key_color
    role_colors = {name: color for name, color, _shape, _protect in roles}
    for name, cells in placements.items():
        for r, c in cells:
            grid[r][c] = role_colors[name]
    return grid


def _rectangular_grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    return None


def _color_components(grid, color, skip=frozenset()):
    h, w = len(grid), len(grid[0])
    seen = set(skip)
    components = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    point = (nr, nc)
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and point not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            components.append(cells)
    return components


def _analysis(grid):
    shape_error = _rectangular_grid_error(grid)
    if shape_error:
        return {"errors": [shape_error]}
    h, w = len(grid), len(grid[0])
    errors = []
    if not 8 <= h <= 16:
        errors.append(f"grid_h={h} outside [8, 16]")
    if not 11 <= w <= 17:
        errors.append(f"grid_w={w} outside [11, 17]")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return {"errors": errors}

    key_pos = (h - 1, 0)
    key = grid[key_pos[0]][key_pos[1]]
    if key == 0:
        errors.append("bottom-left key cell must be nonzero")
        return {"errors": errors}
    for nr, nc in ((h - 2, 0), (h - 1, 1)):
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
            errors.append("bottom-left key cell must be orthogonally isolated")
            break

    key_components = _color_components(grid, key, skip=frozenset({key_pos}))
    if not 1 <= len(key_components) <= 2:
        errors.append(
            f"expected 1..2 keyed-color components, found {len(key_components)}"
        )
    key_sizes = [len(component) for component in key_components]
    if len(key_sizes) != len(set(key_sizes)):
        errors.append("keyed-color components must have distinct sizes")

    nonzero_colors = sorted({value for row in grid for value in row if value != 0})
    distractor_colors = [color for color in nonzero_colors if color != key]
    if not 2 <= len(distractor_colors) <= 3:
        errors.append(
            f"expected 2..3 distractor colors, found {len(distractor_colors)}"
        )
    distractor_components = []
    for color in distractor_colors:
        components = _color_components(grid, color)
        if len(components) != 1:
            errors.append(
                f"distractor color {color} must form one component, found {len(components)}"
            )
        distractor_components.extend(components)

    # Different-colored objects may not touch orthogonally; otherwise the visual
    # grammar is no longer a scene of separated objects.
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other not in (0, value):
                        errors.append("different-colored objects must be separated")
                        break
            else:
                continue
            break
        else:
            continue
        break

    winner = max(key_components, key=len) if key_components else set()
    if winner:
        r0, c0, r1, c1 = _bbox(winner)
        bbox_values = {
            grid[r][c]
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        }
        if not bbox_values <= {0, key}:
            errors.append("winner bbox must contain only background and key color")
        bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if bbox_area <= len(winner):
            errors.append("largest keyed object must be non-rectangular")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "key_color": key,
        "key_components": key_components,
        "winner": winner,
        "distractor_colors": distractor_colors,
        "distractor_components": distractor_components,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    overrides = (meta or {}).get("overrides") if isinstance(meta, dict) else None
    if overrides and not errors:
        observed = {
            "grid_h": analysis["grid_h"],
            "grid_w": analysis["grid_w"],
            "key_color": analysis["key_color"],
            "n_key_blobs": len(analysis["key_components"]),
            "n_distractors": len(analysis["distractor_colors"]),
        }
        for name, expected in overrides.items():
            if name in observed and expected is not None and observed[name] != expected:
                errors.append(f"override {name} requested {expected}, observed {observed[name]}")
    return errors


def strict_canonical_like(grid):
    """Lawful task instances in the sampler's declared semantic manifold."""
    return self_check(grid)


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "key_color": analysis["key_color"],
        "n_key_blobs": len(analysis["key_components"]),
        "n_distractors": len(analysis["distractor_colors"]),
    }


def _upscale2(grid):
    return [
        [value for value in row for _ in range(2)]
        for row in grid
        for _ in range(2)
    ]


def _merge_all_matching_pixels(grid):
    """Rival: crop all keyed-color pixels instead of selecting one component."""
    work = [list(row) for row in grid]
    key = work[-1][0]
    work[-1][0] = 0
    cells = {
        (r, c)
        for r, row in enumerate(work)
        for c, value in enumerate(row)
        if value == key
    }
    if not cells:
        return []
    r0, c0, r1, c1 = _bbox(cells)
    return _upscale2([row[c0 : c1 + 1] for row in work[r0 : r1 + 1]])


def _has_multiple_matching_objects(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["key_components"]) == 2


SEMANTIC_WITNESSES = {
    "multiple_matching_objects": _has_multiple_matching_objects,
}
SEMANTIC_RIVALS = {
    "merge_all_matching_pixels": _merge_all_matching_pixels,
}
WITNESS_RIVALS = {
    "multiple_matching_objects": ["merge_all_matching_pixels"],
}
CANONICAL_SHORTCUTS = {
    "merge_all_matching_pixels": _merge_all_matching_pixels,
}
LESSON_COMPETITORS = {
    "merge_all_matching_pixels": _merge_all_matching_pixels,
}
